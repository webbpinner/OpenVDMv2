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
#     REVISION:  2016-02-08
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
import requests
import datetime
import time
import fnmatch
import subprocess
import signal
import pwd
import grp
from random import randint

def get_collectionSystemTransfer(job, collectionSystemID):
    dataObj = json.loads(job.data)

    # Set Error for current tranfer in DB via API
    url = dataObj['siteRoot'] + 'api/collectionSystemTransfers/getCollectionSystemTransfer/' + collectionSystemID
    r = requests.get(url)
    returnObj = json.loads(r.text)
    return json.loads(r.text)[0]

def get_extraDirectory(job, extraDirectoryID):
    dataObj = json.loads(job.data)

    # Set Error for current tranfer in DB via API
    
    url = dataObj['siteRoot'] + 'api/extraDirectories/getExtraDirectory/' + extraDirectoryID
    r = requests.get(url)
    return json.loads(r.text)[0]

def get_shipToShoreTransfers(job):
    dataObj = json.loads(job.data)

    # Set Error for current tranfer in DB via API
    
    url = dataObj['siteRoot'] + 'api/shipToShoreTransfers/getShipToShoreTransfers'
    r = requests.get(url)
    return json.loads(r.text)

def get_requiredShipToShoreTransfers(job):
    dataObj = json.loads(job.data)

    # Set Error for current tranfer in DB via API
    
    url = dataObj['siteRoot'] + 'api/shipToShoreTransfers/getRequiredShipToShoreTransfers'
    r = requests.get(url)
    return json.loads(r.text)

def get_cruiseDataTransfer(job, cruiseDataTransferID):
    dataObj = json.loads(job.data)
    # Set Error for current tranfer in DB via API
    
    url = dataObj['siteRoot'] + 'api/cruiseDataTransfers/getCruiseDataTransfer/' + cruiseDataTransferID
    r = requests.get(url)
    returnVal = json.loads(r.text)
    return returnVal[0]

def get_shipToShoreBWLimit(job):
    dataObj = json.loads(job.data)

    # Set Error for current tranfer in DB via API
    
    url = dataObj['siteRoot'] + 'api/warehouse/getShipToShoreBWLimit'
    r = requests.get(url)
    returnObj = json.loads(r.text)
    return returnObj['shipToShoreBWLimit']

def get_shipToShoreBWLimitStatus(job):
    dataObj = json.loads(job.data)

    # Set Error for current tranfer in DB via API
    
    url = dataObj['siteRoot'] + 'api/warehouse/getShipToShoreBWLimitStatus'
    r = requests.get(url)
    returnObj = json.loads(r.text)
    if returnObj['shipToShoreBWLimitStatus'] == "On":
        return True

    return False

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


def build_logfileDirPath(warehouseBaseDir, siteRoot):

    url = siteRoot + 'api/extraDirectories/getRequiredExtraDirectories'
    r = requests.get(url)
    transferLogDir = ''
    for directory in r.json():
        if directory['name'] == 'Transfer Logs':
            transferLogDir = warehouseBaseDir + '/' + directory['destDir']
            break
    
    return transferLogDir

def build_filters(raw_filters, data):
    
    returnFilters = raw_filters
    #print json.dumps(raw_filters, indent=2)
    
    returnFilters['includeFilter'] = [returnFilter.replace('{cruiseID}', data['cruiseID']) for returnFilter in returnFilters['includeFilter']]
#    returnFilters['includeFilter'] = returnFilters['includeFilter'].replace('{cruiseID}', data['cruiseID'])
#    returnFilters['excludeFilter'] = returnFilters['excludeFilter'].replace('{cruiseID}', data['cruiseID'])
#    returnFilters['ignoreFilter'] =  returnFilters['ignoreFilter'].replace('{cruiseID}', data['cruiseID'])
    
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
            
def transfer_sshDestDir(data, worker, job):

#    print 'DECODED Data:', json.dumps(data, indent=2)
    
    #print "Transfer from Data Warehouse"
    
    #print "Building filters"
    rawFilters = {'includeFilter':[]}
    shipToShoreTransfers = get_shipToShoreTransfers(job)
    shipToShoreTransfers = shipToShoreTransfers + get_requiredShipToShoreTransfers(job)
    #print json.dumps(shipToShoreTransfers, indent=2)
    
    for x in range(1, 6):
        #print "Processing priority " + str(x) + " transfers"
        for shipToShoreTransfer in shipToShoreTransfers:
            if shipToShoreTransfer['priority'] == str(x):
                if shipToShoreTransfer['enable'] == '1':
                    #print json.dumps(shipToShoreTransfer, indent=2)
                    if not shipToShoreTransfer['collectionSystem'] == "0":
                        #print "Retrieving Collection System information"
                        collectionSystem = get_collectionSystemTransfer(job, shipToShoreTransfer['collectionSystem'])
                        #print json.dumps(collectionSystem, indent=2)
                        shipToShoreFilters = shipToShoreTransfer['includeFilter'].split(' ')
                        shipToShoreFilters = ['*/' + data['cruiseID'] + '/' + collectionSystem['destDir'] + '/' + shipToShoreFilter for shipToShoreFilter in shipToShoreFilters]
                        rawFilters['includeFilter'] = rawFilters['includeFilter'] + shipToShoreFilters
                    elif not shipToShoreTransfer['extraDirectory'] == "0":
                        #print "Retrieving Extra Directory information"
                        extraDirectory = get_extraDirectory(job, shipToShoreTransfer['extraDirectory'])
                        shipToShoreFilters = shipToShoreTransfer['includeFilter'].split(' ')
                        shipToShoreFilters = ['*/' + data['cruiseID'] + '/' + extraDirectory['destDir'] + '/' + shipToShoreFilter for shipToShoreFilter in shipToShoreFilters]
                        #print json.dumps(extraDirectory, indent=2)
                        rawFilters['includeFilter'] = rawFilters['includeFilter'] + shipToShoreFilters
                    else:
                        shipToShoreFilters = shipToShoreTransfer['includeFilter'].split(' ')
                        shipToShoreFilters = ['*/' + data['cruiseID'] + '/' + shipToShoreFilter for shipToShoreFilter in shipToShoreFilters]
                        rawFilters['includeFilter'] = rawFilters['includeFilter'] + shipToShoreFilters

    #print "Raw Filters:"
    #print json.dumps(rawFilters, indent=2)
    
    filters = build_filters(rawFilters, data)
    #print "Proc Filters:"
    #print json.dumps(filters, indent=2)

    sourceDir = data['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir'] + '/' + data['cruiseID']
    
    bwLimit = get_shipToShoreBWLimit(job)
    bwLimitStatus = get_shipToShoreBWLimitStatus(job)
    bwLimitStr = '--bwlimit=10000'
    
    if bwLimitStatus and not bwLimit == "0":
        #print "Setting bandwidth limit"
        bwLimitStr = '--bwlimit=' + bwLimit
            
    #print "Build file list"
    files = build_filelist(sourceDir, filters)
    files['include'] = [ '/' + data['cruiseID'] + filepath for filepath in files['include']]
    
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
        #print '\n'.join([data['cruiseID'] + str(x) for x in files['include']])
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
    
    
    command = ['sshpass', '-p', data['cruiseDataTransfer']['sshPass'], 'rsync', '-ti', '--partial', bwLimitStr, '-e', 'ssh -c arcfour', '--files-from=' + rsyncFileListPath, data['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir'], data['cruiseDataTransfer']['sshUser'] + '@' + data['cruiseDataTransfer']['sshServer'] + ':' + data['cruiseDataTransfer']['destDir']]
    #print command
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #print(line) # yield line
        if line.startswith( '<f+++++++++' ):
            files['new'].append(line.split(' ')[1])
        elif line.startswith( '<f.' ):
            files['updated'].append(line.split(' ')[1])
        worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
        count += 1
        
        elapseTime = datetime.datetime.utcnow() - worker.startTime
        #print elapseTime.seconds
        if elapseTime.seconds > 3480: #58 minutes
            worker.stopTransfer()
            
        if worker.stop:
            print "Stopping"
            break
    
    # Cleanup
    shutil.rmtree(tmpdir)
        
    return files


def setError_cruiseDataTransfer(job, message=None):
    dataObj = json.loads(job.data)

    # Set Error for current tranfer in DB via API
    
    url = dataObj['siteRoot'] + 'api/cruiseDataTransfers/setErrorCruiseDataTransfer/' + dataObj['cruiseDataTransfer']['cruiseDataTransferID']
    r = requests.get(url)
    
    url = dataObj['siteRoot'] + 'api/messages/newMessage'
    payload = {'message': dataObj['cruiseDataTransfer']['name'] + ' data transfer'}
    if message:
        payload['message'] += ': ' + message
    r = requests.post(url, data=payload)

def setRunning_cruiseDataTransfer(job):
    dataObj = json.loads(job.data)
    
    jobPID = os.getpid();

    # Set Error for current tranfer in DB via API
    url = dataObj['siteRoot'] + 'api/cruiseDataTransfers/setRunningCruiseDataTransfer/' + dataObj['cruiseDataTransfer']['cruiseDataTransferID']
    payload = {'jobPid': jobPID}
    r = requests.post(url, data=payload)

    # Add Job to DB via API
    url = dataObj['siteRoot'] + 'api/gearman/newJob/' + job.handle
    payload = {'jobName': 'Run Transfer for ' + dataObj['cruiseDataTransfer']['name'],'jobPid': jobPID}
    r = requests.post(url, data=payload)

def setIdle_cruiseDataTransfer(job):
    dataObj = json.loads(job.data)

    # Set Error for current tranfer in DB via API
    url = dataObj['siteRoot'] + 'api/cruiseDataTransfers/setIdleCruiseDataTransfer/' + dataObj['cruiseDataTransfer']['cruiseDataTransferID']
    r = requests.get(url)

def clearError_cruiseDataTransfer(job):
    dataObj = json.loads(job.data)
    if dataObj['cruiseDataTransfer']['status'] == "3":
        # Clear Error for current tranfer in DB via API
        url = dataObj['siteRoot'] + 'api/cruiseDataTransfers/setIdleCruiseDataTransfer/' + dataObj['cruiseDataTransfer']['cruiseDataTransferID']
        r = requests.get(url)

#def sigquit_handler(_signo, _stack_frame):
#    print "Stopping"
#    stop = True        
        
class CustomGearmanWorker(gearman.GearmanWorker):

    def __init__(self, host_list=None):
        super(CustomGearmanWorker, self).__init__(host_list=host_list)
        self.startTime = datetime.datetime.utcnow()
        self.stop = False
        self.quit = False
        
    def on_job_execute(self, current_job):
        print "Job started: " + current_job.handle
        self.startTime = datetime.datetime.utcnow()
        #print self.startTime
        return super(CustomGearmanWorker, self).on_job_execute(current_job)

    def on_job_exception(self, current_job, exc_info):
        print "Job failed, CAN stop last gasp GEARMAN_COMMAND_WORK_FAIL"
        self.send_job_data(current_job, json.dumps([{"partName": "Unknown Part of Transfer", "result": "Fail"}]))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        setError_cruiseDataTransfer(current_job, "Unknown Part: " + str(exc_tb.tb_lineno))
        print(exc_type, fname, exc_tb.tb_lineno)
        return super(CustomGearmanWorker, self).on_job_exception(current_job, exc_info)

    def on_job_complete(self, current_job, job_result):
        resultObj = json.loads(job_result)
        dataObj = json.loads(current_job.data)
        print "Job complete, CAN stop last gasp GEARMAN_COMMAND_WORK_COMPLETE"
        
        if resultObj['parts'][-1]['partName'] != "Transfer Enabled" and resultObj['parts'][-1]['partName'] != "Transfer In-Progress": # Final Verdict
            if resultObj['parts'][-1]['result'] == "Fail": # Final Verdict
                setError_cruiseDataTransfer(current_job, resultObj['parts'][-1]['partName'])
                print "but something prevented the transfer from successfully completing..."
            else:
                setIdle_cruiseDataTransfer(current_job)

        return super(CustomGearmanWorker, self).send_job_complete(current_job, job_result)

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

def task_callback(gearman_worker, job):

    time.sleep(randint(0,5))

    job_results = {'parts':[], 'files':[], 'startDate':gearman_worker.startTime.strftime("%Y%m%dT%H%M%SZ")}

    dataObj = json.loads(job.data)
    #print 'DECODED:', json.dumps(dataObj, indent=2)

    if dataObj['cruiseDataTransfer']['enable'] == "1" and dataObj['systemStatus'] == "On":
        #print "Transfer Enabled"
        job_results['parts'].append({"partName": "Transfer Enabled", "result": "Pass"})
    else:
        #print "Transfer Disabled"
        #print "Stopping"
        job_results['parts'].append({"partName": "Transfer Enabled", "result": "Pass"})
        return json.dumps(job_results)
    
    transfer = get_cruiseDataTransfer(job, dataObj['cruiseDataTransfer']['cruiseDataTransferID'])
    #print json.dumps(transfer)

    if transfer['status'] == "1": #running
        print "Transfer already in-progress... Stopping"
        job_results['parts'].append({"partName": "Transfer In-Progress", "result": "Pass"})
        return json.dumps(job_results)
    else:
        #print "Transfer not already in-progress"
        job_results['parts'].append({"partName": "Transfer In-Progress", "result": "Pass"})
    
    #print "Testing Connection"
    # Set transfer status to "Running"
    setRunning_cruiseDataTransfer(job)
    
    #print "Testing configuration"
    gearman_worker.send_job_status(job, 1, 10)

    # First test to see if the transfer can occur 
    gm_client = gearman.GearmanClient(['localhost:4730'])
    completed_job_request = gm_client.submit_job("testCruiseDataTransfer", job.data)
    resultsObj = json.loads(completed_job_request.result)
    #print 'DECODED Results:', json.dumps(resultsObj, indent=2)

    if resultsObj[-1]['result'] == "Pass": # Final Verdict
        #print "Connection Test: Passed"
        job_results['parts'].append({'partName': 'Connection Test', 'result': 'Pass'})
    else:
        #print "Connection Test: Failed... Stopping"
        job_results['parts'].append({'partName': 'Connection Test', 'result': 'Fail'})
        return json.dumps(job_results)

    gearman_worker.send_job_status(job, 2, 10)
    print "Transfering Data"
    if  dataObj['cruiseDataTransfer']['transferType'] == "4": # SSH Server
        job_results['files'] = transfer_sshDestDir(dataObj, gearman_worker, job)
        job_results['parts'].append({"partName": "Transfer Files", "result": "Pass"})
    else:
        print "Error: Unknown Transfer Type"
        job_results['parts'].append({"partName": "Transfer Files", "result": "Fail"})
        print "Stopping"
        return json.dumps(job_results)

    
    print "Transfer Complete"
    gearman_worker.send_job_status(job, 9, 10)

    if job_results['files']['new'] or job_results['files']['updated']:
    
        print "Create transfer log"
        warehouseTransferLogDir = build_logfileDirPath(dataObj['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir'] + '/' + dataObj['cruiseID'] , dataObj['siteRoot'])
        #print warehouseTransferLogDir   
    
        if os.path.isdir(warehouseTransferLogDir):
    
            logfileName = warehouseTransferLogDir + '/' + dataObj['cruiseDataTransfer']['name'] + '_' + job_results['startDate'] + '.log'
            #print logfileName
    
            logOutput = {'files':{'new':[], 'updated':[]}}
            logOutput['files']['new'] = job_results['files']['new']
            logOutput['files']['updated'] = job_results['files']['updated']
            if writeLogFile(logfileName, dataObj['shipboardDataWarehouse']['shipboardDataWarehouseUsername'], logOutput['files']):
                job_results['parts'].append({"partName": "Write logfile", "result": "Pass"})
            else:
                job_results['parts'].append({"partName": "Write logfile", "result": "Fail"})
        else:
            job_results['parts'].append({"partName": "Logfile directory", "result": "Fail"})

    gearman_worker.send_job_status(job, 10, 10)
    
    time.sleep(5)

    return json.dumps(job_results)

global new_worker
new_worker = CustomGearmanWorker(['localhost:4730'])

def sigquit_handler(_signo, _stack_frame):
    print "QUIT Signal Received"
    new_worker.stopTransfer()
    
def sigint_handler(_signo, _stack_frame):
    print "INT Signal Received"
    new_worker.quitWorker()
    
signal.signal(signal.SIGQUIT, sigquit_handler)
signal.signal(signal.SIGINT, sigint_handler)

new_worker.set_client_id('runShipToShoreTransfer.py')
new_worker.register_task("runShipToShoreTransfer", task_callback)

new_worker.work()
