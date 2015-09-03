# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_cruise.py
#
#  DESCRIPTION:  Gearman worker the handles the tasks of initializing a new cruise
#                and finalizing the current cruise.  This includes initializing/
#                finalizing the data dashboard, MD5summary and transfer log summary.
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.0
#      CREATED:  2015-01-01
#     REVISION:  2015-06-09
#
# LICENSE INFO: Open Vessel Data Management (OpenVDM) Copyright (C) 2015  Webb Pinner
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
import errno
import gearman
import json
import time
import datetime
import requests
import signal
import pwd
import grp
import shutil

tasks = {
    "setupNewCruise": "Initializing Cruise",
    "finalizeCurrentCruise": "Finalizing Cruise",
    "exportOVDMConfig": "Export OpenVDM Configuration"
}

cruiseConfigFN = 'ovdmConfig.json'

def output_JSONDataToFile(filePath, contents, warehouseUser):
    
    try:
        os.makedirs(os.path.dirname(filePath))
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
            worker.stopJob()
            print "Unable to create directory for dashboard data file"
            return False
    finally:
        os.chown(os.path.dirname(filePath), pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)
    
    try:
        #print "Open JSON file"
        JSONFile = open(filePath, 'w')

        #print "Saving JSON file"
        json.dump(contents, JSONFile, indent=4)

    except IOError:
        print "Error Saving JSON file"
        return False

    finally:
        #print "Closing JSON file"
        JSONFile.close()
        os.chown(filePath, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)

    return True

def build_cruiseConfig(dataObj):
    url = dataObj['siteRoot'] + 'api/warehouse/getCruiseConfig'
    r = requests.get(url)
    ovdmConfig = json.loads(r.text)
    ovdmConfig['configCreatedOn'] = datetime.datetime.utcnow().strftime("%Y/%m/%dT%H:%M:%SZ")
    return ovdmConfig


def move_files(sourceDir, destDir, warehouseUser):

    for root, dirnames, filenames in os.walk(sourceDir):
        for dirname in dirnames:
            dirPath = os.path.join(root, dirname)
            os.chown(dirPath, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)
            shutil.move(dirPath, destDir)
        for filename in filenames:
            filePath = os.path.join(root, filename)
            os.chown(filePath, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)
            shutil.move(filePath, destDir)

def setError_task(job, taskID):
    dataObj = json.loads(job.data)

    # Set Error for current tranfer in DB via API
    url = dataObj['siteRoot'] + 'api/tasks/setErrorTask/' + taskID
    r = requests.get(url)
    
    url = dataObj['siteRoot'] + 'api/messages/newMessage'
    payload = {'message': 'Error: ' + job.task}
    r = requests.post(url, data=payload)

def setRunning_task(job, taskID):
    dataObj = json.loads(job.data)
    jobPID = os.getpid()

    # Set Error for the task in DB via API
    url = dataObj['siteRoot'] + 'api/tasks/setRunningTask/' + taskID
    payload = {'jobPid': jobPID}
    r = requests.post(url, data=payload)

    # Add Job to DB via API
    url = dataObj['siteRoot'] + 'api/gearman/newJob/' + job.handle
    payload = {'jobName': tasks[job.task], 'jobPid': jobPID}
    r = requests.post(url, data=payload)

def setIdle_task(job, taskID):
    dataObj = json.loads(job.data)

    # Set Error for the task in DB via API
    url = dataObj['siteRoot'] + 'api/tasks/setIdleTask/' + taskID
    r = requests.get(url)

def clearError_task(job, taskID):
    dataObj = json.loads(job.data)
    url = dataObj['siteRoot'] + 'api/tasks/getTask/' + taskID
    r = requests.get(url)
    for task in r.json():
        if task['status'] == '3':
            # Clear Error for the task in DB via API
            url = dataObj['siteRoot'] + 'api/tasks/setIdleTask/' + taskID
            r = requests.get(url)
    
class CustomGearmanWorker(gearman.GearmanWorker):
    
    def __init__(self, host_list=None):
        super(CustomGearmanWorker, self).__init__(host_list=host_list)
        self.stop = False
        self.quit = False
        self.taskID = "0"
        
    def get_taskID(self, current_job):
        dataObj = json.loads(current_job.data)
        url = dataObj['siteRoot'] + 'api/tasks/getTasks'
        r = requests.get(url)
        for task in r.json():
            if task['name'] == current_job.task:
                self.taskID = task['taskID']
                return True
        
        self.taskID = "0"
        return False
    
    def on_job_execute(self, current_job):
        print "Job started: " + current_job.handle
        self.get_taskID(current_job)
        setRunning_task(current_job, self.taskID)
        return super(CustomGearmanWorker, self).on_job_execute(current_job)
            

    def on_job_exception(self, current_job, exc_info):
        print "Job failed, CAN stop last gasp GEARMAN_COMMAND_WORK_FAIL"
        self.send_job_data(current_job, json.dumps([{"partName": "Unknown Part of Task", "result": "Fail"}]))
        setError_task(current_job, self.taskID)
        print exc_info
        return super(CustomGearmanWorker, self).on_job_exception(current_job, exc_info)

    def on_job_complete(self, current_job, job_result):
        resultObj = json.loads(job_result)
        print "Job complete, CAN stop last gasp GEARMAN_COMMAND_WORK_COMPLETE"
        
        if resultObj['parts'][-1]['result'] == "Fail": # Final Verdict
            setError_task(current_job,  self.taskID)
            print "but something prevented the task from successfully completing..."
        else:
            setIdle_task(current_job, self.taskID)
            
        return super(CustomGearmanWorker, self).send_job_complete(current_job, job_result)

    def after_poll(self, any_activity):
        self.stop = False
        self.taskID = "0"
        if self.quit:
            print "Quitting"
            self.shutdown()
        return True
    
    def stopWorker(self):
        self.stop = True
        
    def quitWorker(self):
        self.stop = True
        self.quit = True


def task_callback(gearman_worker, job):

    job_results = {'parts':[]}

    dataObj = json.loads(job.data)
    #print 'DECODED:', json.dumps(dataObj, indent=2)
    
    cruiseDir = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+dataObj['cruiseID']
    warehouseUser = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseUsername']
    
    gearman_worker.send_job_status(job, 1, 10)
    
    gm_client = gearman.GearmanClient(['localhost:4730'])
    completed_job_request = gm_client.submit_job("createCruiseDirectory", job.data)
    
    resultObj = json.loads(completed_job_request.result)
    #print 'DECODED Results:', json.dumps(resultObj, indent=2)

    if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
        #print "Connection Test: Passed"
        job_results['parts'].append({"partName": "Create Cruise Directory", "result": "Pass"})
    else:
        print "Create Cruise Directory: Failed"
        #print "Quitting"
        job_results += resultObj['parts']
        job_results['parts'].append({"partName": "Create Cruise Directory", "result": "Fail"})
        #print json.dumps(job_results, indent=2)
        return json.dumps(job_results)
    
    gearman_worker.send_job_status(job, 3, 10)
    
    gm_client = gearman.GearmanClient(['localhost:4730'])
    
    completed_job_request = gm_client.submit_job("rebuildTransferLogSummary", job.data)

    resultObj = json.loads(completed_job_request.result)
    #print 'DECODED Results:', json.dumps(resultObj, indent=2)

    if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
        #print "Connection Test: Passed"
        job_results['parts'].append({"partName": "Create Transfer Log Summary", "result": "Pass"})
    else:
        print "Create Transfer Log Summary File: Failed"
        #print "Quitting"
        job_results += resultObj['parts']
        job_results['parts'].append({"partName": "Create Transfer Log Summary", "result": "Fail"})
        #print json.dumps(job_results, indent=2)
        return json.dumps(job_results)
    
    gearman_worker.send_job_status(job, 5, 10)
    
    completed_job_request = gm_client.submit_job("rebuildDataDashboard", job.data)

    resultObj = json.loads(completed_job_request.result)
    #print 'DECODED Results:', json.dumps(resultObj, indent=2)

    if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
        #print "Connection Test: Passed"
        job_results['parts'].append({"partName": "Create Data Dashboard Manifest", "result": "Pass"})
    else:
        print "Create Data Dashboard Manifest File: Failed"
        #print "Quitting"
        job_results += resultObj['parts']
        job_results['parts'].append({"partName": "Create Data Dashboard Manifest", "result": "Fail"})
        #print json.dumps(job_results, indent=2)
        return json.dumps(job_results)
    
    gearman_worker.send_job_status(job, 7, 10)
    
    completed_job_request = gm_client.submit_job("rebuildMD5Summary", job.data)

    resultObj = json.loads(completed_job_request.result)
    #print 'DECODED Results:', json.dumps(resultObj, indent=2)

    if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
        #print "Connection Test: Passed"
        job_results['parts'].append({"partName": "Create MD5 Summary", "result": "Pass"})
    else:
        print "Create MD5 Summary File: Failed"
        #print "Quitting"
        job_results += resultObj['parts']
        job_results['parts'].append({"partName": "Create MD5 Summary", "result": "Fail"})
        #print json.dumps(job_results, indent=2)
        return json.dumps(job_results)
    
    gearman_worker.send_job_status(job, 9, 10)

    #build OpenVDM Config file
    ovdmConfig = build_cruiseConfig(dataObj)
    output_JSONDataToFile(cruiseDir + '/' + cruiseConfigFN, ovdmConfig, warehouseUser)
    
    gearman_worker.send_job_status(job, 10, 10)

    return json.dumps(job_results)
        
def task_callback2(gearman_worker, job):

    job_results = {'parts':[]}
    gmData = {}

    dataObj = json.loads(job.data)
    #print 'DECODED:', json.dumps(dataObj, indent=2)

    cruiseDir = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+dataObj['cruiseID']
    publicDataDir = dataObj['shipboardDataWarehouse']['shipboardDataWarehousePublicDataDir']
    warehouseUser = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseUsername']
    scienceDir = cruiseDir + '/' + dataObj['scienceDir']
    
    gearman_worker.send_job_status(job, 1, 10)

    if os.path.exists(cruiseDir):
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Fail"})
        return json.dumps(job_results)

    if os.path.exists(publicDataDir):
        job_results['parts'].append({"partName": "Verify Public Data Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Public Data Directory exists", "result": "Fail"})
        return json.dumps(job_results)


    gm_client = gearman.GearmanClient(['localhost:4730'])

    gmData['siteRoot'] = dataObj['siteRoot']
    gmData['shipboardDataWarehouse'] = dataObj['shipboardDataWarehouse']
    gmData['cruiseID'] = dataObj['cruiseID']
    gmData['systemStatus'] = "On";
    
    collectionSystemTransferJobs = []
    
    gearman_worker.send_job_status(job, 3, 10)
    
    for collectionSystemTransfer in dataObj['collectionSystemTransfers']:
        
        gmData['collectionSystemTransfer'] = collectionSystemTransfer
        collectionSystemTransferJobs.append( {"task": "runCollectionSystemTransfer", "data": json.dumps(gmData)} )

    #print json.dumps(collectionSystemTransferJobs, indent=2)
    
    submitted_job_request = gm_client.submit_multiple_jobs(collectionSystemTransferJobs, background=False, wait_until_complete=False)
    
    #print submitted_job_request

    gearman_worker.send_job_status(job, 4, 10)
    
    time.sleep(1)
    completed_requests = gm_client.wait_until_jobs_completed(submitted_job_request)

    gearman_worker.send_job_status(job, 7, 10)
    
    #print "Try to move Public Data from " + publicDataDir + " to " + scienceDir;
    move_files(publicDataDir, scienceDir, warehouseUser)
    
    gearman_worker.send_job_status(job, 8, 10)
    
    #build OpenVDM Config file
    ovdmConfig = build_cruiseConfig(dataObj)
    output_JSONDataToFile(cruiseDir + '/' + cruiseConfigFN, ovdmConfig, warehouseUser)
    gearman_worker.send_job_status(job, 9, 10)
    
    completed_job_request = gm_client.submit_job("rebuildMD5Summary", job.data)
    
    # need to add code for cruise data transfers
    gearman_worker.send_job_status(job, 10, 10)
    return json.dumps(job_results)

def task_callback3(gearman_worker, job):

    job_results = {'parts':[]}
    gmData = {}

    dataObj = json.loads(job.data)
    #print 'DECODED:', json.dumps(dataObj, indent=2)

    cruiseDir = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+dataObj['cruiseID']
    publicDataDir = dataObj['shipboardDataWarehouse']['shipboardDataWarehousePublicDataDir']
    warehouseUser = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseUsername']
    scienceDir = cruiseDir + '/' + dataObj['scienceDir']
    
    gearman_worker.send_job_status(job, 1, 10)

    if os.path.exists(cruiseDir):
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Fail"})
        return json.dumps(job_results)
    
    #build OpenVDM Config file
    ovdmConfig = build_cruiseConfig(dataObj)
    output_JSONDataToFile(cruiseDir + '/' + cruiseConfigFN, ovdmConfig, warehouseUser)
    
    gearman_worker.send_job_status(job, 10, 10)
    return json.dumps(job_results)

global new_worker
new_worker = CustomGearmanWorker(['localhost:4730'])

def sigquit_handler(_signo, _stack_frame):
    print "QUIT Signal Received"
    new_worker.stopWorker()
    
def sigint_handler(_signo, _stack_frame):
    print "INT Signal Received"
    new_worker.quitWorker()
    
signal.signal(signal.SIGQUIT, sigquit_handler)
signal.signal(signal.SIGINT, sigint_handler)

new_worker.set_client_id('cruise.py')
new_worker.register_task("setupNewCruise", task_callback)
new_worker.register_task("finalizeCurrentCruise", task_callback2)
new_worker.register_task("exportOVDMConfig", task_callback3)
new_worker.work()