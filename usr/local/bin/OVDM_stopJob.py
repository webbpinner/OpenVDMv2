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
#      VERSION:  2.0
#      CREATED:  2015-01-01
#     REVISION:  2016-02-08
#
# LICENSE INFO: Open Vessel Data Management (OpenVDM) Copyright (C) 2016  Webb Pinner
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

import os
import sys
import gearman
import shutil
import json
import time
import signal
import openvdm

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
        self.OVDM = openvdm.OpenVDM()
        self.jobPID = ''
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])

    def on_job_execute(self, current_job):
        payloadObj = json.loads(current_job.data)
        self.jobPID = payloadObj['pid']        
        print payloadObj
        
        print "Job: " + current_job.handle + ", Killing PID: " + self.jobPID + ' started at ' + time.strftime("%D %T", time.gmtime())
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)

    def on_job_exception(self, current_job, exc_info):
        print "Job: " + current_job.handle + ", " + taskLookup[current_job.task] + " failed at:    " + time.strftime("%D %T", time.gmtime())
        self.send_job_data(current_job, json.dumps([{"partName": "Unknown Part of task", "result": "Fail"}]))
        
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)

    def on_job_complete(self, current_job, job_result):
        try:
            resultObj = json.loads(job_result)
        
            if len(resultObj['parts']) > 0:
                if resultObj['parts'][-1]['result'] == "Fail": # Final Verdict
                    print resultObj['parts']
        except:
            print "Something went wrong"
            job_result = ''

        print "Job: " + current_job.handle + ", Killing PID: " + self.jobPID + " completed at: " + time.strftime("%D %T", time.gmtime())
            
        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_result)

    def after_poll(self, any_activity):
        # Return True if you want to continue polling, replaces callback_fxn
        return True

    
def task_stopJob(worker, job):

    job_results = {'parts':[]}
    
    jobInfo = getJobInfo(worker)
    #print 'DECODED jobInfo:', json.dumps(jobInfo, indent=2)
    
    job_results['parts'].append({"partName": "Retrieve Job Info", "result": "Pass"})
    
    if jobInfo['type'] != "unknown":
        #print "Quitting job: " + jobInfo['pid']
        try:
            os.kill(int(jobInfo['pid']), signal.SIGQUIT)
        except OSError:
            if jobInfo['type'] == 'collectionSystemTransfer':
                worker.OVDM.setIdle_collectionSystemTransfer(jobInfo['id'])
            elif jobInfo['type'] == 'cruiseDataTransfer':
                worker.OVDM.setIdle_cruiseDataTransfer(jobInfo['id'])
            elif jobInfo['type'] == 'task':
                worker.OVDM.setIdle_task(jobInfo['id'])
                
        if jobInfo['type'] == 'collectionSystemTransfer':
            worker.OVDM.sendMsg("Manual Stop of transfer from " + jobInfo['name'])
        elif jobInfo['type'] == 'cruiseDataTransfer':
            worker.OVDM.sendMsg("Manual Stop of transfer to " + jobInfo['name'])
        elif jobInfo['type'] == 'task':
            worker.OVDM.sendMsg("Manual Stop of " + jobInfo['name'])
            
        job_results['parts'].append({"partName": "Stopped Job", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Stopped Job", "result": "Fail"})
        
    return json.dumps(job_results)

new_worker = OVDMGearmanWorker()
new_worker.set_client_id('stopJob.py')
new_worker.register_task("stopJob", task_stopJob)
new_worker.work()
