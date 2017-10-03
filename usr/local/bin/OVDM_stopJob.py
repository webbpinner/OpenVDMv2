# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_stopJob.py
#
#  DESCRIPTION:  Gearman worker that handles the manual termination of other OVDM data
#                transfers and OVDM tasks.
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.3
#      CREATED:  2015-01-01
#     REVISION:  2017-08-05
#
# LICENSE INFO: Open Vessel Data Management (OpenVDMv2)
#               Copyright (C) OceanDataRat.org 2017
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
from __future__ import print_function
import argparse
import os
import sys
import gearman
import shutil
import json
import time
import signal
import openvdm

DEBUG = False
new_worker = None


def debugPrint(*args, **kwargs):
    global DEBUG
    if DEBUG:
        errPrint(*args, **kwargs)


def errPrint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def getJobInfo(worker):

    collectionSystemTransfers = worker.OVDM.getCollectionSystemTransfers()
    for collectionSystemTransfer in collectionSystemTransfers:
        if collectionSystemTransfer['pid'] == worker.jobPID:
            return {'type': 'collectionSystemTransfer', 'id': collectionSystemTransfer['collectionSystemTransferID'], 'name': collectionSystemTransfer['name'], 'pid': collectionSystemTransfer['pid']}
            
    cruiseDataTransfers = worker.OVDM.getCruiseDataTransfers()
    for cruiseDataTransfer in cruiseDataTransfers:
        if cruiseDataTransfer['pid'] != "0":
            return {'type': 'cruiseDataTransfer', 'id': cruiseDataTransfer['cruiseDataTransferID'], 'name': cruiseDataTransfer['name'], 'pid': cruiseDataTransfer['pid']}
    
    cruiseDataTransfers = worker.OVDM.getRequiredCruiseDataTransfers()
    for cruiseDataTransfer in cruiseDataTransfers:
        if cruiseDataTransfer['pid'] != "0":
            return {'type': 'cruiseDataTransfer', 'id': cruiseDataTransfer['cruiseDataTransferID'], 'name': cruiseDataTransfer['name'], 'pid': cruiseDataTransfer['pid']}
    
    tasks = worker.OVDM.getTasks()
    for task in tasks:
        if task['pid'] != "0":
            return {'type': 'task', 'id': task['taskID'], 'name': task['name'], 'pid': task['pid']}
                        
    return {'type':'unknown'}


class OVDMGearmanWorker(gearman.GearmanWorker):
    
    def __init__(self, host_list=None):
        self.stop = False
        self.quit = False
        self.OVDM = openvdm.OpenVDM()
        self.jobPID = ''
        self.jobInfo = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])

    def on_job_execute(self, current_job):
        payloadObj = json.loads(current_job.data)
        self.jobPID = payloadObj['pid']
        self.jobInfo = getJobInfo(self)
        errPrint("Job:", current_job.handle + ",", "Killing PID:", self.jobPID, "started at   ", time.strftime("%D %T", time.gmtime()))
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)

    def on_job_exception(self, current_job, exc_info):
        errPrint("Job:", current_job.handle + ",", "Killing PID:", self.jobPID, "failed at:   ", time.strftime("%D %T", time.gmtime()))
        self.send_job_data(current_job, json.dumps([{"partName": "Worker Crashed", "result": "Fail", "reason": "Unknown"}]))
        
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        errPrint(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)

    def on_job_complete(self, current_job, job_results):
        try:
            resultsObj = json.loads(job_results)
        
            if len(resultsObj['parts']) > 0:
                if resultsObj['parts'][-1]['result'] == "Fail": # Final Verdict
                    errPrint(json.dumps(resultsObj['parts'], indent=2))
        except:
            errPrint("Something went wrong")
            job_results = ''

        debugPrint('Job Results:', json.dumps(resultsObj, indent=2))

        errPrint("Job:", current_job.handle + ",", "Killing PID:", self.jobPID, "completed at:", time.strftime("%D %T", time.gmtime()))
            
        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_results)

    def after_poll(self, any_activity):
        self.stop = False
        if self.quit:
            errPrint("Quitting")
            self.shutdown()
        else:
            self.quit = False
        return True


    def stopTask(self):
        self.stop = True
        debugPrint("Stopping current task...")


    def quitWorker(self):
        self.stop = True
        self.quit = True
        debugPrint("Quitting worker...")

    
def task_stopJob(worker, current_job):

    job_results = {'parts':[]}

    payloadObj = json.loads(current_job.data)
    debugPrint('Payload:',json.dumps(payloadObj, indent=2))

    debugPrint('jobInfo:', json.dumps(worker.jobInfo, indent=2))
    
    job_results['parts'].append({"partName": "Retrieve Job Info", "result": "Pass"})
    
    if worker.jobInfo['type'] != "unknown":
        job_results['parts'].append({"partName": "Valid OpenVDM Job", "result": "Pass"})

        debugPrint("Quitting job:", worker.jobInfo['pid'])
        try:
            os.kill(int(worker.jobInfo['pid']), signal.SIGQUIT)

        except OSError:
            errPrint("Error killing PID:", worker.jobInfo['pid'])
            job_results['parts'].append({"partName": "Stopped Job", "result": "Fail", "reason": "Error killing PID: " + worker.jobInfo['pid']})

        else:
            if worker.jobInfo['type'] == 'collectionSystemTransfer':
                worker.OVDM.setIdle_collectionSystemTransfer(worker.jobInfo['id'])
                worker.OVDM.sendMsg("Manual Stop of transfer", worker.jobInfo['name'])
            elif worker.jobInfo['type'] == 'cruiseDataTransfer':
                worker.OVDM.setIdle_cruiseDataTransfer(worker.jobInfo['id'])
                worker.OVDM.sendMsg("Manual Stop of transfer", worker.jobInfo['name'])
            elif worker.jobInfo['type'] == 'task':
                worker.OVDM.setIdle_task(worker.jobInfo['id'])
                worker.OVDM.sendMsg("Manual Stop of task", worker.jobInfo['name'])
                            
            job_results['parts'].append({"partName": "Stopped Job", "result": "Pass"})
    else:
        errPrint("Unknown job type:", worker.jobInfo['type'])
        job_results['parts'].append({"partName": "Valid OpenVDM Job", "result": "Fail", "reason": "Unknown job type: " + worker.jobInfo['type']})

    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Main function of the script should it be run as a stand-alone utility.
# -------------------------------------------------------------------------------------
def main(argv):

    parser = argparse.ArgumentParser(description='Handle dynamic stopping of other tasks')
    parser.add_argument('-d', '--debug', action='store_true', help=' display debug messages')

    args = parser.parse_args()
    if args.debug:
        global DEBUG
        DEBUG = True
        debugPrint("Running in debug mode")

    debugPrint('Creating Worker...')
    global new_worker
    new_worker = OVDMGearmanWorker()

    debugPrint('Defining Signal Handlers...')
    def sigquit_handler(_signo, _stack_frame):
        errPrint("QUIT Signal Received")
        new_worker.stopTask()

    def sigint_handler(_signo, _stack_frame):
        errPrint("INT Signal Received")
        new_worker.quitWorker()

    signal.signal(signal.SIGQUIT, sigquit_handler)
    signal.signal(signal.SIGINT, sigint_handler)

    new_worker.set_client_id('stopJob.py')

    debugPrint('Registering worker tasks...')
    debugPrint('   Task:', 'stopJob')
    new_worker.register_task("stopJob", task_stopJob)

    debugPrint('Waiting for jobs...')
    new_worker.work()

# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])
