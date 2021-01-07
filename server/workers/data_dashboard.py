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
#      VERSION:  2.4
#      CREATED:  2015-01-01
#     REVISION:  2020-12-27
#
# LICENSE INFO: Open Vessel Data Management v2.5 (OpenVDMv2)
#               Copyright (C) OceanDataRat.org 2021
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
import argparse
import os
import sys
import python3_gearman
import json
import argparse
import signal
import time
import subprocess
import logging

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.utils.set_ownerGroupPermissions import set_ownerGroupPermissions
from server.utils.check_filenames import bad_filename
from server.utils.output_JSONDataToFile import output_JSONDataToFile
from server.lib.openvdm import OpenVDM_API, DEFAULT_DATA_DASHBOARD_MANIFEST_FN

customTasks = [
    {
        "taskID": "0",
        "name": "updateDataDashboard",
        "longName": "Updating Data Dashboard",
    }
]

def build_filelist(sourceDir):

    logging.debug("sourceDir: {}".format(sourceDir))

    returnFiles = []
    for root, dirnames, filenames in os.walk(sourceDir):
        for filename in filenames:
            returnFiles.append(os.path.join(root, filename))

    returnFiles = [filename.replace(sourceDir + '/', '', 1) for filename in returnFiles]
    return returnFiles


class OVDMGearmanWorker(python3_gearman.GearmanWorker):

    def __init__(self, host_list=None):
        self.stop = False
        self.OVDM = OpenVDM_API()
        self.task = None
        self.cruiseID = ''
        self.loweringID = ''
        self.collectionSystemTransfer = {}
        self.shipboardDataWarehouseConfig = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])


    def get_custom_task(self, current_job):
        task = list(filter(lambda task: task['name'] == current_job.task, customTasks))
        return task[0] if len(task) > 0 else None


    def on_job_execute(self, current_job):

        logging.debug("current_job: {}".format(current_job))

        payloadObj = json.loads(current_job.data)

        self.task = self.get_custom_task(current_job) if self.get_custom_task(current_job) != None else self.OVDM.getTaskByName(current_job.task)
        logging.debug("task: {}".format(self.task))

        if int(self.task['taskID']) > 0:
            self.OVDM.setRunning_task(self.task['taskID'], os.getpid(), current_job.handle)
        else:
            self.OVDM.trackGearmanJob(self.task['longName'], os.getpid(), current_job.handle)

        logging.info("Job: {} ({}) started at: {}".format(self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime())))

        self.cruiseID = payloadObj['cruiseID'] if 'cruiseID' in payloadObj else self.OVDM.getCruiseID()
        self.loweringID = payloadObj['loweringID'] if 'loweringID' in payloadObj else self.OVDM.getLoweringID()
        self.collectionSystemTransfer = self.OVDM.getCollectionSystemTransfer(payloadObj['collectionSystemTransferID']) if 'collectionSystemTransferID' in payloadObj else { 'name': "Unknown" }

        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()
        
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)


    def on_job_exception(self, current_job, exc_info):
        logging.error("Job: {} ({}) failed at: {}".format(self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime())))
        
        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail", "reason": "Unknown, contact Webb :-)"}]))
        if int(self.task['taskID']) > 0:
            self.OVDM.setError_task(self.task['taskID'], "Worker crashed")
        else:
            self.OVDM.sendMsg(self.task['longName'] + ' failed', 'Worker crashed')
        
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)


    def on_job_complete(self, current_job, job_results):
        resultsObj = json.loads(job_results)

        logging.debug("Preparing subsequent Gearman jobs")

        jobData = {
            'cruiseID': self.cruiseID,
            'loweringID': self.loweringID,
            'files': resultsObj['files']
        }
    
        if current_job.task == 'updateDataDashboard':

            gm_client = python3_gearman.GearmanClient([self.OVDM.getGearmanServer()])

            payloadObj = json.loads(current_job.data)
            jobData['collectionSystemTransferID'] = payloadObj['collectionSystemTransferID']

            for task in self.OVDM.getTasksForHook(current_job.task):
                logging.info("Adding post task: {}".format(task));
                submitted_job_request = gm_client.submit_job(task, json.dumps(jobData), background=True)

        elif current_job.task == 'rebuildDataDashboard':

            gm_client = python3_gearman.GearmanClient([self.OVDM.getGearmanServer()])

            for task in self.OVDM.getTasksForHook(current_job.task):
                logging.info("Adding post task: {}".format(task));
                submitted_job_request = gm_client.submit_job(task, json.dumps(jobData), background=True)

        if len(resultsObj['parts']) > 0:
            if resultsObj['parts'][-1]['result'] == "Fail": # Final Verdict
                if int(self.task['taskID']) > 0:
                    self.OVDM.setError_task(self.task['taskID'], resultsObj['parts'][-1]['reason'])
                else:
                    self.OVDM.sendMsg(self.task['longName'] + ' failed', resultsObj['parts'][-1]['reason'])
            else:
                if int(self.task['taskID']) > 0:
                    self.OVDM.setIdle_task(self.task['taskID'])
        else:
            if int(self.task['taskID']) > 0:
                self.OVDM.setIdle_task(self.task['taskID'])
        
        logging.debug("Job Results: {}".format(json.dumps(resultsObj, indent=2)))
        logging.info("Job: {} ({}) completed at: {}".format(self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime())))
            
        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_results)


    def stopTask(self):
        self.stop = True
        logging.warning("Stopping current task...")

    
    def quitWorker(self):
        self.stop = True
        logging.warning("Quitting worker...")
        self.shutdown()


def task_updateDataDashboard(gearman_worker, gearman_job):

    job_results = {
        'parts':[],
        'files':{
            'new':[],
            'updated':[]
        }
    }

    payloadObj = json.loads(gearman_job.data)
    logging.debug('Payload: {}'.format(json.dumps(payloadObj, indent=2)))

    warehouseUser = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)
    loweringDir = os.path.join(cruiseDir, gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir'], gearman_worker.loweringID)
    
    dataDashboardDir = os.path.join(cruiseDir, gearman_worker.OVDM.getRequiredExtraDirectoryByName('Dashboard_Data')['destDir'])
    dataDashboardManifestFilePath = os.path.join(dataDashboardDir, DEFAULT_DATA_DASHBOARD_MANIFEST_FN)
    collectionSystemTransfer = gearman_worker.collectionSystemTransfer

    gearman_worker.send_job_status(gearman_job, 5, 100)

    logging.info('Collection System Transfer: {}'.format(collectionSystemTransfer['name']))

    newManifestEntries = []
    removeManifestEntries = []

    #check for processing file
    processingScriptFilename = os.path.join(gearman_worker.OVDM.getDashboardDataProcessingScriptDir(), collectionSystemTransfer['name'].replace(' ','') + gearman_worker.OVDM.getDashboardDataProcessingScriptSuffix())
    logging.debug("Processing Script Filename: {}".format(processingScriptFilename))

    if os.path.isfile(processingScriptFilename):
        job_results['parts'].append({"partName": "Dashboard Processing File Located", "result": "Pass"})
    else:
        logging.warning("Processing script not found: {}".format(processingScriptFilename))
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 10, 100)

    #build filelist
    fileList = []

    if payloadObj['files']['new'] or payloadObj['files']['updated']:
        fileList = payloadObj['files']['new']
        fileList += payloadObj['files']['updated']
        logging.debug('File List: {}'.format(json.dumps(fileList, indent=2)))
        job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Pass"})

    else:
        logging.warning("No new or updated files to process")
        job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Pass"})
        return json.dumps(job_results)

    fileCount = len(fileList)
    fileIndex = 0
    for filename in fileList:
        
        if gearman_worker.stop:
            break

        logging.info("Processing file: {}".format(filename))
        jsonFileName = os.path.splitext(filename)[0] + '.json'
        rawFilePath = os.path.join(cruiseDir, filename)
        jsonFilePath = os.path.join(dataDashboardDir, jsonFileName)

        if not os.path.isfile(rawFilePath):
            job_results['parts'].append({"partName": "Verify data file exists", "result": "Fail", "reason": "Unable to find data file: " + filename})
            logging.warning("File not found {}, skipping".format(filename))
            continue

        if os.stat(rawFilePath).st_size == 0:
            logging.warning("File is empty {}, skipping".format(filename))
            continue

        command = ['python', processingScriptFilename, '--dataType', rawFilePath]

        s = ' '
        logging.debug("DataType Retrieval Command: {}".format(s.join(command)))

        datatype_proc = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

        if datatype_proc.stdout:
            dd_type = datatype_proc.stdout.rstrip('\n')
            logging.debug("DataType found to be: {}".format(dd_type))

            command = ['python', processingScriptFilename, rawFilePath]

            s = ' '
            logging.debug("Data Processing Command: {}".format(s.join(command)))

            data_proc = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

            if data_proc.stdout:
                try:
                    logging.debug("Verifying output")
                    outObj = json.loads(data_proc.stdout)
                except:
                    logging.error("Error parsing JSON output from file: {}".format(filename))
                    job_results['parts'].append({"partName": "Parsing JSON output from file " + filename, "result": "Fail", "reason": "Error parsing JSON output from file: " + filename})
                    continue
                else:
                    if 'error' in outObj:
                        errorTitle = 'Datafile Parsing error'
                        errorBody = outObj['error']
                        logging.error("{}: {}".format(errorTitle, errorBody))
                        gearman_worker.OVDM.sendMsg(errorTitle,errorBody)
                    else:
                        output_results = output_JSONDataToFile(jsonFilePath, outObj)

                        if output_results['verdict']:
                            job_results['parts'].append({"partName": "Writing DashboardData file: " + filename, "result": "Pass"})
                        else:
                            errorTitle = 'Data Dashboard Processing failed'
                            errorBody = "Error Writing DashboardData file: " + filename + ". Reason: " + output_results['reason']
                            logging.error("{}: {}".format(errorTitle, errorBody))
                            gearman_worker.OVDM.sendMsg(errorTitle,errorBody)
                            job_results['parts'].append({"partName": "Writing Dashboard file: " + filename, "result": "Fail", "reason": output_results['reason']})

                        newManifestEntries.append({"type":dd_type, "dd_json": jsonFilePath.replace(baseDir + '/',''), "raw_data": rawFilePath.replace(baseDir + '/','')})
            else:
                errorTitle = 'Data Dashboard Processing failed'
                errorBody = 'No JSON output recieved from file.  Parsing Command: ' + s.join(command)
                logging.error("{}: {}".format(errorTitle, errorBody))
                gearman_worker.OVDM.sendMsg(errorTitle,errorBody)
                removeManifestEntries.append({"dd_json": jsonFilePath.replace(baseDir + '/',''), "raw_data": rawFilePath.replace(baseDir + '/','')})

                #job_results['parts'].append({"partName": "Parsing JSON output from file " + filename, "result": "Fail"})
                if data_proc.stderr:
                    logging.error("Err: {}".format(data_proc.stderr))
        else:
            logging.warning("File is of unknown datatype: {}".format(rawFilePath))
            removeManifestEntries.append({"dd_json": jsonFilePath.replace(baseDir + '/',''), "raw_data":rawFilePath.replace(baseDir + '/','')})

            if datatype_proc.stderr:
                logging.error("Err: {}".format(datatype_proc.stderr))

        gearman_worker.send_job_status(gearman_job, int(10 + 70*float(fileIndex)/float(fileCount)), 100)
        fileIndex += 1

    gearman_worker.send_job_status(gearman_job, 8, 10)

    if len(newManifestEntries) > 0:
        logging.info("Updating Manifest file: {}".format(dataDashboardManifestFilePath))

        rows_removed = 0

        existingManifestEntries = []

        try:
            with open(dataDashboardManifestFilePath, 'r') as DashboardManifestFile:
                existingManifestEntries = json.load(DashboardManifestFile)

            job_results['parts'].append({"partName": "Reading pre-existing Dashboard manifest file", "result": "Pass"})

        except IOError:
            logging.error("Error Reading Dashboard Manifest file {}".format(dataDashboardManifestFilePath))
            job_results['parts'].append({"partName": "Reading pre-existing Dashboard manifest file", "result": "Fail", "reason": "Error reading dashboard manifest file: " + dataDashboardManifestFilePath})
            return json.dumps(job_results)

        logging.debug("Entries to remove: {}".format(json.dumps(removeManifestEntries, indent=2)))
        for removeEntry in removeManifestEntries:
            for idx, existingEntry in enumerate(existingManifestEntries):
                if removeEntry['raw_data'] == existingEntry['raw_data']:
                    del existingManifestEntries[idx]
                    rows_removed += 1

                    if os.path.isfile(os.path.join(baseDir,removeEntry['dd_json'])):
                        logging.info("Deleting orphaned dd_json file {}".format(os.path.join(baseDir,removeEntry['dd_json'])))
                        os.remove(os.path.join(baseDir,removeEntry['dd_json']))
                    break

        logging.debug("Entries to add/update: {}".format(json.dumps(newManifestEntries, indent=2)))
        for newEntry in newManifestEntries:
            updated = False
            for existingEntry in existingManifestEntries:
                if newEntry['raw_data'] == existingEntry['raw_data']:
                    updated = True
                    job_results['files']['updated'].append(newEntry['dd_json'].replace(gearman_worker.cruiseID + '/',''))
                    break

            if not updated: #added
                job_results['files']['new'].append(newEntry['dd_json'].replace(gearman_worker.cruiseID + '/',''))
                existingManifestEntries.append(newEntry)

        if len(job_results['files']['new']):
            logging.info("{} row(s) added".format(len(job_results['files']['new'])))
        if len(job_results['files']['updated']):
            logging.info("{} row(s) updated".format(len(job_results['files']['updated'])))
        if rows_removed:
            logging.info("{} row(s) removed".format(rows_removed))

        output_results = output_JSONDataToFile(dataDashboardManifestFilePath, existingManifestEntries)

        if not output_results['verdict']:
            logging.error("Error Writing Dashboard manifest file: {}".format(dataDashboardManifestFilePath))
            job_results['parts'].append({"partName": "Writing Dashboard manifest file", "result": "Fail", "reason": output_results['reason']})
            return json.dumps(job_results)
    
        job_results['parts'].append({"partName": "Writing Dashboard manifest file", "result": "Pass"})
        job_results['files']['updated'].append(os.path.join(gearman_worker.OVDM.getRequiredExtraDirectoryByName('Dashboard_Data')['destDir'], DEFAULT_DATA_DASHBOARD_MANIFEST_FN))

        gearman_worker.send_job_status(gearman_job, 9, 10)

        logging.info("Setting file ownership/permissions")
        output_results = set_ownerGroupPermissions(warehouseUser, dataDashboardDir)

        if output_results['verdict']:
            job_results['parts'].append({"partName": "Set file/directory ownership", "result": "Pass"})
        else:
            job_results['parts'].append({"partName": "Set file/directory ownership", "result": "Fail", "reason": output_results['reason']})
            return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 10, 10)

    return json.dumps(job_results)


def task_rebuildDataDashboard(gearman_worker, gearman_job):

    job_results = {
        'parts':[],
        'files':{
            'new':[],
            'updated':[]
        }
    }

    payloadObj = json.loads(gearman_job.data)
    logging.debug('Payload: {}'.format(json.dumps(payloadObj, indent=2)))

    warehouseUser = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)
    dataDashboardDir = os.path.join(cruiseDir, gearman_worker.OVDM.getRequiredExtraDirectoryByName('Dashboard_Data')['destDir'])
    dataDashboardManifestFilePath = os.path.join(dataDashboardDir, DEFAULT_DATA_DASHBOARD_MANIFEST_FN)

    if os.path.exists(dataDashboardDir):
        job_results['parts'].append({"partName": "Verify Data Dashboard Directory exists", "result": "Pass"})
    else:
        logging.error("Data dashboard directory not found: {}".format(dataDashboardDir))
        job_results['parts'].append({"partName": "Verify Data Dashboard Directory exists", "result": "Fail", "reason": "Unable to locate the data dashboard directory: " + dataDashboardDir})
        return json.dumps(job_results)

    collectionSystemTransfers = gearman_worker.OVDM.getActiveCollectionSystemTransfers()
    
    gearman_worker.send_job_status(gearman_job, 1, 100)

    newManifestEntries = []

    collectionSystemTransferCount = len(collectionSystemTransfers)
    collectionSystemTransferIndex = 0
    for collectionSystemTransfer in collectionSystemTransfers:

        logging.info('Processing data from: {}'.format(collectionSystemTransfer['name']))

        processingScriptFilename = os.path.join(gearman_worker.OVDM.getDashboardDataProcessingScriptDir(), collectionSystemTransfer['name'].replace(' ','-') + gearman_worker.OVDM.getDashboardDataProcessingScriptSuffix())
        logging.debug("Processing Script Filename: {}".format(processingScriptFilename))

        if not os.path.isfile(processingScriptFilename):
            logging.warning("Processing script for collection system {} not found, moving on.".format(collectionSystemTransfer['name']))
            gearman_worker.send_job_status(gearman_job, int(10 + (80*float(collectionSystemTransferIndex)/float(collectionSystemTransferCount))), 100)
            collectionSystemTransferIndex += 1
            continue

        # collectionSystemTransferOutputDir = os.path.join(dataDashboardDir, collectionSystemTransfer['destDir'])
        
        #build filelist
        fileList = []
        if collectionSystemTransfer['cruiseOrLowering'] == "0":
            collectionSystemTransferInputDir = os.path.join(cruiseDir, collectionSystemTransfer['destDir'])
            fileList.extend(build_filelist(collectionSystemTransferInputDir))
            fileList = [os.path.join(collectionSystemTransfer['destDir'], filename) for filename in fileList]

        else:
            lowerings = gearman_worker.OVDM.getLowerings()
            loweringBaseDir = gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir']

            for lowering in lowerings:
                collectionSystemTransferInputDir = os.path.join(cruiseDir, loweringBaseDir, lowering, collectionSystemTransfer['destDir'])
                debugPrint(os.path.join(cruiseDir, loweringBaseDir, lowering, collectionSystemTransfer['destDir']))
                loweringFileList = build_filelist(collectionSystemTransferInputDir)
                fileList.extend([os.path.join(loweringBaseDir, lowering, collectionSystemTransfer['destDir'], filename) for filename in loweringFileList])
 
        logging.debug("FileList: {}".format(json.dumps(fileList, indent=2)))

        fileCount = len(fileList)
        fileIndex = 0
        logging.info("{} file(s) to process".format(fileCount))

        for filename in fileList:
        
            if gearman_worker.stop:
                break

            logging.debug("Processing file: {}".format(filename))
            jsonFileName = os.path.splitext(filename)[0] + '.json'
            logging.debug("jsonFileName: {}".format(jsonFileName))
            rawFilePath = os.path.join(cruiseDir, filename)
            logging.debug("rawFilePath: {}".format(rawFilePath))
            jsonFilePath = os.path.join(dataDashboardDir, jsonFileName)
            logging.debug("jsonFilePath: {}".format(jsonFilePath))

            if os.stat(rawFilePath).st_size == 0:
                logging.warning("File {} is empty".format(filename))
                continue

            command = ['python', processingScriptFilename, '--dataType', rawFilePath]

            s = ' '
            logging.debug("Get Datatype Command: {}".format(s.join(command)))

            datatype_proc = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

            if datatype_proc.stdout:
                dd_type = datatype_proc.stdout.rstrip('\n')
                logging.debug("Found to be type: {}".format(dd_type))

                command = ['python', processingScriptFilename, rawFilePath]

                s = ' '
                logging.debug("Processing Command: {}".format(s.join(command)))

                data_proc = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

                if data_proc.stdout:
                    try:
                        logging.debug("Parsing output")
                        outObj = json.loads(data_proc.stdout)
                    except Exception as e:
                        logging.error(str(e))
                        errorTitle = 'Error parsing output'
                        errorBody = 'Invalid JSON output recieved from processing. Command: ' + s.join(command)
                        logging.error("{}: {}".format(errorTitle, errorBody))
                        gearman_worker.OVDM.sendMsg(errorTitle,errorBody)
                        job_results['parts'].append({"partName": "Parsing JSON output " + filename, "result": "Fail", "reason": errorTitle + ':' + errorBody})
                    else:
                        if 'error' in outObj:
                            errorTitle = 'Error processing file'
                            errorBody = outObj['error']
                            logging.error("{}: {}".format(errorTitle, errorBody))
                            gearman_worker.OVDM.sendMsg(errorTitle,errorBody)
                            job_results['parts'].append({"partName": "Processing Datafile " + filename, "result": "Fail", "reason": errorTitle + ':' + errorBody})

                        else:
                            #job_results['parts'].append({"partName": "Processing Datafile " + filename, "result": "Pass"})
                            output_results = output_JSONDataToFile(jsonFilePath, outObj)

                            if output_results['verdict']:
                                job_results['parts'].append({"partName": "Writing DashboardData file: " + filename, "result": "Pass"})
                            else:
                                errorTitle = 'Error writing file'
                                errorBody = "Error Writing DashboardData file: " + filename
                                logging.error("{}: {}".format(errorTitle, errorBody))
                                gearman_worker.OVDM.sendMsg(errorTitle,errorBody)

                                job_results['parts'].append({"partName": "Writing Dashboard file: " + filename, "result": "Fail", "reason": output_results['verdict']})

                            newManifestEntries.append({"type":dd_type, "dd_json": jsonFilePath.replace(baseDir + '/',''), "raw_data": rawFilePath.replace(baseDir + '/','')})
                else:
                    errorTitle = 'Error processing file'
                    errorBody = 'No JSON output recieved from file. Processing Command: ' + s.join(command)
                    logging.error("{}: {}".format(errorTitle, errorBody))
                    gearman_worker.OVDM.sendMsg(errorTitle,errorBody)
                    job_results['parts'].append({"partName": "Parsing JSON output from file " + filename, "result": "Fail", "reason": errorTitle + ': ' + errorBody})
                    
                    if data_proc.stderr:
                        logging.error('err: {}'.format(data_proc.stderr))

            else:
                logging.warning("File is of unknown datatype, moving on")

                if datatype_proc.stderr:
                    logging.error('err: {}'.format(datatype_proc.stderr))

            gearman_worker.send_job_status(gearman_job, int(10 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1

        collectionSystemTransferIndex += 1

    gearman_worker.send_job_status(gearman_job, 90, 100)

    logging.info("Update Dashboard Manifest file")
    output_results = output_JSONDataToFile(dataDashboardManifestFilePath, newManifestEntries)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Updating manifest file", "result": "Pass"})
    else:
        logging.error("Error updating manifest file {}".format(dataDashboardManifestFilePath))
        job_results['parts'].append({"partName": "Updating manifest file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 95, 100)

    logging.info("Setting file ownership/permissions")
    output_results = set_ownerGroupPermissions(warehouseUser, dataDashboardDir)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Pass"})
    else:
        logging.error("Error Setting file/directory ownership/permissions")
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 99, 100)

    job_results['files']['updated'] = [os.path.join(gearman_worker.OVDM.getRequiredExtraDirectoryByName('Dashboard_Data')['destDir'], filepath) for filepath in build_filelist(dataDashboardDir)]# might need to remove cruiseDir from begining of filepaths

    gearman_worker.send_job_status(gearman_job, 10, 10)

    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle data dashboard related tasks')
    parser.add_argument('-v', '--verbosity', dest='verbosity',
                        default=0, action='count',
                        help='Increase output verbosity')

    parsed_args = parser.parse_args()

    ############################
    # Set up logging before we do any other argument parsing (so that we
    # can log problems with argument parsing).
    
    LOGGING_FORMAT = '%(asctime)-15s %(levelname)s - %(message)s'
    logging.basicConfig(format=LOGGING_FORMAT)

    LOG_LEVELS = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    parsed_args.verbosity = min(parsed_args.verbosity, max(LOG_LEVELS))
    logging.getLogger().setLevel(LOG_LEVELS[parsed_args.verbosity])

    logging.debug("Creating Worker...")

    # global new_worker
    new_worker = OVDMGearmanWorker()
    new_worker.set_client_id(__file__)

    logging.debug("Defining Signal Handlers...")
    def sigquit_handler(_signo, _stack_frame):
        logging.warning("QUIT Signal Received")
        new_worker.stopTask()

    def sigint_handler(_signo, _stack_frame):
        logging.warning("INT Signal Received")
        new_worker.quitWorker()

    signal.signal(signal.SIGQUIT, sigquit_handler)
    signal.signal(signal.SIGINT, sigint_handler)

    logging.info("Registering worker tasks...")

    logging.info("\tTask: updateDataDashboard")
    new_worker.register_task("updateDataDashboard", task_updateDataDashboard)
    logging.info("\tTask: rebuildDataDashboard")
    new_worker.register_task("rebuildDataDashboard", task_rebuildDataDashboard)

    logging.info("Waiting for jobs...")
    new_worker.work()
