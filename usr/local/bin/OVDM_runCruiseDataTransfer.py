# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_runCruiseDataTransfer.py
#
#  DESCRIPTION:  Gearman worker that handles the transfer of all cruise data from the
#                Shipboard Data Warehouse to a second location.
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
import tempfile
import gearman
import shutil
import json
import requests
import time
import fnmatch
import subprocess
import signal
from random import randint

def build_filelist(sourceDir, filters):

    #print 'DECODED Filters:', json.dumps(filters, indent=2)  

    returnFiles = {'include':[], 'exclude':[], 'new':[], 'updated':[]}
    for root, dirnames, filenames in os.walk(sourceDir):
        for filename in filenames:
            if not fnmatch.fnmatch(filename, filters['includeFilter']) and not fnmatch.fnmatch(filename, filters['ignoreFilter']):
                returnFiles['exclude'].append(os.path.join(root, filename))
        for filename in fnmatch.filter(filenames, filters['includeFilter']):
            if not fnmatch.fnmatch(filename, filters['excludeFilter']) and not fnmatch.fnmatch(filename, filters['ignoreFilter']):
                returnFiles['include'].append(os.path.join(root, filename))
            if fnmatch.fnmatch(filename, filters['excludeFilter']) and not fnmatch.fnmatch(filename, filters['ignoreFilter']):
                returnFiles['exclude'].append(os.path.join(root, filename))

    returnFiles['include'] = [filename.replace(sourceDir, '', 1) for filename in returnFiles['include']]
    returnFiles['exclude'] = [filename.replace(sourceDir, '', 1) for filename in returnFiles['exclude']]
    return returnFiles

def build_destDirectories(destDir, files):
    files = [filename.replace(filename, destDir + filename, 1) for filename in files]
    #print 'DECODED Files:', json.dumps(files, indent=2)

    for dirname in set(os.path.dirname(p) for p in files):
        if not os.path.isdir(dirname):
            #print "Creating Directory: " + dirname
            os.makedirs(dirname)

def get_cruiseDataTransfer(job, cruiseDataTransferID):
    dataObj = json.loads(job.data)
    # Set Error for current tranfer in DB via API
    
    url = dataObj['siteRoot'] + 'api/cruiseDataTransfers/getCruiseDataTransfer/' + cruiseDataTransferID
    r = requests.get(url)
    returnVal = json.loads(r.text)
    return returnVal[0]

def transfer_localDestDir(data, worker, job):

    #print "Transfer from Local Directory"
    filters = {'includeFilter': '*','excludeFilter': '','ignoreFilter': ''}
    
    sourceDir = data['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+data['cruiseID']
    destDir = data['cruiseDataTransfer']['destDir'].rstrip('/') + '/'

    my_string.rstrip('/')
    
    #print "Build file list"
    files = build_filelist(sourceDir, filters)
    
    #print "Build destination directories"
    build_destDirectories(destDir, files['include'])

    count = 1
    fileCount = len(files['include'])
    
    for filename in files['include']:
        proc = subprocess.Popen(['rsync', '-tri', sourceDir + filename, destDir + filename], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = proc.communicate()
        #print "OUT: " + out
        if err:
            print "ERR: " + err
        
        if out.startswith( '>f+++++++++' ):
            files['new'].append(filename)
        elif out.startswith( '>f.' ):
            files['updated'].append(filename)
        worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
        count += 1
        if worker.stop:
            print "Stopping"
            break
        #else:
        #    print "Next File"

    #print 'DECODED Files:', json.dumps(files, indent=2)
    return files


def transfer_smbDestDir(data, worker, job):

    #print 'DECODED Data:', json.dumps(data, indent=2)
    
    #print "Transfer from SMB Server"
    filters = {'includeFilter': '*','excludeFilter': '','ignoreFilter': ''}

    # Create temp directory
    #print "Create Temp Directory"
    tmpdir = tempfile.mkdtemp()
 
    # Create mountpoint
    #print "Create Mountpoint"
    mntPoint = tmpdir + '/mntpoint'
    os.mkdir(mntPoint, 0755)

    # Mount SMB Share
    #print "Mount SMB Share"
    subprocess.call(['sudo', 'mount', '-t', 'cifs', data['cruiseDataTransfer']['smbServer'], mntPoint, '-o', 'username='+data['cruiseDataTransfer']['smbUser']+',password='+data['cruiseDataTransfer']['smbPass']+',domain='+data['cruiseDataTransfer']['smbDomain']])

    sourceDir = data['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+data['cruiseID']
    destDir = mntPoint+data['cruiseDataTransfer']['destDir'].rstrip('/') + '/' + data['cruiseID']

    #print "Build file list"
    files = build_filelist(sourceDir, filters)
    
    #print "Build destination directories"
    build_destDirectories(destDir, files['include'])

    count = 1
    fileCount = len(files['include'])
    
    for filename in files['include']:
        proc = subprocess.Popen(['rsync', '-rlptDi', sourceDir + filename, destDir + filename], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = proc.communicate()
        #print "OUT: " + out
        if err:
            print "ERR: " + err
        if out.startswith( '>f+++++++++' ):
            files['new'].append(filename)
        elif out.startswith( '>f.' ):
            files['updated'].append(filename)
        worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
        count += 1
        if worker.stop:
            print "Stopping"
            break
        #else:
        #    print "Next File"
        
    #print "Unmount SMB Share"
    subprocess.call(['sudo', 'umount', mntPoint])
    
    #print "Cleanup"
    shutil.rmtree(tmpdir)

    #print 'DECODED Files:', json.dumps(files, indent=2)
    return files

def transfer_rsyncDestDir(data, worker, job):

#    print 'DECODED Data:', json.dumps(data, indent=2)
    
    #print "Transfer from Rsync Server"
    filters = {'includeFilter': '*','excludeFilter': '','ignoreFilter': ''}

    sourceDir = data['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+data['cruiseID']
    
    #print "Build file list"
    files = build_filelist(sourceDir, filters)
    
    createdDirs = []

    count = 1
    fileCount = len(files['include'])
    
    for filename in files['include']:
        print filename
        print data['cruiseDataTransfer']['destDir'] + '/' + data['cruiseID'] + os.path.dirname(filename)
        
        if os.path.dirname(filename) not in createdDirs:
            proc = subprocess.Popen(['sshpass', '-p', data['cruiseDataTransfer']['rsyncPass'], 'ssh', '-c', 'arcfour', data['cruiseDataTransfer']['rsyncUser'] + '@' + data['cruiseDataTransfer']['rsyncServer'], 'mkdir', '-p', data['cruiseDataTransfer']['destDir'] + '/' + data['cruiseID'] + os.path.dirname(filename)], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            out, err = proc.communicate()
            #print "OUT: " + out
            if err:
                print "ERR: " + err
            else:
                createdDirs.append(os.path.dirname(filename))
            #    os.chown(destDir + filename, pwd.getpwnam(data['shipboardDataWarehouse']['shipboardDataWarehouseUsername']).pw_uid, grp.getgrnam(data['shipboardDataWarehouse']['shipboardDataWarehouseUsername']).gr_gid)
        
        proc = subprocess.Popen(['sshpass', '-p', data['cruiseDataTransfer']['rsyncPass'], 'rsync', '-aiv', '-e', 'ssh -c arcfour', sourceDir + filename, data['cruiseDataTransfer']['rsyncUser'] + '@' + data['cruiseDataTransfer']['rsyncServer'] + ':' + data['cruiseDataTransfer']['destDir'] + '/' + data['cruiseID'] + filename], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = proc.communicate()
        #print "OUT: " + out
        if err:
            print "ERR: " + err
        #else:
        #    os.chown(destDir + filename, pwd.getpwnam(data['shipboardDataWarehouse']['shipboardDataWarehouseUsername']).pw_uid, grp.getgrnam(data['shipboardDataWarehouse']['shipboardDataWarehouseUsername']).gr_gid)
            
        if out.startswith( '<f+++++++++' ):
            files['new'].append(data['cruiseDataTransfer']['destDir'].rstrip('/') + filename)
        elif out.startswith( '<f.' ):
            files['updated'].append(data['cruiseDataTransfer']['destDir'].rstrip('/') + filename)
        worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
        count += 1
        if worker.stop:
            print "Stopping"
            break
        #else:
            #print "Next File"

    #print 'DECODED Files:', json.dumps(files, indent=2)
    return files


def setError_cruiseDataTransfer(job):
    dataObj = json.loads(job.data)

    # Set Error for current tranfer in DB via API
    
    url = dataObj['siteRoot'] + 'api/cruiseDataTransfers/setErrorCruiseDataTransfer/' + dataObj['cruiseDataTransfer']['cruiseDataTransferID']
    r = requests.get(url)
    
    url = dataObj['siteRoot'] + 'api/messages/newMessage'
    payload = {'message': 'Error in data transfer for ' + dataObj['cruiseDataTransfer']['name']}
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

def sigquit_handler(_signo, _stack_frame):
    print "Stopping"
    stop = True        
        
class CustomGearmanWorker(gearman.GearmanWorker):

    def __init__(self, host_list=None):
        super(CustomGearmanWorker, self).__init__(host_list=host_list)
        self.stop = False
        self.quit = False
        
    def on_job_execute(self, current_job):
        print "Job started: " + current_job.handle
#        dataObj = json.loads(current_job.data)
#        setRunning_cruiseDataTransfer(current_job)
        return super(CustomGearmanWorker, self).on_job_execute(current_job)

    def on_job_exception(self, current_job, exc_info):
        print "Job failed, CAN stop last gasp GEARMAN_COMMAND_WORK_FAIL"
        self.send_job_data(current_job, json.dumps([{"partName": "Unknown Part of Transfer", "result": "Fail"}]))
        setError_cruiseDataTransfer(current_job)
        print exc_info
        return super(CustomGearmanWorker, self).on_job_exception(current_job, exc_info)

    def on_job_complete(self, current_job, job_result):
        resultObj = json.loads(job_result)
        print "Job complete, CAN stop last gasp GEARMAN_COMMAND_WORK_COMPLETE"
        
        if resultObj['parts'][-1]['partName'] != "Transfer Enabled" and resultObj['parts'][-1]['partName'] != "Transfer In-Progress": # Final Verdict
            if resultObj['parts'][-1]['result'] == "Fail": # Final Verdict
                setError_cruiseDataTransfer(current_job)
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
    
    job_results = {'parts':[], 'files':[]}

    dataObj = json.loads(job.data)
    #print 'DECODED:', json.dumps(dataObj, indent=2)

    if dataObj['cruiseDataTransfer']['enable'] == "1" and dataObj['systemStatus'] == "On":
        #print "Transfer Enabled"
        job_results['parts'].append({"partName": "Transfer Enabled", "result": "Success"})
    else:
        #print "Transfer Disabled"
        #print "Stopping"
        job_results['parts'].append({"partName": "Transfer Enabled", "result": "Success"})
        return json.dumps(job_results)

    transfer = get_cruiseDataTransfer(job, dataObj['cruiseDataTransfer']['cruiseDataTransferID'])
    #print transfer
    
    if transfer['status'] == "1": #running
        #print "Transfer already in-progress"
        job_results['parts'].append({"partName": "Transfer In-Progress", "result": "Fail"})
        #print "Stopping"
        return json.dumps(job_results)
    else:
        #print "Transfer not already in-progress"
        job_results['parts'].append({"partName": "Transfer In-Progress", "result": "Success"})

    
    # Set transfer status to "Running"
    setRunning_cruiseDataTransfer(job)
    
    #print "Testing configuration"
    gearman_worker.send_job_status(job, 1, 10)

    # First test to see if the transfer can occur 
    gm_client = gearman.GearmanClient(['localhost:4730'])
    completed_job_request = gm_client.submit_job("testCruiseDataTransfer", job.data)
    resultsObj = json.loads(completed_job_request.result)
    #print 'DECODED Results:', json.dumps(resultsObj, indent=2)

    if resultsObj[-1]['result'] == "Success": # Final Verdict
        #print "Connection Test: Passed"
        job_results['parts'].append({'partName': 'Connection Test', 'result': 'Success'})
    else:
        #print "Connection Test: Failed"
        #print "Stopping"
        job_results['parts'].append({'partName': 'Connection Test', 'result': 'Fail'})
        #print json.dumps(job_results, indent=2)
        return json.dumps(job_results)

    gearman_worker.send_job_status(job, 2, 10)
    #print "Transfer Data"
    if dataObj['cruiseDataTransfer']['transferType'] == "1": # Local Directory
        job_results['files'] = transfer_localDestDir(dataObj, gearman_worker, job)
    elif  dataObj['cruiseDataTransfer']['transferType'] == "2": # Rsync Server
        job_results['files'] = transfer_rsyncDestDir(dataObj, gearman_worker, job)
    elif  dataObj['cruiseDataTransfer']['transferType'] == "3": # SMB Server
        job_results['files'] = transfer_smbDestDir(dataObj, gearman_worker, job)

    #print "Transfer Complete"
    gearman_worker.send_job_status(job, 9, 10)

    #print "Send transfer log" 
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

new_worker.set_client_id('runCruiseDataTransfer.py')
new_worker.register_task("runCruiseDataTransfer", task_callback)

new_worker.work()