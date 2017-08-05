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
#      VERSION:  2.3
#      CREATED:  2015-01-01
#     REVISION:  2017-08-05
#
# LICENSE INFO: Open Vessel Data Management (OpenVDMv2)
#               Copyright (C) OceanDataRat.org 2017
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
import fnmatch
import subprocess
import signal
import openvdm
from random import randint


DEBUG = False
new_worker = None


def debugPrint(*args, **kwargs):
    global DEBUG
    if DEBUG:
        errPrint(*args, **kwargs)


def errPrint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def build_filelist(sourceDir, filters):

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

    returnFiles['include'] = [filename.replace(sourceDir + '/', '', 1) for filename in returnFiles['include']]
    returnFiles['exclude'] = [filename.replace(sourceDir + '/', '', 1) for filename in returnFiles['exclude']]
    
    return returnFiles


def build_destDirectories(destDir, files):
    files = [filename.replace(filename, destDir + filename, 1) for filename in files]

    for dirname in set(os.path.dirname(p) for p in files):
        if not os.path.isdir(dirname):
            debugPrint("Creating Directory:", dirname)
            os.makedirs(dirname)

            
def transfer_localDestDir(worker, job):

    debugPrint("Transfer to Local Directory")
    filters = {'includeFilter': '*','excludeFilter': '','ignoreFilter': ''}
    
    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    destDir = worker.cruiseDataTransfer['destDir'].rstrip('/') + '/'

    debugPrint('destDir:', destDir)

    debugPrint("Build file list")
    files = build_filelist(cruiseDir, filters)
    
    fileIndex = 0
    fileCount = len(files['include'])
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncFileListPath = os.path.join(tmpdir, 'rsyncFileList.txt')
        
    try:
        rsyncFileListFile = open(rsyncFileListPath, 'w')
        rsyncFileListFile.write('\n'.join([worker.cruiseID + '/' + str(x) for x in files['include']]))

    except IOError:
        errPrint("Error Saving temporary rsync filelist file")
        rsyncFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
        return False

    finally:
        #debugPrint("Closing rsync filelist file")
        rsyncFileListFile.close()    
    
    command = ['rsync', '-tri', '--files-from=' + rsyncFileListPath, baseDir, destDir]

    s = ' '
    debugPrint('Transfer Command:', s.join(command))
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
    	debugPrint('line:', line.rstrip('\n'))
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['new'].append(filename)
            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['updated'].append(filename)
            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
            
        if worker.stop:
            debugPrint("Stopping")
            break    

    files['new'] = [os.path.join(baseDir,filename) for filename in files['new']]
    files['updated'] = [os.path.join(baseDir,filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)    
    return files


def transfer_smbDestDir(worker, job):
    
    debugPrint("Transfer from SMB Source")

    filters = {'includeFilter': '*','excludeFilter': '','ignoreFilter': ''}

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
 
    # Create mountpoint
    mntPoint = os.path.join(tmpdir, 'mntpoint')
    os.mkdir(mntPoint, 0755)

    # Mount SMB Share
    debugPrint("Mounting SMB Share")
    if worker.cruiseDataTransfer['smbUser'] == 'guest':
        
        command = ['sudo', 'mount', '-t', 'cifs', worker.cruiseDataTransfer['smbServer'], mntPoint, '-o', 'rw' + ',guest' +  'domain=' + worker.cruiseDataTransfer['smbDomain']]
        
        s = ' '
        debugPrint(s.join(command))

        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

    else:
        command = ['sudo', 'mount', '-t', 'cifs', worker.cruiseDataTransfer['smbServer'], mntPoint, '-o', 'rw' + ',username=' + worker.cruiseDataTransfer['smbUser'] + ',password='+worker.cruiseDataTransfer['smbPass'] + ',domain='+worker.cruiseDataTransfer['smbDomain']]
        
        s = ' '
        debugPrint(s.join(command))

        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)

    sourceDir = baseDir
    destDir = os.path.join(mntPoint, worker.cruiseDataTransfer['destDir'].rstrip('/')) + '/'

    debugPrint("Build file list")
    files = build_filelist(cruiseDir, filters)
    
    fileIndex = 0
    fileCount = len(files['include'])
    
    rsyncFileListPath = os.path.join(tmpdir, 'rsyncFileList.txt')
        
    try:
        rsyncFileListFile = open(rsyncFileListPath, 'w')
        rsyncFileListFile.write('\n'.join([worker.cruiseID + '/' + str(x) for x in files['include']]))

    except IOError:
        errPrint("Error Saving temporary rsync filelist file")
        rsyncFileListFile.close()
            
        # Cleanup
        subprocess.call(['sudo', 'umount', mntPoint])
        shutil.rmtree(tmpdir)
            
        return False

    finally:
        rsyncFileListFile.close()
    
    command = ['rsync', '-tri', '--files-from=' + rsyncFileListPath, sourceDir, destDir]
    
    s = ' '
    debugPrint('Transfer Command:', s.join(command))

    popen = subprocess.Popen(command, stdout=subprocess.PIPE)

    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #debugPrint('line', line.rstrip('\n'))
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['new'].append(filename)
            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['updated'].append(filename)
            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
            
        if worker.stop:
            debugPrint("Stopping")
            break
    
    files['new'] = [os.path.join(baseDir,filename) for filename in files['new']]
    files['updated'] = [os.path.join(baseDir,filename) for filename in files['updated']]
    
    #print "Cleanup"
    debugPrint("Unmount SMB Share")
    subprocess.call(['sudo', 'umount', mntPoint])
    shutil.rmtree(tmpdir)

    return files


def transfer_rsyncDestDir(worker, job):

    debugPrint("Transfer to Rsync Server")
    filters = {'includeFilter': '*','excludeFilter': '','ignoreFilter': ''}

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)

    sourceDir = cruiseDir
    destDir = worker.cruiseDataTransfer['destDir'].rstrip('/')

    #debugPrint("Source Dir:", sourceDir)
    #debugPrint("Destinstation Dir:", destDir)
    
    debugPrint("Build file list")
    files = build_filelist(sourceDir, filters)
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    
    fileIndex = 0
    fileCount = len(files['include'])
    
    rsyncPasswordFilePath = os.path.join(tmpdir, 'passwordFile')

    try:
        rsyncPasswordFile = open(rsyncPasswordFilePath, 'w')
        rsyncPasswordFile.write(worker.cruiseDataTransfer['rsyncPass'])

    except IOError:
        errPrint("Error Saving temporary rsync password file")
        rsyncPasswordFile.close()

        # Cleanup
        shutil.rmtree(tmpdir)

        return False

    finally:
        rsyncPasswordFile.close()
        os.chmod(rsyncPasswordFilePath, 0600)
    
    rsyncFileListPath = os.path.join(tmpdir, 'rsyncFileList.txt')
        
    try:
        rsyncFileListFile = open(rsyncFileListPath, 'w')
        rsyncFileListFile.write('\n'.join([str(x) for x in files['include']]))

    except IOError:
        errPrint("Error Saving temporary rsync filelist file")
        rsyncFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return False

    finally:
        rsyncFileListFile.close()
    
    command = ['rsync', '-tri', '--no-motd', '--files-from=' + rsyncFileListPath, '--password-file=' + rsyncPasswordFilePath, sourceDir, 'rsync://' + worker.cruiseDataTransfer['rsyncUser'] + '@' + worker.cruiseDataTransfer['rsyncServer'] + destDir + '/']
    
    s = ' '
    debugPrint('Transfer Command:', s.join(command))

    popen = subprocess.Popen(command, stdout=subprocess.PIPE)

    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #debugPrint('line', line.rstrip('\n'))
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['new'].append(filename)
            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['updated'].append(filename)
            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
            
        if worker.stop:
            debugPrint("Stopping")
            break

    files['new'] = [os.path.join(baseDir,filename) for filename in files['new']]
    files['updated'] = [os.path.join(baseDir,filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return files


def transfer_sshDestDir(worker, job):

    debugPrint("Transfer from SSH Server")

    filters = {'includeFilter': '*','excludeFilter': '','ignoreFilter': ''}

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    
    sourceDir = cruiseDir
    destDir = worker.cruiseDataTransfer['destDir'].rstrip('/')
    
    debugPrint("Source Dir:", sourceDir)
    debugPrint("Destinstation Dir:", destDir)

    debugPrint("Build file list")
    files = build_filelist(sourceDir, filters)
        
    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    sshFileListPath = os.path.join(tmpdir, 'sshFileList.txt')
    
    fileIndex = 0
    fileCount = len(files['include'])

    try:
        sshFileListFile = open(sshFileListPath, 'w')
        sshFileListFile.write('\n'.join([worker.cruiseID + '/' + str(x) for x in files['include']]))

    except IOError:
        errPrint("Error Saving temporary ssh filelist file")
        sshFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return False

    finally:
        sshFileListFile.close()

    comand = ''

    if worker.cruiseDataTransfer['sshUseKey'] == '1':
        command = ['rsync', '-tri', '--files-from=' + sshFileListPath, '-e', 'ssh', baseDir, worker.cruiseDataTransfer['sshUser'] + '@' + worker.cruiseDataTransfer['sshServer'] + ':' + destDir]        
    else:
        command = ['sshpass', '-p', worker.cruiseDataTransfer['sshPass'], 'rsync', '-tri', '--files-from=' + sshFileListPath, '-e', 'ssh', baseDir, worker.cruiseDataTransfer['sshUser'] + '@' + worker.cruiseDataTransfer['sshServer'] + ':' + destDir]
    
    s = ' '
    debugPrint('Transfer Command:',s.join(command))
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
   
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #debugPrint('line', line.rstrip('\n'))
        if line.startswith( '<f+++++++++' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['new'].append(filename)
            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
        elif line.startswith( '<f.' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['updated'].append(filename)
            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
            
        if worker.stop:
            debugPrint("Stopping")
            break

    files['new'] = [os.path.join(baseDir,filename) for filename in files['new']]
    files['updated'] = [os.path.join(baseDir,filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return files


def transfer_nfsDestDir(worker, job):
    
    debugPrint("Transfer from NFS Server")

    filters = {'includeFilter': '*','excludeFilter': '','ignoreFilter': ''}

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    mntPoint = os.path.join(tmpdir, 'mntpoint')
    os.mkdir(mntPoint, 0755)

    debugPrint("Mount NFS Server")

    command = ['sudo', 'mount', '-t', 'nfs', worker.cruiseDataTransfer['nfsServer'], mntPoint, '-o', 'rw' + ',vers=2' + ',hard' + ',intr']

    s = ' '
    debugPrint('Mount Command:', s.join(command))

    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    proc.communicate()

    sourceDir = cruiseDir
    destDir = os.path.join(mntPoint,worker.cruiseDataTransfer['destDir'].rstrip('/')).rstrip('/')

    debugPrint("Build file list")
    files = build_filelist(sourceDir, filters)
    
    fileIndex = 0
    fileCount = len(files['include'])
    
    rsyncFileListPath = os.path.join(tmpdir, 'rsyncFileList.txt')
        
    try:
        rsyncFileListFile = open(rsyncFileListPath, 'w')
        rsyncFileListFile.write('\n'.join([worker.cruiseID + '/' + str(x) for x in files['include']]))

    except IOError:
        errPrint("Error Saving temporary rsync filelist file")
        rsyncFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return False

    finally:
        rsyncFileListFile.close()
    
    command = ['rsync', '-rlptDi', '--files-from=' + rsyncFileListPath, sourceDir, destDir]
    
    s = ' '
    debugPrint('Transfer Command:', s.join(command))
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)

    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #debugPrint('line', line.rstrip('\n'))
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['new'].append(filename)
            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['updated'].append(filename)
            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
            
        if worker.stop:
            debugPrint("Stopping")
            break

    files['new'] = [os.path.join(baseDir,filename) for filename in files['new']]
    files['updated'] = [os.path.join(baseDir,filename) for filename in files['updated']]

    # Cleanup
    debugPrint('Unmounting NFS Share')
    subprocess.call(['sudo', 'umount', mntPoint])
    shutil.rmtree(tmpdir)

    return files
    
        
class OVDMGearmanWorker(gearman.GearmanWorker):

    def __init__(self):
        self.stop = False
        self.quit = False
        self.OVDM = openvdm.OpenVDM()
        self.cruiseID = ''
        self.systemStatus = ''
        self.cruiseDataTransfer = {}
        self.shipboardDataWarehouseConfig = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])
        
        
    def on_job_execute(self, current_job):
        payloadObj = json.loads(current_job.data)
        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()
        self.cruiseDataTransfer = self.OVDM.getCruiseDataTransfer(payloadObj['cruiseDataTransfer']['cruiseDataTransferID'])
        self.cruiseDataTransfer.update(payloadObj['cruiseDataTransfer'])
        
        self.cruiseID = self.OVDM.getCruiseID()
        self.systemStatus = self.OVDM.getSystemStatus()
        if len(payloadObj) > 0:
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

        errPrint("Job:", current_job.handle + ",", self.cruiseDataTransfer['name'], "transfer started at:  ", time.strftime("%D %T", time.gmtime()))
        
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)

    
    def on_job_exception(self, current_job, exc_info):
        errPrint("Job:", current_job.handle + ",", self.cruiseDataTransfer['name'], "transfer failed at:  ", time.strftime("%D %T", time.gmtime()))
        
        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail"}]))
        self.OVDM.setError_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'], 'Reason: Worker crashed')
        
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        errPrint(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)

    
    def on_job_complete(self, current_job, job_results):
        resultsObj = json.loads(job_results)
        
        # If the last part of the results failed
        if len(resultsObj['parts']) > 0:
            if resultsObj['parts'][-1]['result'] == "Fail": # Final Verdict
                if resultsObj['parts'][-1]['partName'] != "Transfer In-Progress": # A failed Transfer in-progress test should not cause an error.
                    for test in resultsObj['parts']:
                        if test['result'] == "Fail":
                            self.OVDM.setError_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'], 'Reason: ' +  test['partName'])
                            break
            else:
                self.OVDM.setIdle_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'])
        else:
            self.OVDM.setIdle_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'])

        debugPrint('Job Results:', json.dumps(resultsObj, indent=2))

        errPrint("Job:", current_job.handle + ",", self.cruiseDataTransfer['name'], "transfer completed at:  ", time.strftime("%D %T", time.gmtime()))
            
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

        
        
def task_runCruiseDataTransfer(worker, job):

    time.sleep(randint(0,5))
    
    job_results = {'parts':[], 'files':[]}

    if worker.cruiseDataTransfer['status'] != "1": #running
        debugPrint("Transfer is not already in-progress")
        job_results['parts'].append({"partName": "Transfer In-Progress", "result": "Pass"})
    else:
        debugPrint("Transfer is already in-progress")
        job_results['parts'].append({"partName": "Transfer In-Progress", "result": "Fail"})
        return json.dumps(job_results)

    if worker.cruiseDataTransfer['enable'] == "1" and worker.systemStatus == "On":
        debugPrint("Transfer Enabled")
        job_results['parts'].append({"partName": "Transfer Enabled", "result": "Pass"})
    else:
        debugPrint("Transfer Disabled")
        return json.dumps(job_results)

    #debugPrint("Set transfer status to 'Running'")
    worker.OVDM.setRunning_cruiseDataTransfer(worker.cruiseDataTransfer['cruiseDataTransferID'], os.getpid(), job.handle)
    
    debugPrint("Testing configuration")
    worker.send_job_status(job, 1, 10)

    gm_client = gearman.GearmanClient([worker.OVDM.getGearmanServer()])
    
    gmData = {}
    gmData['cruiseDataTransfer'] = worker.cruiseDataTransfer
    gmData['cruiseID'] = worker.cruiseID
    
    completed_job_request = gm_client.submit_job("testCruiseDataTransfer", json.dumps(gmData))
    resultsObj = json.loads(completed_job_request.result)

    debugPrint('Connection Test Results:', json.dumps(resultsObj, indent=2))

    if resultsObj['parts'][-1]['result'] == "Pass": # Final Verdict
        debugPrint("Connection Test: Passed")
        job_results['parts'].append({'partName': 'Connection Test', 'result': 'Pass'})
    else:
        debugPrint("Connection Test: Failed")
        job_results['parts'].append({'partName': 'Connection Test', 'result': 'Fail'})
        return json.dumps(job_results)

    worker.send_job_status(job, 2, 10)
    
    debugPrint("Start Transfer")
    if worker.cruiseDataTransfer['transferType'] == "1": # Local Directory
        job_results['files'] = transfer_localDestDir(worker, job)
    elif  worker.cruiseDataTransfer['transferType'] == "2": # Rsync Server
        job_results['files'] = transfer_rsyncDestDir(worker, job)
    elif  worker.cruiseDataTransfer['transferType'] == "3": # SMB Server
        job_results['files'] = transfer_smbDestDir(worker, job)
    elif  worker.cruiseDataTransfer['transferType'] == "4": # SSH Server
        job_results['files'] = transfer_sshDestDir(worker, job)
    elif  worker.cruiseDataTransfer['transferType'] == "5": # NFS Server
        job_results['files'] = transfer_nfsDestDir(worker, job)

    debugPrint("Transfer Complete")
    if len(job_results['files']['new']) > 0:
        debugPrint(len(job_results['files']['new']), 'file(s) added')
    if len(job_results['files']['updated']) > 0:
        debugPrint(len(job_results['files']['updated']), 'file(s) updated')
    if len(job_results['files']['exclude']) > 0:
        debugPrint(len(job_results['files']['exclude']), 'misnamed file(s) encounted')

    job_results['parts'].append({"partName": "Transfer Files", "result": "Pass"})

    worker.send_job_status(job, 9, 10)

    time.sleep(5)

    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Main function of the script should it be run as a stand-alone utility.
# -------------------------------------------------------------------------------------
def main(argv):

    parser = argparse.ArgumentParser(description='Handle cruise data transfer related tasks')
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

    new_worker.set_client_id('runCruiseDataTransfer.py')

    debugPrint('Registering worker tasks...')
    debugPrint('   Task:', 'runCruiseDataTransfer')
    new_worker.register_task("runCruiseDataTransfer", task_runCruiseDataTransfer)

    debugPrint('Waiting for jobs...')
    new_worker.work()


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])
