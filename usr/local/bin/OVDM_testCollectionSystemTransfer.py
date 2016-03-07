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
import gearman
import shutil
import json
import time
import subprocess
import openvdm


def build_destDir(worker):
    
    returnDestDir = worker.collectionSystemTransfer['destDir'].replace('{cruiseID}', worker.cruiseID)

    return returnDestDir


def build_sourceDir(worker):
    
    returnSourceDir = worker.collectionSystemTransfer['sourceDir'].replace('{cruiseID}', worker.cruiseID)

    return returnSourceDir


def test_localSourceDir(worker):

    if os.path.isdir(worker.collectionSystemTransfer['sourceDir']):
        return [{"testName": "Source Directory", "result": "Pass"}]
    else:
        return [{"testName": "Source Directory", "result": "Fail"}]

    
def test_smbSourceDir(worker):
    returnVal = []

    # Create temp directory
    #print "Create Temp Directory"
    tmpdir = tempfile.mkdtemp()
 
    command = []
    # Verify the server exists
    if worker.collectionSystemTransfer['smbUser'] == 'guest':
        command = ['smbclient', '-L', worker.collectionSystemTransfer['smbServer'], '-W', worker.collectionSystemTransfer['smbDomain'], '-g', '-N']
    else:
        command = ['smbclient', '-L', worker.collectionSystemTransfer['smbServer'], '-W', worker.collectionSystemTransfer['smbDomain'], '-g', '-U', worker.collectionSystemTransfer['smbUser'] + '%' + worker.collectionSystemTransfer['smbPass']]
    
    #s = ' '
    #print s.join(command)
    
    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    lines_iterator = iter(proc.stdout.readline, b"")
    foundServer = False
    for line in lines_iterator:
        #print line # yield line
        if line.startswith( 'Disk' ):
            foundServer = True
            #print "Yep"
    
    if not foundServer:
        returnVal.append({"testName": "SMB Server", "result": "Fail"})
        returnVal.append({"testName": "SMB Share", "result": "Fail"})
        returnVal.append({"testName": "Source Directory", "result": "Fail"})
    else:
        returnVal.append({"testName": "SMB Server", "result": "Pass"})
    
        # Create mountpoint
        mntPoint = tmpdir + '/mntpoint'
        os.mkdir(mntPoint, 0755)

        # Mount SMB Share

        if worker.collectionSystemTransfer['smbUser'] == 'guest':
            command = ['sudo', 'mount', '-t', 'cifs', worker.collectionSystemTransfer['smbServer'], mntPoint, '-o', 'ro'+',guest'+',domain='+worker.collectionSystemTransfer['smbDomain']]
        else:
            command = ['sudo', 'mount', '-t', 'cifs', worker.collectionSystemTransfer['smbServer'], mntPoint, '-o', 'ro'+',username='+worker.collectionSystemTransfer['smbUser']+',password='+worker.collectionSystemTransfer['smbPass']+',domain='+worker.collectionSystemTransfer['smbDomain']]

        #s = ' '
        #print s.join(command)

        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

        if proc.returncode != 0:
            returnVal.append({"testName": "SMB Share", "result": "Fail"})
            returnVal.append({"testName": "Source Directory", "result": "Fail"})
        else:
            returnVal.append({"testName": "SMB Share", "result": "Pass"})

            # If mount is successful, test source directory
            sourceDir = mntPoint+worker.collectionSystemTransfer['sourceDir']
            if os.path.isdir(mntPoint+worker.collectionSystemTransfer['sourceDir']):
                returnVal.append({"testName": "Source Directory", "result": "Pass"})
            else:
                returnVal.append({"testName": "Source Directory", "result": "Fail"})

            # Unmount SMB Share
            subprocess.call(['sudo', 'umount', mntPoint])

    # Cleanup
    shutil.rmtree(tmpdir)

    return returnVal


def test_rsyncSourceDir(worker):
    
    returnVal = []

    # Connect to RSYNC Server

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncPasswordFilePath = tmpdir + '/' + 'passwordFile'

    try:
        #print "Open Transfer Log Summary file"
        rsyncPasswordFile = open(rsyncPasswordFilePath, 'w')

        #print "Saving Transfer Log Summary file"
        if worker.collectionSystemTransfer['rsyncUser'] != 'anonymous':
            rsyncPasswordFile.write(worker.collectionSystemTransfer['rsyncPass'])
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
    
    command = ['rsync', '--no-motd', '--password-file=' + rsyncPasswordFilePath, 'rsync://' + worker.collectionSystemTransfer['rsyncUser'] + '@' + worker.collectionSystemTransfer['rsyncServer']]
    
    #s = ' '
    #print s.join(command)
    
    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    proc.communicate()

    if proc.returncode == 0:
        returnVal.append({"testName": "Rsync Connection", "result": "Pass"})

        command = ['rsync', '--no-motd', '--password-file=' + rsyncPasswordFilePath, 'rsync://' + worker.collectionSystemTransfer['rsyncUser'] + '@' + worker.collectionSystemTransfer['rsyncServer'] + worker.collectionSystemTransfer['sourceDir']]
        
        #s = ' '
        #print s.join(command)
    
        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

        if proc.returncode == 0:
            returnVal.append({"testName": "Source Directory", "result": "Pass"})
        else:
            returnVal.append({"testName": "Source Directory", "result": "Fail"})
    else:
        returnVal.append({"testName": "Rsync Connection", "result": "Fail"})
        returnVal.append({"testName": "Source Directory", "result": "Fail"})

    # Cleanup
    shutil.rmtree(tmpdir)
        
    #print json.dumps(returnVal, indent=2)
    return returnVal


def test_sshSourceDir(worker):
    
    returnVal = []

    # Connect to SSH Server

    command = ['sshpass', '-p', worker.collectionSystemTransfer['sshPass'], 'ssh', worker.collectionSystemTransfer['sshServer'], '-l', worker.collectionSystemTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', 'ls']
    
    #s = ' '
    #print s.join(command)
    
    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    proc.communicate()

    if proc.returncode == 0:
        returnVal.append({"testName": "SSH Connection", "result": "Pass"})

        command = ['sshpass', '-p', worker.collectionSystemTransfer['sshPass'], 'ssh', worker.collectionSystemTransfer['sshServer'], '-l', worker.collectionSystemTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', 'ls', worker.collectionSystemTransfer['sourceDir']]
        
        #s = ' '
        #print s.join(command)
    
        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

        if proc.returncode == 0:
            returnVal.append({"testName": "Source Directory", "result": "Pass"})
        else:
            returnVal.append({"testName": "Source Directory", "result": "Fail"})
    else:
        returnVal.append({"testName": "SSH Connection", "result": "Fail"})
        returnVal.append({"testName": "Source Directory", "result": "Fail"})
        
    #print json.dumps(returnVal, indent=2)
    return returnVal


def test_nfsSourceDir(worker):
    returnVal = []

    # Create temp directory
    #print "Create Temp Directory"
    tmpdir = tempfile.mkdtemp()
    
    # Verify the server exists
    #if worker.collectionSystemTransfer['nfsUser'] == 'guest':
    command = ['rpcinfo', '-s', worker.collectionSystemTransfer['nfsServer'].split(":")[0]]
    #else:
    #    command = ['rpcinfo', '-s', worker.collectionSystemTransfer['nfsServer'].split(":")[0]]
    
    #s = ' '
    #print s.join(command)
    
    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    lines_iterator = iter(proc.stdout.readline, b"")
    
    foundNFS = False
    foundMountd = False
    
    for line in lines_iterator:
        if foundNFS and foundMountd:
            break
        lineArray = line.split()
        if lineArray[3] == 'nfs':
            foundNFS = True
            continue
        if lineArray[3] == 'mountd':
            foundMountd = True
            continue
    
    if not foundNFS or not foundMountd:
        returnVal.append({"testName": "NFS Server", "result": "Fail"})
        returnVal.append({"testName": "NFS Server/Path", "result": "Fail"})        
        returnVal.append({"testName": "Source Directory", "result": "Fail"})
    else:
        returnVal.append({"testName": "NFS Server", "result": "Pass"})
    
        # Create mountpoint
        mntPoint = tmpdir + '/mntpoint'
        os.mkdir(mntPoint, 0755)

        # Mount NFS Share

        #if worker.collectionSystemTransfer['nfsUser'] == 'guest':
        command = ['sudo', 'mount', '-t', 'nfs', worker.collectionSystemTransfer['nfsServer'], mntPoint, '-o', 'ro' + ',vers=2' + ',hard' + ',intr']
        #else:
        #    command = ['sudo', 'mount', '-t', 'nfs', worker.collectionSystemTransfer['nfsServer'], mntPoint, '-o', 'ro' + ',vers=2' + ',hard' + ',intr']

        #s = ' '
        #print s.join(command)

        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

        if proc.returncode != 0:
            returnVal.append({"testName": "NFS Server/Path", "result": "Fail"})
            returnVal.append({"testName": "Source Directory", "result": "Fail"})
        else:
            returnVal.append({"testName": "NFS Server/Path", "result": "Pass"})

            # If mount is successful, test source directory
            sourceDir = mntPoint+worker.collectionSystemTransfer['sourceDir']
            if os.path.isdir(mntPoint+worker.collectionSystemTransfer['sourceDir']):
                returnVal.append({"testName": "Source Directory", "result": "Pass"})
            else:
                returnVal.append({"testName": "Source Directory", "result": "Fail"})

            # Unmount SMB Share
            subprocess.call(['sudo', 'umount', mntPoint])

    # Cleanup
    shutil.rmtree(tmpdir)

    return returnVal


def test_destDir(worker):
    destDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']+'/'+worker.cruiseID+'/'+worker.collectionSystemTransfer['destDir']
    
    if os.path.isdir(destDir):
        return [{"testName": "Destination Directory", "result": "Pass"}]
    else:
        return [{"testName": "Destination Directory", "result": "Fail"}]

    
class OVDMGearmanWorker(gearman.GearmanWorker):

    def __init__(self):
        self.OVDM = openvdm.OpenVDM()
        self.cruiseID = ''
        self.cruiseStartDate = ''
        self.systemStatus = ''
        self.startTime = time.gmtime(0)
        self.collectionSystemTransfer = {}
        self.shipboardDataWarehouseConfig = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])
        
        
    def on_job_execute(self, current_job):
        payloadObj = json.loads(current_job.data)
        self.startTime = time.gmtime()
        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()
        
        try:
            self.collectionSystemTransfer = self.OVDM.getCollectionSystemTransfer(payloadObj['collectionSystemTransfer']['collectionSystemTransferID'])
        except KeyError:
            self.collectionSystemTransfer = {'collectionSystemTransferID': '0'}
        
        self.collectionSystemTransfer.update(payloadObj['collectionSystemTransfer'])
        
        try:
            payloadObj['cruiseID']
        except KeyError:
            self.cruiseID = self.OVDM.getCruiseID()
        else:
            self.cruiseID = payloadObj['cruiseID']
            
        #print "Set transfer test status to 'Running'"
        if self.collectionSystemTransfer['collectionSystemTransferID'] != '0':
            self.OVDM.setRunning_collectionSystemTransferTest(self.collectionSystemTransfer['collectionSystemTransferID'], os.getpid(), current_job.handle)
        
        print "Job: " + current_job.handle + ", " + self.collectionSystemTransfer['name'] + " connection test started at:   " + time.strftime("%D %T", self.startTime)

        return super(OVDMGearmanWorker, self).on_job_execute(current_job)

    def on_job_exception(self, current_job, exc_info):
        print "Job: " + current_job.handle + ", " + self.collectionSystemTransfer['name'] + " connection test failed at:     " + time.strftime("%D %T", time.gmtime())
        self.send_job_data(current_job, json.dumps([{"testName": "Unknown Testing Process", "result": "Fail"},{"testName": "Final Verdict", "result": "Fail"}]))
        
        if self.collectionSystemTransfer['collectionSystemTransferID'] != '0':
            self.OVDM.setError_collectionSystemTransferTest(self.collectionSystemTransfer['collectionSystemTransferID'])
        
        print exc_info
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)

    
    def on_job_complete(self, current_job, job_result):
        print "Job: " + current_job.handle + ", " + self.collectionSystemTransfer['name'] + " connection test ended at:     " + time.strftime("%D %T", time.gmtime())
        #print json.dumps(job_result)
        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_result)

    
    def after_poll(self, any_activity):
        # Return True if you want to continue polling, replaces callback_fxn
        return True

    
def task_testCollectionSystemTransfer(worker, job):
    worker.send_job_status(job, 1, 4)
    worker.collectionSystemTransfer['destDir'] = build_destDir(worker)
    worker.collectionSystemTransfer['sourceDir'] = build_sourceDir(worker)

    job_results = []
    
#    print "Test Source Directory"
    if worker.collectionSystemTransfer['transferType'] == "1": # Local Directory
        job_results += test_localSourceDir(worker)
    elif  worker.collectionSystemTransfer['transferType'] == "2": # Rsync Server
        job_results += test_rsyncSourceDir(worker)
    elif  worker.collectionSystemTransfer['transferType'] == "3": # SMB Share
        job_results += test_smbSourceDir(worker)
    elif  worker.collectionSystemTransfer['transferType'] == "4": # SSH Server
        job_results += test_sshSourceDir(worker)
    elif  worker.collectionSystemTransfer['transferType'] == "5": # NFS Server/Path
        job_results += test_nfsSourceDir(worker)
    worker.send_job_status(job, 2, 4)

#    print "Test Destination Directory"
    job_results += test_destDir(worker)
    worker.send_job_status(job, 3, 4)
        
    verdict = "Pass"
    for test in job_results:
        if test['result'] == "Fail":
            verdict = "Fail"

    if worker.collectionSystemTransfer['collectionSystemTransferID'] != '0':
        if verdict == "Pass":
            worker.OVDM.clearError_collectionSystemTransfer(worker.collectionSystemTransfer['collectionSystemTransferID'], worker.collectionSystemTransfer['status'])
        else:
            worker.OVDM.setError_collectionSystemTransferTest(worker.collectionSystemTransfer['collectionSystemTransferID'])

    job_results.append({"testName": "Final Verdict", "result": verdict})
    worker.send_job_status(job, 4, 4)

    return json.dumps(job_results)

new_worker = OVDMGearmanWorker()
new_worker.set_client_id('testCollectionSystemTransfer.py')
new_worker.register_task("testCollectionSystemTransfer", task_testCollectionSystemTransfer)
new_worker.work()
