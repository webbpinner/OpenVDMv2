# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_lowering.py
#
#  DESCRIPTION:  Gearman worker the handles the tasks of initializing a new lowering
#                and finalizing the current lowering.
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.3
#      CREATED:  2015-01-01
#     REVISION:  2017-10-05
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


loweringConfigFN = 'loweringConfig.json'

DEBUG = False
new_worker = None


def debugPrint(*args, **kwargs):
    if DEBUG:
        errPrint(*args, **kwargs)


def errPrint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def setOwnerGroupPermissions(worker, path):

    warehouseUser = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']

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

def output_JSONDataToFile(worker, filePath, contents):
    
    try:
        os.makedirs(os.path.dirname(filePath))
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            errPrint("Unable to create parent directory for data file")
            return {'verdict': False, 'reason': 'Unable to create parent directory(ies) for data file: ' + filePath }
    
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


def build_filelist(worker, sourceDir):

    returnFiles = {'include':[], 'exclude':[], 'new':[], 'updated':[]}
    
    for root, dirnames, filenames in os.walk(sourceDir):
        for filename in filenames:
            if os.path.islink(os.path.join(root, filename)):
                continue
            returnFiles['include'].append(os.path.join(root, filename))

    returnFiles['include'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['include']]
    
    return returnFiles

    
class OVDMGearmanWorker(gearman.GearmanWorker):
    
    def __init__(self, host_list=None):
        self.stop = False
        self.quit = False
        self.OVDM = openvdm.OpenVDM()
        self.cruiseID = ''
        self.loweringID = ''
        self.loweringStartDate = ''
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
        self.loweringID = self.OVDM.getLoweringID()
        self.loweringStartDate = self.OVDM.getLoweringStartDate()
        if len(payloadObj) > 0:
            try:
                payloadObj['loweringID']
            except KeyError:
                self.loweringID = self.OVDM.getLoweringID()
            else:
                self.loweringID = payloadObj['loweringID']
                
            try:
                payloadObj['loweringStartDate']
            except KeyError:
                self.loweringStartDate = self.OVDM.getLoweringStartDate()
            else:
                self.loweringStartDate = payloadObj['loweringStartDate']

        if self.task['taskID'] > 0:
            self.OVDM.setRunning_task(self.task['taskID'], os.getpid(), current_job.handle)
#        else:
#            self.OVDM.trackGearmanJob(taskLookup[current_job.task], os.getpid(), current_job.handle)
            
        errPrint("Job:", current_job.handle + ",", self.task['longName'], "started at:  ", time.strftime("%D %T", time.gmtime()))
        
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)
            

    def on_job_exception(self, current_job, exc_info):
        errPrint("Job:", current_job.handle + ",", self.task['longName'], "failed at:   ", time.strftime("%D %T", time.gmtime()))
        
        self.send_job_data(current_job, json.dumps([{"partName": "Worker Crashed", "result": "Fail", "reason": "Worker crashed"}]))
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
        jobData['loweringID'] = self.loweringID
        jobData['loweringStartDate'] = self.loweringStartDate
        
        if current_job.task == 'setupNewLowering':

            gm_client = gearman.GearmanClient([self.OVDM.getGearmanServer()])
        
            for task in self.OVDM.getTasksForHook('setupNewLowering'):
                debugPrint("Adding post task:", task);
                submitted_job_request = gm_client.submit_job(task, json.dumps(jobData), background=True)
                
        elif current_job.task == 'finalizeCurrentLowering':

            gm_client = gearman.GearmanClient([self.OVDM.getGearmanServer()])
        
            for task in self.OVDM.getTasksForHook('finalizeCurrentLowering'):
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


def task_setupNewLowering(worker, job):

    job_results = {'parts':[]}

    payloadObj = json.loads(job.data)
    debugPrint('Payload:', json.dumps(payloadObj, indent=2))
    
    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    loweringDataBaseDir = os.path.join(cruiseDir, worker.shipboardDataWarehouseConfig['loweringDataBaseDir'])
    loweringDir = os.path.join(loweringDataBaseDir, worker.loweringID)
        
    worker.send_job_status(job, 1, 10)
    
    gm_client = gearman.GearmanClient([worker.OVDM.getGearmanServer()])

    #debugPrint("Lockdown the LoweringData directory")
    #completed_job_request = gm_client.submit_job("setLoweringDataDirectoryPermissions", job.data)
    
    #resultObj = json.loads(completed_job_request.result)
    
    #if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
    #    job_results['parts'].append({"partName": "Lockdown the LoweringData directory", "result": "Pass"})
    #else:
    #    errPrint("Failed to lockdown the LoweringData directory")
    #    job_results['parts'].append({"partName": "Lockdown the LoweringData directory", "result": "Fail"})
    #    return json.dumps(job_results)

    debugPrint("Creating lowering data directory")
    completed_job_request = gm_client.submit_job("createLoweringDirectory", job.data)
    
    resultObj = json.loads(completed_job_request.result)

    if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
        job_results['parts'].append({"partName": "Create lowering data directory structure", "result": "Pass"})
    else:
        errPrint("Failed to create lowering data directory")
        job_results['parts'].append({"partName": "Create lowering data directory structure", "result": "Fail", "reason": resultObj['parts'][-1]['reason']})
        return json.dumps(job_results)
    
    worker.send_job_status(job, 5, 10)
    
    #debugPrint("Creating MD5 summary files")
    #completed_job_request = gm_client.submit_job("rebuildMD5Summary", job.data)

    #resultObj = json.loads(completed_job_request.result)
    #print 'DECODED Results rebuildMD5Summary:', json.dumps(resultObj, indent=2)

    #if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
    #    job_results['parts'].append({"partName": "Create MD5 summary files", "result": "Pass"})
    #else:
    #    errPrint("Failed to create MD5 summary files")
    #    job_results['parts'].append({"partName": "Create MD5 summary files", "result": "Fail"})
    #    return json.dumps(job_results)
    
    #worker.send_job_status(job, 7, 10)

    #debugPrint("Creating data dashboard directory structure and manifest file")
    #completed_job_request = gm_client.submit_job("rebuildDataDashboard", job.data)

    #resultObj = json.loads(completed_job_request.result)
    #print 'DECODED Results from rebuildDataDashboard:', json.dumps(resultObj, indent=2)

    #if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
    #    job_results['parts'].append({"partName": "Create data dashboard directory structure and manifest file", "result": "Pass"})
    #else:
    #    errPrint("Failed to create data dashboard directory structure and/or manifest file")
    #    job_results['parts'].append({"partName": "Create data dashboard directory structure and manifest file", "result": "Fail"})
    #    return json.dumps(job_results)
    
    worker.send_job_status(job, 8, 10)

    #build lowering Config file
    debugPrint('Exporting Lowering Configuration')
    loweringConfig = worker.OVDM.getLoweringConfig()

    #debugPrint('Path:', os.path.join(loweringDir,loweringConfigFN))

    output_results = output_JSONDataToFile(worker, os.path.join(loweringDir,loweringConfigFN), loweringConfig)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Export lowering config data to file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Export lowering config data to file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)
    
    output_results = setOwnerGroupPermissions(worker, os.path.join(loweringDir,loweringConfigFN))

    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Set lowering config file ownership", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    worker.send_job_status(job, 9, 10)

    debugPrint("Updating Lowering Size")
    loweringSize = subprocess.check_output(['du','-sb', loweringDir]).split()[0].decode('utf-8')
    # print cruiseSize

    worker.OVDM.set_loweringSize(loweringSize)
    
    worker.send_job_status(job, 10, 10)

    return json.dumps(job_results)
    
    
def task_finalizeCurrentLowering(worker, job):

    job_results = {'parts':[]}

    worker.send_job_status(job, 1, 10)

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)

    loweringDataBaseDir = os.path.join(cruiseDir, worker.shipboardDataWarehouseConfig['loweringDataBaseDir'])
    loweringDir = os.path.join(loweringDataBaseDir, worker.loweringID)

    if os.path.exists(loweringDir) and (worker.loweringID != ''):
        job_results['parts'].append({"partName": "Verify Lowering Directory exists", "result": "Pass"})
    else:
        errorPrint("Failed to find lowering directory:", loweringDir)
        job_results['parts'].append({"partName": "Verify Lowering Directory exists", "result": "Fail", "reason": "Lowering directory: " + loweringDir + " could not be found"})
        return json.dumps(job_results)

    worker.send_job_status(job, 3, 10)
    debugPrint('Queuing Collection System Transfers')

    gm_client = gearman.GearmanClient([worker.OVDM.getGearmanServer()])
    
    gmData = {}
    gmData['loweringID'] = worker.loweringID
    gmData['loweringStartDate'] = worker.loweringStartDate
    gmData['systemStatus'] = "On"
    gmData['collectionSystemTransfer'] = {}
        
    #print gmData
    
    collectionSystemTransferJobs = []
    
    collectionSystemTransfers = worker.OVDM.getActiveCollectionSystemTransfers()

    for collectionSystemTransfer in collectionSystemTransfers:

        if collectionSystemTransfer['cruiseOrLowering'] == '1':
            debugPrint('Adding', collectionSystemTransfer['name'], 'to the queue')        
            gmData['collectionSystemTransfer']['collectionSystemTransferID'] = collectionSystemTransfer['collectionSystemTransferID']
        
            collectionSystemTransferJobs.append( {"task": "runCollectionSystemTransfer", "data": json.dumps(gmData)} )


    if len(collectionSystemTransferJobs) > 0:
    
        worker.send_job_status(job, 5, 10)

        debugPrint('Initiating Collection System Transfers')
        submitted_job_request = gm_client.submit_multiple_jobs(collectionSystemTransferJobs, background=False, wait_until_complete=False)
    
        worker.send_job_status(job, 7, 10)
    
        time.sleep(1)
        completed_requests = gm_client.wait_until_jobs_completed(submitted_job_request)
        debugPrint('Collection System Transfers Complete')

        worker.send_job_status(job, 9, 10)
    
    #build Lowering Config file
    debugPrint('Exporting Lowering Configuration')
    loweringConfig = worker.OVDM.getLoweringConfig()
    loweringConfig['loweringFinalizedOn'] = loweringConfig['configCreatedOn']

    #debugPrint('Path:', os.path.join(loweringDir,loweringConfigFN))
    output_results = output_JSONDataToFile(worker, os.path.join(loweringDir,loweringConfigFN), loweringConfig)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Export Lowering config data to file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Export Lowering config data to file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)
    
    output_results = setOwnerGroupPermissions(worker, os.path.join(loweringDir,loweringConfigFN))

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set Lowering config file ownership", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Set Lowering config file ownership", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    worker.send_job_status(job, 10, 10)
    return json.dumps(job_results)


def task_exportLoweringConfig(worker, job):

    job_results = {'parts':[]}

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    loweringDataBaseDir = os.path.join(cruiseDir, worker.shipboardDataWarehouseConfig['loweringDataBaseDir'])
    loweringDir = os.path.join(loweringDataBaseDir, worker.loweringID)

    worker.send_job_status(job, 1, 10)

    if os.path.exists(loweringDir) and (worker.loweringID != ''):
        job_results['parts'].append({"partName": "Verify Lowering Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Lowering Directory exists", "result": "Fail", "result": "Fail", "reason": "Unable to locate the lowering directory: " + loweringDir})
        return json.dumps(job_results)

    worker.send_job_status(job, 3, 10)

    #build OpenVDM Config file
    loweringConfig = worker.OVDM.getLoweringConfig()

    loweringConfigFilePath = os.path.join(loweringDir,loweringConfigFN)

    if os.path.isfile(loweringConfigFilePath):
        try:

            with open(loweringConfigFilePath) as json_file:  
                data = json.load(json_file)
                if "loweringFinalizedOn" in data:
                    loweringConfig['loweringFinalizedOn'] = data['loweringFinalizedOn']
        
        except OSError as error:
            job_results['parts'].append({"partName": "Read existing configuration file", "result": "Fail", "reason": error})
            return json.dumps(job_results)

        else:
            job_results['parts'].append({"partName": "Read existing configuration file", "result": "Pass"})

    for transfer in loweringConfig['cruiseDataTransfersConfig']:
        del transfer['sshPass']
        del transfer['rsyncPass']
        del transfer['smbPass']

    for transfer in loweringConfig['collectionSystemTransfersConfig']:
        del transfer['sshPass']
        del transfer['rsyncPass']
        del transfer['smbPass']

    output_results = output_JSONDataToFile(worker, loweringConfigFilePath, loweringConfig)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Export data to file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Export data to file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    worker.send_job_status(job, 6, 10)
    
    output_results = setOwnerGroupPermissions(worker, os.path.join(loweringDir,loweringConfigFN))

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

    parser = argparse.ArgumentParser(description='Handle Lowering-Level tasks')
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

    new_worker.set_client_id('lowering.py')

    debugPrint('Registering worker tasks...')
    debugPrint('   Task:', 'setupNewLowering')
    new_worker.register_task("setupNewLowering", task_setupNewLowering)
    debugPrint('   Task:', 'finalizeCurrentLowering')
    new_worker.register_task("finalizeCurrentLowering", task_finalizeCurrentLowering)
    debugPrint('   Task:', 'exportLoweringConfig')
    new_worker.register_task("exportLoweringConfig", task_exportLoweringConfig)
#    debugPrint('   Task:', 'rsyncPublicDataToLoweringData')
#    new_worker.register_task("rsyncPublicDataToLoweringData", task_rsyncPublicDataToLoweringData)

    debugPrint('Waiting for jobs...')
    new_worker.work()

# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])
