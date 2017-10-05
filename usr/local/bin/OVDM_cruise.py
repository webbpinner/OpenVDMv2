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
#      VERSION:  2.3
#      CREATED:  2015-01-01
#     REVISION:  2017-08-05
#
# LICENSE INFO: Open Vessel Data Management v2.3 (OpenVDMv2)
#               Copyright (C) OceanDataRat.org 2017
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
import argparse
import os
import sys
import tempfile
import subprocess
import errno
import gearman
import json
import time
import signal
import pwd
import grp
import shutil
import openvdm
from random import randint


cruiseConfigFN = 'ovdmConfig.json'

DEBUG = False
new_worker = None


def debugPrint(*args, **kwargs):
    if DEBUG:
        errPrint(*args, **kwargs)


def errPrint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def output_JSONDataToFile(worker, filePath, contents):
    
    try:
        os.makedirs(os.path.dirname(filePath))
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            errPrint("Unable to create parent directory for data file")
            return {'verdict': False, 'reason': 'Unable to create parent directory(ies) for data file: ' + filePath }
#    finally:
#        setOwnerGroupPermissions(worker, os.path.dirname(filePath))
    
    try:
        JSONFile = open(filePath, 'w')

        debugPrint("Saving JSON file:", filePath)
        json.dump(contents, JSONFile, indent=4)

    except IOError:
        errPrint("Error Saving JSON file:", filePath)
        return {'verdict': False, 'reason': 'Unable to create data file: ' + filePath }

    finally:
        #debugPrint("Closing JSON file", filePath)
        JSONFile.close()

    return {'verdict': True}


def setOwnerGroupPermissions(worker, path):

    warehouseUser = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']

    debugPrint(path)

    reason = []

    uid = pwd.getpwnam(warehouseUser).pw_uid
    gid = grp.getgrnam(warehouseUser).gr_gid
    # Set the file permission and ownership for the current directory

    if os.path.isfile(path):
        try:
            debugPrint("Setting ownership/permissions for", path)
            os.chown(path, uid, gid)
            os.chmod(path, 0644)
        except OSError:
            errPrint("Unable to set ownership/permissions for", path)
            reason.append("Unable to set ownership/permissions for " + path)

    else: #directory
        try:
            debugPrint("Setting ownership/permissions for", path)
            os.chown(path, uid, gid)
            os.chmod(path, 0755)
        except OSError:
            errPrint("Unable to set ownership/permissions for", path)
            reason.append("Unable to set ownership/permissions for " + path)

        for root, dirs, files in os.walk(path):
            for file in files:
                fname = os.path.join(root, file)
                try:
                    debugPrint("Setting ownership/permissions for", file)
                    os.chown(fname, uid, gid)
                    os.chmod(fname, 0644)
                except OSError:
                    errPrint("Unable to set ownership/permissions for", file)
                    reason.append("Unable to set ownership/permissions for " + file)

            for momo in dirs:
                dname = os.path.join(root, momo)
                try:
                    debugPrint("Setting ownership/permissions for", momo)
                    os.chown(dname, uid, gid)
                    os.chmod(dname, 0755)
                except OSError:
                    errPrint("Unable to set ownership/permissions for", momo)
                    reason.append("Unable to set ownership/permissions for " + momo)

    if len(reason) > 0:
        return {'verdict': False, 'reason': reason.join('\n')}

    return {'verdict': True}


def build_filelist(worker, sourceDir):

    returnFiles = {'include':[], 'exclude':[], 'new':[], 'updated':[]}
    
    for root, dirnames, filenames in os.walk(sourceDir):
        for filename in filenames:
            if os.path.islink(os.path.join(root, filename)):
                continue
            returnFiles['include'].append(os.path.join(root, filename))

    returnFiles['include'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['include']]
    
    return returnFiles

def transfer_PublicDataDir(worker, job):

    publicDataDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehousePublicDataDir']
    cruiseDir = os.path.join(worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'], worker.cruiseID)
    scienceDir = os.path.join(cruiseDir, worker.OVDM.getRequiredExtraDirectoryByName('Science')['destDir'])
    
    #debugPrint("Build file list")
    files = build_filelist(worker, publicDataDir)

    count = 1
    fileCount = len(files['include'])
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncFileListPath = tmpdir + '/rsyncFileList.txt'
        
    try:
        rsyncFileListFile = open(rsyncFileListPath, 'w')

        localTransferFileList = files['include']
        localTransferFileList = [filename.replace(publicDataDir, '', 1) for filename in localTransferFileList]

        rsyncFileListFile.write('\n'.join([str(x) for x in localTransferFileList]))

    except IOError:
        errPrint("Error Saving temporary rsync filelist file")
        rsyncFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
        
        return {'verdict': False, 'reason': 'Error Saving temporary rsync filelist file', 'files': files }

    finally:
        rsyncFileListFile.close()
    
    command = ['rsync', '-tri', '--files-from=' + rsyncFileListPath, publicDataDir + '/', scienceDir]
    debugPrint("Command:", ' '.join(command))
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #debugPrint("Line:",line) # yield line
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['new'].append(filename)
            worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
            count += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['updated'].append(filename)
            worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
            count += 1
            
        if worker.stop:
            errPrint("Stopping")
            break
    
    # Cleanup
    shutil.rmtree(tmpdir)    
    return {'verdict': True, 'files':files }

def clear_publicDataDir(worker):

    publicDataDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehousePublicDataDir']
    
    reason = []

    # Clear out PublicData
    for root, dirs, pdFiles in os.walk(publicDataDir + '/', topdown=False):
        for dir in dirs:
            dirPath = os.path.join(root, dir)
            try:
                os.rmdir(dirPath)
            except OSError:
                errPrint("Directory", dirPath, "is not empty and will not be removed")
                reason.append("Directory" + dirPath + "is not empty and will not be removed")

        for pdFile in pdFiles:
            filePath = os.path.join(root, pdFile)
            try:
                os.remove(filePath)
            except OSError:
                errPrint("File", filePath, "could not be removed")
                reason.append("File" + filePath + "could not be removed")

    if len(reason) > 0:
        return {'verdict': False, 'reason': reason.join('\n')}

    return {'verdict': True}


class OVDMGearmanWorker(gearman.GearmanWorker):
    
    def __init__(self, host_list=None):
        self.stop = False
        self.quit = False
        self.OVDM = openvdm.OpenVDM()
        self.cruiseID = ''
        self.cruiseStartDate = ''
        self.collectionSystemTransfer = {}
        self.shipboardDataWarehouseConfig = {}
        self.task = None
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])
        
    
    def get_task(self, current_job):
        tasks = self.OVDM.getTasks()
        for task in tasks:
            if task['name'] == current_job.task:
                self.task = task
                return True
        self.task = None
        return False
    
    
    def on_job_execute(self, current_job):
        self.get_task(current_job)
        payloadObj = json.loads(current_job.data)
        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()
        
        self.cruiseID = self.OVDM.getCruiseID()
        self.cruiseStartDate = self.OVDM.getCruiseStartDate()
        if len(payloadObj) > 0:
            try:
                payloadObj['cruiseID']
            except KeyError:
                self.cruiseID = self.OVDM.getCruiseID()
            else:
                self.cruiseID = payloadObj['cruiseID']
                
            try:
                payloadObj['cruiseStartDate']
            except KeyError:
                self.cruiseStartDate = self.OVDM.getCruiseStartDate()
            else:
                self.cruiseStartDate = payloadObj['cruiseStartDate']

        if self.task['taskID'] > 0:
            self.OVDM.setRunning_task(self.task['taskID'], os.getpid(), current_job.handle)
#        else:
#            self.OVDM.trackGearmanJob(taskLookup[current_job.task], os.getpid(), current_job.handle)
            
        errPrint("Job:", current_job.handle + ",", self.task['longName'], "started at:  ", time.strftime("%D %T", time.gmtime()))
        
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)
            

    def on_job_exception(self, current_job, exc_info):
        errPrint("Job:", current_job.handle + ",", self.task['longName'], "failed at:   ", time.strftime("%D %T", time.gmtime()))
        
        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail", "reason": "Worker crashed"}]))
        if int(self.task['taskID']) > 0:
            self.OVDM.setError_task(self.task['taskID'], "Worker crashed")
        else:
            self.OVDM.sendMsg(self.task['longName'] + ' failed', 'Worker crashed')
        
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        errPrint(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)

    
    def on_job_complete(self, current_job, job_results):
        resultsObj = json.loads(job_results)
        
        jobData = {}
        jobData['cruiseID'] = self.cruiseID
        jobData['cruiseStartDate'] = self.cruiseStartDate
        
        if current_job.task == 'setupNewCruise':

            gm_client = gearman.GearmanClient([self.OVDM.getGearmanServer()])
        
            for task in self.OVDM.getTasksForHook('setupNewCruise'):
                debugPrint("Adding post task:", task);
                submitted_job_request = gm_client.submit_job(task, json.dumps(jobData), background=True)
                
        elif current_job.task == 'finalizeCurrentCruise':

            gm_client = gearman.GearmanClient([self.OVDM.getGearmanServer()])
        
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
        
        debugPrint('Job Results:', json.dumps(resultsObj, indent=2))
            
        errPrint("Job:", current_job.handle + ",", self.task['longName'], "completed at:", time.strftime("%D %T", time.gmtime()))
            
        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_results)

    
    def after_poll(self, any_activity):
        self.stop = False
        self.task = None
        if self.quit:
            self.shutdown()
        else:
            self.quit = False
        return True
    
    
    def stopTask(self):
        self.stop = True
        debugPrint("Stopping current task...")

    
    def quitWorker(self):
        self.stop = True
        self.quit = True
        debugPrint("Quitting worker...")


def task_setupNewCruise(worker, job):

    job_results = {'parts':[]}

    payloadObj = json.loads(job.data)
    debugPrint('Payload:', json.dumps(payloadObj, indent=2))
    
    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'], worker.cruiseID)
        
    worker.send_job_status(job, 1, 10)
    
    gm_client = gearman.GearmanClient([worker.OVDM.getGearmanServer()])

    debugPrint("Lockdown the CruiseData directory")
    completed_job_request = gm_client.submit_job("setCruiseDataDirectoryPermissions", job.data)
    
    resultObj = json.loads(completed_job_request.result)

    if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
        job_results['parts'].append({"partName": "Lockdown the CruiseData directory", "result": "Pass"})
    else:
        errPrint("Failed to lockdown the CruiseData directory")
        job_results['parts'].append({"partName": "Lockdown the CruiseData directory", "result": "Fail", "reason": resultObj['parts'][-1]['reason']})
        return json.dumps(job_results)

    debugPrint("Creating cruise data directory")
    completed_job_request = gm_client.submit_job("createCruiseDirectory", job.data)
    
    resultObj = json.loads(completed_job_request.result)

    if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
        job_results['parts'].append({"partName": "Create cruise data directory structure", "result": "Pass"})
    else:
        errPrint("Failed to create cruise data directory")
        job_results['parts'].append({"partName": "Create cruise data directory structure", "result": "Fail", "reason": resultObj['parts'][-1]['reason']})
        return json.dumps(job_results)
    
    worker.send_job_status(job, 5, 10)
    
    #build OpenVDM Config file
    debugPrint('Exporting Cruise Configuration')
    ovdmConfig = worker.OVDM.getOVDMConfig()

    #debugPrint('Path:', os.path.join(cruiseDir,cruiseConfigFN))
    
    output_results = output_JSONDataToFile(worker, os.path.join(cruiseDir,cruiseConfigFN), ovdmConfig)
    
    if output_results['verdict']:
        job_results['parts'].append({"partName": "Export OpenVDM config data to file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Export OpenVDM config data to file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)
    
    output_results = setOwnerGroupPermissions(worker, os.path.join(cruiseDir,cruiseConfigFN))

    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Set OpenVDM config file ownership", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)
    
    worker.send_job_status(job, 7, 10)

    debugPrint("Creating MD5 summary files")
    completed_job_request = gm_client.submit_job("rebuildMD5Summary", job.data)

    resultObj = json.loads(completed_job_request.result)

    if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
        job_results['parts'].append({"partName": "Create MD5 summary files", "result": "Pass"})
    else:
        errPrint("Failed to create MD5 summary files")
        job_results['parts'].append({"partName": "Create MD5 summary files", "result": "Fail", "reason": resultObj['parts'][-1]['reason']})
        return json.dumps(job_results)

    worker.send_job_status(job, 8, 10)

    debugPrint("Creating data dashboard directory structure and manifest file")
    completed_job_request = gm_client.submit_job("rebuildDataDashboard", job.data)

    resultObj = json.loads(completed_job_request.result)

    if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
        job_results['parts'].append({"partName": "Create data dashboard directory structure and manifest file", "result": "Pass"})
    else:
        errPrint("Failed to create data dashboard directory structure and/or manifest file")
        job_results['parts'].append({"partName": "Create data dashboard directory structure and manifest file", "result": "Fail", "reason": resultObj['parts'][-1]['reason']})
        return json.dumps(job_results)

    worker.send_job_status(job, 9, 10)

    debugPrint("Updating Cruise Size")
    cruiseSize = subprocess.check_output(['du','-sb', cruiseDir]).split()[0].decode('utf-8')
    # print cruiseSize

    worker.OVDM.set_cruiseSize(cruiseSize)
    worker.OVDM.set_loweringSize("0")
    
    worker.send_job_status(job, 10, 10)

    return json.dumps(job_results)
    
    
def task_finalizeCurrentCruise(worker, job):

    job_results = {'parts':[]}

    worker.send_job_status(job, 1, 10)

    cruiseDir = os.path.join(worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'], worker.cruiseID)  
    debugPrint('Cruise Dir:', cruiseDir)

    publicDataDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehousePublicDataDir']
    debugPrint('PublicData Dir:', publicDataDir)

    scienceDir = worker.OVDM.getRequiredExtraDirectoryByName('Science')['destDir']
    debugPrint('Science Dir:', scienceDir)

    if os.path.exists(cruiseDir):
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Fail", "reason": "Cruise directory: " + cruiseDir + " could not be found"})
        return json.dumps(job_results)

    worker.send_job_status(job, 2, 10)
    debugPrint('Queuing Collection System Transfers')

    gm_client = gearman.GearmanClient([worker.OVDM.getGearmanServer()])
    
    gmData = {}
    gmData['cruiseID'] = worker.cruiseID
    gmData['cruiseStartDate'] = worker.cruiseStartDate
    gmData['systemStatus'] = "On"
    gmData['collectionSystemTransfer'] = {}
        
    #print gmData
    
    collectionSystemTransferJobs = []
    
    collectionSystemTransfers = worker.OVDM.getActiveCollectionSystemTransfers()

    for collectionSystemTransfer in collectionSystemTransfers:

        if collectionSystemTransfer['cruiseOrLowering'] == '0':
            debugPrint('Adding', collectionSystemTransfer['name'], 'to the queue')        
            gmData['collectionSystemTransfer']['collectionSystemTransferID'] = collectionSystemTransfer['collectionSystemTransferID']
        
            collectionSystemTransferJobs.append( {"task": "runCollectionSystemTransfer", "data": json.dumps(gmData)} )

    
    worker.send_job_status(job, 3, 10)

    if len(collectionSystemTransferJobs) > 0:
        debugPrint('Initiating Collection System Transfers')
        submitted_job_request = gm_client.submit_multiple_jobs(collectionSystemTransferJobs, background=False, wait_until_complete=False)
    
        worker.send_job_status(job, 4, 10)
    
        time.sleep(1)
        completed_requests = gm_client.wait_until_jobs_completed(submitted_job_request)
        debugPrint('Collection System Transfers Complete')

    worker.send_job_status(job, 5, 10)
    
    debugPrint('Transferring files from PublicData to the cruise data directory')
    
    if os.path.exists(os.path.join(cruiseDir, scienceDir)):
        job_results['parts'].append({"partName": "Verify Science Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Science Directory exists", "result": "Fail", "reason": "Science directory: " + os.path.join(cruiseDir, scienceDir) + " could not be found"})
        return json.dumps(job_results)

    if os.path.exists(publicDataDir):
        job_results['parts'].append({"partName": "Verify PublicData Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify PublicData Directory exists", "result": "Fail", "reason": "PublicData directory: " + publicDataDir+ " could not be found"})
        return json.dumps(job_results)

    output_results = transfer_PublicDataDir(worker, job)
    debugPrint("Transfer Complete")

    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Transfer PublicData files", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    job_results['parts'].append({"partName": "Transfer PublicData files", "result": "Pass"})

    files = output_results['files']

    debugPrint("PublicData Files Transferred:", json.dumps(files, indent=2))

    debugPrint('Clearing files from PublicData')
    output_results = clear_publicDataDir(worker)
    debugPrint("Clearing Complete")

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Clear out PublicData files", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Clear out PublicData files", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)
    
    worker.send_job_status(job, 9, 10)
    
    if len(files['new']) > 0 or len(files['updated']) > 0:

        output_results = setOwnerGroupPermissions(worker, os.path.join(cruiseDir, scienceDir))

        if output_results['verdict']:
            job_results['parts'].append({"partName": "Set file/directory ownership", "result": "Pass"})
        else:
            job_results['parts'].append({"partName": "Set file/directory ownership", "result": "Fail", "reason": output_results['reason']})
            return json.dumps(job_results)
        
    worker.send_job_status(job, 95, 100)
    
    #build OpenVDM Config file
    debugPrint('Exporting OpenVDM Configuration')
    ovdmConfig = worker.OVDM.getOVDMConfig()

    #debugPrint('Path:', os.path.join(cruiseDir,cruiseConfigFN))

    output_results = output_JSONDataToFile(worker, os.path.join(cruiseDir,cruiseConfigFN), ovdmConfig)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Export OpenVDM config data to file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Export OpenVDM config data to file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)
    
    output_results = setOwnerGroupPermissions(worker, os.path.join(cruiseDir,cruiseConfigFN))

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set OpenVDM config file ownership", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Set OpenVDM config file ownership", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    debugPrint("Initiating MD5 Summary Task")

    gmData = {}
    gmData['cruiseID'] = worker.cruiseID
    gmData['files'] = files
    gmData['files']['new'] = [scienceDir + '/' + filename for filename in gmData['files']['new']]
    gmData['files']['updated'] = [scienceDir + '/' + filename for filename in gmData['files']['updated']]
    
    gmData['files']['updated'].append(cruiseConfigFN)
       
    completed_job_request = gm_client.submit_job("updateMD5Summary", json.dumps(gmData))
    
    debugPrint("MD5 Summary Task Complete")

    # need to add code for cruise data transfers

    worker.send_job_status(job, 10, 10)
    return json.dumps(job_results)

def task_rsyncPublicDataToCruiseData(worker, job):

    job_results = {'parts':[]}

    cruiseDir = os.path.join(worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'], worker.cruiseID)  
    debugPrint('Cruise Dir:', cruiseDir)

    publicDataDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehousePublicDataDir']
    debugPrint('PublicData Dir:', publicDataDir)

    scienceDir = worker.OVDM.getRequiredExtraDirectoryByName('Science')['destDir']
    debugPrint('Science Dir:', scienceDir)
    
    worker.send_job_status(job, 1, 10)

    if os.path.exists(os.path.join(cruiseDir, scienceDir)):
        job_results['parts'].append({"partName": "Verify Science Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Science Directory exists", "result": "Fail", "reason": "Unable to locate the Science directory: " + os.path.join(cruiseDir, scienceDir)})
        return json.dumps(job_results)

    if os.path.exists(publicDataDir):
        job_results['parts'].append({"partName": "Verify Public Data Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Public Data Directory exists", "result": "Fail", "reason": "Unable to locate the PublicData directory: " + publicDataDir})
        return json.dumps(job_results)
    
    worker.send_job_status(job, 5, 10)
    
    output_results = transfer_PublicDataDir(worker, job)
    
    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Transfer files", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)
    
    job_results['parts'].append({"partName": "Transfer files", "result": "Pass"})

    files = output_results['files']

    debugPrint("Files Transferred:", json.dumps(files, indent=2))

    worker.send_job_status(job, 8, 10)
    
    if len(files['new']) > 0 or len(files['updated']) > 0:

        debugPrint("Set file permissions")
        output_results = setOwnerGroupPermissions(worker, os.path.join(cruiseDir, scienceDir))
        debugPrint("Set file permissions - Success")

        if output_results['verdict']:
            job_results['parts'].append({"partName": "Set file/directory ownership", "result": "Pass"})
        else:
            job_results['parts'].append({"partName": "Set file/directory ownership", "result": "Fail", "reason": output_results['reason']})
            return json.dumps(job_results)
        
        worker.send_job_status(job, 9, 100)

        debugPrint("Initiating MD5 Summary Task")

        gm_client = gearman.GearmanClient([worker.OVDM.getGearmanServer()])    
        gmData = {}
        gmData['cruiseID'] = worker.cruiseID
        gmData['files'] = files
        gmData['files']['new'] = [os.path.join(scienceDir,filename) for filename in gmData['files']['new']]
        gmData['files']['updated'] = [os.path.join(scienceDir,filename) for filename in gmData['files']['updated']]
        
        completed_job_request = gm_client.submit_job("updateMD5Summary", json.dumps(gmData))
    
        debugPrint("MD5 Summary Task Complete")

    # need to verify update MD5 completed successfully

    worker.send_job_status(job, 10, 10)
    return json.dumps(job_results)


def task_exportOVDMConfig(worker, job):

    job_results = {'parts':[]}

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    
    publicDataDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehousePublicDataDir']
    
    worker.send_job_status(job, 1, 10)

    if os.path.exists(cruiseDir):
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Fail", "reason": "Unable to locate the cruise directory: " + cruiseDir})
        return json.dumps(job_results)
    
    worker.send_job_status(job, 3, 10)

    #build OpenVDM Config file
    ovdmConfig = worker.OVDM.getOVDMConfig()

    #debugPrint('Path:', os.path.join(cruiseDir,cruiseConfigFN))
    output_results = output_JSONDataToFile(worker, os.path.join(cruiseDir,cruiseConfigFN), ovdmConfig)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Export data to file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Export data to file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    worker.send_job_status(job, 6, 10)
    
    output_results = setOwnerGroupPermissions(worker, os.path.join(cruiseDir,cruiseConfigFN))

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set file ownership", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Set file ownership", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)
    
    worker.send_job_status(job, 10, 10)
    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Main function of the script should it be run as a stand-alone utility.
# -------------------------------------------------------------------------------------
def main(argv):

    parser = argparse.ArgumentParser(description='Handle Cruise-Level tasks')
    parser.add_argument('-d', '--debug', action='store_true', help=' display debug messages')

    args = parser.parse_args()
    if args.debug:
        global DEBUG
        DEBUG = True
        debugPrint("Running in debug mode")

    debugPrint('Creating Worker...')
    global new_worker
    new_worker = OVDMGearmanWorker()

    debugPrint('Defining Signal Handlers...')
    def sigquit_handler(_signo, _stack_frame):
        errPrint("QUIT Signal Received")
        new_worker.stopTask()

    def sigint_handler(_signo, _stack_frame):
        errPrint("INT Signal Received")
        new_worker.quitWorker()

    signal.signal(signal.SIGQUIT, sigquit_handler)
    signal.signal(signal.SIGINT, sigint_handler)

    new_worker.set_client_id('cruise.py')

    debugPrint('Registering worker tasks...')
    debugPrint('   Task:', 'setupNewCruise')
    new_worker.register_task("setupNewCruise", task_setupNewCruise)
    debugPrint('   Task:', 'finalizeCurrentCruise')
    new_worker.register_task("finalizeCurrentCruise", task_finalizeCurrentCruise)
    debugPrint('   Task:', 'exportOVDMConfig')
    new_worker.register_task("exportOVDMConfig", task_exportOVDMConfig)
    debugPrint('   Task:', 'rsyncPublicDataToCruiseData')
    new_worker.register_task("rsyncPublicDataToCruiseData", task_rsyncPublicDataToCruiseData)

    debugPrint('Waiting for jobs...')
    new_worker.work()

# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])
