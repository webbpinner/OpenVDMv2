# ----------------------------------------------------------------------------------- #
#
#         FILE:  stop_job.py
#
#  DESCRIPTION:  Gearman worker that handles the manual termination of other OVDM data
#                transfers and OVDM tasks.
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.5
#      CREATED:  2015-01-01
#     REVISION:  2021-01-02
#
# LICENSE INFO: Open Vessel Data Management v2.5 (OpenVDMv2)
#               Copyright (C) OceanDataRat.org 2021
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/gpl-3.0.html>.
#
# ----------------------------------------------------------------------------------- #
import argparse
import sys
import python3_gearman
import json
import time
import signal
import logging

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.utils.set_ownerGroupPermissions import set_ownerGroupPermissions
from server.lib.openvdm import OpenVDM_API, DEFAULT_CRUISE_CONFIG_FN

def getJobInfo(gearman_worker):

    collectionSystemTransfers = gearman_worker.OVDM.getCollectionSystemTransfers()
    for collectionSystemTransfer in collectionSystemTransfers:
        if collectionSystemTransfer['pid'] == gearman_worker.jobPID:
            return {'type': 'collectionSystemTransfer', 'id': collectionSystemTransfer['collectionSystemTransferID'], 'name': collectionSystemTransfer['name'], 'pid': collectionSystemTransfer['pid']}
            
    cruiseDataTransfers = gearman_worker.OVDM.getCruiseDataTransfers()
    for cruiseDataTransfer in cruiseDataTransfers:
        if cruiseDataTransfer['pid'] != "0":
            return {'type': 'cruiseDataTransfer', 'id': cruiseDataTransfer['cruiseDataTransferID'], 'name': cruiseDataTransfer['name'], 'pid': cruiseDataTransfer['pid']}
    
    cruiseDataTransfers = gearman_worker.OVDM.getRequiredCruiseDataTransfers()
    for cruiseDataTransfer in cruiseDataTransfers:
        if cruiseDataTransfer['pid'] != "0":
            return {'type': 'cruiseDataTransfer', 'id': cruiseDataTransfer['cruiseDataTransferID'], 'name': cruiseDataTransfer['name'], 'pid': cruiseDataTransfer['pid']}
    
    tasks = gearman_worker.OVDM.getTasks()
    for task in tasks:
        if task['pid'] != "0":
            return {'type': 'task', 'id': task['taskID'], 'name': task['name'], 'pid': task['pid']}
                        
    return {'type':'unknown'}


class OVDMGearmanWorker(python3_gearman.GearmanWorker):
    
    def __init__(self, host_list=None):
        self.stop = False
        self.OVDM = OpenVDM_API()
        self.jobPID = ''
        self.jobInfo = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])

    def on_job_execute(self, current_job):

        logging.debug("current_job: {}".format(current_job))

        payloadObj = json.loads(current_job.data)

        self.jobPID = payloadObj['pid']
        self.jobInfo = getJobInfo(self)

        logging.info("Job: {}, Killing PID: {} failed at: {}".format(current_job.handle, self.jobPID, time.strftime("%D %T", time.gmtime())))
        
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)

    def on_job_exception(self, current_job, exc_info):
        logging.info("Job: {} Killing PID {} failed at: {}".format(current_job.handle, self.jobPID, time.strftime("%D %T", time.gmtime())))
        
        self.send_job_data(current_job, json.dumps([{"partName": "Worker Crashed", "result": "Fail", "reason": "Unknown"}]))
        
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)

    def on_job_complete(self, current_job, job_results):
        resultsObj = json.loads(job_results)

        logging.debug("Job Results: {}".format(json.dumps(resultsObj, indent=2)))
        logging.info("Job: {}, Killing PID {} completed at: {}".format(current_job.handle, self.jobPID, time.strftime("%D %T", time.gmtime())))
            
        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_results)


    def stopTask(self):
        self.stop = True
        logging.warning("Stopping current task...")


    def quitWorker(self):
        self.stop = True
        logging.warning("Quitting worker...")
        self.shutdown()

    
def task_stopJob(gearman_worker, gearman_job):

    job_results = {'parts':[]}

    payloadObj = json.loads(gearman_job.data)
    logging.debug("Payload: {}".format(json.dumps(payloadObj, indent=2)))
    
    job_results['parts'].append({"partName": "Retrieve Job Info", "result": "Pass"})
    
    if gearman_worker.jobInfo['type'] != "unknown":
        job_results['parts'].append({"partName": "Valid OpenVDM Job", "result": "Pass"})

        logging.debug("Quitting job:", gearman_worker.jobInfo['pid'])
        try:
            os.kill(int(gearman_worker.jobInfo['pid']), signal.SIGQUIT)

        except OSError as error:
            if error.errno == 3:
                logging.warning("Unable to kill process because the process doesn't exist")
                pass
            else:
                logging.error("Error killing PID:", gearman_worker.jobInfo['pid'])
                logging.error(str(error))
                job_results['parts'].append({"partName": "Stopped Job", "result": "Fail", "reason": "Error killing PID: " + gearman_worker.jobInfo['pid'] + " --> " + error})

        finally:
            if gearman_worker.jobInfo['type'] == 'collectionSystemTransfer':
                gearman_worker.OVDM.setIdle_collectionSystemTransfer(gearman_worker.jobInfo['id'])
                gearman_worker.OVDM.sendMsg("Manual Stop of transfer", gearman_worker.jobInfo['name'])
            elif gearman_worker.jobInfo['type'] == 'cruiseDataTransfer':
                gearman_worker.OVDM.setIdle_cruiseDataTransfer(gearman_worker.jobInfo['id'])
                gearman_worker.OVDM.sendMsg("Manual Stop of transfer", gearman_worker.jobInfo['name'])
            elif gearman_worker.jobInfo['type'] == 'task':
                gearman_worker.OVDM.setIdle_task(gearman_worker.jobInfo['id'])
                gearman_worker.OVDM.sendMsg("Manual Stop of task", gearman_worker.jobInfo['name'])
                            
            job_results['parts'].append({"partName": "Stopped Job", "result": "Pass"})
    else:
        logging.error("Unknown job type: {}".format(gearman_worker.jobInfo['type']))
        job_results['parts'].append({"partName": "Valid OpenVDM Job", "result": "Fail", "reason": "Unknown job type: " + gearman_worker.jobInfo['type']})

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
        logging.warning("QUIT Signal Received")
        new_worker.stopTask()

    def sigint_handler(_signo, _stack_frame):
        logging.warning("INT Signal Received")
        new_worker.quitWorker()

    signal.signal(signal.SIGQUIT, sigquit_handler)
    signal.signal(signal.SIGINT, sigint_handler)

    logging.info("Registering worker tasks...")

    logging.info("\tTask: stopJob")
    new_worker.register_task("stopJob", task_stopJob)

    logging.info("Waiting for jobs...")
    new_worker.work()
