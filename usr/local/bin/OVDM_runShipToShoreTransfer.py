# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_runShipToShoreTransfer.py
#
#  DESCRIPTION:  Gearman worker that handles the transfer of data from the Shipboard
#                Data Warehouse to a Shoreside Data Warehouse.
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.0
#      CREATED:  2015-01-01
#     REVISION:  2015-02-07
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
import gearman
import shutil
import json
import time
import calendar
import fnmatch
import subprocess
import signal
import pwd
import grp
import openvdm
from random import randint


def getShipToShoreTransfer(worker):
    cruiseDataTransfers = worker.OVDM.getRequiredCruiseDataTransfers()
    for cruiseDataTransfer in cruiseDataTransfers:
        if cruiseDataTransfer['name'] == 'SSDW':
            return cruiseDataTransfer
    
    return {}

def build_filelist(sourceDir, filters):

    #print 'Filters:', json.dumps(filters, indent=2)
    #print 'sourceDir:', sourceDir    
    returnFiles = {'include':[], 'new':[], 'updated':[]}
    for includeFilter in filters['includeFilter']:
        for root, dirnames, filenames in os.walk(sourceDir):
            for filename in filenames:
                #print includeFilter, os.path.join(root, filename)
                if fnmatch.fnmatch(os.path.join(root, filename), includeFilter):
                    #print os.path.join(root, filename), "matched!"
                    returnFiles['include'].append(os.path.join(root, filename))

    returnFiles['include'] = [filename.replace(sourceDir, '', 1) for filename in returnFiles['include']]
    #print json.dumps(returnFiles, indent=2)
    return returnFiles

def build_destDirectories(destDir, files):
    files = [filename.replace(filename, destDir + filename, 1) for filename in files]
    #print 'DECODED Files:', json.dumps(files, indent=2)

    for dirname in set(os.path.dirname(p) for p in files):
        if not os.path.isdir(dirname):
            #print "Creating Directory: " + dirname
            os.makedirs(dirname)


def build_logfileDirPath(worker):

    #print siteRoot
    requiredExtraDirectories = worker.OVDM.getRequiredExtraDirectories()

    for directory in requiredExtraDirectories:
        if directory['name'] == 'Transfer Logs':
            return worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'] + '/' + worker.cruiseID + '/' + directory['destDir']
            break
    
    return ''


def build_filters(worker, rawFilters):
    
    returnFilters = rawFilters
    #print json.dumps(rawFilters, indent=2)
    
    #returnFilters['includeFilter'] = returnFilters['includeFilter'].replace('{cruiseID}', worker.cruiseID)
    returnFilters['includeFilter'] = [includeFilter.replace('{cruiseID}', worker.cruiseID) for includeFilter in returnFilters['includeFilter']]
    #returnFilters['excludeFilter'] = returnFilters['excludeFilter'].replace('{cruiseID}', worker.cruiseID)
    #returnFilters['ignoreFilter'] =  returnFilters['ignoreFilter'].replace('{cruiseID}', worker.cruiseID)
    
    #print json.dumps(returnFilters, indent=2)
    return returnFilters

def writeLogFile(logfileName, warehouseUser, files):
    
    try:
        #print "Open MD5 Summary MD5 file"
        Logfile = open(logfileName, 'w')

        #print "Saving MD5 Summary MD5 file"
        Logfile.write(json.dumps(files))

    except IOError:
        print "Error Saving transfer logfile"
        return False

    finally:
        #print "Closing MD5 Summary MD5 file"
        Logfile.close()
        os.chown(logfileName, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)

    return True            
            
def transfer_sshDestDir(worker, job):

    #print "Transfer from Data Warehouse"
    
    #print "Building filters"
    rawFilters = {'includeFilter':[]}
    shipToShoreTransfers = []
    shipToShoreTransfers += worker.OVDM.getShipToShoreTransfers()
    shipToShoreTransfers += worker.OVDM.getRequiredShipToShoreTransfers()
    #print json.dumps(shipToShoreTransfers, indent=2)
    
    for x in range(1, 6):
        #print "Processing priority " + str(x) + " transfers"
        for shipToShoreTransfer in shipToShoreTransfers:
            if shipToShoreTransfer['priority'] == str(x):
                if shipToShoreTransfer['enable'] == '1':
                    #print json.dumps(shipToShoreTransfer, indent=2)
                    if not shipToShoreTransfer['collectionSystem'] == "0":
                        #print "Retrieving Collection System information"
                        collectionSystem = worker.OVDM.getCollectionSystemTransfer(shipToShoreTransfer['collectionSystem'])
                        #print json.dumps(collectionSystem, indent=2)
                        shipToShoreFilters = shipToShoreTransfer['includeFilter'].split(' ')
                        shipToShoreFilters = ['*/' + worker.cruiseID + '/' + collectionSystem['destDir'] + '/' + shipToShoreFilter for shipToShoreFilter in shipToShoreFilters]
                        rawFilters['includeFilter'] = rawFilters['includeFilter'] + shipToShoreFilters
                    elif not shipToShoreTransfer['extraDirectory'] == "0":
                        #print "Retrieving Extra Directory information"
                        extraDirectory = worker.OVDM.getExtraDirectory(shipToShoreTransfer['extraDirectory'])
                        #print json.dumps(extraDirectory)
                        shipToShoreFilters = shipToShoreTransfer['includeFilter'].split(' ')
                        shipToShoreFilters = ['*/' + worker.cruiseID + '/' + extraDirectory['destDir'] + '/' + shipToShoreFilter for shipToShoreFilter in shipToShoreFilters]
                        #print json.dumps(extraDirectory, indent=2)
                        rawFilters['includeFilter'] = rawFilters['includeFilter'] + shipToShoreFilters
                    else:
                        shipToShoreFilters = shipToShoreTransfer['includeFilter'].split(' ')
                        shipToShoreFilters = ['*/' + worker.cruiseID + '/' + shipToShoreFilter for shipToShoreFilter in shipToShoreFilters]
                        rawFilters['includeFilter'] = rawFilters['includeFilter'] + shipToShoreFilters

    #print "Raw Filters:"
    #print json.dumps(rawFilters, indent=2)
    
    filters = build_filters(worker, rawFilters)
    #print "Proc Filters:"
    #print json.dumps(filters, indent=2)

    sourceDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'] + '/' + worker.cruiseID
    #print sourceDir
    
    bwLimit = worker.OVDM.getShipToShoreBWLimit()
    bwLimitStatus = worker.OVDM.getShipToShoreBWLimitStatus()
    bwLimitStr = '--bwlimit=10000'
    
    if bwLimitStatus == "On" and not bwLimit == "0":
        #print "Setting bandwidth limit"
        bwLimitStr = '--bwlimit=' + bwLimit
            
    #print "Build file list"
    files = build_filelist(sourceDir, filters)
    files['include'] = [ '/' + worker.cruiseID + filepath for filepath in files['include']]
    
    #print json.dumps(files)
    
    createdDirs = []

    count = 1
    fileCount = len(files['include'])
    #print '\n'.join(files['include'])
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncFileListPath = tmpdir + '/rsyncFileList.txt'
        
    try:
        #print "Open rsync filelist file"
        rsyncFileListFile = open(rsyncFileListPath, 'w')

        #print "Saving rsync filelist file"
        #print '\n'.join([worker.cruiseID + str(x) for x in files['include']])
        rsyncFileListFile.write('\n'.join(files['include']))

    except IOError:
        print "Error Saving temporary rsync filelist file"
        returnVal.append({"testName": "Writing temporary rsync filelist file", "result": "Fail"})
        rsyncFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return files    

    finally:
        #print "Closing rsync filelist file"
        rsyncFileListFile.close()
        #returnVal.append({"testName": "Writing temporary rsync password file", "result": "Pass"})
    
    command = ['sshpass', '-p', worker.cruiseDataTransfer['sshPass'], 'rsync', '-ti', '--partial', bwLimitStr, '-e', 'ssh -c arcfour', '--files-from=' + rsyncFileListPath, worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'], worker.cruiseDataTransfer['sshUser'] + '@' + worker.cruiseDataTransfer['sshServer'] + ':' + worker.cruiseDataTransfer['destDir']]
    
    #s = ' '
    #print s.join(command)
    
    #print "Copying files"
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    #print "lines interator"
    for line in lines_iterator:
        #print(line) # yield line
        if line.startswith( '<f+++++++++' ):
            #print line.split(' ')[1]
            files['new'].append(line.split(' ')[1])
        elif line.startswith( '<f.' ):
            #print line.split(' ')[1]
            files['updated'].append(line.split(' ')[1])
        worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
        count += 1
        
        elapseTime = calendar.timegm(time.gmtime()) - calendar.timegm(worker.startTime)
        if elapseTime > 3480: #58 minutes
            worker.stopTransfer()
            
        if worker.stop:
            print "Stopping"
            break
    
    # Cleanup
    shutil.rmtree(tmpdir)
        
    return files

        
class OVDMGearmanWorker(gearman.GearmanWorker):

    def __init__(self, host_list=None):
        self.stop = False
        self.quit = False
        self.OVDM = openvdm.OpenVDM()
        self.startTime = 0
        self.cruiseID = ''
        self.systemStatus = ''
        self.cruiseDataTransfer = {}
        self.shipboardDataWarehouseConfig = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])
        
    def on_job_execute(self, current_job):
        payloadObj = json.loads(current_job.data)
        #print json.dumps(payloadObj, indent=2)
        self.startTime = time.gmtime()
        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()
        self.cruiseDataTransfer = getShipToShoreTransfer(self)
        self.cruiseID = self.OVDM.getCruiseID()
        self.systemStatus = self.OVDM.getSystemStatus()
        
        if len(payloadObj) > 0:
            try:
                payloadObj['cruiseDataTransfer']
            except KeyError:
                print "Usings defaults"
            else:
                self.cruiseDataTransfer.update(payloadObj['cruiseDataTransfer'])
        
            try:
                payloadObj['cruiseID']
            except KeyError:
                self.cruiseID = self.OVDM.getCruiseID()
            else:
                self.cruiseID = payloadObj['cruiseID']

            try:
                payloadObj['systemStatus']
            except KeyError:
                self.systemStatus = self.OVDM.getSystemStatus()
            else:
                self.systemStatus = payloadObj['systemStatus']
        
        print "Job: " + current_job.handle + ", " + self.cruiseDataTransfer['name'] + " transfer started at:   " + time.strftime("%D %T", time.gmtime())

        return super(OVDMGearmanWorker, self).on_job_execute(current_job)

    def on_job_exception(self, current_job, exc_info):
        print "Job: " + current_job.handle + ", " + self.cruiseDataTransfer['name'] + " transfer failed at:    " + time.strftime("%D %T", time.gmtime())
        
        self.send_job_data(current_job, json.dumps([{"partName": "Unknown Part of Transfer", "result": "Fail"}]))
        self.OVDM.setError_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'], "Unknown Part of Transfer Failed")
        
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)

    def on_job_complete(self, current_job, job_result):
        resultObj = json.loads(job_result)
        
        #if resultObj['files']['new'] or resultObj['files']['updated']:

        #    jobData = {'cruiseID':'', 'cruiseDataTransferID':'', 'files':{}}
        #    jobData['cruiseID'] = self.cruiseID
        #    jobData['cruiseDataTransferID'] = self.cruiseDataTransfer['cruiseDataTransferID']

        #    destDir = build_destDir(self).rstrip('/')
        #    jobData['files'] = resultObj['files']
        #    jobData['files']['new'] = [destDir + '/' + filename for filename in jobData['files']['new']]
        #    jobData['files']['updated'] = [destDir + '/' + filename for filename in jobData['files']['updated']]
                
        #    gm_client = gearman.GearmanClient([self.OVDM.getGearmanServer()])
            
            #for task in self.OVDM.getTasksForHook('runCruiseDataTransfer'):
                #print task
            #    submitted_job_request = gm_client.submit_job(task, json.dumps(jobData), background=True)
        
        # If the last part of the results failed
        if len(resultObj['parts']) > 0:
            if resultObj['parts'][-1]['result'] == "Fail": # Final Verdict
                #print "...but there was an error:"
                print json.dumps(resultObj['parts'])
                self.OVDM.setError_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'], resultObj['parts'][-1]['partName'])
            else:
                self.OVDM.setIdle_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'])
        else:
            self.OVDM.setIdle_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'])

        print "Job: " + current_job.handle + ", " + self.cruiseDataTransfer['name'] + " transfer completed at: " + time.strftime("%D %T", time.gmtime())
            
        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_result)


    def after_poll(self, any_activity):
        self.stop = False
        if self.quit:
            print "Quitting"
            self.shutdown()
        return True
    
    def stopTransfer(self):
        self.stop = True
        
    def quitWorker(self):
        self.stop = True
        self.quit = True

def task_runShipToShoreTransfer(worker, job):

    time.sleep(randint(0,5))

    job_results = {'parts':[], 'files':[]}
    

    if worker.cruiseDataTransfer['enable'] == "1" and worker.systemStatus == "On":
        #print "Transfer Enabled"
        job_results['parts'].append({"partName": "Transfer Enabled", "result": "Pass"})
    else:
        #print "Transfer Disabled"
        #print "Stopping"
        #job_results['parts'].append({"partName": "Transfer Enabled", "result": "Fail"})
        return json.dumps(job_results)

    if worker.cruiseDataTransfer['status'] != "1": #running
        #print "Transfer is not already in-progress"
        job_results['parts'].append({"partName": "Transfer In-Progress", "result": "Pass"})
    else:
        #print "Transfer is already in-progress"
        #job_results['parts'].append({"partName": "Transfer In-Progress", "result": "Fail"})
        #print "Stopping"
        return json.dumps(job_results)

    #print json.dumps(worker.cruiseDataTransfer['cruiseDataTransferID'])
    
    # Set transfer status to "Running"
    worker.OVDM.setRunning_cruiseDataTransfer(worker.cruiseDataTransfer['cruiseDataTransferID'], os.getpid(), job.handle)
    
    #print "Testing configuration"
    worker.send_job_status(job, 1, 10)

    # First test to see if the transfer can occur 
    gm_client = gearman.GearmanClient([worker.OVDM.getGearmanServer()])
    
    gmData = {}
    gmData['cruiseDataTransfer'] = worker.cruiseDataTransfer
    #gmData['cruiseDataTransfer']['status'] = "1"
    gmData['cruiseID'] = worker.cruiseID
    
    completed_job_request = gm_client.submit_job("testCruiseDataTransfer", json.dumps(gmData))
    resultsObj = json.loads(completed_job_request.result)
    #print 'DECODED Results:', json.dumps(resultsObj, indent=2)

    if resultsObj[-1]['result'] == "Pass": # Final Verdict
        #print "Connection Test: Passed"
        job_results['parts'].append({'partName': 'Connection Test', 'result': 'Pass'})
    else:
        #print "Connection Test: Failed"
        #print "Stopping"
        job_results['parts'].append({'partName': 'Connection Test', 'result': 'Fail'})
        #print json.dumps(job_results, indent=2)
        return json.dumps(job_results)

    worker.send_job_status(job, 2, 10)
    
    #print "Transfering Data"
    if  worker.cruiseDataTransfer['transferType'] == "4": # SSH Server
        job_results['files'] = transfer_sshDestDir(worker, job)
        job_results['parts'].append({"partName": "Transfer Files", "result": "Pass"})
    else:
        #print "Error: Unknown Transfer Type"
        job_results['parts'].append({"partName": "Transfer Files", "result": "Fail"})
        #print "Stopping"
        return json.dumps(job_results)
    
    #print "Transfer Complete"
    worker.send_job_status(job, 9, 10)
    
    warehouseTransferLogDir = build_logfileDirPath(worker)
    #print warehouseTransferLogDir   

    if job_results['files']['new'] or job_results['files']['updated']:
    
        if os.path.isdir(warehouseTransferLogDir):
    
            logfileName = warehouseTransferLogDir + '/' + worker.cruiseDataTransfer['name'] + '_' + time.strftime("%Y%m%dT%H%M%SZ", worker.startTime) + '.log'
            #print logfileName

            logOutput = {'files':{'new':[], 'updated':[]}}
            logOutput['files']['new'] = job_results['files']['new']
            logOutput['files']['updated'] = job_results['files']['updated']
            
            #print json.dumps(logOutput);
            
            if writeLogFile(logfileName, worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername'], logOutput['files']):
                job_results['parts'].append({"partName": "Write logfile", "result": "Pass"})
            else:
                job_results['parts'].append({"partName": "Write logfile", "result": "Fail"})
                
        else:
            job_results['parts'].append({"partName": "Logfile directory", "result": "Fail"})

    worker.send_job_status(job, 10, 10)
    
    time.sleep(5)

    return json.dumps(job_results)

global ovdmWorker
ovdmWorker = OVDMGearmanWorker()

def sigquit_handler(_signo, _stack_frame):
    print "QUIT Signal Received"
    ovdmWorker.stopTransfer()
    
def sigint_handler(_signo, _stack_frame):
    print "INT Signal Received"
    ovdmWorker.quitWorker()
    
signal.signal(signal.SIGQUIT, sigquit_handler)
signal.signal(signal.SIGINT, sigint_handler)

ovdmWorker.set_client_id('runShipToShoreTransfer.py')
ovdmWorker.register_task("runShipToShoreTransfer", task_runShipToShoreTransfer)

ovdmWorker.work()
