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
#      VERSION:  2.2
#      CREATED:  2015-01-01
#     REVISION:  2016-10-30
#
# LICENSE INFO: Open Vessel Data Management (OpenVDMv2)
#               Copyright (C) OceanDataRat.org 2016
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
import gearman
import shutil
import json
import time
import subprocess
import signal
import openvdm

DEBUG = False
new_worker = None


def debugPrint(*args, **kwargs):
    global DEBUG
    if DEBUG:
        errPrint(*args, **kwargs)


def errPrint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def build_destDir(worker):
    
    returnDestDir = worker.collectionSystemTransfer['destDir'].replace('{cruiseID}', worker.cruiseID)

    return returnDestDir


def build_sourceDir(worker):
    
    returnSourceDir = worker.collectionSystemTransfer['sourceDir'].replace('{cruiseID}', worker.cruiseID)

    return returnSourceDir


def test_localSourceDir(worker):
    returnVal = []

    sourceDir = build_sourceDir(worker)
    debugPrint('Source Dir:', sourceDir)
    if os.path.isdir(sourceDir):
        returnVal.append({"testName": "Source Directory", "result": "Pass"})
    else:
        returnVal.append({"testName": "Source Directory", "result": "Fail"})

    return returnVal

    
def test_smbSourceDir(worker):
    returnVal = []

    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    command = []
    # Verify the server exists
    if worker.collectionSystemTransfer['smbUser'] == 'guest':
        command = ['smbclient', '-L', worker.collectionSystemTransfer['smbServer'], '-W', worker.collectionSystemTransfer['smbDomain'], '-g', '-N']
        debugPrint('huh?')
    else:
        command = ['smbclient', '-L', worker.collectionSystemTransfer['smbServer'], '-W', worker.collectionSystemTransfer['smbDomain'], '-g', '-U', worker.collectionSystemTransfer['smbUser'] + '%' + worker.collectionSystemTransfer['smbPass']]

    s = ' '
    debugPrint('Connect Command:', s.join(command))

    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    lines_iterator = iter(proc.stdout.readline, b"")
    foundServer = False
    for line in lines_iterator:
        #debugPrint('line:', line.rstrip('\n')) # yield line
        if line.startswith( 'Disk' ):
            foundServer = True

    if not foundServer:
        returnVal.append({"testName": "SMB Server", "result": "Fail"})
        returnVal.append({"testName": "SMB Share", "result": "Fail"})
        returnVal.append({"testName": "Source Directory", "result": "Fail"})
    else:
        returnVal.append({"testName": "SMB Server", "result": "Pass"})

        # Create mountpoint
        mntPoint = os.path.join(tmpdir, 'mntpoint')
        os.mkdir(mntPoint, 0755)

        # Mount SMB Share
        if worker.collectionSystemTransfer['smbUser'] == 'guest':
            command = ['sudo', 'mount', '-t', 'cifs', worker.collectionSystemTransfer['smbServer'], mntPoint, '-o', 'ro'+',guest'+',domain='+worker.collectionSystemTransfer['smbDomain']]
        else:
            command = ['sudo', 'mount', '-t', 'cifs', worker.collectionSystemTransfer['smbServer'], mntPoint, '-o', 'ro'+',username='+worker.collectionSystemTransfer['smbUser']+',password='+worker.collectionSystemTransfer['smbPass']+',domain='+worker.collectionSystemTransfer['smbDomain']]

        s = ' '
        debugPrint('Connect Command:', s.join(command))

        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

        if proc.returncode != 0:
            returnVal.append({"testName": "SMB Share", "result": "Fail"})
            returnVal.append({"testName": "Source Directory", "result": "Fail"})
        else:
            returnVal.append({"testName": "SMB Share", "result": "Pass"})

            sourceDir = os.path.join(mntPoint, build_sourceDir(worker))
            debugPrint('Source Dir:', sourceDir)
            if os.path.isdir(sourceDir):
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

    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    rsyncPasswordFilePath = os.path.join(tmpdir,'passwordFile')

    try:
        rsyncPasswordFile = open(rsyncPasswordFilePath, 'w')

        #print "Saving Transfer Log Summary file"
        if worker.collectionSystemTransfer['rsyncUser'] != 'anonymous':
            rsyncPasswordFile.write(worker.collectionSystemTransfer['rsyncPass'])
        else:
            rsyncPasswordFile.write('')                

    except IOError:
        errPrint("Error Saving temporary rsync password file")
        returnVal.append({"testName": "Writing temporary rsync password file", "result": "Fail"})
        rsyncPasswordFile.close()

        # Cleanup
        shutil.rmtree(tmpdir)

        return returnVal

    finally:
        rsyncPasswordFile.close()
        os.chmod(rsyncPasswordFilePath, 0600)

    command = ['rsync', '--no-motd', '--password-file=' + rsyncPasswordFilePath, 'rsync://' + worker.collectionSystemTransfer['rsyncUser'] + '@' + worker.collectionSystemTransfer['rsyncServer']]

    s = ' '
    debugPrint('Connection Command:',s.join(command))

    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    proc.communicate()

    if proc.returncode == 0:
        returnVal.append({"testName": "Rsync Connection", "result": "Pass"})

        sourceDir = build_sourceDir(worker)
        debugPrint('Source Dir:', sourceDir)

        command = ['rsync', '--no-motd', '--password-file=' + rsyncPasswordFilePath, 'rsync://' + worker.collectionSystemTransfer['rsyncUser'] + '@' + worker.collectionSystemTransfer['rsyncServer'] + sourceDir]

        s = ' '
        debugPrint('Connection Command:',s.join(command))

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
        
    return returnVal


def test_sshSourceDir(worker):
    
    returnVal = []

    command = ''

    if worker.collectionSystemTransfer['sshUseKey'] == '1':
        command = ['ssh', worker.collectionSystemTransfer['sshServer'], '-l', worker.collectionSystemTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PasswordAuthentication=no', 'ls']
    else:
        command = ['sshpass', '-p', worker.collectionSystemTransfer['sshPass'], 'ssh', worker.collectionSystemTransfer['sshServer'], '-l', worker.collectionSystemTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PubkeyAuthentication=no', 'ls']

    s = ' '
    debugPrint('Connection Command:', s.join(command))
    
    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    proc.communicate()

    debugPrint(proc.returncode)
    if proc.returncode == 0:
        returnVal.append({"testName": "SSH Connection", "result": "Pass"})

        sourceDir = build_sourceDir(worker)
        debugPrint('Source Dir:', sourceDir)

        if worker.collectionSystemTransfer['sshUseKey'] == '1':
            command = ['ssh', worker.collectionSystemTransfer['sshServer'], '-l', worker.collectionSystemTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PasswordAuthentication=no', 'ls', sourceDir]
        else:
            command = ['sshpass', '-p', worker.collectionSystemTransfer['sshPass'], 'ssh', worker.collectionSystemTransfer['sshServer'], '-l', worker.collectionSystemTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PubkeyAuthentication=no', 'ls', sourceDir]
        
        s = ' '
        debugPrint('Connection Command:', s.join(command))
    
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
    tmpdir = tempfile.mkdtemp()
    
    command = ['rpcinfo', '-s', worker.collectionSystemTransfer['nfsServer'].split(":")[0]]
    
    s = ' '
    debugPrint('Connection Command:', s.join(command))
    
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
        mntPoint = os.path.join(tmpdir, 'mntpoint')
        os.mkdir(mntPoint, 0755)

        # Mount NFS Share

        command = ['sudo', 'mount', '-t', 'nfs', worker.collectionSystemTransfer['nfsServer'], mntPoint, '-o', 'ro' + ',vers=2' + ',hard' + ',intr']

        s = ' '
        debugPrint('Connection Command:', s.join(command))

        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

        if proc.returncode != 0:
            returnVal.append({"testName": "NFS Server/Path", "result": "Fail"})
            returnVal.append({"testName": "Source Directory", "result": "Fail"})
        else:
            returnVal.append({"testName": "NFS Server/Path", "result": "Pass"})

            # If mount is successful, test source directory
            sourceDir = os.path.join(mntPoint, build_sourceDir(worker))
            debugPrint('Source Dir:', sourceDir)
            if os.path.isdir(sourceDir):
                returnVal.append({"testName": "Source Directory", "result": "Pass"})
            else:
                returnVal.append({"testName": "Source Directory", "result": "Fail"})

            # Unmount SMB Share
            subprocess.call(['sudo', 'umount', mntPoint])

    # Cleanup
    shutil.rmtree(tmpdir)

    return returnVal


def test_destDir(worker):

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    destDir = os.path.join(cruiseDir, worker.collectionSystemTransfer['destDir'])
    
    if os.path.isdir(destDir):
        return [{"testName": "Destination Directory", "result": "Pass"}]
    else:
        return [{"testName": "Destination Directory", "result": "Fail"}]

    
class OVDMGearmanWorker(gearman.GearmanWorker):

    def __init__(self):
        self.stop = False
        self.quit = False
        self.OVDM = openvdm.OpenVDM()
        self.cruiseID = ''
#        self.cruiseStartDate = ''
#        self.systemStatus = ''
        self.startTime = time.gmtime(0)
        self.collectionSystemTransfer = {}
        self.shipboardDataWarehouseConfig = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])
        
        
    def on_job_execute(self, current_job):
        payloadObj = json.loads(current_job.data)
        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()
        self.cruiseID = self.OVDM.getCruiseID()

        if len(payloadObj) > 0:        
            try:
                payloadObj['collectionSystemTransfer']['collectionSystemTransferID']
            except KeyError:
                debugPrint("Just testing a transfer configuration")
                self.collectionSystemTransfer = payloadObj['collectionSystemTransfer']
                self.collectionSystemTransfer['collectionSystemTransferID'] = None
            else:
                self.collectionSystemTransfer = self.OVDM.getCollectionSystemTransfer(payloadObj['collectionSystemTransfer']['collectionSystemTransferID'])
                self.collectionSystemTransfer.update(payloadObj['collectionSystemTransfer'])
            try:
                payloadObj['cruiseID']
            except KeyError:
                self.cruiseID = self.OVDM.getCruiseID()
            else:
                self.cruiseID = payloadObj['cruiseID']
                
        if self.collectionSystemTransfer['collectionSystemTransferID'] != None:
            self.OVDM.setRunning_collectionSystemTransferTest(self.collectionSystemTransfer['collectionSystemTransferID'], os.getpid(), current_job.handle)
        
        errPrint("Job:", current_job.handle + ",", self.collectionSystemTransfer['name'], "connection test started at:  ", time.strftime("%D %T", time.gmtime()))

        return super(OVDMGearmanWorker, self).on_job_execute(current_job)

    def on_job_exception(self, current_job, exc_info):
        errPrint("Job:", current_job.handle + ",", self.collectionSystemTransfer['name'], "connection test failed at:    ", time.strftime("%D %T", time.gmtime()))
        
        self.send_job_data(current_job, json.dumps([{"testName": "Worker crashed", "result": "Fail"},{"testName": "Final Verdict", "result": "Fail"}]))
        
        self.OVDM.sendMsg(current_job.handle, 'Worker crashed testing ' + self.collectionSystemTransfer['name'])
        
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        errPrint(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)

    
    def on_job_complete(self, current_job, job_results):
        resultsObj = json.loads(job_results)

        debugPrint('Job Results:', json.dumps(resultsObj, indent=2))

        if self.collectionSystemTransfer['collectionSystemTransferID'] != None: # collectionSystemTransferID == None would be testing a new, unsaved config
            if resultsObj['parts'][-1]['result'] == "Fail":
                for test in resultsObj['parts']:
                    if test['result'] == "Fail":
                        self.OVDM.setError_collectionSystemTransferTest(self.collectionSystemTransfer['collectionSystemTransferID'], 'Reason: ' + test['testName'])
                        break
            else:
                self.OVDM.clearError_collectionSystemTransfer(self.collectionSystemTransfer['collectionSystemTransferID'], self.collectionSystemTransfer['status'])



        errPrint("Job:", current_job.handle + ",", self.collectionSystemTransfer['name'], "connection test ended at:    ", time.strftime("%D %T", time.gmtime()))

        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_results)

    
    def after_poll(self, any_activity):
        self.stop = False
        if self.quit:
            errPrint("Quitting")
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

    
def task_testCollectionSystemTransfer(worker, job):

    job_results = {'parts':[]}

    worker.send_job_status(job, 1, 4)
    
    debugPrint("Test Source Directory")
    if worker.collectionSystemTransfer['transferType'] == "1": # Local Directory
        job_results['parts'] = test_localSourceDir(worker)
    elif  worker.collectionSystemTransfer['transferType'] == "2": # Rsync Server
        job_results['parts'] += test_rsyncSourceDir(worker)
    elif  worker.collectionSystemTransfer['transferType'] == "3": # SMB Share
        job_results['parts'] += test_smbSourceDir(worker)
    elif  worker.collectionSystemTransfer['transferType'] == "4": # SSH Server
        job_results['parts'] += test_sshSourceDir(worker)
    elif  worker.collectionSystemTransfer['transferType'] == "5": # NFS Server/Path
        job_results['parts'] += test_nfsSourceDir(worker)

    worker.send_job_status(job, 2, 4)

    debugPrint(json.dumps(worker.collectionSystemTransfer))
    if worker.collectionSystemTransfer['enable'] == '1':
        debugPrint("Test Destination Directory")
        job_results['parts'] += test_destDir(worker)
        worker.send_job_status(job, 3, 4)
        
    verdict = "Pass"
    for test in job_results['parts']:
        if test['result'] == "Fail":
            verdict = "Fail"

    job_results['parts'].append({"testName": "Final Verdict", "result": verdict})
    worker.send_job_status(job, 4, 4)

    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Main function of the script should it be run as a stand-alone utility.
# -------------------------------------------------------------------------------------
def main(argv):

    parser = argparse.ArgumentParser(description='Handle collection system transfer connection test related tasks')
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

    new_worker.set_client_id('testCollectionSystemTransfer.py')

    debugPrint('Registering worker tasks...')
    debugPrint('   Task:', 'testCollectionSystemTransfer')
    new_worker.register_task("testCollectionSystemTransfer", task_testCollectionSystemTransfer)

    debugPrint('Waiting for jobs...')
    new_worker.work()

# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])
