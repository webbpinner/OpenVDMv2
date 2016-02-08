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
    
    command = []
    # Verify the server exists
    if data['cruiseDataTransfer']['smbUser'] == 'guest':
        command = ['smbclient', '-L', data['cruiseDataTransfer']['smbServer'], '-W', data['cruiseDataTransfer']['smbDomain'], '-g', '-N']
    else:
        command = ['smbclient', '-L', data['cruiseDataTransfer']['smbServer'], '-W', data['cruiseDataTransfer']['smbDomain'], '-g', '-U', data['cruiseDataTransfer']['smbUser'] + '%' + data['cruiseDataTransfer']['smbPass']]
 
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

        if data['cruiseDataTransfer']['smbUser'] == 'guest':
            command = ['sudo', 'mount', '-t', 'cifs', data['cruiseDataTransfer']['smbServer'], mntPoint, '-o', 'rw' + ',guest' + ',domain=' + data['cruiseDataTransfer']['smbDomain']]
        else:
            command = ['sudo', 'mount', '-t', 'cifs', data['cruiseDataTransfer']['smbServer'], mntPoint, '-o', 'rw' + ',username='+data['cruiseDataTransfer']['smbUser'] + ',password=' + data['cruiseDataTransfer']['smbPass'] + ',domain=' + data['cruiseDataTransfer']['smbDomain']]

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
            destDir = mntPoint+data['cruiseDataTransfer']['destDir'].rstrip('/')
            if os.path.isdir(mntPoint+data['cruiseDataTransfer']['destDir']):
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
            call(['sudo', 'umount', mntPoint])

    # Cleanup
    shutil.rmtree(tmpdir)

    return returnVal

def test_rsyncDestDir(data):

    returnVal = []
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncPasswordFilePath = tmpdir + '/' + 'passwordFile'
    
    try:
        #print "Open Transfer Log Summary file"
        rsyncPasswordFile = open(rsyncPasswordFilePath, 'w')

        #print "Saving Transfer Log Summary file"
        if data['cruiseDataTransfer']['rsyncUser'] != 'anonymous':
            rsyncPasswordFile.write(data['cruiseDataTransfer']['rsyncPass'])
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
    
    command = ['rsync', '--no-motd', '--password-file=' + rsyncPasswordFilePath, 'rsync://' + data['cruiseDataTransfer']['rsyncUser'] + '@' + data['cruiseDataTransfer']['rsyncServer']]
    
    #s = ' '
    #print s.join(command)

    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    proc.communicate()

    if proc.returncode == 0:
        returnVal.append({"testName": "Rsync Connection", "result": "Pass"})

        command = ['rsync', '--no-motd', '--password-file=' + rsyncPasswordFilePath, 'rsync://' + data['cruiseDataTransfer']['rsyncUser'] + '@' + data['cruiseDataTransfer']['rsyncServer'] + data['cruiseDataTransfer']['sourceDir']]

        #s = ' '
        #print s.join(command)

        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

        if proc.returncode == 0:
            returnVal.append({"testName": "Source Directory", "result": "Pass"})
            
            command = ['sshpass', '-p', data['cruiseDataTransfer']['rsyncPass'], 'ssh', data['cruiseDataTransfer']['rsyncServer'], '-l', data['cruiseDataTransfer']['rsyncUser'], '-o', 'StrictHostKeyChecking=no', 'touch ' + data['cruiseDataTransfer']['destDir'] + '/writeTest.txt']
            
            #s = ' '
            #print s.join(command)

            proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            proc.communicate()

            if proc.returncode == 0:
                returnVal.append({"testName": "Write Test", "result": "Pass"})
                
                command = ['sshpass', '-p', data['cruiseDataTransfer']['rsyncPass'], 'ssh', data['cruiseDataTransfer']['rsyncServer'], '-l', data['cruiseDataTransfer']['rsyncUser'], '-o', 'StrictHostKeyChecking=no', 'rm ' + data['cruiseDataTransfer']['destDir'] + '/writeTest.txt']
            
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

def test_sshDestDir(data):

    returnVal = []
    
    # Connect to SSH Server
    
    command = ['sshpass', '-p', data['cruiseDataTransfer']['sshPass'], 'ssh', data['cruiseDataTransfer']['sshServer'], '-l', data['cruiseDataTransfer']['sshUser'], '-o', 'StrictHostKeyChecking=no', 'ls'];
    
    #s = ' '
    #print s.join(command)

    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    proc.communicate()

    if proc.returncode == 0:
        returnVal.append({"testName": "SSH Connection", "result": "Pass"})

        command = ['sshpass', '-p', data['cruiseDataTransfer']['sshPass'], 'ssh', data['cruiseDataTransfer']['sshServer'], '-l', data['cruiseDataTransfer']['sshUser'], '-o', 'StrictHostKeyChecking=no', 'ls', data['cruiseDataTransfer']['destDir']]
        
        #s = ' '
        #print s.join(command)

        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

        if proc.returncode == 0:
            returnVal.append({"testName": "Destination Directory", "result": "Pass"})
            
            command = ['sshpass', '-p', data['cruiseDataTransfer']['sshPass'], 'ssh', data['cruiseDataTransfer']['sshServer'], '-l', data['cruiseDataTransfer']['sshUser'], '-o', 'StrictHostKeyChecking=no', 'touch ' + data['cruiseDataTransfer']['destDir'] + '/writeTest.txt']
            
            #s = ' '
            #print s.join(command)

            proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            proc.communicate()

            if proc.returncode == 0:
                returnVal.append({"testName": "Write Test", "result": "Pass"})
        
                command = ['sshpass', '-p', data['cruiseDataTransfer']['sshPass'], 'ssh', data['cruiseDataTransfer']['sshServer'], '-l', data['cruiseDataTransfer']['sshUser'], '-o', 'StrictHostKeyChecking=no', 'rm ' + data['cruiseDataTransfer']['destDir'] + '/writeTest.txt']
            
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

def test_nfsDestDir(data):
    returnVal = []

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    
    command = []

    # Verify the server exists
    command = ['rpcinfo', '-s', data['cruiseDataTransfer']['nfsServer'].split(":")[0]]
    
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

        command = ['sudo', 'mount', '-t', 'nfs', data['cruiseDataTransfer']['nfsServer'], mntPoint, '-o', 'rw' + ',vers=2' + ',hard' + ',intr']

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
            destDir = mntPoint+data['cruiseDataTransfer']['destDir'].rstrip('/')
            if os.path.isdir(mntPoint+data['cruiseDataTransfer']['destDir']):
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
            call(['sudo', 'umount', mntPoint])

    # Cleanup
    shutil.rmtree(tmpdir)

    return returnVal

def setError_cruiseDataTransfer(job):
    dataObj = json.loads(job.data)

    if 'cruiseDataTransferID' in dataObj['cruiseDataTransfer']:
        # Set Error for current tranfer in DB via API
        url = dataObj['siteRoot'] + 'api/cruiseDataTransfers/setErrorCruiseDataTransfer/' + dataObj['cruiseDataTransfer']['cruiseDataTransferID']
        r = requests.get(url)
    
def clearError_cruiseDataTransfer(job):
    dataObj = json.loads(job.data)
    if dataObj['cruiseDataTransfer']['status'] == "3":
        if 'cruiseDataTransferID' in dataObj['cruiseDataTransfer']:
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
    elif  dataObj['cruiseDataTransfer']['transferType'] == "4": # SSH Server
        job_results += test_sshDestDir(dataObj)
    elif  dataObj['cruiseDataTransfer']['transferType'] == "5": # NFS Server
        job_results += test_nfsDestDir(dataObj)
        
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
