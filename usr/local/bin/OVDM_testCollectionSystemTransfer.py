# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_testCollectionSystemTransfer.py
#
#  DESCRIPTION:  Gearman worker that handles testing collection system transfer
#                configurations
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.0
#      CREATED:  2015-01-01
#     REVISION:  2015-07-18
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

from subprocess import call

def build_destDir(raw_destDir, data):
    
    #print raw_destDir
    
    returnDestDir = raw_destDir.replace('{cruiseID}', data['cruiseID'])

    return returnDestDir

def build_sourceDir(raw_sourceDir, data):
    
    #print raw_sourceDir
    
    returnSourceDir = raw_sourceDir.replace('{cruiseID}', data['cruiseID'])

    return returnSourceDir

def test_localSourceDir(data):
    if os.path.isdir(data['collectionSystemTransfer']['sourceDir']):
        return [{"testName": "Source Directory", "result": "Pass"}]
    else:
        return [{"testName": "Source Directory", "result": "Fail"}]

def test_smbSourceDir(data):
    returnVal = []

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
 
    # Create mountpoint
    mntPoint = tmpdir + '/mntpoint'
    os.mkdir(mntPoint, 0755)

    # Mount SMB Share
    if data['collectionSystemTransfer']['smbUser'] == 'guest':
        retVal = call(['sudo', 'mount', '-t', 'cifs', data['collectionSystemTransfer']['smbServer'], mntPoint, '-o', 'ro'+',domain='+data['collectionSystemTransfer']['smbDomain']])
    else:
        retVal = call(['sudo', 'mount', '-t', 'cifs', data['collectionSystemTransfer']['smbServer'], mntPoint, '-o', 'ro'+',username='+data['collectionSystemTransfer']['smbUser']+',password='+data['collectionSystemTransfer']['smbPass']+',domain='+data['collectionSystemTransfer']['smbDomain']])
    
    if retVal == 0:
        #sudo mount -t cifs $collectionSystemTransfer->{'smbServer'} $tempMountPoint -o username=$collectionSystemTransfer->{'smbUser'},password=$collectionSystemTransfer->{'smbPass'},domain='+data['collectionSystemTransfer']['smbDomain'] 2> /dev/null
        returnVal.append({"testName": "SMB Mount", "result": "Pass"})

        # If mount is successful, test source directory
        sourceDir = mntPoint+data['collectionSystemTransfer']['sourceDir']
        if os.path.isdir(mntPoint+data['collectionSystemTransfer']['sourceDir']):
            returnVal.append({"testName": "Source Directory", "result": "Pass"})
        else:
            returnVal.append({"testName": "Source Directory", "result": "Fail"})

        # Unmount SMB Share
        call(['sudo', 'umount', mntPoint])
    else:
        returnVal.append({"testName": "SMB Mount", "result": "Fail"})
        returnVal.append({"testName": "Source Directory", "result": "Fail"})

    # Cleanup
    shutil.rmtree(tmpdir)

    return returnVal

def test_rsyncSourceDir(data):
    
    returnVal = []

    # Connect to RSYNC Server
    if data['collectionSystemTransfer']['rsyncUseSSH'] == '0':
        # Create temp directory
        tmpdir = tempfile.mkdtemp()
        rsyncPasswordFilePath = tmpdir + '/' + 'passwordFile'
        
        try:
            #print "Open Transfer Log Summary file"
            rsyncPasswordFile = open(rsyncPasswordFilePath, 'w')

            #print "Saving Transfer Log Summary file"
            if data['collectionSystemTransfer']['rsyncUser'] != 'anonymous':
                rsyncPasswordFile.write(data['collectionSystemTransfer']['rsyncPass'])
            else:
                rsyncPasswordFile.write('noPasswordNeeded')                
            
        except IOError:
            print "Error Saving temporary rsync password file"
            returnVal.append({"testName": "Writing temporary rsync password file", "result": "Fail"})
            rsyncPasswordFile.close()
            
            # Cleanup
            shutil.rmtree(tmpdir)
            
            return returnVal    

        finally:
            #print "Closing Transfer Log Summary file"
            rsyncPasswordFile.close()
            os.chmod(rsyncPasswordFilePath, 0600)
            #returnVal.append({"testName": "Writing temporary rsync password file", "result": "Pass"})
        
    # /usr/bin/rsync -ratlz --rsh="/usr/bin/sshpass -p password ssh -o StrictHostKeyChecking=no -l username" src_path  dest_path
    if data['collectionSystemTransfer']['rsyncUseSSH'] == '0':
        if call(['rsync', '--no-motd', '--password-file=' + rsyncPasswordFilePath, 'rsync://' + data['collectionSystemTransfer']['rsyncUser'] + '@' + data['collectionSystemTransfer']['rsyncServer'], '> /dev/null']) == 0:
            returnVal.append({"testName": "Rsync Connection", "result": "Pass"})

            if call(['rsync', '--no-motd', '--password-file=' + rsyncPasswordFilePath, 'rsync://' + data['collectionSystemTransfer']['rsyncUser'] + '@' + data['collectionSystemTransfer']['rsyncServer'] + data['collectionSystemTransfer']['sourceDir'], '> /dev/null']) == 0:
                returnVal.append({"testName": "Source Directory", "result": "Pass"})
            else:
                returnVal.append({"testName": "Source Directory", "result": "Fail"})
        else:
            returnVal.append({"testName": "Rsync Connection", "result": "Fail"})
            returnVal.append({"testName": "Source Directory", "result": "Fail"})

        # Cleanup
            shutil.rmtree(tmpdir)

    else:
        # /usr/bin/rsync -ratlz --rsh="/usr/bin/sshpass -p password ssh -o StrictHostKeyChecking=no -l username" src_path  dest_path
        if call(['sshpass', '-p', data['collectionSystemTransfer']['rsyncPass'], 'ssh', data['collectionSystemTransfer']['rsyncServer'], '-l', data['collectionSystemTransfer']['rsyncUser'], '-o', 'StrictHostKeyChecking=no', 'ls', '> /dev/null']) == 0:
            returnVal.append({"testName": "Rsync Connection", "result": "Pass"})

            if call(['sshpass', '-p', data['collectionSystemTransfer']['rsyncPass'], 'ssh', data['collectionSystemTransfer']['rsyncServer'], '-l', data['collectionSystemTransfer']['rsyncUser'], '-o', 'StrictHostKeyChecking=no', 'ls', data['collectionSystemTransfer']['sourceDir'], '> /dev/null']) == 0:
                returnVal.append({"testName": "Source Directory", "result": "Pass"})
            else:
                returnVal.append({"testName": "Source Directory", "result": "Fail"})
        else:
            returnVal.append({"testName": "Rsync Connection", "result": "Fail"})
            returnVal.append({"testName": "Source Directory", "result": "Fail"})

        
    #print json.dumps(returnVal, indent=2)
    return returnVal

def test_destDir(data):
    destDir = data['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+data['cruiseID']+'/'+data['collectionSystemTransfer']['destDir']
        
    if os.path.isdir(destDir):
        return [{"testName": "Destination Directory", "result": "Pass"}]
    else:
        return [{"testName": "Destination Directory", "result": "Fail"}]
    
def setError_collectionSystemTransfer(job):
    dataObj = json.loads(job.data)

    if 'collectionSystemTransferID' in dataObj['collectionSystemTransfer']: 
        # Set Error for current tranfer in DB via API
        url = dataObj['siteRoot'] + 'api/collectionSystemTransfers/setErrorCollectionSystemTransfer/' + dataObj['collectionSystemTransfer']['collectionSystemTransferID']
        r = requests.get(url)

def clearError_collectionSystemTransfer(job):
    dataObj = json.loads(job.data)
    if dataObj['collectionSystemTransfer']['status'] == "3":
        if 'collectionSystemTransferID' in dataObj['collectionSystemTransfer']:
            # Clear Error for current tranfer in DB via API
            url = dataObj['siteRoot'] + 'api/collectionSystemTransfers/setIdleCollectionSystemTransfer/' + dataObj['collectionSystemTransfer']['collectionSystemTransferID']
            r = requests.get(url)

class CustomGearmanWorker(gearman.GearmanWorker):

    def on_job_execute(self, current_job):
        print "Job started: " + current_job.handle
        dataObj = json.loads(current_job.data)

        # Add Job to DB via API
        url = dataObj['siteRoot'] + 'api/gearman/newJob/' + current_job.handle
        payload = {'jobName': 'Connection Test for ' + dataObj['collectionSystemTransfer']['name'],'jobPid': os.getpid()}
        r = requests.post(url, data=payload)

        return super(CustomGearmanWorker, self).on_job_execute(current_job)

    def on_job_exception(self, current_job, exc_info):
        print "Job failed, CAN stop last gasp GEARMAN_COMMAND_WORK_FAIL"
        self.send_job_data(current_job, json.dumps([{"testName": "Unknown Testing Process", "result": "Fail"},{"testName": "Final Verdict", "result": "Fail"}]))
        setError_collectionSystemTransfer(current_job)
        print exc_info
        return super(CustomGearmanWorker, self).on_job_exception(current_job, exc_info)

    def on_job_complete(self, current_job, job_result):
        print "Job complete, CAN stop last gasp GEARMAN_COMMAND_WORK_COMPLETE"
        print json.dumps(job_result)
        dataObj = json.loads(current_job.data)
        return super(CustomGearmanWorker, self).send_job_complete(current_job, job_result)

    def after_poll(self, any_activity):
        # Return True if you want to continue polling, replaces callback_fxn
        return True

def task_callback(gearman_worker, job):
    gearman_worker.send_job_status(job, 1, 4)
    dataObj = json.loads(job.data)
    dataObj['collectionSystemTransfer']['destDir'] = build_destDir(dataObj['collectionSystemTransfer']['destDir'],dataObj)
    dataObj['collectionSystemTransfer']['sourceDir'] = build_sourceDir(dataObj['collectionSystemTransfer']['sourceDir'],dataObj)
#    print 'DECODED:', json.dumps(dataObj, indent=2)

    job_results = []
    
#    print "Test Source Directory"
    if dataObj['collectionSystemTransfer']['transferType'] == "1": # Local Directory
        job_results += test_localSourceDir(dataObj)
    elif  dataObj['collectionSystemTransfer']['transferType'] == "2": # Rsync Server
        job_results += test_rsyncSourceDir(dataObj)
    elif  dataObj['collectionSystemTransfer']['transferType'] == "3": # SMB Server
        job_results += test_smbSourceDir(dataObj)
    gearman_worker.send_job_status(job, 2, 4)

#    print "Test Destination Directory"
    job_results += test_destDir(dataObj)
    gearman_worker.send_job_status(job, 3, 4)
        
    verdict = "Pass"
    for test in job_results:
        if test['result'] == "Fail":
            verdict = "Fail"
            setError_collectionSystemTransfer(job)

    if verdict == "Pass":
        clearError_collectionSystemTransfer(job)

    job_results.append({"testName": "Final Verdict", "result": verdict})
    gearman_worker.send_job_status(job, 4, 4)

    return json.dumps(job_results)

new_worker = CustomGearmanWorker(['localhost:4730'])
new_worker.set_client_id('testCollectionSystemTransfer.py')
new_worker.register_task("testCollectionSystemTransfer", task_callback)
new_worker.work()