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
#      VERSION:  2.1rc
#      CREATED:  2015-01-01
#     REVISION:  2016-03-07
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
import errno
import gearman
import json
import time
import signal
import pwd
import grp
import openvdm

taskLookup = {
    "createCruiseDirectory": "Creating Cruise Directory",
    "rebuildCruiseDirectory": "Updating Cruise Directory"
}


def build_destDir(worker, destDir):
    
    #print raw_destDir
    returnDestDir = destDir.replace('{cruiseID}', worker.cruiseID)
    #print returnDestDir
    return returnDestDir


def build_directorylist(worker):

    returnDirectories = []
    shipboardDataWarehouseConfig = worker.OVDM.getShipboardDataWarehouseConfig()
    cruiseDir = shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']+'/'+worker.cruiseID
    
    collectionSystemTransfers = worker.OVDM.getCollectionSystemTransfers()
    for collectionSystemTransfer in collectionSystemTransfers:
        if collectionSystemTransfer['enable'] == "1":
            destDir = build_destDir(worker, collectionSystemTransfer['destDir'])
            returnDirectories.append(cruiseDir + '/' + destDir)

    requiredExtraDirectories = worker.OVDM.getRequiredExtraDirectories()
    for requiredExtraDirectory in requiredExtraDirectories:
        destDir = build_destDir(worker, requiredExtraDirectory['destDir'])
        returnDirectories.append(cruiseDir + '/' + destDir)

    extraDirectories = worker.OVDM.getExtraDirectories()
    for extraDirectory in extraDirectories:
        if extraDirectory['enable'] == "1":
            destDir = build_destDir(worker, extraDirectory['destDir'])
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
    try:
        os.chown(path, uid, gid)
        os.chmod(path, 0755)
    except OSError:
        return False
    
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
                os.chmod(itempath, 0644)
            except OSError:
                return False
    return True

    
class OVDMGearmanWorker(gearman.GearmanWorker):
    
    def __init__(self, host_list=None):
        self.stop = False
        self.quit = False
        self.OVDM = openvdm.OpenVDM()
        self.cruiseID = ''
        self.taskID = '0'
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])
        
    def get_taskID(self, current_job):
        tasks = self.OVDM.getTasks()
        for task in tasks:
            if task['name'] == current_job.task:
                self.taskID = task['taskID']
                return True
        self.taskID = '0'
        return False
    
    def on_job_execute(self, current_job):
        self.get_taskID(current_job)
        payloadObj = json.loads(current_job.data)
        
        self.cruiseID = self.OVDM.getCruiseID()
        if len(payloadObj) > 0:
            try:
                payloadObj['cruiseID']
            except KeyError:
                self.cruiseID = self.OVDM.getCruiseID()
            else:
                self.cruiseID = payloadObj['cruiseID']

        if int(self.taskID) > 0:
            self.OVDM.setRunning_task(self.taskID, os.getpid(), current_job.handle)
        else:
            self.OVDM.trackGearmanJob(taskLookup[current_job.task], os.getpid(), current_job.handle)
            
        print "Job: " + current_job.handle + ", " + taskLookup[current_job.task] + " started at:   " + time.strftime("%D %T", time.gmtime())
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)
            

    def on_job_exception(self, current_job, exc_info):
        print "Job: " + current_job.handle + ", " + taskLookup[current_job.task] + " failed at:    " + time.strftime("%D %T", time.gmtime())
        
        self.send_job_data(current_job, json.dumps([{"partName": "Unknown Part of Task", "result": "Fail"}]))
        if int(self.taskID) > 0:
            self.OVDM.setError_task(self.taskID, "Unknown Part of Task")
        else:
            self.OVDM.sendMsg(taskLookup[current_job.task] + ' failed', 'Unknown Part of Task')
        
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)


    def on_job_complete(self, current_job, job_result):
        resultObj = json.loads(job_result)
        
        if len(resultObj['parts']) > 0:
            if resultObj['parts'][-1]['result'] == "Fail": # Final Verdict
                if int(self.taskID) > 0:
                    self.OVDM.setError_task(self.taskID, resultObj['parts'][-1]['partName'])
                else:
                    self.OVDM.sendMsg(taskLookup[current_job.task] + ' failed', resultObj['parts'][-1]['partName'])
            else:
                self.OVDM.setIdle_task(self.taskID)
        else:
            self.OVDM.setIdle_task(self.taskID)
        
            
        print "Job: " + current_job.handle + ", " + taskLookup[current_job.task] + " completed at: " + time.strftime("%D %T", time.gmtime())
            
        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_result)

    
    def after_poll(self, any_activity):
        self.stop = False
        self.taskID = '0'
        if self.quit:
            print "Quitting"
            self.shutdown()
        else:
            self.quit - False
        return True
    
    
    def stopTask(self):
        self.stop = True

    
    def quitWorker(self):
        self.stop = True
        self.quit = True


def task_createCruiseDirectory(worker, job):

    job_results = {'parts':[]}

    payloadObj = json.loads(job.data)
    #print 'DECODED payloadObj:', json.dumps(payloadObj, indent=2)
    
    worker.send_job_status(job, 1, 10)
    
    shipboardDataWarehouseConfig = worker.OVDM.getShipboardDataWarehouseConfig()
    cruiseDir = shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']+'/'+worker.cruiseID
    warehouseUser = shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
            
    if not os.path.exists(cruiseDir):
        job_results['parts'].append({"partName": "Verify Cruise Directory does not exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Cruise Directory does not exists", "result": "Fail"})
        return json.dumps(job_results)

    worker.send_job_status(job, 2, 10)

    directoryList = build_directorylist(worker)
    #print 'DECODED directoryList:', json.dumps(directoryList, indent=2)
    
    job_results['parts'].append({"partName": "Build Directory List", "result": "Pass"})
    
    worker.send_job_status(job, 5, 10)
    
    if create_directories(worker, directoryList):
        job_results['parts'].append({"partName": "Create Directories", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Create Directories", "result": "Fail"})

    worker.send_job_status(job, 7, 10)
        
    if setDirectoryOwnerGroupPermissions(cruiseDir, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid):
        job_results['parts'].append({"partName": "Set Directory Permissions", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Set Directory Permissions", "result": "Fail"})

    worker.send_job_status(job, 10, 10)
    
    return json.dumps(job_results)
        

def task_rebuildCruiseDirectory(worker, job):

    job_results = {'parts':[]}

    payloadObj = json.loads(job.data)
    #print 'DECODED payloadObj:', json.dumps(payloadObj, indent=2)

    worker.send_job_status(job, 1, 10)

    shipboardDataWarehouseConfig = worker.OVDM.getShipboardDataWarehouseConfig()
    cruiseDir = shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']+'/'+worker.cruiseID
    warehouseUser = shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    
    if os.path.exists(cruiseDir):
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Fail"})
        return json.dumps(job_results)

    worker.send_job_status(job, 2, 10)

    directoryList = build_directorylist(worker)
    #print 'DECODED directoryList:', json.dumps(directoryList, indent=2)
    
    job_results['parts'].append({"partName": "Build Directory List", "result": "Pass"})
    
    worker.send_job_status(job, 5, 10)

    if create_directories(worker, directoryList):
        job_results['parts'].append({"partName": "Create Missing Directories", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Create Missing Directories", "result": "Fail"})

    worker.send_job_status(job, 7, 10)

    if setDirectoryOwnerGroupPermissions(cruiseDir, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid):
        job_results['parts'].append({"partName": "Set Directory Permissions", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Set Directory Permissions", "result": "Fail"})
        
    worker.send_job_status(job, 10, 10)

    return json.dumps(job_results)


global new_worker
new_worker = OVDMGearmanWorker()

def sigquit_handler(_signo, _stack_frame):
    print "QUIT Signal Received"
    new_worker.stopWorker()
    

def sigint_handler(_signo, _stack_frame):
    print "INT Signal Received"
    new_worker.quitWorker()
    
    
signal.signal(signal.SIGQUIT, sigquit_handler)
signal.signal(signal.SIGINT, sigint_handler)

new_worker.set_client_id('cruiseDirectory.py')
new_worker.register_task("createCruiseDirectory", task_createCruiseDirectory)
new_worker.register_task("rebuildCruiseDirectory", task_rebuildCruiseDirectory)
new_worker.work()
