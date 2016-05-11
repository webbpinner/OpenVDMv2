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


def test_sourceDir(worker):
    sourceDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']+'/'+worker.cruiseID
    if os.path.isdir(sourceDir):
        return [{"testName": "Cruise Data Directory", "result": "Pass"}]
    else:
        return [{"testName": "Cruise Data Directory", "result": "Fail"}]

    
def test_localDestDir(worker):

    returnVal = []
    sourceDir = worker.cruiseDataTransfer['destDir']
    
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


def test_smbDestDir(worker):
    returnVal = []

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    
    command = []
    # Verify the server exists
    if worker.cruiseDataTransfer['smbUser'] == 'guest':
        command = ['smbclient', '-L', worker.cruiseDataTransfer['smbServer'], '-W', worker.cruiseDataTransfer['smbDomain'], '-g', '-N']
    else:
        command = ['smbclient', '-L', worker.cruiseDataTransfer['smbServer'], '-W', worker.cruiseDataTransfer['smbDomain'], '-g', '-U', worker.cruiseDataTransfer['smbUser'] + '%' + worker.cruiseDataTransfer['smbPass']]
 
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
        returnVal.append({"testName": "Destination Directory", "result": "Fail"})
        returnVal.append({"testName": "Write Test", "result": "Fail"})
    else:
        returnVal.append({"testName": "SMB Server", "result": "Pass"})
        
        # Create mountpoint
        mntPoint = tmpdir + '/mntpoint'
        os.mkdir(mntPoint, 0755)

        # Mount SMB Share

        if worker.cruiseDataTransfer['smbUser'] == 'guest':
            command = ['sudo', 'mount', '-t', 'cifs', worker.cruiseDataTransfer['smbServer'], mntPoint, '-o', 'rw' + ',guest' + ',domain=' + worker.cruiseDataTransfer['smbDomain']]
        else:
            command = ['sudo', 'mount', '-t', 'cifs', worker.cruiseDataTransfer['smbServer'], mntPoint, '-o', 'rw' + ',username='+worker.cruiseDataTransfer['smbUser'] + ',password=' + worker.cruiseDataTransfer['smbPass'] + ',domain=' + worker.cruiseDataTransfer['smbDomain']]

        #s = ' '
        #print s.join(command)

        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

        if proc.returncode != 0:
            returnVal.append({"testName": "SMB Share", "result": "Fail"})
            returnVal.append({"testName": "Destination Directory", "result": "Fail"})
            returnVal.append({"testName": "Write Test", "result": "Fail"})
        else:
            returnVal.append({"testName": "SMB Share", "result": "Pass"})

            # If mount is successful, test source directory
            destDir = mntPoint + worker.cruiseDataTransfer['destDir'].rstrip('/')
            if os.path.isdir(mntPoint + worker.cruiseDataTransfer['destDir']):
                returnVal.append({"testName": "Destination Directory", "result": "Pass"})
                try:
                    filepath = destDir + '/' + 'writeTest.txt'
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
            subprocess.call(['sudo', 'umount', mntPoint])

    # Cleanup
    shutil.rmtree(tmpdir)

    return returnVal


def test_rsyncDestDir(worker):

    returnVal = []
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncPasswordFilePath = tmpdir + '/' + 'passwordFile'
    
    try:
        #print "Open Transfer Log Summary file"
        rsyncPasswordFile = open(rsyncPasswordFilePath, 'w')

        #print "Saving Transfer Log Summary file"
        if worker.cruiseDataTransfer['rsyncUser'] != 'anonymous':
            rsyncPasswordFile.write(worker.cruiseDataTransfer['rsyncPass'])
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
    
    command = ['rsync', '--no-motd', '--password-file=' + rsyncPasswordFilePath, 'rsync://' + worker.cruiseDataTransfer['rsyncUser'] + '@' + worker.cruiseDataTransfer['rsyncServer']]
    
    #s = ' '
    #print s.join(command)

    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    proc.communicate()

    if proc.returncode == 0:
        returnVal.append({"testName": "Rsync Connection", "result": "Pass"})

        command = ['rsync', '--no-motd', '--password-file=' + rsyncPasswordFilePath, 'rsync://' + worker.cruiseDataTransfer['rsyncUser'] + '@' + worker.cruiseDataTransfer['rsyncServer'] + worker.cruiseDataTransfer['sourceDir']]

        #s = ' '
        #print s.join(command)

        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

        if proc.returncode == 0:
            returnVal.append({"testName": "Source Directory", "result": "Pass"})
            
            command = ['sshpass', '-p', worker.cruiseDataTransfer['rsyncPass'], 'ssh', worker.cruiseDataTransfer['rsyncServer'], '-l', worker.cruiseDataTransfer['rsyncUser'], '-o', 'StrictHostKeyChecking=no', 'touch ' + worker.cruiseDataTransfer['destDir'] + '/writeTest.txt']
            
            #s = ' '
            #print s.join(command)

            proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            proc.communicate()

            if proc.returncode == 0:
                returnVal.append({"testName": "Write Test", "result": "Pass"})
                
                command = ['sshpass', '-p', worker.cruiseDataTransfer['rsyncPass'], 'ssh', worker.cruiseDataTransfer['rsyncServer'], '-l', worker.cruiseDataTransfer['rsyncUser'], '-o', 'StrictHostKeyChecking=no', 'rm ' + worker.cruiseDataTransfer['destDir'] + '/writeTest.txt']
            
                #s = ' '
                #print s.join(command)

                proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                proc.communicate()

            else:
                returnVal.append({"testName": "Write Test", "result": "Fail"})
        else:
            returnVal.append({"testName": "Source Directory", "result": "Fail"})
            returnVal.append({"testName": "Write Test", "result": "Fail"})
    else:
        returnVal.append({"testName": "Rsync Connection", "result": "Fail"})
        returnVal.append({"testName": "Source Directory", "result": "Fail"})
        returnVal.append({"testName": "Write Test", "result": "Fail"})

    # Cleanup
        shutil.rmtree(tmpdir)

    #print json.dumps(returnVal, indent=2)
    return returnVal


def test_sshDestDir(worker):

    returnVal = []
    
    # Connect to SSH Server
    
    command = ['sshpass', '-p', worker.cruiseDataTransfer['sshPass'], 'ssh', worker.cruiseDataTransfer['sshServer'], '-l', worker.cruiseDataTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', 'ls'];
    
    #s = ' '
    #print s.join(command)

    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    proc.communicate()

    if proc.returncode == 0:
        returnVal.append({"testName": "SSH Connection", "result": "Pass"})

        command = ['sshpass', '-p', worker.cruiseDataTransfer['sshPass'], 'ssh', worker.cruiseDataTransfer['sshServer'], '-l', worker.cruiseDataTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', 'ls', worker.cruiseDataTransfer['destDir']]
        
        #s = ' '
        #print s.join(command)

        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

        if proc.returncode == 0:
            returnVal.append({"testName": "Destination Directory", "result": "Pass"})
            
            command = ['sshpass', '-p', worker.cruiseDataTransfer['sshPass'], 'ssh', worker.cruiseDataTransfer['sshServer'], '-l', worker.cruiseDataTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', 'touch ' + worker.cruiseDataTransfer['destDir'] + '/writeTest.txt']
            
            #s = ' '
            #print s.join(command)

            proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            proc.communicate()

            if proc.returncode == 0:
                returnVal.append({"testName": "Write Test", "result": "Pass"})
        
                command = ['sshpass', '-p', worker.cruiseDataTransfer['sshPass'], 'ssh', worker.cruiseDataTransfer['sshServer'], '-l', worker.cruiseDataTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', 'rm ' + worker.cruiseDataTransfer['destDir'] + '/writeTest.txt']
            
                #s = ' '
                #print s.join(command)

                proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                proc.communicate()
            
            else:
                returnVal.append({"testName": "Write Test", "result": "Fail"})

        else:
            returnVal.append({"testName": "Destination Directory", "result": "Fail"})
            returnVal.append({"testName": "Write Test", "result": "Fail"})

    else:
        returnVal.append({"testName": "SSH Connection", "result": "Fail"})
        returnVal.append({"testName": "Destination Directory", "result": "Fail"})
        returnVal.append({"testName": "Write Test", "result": "Fail"})

    #print json.dumps(returnVal, indent=2)
    return returnVal


def test_nfsDestDir(worker):
    returnVal = []

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    
    command = []

    # Verify the server exists
    command = ['rpcinfo', '-s', worker.cruiseDataTransfer['nfsServer'].split(":")[0]]
    
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
        returnVal.append({"testName": "Destination Directory", "result": "Fail"})
    else:
        returnVal.append({"testName": "NFS Server", "result": "Pass"})
        
        # Create mountpoint
        mntPoint = tmpdir + '/mntpoint'
        os.mkdir(mntPoint, 0755)

        # Mount NFS Share

        command = ['sudo', 'mount', '-t', 'nfs', worker.cruiseDataTransfer['nfsServer'], mntPoint, '-o', 'rw' + ',vers=2' + ',hard' + ',intr']

        #s = ' '
        #print s.join(command)

        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

        if proc.returncode != 0:
            returnVal.append({"testName": "NFS Server/Path", "result": "Fail"})
            returnVal.append({"testName": "Destination Directory", "result": "Fail"})
            returnVal.append({"testName": "Write Test", "result": "Fail"})
        else:
            returnVal.append({"testName": "NFS Server/Path", "result": "Pass"})

            # If mount is successful, test source directory
            destDir = mntPoint+worker.cruiseDataTransfer['destDir'].rstrip('/')
            if os.path.isdir(mntPoint+worker.cruiseDataTransfer['destDir']):
                returnVal.append({"testName": "Destination Directory", "result": "Pass"})
                try:
                    filepath = destDir + '/' + 'writeTest.txt'
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
            subprocess.call(['sudo', 'umount', mntPoint])

    # Cleanup
    shutil.rmtree(tmpdir)

    return returnVal


class OVDMGearmanWorker(gearman.GearmanWorker):

    def __init__(self):
        self.OVDM = openvdm.OpenVDM()
        self.cruiseID = ''
        self.systemStatus = ''
        self.startTime = time.gmtime(0)
        self.cruiseDataTransfer = {}
        self.shipboardDataWarehouseConfig = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])
    
    
    def on_job_execute(self, current_job):
        payloadObj = json.loads(current_job.data)
        self.startTime = time.gmtime()
        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()
        
        try:
            self.cruiseDataTransfer = self.OVDM.getCruiseDataTransfer(payloadObj['cruiseDataTransfer']['cruiseDataTransferID'])
        except KeyError:
            self.cruiseDataTransfer = {'cruiseDataTransferID':'0'}
        
        self.cruiseDataTransfer.update(payloadObj['cruiseDataTransfer'])
        
        try:
            payloadObj['cruiseID']
        except KeyError:
            self.cruiseID = self.OVDM.getCruiseID()
        else:
            self.cruiseID = payloadObj['cruiseID']
            
        #print "Set transfer test status to 'Running'"
        if self.cruiseDataTransfer['cruiseDataTransferID'] != '0':
            self.OVDM.setRunning_cruiseDataTransferTest(self.cruiseDataTransfer['cruiseDataTransferID'], os.getpid(), current_job.handle)
        
        print "Job: " + current_job.handle + ", " + self.cruiseDataTransfer['name'] + " connection test started at:   " + time.strftime("%D %T", self.startTime)

        return super(OVDMGearmanWorker, self).on_job_execute(current_job)

    
    def on_job_exception(self, current_job, exc_info):
        print "Job: " + current_job.handle + ", " + self.cruiseDataTransfer['name'] + " connection test failed at:     " + time.strftime("%D %T", time.gmtime())
        self.send_job_data(current_job, json.dumps([{"testName": "Unknown Testing Process", "result": "Fail"},{"testName": "Final Verdict", "result": "Fail"}]))
        
        if self.cruiseDataTransfer['cruiseDataTransferID'] != '0':
            self.OVDM.setError_cruiseDataTransferTest(self.cruiseDataTransfer['cruiseDataTransferID'])
        
        print exc_info
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)

    
    def on_job_complete(self, current_job, job_result):
        print "Job: " + current_job.handle + ", " + self.cruiseDataTransfer['name'] + " connection test ended at:     " + time.strftime("%D %T", time.gmtime())
        #print json.dumps(job_result)
        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_result)

    
    def after_poll(self, any_activity):
        # Return True if you want to continue polling, replaces callback_fxn
        return True

    
def task_testCruiseDataTransfer(worker, job):
    worker.send_job_status(job, 1, 4)

    job_results = []
    
#    print "Test Source Directory"
    job_results += test_sourceDir(worker)
    worker.send_job_status(job, 2, 4)

#    print "Test Destination Directory"
    if worker.cruiseDataTransfer['transferType'] == "1": # Local Directory
        job_results += test_localDestDir(worker)
    elif  worker.cruiseDataTransfer['transferType'] == "2": # Rsync Server
        job_results += test_rsyncDestDir(worker)
    elif  worker.cruiseDataTransfer['transferType'] == "3": # SMB Server
        job_results += test_smbDestDir(worker)
    elif  worker.cruiseDataTransfer['transferType'] == "4": # SSH Server
        job_results += test_sshDestDir(worker)
    elif  worker.cruiseDataTransfer['transferType'] == "5": # NFS Server
        job_results += test_nfsDestDir(worker)
        
    #print json.dumps(job_results)
    
    worker.send_job_status(job, 3, 4)

    verdict = "Pass"
    for test in job_results:
        if test['result'] == "Fail":
            verdict = "Fail"

    if worker.cruiseDataTransfer['cruiseDataTransferID'] != '0':
        if verdict == "Pass":
            worker.OVDM.clearError_cruiseDataTransfer(worker.cruiseDataTransfer['cruiseDataTransferID'], worker.cruiseDataTransfer['status'])
        else:
            worker.OVDM.setError_cruiseDataTransferTest(worker.cruiseDataTransfer['cruiseDataTransferID'])
        
    job_results.append({"testName": "Final Verdict", "result": verdict})
    worker.send_job_status(job, 4, 4)

    return json.dumps(job_results)

new_worker = OVDMGearmanWorker()
new_worker.set_client_id('testCruiseDataTransfer.py')
new_worker.register_task("testCruiseDataTransfer", task_testCruiseDataTransfer)
new_worker.work()