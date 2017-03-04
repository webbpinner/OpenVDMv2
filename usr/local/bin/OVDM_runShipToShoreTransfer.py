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
#      VERSION:  2.2
#      CREATED:  2015-01-01
#     REVISION:  2015-10-30
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
import calendar
import fnmatch
import subprocess
import signal
import pwd
import grp
import openvdm
from random import randint

DEBUG = False
new_worker = None


def debugPrint(*args, **kwargs):
    if DEBUG:
        errPrint(*args, **kwargs)


def errPrint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def build_filelist(worker):

    debugPrint("Building filters")
    rawFilters = {'includeFilter':[]}
    shipToShoreTransfers = []
    shipToShoreTransfers += worker.OVDM.getShipToShoreTransfers()
    shipToShoreTransfers += worker.OVDM.getRequiredShipToShoreTransfers()

    #debugPrint('shipToShoreTransfers:',json.dumps(shipToShoreTransfers, indent=2))
    
    for x in range(1, 6):
        for shipToShoreTransfer in shipToShoreTransfers:
            if shipToShoreTransfer['priority'] == str(x):
                if shipToShoreTransfer['enable'] == '1':
                    if not shipToShoreTransfer['collectionSystem'] == "0":
                        collectionSystem = worker.OVDM.getCollectionSystemTransfer(shipToShoreTransfer['collectionSystem'])
                        shipToShoreFilters = shipToShoreTransfer['includeFilter'].split(',')
                        shipToShoreFilters = ['*/' + worker.cruiseID + '/' + collectionSystem['destDir'] + '/' + shipToShoreFilter for shipToShoreFilter in shipToShoreFilters]
                        rawFilters['includeFilter'] = rawFilters['includeFilter'] + shipToShoreFilters
                    elif not shipToShoreTransfer['extraDirectory'] == "0":
                        extraDirectory = worker.OVDM.getExtraDirectory(shipToShoreTransfer['extraDirectory'])
                        shipToShoreFilters = shipToShoreTransfer['includeFilter'].split(',')
                        shipToShoreFilters = ['*/' + worker.cruiseID + '/' + extraDirectory['destDir'] + '/' + shipToShoreFilter for shipToShoreFilter in shipToShoreFilters]
                        rawFilters['includeFilter'] = rawFilters['includeFilter'] + shipToShoreFilters
                    else:
                        shipToShoreFilters = shipToShoreTransfer['includeFilter'].split(',')
                        shipToShoreFilters = ['*/' + worker.cruiseID + '/' + shipToShoreFilter for shipToShoreFilter in shipToShoreFilters]
                        rawFilters['includeFilter'] = rawFilters['includeFilter'] + shipToShoreFilters

    #debugPrint("Raw Filters:", json.dumps(rawFilters, indent=2))
    
    procfilters = build_filters(worker, rawFilters)
    #debugPrint("Processed Filters:", json.dumps(rawFilters, indent=2))

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)

    returnFiles = {'include':[], 'new':[], 'updated':[]}
    for includeFilter in procfilters['includeFilter']:
        for root, dirnames, filenames in os.walk(cruiseDir):
            for filename in filenames:
                if fnmatch.fnmatch(os.path.join(root, filename), includeFilter):
                    returnFiles['include'].append(os.path.join(root, filename))

    returnFiles['include'] = [filename.replace(baseDir + '/', '', 1) for filename in returnFiles['include']]
    return returnFiles


def build_destDirectories(destDir, files):
    files = [filename.replace(filename, destDir + filename, 1) for filename in files]

    for dirname in set(os.path.dirname(p) for p in files):
        if not os.path.isdir(dirname):
            debugPrint("Creating Directory:", dirname)
            os.makedirs(dirname)


def build_logfileDirPath(worker):

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    warehouseTransferLogDir = os.path.join(cruiseDir, worker.OVDM.getRequiredExtraDirectoryByName('Transfer Logs')['destDir'])

    #debugPrint('warehouseTransferLogDir', warehouseTransferLogDir)
    
    return warehouseTransferLogDir


def build_filters(worker, rawFilters):

    returnFilters = rawFilters
    returnFilters['includeFilter'] = [includeFilter.replace('{cruiseID}', worker.cruiseID) for includeFilter in returnFilters['includeFilter']]
    return returnFilters


def setOwnerGroupPermissions(worker, path):

    warehouseUser = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']

    debugPrint(path)

    uid = pwd.getpwnam(warehouseUser).pw_uid
    gid = grp.getgrnam(warehouseUser).gr_gid
    # Set the file permission and ownership for the current directory

    if os.path.isfile(path):
        try:
            debugPrint("Setting ownership for", path, "to", warehouseUser + ":" + warehouseUser)
            os.chown(path, uid, gid)
            os.chmod(path, 0644)
        except OSError:
            errPrint("Unable to set file permissions for", path)
            return False
    else: #directory
        try:
            debugPrint("Setting ownership for", path, "to", warehouseUser + ":" + warehouseUser)
            os.chown(path, uid, gid)
            os.chmod(path, 0755)
        except OSError:
            errPrint("Unable to set file permissions for", fname)
            return False
        for root, dirs, files in os.walk(path):
            for file in files:
                fname = os.path.join(root, file)
                try:
                    debugPrint("Setting ownership for", file, "to", warehouseUser + ":" + warehouseUser)
                    os.chown(fname, uid, gid)
                    os.chmod(fname, 0644)
                except OSError:
                    errPrint("Unable to set file permissions for", fname)
                    return False

            for momo in dirs:
                dname = os.path.join(root, momo)
                try:
                    debugPrint("Setting ownership for", momo, "to", warehouseUser + ":" + warehouseUser)
                    os.chown(dname, uid, gid)
                    os.chmod(dname, 0755)
                except OSError:
                    errPrint("Unable to set file permissions for", dname)
                    return False

    return True

def writeLogFile(worker, logfileName, fileList):

    logfileDir = build_logfileDirPath(worker)
    #debugPrint('logfileDir', logfileDir)
    logfilePath = os.path.join(logfileDir, logfileName)
    
    try:
        #print "Open MD5 Summary MD5 file"
        Logfile = open(logfilePath, 'w')

        #print "Saving MD5 Summary MD5 file"
        Logfile.write(json.dumps(fileList))

    except IOError:
        errPrint("Error Saving transfer logfile")
        return False

    finally:
        #print "Closing MD5 Summary MD5 file"
        Logfile.close()
        setOwnerGroupPermissions(worker, logfilePath)

    return True
            
    
def transfer_sshDestDir(worker, job):

    debugPrint("Transfer from SSH Server")

    filters = {'includeFilter': '*','excludeFilter': '','ignoreFilter': ''}

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    
    sourceDir = cruiseDir
    destDir = worker.cruiseDataTransfer['destDir'].rstrip('/')
    
    #debugPrint("Source Dir:", sourceDir)
    #debugPrint("Destination Dir:", destDir)

    debugPrint("Build file list")
    files = build_filelist(worker)
        
    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    sshFileListPath = os.path.join(tmpdir, 'sshFileList.txt')
    
    fileIndex = 0
    fileCount = len(files['include'])

    try:
        sshFileListFile = open(sshFileListPath, 'w')
        sshFileListFile.write('\n'.join(files['include']))

    except IOError:
        errPrint("Error Saving temporary ssh filelist file")
        sshFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return False

    finally:
        sshFileListFile.close()
    
    command = ['sshpass', '-p', worker.cruiseDataTransfer['sshPass'], 'rsync', '-tri', '--files-from=' + sshFileListPath, '-e', 'ssh', baseDir, worker.cruiseDataTransfer['sshUser'] + '@' + worker.cruiseDataTransfer['sshServer'] + ':' + destDir]
#    command = ['sshpass', '-p', worker.cruiseDataTransfer['sshPass'], 'rsync', '-tri', '--files-from=' + sshFileListPath, '-e', 'ssh -c arcfour', baseDir, worker.cruiseDataTransfer['sshUser'] + '@' + worker.cruiseDataTransfer['sshServer'] + ':' + destDir]
    
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

#    files['new'] = [os.path.join(baseDir,filename) for filename in files['new']]
#    files['updated'] = [os.path.join(baseDir,filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return files

        
class OVDMGearmanWorker(gearman.GearmanWorker):

    def __init__(self):
        self.stop = False
        self.quit = False
        self.OVDM = openvdm.OpenVDM()
        self.cruiseID = ''
        self.transferStartDate = ''
        self.systemStatus = ''
        self.cruiseDataTransfer = {}
        self.shipboardDataWarehouseConfig = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])
    
    def getShipToShoreTransfer(self):
        cruiseDataTransfers = self.OVDM.getRequiredCruiseDataTransfers()
        for cruiseDataTransfer in cruiseDataTransfers:
            if cruiseDataTransfer['name'] == 'SSDW':
                return cruiseDataTransfer
        
        return {}
        
    def on_job_execute(self, current_job):
        payloadObj = json.loads(current_job.data)
        #debugPrint("Payload:", json.dumps(payloadObj))
        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()
        self.cruiseDataTransfer = self.getShipToShoreTransfer()
        
        self.cruiseID = self.OVDM.getCruiseID()
        self.transferStartDate = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        self.systemStatus = self.OVDM.getSystemStatus()
        
        if len(payloadObj) > 0:

            try:
                payloadObj['cruiseDataTransfer']
            except KeyError:
                self.cruiseDataTransfer = self.getShipToShoreTransfer()
            else:
               self.cruiseDataTransfer.update(payloadObj['cruiseDataTransfer'])

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
        self.OVDM.setError_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'], "Worker Crashed")
        
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        errPrint(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)
    
    def on_job_complete(self, current_job, job_results):
        resultsObj = json.loads(job_results)
        
        # If the last part of the results failed
        if len(resultsObj['parts']) > 0:
            if resultsObj['parts'][-1]['result'] == "Fail": # Final Verdict
                if resultsObj['parts'][-1]['partName'] != 'Transfer In-Progress': # only if the part names are not these is there a problem
                    self.OVDM.setError_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'])
            else:
                self.OVDM.setIdle_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'])
        else:
            self.OVDM.setIdle_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'])

        debugPrint('Job Results:', json.dumps(resultsObj['parts'], indent=2))

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

        
def task_runShipToShoreTransfer(worker, job):

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

    #debugPrint('Connection Test Results:', json.dumps(resultsObj['parts'], indent=2))

    if resultsObj['parts'][-1]['result'] == "Pass": # Final Verdict
        debugPrint("Connection Test: Passed")
        job_results['parts'].append({'partName': 'Connection Test', 'result': 'Pass'})
    else:
        debugPrint("Connection Test: Failed")
        job_results['parts'].append({'partName': 'Connection Test', 'result': 'Fail'})
        return json.dumps(job_results)

    worker.send_job_status(job, 2, 10)
    
    debugPrint("Start Transfer")
    if  worker.cruiseDataTransfer['transferType'] == "4": # SSH Server
        job_results['files'] = transfer_sshDestDir(worker, job)

        debugPrint("Transfer Complete")
        if len(job_results['files']['new']) > 0:
            debugPrint(len(job_results['files']['new']), 'file(s) added')
        if len(job_results['files']['updated']) > 0:
            debugPrint(len(job_results['files']['updated']), 'file(s) updated')

        job_results['parts'].append({"partName": "Transfer Files", "result": "Pass"})
    else:
        errPrint("Error: Unknown Transfer Type")
        job_results['parts'].append({"partName": "Transfer Files", "result": "Fail"})
        return json.dumps(job_results)
    
    worker.send_job_status(job, 9, 10)
    
    if job_results['files']['new'] or job_results['files']['updated']:
    
        debugPrint("Building Logfiles")

        warehouseTransferLogDir = build_logfileDirPath(worker)

        if warehouseTransferLogDir:
    
            logfileName = worker.cruiseDataTransfer['name'] + '_' + worker.transferStartDate + '.log'
            
            logContents = {'files':{'new':[], 'updated':[]}}
            logContents['files']['new'] = job_results['files']['new']
            logContents['files']['updated'] = job_results['files']['updated']
            #debugPrint('logContents',logContents)
            
            if writeLogFile(worker, logfileName, logContents['files']):
                job_results['parts'].append({"partName": "Write transfer logfile", "result": "Pass"})
            else:
                job_results['parts'].append({"partName": "Write transfer logfile", "result": "Fail"})
                return job_results
        else:
            job_results['parts'].append({"partName": "Write transfer logfile", "result": "Fail"})

    worker.send_job_status(job, 10, 10)
    
    time.sleep(5)

    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Main function of the script should it be run as a stand-alone utility.
# -------------------------------------------------------------------------------------
def main(argv):

    parser = argparse.ArgumentParser(description='Handle Ship-to-Shore transfer related tasks')
    parser.add_argument('-d', '--debug', action='store_true', help=' display debug messages')

    args = parser.parse_args()
    if args.debug:
        global DEBUG
        DEBUG = True
        debugPrint("Running in debug mode")

    debugPrint('Creating Worker...')
    global new_worker
    new_worker = OVDMGearmanWorker()

    def sigquit_handler(_signo, _stack_frame):
        errPrint("QUIT Signal Received")
        new_worker.stopTransfer()

        
    def sigint_handler(_signo, _stack_frame):
        errPrint("INT Signal Received")
        new_worker.quitWorker()
        
        
    signal.signal(signal.SIGQUIT, sigquit_handler)
    signal.signal(signal.SIGINT, sigint_handler)

    new_worker.set_client_id('runShipToShoreTransfer.py')

    debugPrint('Registering worker tasks...')
    debugPrint('   Task:', 'runShipToShoreTransfer')
    new_worker.register_task("runShipToShoreTransfer", task_runShipToShoreTransfer)

    debugPrint('Waiting for jobs...')
    new_worker.work()


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])
