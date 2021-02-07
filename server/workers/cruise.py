#!/usr/bin/env python3
"""
FILE:  OVDM_cruise.py

DESCRIPTION:  Gearman worker the handles the tasks of initializing a new cruise
    and finalizing the current cruise.  This includes initializing/finalizing
    the data dashboard, MD5summary and transfer log summary.

     BUGS:
    NOTES:
   AUTHOR:  Webb Pinner
  COMPANY:  Capable Solutions
  VERSION:  2.5
  CREATED:  2015-01-01
 REVISION:  2020-12-25

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
import tempfile
import subprocess
import json
import time
import signal
import shutil
import logging
from os.path import dirname, realpath
import python3_gearman

sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.lib.set_owner_group_permissions import set_owner_group_permissions
from server.lib.check_filenames import bad_filename
from server.lib.output_json_data_to_file import output_json_data_to_file
from server.lib.openvdm import OpenVDM, DEFAULT_CRUISE_CONFIG_FN

def build_filelist(source_dir):
    """
    Builds the list of files in the source directory
    """

    return_files = { 'include':[], 'exclude':[], 'new':[], 'updated':[]}

    for root, _, filenames in os.walk(source_dir):

        return_files['include'] = [os.path.join(root, filename) for filename in filenames]

        return_files['exclude'] = list(filter(lambda filename: os.path.islink(filename) or bad_filename(filename), return_files['include']))
        return_files['include'] = list(filter(lambda filename: not os.path.islink(filename) and not bad_filename(filename), return_files['include']))

    return_files['exclude'] = [filename.split(source_dir + '/',1).pop() for filename in return_files['exclude']]
    return_files['include'] = [filename.split(source_dir + '/',1).pop() for filename in return_files['include']]

    return return_files


def clear_directory(directory):
    """
    Deletes all files and subdirectorties within the specified directory
    """

    reasons = []

    # Clear out PublicData
    for root, dirs, files in os.walk(directory + '/', topdown=False):
        for pd_dir in dirs:
            try:
                os.rmdir(os.path.join(root, pd_dir))
            except OSError:
                logging.error("Unable to delete %s", os.path.join(root, pd_dir))
                reasons.append("Unable to delete {}".format(os.path.join(root, pd_dir)))

        for pd_file in files:
            try:
                os.unlink(os.path.join(root, pd_file))
            except OSError:
                logging.error("Unable to delete %s", os.path.join(root, pd_file))
                reasons.append("Unable to delete {}".format(os.path.join(root, pd_file)))

    if len(reasons) > 0:
        return {'verdict': False, 'reason': "\n".join(reasons)}

    return {'verdict': True}


def export_ovdm_config(gearman_worker, ovdm_config_file_path, finalize=False):
    """
    Export the current OpenVDM configuration to the specified filepath
    """

    ovdm_config = gearman_worker.ovdm.get_ovdm_config()

    if finalize:
        ovdm_config['cruiseFinalizedOn'] = ovdm_config['configCreatedOn']
    elif os.path.isfile(ovdm_config_file_path):
        logging.info("Reading existing configuration file")
        try:
            with open(ovdm_config_file_path) as json_file:
                data = json.load(json_file)
                if "cruiseFinalizedOn" in data:
                    ovdm_config['cruiseFinalizedOn'] = data['cruiseFinalizedOn']

        except OSError as err:
            logging.debug(str(err))
            return {'verdict': False, 'reason': "Unable to read existing configuration file"}

    for transfer in ovdm_config['cruiseDataTransfersConfig']:
        del transfer['sshPass']
        del transfer['rsyncPass']
        del transfer['smbPass']

    for transfer in ovdm_config['collectionSystemTransfersConfig']:
        del transfer['sshPass']
        del transfer['rsyncPass']
        del transfer['smbPass']

    return output_json_data_to_file(ovdm_config_file_path, ovdm_config)


def transfer_publicdata_dir(gearman_worker, gearman_job):
    """
    Transfer the contents of the PublicData share to the Cruise Data Directory
    """

    publicdata_dir = gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehousePublicDataDir']

    logging.debug("Building file list")
    files = build_filelist(publicdata_dir)

    logging.debug("Files: %s", json.dumps(files, indent=2))

    if len(files['exclude']) > 0:
        logging.warning("Found %s problem filename(s):", len(files['exclude']))
        logging.warning("\t %s", "\n\t".join(files['exclude']))
        return {'verdict': False, 'reason': "Symbolic links or Non-ASCii filenames in {}: {}".format(publicdata_dir,', '.join(files['exclude'])), 'files': files }

    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    # Build rsync file transfer list
    rsync_filelist_path = os.path.join(tmpdir, "rsyncFileList.txt")

    try:
        local_transfer_filelist = [filename.replace(publicdata_dir, '', 1) for filename in files['include']]
        with open(rsync_filelist_path, 'w') as rsync_filelist_file:
            rsync_filelist_file.write('\n'.join([str(file) for file in local_transfer_filelist]))
    except IOError:
        logging.error("Error Saving temporary rsync filelist file")

        # Cleanup
        shutil.rmtree(tmpdir)

        return {'verdict': False, 'reason': "Error Saving temporary rsync filelist file", 'files': files }

    # Build transfer command
    command = ['rsync', '-tri', '--files-from=' + rsync_filelist_path, publicdata_dir + '/', os.path.join(gearman_worker.cruise_dir, gearman_worker.ovdm.get_required_extra_directory_by_name('From_PublicData')['destDir'])]
    logging.debug("Command: %s", ' '.join(command))

    file_count = 1
    total_files = len(files['include'])

    # Transfer files
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")

    for line in lines_iterator:
        logging.debug("Line: %s", line) # yield line
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['new'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(round(20 + (70*file_count/total_files),0)), 100)
            file_count += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['updated'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(round(20 + (70*file_count/total_files),0)), 100)
            file_count += 1

        if gearman_worker.stop:
            logging.error("Stopping rsync transfer")
            popen.terminate()
            break

    # Cleanup
    shutil.rmtree(tmpdir)
    return {'verdict': True, 'files':files }


class OVDMGearmanWorker(python3_gearman.GearmanWorker):
    """
    Class for the current Gearman worker
    """

    def __init__(self):
        self.stop = False
        self.ovdm = OpenVDM()
        self.task = None
        self.cruise_id = self.ovdm.get_cruise_id()
        self.cruise_start_date = self.ovdm.get_cruise_start_date()
        self.shipboard_data_warehouse_config = self.ovdm.get_shipboard_data_warehouse_config()
        self.cruise_dir = os.path.join(self.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], self.cruise_id)
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
#            self.ovdm.track_gearman_job(task_lookup[current_job.task], os.getpid(), current_job.handle)

        logging.info("Job: %s (%s) started at: %s", self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime()))

        self.cruise_id = payload_obj['cruiseID'] if 'cruiseID' in payload_obj else self.ovdm.get_cruise_id()
        self.cruise_start_date = payload_obj['cruiseStartDate'] if 'cruiseStartDate' in payload_obj else self.ovdm.get_cruise_start_date()
        self.shipboard_data_warehouse_config = self.ovdm.get_shipboard_data_warehouse_config()
        self.cruise_dir = os.path.join(self.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], self.cruise_id)

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
            'cruiseStartDate': self.cruise_start_date
        }

        if current_job.task == "setupNewCruise":

            gm_client = python3_gearman.GearmanClient([self.ovdm.get_gearman_server()])

            for task in self.ovdm.get_tasks_for_hook('setupNewCruise'):
                logging.info("Adding post task: %s", task)
                gm_client.submit_job(task, json.dumps(job_data), background=True)

        elif current_job.task == "finalizeCurrentCruise":

            gm_client = python3_gearman.GearmanClient([self.ovdm.get_gearman_server()])

            for task in self.ovdm.get_tasks_for_hook('finalizeCurrentCruise'):
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


def task_setup_new_cruise(gearman_worker, gearman_job): # pylint: disable=too-many-return-statements,too-many-statements
    """
    Setup a new cruise
    """
    job_results = {'parts':[]}

    payload_obj = json.loads(gearman_job.data)
    logging.debug("Payload: %s", json.dumps(payload_obj, indent=2))

    ovdm_config_file_path = os.path.join(gearman_worker.cruise_dir, DEFAULT_CRUISE_CONFIG_FN)

    gearman_worker.send_job_status(gearman_job, 1, 10)

    gm_client = python3_gearman.GearmanClient([gearman_worker.ovdm.get_gearman_server()])

    logging.info("Set ownership/permissions for the CruiseData directory")
    completed_job_request = gm_client.submit_job("setCruiseDataDirectoryPermissions", gearman_job.data)

    result_obj = json.loads(completed_job_request.result)

    if result_obj['parts'][-1]['result'] != "Pass": # Final Verdict
        logging.error("Failed to lockdown the CruiseData directory")
        job_results['parts'].append({"partName": "Set ownership/permissions for CruiseData directory", "result": "Fail", "reason": result_obj['parts'][-1]['reason']})
        return json.dumps(job_results)

    job_results['parts'].append({"partName": "Set ownership/permissions for CruiseData directory", "result": "Pass"})

    logging.info("Creating cruise data directory")
    completed_job_request = gm_client.submit_job("createCruiseDirectory", gearman_job.data)

    result_obj = json.loads(completed_job_request.result)

    if result_obj['parts'][-1]['result'] != "Pass": # Final Verdict
        logging.error("Failed to create cruise data directory")
        job_results['parts'].append({"partName": "Create cruise data directory structure", "result": "Fail", "reason": result_obj['parts'][-1]['reason']})
        return json.dumps(job_results)

    job_results['parts'].append({"partName": "Create cruise data directory structure", "result": "Pass"})

    gearman_worker.send_job_status(gearman_job, 5, 10)

    #build OpenVDM Config file
    logging.info("Exporting Cruise Configuration")
    output_results = export_ovdm_config(gearman_worker, ovdm_config_file_path)

    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Export OpenVDM config data to file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    job_results['parts'].append({"partName": "Export OpenVDM config data to file", "result": "Pass"})

    output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], ovdm_config_file_path)

    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Set OpenVDM config file ownership/permissions", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 7, 10)

    logging.info("Creating MD5 summary files")
    completed_job_request = gm_client.submit_job("rebuildMD5Summary", gearman_job.data)

    result_obj = json.loads(completed_job_request.result)

    if result_obj['parts'][-1]['result'] != "Pass": # Final Verdict
        logging.error("Failed to create MD5 summary files")
        job_results['parts'].append({"partName": "Create MD5 summary files", "result": "Fail", "reason": result_obj['parts'][-1]['reason']})
        return json.dumps(job_results)

    job_results['parts'].append({"partName": "Create MD5 summary files", "result": "Pass"})

    gearman_worker.send_job_status(gearman_job, 8, 10)

    logging.info("Creating data dashboard directory structure and manifest file")
    completed_job_request = gm_client.submit_job("rebuildDataDashboard", gearman_job.data)

    result_obj = json.loads(completed_job_request.result)

    if result_obj['parts'][-1]['result'] != "Pass": # Final Verdict
        logging.error("Failed to create data dashboard directory structure and/or manifest file")
        job_results['parts'].append({"partName": "Create data dashboard directory structure and manifest file", "result": "Fail", "reason": result_obj['parts'][-1]['reason']})
        return json.dumps(job_results)

    job_results['parts'].append({"partName": "Create data dashboard directory structure and manifest file", "result": "Pass"})

    gearman_worker.send_job_status(gearman_job, 9, 10)

    logging.info("Updating Cruise Size")
    cruise_size_proc = subprocess.run(['du','-sb', gearman_worker.cruise_dir], capture_output=True, text=True, check=False)
    if cruise_size_proc.returncode == 0:
        logging.info("Cruise Size: %s", cruise_size_proc.stdout.split()[0])
        gearman_worker.ovdm.set_cruise_size(cruise_size_proc.stdout.split()[0])
    else:
        gearman_worker.ovdm.set_cruise_size("0")

    gearman_worker.ovdm.set_lowering_size("0")

    gearman_worker.send_job_status(gearman_job, 10, 10)

    return json.dumps(job_results)

def task_finalize_current_cruise(gearman_worker, gearman_job): # pylint: disable=too-many-return-statements,too-many-statements
    """
    Finalize the current cruise
    """
    job_results = {'parts':[]}

    gearman_worker.send_job_status(gearman_job, 1, 10)

    publicdata_dir = gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehousePublicDataDir']
    from_publicdata_dir = os.path.join(gearman_worker.cruise_dir, gearman_worker.ovdm.get_required_extra_directory_by_name('From_PublicData')['destDir'])

    ovdm_config_file_path = os.path.join(gearman_worker.cruise_dir, DEFAULT_CRUISE_CONFIG_FN)

    if not os.path.exists(gearman_worker.cruise_dir):
        job_results['parts'].append({"partName": "Verify cruise directory exists", "result": "Fail", "reason": "Cruise directory: " + gearman_worker.cruise_dir + " could not be found"})
        return json.dumps(job_results)

    job_results['parts'].append({"partName": "Verify cruise directory exists", "result": "Pass"})

    gearman_worker.send_job_status(gearman_job, 2, 10)
    logging.info("Queuing Collection System Transfers")

    gm_client = python3_gearman.GearmanClient([gearman_worker.ovdm.get_gearman_server()])

    gm_data = {
        'cruiseID': gearman_worker.cruise_id,
        'cruiseStartDate': gearman_worker.cruise_start_date,
        'systemStatus': "On",
        'collectionSystemTransfer': {}
    }

    collection_system_transfer_jobs = []

    collection_system_transfers = gearman_worker.ovdm.get_active_collection_system_transfers(lowering=False)

    for collection_system_transfer in collection_system_transfers:

        logging.debug("Queuing runCollectionSystemTransfer job for %s", collection_system_transfer['name'])
        gm_data['collectionSystemTransfer']['collectionSystemTransferID'] = collection_system_transfer['collectionSystemTransferID']

        collection_system_transfer_jobs.append( {"task": "runCollectionSystemTransfer", "data": json.dumps(gm_data)} )

    gearman_worker.send_job_status(gearman_job, 3, 10)

    if len(collection_system_transfer_jobs) > 0:
        logging.info("Submitting runCollectionSystemTransfer jobs")
        submitted_job_request = gm_client.submit_multiple_jobs(collection_system_transfer_jobs, background=False, wait_until_complete=False)

        gearman_worker.send_job_status(gearman_job, 4, 10)

        time.sleep(1)
        gm_client.wait_until_jobs_completed(submitted_job_request)
        logging.info("Completed runCollectionSystemTransfers jobs")

    gearman_worker.send_job_status(gearman_job, 5, 10)

    logging.info("Transferring files from PublicData to the cruise data directory")

    logging.debug("Verify From_PublicData directory exists within the cruise data directory")
    if not os.path.exists(from_publicdata_dir):
        job_results['parts'].append({"partName": "Verify From_PublicData directory exists", "result": "Fail", "reason": "From_PublicData directory: " + from_publicdata_dir + " could not be found"})
        return json.dumps(job_results)

    job_results['parts'].append({"partName": "Verify From_PublicData directory exists", "result": "Pass"})

    logging.debug("Verify PublicData Directory exists")
    if not os.path.exists(publicdata_dir):
        job_results['parts'].append({"partName": "Verify PublicData directory exists", "result": "Fail", "reason": "PublicData directory: " + publicdata_dir+ " could not be found"})
        return json.dumps(job_results)

    job_results['parts'].append({"partName": "Verify PublicData directory exists", "result": "Pass"})

    logging.debug("Transferring files")
    output_results = transfer_publicdata_dir(gearman_worker, gearman_job)
    logging.debug("Transfer Complete")

    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Transfer PublicData files", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    job_results['parts'].append({"partName": "Transfer PublicData files", "result": "Pass"})

    files = output_results['files']

    logging.debug("PublicData Files Transferred: %s", json.dumps(files, indent=2))

    logging.info("Clearing files from PublicData")
    output_results = clear_directory(publicdata_dir)
    logging.debug("Clearing Complete")

    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Clear out PublicData files", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    job_results['parts'].append({"partName": "Clear out PublicData files", "result": "Pass"})

    gearman_worker.send_job_status(gearman_job, 9, 10)

    if len(files['new']) > 0 or len(files['updated']) > 0:

        output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], from_publicdata_dir)

        if not output_results['verdict']:
            job_results['parts'].append({"partName": "Set file/directory ownership/permissions", "result": "Fail", "reason": output_results['reason']})
            return json.dumps(job_results)

        job_results['parts'].append({"partName": "Set file/directory ownership/permissions", "result": "Pass"})

    gearman_worker.send_job_status(gearman_job, 95, 100)

    #build OpenVDM Config file
    logging.info("Exporting OpenVDM Configuration")
    output_results = export_ovdm_config(gearman_worker, ovdm_config_file_path, finalize=True)

    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Export OpenVDM config data to file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    job_results['parts'].append({"partName": "Export OpenVDM config data to file", "result": "Pass"})

    output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], ovdm_config_file_path)

    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Set OpenVDM config file ownership/permissions", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    job_results['parts'].append({"partName": "Set OpenVDM config file ownership/permissions", "result": "Pass"})

    logging.info("Initiating MD5 Summary Task")

    gm_data = {
        'cruiseID': gearman_worker.cruise_id,
        'files': files
    }

    gm_data['files']['new'] = [from_publicdata_dir.replace(gearman_worker.cruise_dir, '') + '/' + filename for filename in gm_data['files']['new']]
    gm_data['files']['updated'] = [from_publicdata_dir.replace(gearman_worker.cruise_dir, '') + '/' + filename for filename in gm_data['files']['updated']]
    gm_data['files']['updated'].append(DEFAULT_CRUISE_CONFIG_FN)

    gm_client.submit_job("updateMD5Summary", json.dumps(gm_data))

    logging.debug("MD5 Summary Task Complete")

    # need to add code for cruise data transfers

    gearman_worker.send_job_status(gearman_job, 10, 10)
    return json.dumps(job_results)

def task_rsync_publicdata_to_cruise_data(gearman_worker, gearman_job):
    """
    Sync the contents of the PublicData share to the from_PublicData Extra Directory
    """
    job_results = {'parts':[]}

    publicdata_dir = gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehousePublicDataDir']
    from_publicdata_dir = os.path.join(gearman_worker.cruise_dir, gearman_worker.ovdm.get_required_extra_directory_by_name('From_PublicData')['destDir'])

    gearman_worker.send_job_status(gearman_job, 1, 10)

    if os.path.exists(from_publicdata_dir):
        job_results['parts'].append({"partName": "Verify From_PublicData directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify From_PublicData directory exists", "result": "Fail", "reason": "Unable to locate the From_PublicData directory: " + from_publicdata_dir})
        return json.dumps(job_results)

    if os.path.exists(publicdata_dir):
        job_results['parts'].append({"partName": "Verify PublicData directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify PublicData directory exists", "result": "Fail", "reason": "Unable to locate the PublicData directory: " + publicdata_dir})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 5, 10)

    logging.info("Transferring files from PublicData to the cruise data directory")
    output_results = transfer_publicdata_dir(gearman_worker, gearman_job)

    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Transfer files", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    job_results['parts'].append({"partName": "Transfer files", "result": "Pass"})

    files = output_results['files']

    logging.debug("Files Transferred: %s",json.dumps(files, indent=2))

    gearman_worker.send_job_status(gearman_job, 8, 10)

    if len(files['new']) > 0 or len(files['updated']) > 0:

        logging.info("Setting file permissions")
        output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], from_publicdata_dir)

        if output_results['verdict']:
            job_results['parts'].append({"partName": "Set file/directory ownership/permissions", "result": "Pass"})
        else:
            job_results['parts'].append({"partName": "Set file/directory ownership/permissions", "result": "Fail", "reason": output_results['reason']})
            return json.dumps(job_results)

        gearman_worker.send_job_status(gearman_job, 9, 100)

        logging.info("Initiating MD5 Summary Task")

        gm_client = python3_gearman.GearmanClient([gearman_worker.ovdm.get_gearman_server()])
        gm_data = {}
        gm_data['cruiseID'] = gearman_worker.cruise_id
        gm_data['files'] = files
        gm_data['files']['new'] = [os.path.join(from_publicdata_dir,filename) for filename in gm_data['files']['new']]
        gm_data['files']['updated'] = [os.path.join(from_publicdata_dir,filename) for filename in gm_data['files']['updated']]

        gm_client.submit_job("updateMD5Summary", json.dumps(gm_data))

        logging.info("MD5 Summary Task Complete")

    # need to verify update MD5 completed successfully

    gearman_worker.send_job_status(gearman_job, 10, 10)
    return json.dumps(job_results)


def task_export_ovdm_config(gearman_worker, gearman_job):
    """
    Export the OpenVDM configuration to file
    """
    job_results = {'parts':[]}

    ovdm_config_file_path = os.path.join(gearman_worker.cruise_dir, DEFAULT_CRUISE_CONFIG_FN)

    gearman_worker.send_job_status(gearman_job, 1, 10)

    logging.info("Verifying cruise directory exists")
    if os.path.exists(gearman_worker.cruise_dir):
        job_results['parts'].append({"partName": "Verify cruise directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify cruise directory exists", "result": "Fail", "reason": "Unable to locate the cruise directory: " + gearman_worker.cruise_dir})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 3, 10)

    #build OpenVDM Config file
    logging.info("Exporting OpenVDM Configuration")
    output_results = export_ovdm_config(gearman_worker, ovdm_config_file_path)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Export OpenVDM config data to file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Export OpenVDM config data to file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 6, 10)

    logging.info("Setting file ownership/permissions")
    output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], ovdm_config_file_path)

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
    parser = argparse.ArgumentParser(description='Handle Cruise-Level tasks')
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

    logging.info("\tTask: setupNewCruise")
    new_worker.register_task("setupNewCruise", task_setup_new_cruise)

    logging.info("\tTask: finalizeCurrentCruise")
    new_worker.register_task("finalizeCurrentCruise", task_finalize_current_cruise)

    logging.info("\tTask: exportOVDMConfig")
    new_worker.register_task("exportOVDMConfig", task_export_ovdm_config)

    logging.info("\tTask: rsyncPublicDataToCruiseData")
    new_worker.register_task("rsyncPublicDataToCruiseData", task_rsync_publicdata_to_cruise_data)

    logging.info("Waiting for jobs...")
    new_worker.work()
