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
import requests
import signal

def getJobInfo(dataObj):

    jobs = []
        
    # Set Error for current tranfer in DB via API
    url = dataObj['siteRoot'] + 'api/collectionSystemTransfers/getCollectionSystemTransfers'
    r = requests.get(url)
    #print r.json()
    for transfer in r.json():
        if transfer['pid'] != "0":
            jobs.append({'type': 'collectionSystemTransfer', 'id': transfer['collectionSystemTransferID'], 'name': transfer['name'], 'pid': transfer['pid']})

    # Set Error for current tranfer in DB via API
    url = dataObj['siteRoot'] + 'api/cruiseDataTransfers/getCruiseDataTransfers'
    r = requests.get(url)
    #print r.json()
    for transfer in r.json():
        if transfer['pid'] != "0":
            jobs.append({'type': 'cruiseDataTransfer', 'id': transfer['cruiseDataTransferID'], 'name': transfer['name'], 'pid': transfer['pid']})
    
    # Set Error for current tranfer in DB via API
    url = dataObj['siteRoot'] + 'api/cruiseDataTransfers/getRequiredCruiseDataTransfers'
    r = requests.get(url)
    #print r.json()
    for transfer in r.json():
        if transfer['pid'] != "0":
            jobs.append({'type': 'cruiseDataTransfer', 'id': transfer['cruiseDataTransferID'], 'name': transfer['name'], 'pid': transfer['pid']})
    
    # Set Error for current tranfer in DB via API
    url = dataObj['siteRoot'] + 'api/tasks/getTasks'
    r = requests.get(url)
    #print r.json()
    for task in r.json():
        if task['pid'] != "0":
            jobs.append({'type': 'task', 'id': task['taskID'], 'name': task['name'], 'pid': task['pid']})
            
    # Set Error for current tranfer in DB via API
    #url = dataObj['siteRoot'] + 'api/cruiseDataTransfers/getCruiseDataTransfers'
    #r = requests.get(url)
    #print jobs
    
    for job in jobs:
        if job['pid'] == dataObj['pid']:
            return job
        
    return {'type':'unknown'}

def sendKillMsg(dataObj, message):
    
    url = dataObj['siteRoot'] + 'api/messages/newMessage'
    payload = {'message': message}
    r = requests.post(url, data=payload)

def setIdle_cruiseDataTransfer(dataObj, id):

    # Set Error for current tranfer in DB via API
    url = dataObj['siteRoot'] + 'api/cruiseDataTransfers/setIdleCruiseDataTransfer/' + id
    r = requests.get(url)

def setIdle_collectionSystemTransfer(dataObj, id):

    # Set Error for current tranfer in DB via API
    url = dataObj['siteRoot'] + 'api/collectionSystemTransfers/setIdleCollectionSystemTransfer/' + id
    r = requests.get(url)

def setIdle_task(dataObj, id):

    # Set Error for current tranfer in DB via API
    url = dataObj['siteRoot'] + 'api/tasks/setIdleTask/' + id
    r = requests.get(url)

class CustomGearmanWorker(gearman.GearmanWorker):

    def on_job_execute(self, current_job):
        print "Job started: " + current_job.handle
        dataObj = json.loads(current_job.data)
#        setRunning_cruiseDataTransfer(current_job)
        return super(CustomGearmanWorker, self).on_job_execute(current_job)

    def on_job_exception(self, current_job, exc_info):
        print "Job failed, CAN stop last gasp GEARMAN_COMMAND_WORK_FAIL"
        self.send_job_data(current_job, json.dumps([{"partName": "Unknown Part of Transfer", "result": "Fail"}]))
        print exc_info
#        setError_cruiseDataTransfer(current_job)
        return super(CustomGearmanWorker, self).on_job_exception(current_job, exc_info)

    def on_job_complete(self, current_job, job_result):
        resultObj = json.loads(job_result)
        print "Job complete, CAN stop last gasp GEARMAN_COMMAND_WORK_COMPLETE"
        
        if resultObj['parts'][-1]['result'] == "Fail": # Final Verdict
#            setError_cruiseDataTransfer(current_job)
            print "but something prevented the transfer from successfully completing..."
            print json.dumps(resultObj)
        return super(CustomGearmanWorker, self).send_job_complete(current_job, job_result)

    def after_poll(self, any_activity):
        # Return True if you want to continue polling, replaces callback_fxn
        return True

def task_callback(gearman_worker, job):

    job_results = {'parts':[]}

    dataObj = json.loads(job.data)
    print 'DECODED dataObj:', json.dumps(dataObj, indent=2)
    
    jobInfo = getJobInfo(dataObj)
    print 'DECODED jobInfo:', json.dumps(jobInfo, indent=2)
    
    job_results['parts'].append({"partName": "Retrieve Job Info", "result": "Pass"})
    
    if jobInfo['type'] != "unknown":
        print "Quitting job: " + jobInfo['pid']
        try:
            os.kill(int(jobInfo['pid']), signal.SIGQUIT)
        except OSError:
            if jobInfo['type'] == 'collectionSystemTransfer':
                setIdle_collectionSystemTransfer(dataObj, jobInfo['id'])
            elif jobInfo['type'] == 'cruiseDataTransfer':
                setIdle_cruiseDataTransfer(dataObj, jobInfo['id'])
            elif jobInfo['type'] == 'task':
                setIdle_task(dataObj, jobInfo['id'])
                
        if jobInfo['type'] == 'collectionSystemTransfer':
            sendKillMsg(dataObj, "Manual Stop of transfer from " + jobInfo['name'])
        elif jobInfo['type'] == 'cruiseDataTransfer':
            sendKillMsg(dataObj, "Manual Stop of transfer to " + jobInfo['name'])
        elif jobInfo['type'] == 'task':
            sendKillMsg(dataObj, "Manual Stop of " + jobInfo['name'])
            
        job_results['parts'].append({"partName": "Stopped Job", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Stopped Job", "result": "Fail"})

    return json.dumps(job_results)

new_worker = CustomGearmanWorker(['localhost:4730'])
new_worker.set_client_id('stopJob.py')
new_worker.register_task("stopJob", task_callback)
new_worker.work()
