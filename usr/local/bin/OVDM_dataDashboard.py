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
from __future__ import print_function
import os
import sys
import gearman
import shutil
import errno
import json
import argparse
import signal
import pwd
import grp
import time
import subprocess
import openvdm

DEBUG = False

taskLookup = {
    "rebuildDataDashboard": "Rebuilding Data Dashboard",
    "updateDataDashboard": "Updating Data Dashboard"
}

dataDashboardManifestFN = 'manifest.json'

def debugPrint(*args, **kwargs):
    global DEBUG
    if DEBUG:
        errPrint(*args, **kwargs)


def errPrint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


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
            errPrint("Unable to create directory for dashboard data file")
            return False
    finally:
        os.chown(os.path.dirname(filePath), pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)

    try:
        JSONFile = open(filePath, 'w')
        debugPrint("Saving output to: ", filePath)
        json.dump(contents, JSONFile)

    except IOError:
        errPrint("Error Saving JSON file")
        return False

    finally:
        #debugPrint("Closing JSON file")
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

        errPrint("Job: " + current_job.handle + ", " + taskLookup[current_job.task] + " started at:   " + time.strftime("%D %T", time.gmtime()))
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)


    def on_job_exception(self, current_job, exc_info):
        errPrint("Job: " + current_job.handle + ", " + taskLookup[current_job.task] + " failed at:    " + time.strftime("%D %T", time.gmtime()))

        self.send_job_data(current_job, json.dumps([{"partName": "Unknown Part of Task", "result": "Fail"}]))
        if int(self.taskID) > 0:
            self.OVDM.setError_task(self.taskID, "Unknown Part of Task")
        else:
            self.OVDM.sendMsg(taskLookup[current_job.task] + ' failed', 'Unknown Part of Task')
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        errPrint(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)


    def on_job_complete(self, current_job, job_result):
        resultObj = json.loads(job_result)

        gm_client = gearman.GearmanClient([self.OVDM.getGearmanServer()])

        jobData = {'cruiseID':'', 'collectionSystemTransferID':''}
        jobData['cruiseID'] = self.cruiseID

        if current_job.task == 'updateDataDashboard':

            payloadObj = json.loads(current_job.data)
            jobData['collectionSystemTransferID'] = payloadObj['collectionSystemTransferID']
            jobData['files'] = payloadObj['files']

            for task in self.OVDM.getTasksForHook(current_job.task):
                debugPrint(task)
                submitted_job_request = gm_client.submit_job(task, json.dumps(jobData), background=True)

        elif current_job.task == 'rebuildDataDashboard':

            collectionSystemTransfers = self.OVDM.getCollectionSystemTransfers()
            for collectionSystemTransfer in collectionSystemTransfers:
                jobData['collectionSystemTransferID'] = collectionSystemTransfer['collectionSystemTransferID']
                for task in self.OVDM.getTasksForHook(current_job.task):
                    debugPrint(task)
                    submitted_job_request = gm_client.submit_job(task, json.dumps(jobData), background=True)

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

        errPrint("Job: " + current_job.handle + ", " + taskLookup[current_job.task] + " completed at: " + time.strftime("%D %T", time.gmtime()))

        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_result)


    def after_poll(self, any_activity):
        self.stop = False
        self.taskID = '0'
        if self.quit:
            errPrint("Quitting")
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
    debugPrint('DECODED payloadObj:', json.dumps(payloadObj, indent=2))

    shipboardDataWarehouseConfig = worker.OVDM.getShipboardDataWarehouseConfig()
    baseDir = shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    warehouseUser = shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    dataDashboardDir = build_DashboardDataDirPath(worker)
    dataDashboardManifestFilePath = baseDir + '/' + worker.cruiseID + '/' +  dataDashboardDir + '/' + dataDashboardManifestFN
    collectionSystemTransfer = worker.OVDM.getCollectionSystemTransfer(payloadObj['collectionSystemTransferID'])

    worker.send_job_status(job, 5, 100)

    debugPrint('DECODED collectionSystemTransfer:', json.dumps(collectionSystemTransfer, indent=2))

    newManifestEntries = []
    removeManifestEntries = []

    #check for processing file
    processingScriptFilename = worker.OVDM.getDashboardDataProcessingScriptDir() + '/' + collectionSystemTransfer['name'].replace(' ','') + worker.OVDM.getDashboardDataProcessingScriptSuffix()
    debugPrint("processingScriptFilename: " + processingScriptFilename)

    if os.path.isfile(processingScriptFilename):
        job_results['parts'].append({"partName": "Dashboard Processing File Located", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Dashboard Processing File Located", "result": "Fail"})
        return json.dumps(job_results)

    worker.send_job_status(job, 10, 100)

    #build filelist
    fileList = []

    if payloadObj['files']['new'] or payloadObj['files']['updated']:
        fileList = payloadObj['files']['new']
        fileList += payloadObj['files']['updated']
        job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Pass"})
        debugPrint('DECODED fileList:', json.dumps(fileList, indent=2))

    else:
        job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Pass"})
        debugPrint("No new or updated files to process")
        return json.dumps(job_results)

    fileCount = len(fileList)
    index = 1
    for filename in fileList:
        debugPrint("Processing file: " + filename)
        jsonFileName = filename.split('.')[0] + '.json'
        rawFilePath = baseDir + '/' + worker.cruiseID + '/' + filename
        jsonFilePath = baseDir + '/' + worker.cruiseID + '/' + dataDashboardDir + '/' + jsonFileName

        if os.stat(rawFilePath).st_size == 0:
            debugPrint("File is empty")
            continue

        command = ['python', processingScriptFilename, '--dataType', rawFilePath]

        s = ' '
        debugPrint(s.join(command))

        proc = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = proc.communicate()

        if out:
            dd_type = out.rstrip('\n')
            debugPrint("Found to be type: " + dd_type)

            command = ['python', processingScriptFilename, rawFilePath]

            s = ' '
            debugPrint(s.join(command))

            proc = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            out, err = proc.communicate()
            #print "JSONProc Out: " + out
            #print "JSONProc Err: " + err

            if out:
                try:
                    outObj = json.loads(out)
                except:
                    errPrint("Error parsing JSON output from file " + filename)
                    job_results['parts'].append({"partName": "Parsing JSON output from file " + filename, "result": "Fail"})
                    continue
                else:
                    if 'error' in outObj:
                        errorTitle = 'Datafile Parsing error'
                        errorBody = outObj['error']
                        errPrint(errorTitle + ': ', errorBody)
                        worker.OVDM.sendMsg(errorTitle,errorBody)
                    elif output_JSONDataToFile(jsonFilePath, outObj, warehouseUser):
                        newManifestEntries.append({"type":dd_type, "dd_json": worker.cruiseID + '/' + dataDashboardDir + '/' + jsonFileName, "raw_data":worker.cruiseID + '/' + filename})
            else:
                errPrint("No JSON output recieved from file " + filename)
                removeManifestEntries.append({"dd_json": worker.cruiseID + '/' + dataDashboardDir + '/' + jsonFileName, "raw_data":worker.cruiseID + '/' + filename})

                #job_results['parts'].append({"partName": "Parsing JSON output from file " + filename, "result": "Fail"})
                if err:
                    errPrint(err)
        else:
            debugPrint("File is of unknown datatype")
            removeManifestEntries.append({"dd_json": worker.cruiseID + '/' + dataDashboardDir + '/' + jsonFileName, "raw_data":worker.cruiseID + '/' + filename})

            if err:
                errPrint(err)

        worker.send_job_status(job, int(round(10 + (70*index/fileCount),0)), 100)
        index += 1

    worker.send_job_status(job, 8, 10)

    if newManifestEntries:

        try:
            debugPrint("Open Dashboard Manifest file: " + dataDashboardManifestFilePath)
            DashboardManifestFile = open(dataDashboardManifestFilePath, 'r')

            existingManifestEntries = json.load(DashboardManifestFile)

        except IOError:
            errPrint("Error Reading Dashboard Manifest file")
            job_results['parts'].append({"partName": "Reading pre-existing Dashboard manifest file", "result": "Fail"})
            return json.dumps(job_results)

        finally:
            debugPrint("Closing Dashboard Manifest file")
            DashboardManifestFile.close()
            job_results['parts'].append({"partName": "Reading pre-existing Dashboard manifest file", "result": "Pass"})

        #debugPrint("DECODED - existing dashboard manifest: " + json.dumps(existingManifestEntries))

        for removeEntry in removeManifestEntries:
            for idx, existingEntry in enumerate(existingManifestEntries):
                if removeEntry['raw_data'] == existingEntry['raw_data']:
                    del existingManifestEntries[idx]
                    debugPrint("Row Deleted")

                    if os.path.isfile(removeEntry['dd_json']):
                        os.remove(removeEntry['dd_json'])
                        debugPrint("Orphaned dd_json file deleted")
                    break

        for newEntry in newManifestEntries:
            updated = False
            for existingEntry in existingManifestEntries:
                if newEntry['raw_data'] == existingEntry['raw_data']:
                    updated = True
                    debugPrint("Row Updated")
                    break

            if not updated:
                debugPrint("Row Added")
                existingManifestEntries.append(newEntry)

        #debugPrint('DECODED  - Updated Manifest Entries:', json.dumps(existingManifestEntries))
        if output_JSONDataToFile(dataDashboardManifestFilePath, existingManifestEntries, warehouseUser):
            job_results['parts'].append({"partName": "Writing Dashboard manifest file", "result": "Pass"})
        else:
            job_results['parts'].append({"partName": "Writing Dashboard manifest file", "result": "Fail"})
            return json.dumps(job_results)

    worker.send_job_status(job, 9, 10)

    if(setDirectoryOwnerGroupPermissions(baseDir + '/' + worker.cruiseID + '/' +  dataDashboardDir, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)):
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Pass"})
    else:
        errPrint("Error Setting file/directory ownership")
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Fail"})

    worker.send_job_status(job, 10, 10)

    return json.dumps(job_results)


def task_rebuildDataDashboard(worker, job):

    job_results = {'parts':[]}

    payloadObj = json.loads(job.data)
    debugPrint('DECODED dataObj:', json.dumps(payloadObj, indent=2))

    shipboardDataWarehouseConfig = worker.OVDM.getShipboardDataWarehouseConfig()
    baseDir = shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    warehouseUser = shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    dataDashboardDir = build_DashboardDataDirPath(worker)
    dataDashboardManifestFilePath = baseDir + '/' + worker.cruiseID + '/' +  dataDashboardDir + '/' + dataDashboardManifestFN
    collectionSystemTransfers = worker.OVDM.getCollectionSystemTransfers()
    debugPrint('DECODED collectionSystemTransfers:', json.dumps(collectionSystemTransfers, indent=2))

    worker.send_job_status(job, 5, 100)

    newManifestEntries = []

    collectionSystemTransferCount = len(collectionSystemTransfers)
    collectionSystemTransferIndex = 1
    for collectionSystemTransfer in collectionSystemTransfers:

        debugPrint('DECODED:', json.dumps(collectionSystemTransfer, indent=2))

        #check for processing file
        processingScriptFilename = worker.OVDM.getDashboardDataProcessingScriptDir() + '/' + collectionSystemTransfer['name'].replace(' ','') + worker.OVDM.getDashboardDataProcessingScriptSuffix()
        debugPrint('DECODED:', processingScriptFilename)

        if not os.path.isfile(processingScriptFilename):
            worker.send_job_status(job, int(round(10 + (80*collectionSystemTransferIndex/collectionSystemTransferCount),0)), 100)
            collectionSystemTransferIndex += 1
            continue

        #build filelist
        fileList = build_filelist(baseDir + '/' + worker.cruiseID + '/' + collectionSystemTransfer['destDir'])
        fileCount = len(fileList)
        fileIndex = 1
        debugPrint('DECODED:', json.dumps(fileList, indent=2))

        for filename in fileList:
            #debugPrint("Processing file: " + filename)
            jsonFileName = filename.split('.')[0] + '.json'
            rawFilePath = baseDir + '/' + worker.cruiseID + '/' + collectionSystemTransfer['destDir'] + '/' + filename
            jsonFilePath = baseDir + '/' + worker.cruiseID + '/' + dataDashboardDir + '/' + collectionSystemTransfer['destDir'] + '/' + jsonFileName

            debugPrint("Processing file: " + rawFilePath)

            if os.stat(rawFilePath).st_size == 0:
                debugPrint("File is empty")
                continue

            proc = subprocess.Popen(['python', processingScriptFilename, '--dataType', rawFilePath], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            out, err = proc.communicate()
            #print "DataType Out: " + out
            #print "DataType Err: " + err

            if out:
                dd_type = out.rstrip('\n')
                debugPrint("Found to be type: " + dd_type)

                proc = subprocess.Popen(['python', processingScriptFilename, rawFilePath], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                out, err = proc.communicate()
                #print "JSONProc Out: " + out
                #print "JSONProc Err: " + err

                if out:
                    try:
                        outObj = json.loads(out)
                    except:
                        errPrint("Error parsing JSON output from file " + filename)
                        job_results['parts'].append({"partName": "Parsing JSON output from file " + filename, "result": "Fail"})
                        continue
                    else:
                        if 'error' in outObj:
                            errorTitle = 'Datafile Parsing error'
                            errorBody = outObj['error']
                            errPrint(errorTitle + ': ', errorBody)
                            worker.OVDM.sendMsg(errorTitle,errorBody)
                        elif output_JSONDataToFile(jsonFilePath, outObj, warehouseUser):
                            newManifestEntries.append({"type":dd_type, "dd_json": worker.cruiseID + '/' + dataDashboardDir + '/' + collectionSystemTransfer['destDir'] +  '/' + jsonFileName, "raw_data":worker.cruiseID + '/' + collectionSystemTransfer['destDir'] + '/' + filename})
                else:
                    errPrint("No JSON output recieved from file " + filename)
                    #job_results['parts'].append({"partName": "Parsing JSON output from file " + filename, "result": "Fail"})
                    if err:
                        errPrint(err)
#                if out:
#                    try:
#                        outObj = json.loads(out)
#                        if output_JSONDataToFile(jsonFilePath, outObj, warehouseUser):
#                            newManifestEntries.append({"type":dd_type, "dd_json": worker.cruiseID + '/' + dataDashboardDir + '/' + collectionSystemTransfer['destDir'] + '/' + jsonFileName, "raw_data":worker.cruiseID + '/' + collectionSystemTransfer['destDir'] + '/' + filename})
#                    except:
#                        errPrint("Error parsing JSON output from file " + filename)
#                        job_results['parts'].append({"partName": "Parsing JSON output from file " + filename, "result": "Fail"})
#                        continue
#
#                else:
#                    errPrint("No JSON output recieved from file " + filename)
#                    job_results['parts'].append({"partName": "Parsing JSON output from file " + filename, "result": "Fail"})
#                    if err:
#                        errPrint(err)
            else:
                debugPrint("File is of unknown datatype")
                if err:
                    debugPrint(err)

            worker.send_job_status(job, int(round(10 + (70*collectionSystemTransferIndex/collectionSystemTransferCount),0)), 100)
            fileIndex += 1

            if worker.stop:
                debugPrint("Stopping")
                break

        collectionSystemTransferIndex += 1

    worker.send_job_status(job, 80, 100)

    if(setDirectoryOwnerGroupPermissions(baseDir + '/' + worker.cruiseID + '/' +  dataDashboardDir, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)):
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Pass"})
    else:
        errPrint("Error Setting file/directory ownership")
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Fail"})

    worker.send_job_status(job, 90, 100)

    try:
        debugPrint("Open Data Dashboard Manifest file")
        DataDashboardManifest = open(dataDashboardManifestFilePath, 'w')
        json.dump(newManifestEntries, DataDashboardManifest)

    except IOError:
        debugPrint("Error Saving Data Dashboard Manifest file")
        job_results['parts'].append({"partName": "Writing Data Dashboard Manifest file", "result": "Fail"})
        DataDashboardManifest.close()
        return json.dumps(job_results)

    finally:
        debugPrint("Closing Data Dashboard Manifest file")
        DataDashboardManifest.close()
        os.chown(dataDashboardManifestFilePath, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)
        job_results['parts'].append({"partName": "Writing Data Dashboard Manifest file", "result": "Pass"})
        worker.send_job_status(job, 95, 100)

    worker.send_job_status(job, 10, 10)

    return json.dumps(job_results)

new_worker = OVDMGearmanWorker()

def sigquit_handler(_signo, _stack_frame):
    global new_worker
    errPrint("Stopping")
    new_worker.stopTask()


def sigint_handler(_signo, _stack_frame):
    global new_worker
    errPrint("Quitting")
    new_worker.quitWorker()

signal.signal(signal.SIGQUIT, sigquit_handler)
signal.signal(signal.SIGINT, sigint_handler)

parser = argparse.ArgumentParser(description='buld databoard data files.')
parser.add_argument('-d', '--debug', action='store_true', help=' display debug messages')

args = parser.parse_args()
if args.debug:
    DEBUG = True
    debugPrint("Running in debug mode")

new_worker.set_client_id('dataDashboard.py')
new_worker.register_task("updateDataDashboard", task_updateDataDashboard)
new_worker.register_task("rebuildDataDashboard", task_rebuildDataDashboard)
new_worker.work()
