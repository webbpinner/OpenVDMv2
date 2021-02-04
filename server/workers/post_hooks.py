#!/usr/bin/env python3
"""

FILE:  post_hooks.py

DESCRIPTION:  Gearman worker that runs user-defined scripts following the
    completion of the setupNewCruise, setupNewLowering,
    postCollectionSystemTransfer, postDataDashboard, finalizeCurrentCruise and
    finalizeCurrentLowering tasks.

     BUGS:
    NOTES:
   AUTHOR:  Webb Pinner
  COMPANY:  Capable Solutions
  VERSION:  2.5
  CREATED:  2016-02-09
 REVISION:  2020-12-30

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
import logging
from os.path import dirname, realpath
import python3_gearman

sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.lib.openvdm import OpenVDM
from server.lib.hooks import get_post_hook_commands, run_commands
from server.lib.hooks import POST_COLLECTION_SYSTEM_TRANSFER_HOOK_NAME, POST_DATA_DASHBOARD_HOOK_NAME, POST_SETUP_NEW_CRUISE_HOOK_NAME, POST_SETUP_NEW_LOWERING_HOOK_NAME, POST_FINALIZE_CURRENT_CRUISE_HOOK_NAME, POST_FINALIZE_CURRENT_LOWERING_HOOK_NAME

CUSTOM_TASKS = [
    {
        "taskID": "0",
        "name": POST_COLLECTION_SYSTEM_TRANSFER_HOOK_NAME,
        "longName": "Post Collection System Transfer",
    },
    {
        "taskID": "0",
        "name": POST_DATA_DASHBOARD_HOOK_NAME,
        "longName": "Post Data Dashboard Processing",
    },
    {
        "taskID": "0",
        "name": POST_SETUP_NEW_CRUISE_HOOK_NAME,
        "longName": "Post Setup New Cruise",
    },
    {
        "taskID": "0",
        "name": POST_SETUP_NEW_LOWERING_HOOK_NAME,
        "longName": "Post Setup New Lowering",
    },
    {
        "taskID": "0",
        "name": POST_FINALIZE_CURRENT_CRUISE_HOOK_NAME,
        "longName": "Post Finalize Current Cruise",
    },
    {
        "taskID": "0",
        "name": POST_FINALIZE_CURRENT_LOWERING_HOOK_NAME,
        "longName": "Post Finalize Current Lowering",
    }
]


class OVDMGearmanWorker(python3_gearman.GearmanWorker): # pylint: disable=too-many-instance-attributes
    """
    Class for the current Gearman worker
    """

    def __init__(self):
        self.stop = False
        self.ovdm = OpenVDM()
        self.task = None
        self.files = { 'new':[], 'updated':[] }
        self.cruise_id = self.ovdm.get_cruise_id()
        self.lowering_id = self.ovdm.get_lowering_id()
        self.collection_system_transfer = { 'name': "" }
        self.shipboard_data_warehouse_config = self.ovdm.get_shipboard_data_warehouse_config()

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

        if self.task is None:
            self.on_job_complete(current_job, json.dumps({'parts': [{"partName": "Verify Task", "result": "Fail", "reason": "undefined task"}]}))
        elif int(self.task['taskID']) > 0:
            self.ovdm.set_running_task(self.task['taskID'], os.getpid(), current_job.handle)
        else:
            self.ovdm.track_gearman_job(self.task['longName'], os.getpid(), current_job.handle)

        logging.info("Job: %s (%s) started at: %s", self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime()))

        self.files = payload_obj['files'] if 'files' in payload_obj else { 'new':[], 'updated':[] }
        self.cruise_id = payload_obj['cruiseID'] if 'cruiseID' in payload_obj else self.ovdm.get_cruise_id()
        self.lowering_id = payload_obj['loweringID'] if 'loweringID' in payload_obj else self.ovdm.get_lowering_id()
        self.collection_system_transfer =  self.ovdm.get_collection_system_transfer(payload_obj['collectionSystemTransferID']) if 'collectionSystemTransferID' in payload_obj else { 'name': "" }
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


    def on_job_complete(self, current_job, job_result):
        """
        Function run whenever the current job completes
        """

        results_obj = json.loads(job_result)

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


def task_post_hook(gearman_worker, gearman_job):
    """
    Run the post-hook tasks
    """

    job_results = {'parts':[]}

    payload_obj = json.loads(gearman_job.data)
    logging.debug("Payload: %s", json.dumps(payload_obj, indent=2))

    gearman_worker.send_job_status(gearman_job, 1, 10)

    logging.info("Retrieving Commands")
    output_results = get_post_hook_commands(gearman_worker, gearman_worker.task['name'])

    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Get Commands", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    logging.debug("Command List: %s", json.dumps(output_results['commandList'], indent=2))

    job_results['parts'].append({"partName": "Get Commands", "result": "Pass"})

    gearman_worker.send_job_status(gearman_job, 3, 10)

    logging.info("Running Commands")
    if len(output_results['commandList']) > 0:
        output_results = run_commands(output_results['commandList'])

        if not output_results['verdict']:

            for reason in output_results['reason'].split("\n"):
                gearman_worker.ovdm.send_msg("Error executing postHook process", reason)

            job_results['parts'].append({"partName": "Running commands", "result": "Fail", "reason": "One or more of the post-hook processes failed"})
        else:
            job_results['parts'].append({"partName": "Running commands", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Running commands", "result": "Pass"})

    gearman_worker.send_job_status(gearman_job, 10, 10)

    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle post-hook processes')
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

    logging.info("\tTask: postCollectionSystemTransfer")
    new_worker.register_task("postCollectionSystemTransfer", task_post_hook)
    logging.info("\tTask: postDataDashboard")
    new_worker.register_task("postDataDashboard", task_post_hook)
    logging.info("\tTask: postSetupNewCruise")
    new_worker.register_task("postSetupNewCruise", task_post_hook)
    logging.info("\tTask: postSetupNewLowering")
    new_worker.register_task("postSetupNewLowering", task_post_hook)
    logging.info("\tTask: postFinalizeCurrentCruise")
    new_worker.register_task("postFinalizeCurrentCruise", task_post_hook)
    logging.info("\tTask: postFinalizeCurrentLowering")
    new_worker.register_task("postFinalizeCurrentLowering", task_post_hook)

    logging.info("Waiting for jobs...")
    new_worker.work()
