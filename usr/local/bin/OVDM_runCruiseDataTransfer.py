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
#     REVISION:  2016-02-06
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
import fnmatch
import subprocess
import signal
import openvdm
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

def transfer_localDestDir(worker, job):

    #print "Transfer from Local Directory"
    filters = {'includeFilter': '*','excludeFilter': '','ignoreFilter': ''}
    
    sourceDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']+'/'+worker.cruiseID
    destDir = worker.cruiseDataTransfer['destDir'].rstrip('/') + '/'

    #print "Build file list"
    files = build_filelist(sourceDir, filters)
    
    count = 0
    fileCount = len(files['include'])
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncFileListPath = tmpdir + '/rsyncFileList.txt'
        
    try:
        #print "Open rsync password file"
        rsyncFileListFile = open(rsyncFileListPath, 'w')

        #print "Saving rsync password file"
        #print '\n'.join([worker.cruiseID + str(x) for x in files['include']])
        rsyncFileListFile.write('\n'.join([worker.cruiseID + str(x) for x in files['include']]))

    except IOError:
        print "Error Saving temporary rsync filelist file"
        #returnVal.append({"testName": "Writing temporary rsync password file", "result": "Fail"})
        rsyncFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return files    

    finally:
        #print "Closing rsync filelist file"
        rsyncFileListFile.close()
        #returnVal.append({"testName": "Writing temporary rsync password file", "result": "Pass"})
    
    
    command = ['rsync', '-tri', '--files-from=' + rsyncFileListPath, worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'], destDir]
    #print command
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #print(line) # yield line
        if line.startswith( '>f+++++++++' ):
            files['new'].append(line.split(' ')[1])
            count += 1
        elif line.startswith( '>f.' ):
            files['updated'].append(line.split(' ')[1])
            count += 1

        worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
            
        if worker.stop:
            print "Stopping"
            break
    
    # Cleanup
    shutil.rmtree(tmpdir)    
    return files

def transfer_smbDestDir(worker, job):
    
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
    if worker.cruiseDataTransfer['smbUser'] == 'guest':
        
        command = ['sudo', 'mount', '-t', 'cifs', worker.cruiseDataTransfer['smbServer'], mntPoint, '-o', 'rw' + ',guest' +  'domain=' + worker.cruiseDataTransfer['smbDomain']]
        
        #s = ' '
        #print s.join(command)

        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()
    else:
        command = ['sudo', 'mount', '-t', 'cifs', worker.cruiseDataTransfer['smbServer'], mntPoint, '-o', 'rw' + ',username=' + worker.cruiseDataTransfer['smbUser'] + ',password='+worker.cruiseDataTransfer['smbPass'] + ',domain='+worker.cruiseDataTransfer['smbDomain']]
        
        #s = ' '
        #print s.join(command)

        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

    sourceDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']+'/'+worker.cruiseID
    destDir = mntPoint+worker.cruiseDataTransfer['destDir'].rstrip('/') + '/'

    #print "Build file list"
    files = build_filelist(sourceDir, filters)
    
    #print "Build destination directories"
    #build_destDirectories(destDir, files['include'])

    count = 0
    fileCount = len(files['include'])
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncFileListPath = tmpdir + '/rsyncFileList.txt'
        
    try:
        #print "Open rsync password file"
        rsyncFileListFile = open(rsyncFileListPath, 'w')

        #print "Saving rsync password file"
        #print '\n'.join([worker.cruiseID + str(x) for x in files['include']])
        rsyncFileListFile.write('\n'.join([worker.cruiseID + str(x) for x in files['include']]))

    except IOError:
        print "Error Saving temporary rsync filelist file"
        #returnVal.append({"testName": "Writing temporary rsync password file", "result": "Fail"})
        rsyncFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return files    

    finally:
        #print "Closing rsync filelist file"
        rsyncFileListFile.close()
        #returnVal.append({"testName": "Writing temporary rsync password file", "result": "Pass"})
    
    
    command = ['rsync', '-rlptDi', '--files-from=' + rsyncFileListPath, worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'], destDir]
    
    #s = ' '
    #print s.join(command)
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #print(line) # yield line
        if line.startswith( '>f+++++++++' ):
            files['new'].append(line.split(' ')[1])
            count += 1
        elif line.startswith( '>f.' ):
            files['updated'].append(line.split(' ')[1])
            count += 1

        worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
            
        if worker.stop:
            print "Stopping"
            break
    
    #print "Unmount SMB Share"
    subprocess.call(['sudo', 'umount', mntPoint])
    
    #print "Cleanup"
    shutil.rmtree(tmpdir)

    #print 'DECODED Files:', json.dumps(files, indent=2)
    return files

def transfer_rsyncDestDir(worker, job):

    #print "Transfer from Rsync Server"
    filters = {'includeFilter': '*','excludeFilter': '','ignoreFilter': ''}

    sourceDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']+'/'+worker.cruiseID
    
    #print "Build file list"
    files = build_filelist(sourceDir, filters)
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    
    count = 0
    fileCount = len(files['include'])
    
    rsyncPasswordFilePath = tmpdir + '/passwordFile'

    try:
        #print "Open temporary rsync password file"
        rsyncPasswordFile = open(rsyncPasswordFilePath, 'w')

        #print "Saving temporary rsync password file"
        rsyncPasswordFile.write(worker.cruiseDataTransfer['rsyncPass'])

    except IOError:
        #print "Error Saving temporary rsync password file"
        returnVal.append({"testName": "Writing temporary rsync password file", "result": "Fail"})
        rsyncPasswordFile.close()

        # Cleanup
        shutil.rmtree(tmpdir)

        return returnVal    

    finally:
        #print "Closing temporary rsync password file"
        rsyncPasswordFile.close()
        os.chmod(rsyncPasswordFilePath, 0600)
        #returnVal.append({"testName": "Writing temporary rsync password file", "result": "Pass"})
    
    rsyncFileListPath = tmpdir + '/rsyncFileList.txt'
        
    try:
        #print "Open rsync password file"
        rsyncFileListFile = open(rsyncFileListPath, 'w')

        #print "Saving rsync password file"
        #print '\n'.join([worker.cruiseID + str(x) for x in files['include']])
        rsyncFileListFile.write('\n'.join([worker.cruiseID + str(x) for x in files['include']]))

    except IOError:
        print "Error Saving temporary rsync filelist file"
        returnVal.append({"testName": "Writing temporary rsync password file", "result": "Fail"})
        rsyncFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return files    

    finally:
        #print "Closing rsync filelist file"
        rsyncFileListFile.close()
        #returnVal.append({"testName": "Writing temporary rsync password file", "result": "Pass"})
    
    command = ['rsync', '-ti', '--no-motd', '--files-from=' + rsyncFileListPath, '--password-file=' + rsyncPasswordFilePath, 'rsync://' + worker.cruiseDataTransfer['rsyncUser'] + '@' + worker.cruiseDataTransfer['rsyncServer'] + sourceDir, destDir]
    
    #s = ' '
    #print s.join(command)
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #print(line) # yield line
        if line.startswith( '>f+++++++++' ):
            files['new'].append(line.split(' ')[1])
            count += 1
        elif line.startswith( '>f.' ):
            files['updated'].append(line.split(' ')[1])
            count += 1
        worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
            
        if worker.stop:
            print "Stopping"
            break
    
    # Cleanup
    shutil.rmtree(tmpdir)    
    return files

def transfer_sshDestDir(worker, job):

    #print "Transfer from SSH Server"
    filters = {'includeFilter': '*','excludeFilter': '','ignoreFilter': ''}

    sourceDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']+'/'+worker.cruiseID
    
    #print "Build file list"
    files = build_filelist(sourceDir, filters)
    
    count = 0
    fileCount = len(files['include'])
    
    # Create temp directory
    #print "Create Temp Directory"
    tmpdir = tempfile.mkdtemp()
    sshFileListPath = tmpdir + '/sshFileList.txt'
        
    try:
        #print "Open rsync password file"
        sshFileListFile = open(sshFileListPath, 'w')

        #print "Saving ssh filelist file"
        #print '\n'.join([worker.cruiseID + str(x) for x in files['include']])
        sshFileListFile.write('\n'.join([worker.cruiseID + str(x) for x in files['include']]))

    except IOError:
        print "Error Saving temporary ssh filelist file"
        returnVal.append({"testName": "Writing temporary ssh password file", "result": "Fail"})
        sshFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return files    

    finally:
        #print "Closing rsync filelist file"
        sshFileListFile.close()
        #returnVal.append({"testName": "Writing temporary ssh filelist file", "result": "Pass"})
    
    command = ['sshpass', '-p', worker.cruiseDataTransfer['sshPass'], 'rsync', '-aiv', '--files-from=' + sshFileListPath, '-e', 'ssh -c arcfour', worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'], worker.cruiseDataTransfer['sshUser'] + '@' + worker.cruiseDataTransfer['sshServer'] + ':' + worker.cruiseDataTransfer['destDir']]
    
    #s = ' '
    #print s.join(command)
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #print(line) # yield line
        if line.startswith( '>f+++++++++' ):
            files['new'].append(line.split(' ')[1])
            count += 1
        elif line.startswith( '>f.' ):
            files['updated'].append(line.split(' ')[1])
            count += 1
        worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
            
        if worker.stop:
            print "Stopping"
            break
    
    # Cleanup
    shutil.rmtree(tmpdir)    
    return files

def transfer_nfsDestDir(worker, job):
    
    #print "Transfer from NFS Server"
    filters = {'includeFilter': '*','excludeFilter': '','ignoreFilter': ''}

    # Create temp directory
    #print "Create Temp Directory"
    tmpdir = tempfile.mkdtemp()
 
    # Create mountpoint
    #print "Create Mountpoint"
    mntPoint = tmpdir + '/mntpoint'
    os.mkdir(mntPoint, 0755)

    # Mount SMB Share
    #print "Mount NFS Server"
    command = ['sudo', 'mount', '-t', 'nfs', worker.cruiseDataTransfer['nfsServer'], mntPoint, '-o', 'rw' + ',vers=2' + ',hard' + ',intr']

    #s = ' '
    #print s.join(command)

    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    proc.communicate()

    sourceDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']+'/'+worker.cruiseID
    destDir = mntPoint+worker.cruiseDataTransfer['destDir'].rstrip('/') + '/'

    #print "Build file list"
    files = build_filelist(sourceDir, filters)
    
    #print "Build destination directories"
    #build_destDirectories(destDir, files['include'])

    count = 0
    fileCount = len(files['include'])
    
    rsyncFileListPath = tmpdir + '/rsyncFileList.txt'
        
    try:
        #print "Open rsync password file"
        rsyncFileListFile = open(rsyncFileListPath, 'w')

        #print "Saving rsync password file"
        #print '\n'.join([worker.cruiseID + str(x) for x in files['include']])
        rsyncFileListFile.write('\n'.join([worker.cruiseID + str(x) for x in files['include']]))

    except IOError:
        print "Error Saving temporary rsync filelist file"
        #returnVal.append({"testName": "Writing temporary rsync password file", "result": "Fail"})
        rsyncFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return files    

    finally:
        #print "Closing rsync filelist file"
        rsyncFileListFile.close()
        #returnVal.append({"testName": "Writing temporary rsync password file", "result": "Pass"})
    
    # Copy files
    command = ['rsync', '-rlptDi', '--files-from=' + rsyncFileListPath, worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'], destDir]
    
    #s = ' '
    #print s.join(command)
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #print(line) # yield line
        if line.startswith( '>f+++++++++' ):
            files['new'].append(line.split(' ')[1])
            count += 1
        elif line.startswith( '>f.' ):
            files['updated'].append(line.split(' ')[1])
            count += 1

        worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
            
        if worker.stop:
            print "Stopping"
            break
    
    #print "Unmount NFS Server"
    subprocess.call(['sudo', 'umount', mntPoint])
    
    #print "Cleanup"
    shutil.rmtree(tmpdir)

    #print 'DECODED Files:', json.dumps(files, indent=2)
    return files
    
        
class OVDMGearmanWorker(gearman.GearmanWorker):

    def __init__(self, host_list=None):
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
        
        print "Job: " + current_job.handle + ", " + self.cruiseDataTransfer['name'] + " transfer started at:   " + time.strftime("%D %T", time.gmtime())
        
        #print self.shipboardDataWarehouseConfig
        #print self.cruiseDataTransfer
        #print self.cruiseID
        #print self.systemStatus

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
        
def task_runCruiseDataTransfer(worker, job):

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
    
    #print "Transfer Data"
    #print "TransferType: ", worker.cruiseDataTransfer['transferType']
    
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

    #print "Transfer Complete"
    worker.send_job_status(job, 9, 10)

    #print "Send transfer log" 
    worker.send_job_status(job, 10, 10)
    
    time.sleep(5)

    #print "DECODED: ", json.dumps(job_results)
    return json.dumps(job_results)

global new_worker
new_worker = OVDMGearmanWorker()

def sigquit_handler(_signo, _stack_frame):
    print "QUIT Signal Received"
    new_worker.stopTransfer()
    
def sigint_handler(_signo, _stack_frame):
    print "INT Signal Received"
    new_worker.quitWorker()
    
signal.signal(signal.SIGQUIT, sigquit_handler)
signal.signal(signal.SIGINT, sigint_handler)

new_worker.set_client_id('runCruiseDataTransfer.py')
new_worker.register_task("runCruiseDataTransfer", task_runCruiseDataTransfer)

new_worker.work()
