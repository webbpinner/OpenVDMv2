#!/usr/bin/env python3
"""

FILE:  md5_summary.py

DESCRIPTION:  Gearman worker tha handles the creation and update of an MD5
    checksum summary.

     BUGS:
    NOTES:
   AUTHOR:  Webb Pinner
  COMPANY:  Capable Solutions
  VERSION:  2.5
  CREATED:  2015-01-01
 REVISION:  2020-12-29

LICENSE INFO: Open Vessel Data Management v2.5 (OpenVDMv2)
Copyright (C) OceanDataRat.org 2021

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/gpl-3.0.html>.

"""

import argparse
import os
import sys
import json
import hashlib
import signal
import time
import logging
import python3_gearman

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.utils.set_owner_group_permissions import set_owner_group_permissions
from server.lib.openvdm import OpenVDM, DEFAULT_MD5_SUMMARY_FN, DEFAULT_MD5_SUMMARY_MD5_FN


CUSTOM_TASKS = [
    {
        "taskID": "0",
        "name": "updateMD5Summary",
        "longName": "Updating MD5 Summary",
    }
]

BUF_SIZE = 65536  # read files in 64kb chunks


def build_filelist(source_dir):
    """
    Build the filelist
    """

    logging.debug("sourceDir: %s", source_dir)

    return_files = []
    for root, _, filenames in os.walk(source_dir):
        for filename in filenames:
            if filename not in (DEFAULT_MD5_SUMMARY_FN, DEFAULT_MD5_SUMMARY_MD5_FN):
                return_files.append(os.path.join(root, filename))

    return_files = [filename.replace(source_dir + '/', '', 1) for filename in return_files]
    return return_files


def hash_file(filepath):
    """
    Build the md5 hash for the given file
    """
    try:
        md5 = hashlib.md5()
        with open(filepath, 'rb') as file:
            while True:
                data = file.read(BUF_SIZE)
                if not data:
                    break
                md5.update(data)
        return md5.hexdigest()
    except Exception as err:
        raise err

def build_md5_hashes(gearman_worker, gearman_job, filelist):
    """
    Build the md5 hashes for the files in the filelist
    """

    filesize_limit = gearman_worker.OVDM.getMD5FilesizeLimit()
    filesize_limit_status = gearman_worker.OVDM.getMD5FilesizeLimitStatus()

    hashes = []

    for idx, filename in enumerate(filelist):

        if gearman_worker.stop:
            logging.debug("Stopping job")
            break

        filepath = os.path.join(gearman_worker.cruise_dir, filename)

        if filesize_limit_status == 'On' and filesize_limit != '0':
            if os.stat(filepath).st_size < int(filesize_limit) * 1000000:
                try:
                    hashes.append({'hash': hash_file(filepath), 'filename': filename})
                except Exception as err:
                    logging.error("Could not generate md5 hash for file: %s", filename)
                    logging.debug(str(err))

            else:
                hashes.append({'hash': '********************************', 'filename': filename})
        else:
            try:
                hashes.append({'hash': hash_file(filepath), 'filename': filename})
            except Exception as err:
                logging.error("Could not generate md5 hash for file: %s", filename)
                logging.error(str(err))

        gearman_worker.send_job_status(gearman_job, int(20 + 60*float(idx)/float(len(filelist))), 100)

    return hashes


def build_md5_summary_md5(gearman_worker):
    """
    Build the md5 hash for the md5 summary file
    """

    md5_summary_filepath = os.path.join(gearman_worker.cruise_dir, DEFAULT_MD5_SUMMARY_FN)
    md5_summary_md5_filepath = os.path.join(gearman_worker.cruise_dir, DEFAULT_MD5_SUMMARY_MD5_FN)

    try:
        with open(md5_summary_md5_filepath, 'w') as md5_summary_md5_file:
            md5_summary_md5_file.write(hash_file(md5_summary_filepath))

    except IOError:
        logging.error("Error Saving MD5 Summary MD5 file: %s", md5_summary_md5_filepath)
        return {"verdict": False, "reason": "Error Saving MD5 Summary MD5 file: " + md5_summary_md5_filepath}

    return {"verdict": True}


class OVDMGearmanWorker(python3_gearman.GearmanWorker): # pylint: disable=too-many-instance-attributes
    """
    Class for the current Gearman worker
    """

    def __init__(self):
        self.stop = False
        self.ovdm = OpenVDM()
        self.task = None
        self.cruise_id = self.ovdm.get_cruise_id()
        self.shipboard_data_warehouse_config = self.ovdm.get_shipboard_data_warehouse_config()
        self.cruise_dir = os.path.join(self.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], self.cruise_id)
        self.md5_summary_filepath = os.path.join(self.cruise_dir, DEFAULT_MD5_SUMMARY_FN)
        self.md5_summary_md5_filepath = os.path.join(self.cruise_dir, DEFAULT_MD5_SUMMARY_MD5_FN)

        super().__init__(host_list=[self.ovdm.get_gearman_server()])

    @staticmethod
    def _get_custom_task(current_job):
        """
        Fetch task metadata
        """

        task = list(filter(lambda task: task['name'] == current_job.task, CUSTOM_TASKS))
        return task[0] if len(task) > 0 else None


    def on_job_execute(self, current_job):
        """
        Function run whenever a new job arrives
        """

        logging.debug("current_job: %s", current_job)

        self.stop = False
        payload_obj = json.loads(current_job.data)

        self.task = self._get_custom_task(current_job) if self._get_custom_task(current_job) is not None else self.ovdm.get_task_by_name(current_job.task)
        logging.debug("task: %s", self.task)

        if int(self.task['taskID']) > 0:
            self.ovdm.set_running_task(self.task['taskID'], os.getpid(), current_job.handle)
        else:
            self.ovdm.track_gearman_job(self.task['longName'], os.getpid(), current_job.handle)

        logging.info("Job: %s (%s) started at: %s", self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime()))

        self.cruise_id = payload_obj['cruiseID'] if 'cruiseID' in payload_obj else self.ovdm.get_cruise_id()
        self.shipboard_data_warehouse_config = self.ovdm.get_shipboard_data_warehouse_config()
        self.cruise_dir = os.path.join(self.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], self.cruise_id)
        self.md5_summary_filepath = os.path.join(self.cruise_dir, DEFAULT_MD5_SUMMARY_FN)
        self.md5_summary_md5_filepath = os.path.join(self.cruise_dir, DEFAULT_MD5_SUMMARY_MD5_FN)
        return super().on_job_execute(current_job)


    def on_job_exception(self, current_job, exc_info):
        """
        Function run whenever the current job has an exception
        """

        logging.error("Job: %s (%s) failed at: %s", self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime()))

        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail", "reason": "Unknown"}]))
        if int(self.task['taskID']) > 0:
            self.ovdm.set_error_task(self.task['taskID'], "Worker crashed")
        else:
            self.ovdm.send_msg(self.task['longName'] + ' failed', 'Worker crashed')

        exc_type, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error(exc_type, fname, exc_tb.tb_lineno)
        return super().on_job_exception(current_job, exc_info)


    def on_job_complete(self, current_job, job_results):
        """
        Function run whenever the current job completes
        """

        results_obj = json.loads(job_results)

        if len(results_obj['parts']) > 0:
            if results_obj['parts'][-1]['result'] == "Fail": # Final Verdict
                if int(self.task['taskID']) > 0:
                    self.ovdm.set_error_task(self.task['taskID'], results_obj['parts'][-1]['reason'])
                else:
                    self.ovdm.send_msg(self.task['longName'] + ' failed', results_obj['parts'][-1]['reason'])
            else:
                if int(self.task['taskID']) > 0:
                    self.ovdm.set_idle_task(self.task['taskID'])
        else:
            if int(self.task['taskID']) > 0:
                self.ovdm.set_idle_task(self.task['taskID'])

        logging.debug("Job Results: %s", json.dumps(results_obj, indent=2))
        logging.info("Job: %s (%s) completed at: %s", self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime()))

        return super().send_job_complete(current_job, job_results)


    def stop_task(self):
        """
        Function to stop the current job
        """
        self.stop = True
        logging.warning("Stopping current task...")


    def quit_worker(self):
        """
        Function to quit the worker
        """
        self.stop = True
        logging.warning("Quitting worker...")
        self.shutdown()


def task_update_md5_summary(gearman_worker, gearman_job): # pylint: disable=too-many-branches,too-many-statements,too-many-locals
    """
    Update the existing MD5 summary files
    """

    job_results = {'parts':[]}

    payload_obj = json.loads(gearman_job.data)
    logging.debug("Payload: %s", json.dumps(payload_obj, indent=2))

    gearman_worker.send_job_status(gearman_job, 1, 10)

    logging.debug("Building filelist")
    filelist = []

    job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Pass"})

    if payload_obj['files']['new'] or payload_obj['files']['updated']:
        filelist.extend(payload_obj['files']['new'])
        filelist.extend(payload_obj['files']['updated'])
    else:
        return json.dumps(job_results)

    #filelist = [os.path.join(gearman_worker.cruiseID, filename) for filename in filelist]
    logging.debug('Filelist: %s', json.dumps(filelist, indent=2))

    gearman_worker.send_job_status(gearman_job, 2, 10)

    logging.debug("Building hashes")
    new_hashes = build_md5_hashes(gearman_worker, gearman_job, filelist)
    logging.debug('Hashes: %s', json.dumps(new_hashes, indent=2))

    gearman_worker.send_job_status(gearman_job, 8, 10)

    if gearman_worker.stop:
        return json.dumps(job_results)

    job_results['parts'].append({"partName": "Calculate Hashes", "result": "Pass"})

    existing_hashes = []

    logging.debug("Processing existing MD5 summary file")

    try:
        with open(gearman_worker.md5_summary_filepath, 'r') as md5_summary_file:

            for line in md5_summary_file:
                (md5_hash, filename) = line.split(' ', 1)
                existing_hashes.append({'hash': md5_hash, 'filename': filename.rstrip('\n')})

    except IOError:
        logging.error("Error Reading pre-existing MD5 Summary file: %s", gearman_worker.md5_summary_filepath)
        job_results['parts'].append({"partName": "Reading pre-existing MD5 Summary file", "result": "Fail", "reason": "Error Reading pre-existing MD5 Summary file: " + gearman_worker.md5_summary_filepath})
        return json.dumps(job_results)

    #logging.debug('Existing Hashes:', json.dumps(existing_hashes, indent=2))
    job_results['parts'].append({"partName": "Reading pre-existing MD5 Summary file", "result": "Pass"})

    row_added = 0
    row_updated = 0

    for new_hash in new_hashes:
        updated = False
        for existing_hash in existing_hashes:
            if new_hash['filename'] == existing_hash['filename']:
                existing_hash['hash'] = new_hash['hash']
                updated = True
                row_updated += 1
                break

        if not updated:
            existing_hashes.append({'hash': new_hash['hash'], 'filename': new_hash['filename']})
            row_added += 1

    if row_added > 0:
        logging.debug("%s row(s) added", row_added)
    if row_updated > 0:
        logging.debug("%s row(s) updated", row_updated)

    gearman_worker.send_job_status(gearman_job, 85, 100)

    #logging.debug("Sorting hashes")
    sorted_hashes = sorted(existing_hashes, key=lambda hashes: hashes['filename'])

    logging.debug("Building MD5 Summary file")
    try:
        with open(gearman_worker.md5_summary_filepath, 'w') as md5_summary_file:

            for filehash in sorted_hashes:
                md5_summary_file.write(filehash['hash'] + ' ' + filehash['filename'] + '\n')

        job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Pass"})

    except IOError:
        logging.error("Error updating MD5 Summary file: %s", gearman_worker.md5_summary_filepath)
        job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Fail", "reason": "Error updating MD5 Summary file: " + gearman_worker.md5_summary_filepath})
        return json.dumps(job_results)

    output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], gearman_worker.md5_summary_filepath)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set MD5 Summary file ownership/permissions", "result": "Pass"})
    else:
        logging.error("Failed to set directory ownership")
        job_results['parts'].append({"partName": "Set MD5 Summary file ownership/permissions", "result": "Fail", "reason": output_results['reason']})

    gearman_worker.send_job_status(gearman_job, 9, 10)

    logging.debug("Building MD5 Summary MD5 file")

    output_results = build_md5_summary_md5(gearman_worker)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Writing MD5 Summary MD5 file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Writing MD5 Summary MD5 file", "result": "Fail", "reason": output_results['reason']})

    output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], gearman_worker.md5_summary_md5_filepath)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set MD5 Summary MD5 file ownership/permissions", "result": "Pass"})
    else:
        logging.error("Failed to set directory ownership")
        job_results['parts'].append({"partName": "Set MD5 Summary MD5 file ownership/permissions", "result": "Fail", "reason": output_results['reason']})

    gearman_worker.send_job_status(gearman_job, 10, 10)
    return json.dumps(job_results)


def task_rebuild_md5_summary(gearman_worker, gearman_job): # pylint: disable=too-many-statements
    """
    Rebuild the existing MD5 summary files
    """

    job_results = {'parts':[]}

    payload_obj = json.loads(gearman_job.data)
    logging.debug("Payload: %s", json.dumps(payload_obj, indent=2))

    gearman_worker.send_job_status(gearman_job, 1, 10)

    if os.path.exists(gearman_worker.cruise_dir):
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Pass"})
    else:
        logging.error("Cruise directory not found")
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Fail", "reason": "Unable to locate the cruise directory: " + gearman_worker.cruise_dir})
        return json.dumps(job_results)

    logging.info("Building filelist")
    filelist = build_filelist(gearman_worker.cruise_dir)
    logging.debug('Filelist: %s', json.dumps(filelist, indent=2))

    job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Pass"})

    gearman_worker.send_job_status(gearman_job, 2, 10)

    logging.info("Building hashes")
    new_hashes = build_md5_hashes(gearman_worker, gearman_job, filelist)
    logging.debug("Hashes: %s", json.dumps(new_hashes, indent=2))

    if gearman_worker.stop:
        job_results['parts'].append({"partName": "Calculate Hashes", "result": "Fail", "reason": "Job was stopped by user"})
        return json.dumps(job_results)

    job_results['parts'].append({"partName": "Calculate Hashes", "result": "Pass"})

    gearman_worker.send_job_status(gearman_job, 85, 100)

    logging.debug("Sorting Hashes")
    sorted_hashes = sorted(new_hashes, key=lambda hashes: hashes['filename'])

    gearman_worker.send_job_status(gearman_job, 9, 10)

    logging.info("Building MD5 Summary file")
    try:
        #logging.debug("Saving new MD5 Summary file")
        with open(gearman_worker.md5_summary_filepath, 'w') as md5_summary_file:

            for filehash in sorted_hashes:
                md5_summary_file.write(filehash['hash'] + ' ' + filehash['filename'] + '\n')

        job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Pass"})

    except IOError:
        logging.error("Error saving MD5 Summary file: %s", gearman_worker.md5_summary_filepath)
        job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Fail", "reason": "Error saving MD5 Summary file: " + gearman_worker.md5_summary_filepath})
        return json.dumps(job_results)

    output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], gearman_worker.md5_summary_filepath)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set MD5 Summary file ownership/permissions", "result": "Pass"})
    else:
        logging.error("Failed to set directory ownership")
        job_results['parts'].append({"partName": "Set MD5 Summary file ownership/permissions", "result": "Fail", "reason": output_results['reason']})

    gearman_worker.send_job_status(gearman_job, 95, 100)

    logging.info("Building MD5 Summary MD5 file")

    output_results = build_md5_summary_md5(gearman_worker)
    if output_results['verdict']:
        job_results['parts'].append({"partName": "Writing MD5 Summary MD5 file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Writing MD5 Summary MD5 file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], gearman_worker.md5_summary_md5_filepath)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set MD5 Summary MD5 file ownership/permissions", "result": "Pass"})
    else:
        logging.error("Failed to set directory ownership")
        job_results['parts'].append({"partName": "Set MD5 Summary MD5 file ownership/permissions", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 10, 10)
    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle MD5 Summary related tasks')
    parser.add_argument('-v', '--verbosity', dest='verbosity',
                        default=0, action='count',
                        help='Increase output verbosity')

    parsed_args = parser.parse_args()

    ############################
    # Set up logging before we do any other argument parsing (so that we
    # can log problems with argument parsing).

    LOGGING_FORMAT = '%(asctime)-15s %(levelname)s - %(message)s'
    logging.basicConfig(format=LOGGING_FORMAT)

    LOG_LEVELS = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    parsed_args.verbosity = min(parsed_args.verbosity, max(LOG_LEVELS))
    logging.getLogger().setLevel(LOG_LEVELS[parsed_args.verbosity])

    logging.debug("Creating Worker...")

    new_worker = OVDMGearmanWorker()
    new_worker.set_client_id(__file__)

    logging.debug("Defining Signal Handlers...")
    def sigquit_handler(_signo, _stack_frame):
        """
        Signal Handler for QUIT
        """
        logging.warning("QUIT Signal Received")
        new_worker.stop_task()

    def sigint_handler(_signo, _stack_frame):
        """
        Signal Handler for INT
        """
        logging.warning("INT Signal Received")
        new_worker.quit_worker()

    signal.signal(signal.SIGQUIT, sigquit_handler)
    signal.signal(signal.SIGINT, sigint_handler)

    logging.info("Registering worker tasks...")

    logging.info("\tTask: updateMD5Summary")
    new_worker.register_task("updateMD5Summary", task_update_md5_summary)
    logging.info("\tTask: rebuildMD5Summary")
    new_worker.register_task("rebuildMD5Summary", task_rebuild_md5_summary)

    logging.info("Waiting for jobs...")
    new_worker.work()
