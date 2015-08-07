# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_cruiseDirectory.py
#
#  DESCRIPTION:  Gearman worker the handles the tasks of creating a new cruise data
#                directory and updating the cruise directory structure when additional
#                subdirectories must be added.
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
import requests
import signal
import pwd
import grp

tasks = {
    "createCruiseDirectory": "Creating Cruise Directory",
    "rebuildCruiseDirectory": "Updating Cruise Directory"
}

def build_destDir(raw_destDir, data):
    
    #print raw_destDir
    returnDestDir = raw_destDir.replace('{cruiseID}', data['cruiseID'])
    #print returnDestDir
    return returnDestDir

def build_directorylist(dataObj):

    returnDirectories = []
    cruiseDir = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+dataObj['cruiseID']
    
    url = dataObj['siteRoot'] + 'api/collectionSystemTransfers/getCollectionSystemTransfers'
    r = requests.get(url)
    for collectionSystem in r.json():
        if collectionSystem['enable'] == "1":
            destDir = build_destDir(collectionSystem['destDir'], dataObj)
            returnDirectories.append(cruiseDir + '/' + destDir)

    url = dataObj['siteRoot'] + 'api/extraDirectories/getRequiredExtraDirectories'
    r = requests.get(url)
    for requiredExtraDirectory in r.json():
        destDir = build_destDir(requiredExtraDirectory['destDir'], dataObj)
        returnDirectories.append(cruiseDir + '/' + destDir)

    url = dataObj['siteRoot'] + 'api/extraDirectories/getExtraDirectories'
    r = requests.get(url)
    for extraDirectory in r.json():
        if extraDirectory['enable'] == "1":
            destDir = build_destDir(extraDirectory['destDir'], dataObj)
            returnDirectories.append(cruiseDir + '/' + destDir)
    
    return returnDirectories

def create_directories(worker, directoryList):

    for directory in directoryList:
        try:
            os.makedirs(directory)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
                worker.stopJob()
                return False
        
    return True

def setDirectoryOwnerGroupPermissions(path, uid, gid):
    os.chown(path, uid, gid)
    for item in os.listdir(path):
        itempath = os.path.join(path, item)
        if os.path.isdir(itempath):
            try:
                setDirectoryOwnerGroupPermissions(itempath, uid, gid)
            except OSError:
                return False
        elif os.path.isfile(itempath):
            try:
                os.chown(itempath, uid, gid)
            except OSError:
                return False
    return True

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
    payload = {'jobName': tasks[job.task],'jobPid': jobPID}
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
        return True
    
    def stopJob(self):
        self.stop = True


def task_callback(gearman_worker, job):

    job_results = {'parts':[]}

    dataObj = json.loads(job.data)
    #print 'DECODED:', json.dumps(dataObj, indent=2)
    
    gearman_worker.send_job_status(job, 1, 10)
    
    cruiseDir = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+dataObj['cruiseID']
    warehouseUser = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseUsername']
    
    if not os.path.exists(cruiseDir):
        job_results['parts'].append({"partName": "Verify Cruise Directory does not exists", "result": "Success"})
    else:
        job_results['parts'].append({"partName": "Verify Cruise Directory does not exists", "result": "Fail"})
        return json.dumps(job_results)
        
    gearman_worker.send_job_status(job, 2, 10)

    directoryList = build_directorylist(dataObj)
    #print 'DECODED:', json.dumps(directoryList, indent=2)
    
    job_results['parts'].append({"partName": "Build Directory List", "result": "Success"})
    
    gearman_worker.send_job_status(job, 5, 10)
    
    if create_directories(gearman_worker, directoryList):
        job_results['parts'].append({"partName": "Create Directories", "result": "Success"})
    else:
        job_results['parts'].append({"partName": "Create Directories", "result": "Fail"})

    gearman_worker.send_job_status(job, 7, 10)
        
    if setDirectoryOwnerGroupPermissions(cruiseDir, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid):
        job_results['parts'].append({"partName": "Set Directory Permissions", "result": "Success"})
    else:
        job_results['parts'].append({"partName": "Set Directory Permissions", "result": "Fail"})
        
    gearman_worker.send_job_status(job, 10, 10)
    
    return json.dumps(job_results)
        
def task_callback2(gearman_worker, job):

    job_results = {'parts':[]}

    dataObj = json.loads(job.data)
    #print 'DECODED:', json.dumps(dataObj, indent=2)

    gearman_worker.send_job_status(job, 1, 10)

    cruiseDir = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+dataObj['cruiseID']
    warehouseUser = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseUsername']
    
    if os.path.exists(cruiseDir):
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Success"})
    else:
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Fail"})
        return json.dumps(job_results)

    gearman_worker.send_job_status(job, 2, 10)

    directoryList = build_directorylist(dataObj)
    #print 'DECODED:', json.dumps(directoryList, indent=2)
    
    job_results['parts'].append({"partName": "Build Directory List", "result": "Success"})
    
    gearman_worker.send_job_status(job, 5, 10)

    if create_directories(gearman_worker, directoryList):
        job_results['parts'].append({"partName": "Create Missing Directories", "result": "Success"})
    else:
        job_results['parts'].append({"partName": "Create Missing Directories", "result": "Fail"})

    gearman_worker.send_job_status(job, 7, 10)

    if setDirectoryOwnerGroupPermissions(cruiseDir, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid):
        job_results['parts'].append({"partName": "Set Directory Permissions", "result": "Success"})
    else:
        job_results['parts'].append({"partName": "Set Directory Permissions", "result": "Fail"})
        
    gearman_worker.send_job_status(job, 10, 10)

    return json.dumps(job_results)

global new_worker
new_worker = CustomGearmanWorker(['localhost:4730'])

def sigquit_handler(_signo, _stack_frame):
    print "Stopping"
    new_worker.stopJob()
    
signal.signal(signal.SIGQUIT, sigquit_handler)

new_worker.set_client_id('cruiseDirectory.py')
new_worker.register_task("createCruiseDirectory", task_callback)
new_worker.register_task("rebuildCruiseDirectory", task_callback2)
new_worker.work()