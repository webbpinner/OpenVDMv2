#!/usr/bin/env python3
"""

FILE:  OVDM_lowering.py

DESCRIPTION:  Gearman worker the handles the tasks of initializing a new
lowering and finalizing the current lowering.

     BUGS:
    NOTES:
   AUTHOR:  Webb Pinner
  COMPANY:  Capable Solutions
  VERSION:  2.5
  CREATED:  2015-01-01
 REVISION:  2020-12-28

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
import subprocess
import json
import time
import signal
import logging
from os.path import dirname, realpath
import python3_gearman

sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.utils.set_owner_group_permissions import set_owner_group_permissions
from server.utils.output_json_data_to_file import output_json_data_to_file
from server.lib.openvdm import OpenVDM, DEFAULT_LOWERING_CONFIG_FN


def build_filelist(source_dir):
    """
    Builds the list of files in the source directory
    """

    logging.debug("source_dir: %s", source_dir)

    return_files = []
    for root, _, filenames in os.walk(source_dir):
        for filename in filenames:
            return_files.append(os.path.join(root, filename))

    return_files = [filename.replace(source_dir + '/', '', 1) for filename in return_files]
    return return_files


def export_lowering_config(gearman_worker, lowering_config_filepath, finalize=False):
    """
    Export the current OpenVDM configuration to the specified filepath
    """

    lowering_config = gearman_worker.ovdm.get_lowering_config()

    if finalize:
        lowering_config['loweringFinalizedOn'] = lowering_config['configCreatedOn']
    elif os.path.isfile(lowering_config_filepath):
        logging.info("Reading existing configuration file")
        try:
            with open(lowering_config_filepath) as json_file:
                data = json.load(json_file)
                if "loweringFinalizedOn" in data:
                    lowering_config['loweringFinalizedOn'] = data['loweringFinalizedOn']

        except OSError as err:
            logging.debug(str(err))
            return {'verdict': False, 'reason': "Unable to read existing configuration file"}

    for transfer in lowering_config['collectionSystemTransfersConfig']:
        del transfer['sshPass']
        del transfer['rsyncPass']
        del transfer['smbPass']

    return output_json_data_to_file(lowering_config_filepath, lowering_config)


class OVDMGearmanWorker(python3_gearman.GearmanWorker): # pylint: disable=too-many-instance-attributes
    """
    Class for the current Gearman worker
    """

    def __init__(self):
        self.stop = False
        self.ovdm = OpenVDM()
        self.task = None
        self.cruise_id = self.ovdm.get_cruise_id()
        self.lowering_id = self.ovdm.get_lowering_id()
        self.lowering_start_date = self.ovdm.get_lowering_start_date()
        self.shipboard_data_warehouse_config = self.ovdm.get_shipboard_data_warehouse_config()
        self.lowering_dir = os.path.join(self.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], self.cruise_id, self.shipboard_data_warehouse_config['loweringDataBaseDir'], self.lowering_id)

        super().__init__(host_list=[self.ovdm.get_gearman_server()])

    def on_job_execute(self, current_job):
        """
        Function run whenever a new job arrives
        """

        logging.debug("current_job: %s", current_job)

        payload_obj = json.loads(current_job.data)

        self.stop = False
        self.task = self.ovdm.get_task_by_name(current_job.task)
        logging.debug("task: %s", self.task)

        if int(self.task['taskID']) > 0:
            self.ovdm.set_running_task(self.task['taskID'], os.getpid(), current_job.handle)
#        else:
#            self.ovdm.trackGearmanJob(taskLookup[current_job.task], os.getpid(), current_job.handle)

        logging.info("Job: %s (%s) started at: %s", self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime()))

        self.cruise_id = payload_obj['cruiseID'] if 'cruiseID' in payload_obj else self.ovdm.get_cruise_id()
        self.lowering_id = payload_obj['loweringID'] if 'loweringID' in payload_obj else self.ovdm.get_lowering_id()
        self.lowering_start_date = payload_obj['loweringStartDate'] if 'loweringStartDate' in payload_obj else self.ovdm.get_lowering_start_date()
        self.shipboard_data_warehouse_config = self.ovdm.get_shipboard_data_warehouse_config()
        self.lowering_dir = os.path.join(self.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], self.cruise_id, self.shipboard_data_warehouse_config['loweringDataBaseDir'], self.lowering_id)

        return super().on_job_execute(current_job)


    def on_job_exception(self, current_job, exc_info):
        """
        Function run whenever the current job has an exception
        """

        logging.error("Job: %s (%s) failed at: %s", self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime()))

        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail", "reason": "Worker crashed"}]))
        if int(self.task['taskID']) > 0:
            self.ovdm.set_error_task(self.task['taskID'], "Worker crashed")
        else:
            self.ovdm.send_msg(self.task['longName'] + ' failed', 'Worker crashed')

        exc_type, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error(exc_type, fname, exc_tb.tb_lineno)
        return super().on_job_exception(current_job, exc_info)


    def on_job_complete(self, current_job, job_result):
        """
        Function run whenever the current job completes
        """

        results_obj = json.loads(job_result)

        job_data = {
            'cruiseID': self.cruise_id,
            'loweringID': self.lowering_id,
            'loweringStartDate': self.lowering_start_date
        }

        if current_job.task == 'setupNewLowering':

            gm_client = python3_gearman.GearmanClient([self.ovdm.get_gearman_server()])

            for task in self.ovdm.get_tasks_for_hook('setupNewLowering'):
                logging.info("Adding post task: %s", task)
                gm_client.submit_job(task, json.dumps(job_data), background=True)

        elif current_job.task == 'finalizeCurrentLowering':

            gm_client = python3_gearman.GearmanClient([self.ovdm.get_gearman_server()])

            for task in self.ovdm.get_tasks_for_hook('finalizeCurrentLowering'):
                logging.info("Adding post task: %s", task)
                gm_client.submit_job(task, json.dumps(job_data), background=True)

        if len(results_obj['parts']) > 0:
            if results_obj['parts'][-1]['result'] == "Fail": # Final Verdict
                if int(self.task['taskID']) > 0:
                    self.ovdm.set_error_task(self.task['taskID'], results_obj['parts'][-1]['reason'])
                else:
                    self.ovdm.send_msg(self.task['longName'] + ' failed', results_obj['parts'][-1]['reason'])
            else:
                self.ovdm.set_idle_task(self.task['taskID'])
        else:
            self.ovdm.set_idle_task(self.task['taskID'])

        logging.debug("Job Results: %s", json.dumps(results_obj, indent=2))
        logging.info("Job: %s (%s) completed at: %s", self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime()))

        return super().send_job_complete(current_job, job_result)


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


def task_setup_new_lowering(gearman_worker, gearman_job):
    """
    Setup a new lowering
    """
    job_results = {'parts':[]}

    payload_obj = json.loads(gearman_job.data)
    logging.debug("Payload: %s", json.dumps(payload_obj, indent=2))

    lowering_config_filepath = os.path.join(gearman_worker.lowering_dir, DEFAULT_LOWERING_CONFIG_FN)

    gearman_worker.send_job_status(gearman_job, 1, 10)

    gm_client = python3_gearman.GearmanClient([gearman_worker.ovdm.get_gearman_server()])

    logging.info("Creating lowering data directory")
    completed_job_request = gm_client.submit_job("createLoweringDirectory", gearman_job.data)

    result_obj = json.loads(completed_job_request.result)

    if result_obj['parts'][-1]['result'] == "Pass": # Final Verdict
        job_results['parts'].append({"partName": "Create lowering data directory structure", "result": "Pass"})
    else:
        logging.error("Failed to create lowering data directory")
        job_results['parts'].append({"partName": "Create lowering data directory structure", "result": "Fail", "reason": result_obj['parts'][-1]['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 5, 10)

    #build lowering Config file
    logging.info("Exporting Lowering Configuration")
    output_results = export_lowering_config(gearman_worker, lowering_config_filepath)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Export lowering config data to file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Export lowering config data to file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], lowering_config_filepath)

    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Set lowering config file ownership/permissions", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 9, 10)

    logging.info("Updating Lowering Size")
    lowering_size_proc = subprocess.run(['du','-sb', gearman_worker.lowering_dir], capture_output=True, text=True, check=False)
    if lowering_size_proc.returncode == 0:
        logging.info("Cruise Size: %s", lowering_size_proc.stdout.split()[0])
        gearman_worker.ovdm.set_lowering_size(lowering_size_proc.stdout.split()[0])
    else:
        gearman_worker.ovdm.set_lowering_size("0")

    gearman_worker.send_job_status(gearman_job, 10, 10)

    return json.dumps(job_results)

def task_finalize_current_lowering(gearman_worker, gearman_job):
    """
    Finalize the current lowering
    """
    job_results = {'parts':[]}

    gearman_worker.send_job_status(gearman_job, 1, 10)

    lowering_config_filepath = os.path.join(gearman_worker.lowering_dir, DEFAULT_LOWERING_CONFIG_FN)

    if os.path.exists(gearman_worker.lowering_dir) and (gearman_worker.loweringID != ''):
        job_results['parts'].append({"partName": "Verify Lowering Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Lowering Directory exists", "result": "Fail", "reason": "Lowering directory: " + gearman_worker.lowering_dir + " could not be found"})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 3, 10)
    logging.info("Queuing Collection System Transfers")

    gm_client = python3_gearman.GearmanClient([gearman_worker.ovdm.get_gearman_server()])

    gm_data = {
        'loweringID': gearman_worker.loweringID,
        'loweringStartDate': gearman_worker.loweringStartDate,
        'systemStatus': "On",
        'collectionSystemTransfer': {}
    }

    collection_system_transfer_jobs = []

    collection_system_transfers = gearman_worker.ovdm.get_active_collection_system_transfers(cruise=False)

    for collection_system_transfer in collection_system_transfers:

        logging.debug("Queuing runCollectionSystemTransfer job for %s", collection_system_transfer['name'])
        gm_data['collectionSystemTransfer']['collectionSystemTransferID'] = collection_system_transfer['collectionSystemTransferID']

        collection_system_transfer_jobs.append( {"task": "runCollectionSystemTransfer", "data": json.dumps(gm_data)} )

    gearman_worker.send_job_status(gearman_job, 5, 10)

    if len(collection_system_transfer_jobs) > 0:
        logging.info("Submitting runCollectionSystemTransfer jobs")
        submitted_job_request = gm_client.submit_multiple_jobs(collection_system_transfer_jobs, background=False, wait_until_complete=False)

        gearman_worker.send_job_status(gearman_job, 7, 10)

        time.sleep(1)
        gm_client.wait_until_jobs_completed(submitted_job_request)
        logging.info("Completed runCollectionSystemTransfers jobs")

    gearman_worker.send_job_status(gearman_job, 9, 10)

    #build Lowering Config file
    logging.info("Exporting Lowering Configuration")
    output_results = export_lowering_config(gearman_worker, lowering_config_filepath, finalize=True)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Export Lowering config data to file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Export Lowering config data to file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], lowering_config_filepath)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set Lowering config file ownership/permissions", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Set Lowering config file ownership/permissions", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    # need to add code for updating MD5

    gearman_worker.send_job_status(gearman_job, 10, 10)
    return json.dumps(job_results)


def task_export_lowering_config(gearman_worker, gearman_job):
    """
    Export the Lowering configuration to file
    """
    job_results = {'parts':[]}

    lowering_config_filepath = os.path.join(gearman_worker.lowering_dir, DEFAULT_LOWERING_CONFIG_FN)

    gearman_worker.send_job_status(gearman_job, 1, 10)

    logging.info("Verifying lowering directory exists")
    if os.path.exists(gearman_worker.lowering_dir) and (gearman_worker.loweringID != ''):
        job_results['parts'].append({"partName": "Verify Lowering Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Lowering Directory exists", "result": "Fail", "reason": "Unable to locate the lowering directory: " + gearman_worker.lowering_dir})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 3, 10)

    #build OpenVDM Config file
    logging.info("Exporting Lowering Configuration")
    output_results = export_lowering_config(gearman_worker, lowering_config_filepath)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Export Lowering config data to file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Export Lowering config data to file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 6, 10)

    logging.info("Setting file ownership/permissions")
    output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], lowering_config_filepath)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set file ownership/permissions", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Set file ownership/permissions", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 10, 10)
    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle Lowering-Level tasks')
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

    # global new_worker
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

    logging.info("\tTask: setupNewLowering")
    new_worker.register_task("setupNewLowering", task_setup_new_lowering)
    logging.info("\tTask: finalizeCurrentLowering")
    new_worker.register_task("finalizeCurrentLowering", task_finalize_current_lowering)
    logging.info("\tTask: exportLoweringConfig")
    new_worker.register_task("exportLoweringConfig", task_export_lowering_config)

    logging.info("Waiting for jobs...")
    new_worker.work()
