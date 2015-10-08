# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_transferLogSummary.py
#
#  DESCRIPTION:  Gearman worker that handles creations and management of the transfer
#                log summaries for filename errors, shipboard transfers and ship-to-
#                shore transfers.
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
import gearman
import shutil
import json
import requests
import hashlib
import signal
import fnmatch
import pwd
import grp

tasks = {
    "updateShipboardTransferLogSummary": "Updating Shipboard Transfer Log Summary",
    "updateShipboardFilenameErrorLogSummary": "Updating Shipboard Filename Error Log Summary",
    "updateShipToShoreTransferLogSummary": "Updating Ship-to-Shore Transfer Log Summary",
    "rebuildTransferLogSummary": "Rebuilding Transfer Log Summaries"
}

def build_logfileDirPath(cruiseDir, siteRoot):

    # Set Error for current tranfer in DB via API
    url = siteRoot + 'api/extraDirectories/getRequiredExtraDirectories'
    r = requests.get(url)
    transferLogDir = ''
    for directory in r.json():
        if directory['name'] == 'Transfer Logs':
            transferLogDir = cruiseDir + '/' + directory['destDir']
            break
    
    return transferLogDir

def build_DashboardDataDirPath(cruiseDir, siteRoot):

    # Set Error for current tranfer in DB via API
    url = siteRoot + 'api/extraDirectories/getRequiredExtraDirectories'
    r = requests.get(url)
    dashboardDataDir = ''
    for directory in r.json():
        if directory['name'] == 'Dashboard Data':
            dashboardDataDir = cruiseDir + '/' + directory['destDir']
            break
    
    return dashboardDataDir

def build_filelist(sourceDir):

    returnFiles = []
    for root, dirnames, filenames in os.walk(sourceDir):
        for filename in filenames:
            if not filename.startswith('SSDW') and not filename.endswith('_Exclude.log'):
                returnFiles.append(os.path.join(root, filename))
                
    returnFiles.sort(key=lambda x: os.stat(os.path.join(sourceDir, x)).st_mtime)
    return returnFiles

def build_shipToShoreFilelist(sourceDir):

    returnFiles = []
    for root, dirnames, filenames in os.walk(sourceDir):
        for filename in filenames:
            if filename.startswith('SSDW'):
                returnFiles.append(os.path.join(root, filename))
                
    returnFiles.sort(key=lambda x: os.stat(os.path.join(sourceDir, x)).st_mtime)
    return returnFiles

def build_filenameErrorFilelist(sourceDir):

    returnFiles = []
    for root, dirnames, filenames in os.walk(sourceDir):
        for filename in filenames:
            if filename.endswith('_Exclude.log'):
                returnFiles.append(os.path.join(root, filename))
                
    returnFiles.sort(key=lambda x: os.stat(os.path.join(sourceDir, x)).st_mtime)
    #print returnFiles
    return returnFiles
    
def setError_task(job, taskID, message=None):
    dataObj = json.loads(job.data)

    # Set Error for current tranfer in DB via API
    url = dataObj['siteRoot'] + 'api/tasks/setErrorTask/' + taskID
    r = requests.get(url)
    
    url = dataObj['siteRoot'] + 'api/messages/newMessage'
    payload = {'message': 'Error: ' + job.task}
    if message:
        payload['message'] += ': ' + message
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

def sendMsg(dataObj, message):
    
    url = dataObj['siteRoot'] + 'api/messages/newMessage'
    payload = {'message': message}
    r = requests.post(url, data=payload)

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
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        setError_task(current_job, self.taskID, "Unknown Part: " + str(exc_tb.tb_lineno))
        print(exc_type, fname, exc_tb.tb_lineno)
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
    
    def stopTransfer(self):
        self.stop = True


def task_callback(gearman_worker, job):

    job_results = {'parts':[]}

    dataObj = json.loads(job.data)
    #print 'DECODED:', json.dumps(dataObj, indent=2)

    gearman_worker.send_job_status(job, 1, 10)

    cruiseDir = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+dataObj['cruiseID']
    warehouseUser = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseUsername']
    dashboardDataDir = build_DashboardDataDirPath(cruiseDir, dataObj['siteRoot'])
    transferLogSummaryFilename = dashboardDataDir + '/' + 'TransferLogSummary.json'
    
    gearman_worker.send_job_status(job, 3, 10)
    #print 'DECODED:', json.dumps(fileList, indent=2)
        
    existingSummary = {'filenameErrors':[], 'shipboardTransfers':[], 'shipToShoreTransfers':[]}
    
    try:
        #print "Open MD5 Summary file: " + md5SummaryFilename
        TransferSummaryFile = open(transferLogSummaryFilename, 'r')
        
        with open(transferLogSummaryFilename) as data_file:    
            existingSummary = json.load(data_file)
        
    except IOError:
        print "Error Reading Transfer Log Summary file"
        job_results['parts'].append({"partName": "Reading pre-existing Transfer Log Summary file", "result": "Fail"})
        return json.dumps(job_results)

    finally:
        job_results['parts'].append({"partName": "Reading pre-existing Transfer Log Summary file", "result": "Pass"})
        gearman_worker.send_job_status(job, 7, 10)

    shipboardTransfers = {'collectionSystemName':dataObj['collectionSystemName'], 'date':dataObj['transferDate'], 'newFiles':dataObj['files']['new'], 'updatedFiles':dataObj['files']['updated'] }
    
    if shipboardTransfers['newFiles'] or shipboardTransfers['updatedFiles']:
        existingSummary['shipboardTransfers'].append(shipboardTransfers)
        
    #print 'DECODED existingHashes:', json.dumps(existingSummary, indent=2)
        
    #print 'DECODED updatedHashes:', json.dumps(existingHashes, indent=2)
    gearman_worker.send_job_status(job, 8, 10)
    
    try:
        #print "Open MD5 Summary file"
        TransferSummaryFile = open(transferLogSummaryFilename, 'w')

        #print "Saving Transfer Log Summary file"
        #sorted(student_tuples, key=itemgetter(2))
        TransferSummaryFile.write(json.dumps(existingSummary))

    except IOError:
        print "Error Saving Transfer Log Summary file"
        job_results['parts'].append({"partName": "Writing Transfer Log Summary file", "result": "Fail"})
        TransferSummaryFile.close()
        return json.dumps(job_results)    

    finally:
        #print "Closing Transfer Log Summary file"
        TransferSummaryFile.close()
        os.chown(transferLogSummaryFilename, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)
        job_results['parts'].append({"partName": "Writing Transfer Log Summary file", "result": "Pass"})

    gearman_worker.send_job_status(job, 10, 10)
    return json.dumps(job_results)

def task_callback2(gearman_worker, job):

    job_results = {'parts':[]}

    dataObj = json.loads(job.data)
    #print 'DECODED:', json.dumps(dataObj, indent=2)

    gearman_worker.send_job_status(job, 1, 10)

    cruiseDir = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+dataObj['cruiseID']
    warehouseUser = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseUsername']
    dashboardDataDir = build_DashboardDataDirPath(cruiseDir, dataObj['siteRoot'])
    transferLogSummaryFilename = dashboardDataDir + '/' + 'TransferLogSummary.json'
    
    gearman_worker.send_job_status(job, 3, 10)
    #print 'DECODED:', json.dumps(dataObj['files']['exclude'], indent=2)
        
    existingSummary = {'filenameErrors':[], 'shipboardTransfers':[], 'shipToShoreTransfers':[]}
    
    try:
        #print "Open MD5 Summary file: " + md5SummaryFilename
        TransferSummaryFile = open(transferLogSummaryFilename, 'r')
        
        with open(transferLogSummaryFilename) as data_file:    
            existingSummary = json.load(data_file)
        
    except IOError:
        print "Error Reading Transfer Log Summary file"
        job_results['parts'].append({"partName": "Reading pre-existing Transfer Log Summary file", "result": "Fail"})
        return json.dumps(job_results)

    finally:
        job_results['parts'].append({"partName": "Reading pre-existing Transfer Log Summary file", "result": "Pass"})
        gearman_worker.send_job_status(job, 7, 10)

    
    filenameErrors = {'collectionSystemName':dataObj['collectionSystemName'], 'errorFiles':dataObj['files']['exclude'] }
    #print filenameErrors
        
    index = 0
    for error in existingSummary['filenameErrors']:
        if error['collectionSystemName'] == filenameErrors['collectionSystemName']:
            if len(filenameErrors['errorFiles']) > 0:
#                existingSummary['filenameErrors'][index]['date'] = filenameErrors['date']
                existingSummary['filenameErrors'][index]['errorFiles'] = filenameErrors['errorFiles']
            else:
                del existingSummary['filenameErrors'][index]
                index -= 1
            break
        index += 1
        
    if index > len(existingSummary['filenameErrors'])-1:
        if filenameErrors['errorFiles']:
            existingSummary['filenameErrors'].append(filenameErrors)
    
    gearman_worker.send_job_status(job, 8, 10)
    
    try:
        #print "Open MD5 Summary file"
        TransferSummaryFile = open(transferLogSummaryFilename, 'w')

        #print "Saving Transfer Log Summary file"
        #sorted(student_tuples, key=itemgetter(2))
        TransferSummaryFile.write(json.dumps(existingSummary))

    except IOError:
        print "Error Saving Transfer Log Summary file"
        job_results['parts'].append({"partName": "Writing Transfer Log Summary file", "result": "Fail"})
        TransferSummaryFile.close()
        return json.dumps(job_results)    

    finally:
        #print "Closing Transfer Log Summary file"
        TransferSummaryFile.close()
        os.chown(transferLogSummaryFilename, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)
        job_results['parts'].append({"partName": "Writing Transfer Log Summary file", "result": "Pass"})

    gearman_worker.send_job_status(job, 10, 10)
    return json.dumps(job_results)

def task_callback3(gearman_worker, job):

    job_results = {'parts':[]}

    dataObj = json.loads(job.data)
    #print 'DECODED:', json.dumps(dataObj, indent=2)

    gearman_worker.send_job_status(job, 1, 10)

    cruiseDir = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+dataObj['cruiseID']
    warehouseUser = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseUsername']
    dashboardDataDir = build_DashboardDataDirPath(cruiseDir, dataObj['siteRoot'])
    transferLogSummaryFilename = dashboardDataDir + '/' + 'TransferLogSummary.json'
    
    gearman_worker.send_job_status(job, 3, 10)
        
    existingSummary = {'filenameErrors':[], 'shipboardTransfers':[], 'shipToShoreTransfers':[]}
    
    try:
        #print "Open Transfer Log Summary file: " + transferLogSummaryFilename
        TransferSummaryFile = open(transferLogSummaryFilename, 'r')
        
        with open(transferLogSummaryFilename) as data_file:    
            existingSummary = json.load(data_file)
        
    except IOError:
        print "Error Reading Transfer Log Summary file"
        job_results['parts'].append({"partName": "Reading pre-existing Transfer Log Summary file", "result": "Fail"})
        return json.dumps(job_results)

    finally:
        job_results['parts'].append({"partName": "Reading pre-existing Transfer Log Summary file", "result": "Pass"})
        gearman_worker.send_job_status(job, 7, 10)

    
    shipToShoreTransfers = {'shipToShoreTransferName':dataObj['shipToShoreTransferName'], 'date':dataObj['transferDate'], 'newFiles':dataObj['files']['new'], 'updatedFiles':dataObj['files']['updated'] }
    
    if shipToShoreTransfers['newFiles'] or shipToShoreTransfers['updatedFiles']:
        existingSummary['shipToShoreTransfers'].append(shipToShoreTransfers)
        
    gearman_worker.send_job_status(job, 8, 10)
    
    try:
        #print "Open Transfer Log Summary file"
        TransferSummaryFile = open(transferLogSummaryFilename, 'w')

        #print "Saving Transfer Log Summary file"
        TransferSummaryFile.write(json.dumps(existingSummary))

    except IOError:
        print "Error Saving Transfer Log Summary file"
        job_results['parts'].append({"partName": "Writing Transfer Log Summary file", "result": "Fail"})
        TransferSummaryFile.close()
        return json.dumps(job_results)    

    finally:
        #print "Closing Transfer Log Summary file"
        TransferSummaryFile.close()
        os.chown(transferLogSummaryFilename, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)
        job_results['parts'].append({"partName": "Writing Transfer Log Summary file", "result": "Pass"})

    gearman_worker.send_job_status(job, 10, 10)
    return json.dumps(job_results)    
        
def task_callback4(gearman_worker, job):

    job_results = {'parts':[]}

    dataObj = json.loads(job.data)
    #print 'DECODED:', json.dumps(dataObj, indent=2)

    gearman_worker.send_job_status(job, 1, 10)
    
    cruiseDir = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+dataObj['cruiseID']
    warehouseUser = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseUsername']
    dashboardDataDir = build_DashboardDataDirPath(cruiseDir, dataObj['siteRoot'])
    transferLogDir = build_logfileDirPath(cruiseDir, dataObj['siteRoot'])
    transferLogSummaryFilename = dashboardDataDir + '/' + 'TransferLogSummary.json'
    
    shipboardTransferLogfileList = build_filelist(transferLogDir)
    shipboardFilenameErrorLogfileList = build_filenameErrorFilelist(transferLogDir)
    shipToShoreTransferLogfileList = build_shipToShoreFilelist(transferLogDir)
    #print 'DECODED:', json.dumps(transferLogfileList, indent=2)
    
    newSummary = {'filenameErrors':[], 'shipboardTransfers':[], 'shipToShoreTransfers':[]}
    
    #print "Process Shipboard Transfer Logs"
    #print shipboardTransferLogfileList
    for filename in shipboardTransferLogfileList:
        try:
            #print "Processing Shipboard Transfer Logfile: " + filename
            transferLogFile = open(filename, 'r')
            transferLogFileObj =  json.load(transferLogFile)
            
            #collectionSystemName, date = os.path.basename(filename).replace('.log','').split('_')
            nameArray = os.path.basename(filename).replace('.log','').split('_')
            date = nameArray.pop();
            collectionSystemName = '_'.join(nameArray)
            
            if transferLogFileObj['new'] or transferLogFileObj['updated']:
                shipboardTransfer = {'collectionSystemName':collectionSystemName, 'date':date, 'newFiles':transferLogFileObj['new'], 'updatedFiles':transferLogFileObj['updated']}
                newSummary['shipboardTransfers'].append(shipboardTransfer)

        except IOError:
            print "Error Opening Shipboard Transfer Logfile"
            job_results['parts'].append({"partName": "Reading Transfer Log file", "result": "Fail"})
            transferLogSummaryFile.close()
            return json.dumps(job_results)

        finally:
            #print "Closing Transfer Log file"
            transferLogFile.close()
            job_results['parts'].append({"partName": "Reading Transfer Log file", "result": "Pass"})
    
    gearman_worker.send_job_status(job, 3, 10)

    #print "Process Filename Error Logs"
    for filename in shipboardFilenameErrorLogfileList:
        try:
            #print "Processing Error Logfile: " + filename
            transferLogFile = open(filename, 'r')
            transferLogFileObj =  json.load(transferLogFile)
            
            #collectionSystemName, excludeStr = os.path.basename(filename).replace('.log','').split('_')
            nameArray = os.path.basename(filename).replace('.log','').split('_')
            excludeStr = nameArray.pop();
            collectionSystemName = '_'.join(nameArray)
            index = 0
            for fileErrors in newSummary['filenameErrors']:
                if fileErrors['collectionSystemName'] == collectionSystemName:
                    del newSummary['filenameErrors'][index]
                    #print "Delete " + collectionSystemName
                    break
                index += 1

            if transferLogFileObj['exclude']:
                filenameError = {'collectionSystemName':collectionSystemName, 'errorFiles':transferLogFileObj['exclude']}
                newSummary['filenameErrors'].append(filenameError)
                #print "Add Errors from: " + collectionSystemName

        except IOError:
            print "Error Opening Error Logfile"
            job_results['parts'].append({"partName": "Reading Transfer Log file", "result": "Fail"})
            transferLogSummaryFile.close()
            return json.dumps(job_results)

        finally:
            #print "Closing Transfer Log file"
            transferLogFile.close()
            job_results['parts'].append({"partName": "Reading Transfer Log file", "result": "Pass"})
            gearman_worker.send_job_status(job, 7, 10)

    #print "Process Ship-to-shore Transfer Logs"
    for filename in shipToShoreTransferLogfileList:
        try:
            #print "Processing Ship-to-Shore Transfer Logfile: " + filename
            transferLogFile = open(filename, 'r')
            transferLogFileObj =  json.load(transferLogFile)
            
            shipToShoreTransferName, date = os.path.basename(filename).replace('.log','').split('_')
            
            if transferLogFileObj['new'] or transferLogFileObj['updated']:
                shipToShoreTransfer = {'shipToShoreTransferName':shipToShoreTransferName, 'date':date, 'newFiles':transferLogFileObj['new'], 'updatedFiles':transferLogFileObj['updated']}
                newSummary['shipToShoreTransfers'].append(shipToShoreTransfer)

        except IOError:
            print "Error Opening Ship-to-Shore Transfer Logfile"
            job_results['parts'].append({"partName": "Reading Transfer Log file", "result": "Fail"})
            transferLogSummaryFile.close()
            return json.dumps(job_results)

        finally:
            #print "Closing Transfer Log file"
            transferLogFile.close()
            job_results['parts'].append({"partName": "Reading Transfer Log file", "result": "Pass"})
            gearman_worker.send_job_status(job, 7, 10)
    
    try:
        #print "Open Transfer Log Summary file"
        transferLogSummaryFile = open(transferLogSummaryFilename, 'w')
        transferLogSummaryFile.write(json.dumps(newSummary))
                
    except IOError:
        print "Error Saving Transfer Log Summary file"
        job_results['parts'].append({"partName": "Writing Transfer Log Summary file", "result": "Fail"})
        transferLogSummaryFile.close()
        return json.dumps(job_results)

    finally:
        #print "Closing Transfer Log Summary file"
        transferLogSummaryFile.close()
        os.chown(transferLogSummaryFilename, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)
        job_results['parts'].append({"partName": "Writing Transfer Log Summary file", "result": "Pass"})
        gearman_worker.send_job_status(job, 7, 10)

    gearman_worker.send_job_status(job, 10, 10)
    
    return json.dumps(job_results)

global new_worker
new_worker = CustomGearmanWorker(['localhost:4730'])

def sigquit_handler(_signo, _stack_frame):
    print "Stopping"
    new_worker.stopTransfer()
    
signal.signal(signal.SIGQUIT, sigquit_handler)

new_worker.set_client_id('transferLogSummary.py')
new_worker.register_task("updateShipboardTransferLogSummary", task_callback)
new_worker.register_task("updateShipboardFilenameErrorLogSummary", task_callback2)
new_worker.register_task("updateShipToShoreTransferLogSummary", task_callback3)
new_worker.register_task("rebuildTransferLogSummary", task_callback4)

new_worker.work()
