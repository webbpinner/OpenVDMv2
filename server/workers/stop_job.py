#!/usr/bin/env python3
"""

FILE:  stop_job.py

DESCRIPTION:  Gearman worker that handles the manual termination of other OVDM
    data transfers and OVDM tasks.

     BUGS:
    NOTES:
   AUTHOR:  Webb Pinner
  COMPANY:  Capable Solutions
  VERSION:  2.5
  CREATED:  2015-01-01
 REVISION:  2021-01-02

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
import time
import signal
import logging
import python3_gearman

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.lib.openvdm import OpenVDM


class OVDMGearmanWorker(python3_gearman.GearmanWorker):
    """
    Class for the current Gearman worker
    """

    def __init__(self):
        self.stop = False
        self.ovdm = OpenVDM()
        self.job_pid = ''
        self.job_info = {}
        super().__init__(host_list=[self.ovdm.get_gearman_server()])


    def _get_job_info(self):
        """
        Fetch job metadata
        """

        collection_system_transfers = self.ovdm.get_collection_system_transfers()
        for collection_system_transfer in collection_system_transfers:
            if collection_system_transfer['pid'] == self.job_pid:
                return {'type': 'collectionSystemTransfer', 'id': collection_system_transfer['collectionSystemTransferID'], 'name': collection_system_transfer['name'], 'pid': collection_system_transfer['pid']}

        cruise_data_transfers = self.ovdm.get_cruise_data_transfers()
        for cruise_data_transfer in cruise_data_transfers:
            if cruise_data_transfer['pid'] != "0":
                return {'type': 'cruiseDataTransfer', 'id': cruise_data_transfer['cruiseDataTransferID'], 'name': cruise_data_transfer['name'], 'pid': cruise_data_transfer['pid']}

        cruise_data_transfers = self.ovdm.get_required_cruise_data_transfers()
        for cruise_data_transfer in cruise_data_transfers:
            if cruise_data_transfer['pid'] != "0":
                return {'type': 'cruiseDataTransfer', 'id': cruise_data_transfer['cruiseDataTransferID'], 'name': cruise_data_transfer['name'], 'pid': cruise_data_transfer['pid']}

        tasks = self.ovdm.get_tasks()
        for task in tasks:
            if task['pid'] != "0":
                return {'type': 'task', 'id': task['taskID'], 'name': task['name'], 'pid': task['pid']}

        return {'type':'unknown'}


    def on_job_execute(self, current_job):
        """
        Function run whenever a new job arrives
        """

        logging.debug("current_job: %s", current_job)

        payload_obj = json.loads(current_job.data)

        self.job_pid = payload_obj['pid']
        self.job_info = self._get_job_info()

        logging.info("Job: %s, Killing PID: %s failed at: %s", current_job.handle, self.job_pid, time.strftime("%D %T", time.gmtime()))

        return super().on_job_execute(current_job)

    def on_job_exception(self, current_job, exc_info):
        """
        Function run whenever the current job has an exception
        """

        logging.info("Job: %s Killing PID %s failed at: %s", current_job.handle, self.job_pid, time.strftime("%D %T", time.gmtime()))

        self.send_job_data(current_job, json.dumps([{"partName": "Worker Crashed", "result": "Fail", "reason": "Unknown"}]))

        exc_type, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error(exc_type, fname, exc_tb.tb_lineno)
        return super().on_job_exception(current_job, exc_info)

    def on_job_complete(self, current_job, job_results):
        """
        Function run whenever the current job completes
        """

        results_obj = json.loads(job_results)

        logging.debug("Job Results: %s", json.dumps(results_obj, indent=2))
        logging.info("Job: %s, Killing PID %s completed at: %s", current_job.handle, self.job_pid, time.strftime("%D %T", time.gmtime()))

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


def task_stop_job(gearman_worker, gearman_job):
    """
    Stop the specified OpenVDM task/transfer/process
    """

    job_results = {'parts':[]}

    payload_obj = json.loads(gearman_job.data)
    logging.debug("Payload: %s", json.dumps(payload_obj, indent=2))

    job_results['parts'].append({"partName": "Retrieve Job Info", "result": "Pass"})

    if gearman_worker.job_info['type'] != "unknown":
        job_results['parts'].append({"partName": "Valid OpenVDM Job", "result": "Pass"})

        logging.debug("Quitting job: %s", gearman_worker.job_info['pid'])
        try:
            os.kill(int(gearman_worker.job_info['pid']), signal.SIGQUIT)

        except OSError as err:
            if err.errno == 3:
                logging.warning("Unable to kill process because the process doesn't exist")
            else:
                logging.error("Error killing PID: %s", gearman_worker.job_info['pid'])
                logging.error(str(err))
                job_results['parts'].append({"partName": "Stopped Job", "result": "Fail", "reason": "Error killing PID: {} --> {}".format(gearman_worker.job_info['pid'], err) })

        finally:
            if gearman_worker.job_info['type'] == 'collectionSystemTransfer':
                gearman_worker.ovdm.set_idle_collection_system_transfer(gearman_worker.job_info['id'])
                gearman_worker.ovdm.send_msg("Manual Stop of transfer", gearman_worker.job_info['name'])
            elif gearman_worker.job_info['type'] == 'cruiseDataTransfer':
                gearman_worker.ovdm.set_idle_cruise_data_transfer(gearman_worker.job_info['id'])
                gearman_worker.ovdm.send_msg("Manual Stop of transfer", gearman_worker.job_info['name'])
            elif gearman_worker.job_info['type'] == 'task':
                gearman_worker.ovdm.set_idle_task(gearman_worker.job_info['id'])
                gearman_worker.ovdm.send_msg("Manual Stop of task", gearman_worker.job_info['name'])

            job_results['parts'].append({"partName": "Stopped Job", "result": "Pass"})
    else:
        logging.error("Unknown job type: %s", gearman_worker.job_info['type'])
        job_results['parts'].append({"partName": "Valid OpenVDM Job", "result": "Fail", "reason": "Unknown job type: " + gearman_worker.job_info['type']})

    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle dynamic stopping of other tasks')
    parser.add_argument('-d', '--debug', action='store_true', help=' display debug messages')
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

    logging.info("\tTask: stopJob")
    new_worker.register_task("stopJob", task_stop_job)

    logging.info("Waiting for jobs...")
    new_worker.work()
