# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_testCruiseDataTransfer.py
#
#  DESCRIPTION:  Gearman worker that handles testing cruise data transfer
#                configurations
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
import subprocess

from subprocess import call

def test_sourceDir(data):
    sourceDir = data['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+data['cruiseID']
    if os.path.isdir(sourceDir):
        return [{"testName": "Cruise Data Directory", "result": "Pass"}]
    else:
        return [{"testName": "Cruise Data Directory", "result": "Fail"}]

def test_localDestDir(data):

    returnVal = []
    sourceDir = data['cruiseDataTransfer']['destDir']
    
    if os.path.isdir(sourceDir):
        returnVal.append({"testName": "Destination Directory", "result": "Pass"})
        try:
            filepath = sourceDir + '/' + 'writeTest.txt'
            filehandle = open( filepath, 'w' )
            filehandle.close()
            os.remove(filepath)
            returnVal.append({"testName": "Write Test", "result": "Pass"})
        except IOError:
            returnVal.append({"testName": "Write Test", "result": "Fail"})
    else:
        returnVal.append({"testName": "Destination Directory", "result": "Fail"})
        returnVal.append({"testName": "Write Test", "result": "Fail"})

    return returnVal

def test_smbDestDir(data):
    returnVal = []

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
 
    # Create mountpoint
    mntPoint = tmpdir + '/mntpoint'
    os.mkdir(mntPoint, 0755)

    # Mount SMB Share
    if call(['sudo', 'mount', '-t', 'cifs', data['cruiseDataTransfer']['smbServer'], mntPoint, '-o', 'username='+data['cruiseDataTransfer']['smbUser']+',password='+data['cruiseDataTransfer']['smbPass']+',domain='+data['cruiseDataTransfer']['smbDomain']]) == 0:
        returnVal.append({"testName": "SMB Mount", "result": "Pass"})

        # If mount is successful, test source directory
        sourceDir = mntPoint+data['cruiseDataTransfer']['destDir']
        if os.path.isdir(mntPoint+data['cruiseDataTransfer']['destDir']):
            returnVal.append({"testName": "Destination Directory", "result": "Pass"})
            try:
                filepath = sourceDir + '/' + 'writeTest.txt'
                filehandle = open(filepath, 'w')
                filehandle.close()
                os.remove(filepath)
                returnVal.append({"testName": "Write Test", "result": "Pass"})
            except Exception as e:
                print e
                print "{}".format(e)
                print "IOError"
                returnVal.append({"testName": "Write Test", "result": "Fail"})
        else:
            returnVal.append({"testName": "Destination Directory", "result": "Fail"})
            returnVal.append({"testName": "Write Test", "result": "Fail"})

        # Unmount SMB Share
        call(['sudo', 'umount', mntPoint])
    else:
        returnVal.append({"testName": "SMB Mount", "result": "Fail"})
        returnVal.append({"testName": "Destination Directory", "result": "Fail"})
        returnVal.append({"testName": "Write Test", "result": "Fail"})

    # Cleanup
    shutil.rmtree(tmpdir)

    return returnVal

def test_rsyncDestDir(data):

    returnVal = []
    
    # Connect to RSYNC Server
    if call(['sshpass', '-p', data['cruiseDataTransfer']['rsyncPass'], 'ssh', data['cruiseDataTransfer']['rsyncServer'], '-l', data['cruiseDataTransfer']['rsyncUser'], '-o', 'StrictHostKeyChecking=no', 'ls', '> /dev/null']) == 0:
        returnVal.append({"testName": "Rsync Connection", "result": "Pass"})

        #sshpass -p Tethys337813 ssh 192.168.1.4 -l survey -o StrictHostKeyChecking=no ls /mnt/vault/FTPRoot/CruiseData
        if call(['sshpass', '-p', data['cruiseDataTransfer']['rsyncPass'], 'ssh', data['cruiseDataTransfer']['rsyncServer'], '-l', data['cruiseDataTransfer']['rsyncUser'], '-o', 'StrictHostKeyChecking=no', 'ls', data['cruiseDataTransfer']['destDir'], '> /dev/null']) == 0:
            returnVal.append({"testName": "Destination Directory", "result": "Pass"})
            if call(['sshpass', '-p', data['cruiseDataTransfer']['rsyncPass'], 'ssh', data['cruiseDataTransfer']['rsyncServer'], '-l', data['cruiseDataTransfer']['rsyncUser'], '-o', 'StrictHostKeyChecking=no', 'touch ' + data['cruiseDataTransfer']['destDir'] + '/writeTest.txt', '> /dev/null']) == 0:
                returnVal.append({"testName": "Write Test", "result": "Pass"})
                call(['sshpass', '-p', data['cruiseDataTransfer']['rsyncPass'], 'ssh', data['cruiseDataTransfer']['rsyncServer'], '-l', data['cruiseDataTransfer']['rsyncUser'], '-o', 'StrictHostKeyChecking=no', 'rm ' + data['cruiseDataTransfer']['destDir'] + '/writeTest.txt', '> /dev/null'])
            else:
                returnVal.append({"testName": "Write Test", "result": "Fail"})

        else:
            returnVal.append({"testName": "Destination Directory", "result": "Fail"})
            returnVal.append({"testName": "Write Test", "result": "Fail"})

    else:
        returnVal.append({"testName": "Rsync Connection", "result": "Fail"})
        returnVal.append({"testName": "Destination Directory", "result": "Fail"})
        returnVal.append({"testName": "Write Test", "result": "Fail"})

    #print json.dumps(returnVal, indent=2)
    return returnVal

def setError_cruiseDataTransfer(job):
    dataObj = json.loads(job.data)

    # Set Error for current tranfer in DB via API
    url = dataObj['siteRoot'] + 'api/cruiseDataTransfers/setErrorCruiseDataTransfer/' + dataObj['cruiseDataTransfer']['cruiseDataTransferID']
    r = requests.get(url)
    
def clearError_cruiseDataTransfer(job):
    dataObj = json.loads(job.data)
    if dataObj['cruiseDataTransfer']['status'] == "3":
        # Clear Error for current tranfer in DB via API
        url = dataObj['siteRoot'] + 'api/cruiseDataTransfers/setIdleCruiseDataTransfer/' + dataObj['cruiseDataTransfer']['cruiseDataTransferID']
        r = requests.get(url)

class CustomGearmanWorker(gearman.GearmanWorker):

    def on_job_execute(self, current_job):
        print "Job started: " + current_job.handle
        dataObj = json.loads(current_job.data)

        # Add Job to DB via API
        url = dataObj['siteRoot'] + 'api/gearman/newJob/' + current_job.handle
        payload = {'jobName': 'Connection Test for ' + dataObj['cruiseDataTransfer']['name'],'jobPid': os.getpid()}
        r = requests.post(url, data=payload)

        return super(CustomGearmanWorker, self).on_job_execute(current_job)

    def on_job_exception(self, current_job, exc_info):
        print "Job failed, CAN stop last gasp GEARMAN_COMMAND_WORK_FAIL"
        self.send_job_data(current_job, json.dumps([{"testName": "Unknown Testing Process", "result": "Fail"},{"testName": "Final Verdict", "result": "Fail"}]))
        setError_cruiseDataTransfer(current_job)
        print exc_info
        return super(CustomGearmanWorker, self).on_job_exception(current_job, exc_info)

    def on_job_complete(self, current_job, job_result):
        print "Job complete, CAN stop last gasp GEARMAN_COMMAND_WORK_COMPLETE"
        dataObj = json.loads(current_job.data)
        return super(CustomGearmanWorker, self).send_job_complete(current_job, job_result)

    def after_poll(self, any_activity):
        # Return True if you want to continue polling, replaces callback_fxn
        return True

def task_callback(gearman_worker, job):
    gearman_worker.send_job_status(job, 1, 4)
    dataObj = json.loads(job.data)
#    print 'DECODED:', json.dumps(dataObj, indent=2)

    job_results = []
    
#    print "Test Source Directory"
    job_results += test_sourceDir(dataObj)
    gearman_worker.send_job_status(job, 2, 4)

#    print "Test Destination Directory"
    if dataObj['cruiseDataTransfer']['transferType'] == "1": # Local Directory
        job_results += test_localDestDir(dataObj)
    elif  dataObj['cruiseDataTransfer']['transferType'] == "2": # Rsync Server
        job_results += test_rsyncDestDir(dataObj)
    elif  dataObj['cruiseDataTransfer']['transferType'] == "3": # SMB Server
        job_results += test_smbDestDir(dataObj)
        
    #print json.dumps(job_results)
    
    gearman_worker.send_job_status(job, 3, 4)

    verdict = "Pass"
    for test in job_results:
        if test['result'] == "Fail":
            verdict = "Fail"
            setError_cruiseDataTransfer(job)

    if verdict == "Pass":
        clearError_cruiseDataTransfer(job)

    job_results.append({"testName": "Final Verdict", "result": verdict})
    gearman_worker.send_job_status(job, 4, 4)

    return json.dumps(job_results)

new_worker = CustomGearmanWorker(['localhost:4730'])
new_worker.set_client_id('testCruiseDataTransfer.py')
new_worker.register_task("testCruiseDataTransfer", task_callback)
new_worker.work()