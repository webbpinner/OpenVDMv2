#!/usr/bin/env python3
"""
FILE:  cruise_directory.py

DESCRIPTION:  Gearman worker the handles the tasks of creating a new cruise
    data directory and updating the cruise directory structure when additional
    subdirectories must be added.

     BUGS:
    NOTES:
   AUTHOR:  Webb Pinner
  COMPANY:  Capable Solutions
  VERSION:  2.5
  CREATED:  2015-01-01
 REVISION:  2020-12-26

LICENSE INFO: Open Vessel Data Management v2.5 (OpenVDMv2)
Copyright (C) OceanDataRat 2021

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
import errno
import json
import time
import signal
import logging
import python3_gearman

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.utils.set_owner_group_permissions import set_owner_group_permissions
from server.lib.openvdm import OpenVDM

CUSTOM_TASKS = [
    {
        "taskID": "0",
        "name": "createCruiseDirectory",
        "longName": "Creating Cruise Directory",
    },
    {
        "taskID": "0",
        "name": "setCruiseDataDirectoryPermissions",
        "longName": "Setting CruiseData Directory Permissions",
    }

]


def build_dest_dir(gearman_worker, dest_dir):
    """
    Replace any wildcards in the provided directory
    """
    return_dest_dir = dest_dir.replace('{loweringID}', gearman_worker.lowering_id)
    return_dest_dir = return_dest_dir.replace('{loweringDataBaseDir}', gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir'],)
    return_dest_dir = return_dest_dir.replace('{cruiseID}', gearman_worker.cruise_id)
    return return_dest_dir


def build_directorylist(gearman_worker):
    """
    build the list of directories to be created as part of creating the new
    cruise
    """

    return_directories = []

    if gearman_worker.ovdm.get_show_lowering_components():
        return_directories.append(os.path.join(gearman_worker.cruise_dir, gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir']))

    collection_system_transfers = gearman_worker.ovdm.get_active_collection_system_transfers()

    for collection_system_transfer in collection_system_transfers:
        if collection_system_transfer['enable'] == "1" and collection_system_transfer['cruiseOrLowering'] == "0":
            dest_dir = build_dest_dir(gearman_worker, collection_system_transfer['destDir'])
            return_directories.append(os.path.join(gearman_worker.cruise_dir, dest_dir))

    required_extra_directories = gearman_worker.ovdm.get_required_extra_directories()
    for required_extra_directory in required_extra_directories:
        dest_dir = build_dest_dir(gearman_worker, required_extra_directory['destDir'])
        return_directories.append(os.path.join(gearman_worker.cruise_dir, dest_dir))

    extra_directories = gearman_worker.ovdm.get_extra_directories()
    if extra_directories:
        for extra_directory in extra_directories:
            if extra_directory['enable'] == "1":
                dest_dir = build_dest_dir(gearman_worker, extra_directory['destDir'])
                return_directories.append(os.path.join(gearman_worker.cruise_dir, dest_dir))

    return return_directories


def create_directories(directorylist):
    """
    Create the directories in the provide directory list
    """

    reasons = []
    for directory in directorylist:
        try:
            os.makedirs(directory)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                logging.error("Unable to create directory: %s", directory)
                reasons.append("Unable to create directory: %s", directory)

    if len(reasons) > 0:
        return {'verdict': False, 'reason': '\n'.join(reasons)}

    return {'verdict': True}


def lockdown_directory(base_dir, exempt_dir):
    """
    Lockdown permissions on the base directory, skip the exempt directory if present
    """

    dir_contents = [ os.path.join(base_dir,f) for f in os.listdir(base_dir)]
    files = filter(os.path.isfile, dir_contents)
    for file in files:
        os.chmod(file, 0o600)

    directories = filter(os.path.isdir, dir_contents)
    for directory in directories:
        if not directory == exempt_dir:
            os.chmod(directory, 0o700)


class OVDMGearmanWorker(python3_gearman.GearmanWorker): # pylint: disable=too-many-instance-attributes
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
        self.lowering_id = self.ovdm.get_cruise_id()
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
        # else:
        #     self.ovdm.track_gearman_job(taskLookup[current_job.task], os.getpid(), current_job.handle)

        logging.info("Job: %s (%s) started at: %s", self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime()))

        self.cruise_id = payload_obj['cruiseID'] if 'cruiseID' in payload_obj else self.ovdm.get_cruise_id()
        self.cruise_dir = os.path.join(self.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], self.cruise_id)

        self.lowering_id = payload_obj['loweringID'] if 'loweringID' in payload_obj else self.ovdm.get_lowering_id()
        self.shipboard_data_warehouse_config = self.ovdm.get_shipboard_data_warehouse_config()

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


def task_create_cruise_directory(gearman_worker, gearman_job):
    """
    Setup the cruise directory for the specified cruise ID
    """

    job_results = {'parts':[]}

    payload_obj = json.loads(gearman_job.data)
    logging.debug("Payload: %s", json.dumps(payload_obj, indent=2))

    gearman_worker.send_job_status(gearman_job, 1, 10)

    if os.path.exists(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir']):
        job_results['parts'].append({"partName": "Verify Base Directory exists", "result": "Pass"})
    else:
        logging.error("Failed to find base directory: %s", gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'])
        job_results['parts'].append({"partName": "Verify Base Directory exists", "result": "Fail", "reason": "Failed to find base directory: " + gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir']})
        return json.dumps(job_results)


    if not os.path.exists(gearman_worker.cruise_dir):
        job_results['parts'].append({"partName": "Verify Cruise Directory does not exists", "result": "Pass"})
    else:
        logging.error("Cruise directory already exists: %s", gearman_worker.cruise_dir)
        job_results['parts'].append({"partName": "Verify Cruise Directory does not exists", "result": "Fail", "reason": "Cruise directory " + gearman_worker.cruise_dir + " already exists"})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 2, 10)

    directorylist = build_directorylist(gearman_worker)
    logging.debug("Directory List: %s", json.dumps(directorylist, indent=2))

    if len(directorylist) > 0:
        job_results['parts'].append({"partName": "Build Directory List", "result": "Pass"})
    else:
        logging.warning("Directory list is empty")
        job_results['parts'].append({"partName": "Build Directory List", "result": "Fail", "reason": "Empty list of directories to create"})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 5, 10)

    output_results = create_directories(directorylist)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Create Directories", "result": "Pass"})
    else:
        logging.error("Failed to create any/all of the cruise data directory structure")
        job_results['parts'].append({"partName": "Create Directories", "result": "Fail", "reason": output_results['reason']})

    gearman_worker.send_job_status(gearman_job, 7, 10)

    if gearman_worker.ovdm.show_only_current_cruise_dir():
        logging.info("Clear read permissions for all cruise directories")
        lockdown_directory(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], gearman_worker.cruise_dir)

        job_results['parts'].append({"partName": "Clear CruiseData Directory Read Permissions", "result": "Pass"})

    gearman_worker.send_job_status(gearman_job, 8, 10)

    output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], gearman_worker.cruise_dir)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set cruise directory ownership/permissions", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Set cruise directory ownership/permissions", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 10, 10)

    return json.dumps(job_results)


def task_set_cruise_data_directory_permissions(gearman_worker, gearman_job):
    """
    Set the permissions for the specified cruise ID
    """

    job_results = {'parts':[]}

    payload_obj = json.loads(gearman_job.data)
    logging.debug("Payload: %s", json.dumps(payload_obj, indent=2))

    gearman_worker.send_job_status(gearman_job, 5, 10)

    if gearman_worker.ovdm.show_only_current_cruise_dir():
        logging.info("Clear read permissions")
        lockdown_directory(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], gearman_worker.cruise_dir)
        job_results['parts'].append({"partName": "Clear CruiseData Directory Read Permissions", "result": "Pass"})

    gearman_worker.send_job_status(gearman_job, 8, 10)

    if os.path.isdir(gearman_worker.cruise_dir):
        logging.info("Clear read permissions")
        set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], gearman_worker.cruise_dir)
        job_results['parts'].append({"partName": "Set Directory Permissions for current cruise", "result": "Pass"})

    job_results['parts'].append({"partName": "Set CruiseData Directory Permissions", "result": "Pass"})
    gearman_worker.send_job_status(gearman_job, 10, 10)

    return json.dumps(job_results)


def task_rebuild_cruise_directory(gearman_worker, gearman_job):
    """
    Verify and create if necessary all the cruise sub-directories
    """

    job_results = {'parts':[]}

    payload_obj = json.loads(gearman_job.data)
    logging.debug("Payload: %s", json.dumps(payload_obj, indent=2))

    gearman_worker.send_job_status(gearman_job, 1, 10)

    if gearman_worker.ovdm.show_only_current_cruise_dir():
        logging.info("Clear read permissions")
        lockdown_directory(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], gearman_worker.cruise_dir)
        job_results['parts'].append({"partName": "Clear CruiseData Directory Read Permissions", "result": "Pass"})

    if os.path.exists(gearman_worker.cruise_dir):
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Pass"})
    else:
        logging.error("Cruise directory not found")
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Fail", "reason": "Unable to locate the cruise directory: " + gearman_worker.cruise_dir})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 2, 10)

    logging.info("Build directory list")
    directorylist = build_directorylist(gearman_worker)
    logging.debug("Directory List: %s", json.dumps(directorylist, indent=2))

    if len(directorylist) > 0:
        job_results['parts'].append({"partName": "Build Directory List", "result": "Pass"})
    else:
        logging.error("Directory list is empty")
        job_results['parts'].append({"partName": "Build Directory List", "result": "Fail", "reason": "Empty list of directories to create"})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 5, 10)

    logging.info("Create directories")

    output_results = create_directories(directorylist)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Create Directories", "result": "Pass"})
    else:
        logging.error("Failed to create any/all of the cruise data directory structure")
        job_results['parts'].append({"partName": "Create Directories", "result": "Fail", "reason": output_results['reason']})

    gearman_worker.send_job_status(gearman_job, 7, 10)

    logging.info("Set directory ownership/permissions")

    output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], gearman_worker.cruise_dir)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set Directory ownership/permissions", "result": "Pass"})
    else:
        logging.error("Failed to set directory ownership")
        job_results['parts'].append({"partName": "Set Directory ownership/permissions", "result": "Fail", "reason": output_results['reason']})

    gearman_worker.send_job_status(gearman_job, 10, 10)

    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle Cruise data directory related tasks')
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

    logging.info("\tTask: createCruiseDirectory")
    new_worker.register_task("createCruiseDirectory", task_create_cruise_directory)

    logging.info("\tTask: setCruiseDataDirectoryPermissions")
    new_worker.register_task("setCruiseDataDirectoryPermissions", task_set_cruise_data_directory_permissions)

    logging.info("\tTask: rebuildCruiseDirectory")
    new_worker.register_task("rebuildCruiseDirectory", task_rebuild_cruise_directory)

    logging.info("Waiting for jobs...")
    new_worker.work()
