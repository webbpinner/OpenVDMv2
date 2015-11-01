# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_dataDashboard.py
#
#  DESCRIPTION:  Gearman worker tha handles the creation and update of OVDM data
#                dashboard objects.
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
import errno
import json
import requests
import hashlib
import signal
import fnmatch
import pwd
import grp
import subprocess

processingScriptDir = "/usr/local/bin/OVDM_dataProcessingScripts"
processingScriptSuffix = "_dataDashboard.py"

tasks = {
    "rebuildDataDashboard": "Rebuilding Data Dashboard",
    "updateDataDashboard": "Updating Data Dashboard"
}


def build_filelist(sourceDir):

    returnFiles = []
    for root, dirnames, filenames in os.walk(sourceDir):
        for filename in filenames:
            returnFiles.append(os.path.join(root, filename))
                
    returnFiles = [filename.replace(sourceDir + '/', '', 1) for filename in returnFiles]
    return returnFiles

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

def get_collectionSystemData(collectionSystemID, siteRoot):

    # Set Error for current tranfer in DB via API
    url = siteRoot + 'api/collectionSystemTransfers/getCollectionSystemTransfer/' + collectionSystemID
    #print url
    r = requests.get(url)
    return r.json()[0]

def get_collectionSystemsData(siteRoot):

    # Set Error for current tranfer in DB via API
    url = siteRoot + 'api/collectionSystemTransfers/getCollectionSystemTransfers'
    #print url
    r = requests.get(url)
    return r.json()


def build_DashboardDataDirPath(siteRoot):

    # Set Error for current tranfer in DB via API
    url = siteRoot + 'api/extraDirectories/getRequiredExtraDirectories'
    r = requests.get(url)
    for directory in r.json():
        if directory['name'] == 'Dashboard Data':
            return directory['destDir']
            break
    
    return ''

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
        json.dump(contents, JSONFile)

    except IOError:
        print "Error Saving JSON file"
        return False

    finally:
        #print "Closing JSON file"
        JSONFile.close()
        os.chown(filePath, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)

    return True

#def updateDB(siteRoot, cruiseID):
    
#    url = siteRoot + 'api/dataDashboard/updateDataDashboardObjectsFromManifest/' + cruiseID
    #print url
#    r = requests.get(url)
    
#    if r.json()[0].get('error'):
#        print r.json()[0]['error']
#        return False
#    return True

def setError_tasks(job, taskID):
    dataObj = json.loads(job.data)

    # Set Error for current tranfer in DB via API
    url = dataObj['siteRoot'] + 'api/tasks/setErrorTask/' + taskID
    r = requests.get(url)
    
    url = dataObj['siteRoot'] + 'api/messages/newMessage'
    payload = {'message': 'Error: ' + job.task}
    r = requests.post(url, data=payload)

def setRunning_tasks(job, taskID):
    dataObj = json.loads(job.data)
    jobPID = os.getpid()

    # Set Error for the tasks in DB via API
    url = dataObj['siteRoot'] + 'api/tasks/setRunningTask/' + taskID
    payload = {'jobPid': jobPID}
    r = requests.post(url, data=payload)

    # Add Job to DB via API
    url = dataObj['siteRoot'] + 'api/gearman/newJob/' + job.handle
    payload = {'jobName': tasks[job.task],'jobPid': jobPID}
    r = requests.post(url, data=payload)

def setIdle_tasks(job, taskID):
    dataObj = json.loads(job.data)

    # Set Error for the tasks in DB via API
    url = dataObj['siteRoot'] + 'api/tasks/setIdleTask/' + taskID
    r = requests.get(url)

def clearError_tasks(job, taskID):
    dataObj = json.loads(job.data)
    url = dataObj['siteRoot'] + 'api/tasks/getTask/' + taskID
    r = requests.get(url)
    for tasks in r.json():
        if tasks['status'] == '3':
            # Clear Error for the tasks in DB via API
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
        setRunning_tasks(current_job, self.taskID)
        return super(CustomGearmanWorker, self).on_job_execute(current_job)
            

    def on_job_exception(self, current_job, exc_info):
        print "Job failed, CAN stop last gasp GEARMAN_COMMAND_WORK_FAIL"
        self.send_job_data(current_job, json.dumps([{"partName": "Unknown Part of Task", "result": "Fail"}]))
        setError_tasks(current_job, self.taskID)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        return super(CustomGearmanWorker, self).on_job_exception(current_job, exc_info)

    def on_job_complete(self, current_job, job_result):
        resultObj = json.loads(job_result)
        print "Job complete, CAN stop last gasp GEARMAN_COMMAND_WORK_COMPLETE"
        #print json.dumps(job_result, indent=2)
        
        if resultObj['parts'][-1]['result'] == "Fail": # Final Verdict
            if resultObj['parts'][-1]['partName'] == "Dashboard Processing File Located":
                print "No processing script found for this collection system"
                setIdle_tasks(current_job, self.taskID)
            else:
                print "but something prevented the tasks from successfully completing..."
                setError_tasks(current_job,  self.taskID)
        else:
            setIdle_tasks(current_job, self.taskID)
            
        return super(CustomGearmanWorker, self).send_job_complete(current_job, job_result)

    def after_poll(self, any_activity):
        self.stop = False
        self.taskID = "0"
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

def task_callback(gearman_worker, job):

    job_results = {'parts':[]}
    

    dataObj = json.loads(job.data)
    #print 'DECODED dataObj:', json.dumps(dataObj, indent=2)
    
    gearman_worker.send_job_status(job, 5, 100)
    
    baseDir = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']
    cruiseID = dataObj['cruiseID']
    warehouseUser = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseUsername']
    dataDashboardDir = build_DashboardDataDirPath(dataObj['siteRoot'])
    dataDashboardManifestFilename = 'manifest.json'
    dataDashboardManifestFilePath = baseDir + '/' + cruiseID + '/' +  dataDashboardDir + '/' + dataDashboardManifestFilename    
    collectionSystem = get_collectionSystemData(dataObj['collectionSystemID'], dataObj['siteRoot'])
    #print 'DECODED collectionSystem:', json.dumps(collectionSystem, indent=2)
    
    newManifestEntries = []

    #check for processing file
    processingScriptFilename = processingScriptDir + '/' + collectionSystem['name'].replace(' ','') + processingScriptSuffix
    
    if os.path.isfile(processingScriptFilename):
        job_results['parts'].append({"partName": "Dashboard Processing File Located", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Dashboard Processing File Located", "result": "Fail"})
        return json.dumps(job_results)

    gearman_worker.send_job_status(job, 1, 10)
    #print 'DECODED:', json.dumps(fileList, indent=2)

    #build filelist
    fileList = []

    if dataObj['files']['new'] or dataObj['files']['updated']:
        fileList = dataObj['files']['new']
        fileList += dataObj['files']['updated']
        job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Pass"})
        #print 'DECODED fileList:', json.dumps(fileList, indent=2)

    else:
        job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Pass"})
        #print "No new or updated files to process"
        return json.dumps(job_results)

    fileCount = len(fileList)
    index = 1
    for filename in fileList:
        #print "Processing file: " + filename
        jsonFileName = filename.split('.')[0] + '.json'
        rawFilePath = baseDir + '/' + cruiseID + '/' + filename
        jsonFilePath = baseDir + '/' + cruiseID + '/' + dataDashboardDir + '/' + jsonFileName
        
        proc = subprocess.Popen(['python', processingScriptFilename, '--dataType', rawFilePath], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = proc.communicate()
        #print "DataType Out: " + out
        #print "DataType Err: " + err
        
        if out:
            dd_type = out.rstrip('\n')
            #print " Found to be type: " + dd_type

            proc = subprocess.Popen(['python', processingScriptFilename, rawFilePath], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            out, err = proc.communicate()
            #print "JSONProc Out: " + out
            #print "JSONProc Err: " + err

            if out:
                #print " JSON-formatted version created."
                try:
                    outObj = json.loads(out)
                    if output_JSONDataToFile(jsonFilePath, outObj, warehouseUser):
                        newManifestEntries.append({"type":dd_type, "dd_json": cruiseID + '/' + dataDashboardDir + '/' + jsonFileName, "raw_data":cruiseID + '/' + filename})
                except:
                    print "Error parsing JSON output from file " + filename
                    job_results['parts'].append({"partName": "Parsing JSON output from file " + filename, "result": "Fail"})
                    continue
            else:
                print "No JSON output recieved from file " + filename
                job_results['parts'].append({"partName": "Parsing JSON output from file " + filename, "result": "Fail"})
                if err:
                    print err
        else:
            print " *** NO data type returned from processing script for file: " + filename + " ***"
            if err:
                print err

        gearman_worker.send_job_status(job, int(round(10 + (70*index/fileCount),0)), 100)
        index += 1

    gearman_worker.send_job_status(job, 8, 10)
    
    if newManifestEntries:
        
        try:
            #print "Open Dashboard Manifest file: " + dataDashboardManifestFilePath
            DashboardManifestFile = open(dataDashboardManifestFilePath, 'r')
            
            existingManifestEntries = json.load(DashboardManifestFile)

        except IOError:
            print "Error Reading Dashboard Manifest file"
            job_results['parts'].append({"partName": "Reading pre-existing Dashboard manifest file", "result": "Fail"})
            return json.dumps(job_results)

        finally:
            #print "Closing Dashboard Manifest file"
            DashboardManifestFile.close()
            job_results['parts'].append({"partName": "Reading pre-existing Dashboard manifest file", "result": "Pass"})

        #print "DECODED - existing dashboard manifest: " + json.dumps(existingManifestEntries)

        for newEntry in newManifestEntries:
            updated = False
            for existingEntry in existingManifestEntries:
                if newEntry['raw_data'] == existingEntry['raw_data']:
                    updated = True
                    break
        
            if not updated:
                #print "Row Added"
                existingManifestEntries.append(newEntry)
                
        ### need to add delete code here ###
        
        
        #print 'DECODED  - Updated Manifest Entries:', json.dumps(existingManifestEntries)
        if output_JSONDataToFile(dataDashboardManifestFilePath, existingManifestEntries, warehouseUser):
            job_results['parts'].append({"partName": "Writing Dashboard manifest file", "result": "Pass"})

            #if updateDB(dataObj['siteRoot'], cruiseID):
            #    job_results['parts'].append({"partName": "Updating Database", "result": "Pass"})
            #else:
            #    job_results['parts'].append({"partName": "Updating Database", "result": "Fail"})
            #    return json.dumps(job_results)
        else:
            job_results['parts'].append({"partName": "Writing Dashboard manifest file", "result": "Fail"})
            return json.dumps(job_results)
        
    gearman_worker.send_job_status(job, 9, 10)

    if(setDirectoryOwnerGroupPermissions(baseDir + '/' + cruiseID + '/' +  dataDashboardDir, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)):
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Pass"})
    else:
        print "Error Setting file/directory ownership"
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Fail"})
        
    gearman_worker.send_job_status(job, 10, 10)

    return json.dumps(job_results)    
        
def task_callback2(gearman_worker, job):

    job_results = {'parts':[]}

    dataObj = json.loads(job.data)
    #print 'DECODED:', json.dumps(dataObj, indent=2)

    gearman_worker.send_job_status(job, 1, 10)
    
    baseDir = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']
    cruiseID = dataObj['cruiseID']
    warehouseUser = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseUsername']
    dataDashboardDir = build_DashboardDataDirPath(dataObj['siteRoot'])
    dataDashboardManifestFilename = 'manifest.json'
    dataDashboardManifestFilePath = baseDir + '/' + cruiseID + '/' +  dataDashboardDir + '/' + dataDashboardManifestFilename
    collectionSystems = get_collectionSystemsData(dataObj['siteRoot'])

    gearman_worker.send_job_status(job, 1, 10)

    newManifestEntries = []

    collectionSystemCount = len(collectionSystems)
    collectionSystemIndex = 1
    for collectionSystem in collectionSystems:
    
        #print 'DECODED:', json.dumps(collectionSystem, indent=2)

        #check for processing file
        processingScriptFilename = processingScriptDir + '/' + collectionSystem['name'].replace(' ','') + processingScriptSuffix
        #print 'DECODED:', processingScriptFilename
    
        if not os.path.isfile(processingScriptFilename):
            gearman_worker.send_job_status(job, int(round(10 + (80*collectionSystemIndex/collectionSystemCount),0)), 100)
            collectionSystemIndex += 1
            continue
            
        #gearman_worker.send_job_status(job, 2, 10)
        #print 'DECODED:', json.dumps(fileList, indent=2)

        #build filelist
        fileList = build_filelist(baseDir + '/' + cruiseID + '/' + collectionSystem['destDir'])
        fileCount = len(fileList)
        fileIndex = 1
        #print 'DECODED:', json.dumps(fileList, indent=2)
        
        for filename in fileList:
            #print "Processing file: " + filename
            jsonFileName = filename.split('.')[0] + '.json'
            rawFilePath = baseDir + '/' + cruiseID + '/' + collectionSystem['destDir'] + '/' + filename
            jsonFilePath = baseDir + '/' + cruiseID + '/' + dataDashboardDir + '/' + collectionSystem['destDir'] + '/' + jsonFileName
            
            #print "Processing file: " + rawFilePath
        
            proc = subprocess.Popen(['python', processingScriptFilename, '--dataType', rawFilePath], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            out, err = proc.communicate()
            #print "DataType Out: " + out
            #print "DataType Err: " + err
        
            if out:
                dd_type = out.rstrip('\n')
                #print " Found to be type: " + dd_type

                proc = subprocess.Popen(['python', processingScriptFilename, rawFilePath], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                out, err = proc.communicate()
                #print "JSONProc Out: " + out
                #print "JSONProc Err: " + err

                if out:
                    try:
                        outObj = json.loads(out)
                        if output_JSONDataToFile(jsonFilePath, outObj, warehouseUser):
                            newManifestEntries.append({"type":dd_type, "dd_json": cruiseID + '/' + dataDashboardDir + '/' + collectionSystem['destDir'] + '/' + jsonFileName, "raw_data":cruiseID + '/' + collectionSystem['destDir'] + '/' +filename})
                    except:
                        print "Error parsing JSON output from file " + filename
                        job_results['parts'].append({"partName": "Parsing JSON output from file " + filename, "result": "Fail"})
                        continue

                else:
                    print "No JSON output recieved from file " + filename
                    job_results['parts'].append({"partName": "Parsing JSON output from file " + filename, "result": "Fail"})
                    if err:
                        print err
            else:
                #print " *** NO data type returned from processing script ***"
                if err:
                    print err
                    
            gearman_worker.send_job_status(job, int(round(10 + (70*collectionSystemIndex/collectionSystemCount),0)), 100)
            fileIndex += 1
            
            if gearman_worker.stop:
                print "Stopping"
                break

        collectionSystemIndex += 1

    
    gearman_worker.send_job_status(job, 8, 10)
    
    if(setDirectoryOwnerGroupPermissions(baseDir + '/' + cruiseID + '/' +  dataDashboardDir, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)):
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Pass"})
    else:
        print "Error Setting file/directory ownership"
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Fail"})
    
    gearman_worker.send_job_status(job, 9, 10)
    
    try:
        #print "Open Data Dashboard Manifest file"
        DataDashboardManifest = open(dataDashboardManifestFilePath, 'w')
        json.dump(newManifestEntries, DataDashboardManifest)

    except IOError:
        print "Error Saving Data Dashboard Manifest file"
        job_results['parts'].append({"partName": "Writing Data Dashboard Manifest file", "result": "Fail"})
        DataDashboardManifest.close()
        return json.dumps(job_results)

    finally:
        #print "Closing Data Dashboard Manifest file"
        DataDashboardManifest.close()
        os.chown(dataDashboardManifestFilePath, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)
        job_results['parts'].append({"partName": "Writing Data Dashboard Manifest file", "result": "Pass"})
        gearman_worker.send_job_status(job, 95, 100)

    #print 'Updating DB'  
    #updateDB(dataObj['siteRoot'], cruiseID)
    
    gearman_worker.send_job_status(job, 10, 10)
    
    return json.dumps(job_results)

global new_worker
new_worker = CustomGearmanWorker(['localhost:4730'])

def sigquit_handler(_signo, _stack_frame):
    print "Stopping"
    new_worker.stopTask()
    
def sigint_handler(_signo, _stack_frame):
    print "Quitting"
    new_worker.quitWorker()
    
signal.signal(signal.SIGQUIT, sigquit_handler)

signal.signal(signal.SIGINT, sigint_handler)

new_worker.set_client_id('dataDashboard.py')
new_worker.register_task("updateDataDashboard", task_callback)
new_worker.register_task("rebuildDataDashboard", task_callback2)
new_worker.work()
