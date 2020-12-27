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
#      VERSION:  2.5
#      CREATED:  2015-01-01
#     REVISION:  2020-12-25
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
import tempfile
import subprocess
import python3_gearman
import json
import time
import signal
import shutil
import logging

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.utils.set_ownerGroupPermissions import set_ownerGroupPermissions
from server.utils.check_filenames import bad_filename
from server.utils.output_JSONDataToFile import output_JSONDataToFile
from server.lib.openvdm import OpenVDM_API, DEFAULT_CRUISE_CONFIG_FN

def build_filelist(sourceDir):

    returnFiles = { 'include':[], 'exclude':[], 'new':[], 'updated':[]}
    
    for root, dirnames, filenames in os.walk(sourceDir):

        returnFiles['include'] = [os.path.join(root, filename) for filename in filenames]
        
        returnFiles['exclude'] = list(filter(lambda filename: os.path.islink(filename) or bad_filename(filename), returnFiles['include']))
        returnFiles['include'] = list(filter(lambda filename: not os.path.islink(filename) and not bad_filename(filename), returnFiles['include']))
        
    returnFiles['exclude'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['exclude']]
    returnFiles['include'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['include']]
        
    return returnFiles


def clear_directory(directory):
    
    reasons = []

    # Clear out PublicData
    for root, dirs, pdFiles in os.walk(directory + '/', topdown=False):
        for pdDir in dirs:
            try:
                os.rmdir(os.path.join(root, pdDir))
            except OSError:
                logging.error("Unable to delete {}".format(os.path.join(root, pdDir)))
                reasons.append("Unable to delete {}".format(os.path.join(root, pdDir)))

        for pdFile in pdFiles:
            try:
                os.unlink(os.path.join(root, pdFile))
            except OSError:
                logging.error("Unable to delete {}".format(os.path.join(root, pdFile)))
                reasons.append("Unable to delete {}".format(os.path.join(root, pdFile)))

    if len(reasons) > 0:
        return {'verdict': False, 'reason': "\n".join(reasons)}

    return {'verdict': True}


def export_OVDMConfig(gearman_worker, ovdmConfigFilePath, finalize=False):
    ovdmConfig = gearman_worker.OVDM.getOVDMConfig()

    if finalize:
        ovdmConfig['cruiseFinalizedOn'] = ovdmConfig['configCreatedOn']
    elif os.path.isfile(ovdmConfigFilePath):
        logging.info("Reading existing configuration file")
        try:
            with open(ovdmConfigFilePath) as json_file:  
                data = json.load(json_file)
                if "cruiseFinalizedOn" in data:
                    ovdmConfig['cruiseFinalizedOn'] = data['cruiseFinalizedOn']
        
        except OSError as error:
            return {'verdict': False, 'reason': "Unable to read existing configuration file"}

    for transfer in ovdmConfig['cruiseDataTransfersConfig']:
        del transfer['sshPass']
        del transfer['rsyncPass']
        del transfer['smbPass']

    for transfer in ovdmConfig['collectionSystemTransfersConfig']:
        del transfer['sshPass']
        del transfer['rsyncPass']
        del transfer['smbPass']

    return output_JSONDataToFile(ovdmConfigFilePath, ovdmConfig)


def transfer_PublicDataDir(gearman_worker, gearman_job):

    publicDataDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehousePublicDataDir']
    cruiseDir = os.path.join(gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'], gearman_worker.cruiseID)
    fromPublicDataDir = os.path.join(cruiseDir, gearman_worker.OVDM.getRequiredExtraDirectoryByName('From_PublicData')['destDir'])
    
    logging.debug("Building file list")
    files = build_filelist(publicDataDir)

    logging.debug("Files: {}".format(json.dumps(files, indent=2)))
    
    if len(files['exclude']) > 0:
        logging.warning("Found {} problem filename(s):".format(len(files['exclude'])))
        logging.warning("\t" + '\n\t'.join(files['exclude']))
        return {'verdict': False, 'reason': "Symbolic links or Non-ASCii filenames in {}: {}".format(publicDataDir,', '.join(files['exclude'])), 'files': files }

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    #logging.debug("tmpdir: {}".format(tmpdir))

    # Build rsync file transfer list
    rsyncFileListPath = os.path.join(tmpdir, "rsyncFileList.txt")
    #logging.debug("rsyncFileListPath: {}".format(rsyncFileListPath))

    try:
        localTransferFileList = [filename.replace(publicDataDir, '', 1) for filename in files['include']]
        with open(rsyncFileListPath, 'w') as rsyncFileListFile:
            rsyncFileListFile.write('\n'.join([str(file) for file in localTransferFileList]))
    except IOError:
        logging.error("Error Saving temporary rsync filelist file")

        # Cleanup
        shutil.rmtree(tmpdir)

        return {'verdict': False, 'reason': "Error Saving temporary rsync filelist file", 'files': files }
    
    # Build transfer command
    command = ['rsync', '-tri', '--files-from=' + rsyncFileListPath, publicDataDir + '/', fromPublicDataDir]
    logging.debug("Command: {}".format(' '.join(command)))
    
    fileCount = 1
    totalFiles = len(files['include'])

    # Transfer files
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")

    for line in lines_iterator:
        logging.debug("Line: {}".format(line)) # yield line
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['new'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(round(20 + (70*fileCount/totalFiles),0)), 100)
            fileCount += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['updated'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(round(20 + (70*fileCount/totalFiles),0)), 100)
            fileCount += 1
            
        if gearman_worker.stop:
            logging.error("Stopping rsync transfer")
            popen.terminate()
            break
    
    # Cleanup
    shutil.rmtree(tmpdir)
    return {'verdict': True, 'files':files }


class OVDMGearmanWorker(python3_gearman.GearmanWorker):
    
    def __init__(self, host_list=None):
        self.stop = False
        self.OVDM = OpenVDM_API()
        self.task = None
        self.cruiseID = ''
        self.cruiseStartDate = ''
        self.collectionSystemTransfer = {}
        self.shipboardDataWarehouseConfig = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])
        
    
    # def get_task(self, current_job):
    #     tasks = self.OVDM.getTasks()
    #     for task in tasks:
    #         if task['name'] == current_job.task:
    #             self.task = task
    #             return True
    #     self.task = None
    #     return False
    
    
    def on_job_execute(self, current_job):

        logging.debug("current_job: {}".format(current_job))

        payloadObj = json.loads(current_job.data)

        self.task = self.OVDM.getTaskByName(current_job.task)
        logging.debug("task: {}".format(self.task))
        
        if int(self.task['taskID']) > 0:
            self.OVDM.setRunning_task(self.task['taskID'], os.getpid(), current_job.handle)
#        else:
#            self.OVDM.trackGearmanJob(taskLookup[current_job.task], os.getpid(), current_job.handle)

        logging.info("Job: {} ({}) started at: {}".format(self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime())))
        
        self.cruiseID = payloadObj['cruiseID'] if 'cruiseID' in payloadObj else self.OVDM.getCruiseID()
        self.cruiseStartDate = payloadObj['cruiseStartDate'] if 'cruiseStartDate' in payloadObj else self.OVDM.getCruiseStartDate()
        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()        

        return super(OVDMGearmanWorker, self).on_job_execute(current_job)
            

    def on_job_exception(self, current_job, exc_info):
        logging.error("Job: {} ({}) failed at: {}".format(self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime())))
        
        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail", "reason": "Worker crashed"}]))
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
        
        jobData = {
            'cruiseID': self.cruiseID,
            'cruiseStartDate': self.cruiseStartDate
        }

        if current_job.task == "setupNewCruise":

            gm_client = python3_gearman.GearmanClient([self.OVDM.getGearmanServer()])
        
            for task in self.OVDM.getTasksForHook('setupNewCruise'):
                logging.debug("Adding post task: {}".format(task));
                submitted_job_request = gm_client.submit_job(task, json.dumps(jobData), background=True)
                
        elif current_job.task == "finalizeCurrentCruise":

            gm_client = python3_gearman.GearmanClient([self.OVDM.getGearmanServer()])
        
            for task in self.OVDM.getTasksForHook('finalizeCurrentCruise'):
                submitted_job_request = gm_client.submit_job(task, json.dumps(jobData), background=True)
        
        if len(resultsObj['parts']) > 0:
            if resultsObj['parts'][-1]['result'] == "Fail": # Final Verdict
                if int(self.task['taskID']) > 0:
                    self.OVDM.setError_task(self.task['taskID'], resultsObj['parts'][-1]['reason'])
                else:
                    self.OVDM.sendMsg(self.task['longName'] + ' failed', resultsObj['parts'][-1]['reason'])
            else:
                self.OVDM.setIdle_task(self.task['taskID'])
        else:
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


def task_setupNewCruise(gearman_worker, gearman_job):

    job_results = {'parts':[]}

    payloadObj = json.loads(gearman_job.data)
    logging.debug("Payload: {}".format(json.dumps(payloadObj, indent=2)))
    
    warehouseUser = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'], gearman_worker.cruiseID)
    ovdmConfigFilePath = os.path.join(cruiseDir, DEFAULT_CRUISE_CONFIG_FN)

    gearman_worker.send_job_status(gearman_job, 1, 10)
    
    gm_client = python3_gearman.GearmanClient([gearman_worker.OVDM.getGearmanServer()])

    logging.info("Set ownership/permissions for the CruiseData directory")
    completed_job_request = gm_client.submit_job("setCruiseDataDirectoryPermissions", gearman_job.data)

    resultObj = json.loads(completed_job_request.result)

    if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
        job_results['parts'].append({"partName": "Set ownership/permissions for CruiseData directory", "result": "Pass"})
    else:
        logging.error("Failed to lockdown the CruiseData directory")
        job_results['parts'].append({"partName": "Set ownership/permissions for CruiseData directory", "result": "Fail", "reason": resultObj['parts'][-1]['reason']})
        return json.dumps(job_results)

    logging.info("Creating cruise data directory")
    completed_job_request = gm_client.submit_job("createCruiseDirectory", gearman_job.data)
    
    resultObj = json.loads(completed_job_request.result)

    if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
        job_results['parts'].append({"partName": "Create cruise data directory structure", "result": "Pass"})
    else:
        logging.error("Failed to create cruise data directory")
        job_results['parts'].append({"partName": "Create cruise data directory structure", "result": "Fail", "reason": resultObj['parts'][-1]['reason']})
        return json.dumps(job_results)
    
    gearman_worker.send_job_status(gearman_job, 5, 10)
    
    #build OpenVDM Config file
    logging.info("Exporting Cruise Configuration")
    output_results = export_OVDMConfig(gearman_worker, ovdmConfigFilePath)
    
    if output_results['verdict']:
        job_results['parts'].append({"partName": "Export OpenVDM config data to file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Export OpenVDM config data to file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)
    
    output_results = set_ownerGroupPermissions(warehouseUser, os.path.join(cruiseDir,DEFAULT_CRUISE_CONFIG_FN))

    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Set OpenVDM config file ownership/permissions", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)
    
    gearman_worker.send_job_status(gearman_job, 7, 10)

    logging.info("Creating MD5 summary files")
    completed_job_request = gm_client.submit_job("rebuildMD5Summary", gearman_job.data)

    resultObj = json.loads(completed_job_request.result)

    if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
        job_results['parts'].append({"partName": "Create MD5 summary files", "result": "Pass"})
    else:
        logging.error("Failed to create MD5 summary files")
        job_results['parts'].append({"partName": "Create MD5 summary files", "result": "Fail", "reason": resultObj['parts'][-1]['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 8, 10)

    logging.info("Creating data dashboard directory structure and manifest file")
    completed_job_request = gm_client.submit_job("rebuildDataDashboard", gearman_job.data)

    resultObj = json.loads(completed_job_request.result)

    if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
        job_results['parts'].append({"partName": "Create data dashboard directory structure and manifest file", "result": "Pass"})
    else:
        logging.error("Failed to create data dashboard directory structure and/or manifest file")
        job_results['parts'].append({"partName": "Create data dashboard directory structure and manifest file", "result": "Fail", "reason": resultObj['parts'][-1]['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 9, 10)

    logging.info("Updating Cruise Size")
    cruiseSize = subprocess.check_output(['du','-sb', cruiseDir]).split()[0].decode('utf-8')

    gearman_worker.OVDM.set_cruiseSize(cruiseSize)
    gearman_worker.OVDM.set_loweringSize("0")
    
    gearman_worker.send_job_status(gearman_job, 10, 10)

    return json.dumps(job_results)
    
    
def task_finalizeCurrentCruise(gearman_worker, gearman_job):

    job_results = {'parts':[]}

    gearman_worker.send_job_status(gearman_job, 1, 10)

    warehouseUser = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    cruiseDir = os.path.join(gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'], gearman_worker.cruiseID)  
    logging.debug("Cruise Dir: {}".format(cruiseDir))

    publicDataDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehousePublicDataDir']
    logging.debug("PublicData Dir: {}".format(publicDataDir))

    fromPublicDataDir = os.path.join(cruiseDir, gearman_worker.OVDM.getRequiredExtraDirectoryByName('From_PublicData')['destDir'])
    logging.debug("From_PublicData Dir: {}".format(fromPublicDataDir))

    ovdmConfigFilePath = os.path.join(cruiseDir, DEFAULT_CRUISE_CONFIG_FN)
    
    if os.path.exists(cruiseDir):
        job_results['parts'].append({"partName": "Verify cruise directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify cruise directory exists", "result": "Fail", "reason": "Cruise directory: " + cruiseDir + " could not be found"})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 2, 10)
    logging.info("Queuing Collection System Transfers")

    gm_client = python3_gearman.GearmanClient([gearman_worker.OVDM.getGearmanServer()])
    
    gmData = {}
    gmData['cruiseID'] = gearman_worker.cruiseID
    gmData['cruiseStartDate'] = gearman_worker.cruiseStartDate
    gmData['systemStatus'] = "On"
    gmData['collectionSystemTransfer'] = {}
        
    collectionSystemTransferJobs = []
    
    collectionSystemTransfers = gearman_worker.OVDM.getActiveCollectionSystemTransfers()

    for collectionSystemTransfer in collectionSystemTransfers:

        if collectionSystemTransfer['cruiseOrLowering'] == '0':
            logging.debug("Queuing runCollectionSystemTransfer job for {}".format(collectionSystemTransfer['name']))        
            gmData['collectionSystemTransfer']['collectionSystemTransferID'] = collectionSystemTransfer['collectionSystemTransferID']
        
            collectionSystemTransferJobs.append( {"task": "runCollectionSystemTransfer", "data": json.dumps(gmData)} )

    
    gearman_worker.send_job_status(gearman_job, 3, 10)

    if len(collectionSystemTransferJobs) > 0:
        logging.info("Submitting runCollectionSystemTransfer jobs")
        submitted_job_request = gm_client.submit_multiple_jobs(collectionSystemTransferJobs, background=False, wait_until_complete=False)
    
        gearman_worker.send_job_status(gearman_job, 4, 10)
    
        time.sleep(1)
        completed_requests = gm_client.wait_until_jobs_completed(submitted_job_request)
        logging.info("Completed runCollectionSystemTransfers jobs")

    gearman_worker.send_job_status(gearman_job, 5, 10)
    
    logging.info("Transferring files from PublicData to the cruise data directory")
    
    logging.debug("Verify From_PublicData directory exists within the cruise data directory")
    if os.path.exists(fromPublicDataDir):
        job_results['parts'].append({"partName": "Verify From_PublicData directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify From_PublicData directory exists", "result": "Fail", "reason": "From_PublicData directory: " + fromPublicDataDir + " could not be found"})
        return json.dumps(job_results)

    logging.debug("Verify PublicData Directory exists")
    if os.path.exists(publicDataDir):
        job_results['parts'].append({"partName": "Verify PublicData directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify PublicData directory exists", "result": "Fail", "reason": "PublicData directory: " + publicDataDir+ " could not be found"})
        return json.dumps(job_results)

    logging.debug("Transferring files")
    output_results = transfer_PublicDataDir(gearman_worker, gearman_job)
    logging.debug("Transfer Complete")

    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Transfer PublicData files", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    job_results['parts'].append({"partName": "Transfer PublicData files", "result": "Pass"})

    files = output_results['files']

    logging.debug("PublicData Files Transferred: {}".format(json.dumps(files, indent=2)))

    logging.info("Clearing files from PublicData")
    output_results = clear_directory(publicDataDir)
    logging.debug("Clearing Complete")

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Clear out PublicData files", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Clear out PublicData files", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)
    
    gearman_worker.send_job_status(gearman_job, 9, 10)
    
    if len(files['new']) > 0 or len(files['updated']) > 0:

        output_results = set_ownerGroupPermissions(warehouseUser, fromPublicDataDir)

        if output_results['verdict']:
            job_results['parts'].append({"partName": "Set file/directory ownership/permissions", "result": "Pass"})
        else:
            job_results['parts'].append({"partName": "Set file/directory ownership/permissions", "result": "Fail", "reason": output_results['reason']})
            return json.dumps(job_results)
        
    gearman_worker.send_job_status(gearman_job, 95, 100)
    
    #build OpenVDM Config file
    logging.info("Exporting OpenVDM Configuration")
    output_results = export_OVDMConfig(gearman_worker, ovdmConfigFilePath, finalize=True)
    
    if output_results['verdict']:
        job_results['parts'].append({"partName": "Export OpenVDM config data to file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Export OpenVDM config data to file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)
    
    output_results = set_ownerGroupPermissions(warehouseUser, os.path.join(cruiseDir,DEFAULT_CRUISE_CONFIG_FN))

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set OpenVDM config file ownership/permissions", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Set OpenVDM config file ownership/permissions", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    logging.info("Initiating MD5 Summary Task")

    gmData = {}
    gmData['cruiseID'] = gearman_worker.cruiseID
    gmData['files'] = files
    gmData['files']['new'] = [fromPublicDataDir.replace(cruiseDir, '') + '/' + filename for filename in gmData['files']['new']]
    gmData['files']['updated'] = [fromPublicDataDir.replace(cruiseDir, '') + '/' + filename for filename in gmData['files']['updated']]
    
    gmData['files']['updated'].append(DEFAULT_CRUISE_CONFIG_FN)
       
    completed_job_request = gm_client.submit_job("updateMD5Summary", json.dumps(gmData))
    
    logging.debug("MD5 Summary Task Complete")

    # need to add code for cruise data transfers

    gearman_worker.send_job_status(gearman_job, 10, 10)
    return json.dumps(job_results)

def task_rsyncPublicDataToCruiseData(gearman_worker, gearman_job):

    job_results = {'parts':[]}

    warehouseUser = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']

    cruiseDir = os.path.join(gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'], gearman_worker.cruiseID)  
    logging.debug("Cruise Dir: {}".format(cruiseDir))

    publicDataDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehousePublicDataDir']
    logging.debug("PublicData Dir: {}".format(publicDataDir))

    fromPublicDataDir = gearman_worker.OVDM.getRequiredExtraDirectoryByName('From_PublicData')['destDir']
    logging.debug("FromPublicData Dir: {}".format(publicDataDir))
    
    gearman_worker.send_job_status(gearman_job, 1, 10)

    if os.path.exists(os.path.join(cruiseDir, fromPublicDataDir)):
        job_results['parts'].append({"partName": "Verify From_PublicData directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify From_PublicData directory exists", "result": "Fail", "reason": "Unable to locate the From_PublicData directory: " + os.path.join(cruiseDir, fromPublicDataDir)})
        return json.dumps(job_results)

    if os.path.exists(publicDataDir):
        job_results['parts'].append({"partName": "Verify PublicData directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify PublicData directory exists", "result": "Fail", "reason": "Unable to locate the PublicData directory: " + publicDataDir})
        return json.dumps(job_results)
    
    gearman_worker.send_job_status(gearman_job, 5, 10)
    
    logging.info("Transferring files from PublicData to the cruise data directory")
    output_results = transfer_PublicDataDir(gearman_worker, gearman_job)
    
    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Transfer files", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)
    
    job_results['parts'].append({"partName": "Transfer files", "result": "Pass"})

    files = output_results['files']

    logging.debug("Files Transferred: {}".format(json.dumps(files, indent=2)))

    gearman_worker.send_job_status(gearman_job, 8, 10)
    
    if len(files['new']) > 0 or len(files['updated']) > 0:

        logging.info("Setting file permissions")
        output_results = set_ownerGroupPermissions(warehouseUser, os.path.join(cruiseDir, fromPublicDataDir))
        
        if output_results['verdict']:
            job_results['parts'].append({"partName": "Set file/directory ownership/permissions", "result": "Pass"})
        else:
            job_results['parts'].append({"partName": "Set file/directory ownership/permissions", "result": "Fail", "reason": output_results['reason']})
            return json.dumps(job_results)
        
        gearman_worker.send_job_status(gearman_job, 9, 100)

        logging.info("Initiating MD5 Summary Task")

        gm_client = python3_gearman.GearmanClient([gearman_worker.OVDM.getGearmanServer()])    
        gmData = {}
        gmData['cruiseID'] = gearman_worker.cruiseID
        gmData['files'] = files
        gmData['files']['new'] = [os.path.join(fromPublicDataDir,filename) for filename in gmData['files']['new']]
        gmData['files']['updated'] = [os.path.join(fromPublicDataDir,filename) for filename in gmData['files']['updated']]
        
        completed_job_request = gm_client.submit_job("updateMD5Summary", json.dumps(gmData))
    
        logging.info("MD5 Summary Task Complete")

    # need to verify update MD5 completed successfully

    gearman_worker.send_job_status(gearman_job, 10, 10)
    return json.dumps(job_results)


def task_exportOVDMConfig(gearman_worker, gearman_job):

    job_results = {'parts':[]}

    warehouseUser = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    
    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)
    ovdmConfigFilePath = os.path.join(cruiseDir, DEFAULT_CRUISE_CONFIG_FN)

    # publicDataDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehousePublicDataDir']
    
    gearman_worker.send_job_status(gearman_job, 1, 10)

    logging.info("Verifying cruise directory exists")
    if os.path.exists(cruiseDir):
        job_results['parts'].append({"partName": "Verify cruise directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify cruise directory exists", "result": "Fail", "reason": "Unable to locate the cruise directory: " + cruiseDir})
        return json.dumps(job_results)
    
    gearman_worker.send_job_status(gearman_job, 3, 10)

    #build OpenVDM Config file
    logging.info("Exporting OpenVDM Configuration")
    output_results = export_OVDMConfig(gearman_worker, ovdmConfigFilePath)
    
    if output_results['verdict']:
        job_results['parts'].append({"partName": "Export OpenVDM config data to file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Export OpenVDM config data to file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)
    
    output_results = set_ownerGroupPermissions(warehouseUser, os.path.join(cruiseDir,DEFAULT_CRUISE_CONFIG_FN))

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set OpenVDM config file ownership/permissions", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Set OpenVDM config file ownership/permissions", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 6, 10)
    
    logging.info("Setting file ownership/permissions")
    output_results = set_ownerGroupPermissions(warehouseUser, ovdmConfigFilePath)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set file ownership/permissions", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Set file ownership/permissions", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)
    
    gearman_worker.send_job_status(gearman_job, 10, 10)
    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle Cruise-Level tasks')
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

    logging.info("\tTask: setupNewCruise")
    new_worker.register_task("setupNewCruise", task_setupNewCruise)
    
    logging.info("\tTask: finalizeCurrentCruise")
    new_worker.register_task("finalizeCurrentCruise", task_finalizeCurrentCruise)
    
    logging.info("\tTask: exportOVDMConfig")
    new_worker.register_task("exportOVDMConfig", task_exportOVDMConfig)
    
    logging.info("\tTask: rsyncPublicDataToCruiseData")
    new_worker.register_task("rsyncPublicDataToCruiseData", task_rsyncPublicDataToCruiseData)

    logging.info("Waiting for jobs...")
    new_worker.work()
