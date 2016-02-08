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
#     REVISION:  2016-02-05
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
import errno
import json
import signal
import pwd
import grp
import time
import subprocess
import openvdm

#processingScriptDir = "/usr/local/bin/OVDM_dataProcessingScripts"
#processingScriptSuffix = "_dataDashboard.py"

taskLookup = {
    "rebuildDataDashboard": "Rebuilding Data Dashboard",
    "updateDataDashboard": "Updating Data Dashboard"
}

dataDashboardManifestFilename = 'manifest.json'



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

def build_DashboardDataDirPath(worker):

    # Set Error for current tranfer in DB via API
    directories = worker.OVDM.getRequiredExtraDirectories()
    for directory in directories:
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
            self.OVDM.sendMsg(taskLookup[current_job.task] + ' failed: Unknown Part of Task')
        
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
                    self.OVDM.sendMsg(taskLookup[current_job.task] + ' failed: ' + resultObj['parts'][-1]['partName'])
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

def task_updateDataDashboard(worker, job):

    job_results = {'parts':[]}
    
    payloadObj = json.loads(job.data)
    #print 'DECODED payloadObj:', json.dumps(payloadObj, indent=2)
    
    shipboardDataWarehouseConfig = worker.OVDM.getShipboardDataWarehouseConfig()
    baseDir = shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    warehouseUser = shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    dataDashboardDir = build_DashboardDataDirPath(worker)
    dataDashboardManifestFilePath = baseDir + '/' + worker.cruiseID + '/' +  dataDashboardDir + '/' + dataDashboardManifestFilename
    collectionSystemTransfer = worker.OVDM.getCollectionSystemTransfer(payloadObj['collectionSystemTransferID'])

    worker.send_job_status(job, 5, 100)

    #print 'DECODED collectionSystemTransfer:', json.dumps(collectionSystemTransfer, indent=2)
    
    newManifestEntries = []

    #check for processing file
    processingScriptFilename = worker.OVDM.getDashboardDataProcessingScriptDir() + '/' + collectionSystemTransfer['name'].replace(' ','') + worker.OVDM.getDashboardDataProcessingScriptSuffix()
    #print "processingScriptFilename: " + processingScriptFilename
    
    if os.path.isfile(processingScriptFilename):
        job_results['parts'].append({"partName": "Dashboard Processing File Located", "result": "Pass"})
    else:
        #job_results['parts'].append({"partName": "Dashboard Processing File Located", "result": "Fail"})
        return json.dumps(job_results)

    worker.send_job_status(job, 10, 100)
    #print 'DECODED:', json.dumps(fileList, indent=2)

    #build filelist
    fileList = []

    if payloadObj['files']['new'] or payloadObj['files']['updated']:
        fileList = payloadObj['files']['new']
        fileList += payloadObj['files']['updated']
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
        rawFilePath = baseDir + '/' + worker.cruiseID + '/' + filename
        jsonFilePath = baseDir + '/' + worker.cruiseID + '/' + dataDashboardDir + '/' + jsonFileName
        
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
                        newManifestEntries.append({"type":dd_type, "dd_json": worker.cruiseID + '/' + dataDashboardDir + '/' + jsonFileName, "raw_data":worker.cruiseID + '/' + filename})
                except:
                    print "Error parsing JSON output from file " + filename
                    job_results['parts'].append({"partName": "Parsing JSON output from file " + filename, "result": "Fail"})
                    continue
            else:
                #print "No JSON output recieved from file " + filename
                job_results['parts'].append({"partName": "Parsing JSON output from file " + filename, "result": "Fail"})
                if err:
                    print err
        else:
            #print " *** NO data type returned from processing script for file: " + filename + " ***"
            if err:
                print err

        worker.send_job_status(job, int(round(10 + (70*index/fileCount),0)), 100)
        index += 1

    worker.send_job_status(job, 8, 10)
    
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
        else:
            job_results['parts'].append({"partName": "Writing Dashboard manifest file", "result": "Fail"})
            return json.dumps(job_results)
        
    worker.send_job_status(job, 9, 10)

    if(setDirectoryOwnerGroupPermissions(baseDir + '/' + worker.cruiseID + '/' +  dataDashboardDir, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)):
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Pass"})
    else:
        print "Error Setting file/directory ownership"
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Fail"})
        
    worker.send_job_status(job, 10, 10)

    return json.dumps(job_results)    
        
def task_rebuildDataDashboard(worker, job):

    job_results = {'parts':[]}
    
    payloadObj = json.loads(job.data)
    #print 'DECODED dataObj:', json.dumps(payloadObj, indent=2)
    
    shipboardDataWarehouseConfig = worker.OVDM.getShipboardDataWarehouseConfig()
    baseDir = shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    warehouseUser = shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    dataDashboardDir = build_DashboardDataDirPath(worker)
    dataDashboardManifestFilePath = baseDir + '/' + worker.cruiseID + '/' +  dataDashboardDir + '/' + dataDashboardManifestFilename
    collectionSystemTransfers = worker.OVDM.getCollectionSystemTransfers()
    #print 'DECODED collectionSystemTransfers:', json.dumps(collectionSystemTransfers, indent=2)

    worker.send_job_status(job, 5, 100)

    newManifestEntries = []

    collectionSystemTransferCount = len(collectionSystemTransfers)
    collectionSystemTransferIndex = 1
    for collectionSystemTransfer in collectionSystemTransfers:
    
        #print 'DECODED:', json.dumps(collectionSystemTransfer, indent=2)

        #check for processing file
        processingScriptFilename = worker.OVDM.getDashboardDataProcessingScriptDir() + '/' + collectionSystemTransfer['name'].replace(' ','') + worker.OVDM.getDashboardDataProcessingScriptSuffix()
        #print 'DECODED:', processingScriptFilename
    
        if not os.path.isfile(processingScriptFilename):
            worker.send_job_status(job, int(round(10 + (80*collectionSystemTransferIndex/collectionSystemTransferCount),0)), 100)
            collectionSystemTransferIndex += 1
            continue

        #build filelist
        fileList = build_filelist(baseDir + '/' + worker.cruiseID + '/' + collectionSystemTransfer['destDir'])
        fileCount = len(fileList)
        fileIndex = 1
        #print 'DECODED:', json.dumps(fileList, indent=2)
        
        for filename in fileList:
            #print "Processing file: " + filename
            jsonFileName = filename.split('.')[0] + '.json'
            rawFilePath = baseDir + '/' + worker.cruiseID + '/' + collectionSystemTransfer['destDir'] + '/' + filename
            jsonFilePath = baseDir + '/' + worker.cruiseID + '/' + dataDashboardDir + '/' + collectionSystemTransfer['destDir'] + '/' + jsonFileName
            
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
                            newManifestEntries.append({"type":dd_type, "dd_json": worker.cruiseID + '/' + dataDashboardDir + '/' + collectionSystemTransfer['destDir'] + '/' + jsonFileName, "raw_data":worker.cruiseID + '/' + collectionSystemTransfer['destDir'] + '/' +filename})
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
                    
            worker.send_job_status(job, int(round(10 + (70*collectionSystemTransferIndex/collectionSystemTransferCount),0)), 100)
            fileIndex += 1
            
            if worker.stop:
                print "Stopping"
                break

        collectionSystemTransferIndex += 1

    
    worker.send_job_status(job, 80, 100)
    
    if(setDirectoryOwnerGroupPermissions(baseDir + '/' + worker.cruiseID + '/' +  dataDashboardDir, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)):
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Pass"})
    else:
        print "Error Setting file/directory ownership"
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Fail"})
    
    worker.send_job_status(job, 90, 100)
    
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
        worker.send_job_status(job, 95, 100)
    
    worker.send_job_status(job, 10, 10)
    
    return json.dumps(job_results)

global new_worker
new_worker = OVDMGearmanWorker()

def sigquit_handler(_signo, _stack_frame):
    print "Stopping"
    new_worker.stopTask()
    
def sigint_handler(_signo, _stack_frame):
    print "Quitting"
    new_worker.quitWorker()
    
signal.signal(signal.SIGQUIT, sigquit_handler)

signal.signal(signal.SIGINT, sigint_handler)

new_worker.set_client_id('dataDashboard.py')
new_worker.register_task("updateDataDashboard", task_updateDataDashboard)
new_worker.register_task("rebuildDataDashboard", task_rebuildDataDashboard)
new_worker.work()
