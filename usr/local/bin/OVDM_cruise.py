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

taskLookup = {
    "setupNewCruise": "Setting up New Cruise",
    "finalizeCurrentCruise": "Finalizing Current Cruise",
    "exportOVDMConfig": "Exporting OpenVDM Configuration",
    "rsyncPublicDataToCruiseData": "Copy PublicData to Cruise Data"
}

cruiseConfigFN = 'ovdmConfig.json'

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

        #print "Saving JSON file: " + filePath
        json.dump(contents, JSONFile, indent=4)

    except IOError:
        print "Error Saving JSON file: " + filePath
        return False

    finally:
        #print "Closing JSON file"
        JSONFile.close()
        os.chown(filePath, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)

    return True

def build_filelist(sourceDir):

    returnFiles = []
    for root, dirnames, filenames in os.walk(sourceDir):
        for filename in filenames:
            returnFiles.append(os.path.join(root, filename))
                
    returnFiles = [filename.replace(sourceDir + '/', '', 1) for filename in returnFiles]
    return returnFiles

def transfer_localSourceDir(worker, job, sourceDir, destDir):

    #print "Transfer from Local Directory"
    
#    staleness = worker.collectionSystemTransfer['staleness']
#    cruiseStartDate = worker.cruiseStartDate
    
#    destDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']+'/'+worker.cruiseID+'/'+worker.collectionSystemTransfer['destDir'].rstrip('/')
#    sourceDir = worker.collectionSystemTransfer['sourceDir'].rstrip('/')
#    sourceDir = build_sourceDir(worker).rstrip('/')

    #print "Build file list"
    files = {'include':[], 'exclude':[], 'new':[], 'updated':[]}
    
    files['include'] = build_filelist(sourceDir)

    #print "Build destination directories"
    #build_destDirectories(destDir, files['include'])
    
    count = 1
    fileCount = len(files['include'])
    #print fileCount
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncFileListPath = tmpdir + '/rsyncFileList.txt'
        
    try:
        #print "Open rsync password file"
        rsyncFileListFile = open(rsyncFileListPath, 'w')

        #print "Saving rsync password file"
        localTransferFileList = files['include']
        localTransferFileList = [filename.replace(sourceDir, '', 1) for filename in localTransferFileList]

        #print '\n'.join([str(x) for x in localTransferFileList])
        rsyncFileListFile.write('\n'.join([str(x) for x in localTransferFileList]))

    except IOError:
        print "Error Saving temporary rsync filelist file"
        #returnVal.append({"testName": "Writing temporary rsync password file", "result": "Fail"})
        rsyncFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return files    

    finally:
        #print "Closing rsync filelist file"
        rsyncFileListFile.close()
        #returnVal.append({"testName": "Writing temporary rsync password file", "result": "Pass"})
    
    command = ['rsync', '-tri', '--files-from=' + rsyncFileListPath, sourceDir + '/', destDir]
    
    #s = ' '
    #print s.join(command)
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #print(line) # yield line
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ')[1].rstrip('\n')
            files['new'].append(filename)
            #os.chown(destDir + '/' + filename, pwd.getpwnam(data['shipboardDataWarehouse']['shipboardDataWarehouseUsername']).pw_uid, grp.getgrnam(data['shipboardDataWarehouse']['shipboardDataWarehouseUsername']).gr_gid)
            worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
            count += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ')[1].rstrip('\n')
            files['updated'].append(filename)
            #os.chown(destDir + '/' + filename, pwd.getpwnam(data['shipboardDataWarehouse']['shipboardDataWarehouseUsername']).pw_uid, grp.getgrnam(data['shipboardDataWarehouse']['shipboardDataWarehouseUsername']).gr_gid)
            worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
            count += 1
            
        if worker.stop:
            print "Stopping"
            break

    # Cleanup
    shutil.rmtree(tmpdir)    
    return files

def move_files(sourceDir, destDir, warehouseUser):

    files = {'new':[],'updated':[]}
    
    for root, dirnames, filenames in os.walk(sourceDir):
        for dirname in dirnames:
            dirPath = os.path.join(root, dirname)
            os.chown(dirPath, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)
            shutil.move(dirPath, destDir)
        for filename in filenames:
            filePath = os.path.join(root, filename)
            os.chown(filePath, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)
            shutil.move(filePath, destDir)
            files['new'].append(filePath)
    
    return files
            
def build_ScienceDirPath(worker):

    # Set Error for current tranfer in DB via API
    directories = worker.OVDM.getRequiredExtraDirectories()
    for directory in directories:
        if directory['name'] == 'Science':
            return directory['destDir']
            break
    
    return ''

    
class OVDMGearmanWorker(gearman.GearmanWorker):
    
    def __init__(self, host_list=None):
        self.stop = False
        self.quit = False
        self.OVDM = openvdm.OpenVDM()
        self.cruiseID = ''
        self.cruiseStartDate = ''
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

        if int(self.taskID) > 0:
            self.OVDM.setRunning_task(self.taskID, os.getpid(), current_job.handle)
        else:
            self.OVDM.trackGearmanJob(taskLookup[current_job.task], os.getpid(), current_job.handle)
            
        print "Job: " + current_job.handle + ", " + taskLookup[current_job.task] + " started at:   " + time.strftime("%D %T", time.gmtime())
        
        #print "CruiseID: " + self.cruiseID
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
        
        jobData = {'cruiseID':'', 'self.cruiseStartDate':''}
        jobData['cruiseID'] = self.cruiseID
        jobData['cruiseStartDate'] = self.cruiseStartDate
        
        if current_job.task == 'setupNewCruise':
        
            for task in self.OVDM.getTasksForHook('setupNewCruise'):
                #print task
                submitted_job_request = gm_client.submit_job(task, json.dumps(jobData), background=True)
                
        elif current_job.task == 'finalizeCurrentCruise':
        
            for task in self.OVDM.getTasksForHook('finalizeCurrentCruise'):
                #print task
                submitted_job_request = gm_client.submit_job(task, json.dumps(jobData), background=True)
        
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


def task_setupNewCruise(worker, job):

    job_results = {'parts':[]}

    payloadObj = json.loads(job.data)
    #print 'DECODED Payload:', json.dumps(payloadObj, indent=2)
    
    shipboardDataWarehouseConfig = worker.OVDM.getShipboardDataWarehouseConfig()
    baseDir = shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = baseDir + '/' + worker.cruiseID
    

    warehouseUser = shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    
    worker.send_job_status(job, 1, 10)
    
    gm_client = gearman.GearmanClient([worker.OVDM.getGearmanServer()])
    completed_job_request = gm_client.submit_job("createCruiseDirectory", job.data)
    
    resultObj = json.loads(completed_job_request.result)
    #print 'DECODED Results from createCruiseDirectory:', json.dumps(resultObj, indent=2)

    if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
        #print "Create Directory: Passed"
        job_results['parts'].append({"partName": "Create Cruise Directory", "result": "Pass"})
    else:
        print "Create Cruise Directory: Failed"
        #print "Quitting"
        job_results += resultObj['parts']
        job_results['parts'].append({"partName": "Create Cruise Directory", "result": "Fail"})
        #print json.dumps(job_results, indent=2)
        return json.dumps(job_results)
    
    worker.send_job_status(job, 5, 10)
    
    completed_job_request = gm_client.submit_job("rebuildDataDashboard", job.data)

    resultObj = json.loads(completed_job_request.result)
    #print 'DECODED Results from rebuildDataDashboard:', json.dumps(resultObj, indent=2)

    if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
        #print "Connection Test: Passed"
        job_results['parts'].append({"partName": "Create Data Dashboard Manifest", "result": "Pass"})
    else:
        print "Create Data Dashboard Manifest File: Failed"
        #print "Quitting"
        job_results += resultObj['parts']
        job_results['parts'].append({"partName": "Create Data Dashboard Manifest", "result": "Fail"})
        #print json.dumps(job_results, indent=2)
        return json.dumps(job_results)
    
    worker.send_job_status(job, 7, 10)
    
    completed_job_request = gm_client.submit_job("rebuildMD5Summary", job.data)

    resultObj = json.loads(completed_job_request.result)
    #print 'DECODED Results rebuildMD5Summary:', json.dumps(resultObj, indent=2)

    if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
        #print "Connection Test: Passed"
        job_results['parts'].append({"partName": "Create MD5 Summary", "result": "Pass"})
    else:
        print "Create MD5 Summary File: Failed"
        #print "Quitting"
        job_results += resultObj['parts']
        job_results['parts'].append({"partName": "Create MD5 Summary", "result": "Fail"})
        #print json.dumps(job_results, indent=2)
        return json.dumps(job_results)
    
    worker.send_job_status(job, 9, 10)

    #build OpenVDM Config file
    ovdmConfig = worker.OVDM.getOVDMConfig()

    output_JSONDataToFile(cruiseDir + '/' + cruiseConfigFN, ovdmConfig, warehouseUser)
    
    worker.send_job_status(job, 10, 10)

    return json.dumps(job_results)
    
    
def task_finalizeCurrentCruise(worker, job):

    job_results = {'parts':[]}
    gmData = {}

    payloadObj = json.loads(job.data)
    #print 'DECODED:', json.dumps(payloadObj, indent=2)

    shipboardDataWarehouseConfig = worker.OVDM.getShipboardDataWarehouseConfig()
    baseDir = shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = baseDir + '/' + worker.cruiseID
    warehouseUser = shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    
    publicDataDir = shipboardDataWarehouseConfig['shipboardDataWarehousePublicDataDir']
    scienceDir = cruiseDir + '/' + build_ScienceDirPath(worker)
    print 'scienceDir:', scienceDir
    
    worker.send_job_status(job, 1, 10)

    if os.path.exists(cruiseDir):
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Fail"})
        return json.dumps(job_results)

    if os.path.exists(publicDataDir):
        job_results['parts'].append({"partName": "Verify Public Data Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Public Data Directory exists", "result": "Fail"})
        return json.dumps(job_results)

    gm_client = gearman.GearmanClient([worker.OVDM.getGearmanServer()])
    
    gmData['cruiseID'] = worker.cruiseID
    gmData['cruiseStartDate'] = worker.cruiseStartDate
    gmData['systemStatus'] = "On";
    gmData['collectionSystemTransfer'] = {}
        
    print gmData
    
    collectionSystemTransferJobs = []
    
    worker.send_job_status(job, 3, 10)

    collectionSystemTransfers = worker.OVDM.getCollectionSystemTransfers()

    for collectionSystemTransfer in collectionSystemTransfers:
        
        gmData['collectionSystemTransfer']['collectionSystemTransferID'] = collectionSystemTransfer['collectionSystemTransferID']
        #print gmData
        
        collectionSystemTransferJobs.append( {"task": "runCollectionSystemTransfer", "data": json.dumps(gmData)} )

    #print json.dumps(collectionSystemTransferJobs, indent=2)
    
    submitted_job_request = gm_client.submit_multiple_jobs(collectionSystemTransferJobs, background=False, wait_until_complete=False)
    
    #print submitted_job_request

    worker.send_job_status(job, 4, 10)
    
    time.sleep(1)
    completed_requests = gm_client.wait_until_jobs_completed(submitted_job_request)

    worker.send_job_status(job, 7, 10)
    
    #print "Try to move Public Data from " + publicDataDir + " to " + scienceDir;
    files = move_files(publicDataDir, scienceDir, warehouseUser)
    
    worker.send_job_status(job, 8, 10)
    
    #build OpenVDM Config file
    ovdmConfig = worker.OVDM.getOVDMConfig()
    output_JSONDataToFile(cruiseDir + '/' + cruiseConfigFN, ovdmConfig, warehouseUser)
    worker.send_job_status(job, 9, 10)
    
    completed_job_request = gm_client.submit_job("rebuildMD5Summary", job.data)
    
    # need to add code for cruise data transfers
    worker.send_job_status(job, 10, 10)
    return json.dumps(job_results)

def task_rsyncPublicDataToCruiseData(worker, job):

    job_results = {'parts':[]}

    payloadObj = json.loads(job.data)
    print 'DECODED:', json.dumps(payloadObj, indent=2)

    shipboardDataWarehouseConfig = worker.OVDM.getShipboardDataWarehouseConfig()
    baseDir = shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = baseDir + '/' + worker.cruiseID
    warehouseUser = shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    
    publicDataDir = shipboardDataWarehouseConfig['shipboardDataWarehousePublicDataDir']
    scienceDir = cruiseDir + '/' + build_ScienceDirPath(worker)
    print 'scienceDir:', scienceDir
    
    worker.send_job_status(job, 1, 10)

    if os.path.exists(cruiseDir):
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Fail"})
        return json.dumps(job_results)

    if os.path.exists(publicDataDir):
        job_results['parts'].append({"partName": "Verify Public Data Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Public Data Directory exists", "result": "Fail"})
        return json.dumps(job_results)
    
    worker.send_job_status(job, 2, 10)
    
    files = transfer_localSourceDir(worker, job, publicDataDir, scienceDir)
    print json.dumps(files, indent=2)

    gm_client = gearman.GearmanClient([worker.OVDM.getGearmanServer()])
    
    gmData = {}
    gmData['cruiseID'] = worker.cruiseID
    gmData['files'] = files;
    gmData['files']['new'] = [build_ScienceDirPath(worker) + '/' + filename for filename in gmData['files']['new']]
    gmData['files']['updated'] = [build_ScienceDirPath(worker) + '/' + filename for filename in gmData['files']['updated']]
    
    worker.send_job_status(job, 9, 10)
        
    completed_job_request = gm_client.submit_job("updateMD5Summary", json.dumps(gmData))
    
    # need to add code for cruise data transfers
    worker.send_job_status(job, 10, 10)
    return json.dumps(job_results)


def task_exportOVDMConfig(worker, job):

    job_results = {'parts':[]}
    gmData = {}

    payloadObj = json.loads(job.data)
    #print 'DECODED:', json.dumps(payloadObj, indent=2)

    shipboardDataWarehouseConfig = worker.OVDM.getShipboardDataWarehouseConfig()
    cruiseDir = shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']+'/'+worker.OVDM.getCruiseID()
    publicDataDir = shipboardDataWarehouseConfig['shipboardDataWarehousePublicDataDir']
    warehouseUser = shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    
    worker.send_job_status(job, 1, 10)

    if os.path.exists(cruiseDir):
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Fail"})
        return json.dumps(job_results)
    
    #build OpenVDM Config file
    ovdmConfig = worker.OVDM.getOVDMConfig()
    #print json.dumps(ovdmConfig, indent=2)
    output_JSONDataToFile(cruiseDir + '/' + cruiseConfigFN, ovdmConfig, warehouseUser)
    
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

new_worker.set_client_id('cruise.py')
new_worker.register_task("setupNewCruise", task_setupNewCruise)
new_worker.register_task("finalizeCurrentCruise", task_finalizeCurrentCruise)
new_worker.register_task("exportOVDMConfig", task_exportOVDMConfig)
new_worker.register_task("rsyncPublicDataToCruiseData", task_rsyncPublicDataToCruiseData)

new_worker.work()
