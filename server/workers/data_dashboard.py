
#!/usr/bin/env python3
"""
FILE:  OVDM_dataDashboard.py

DESCRIPTION:  Gearman worker tha handles the creation and update of OVDM data
    dashboard objects.

     BUGS:
    NOTES:
   AUTHOR:  Webb Pinner
  COMPANY:  Capable Solutions
  VERSION:  2.4
  CREATED:  2015-01-01
 REVISION:  2020-12-27

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
import signal
import time
import subprocess
import logging
from os.path import dirname, realpath
import python3_gearman

sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.utils.set_owner_group_permissions import set_owner_group_permissions
from server.utils.output_json_data_to_file import output_json_data_to_file
from server.lib.openvdm import OpenVDM, DEFAULT_DATA_DASHBOARD_MANIFEST_FN

PYTHON_BINARY = os.path.join(dirname(dirname(dirname(realpath(__file__)))), 'venv/bin/python')

customTasks = [
    {
        "taskID": "0",
        "name": "updateDataDashboard",
        "longName": "Updating Data Dashboard",
    }
]

def build_filelist(source_dir):
    """
    return the list of files in the source directory
    """

    logging.debug("sourceDir: %s", source_dir)

    return_files = []
    for root, _, filenames in os.walk(source_dir):
        for filename in filenames:
            return_files.append(os.path.join(root, filename))

    return_files = [filename.replace(source_dir + '/', '', 1) for filename in return_files]
    return return_files


class OVDMGearmanWorker(python3_gearman.GearmanWorker): # pylint: disable=too-many-instance-attributes
    """
    Class for the current Gearman worker
    """

    def __init__(self):
        self.stop = False
        self.ovdm = OpenVDM()
        self.task = None
        self.shipboard_data_warehouse_config = self.ovdm.get_shipboard_data_warehouse_config()
        self.cruise_id = self.ovdm.get_cruise_id()
        self.cruise_dir = os.path.join(self.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], self.cruise_id)
        self.lowering_id = self.ovdm.get_cruise_id()
        self.lowering_dir = os.path.join(self.cruise_dir, self.shipboard_data_warehouse_config['loweringDataBaseDir'], self.lowering_id) if self.lowering_id else None
        self.data_dashboard_dir = os.path.join(self.cruise_dir, self.ovdm.get_required_extra_directory_by_name('Dashboard_Data')['destDir'])
        self.data_dashboard_manifest_file_path = os.path.join(self.data_dashboard_dir, DEFAULT_DATA_DASHBOARD_MANIFEST_FN)

        self.collection_system_transfer = {}

        super().__init__(host_list=[self.ovdm.get_gearman_server()])

    @staticmethod
    def get_custom_task(current_job):
        """
        Retrieve task metadata
        """
        task = list(filter(lambda task: task['name'] == current_job.task, customTasks))
        return task[0] if len(task) > 0 else None

    def on_job_execute(self, current_job):
        """
        Function run whenever a new job arrives
        """

        logging.debug("current_job: %s", current_job)

        payload_obj = json.loads(current_job.data)

        self.task = self.get_custom_task(current_job) if self.get_custom_task(current_job) is not None else self.ovdm.get_task_by_name(current_job.task)
        logging.debug("task: %s", self.task)

        if int(self.task['taskID']) > 0:
            self.ovdm.set_running_task(self.task['taskID'], os.getpid(), current_job.handle)
        else:
            self.ovdm.track_gearman_job(self.task['longName'], os.getpid(), current_job.handle)

        logging.info("Job: %s (%s) started at: %s", self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime()))

        self.shipboard_data_warehouse_config = self.ovdm.get_shipboard_data_warehouse_config()
        self.cruise_id = payload_obj['cruiseID'] if 'cruiseID' in payload_obj else self.ovdm.get_cruise_id()
        self.cruise_dir = os.path.join(self.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], self.cruise_id)
        self.lowering_id = payload_obj['loweringID'] if 'loweringID' in payload_obj else self.ovdm.get_lowering_id()
        self.lowering_dir = os.path.join(self.cruise_dir, self.shipboard_data_warehouse_config['loweringDataBaseDir'], self.lowering_id) if self.lowering_id else None
        self.collection_system_transfer = self.ovdm.get_collection_system_transfer(payload_obj['collectionSystemTransferID']) if 'collectionSystemTransferID' in payload_obj else { 'name': "Unknown" }
        self.data_dashboard_dir = os.path.join(self.cruise_dir, self.ovdm.get_required_extra_directory_by_name('Dashboard_Data')['destDir'])
        self.data_dashboard_manifest_file_path = os.path.join(self.data_dashboard_dir, DEFAULT_DATA_DASHBOARD_MANIFEST_FN)

        return super().on_job_execute(current_job)


    def on_job_exception(self, current_job, exc_info):
        """
        Function run whenever the current job has an exception
        """

        logging.error("Job: %s (%s) failed at: %s", self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime()))

        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail", "reason": "Unknown, contact Webb :-)"}]))
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

        logging.debug("Preparing subsequent Gearman jobs")

        job_data = {
            'cruiseID': self.cruise_id,
            'loweringID': self.lowering_id,
            'files': results_obj['files']
        }

        if current_job.task == 'updateDataDashboard':

            gm_client = python3_gearman.GearmanClient([self.ovdm.get_gearman_server()])

            payload_obj = json.loads(current_job.data)
            job_data['collectionSystemTransferID'] = payload_obj['collectionSystemTransferID']

            for task in self.ovdm.get_tasks_for_hook(current_job.task):
                logging.info("Adding post task: %s", task)
                gm_client.submit_job(task, json.dumps(job_data), background=True)

        elif current_job.task == 'rebuildDataDashboard':

            gm_client = python3_gearman.GearmanClient([self.ovdm.get_gearman_server()])

            for task in self.ovdm.get_tasks_for_hook(current_job.task):
                logging.info("Adding post task: %s", task)
                gm_client.submit_job(task, json.dumps(job_data), background=True)

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


def task_update_data_dashboard(gearman_worker, gearman_job): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """
    Update the existing dashboard files with new/updated raw data
    """
    job_results = {
        'parts':[],
        'files':{
            'new':[],
            'updated':[]
        }
    }

    payload_obj = json.loads(gearman_job.data)
    logging.debug('Payload: %s', json.dumps(payload_obj, indent=2))

    gearman_worker.send_job_status(gearman_job, 5, 100)

    logging.info('Collection System Transfer: %s', gearman_worker.collection_system_transfer['name'])

    new_manifest_entries = []
    remove_manifest_entries = []

    #check for processing file
    processing_script_filename = os.path.join(gearman_worker.ovdm.get_dashboard_data_processing_script_dir(), gearman_worker.collection_system_transfer['name'].replace(' ','') + gearman_worker.ovdm.get_dashboard_data_processing_script_suffix())
    logging.debug("Processing Script Filename: %s", processing_script_filename)

    if os.path.isfile(processing_script_filename):
        job_results['parts'].append({"partName": "Dashboard Processing File Located", "result": "Pass"})
    else:
        logging.warning("Processing script not found: %s", processing_script_filename)
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 10, 100)

    #build filelist
    filelist = []

    if payload_obj['files']['new'] or payload_obj['files']['updated']:
        filelist = payload_obj['files']['new']
        filelist += payload_obj['files']['updated']
        logging.debug('File List: %s', json.dumps(filelist, indent=2))
        job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Pass"})

    else:
        logging.warning("No new or updated files to process")
        job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Pass"})
        return json.dumps(job_results)

    file_count = len(filelist)
    file_index = 0
    for filename in filelist:  # pylint: disable=too-many-nested-blocks

        if gearman_worker.stop:
            break

        logging.info("Processing file: %s", filename)
        json_filename = os.path.splitext(filename)[0] + '.json'
        raw_filepath = os.path.join(gearman_worker.cruise_dir, filename)
        json_filepath = os.path.join(gearman_worker.data_dashboard_dir, json_filename)

        if not os.path.isfile(raw_filepath):
            job_results['parts'].append({"partName": "Verify data file exists", "result": "Fail", "reason": "Unable to find data file: " + filename})
            logging.warning("File not found %s, skipping", filename)
            continue

        if os.stat(raw_filepath).st_size == 0:
            logging.warning("File is empty %s, skipping", filename)
            continue

        command = [PYTHON_BINARY, processing_script_filename, '--dataType', raw_filepath]

        logging.debug("DataType Retrieval Command: %s", ' '.join(command))

        datatype_proc = subprocess.run(command, capture_output=True, text=True, check=False)

        if datatype_proc.stdout:
            dd_type = datatype_proc.stdout.rstrip('\n')
            logging.debug("DataType found to be: %s", dd_type)

            command = [PYTHON_BINARY, processing_script_filename, raw_filepath]

            logging.debug("Data Processing Command: %s", ' '.join(command))

            data_proc = subprocess.run(command, capture_output=True, text=True, check=False)

            if data_proc.stdout:
                try:
                    logging.debug("Verifying output")
                    out_obj = json.loads(data_proc.stdout)
                except Exception as err:
                    logging.error("Error parsing JSON output from file: %s", filename)
                    logging.debug(str(err))
                    job_results['parts'].append({"partName": "Parsing JSON output from file " + filename, "result": "Fail", "reason": "Error parsing JSON output from file: " + filename})
                    continue
                else:
                    if not out_obj:
                        error_title = 'Datafile Parsing error'
                        error_body = "Parser returned no output. Parsing command: {}", ' '.join(command)
                        logging.error("%s: %s", error_title, error_body)
                        gearman_worker.ovdm.send_msg(error_title,error_body)
                    elif 'error' in out_obj:
                        error_title = 'Datafile Parsing error'
                        error_body = out_obj['error']
                        logging.error("%s: %s", error_title, error_body)
                        gearman_worker.ovdm.send_msg(error_title,error_body)
                    else:
                        output_results = output_json_data_to_file(json_filepath, out_obj)

                        if output_results['verdict']:
                            job_results['parts'].append({"partName": "Writing DashboardData file: " + filename, "result": "Pass"})
                        else:
                            error_title = 'Data Dashboard Processing failed'
                            error_body = "Error Writing DashboardData file: " + filename + ". Reason: " + output_results['reason']
                            logging.error("%s: %s", error_title, error_body)
                            gearman_worker.ovdm.send_msg(error_title,error_body)
                            job_results['parts'].append({"partName": "Writing Dashboard file: " + filename, "result": "Fail", "reason": output_results['reason']})

                        new_manifest_entries.append({"type":dd_type, "dd_json": json_filepath.replace(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'] + '/',''), "raw_data": raw_filepath.replace(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'] + '/','')})
            else:
                error_title = 'Data Dashboard Processing failed'
                error_body = 'No JSON output recieved from file.  Parsing Command: ' + ' '.join(command)
                logging.error("%s: %s", error_title, error_body)
                gearman_worker.ovdm.send_msg(error_title,error_body)
                remove_manifest_entries.append({"dd_json": json_filepath.replace(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'] + '/',''), "raw_data": raw_filepath.replace(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'] + '/','')})

                #job_results['parts'].append({"partName": "Parsing JSON output from file " + filename, "result": "Fail"})
                if data_proc.stderr:
                    logging.error("Err: %s", data_proc.stderr)
        else:
            logging.warning("File is of unknown datatype: %s", raw_filepath)
            remove_manifest_entries.append({"dd_json": json_filepath.replace(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'] + '/',''), "raw_data":raw_filepath.replace(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'] + '/','')})

            if datatype_proc.stderr:
                logging.error("Err: %s", datatype_proc.stderr)

        gearman_worker.send_job_status(gearman_job, int(10 + 70*float(file_index)/float(file_count)), 100)
        file_index += 1

    gearman_worker.send_job_status(gearman_job, 8, 10)

    if len(new_manifest_entries) > 0:
        logging.info("Updating Manifest file: %s", gearman_worker.data_dashboard_manifest_file_path)

        rows_removed = 0

        existing_manifest_entries = []

        try:
            with open(gearman_worker.data_dashboard_manifest_file_path, 'r') as dashboard_manifest_file:
                existing_manifest_entries = json.load(dashboard_manifest_file)

            job_results['parts'].append({"partName": "Reading pre-existing Dashboard manifest file", "result": "Pass"})

        except IOError:
            logging.error("Error Reading Dashboard Manifest file %s", gearman_worker.data_dashboard_manifest_file_path)
            job_results['parts'].append({"partName": "Reading pre-existing Dashboard manifest file", "result": "Fail", "reason": "Error reading dashboard manifest file: " + gearman_worker.data_dashboard_manifest_file_path})
            return json.dumps(job_results)

        logging.debug("Entries to remove: %s", json.dumps(remove_manifest_entries, indent=2))
        for remove_entry in remove_manifest_entries:
            for idx, existing_entry in enumerate(existing_manifest_entries):
                if remove_entry['raw_data'] == existing_entry['raw_data']:
                    del existing_manifest_entries[idx]
                    rows_removed += 1

                    if os.path.isfile(os.path.join(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'],remove_entry['dd_json'])):
                        logging.info("Deleting orphaned dd_json file %s", os.path.join(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'],remove_entry['dd_json']))
                        os.remove(os.path.join(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'],remove_entry['dd_json']))
                    break

        logging.debug("Entries to add/update: %s", json.dumps(new_manifest_entries, indent=2))
        for new_entry in new_manifest_entries:
            updated = False
            for existing_entry in existing_manifest_entries:
                if new_entry['raw_data'] == existing_entry['raw_data']:
                    updated = True
                    job_results['files']['updated'].append(new_entry['dd_json'].replace(gearman_worker.cruise_id + '/',''))
                    break

            if not updated: #added
                job_results['files']['new'].append(new_entry['dd_json'].replace(gearman_worker.cruise_id + '/',''))
                existing_manifest_entries.append(new_entry)

        if len(job_results['files']['new']) > 0:
            logging.info("%s row(s) added", len(job_results['files']['new']))
        if len(job_results['files']['updated']) > 0:
            logging.info("%s row(s) updated", len(job_results['files']['updated']))
        if rows_removed:
            logging.info("%s row(s) removed", rows_removed)

        output_results = output_json_data_to_file(gearman_worker.data_dashboard_manifest_file_path, existing_manifest_entries)

        if not output_results['verdict']:
            logging.error("Error Writing Dashboard manifest file: %s", gearman_worker.data_dashboard_manifest_file_path)
            job_results['parts'].append({"partName": "Writing Dashboard manifest file", "result": "Fail", "reason": output_results['reason']})
            return json.dumps(job_results)

        job_results['parts'].append({"partName": "Writing Dashboard manifest file", "result": "Pass"})
        job_results['files']['updated'].append(os.path.join(gearman_worker.ovdm.get_required_extra_directory_by_name('Dashboard_Data')['destDir'], DEFAULT_DATA_DASHBOARD_MANIFEST_FN))

        gearman_worker.send_job_status(gearman_job, 9, 10)

        logging.info("Setting file ownership/permissions")
        output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], gearman_worker.data_dashboard_dir)

        if output_results['verdict']:
            job_results['parts'].append({"partName": "Set file/directory ownership", "result": "Pass"})
        else:
            job_results['parts'].append({"partName": "Set file/directory ownership", "result": "Fail", "reason": output_results['reason']})
            return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 10, 10)

    return json.dumps(job_results)


def task_rebuild_data_dashboard(gearman_worker, gearman_job): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """
    Rebuild the existing dashboard files
    """

    job_results = {
        'parts':[],
        'files':{
            'new':[],
            'updated':[]
        }
    }

    payload_obj = json.loads(gearman_job.data)
    logging.debug('Payload: %s', json.dumps(payload_obj, indent=2))


    if os.path.exists(gearman_worker.data_dashboard_dir):
        job_results['parts'].append({"partName": "Verify Data Dashboard Directory exists", "result": "Pass"})
    else:
        logging.error("Data dashboard directory not found: %s", gearman_worker.data_dashboard_dir)
        job_results['parts'].append({"partName": "Verify Data Dashboard Directory exists", "result": "Fail", "reason": "Unable to locate the data dashboard directory: " + gearman_worker.data_dashboard_dir})
        return json.dumps(job_results)

    collection_system_transfers = gearman_worker.ovdm.get_active_collection_system_transfers()

    gearman_worker.send_job_status(gearman_job, 1, 100)

    new_manifest_entries = []

    collection_system_transfer_count = len(collection_system_transfers)
    collection_system_transfer_index = 0
    for collection_system_transfer in collection_system_transfers:  # pylint: disable=too-many-nested-blocks

        logging.info('Processing data from: %s', collection_system_transfer['name'])

        processing_script_filename = os.path.join(gearman_worker.ovdm.get_dashboard_data_processing_script_dir(), collection_system_transfer['name'].replace(' ','-') + gearman_worker.ovdm.get_dashboard_data_processing_script_suffix())
        logging.debug("Processing Script Filename: %s", processing_script_filename)

        if not os.path.isfile(processing_script_filename):
            logging.warning("Processing script for collection system %s not found, moving on.", collection_system_transfer['name'])
            gearman_worker.send_job_status(gearman_job, int(10 + (80*float(collection_system_transfer_index)/float(collection_system_transfer_count))), 100)
            collection_system_transfer_index += 1
            continue

        # collection_system_transferOutputDir = os.path.join(gearman_worker.data_dashboard_dir, collection_system_transfer['destDir'])

        #build filelist
        filelist = []
        if collection_system_transfer['cruiseOrLowering'] == "0":
            collection_system_transfer_input_dir = os.path.join(gearman_worker.cruise_dir, collection_system_transfer['destDir'])
            filelist.extend(build_filelist(collection_system_transfer_input_dir))
            filelist = [os.path.join(collection_system_transfer['destDir'], filename) for filename in filelist]

        else:
            lowerings = gearman_worker.ovdm.get_lowerings()
            lowering_base_dir = gearman_worker.shipboard_data_warehouse_config['loweringDataBaseDir']

            for lowering in lowerings:
                collection_system_transfer_input_dir = os.path.join(gearman_worker.cruise_dir, lowering_base_dir, lowering, collection_system_transfer['destDir'])
                lowering_filelist = build_filelist(collection_system_transfer_input_dir)
                filelist.extend([os.path.join(lowering_base_dir, lowering, collection_system_transfer['destDir'], filename) for filename in lowering_filelist])

        logging.debug("FileList: %s", json.dumps(filelist, indent=2))

        file_count = len(filelist)
        file_index = 0
        logging.info("%s file(s) to process", file_count)

        for filename in filelist:

            if gearman_worker.stop:
                break

            logging.info("Processing file: %s", filename)
            json_filename = os.path.splitext(filename)[0] + '.json'
            logging.debug("jsonFileName: %s", json_filename)
            raw_filepath = os.path.join(gearman_worker.cruise_dir, filename)
            logging.debug("rawFilePath: %s", raw_filepath)
            json_filepath = os.path.join(gearman_worker.data_dashboard_dir, json_filename)
            logging.debug("jsonFilePath: %s", json_filepath)

            if os.stat(raw_filepath).st_size == 0:
                logging.warning("File %s is empty", filename)
                continue

            command = [PYTHON_BINARY, processing_script_filename, '--dataType', raw_filepath]

            logging.debug("Get Datatype Command: %s", ' '.join(command))

            datatype_proc = subprocess.run(command, capture_output=True, text=True, check=False)

            if datatype_proc.stdout:
                dd_type = datatype_proc.stdout.rstrip('\n')
                logging.debug("Found to be type: %s", dd_type)

                command = [PYTHON_BINARY, processing_script_filename, raw_filepath]

                logging.debug("Processing Command: %s", ' '.join(command))

                data_proc = subprocess.run(command, capture_output=True, text=True, check=False)

                if data_proc.stdout:
                    try:
                        logging.debug("Parsing output")
                        out_obj = json.loads(data_proc.stdout)
                    except Exception as err:
                        logging.error(str(err))
                        error_title = 'Error parsing output'
                        error_body = 'Invalid JSON output recieved from processing. Command: ' + ' '.join(command)
                        logging.error("%s: %s", error_title, error_body)
                        gearman_worker.ovdm.send_msg(error_title, error_body)
                        job_results['parts'].append({"partName": "Parsing JSON output " + filename, "result": "Fail", "reason": error_title + ':' + error_body})
                    else:
                        if 'error' in out_obj:
                            error_title = 'Error processing file'
                            error_body = out_obj['error']
                            logging.error("%s: %s", error_title, error_body)
                            gearman_worker.ovdm.send_msg(error_title, error_body)
                            job_results['parts'].append({"partName": "Processing Datafile " + filename, "result": "Fail", "reason": error_title + ':' + error_body})

                        else:
                            #job_results['parts'].append({"partName": "Processing Datafile " + filename, "result": "Pass"})
                            output_results = output_json_data_to_file(json_filepath, out_obj)

                            if output_results['verdict']:
                                job_results['parts'].append({"partName": "Writing DashboardData file: " + filename, "result": "Pass"})
                            else:
                                error_title = 'Error writing file'
                                error_body = "Error Writing DashboardData file: " + filename
                                logging.error("%s: %s", error_title, error_body)
                                gearman_worker.ovdm.send_msg(error_title, error_body)

                                job_results['parts'].append({"partName": "Writing Dashboard file: " + filename, "result": "Fail", "reason": output_results['verdict']})

                            new_manifest_entries.append({"type":dd_type, "dd_json": json_filepath.replace(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'] + '/',''), "raw_data": raw_filepath.replace(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'] + '/','')})
                else:
                    error_title = 'Error processing file'
                    error_body = 'No JSON output recieved from file. Processing Command: ' + ' '.join(command)
                    logging.error("%s: %s", error_title, error_body)
                    gearman_worker.ovdm.send_msg(error_title, error_body)
                    job_results['parts'].append({"partName": "Parsing JSON output from file " + filename, "result": "Fail", "reason": error_title + ': ' + error_body})

                    if data_proc.stderr:
                        logging.error('err: %s', data_proc.stderr)

            else:
                logging.warning("File is of unknown datatype, moving on")

                if datatype_proc.stderr:
                    logging.error('err: %s', datatype_proc.stderr)

            gearman_worker.send_job_status(gearman_job, int(10 + 70*float(file_index)/float(file_count)), 100)
            file_index += 1

        collection_system_transfer_index += 1

    gearman_worker.send_job_status(gearman_job, 90, 100)

    logging.info("Update Dashboard Manifest file")
    output_results = output_json_data_to_file(gearman_worker.data_dashboard_manifest_file_path, new_manifest_entries)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Updating manifest file", "result": "Pass"})
    else:
        logging.error("Error updating manifest file %s", gearman_worker.data_dashboard_manifest_file_path)
        job_results['parts'].append({"partName": "Updating manifest file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 95, 100)

    logging.info("Setting file ownership/permissions")
    output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], gearman_worker.data_dashboard_dir)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Pass"})
    else:
        logging.error("Error Setting file/directory ownership/permissions")
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 99, 100)

    data_dashboard_dest_dir = gearman_worker.ovdm.get_required_extra_directory_by_name('Dashboard_Data')['destDir']
    job_results['files']['updated'] = [os.path.join(data_dashboard_dest_dir, filepath) for filepath in build_filelist(gearman_worker.data_dashboard_dir)]# might need to remove cruise_dir from begining of filepaths

    gearman_worker.send_job_status(gearman_job, 10, 10)

    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle data dashboard related tasks')
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

    logging.info("\tTask: updateDataDashboard")
    new_worker.register_task("updateDataDashboard", task_update_data_dashboard)
    logging.info("\tTask: rebuildDataDashboard")
    new_worker.register_task("rebuildDataDashboard", task_rebuild_data_dashboard)

    logging.info("Waiting for jobs...")
    new_worker.work()
