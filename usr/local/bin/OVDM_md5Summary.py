# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_md5Summary.py
#
#  DESCRIPTION:  Gearman worker tha handles the creation and update of an MD5 checksum
#                summary.
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.1
#      CREATED:  2015-01-01
#     REVISION:  2016-10-19
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
from __future__ import print_function
import argparse
import os
import sys
import gearman
import shutil
import json
import hashlib
import signal
import fnmatch
import pwd
import grp
import time
import openvdm

customTaskLookup = [
    {
        "taskID": "0",
        "name": "updateMD5Summary",
        "longName": "Updating MD5 Summary",
    }
]

DEBUG = False
new_worker = None

md5SummaryFN = 'MD5_Summary.txt'
md5SummaryMD5FN = 'MD5_Summary.md5'


def debugPrint(*args, **kwargs):
    global DEBUG
    if DEBUG:
        errPrint(*args, **kwargs)


def errPrint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def build_filelist(worker):

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)

    returnFiles = []
    for root, dirnames, filenames in os.walk(cruiseDir):
        for filename in filenames:
            if not filename == md5SummaryFN and not filename == md5SummaryMD5FN:
                returnFiles.append(os.path.join(root, filename))

    returnFiles = [filename.replace(baseDir + '/', '', 1) for filename in returnFiles]
    return returnFiles


def build_hashes(worker, job, fileList):

    #print sourceDir
    #print json.dumps(fileList, indent=2)

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)

    filesizeLimit = worker.OVDM.getMD5FilesizeLimit()
    filesizeLimitStatus = worker.OVDM.getMD5FilesizeLimitStatus() 

    hashes = []

    fileCount = len(fileList)
    index = 0
    for filename in fileList:
        #print filename
        if filesizeLimitStatus == 'On' and not filesizeLimit == '0':
            if os.stat(os.path.join(baseDir, filename)).st_size < int(filesizeLimit) * 1000000:
                hashes.append({'hash': hashlib.md5(os.path.join(baseDir, filename)).hexdigest(), 'filename': filename})
            else:
                #print 'Skipping File: ' + filename
                hashes.append({'hash': '********************************', 'filename': filename})
        else:
            hashes.append({'hash': hashlib.md5(os.path.join(baseDir, filename)).hexdigest(), 'filename': filename})

        worker.send_job_status(job, int(20 + 60*float(index)/float(fileCount)), 100)

        if worker.stop:
            debugPrint("Stopping")
            break

        index += 1

    return hashes


def setOwnerGroupPermissions(worker, path):

    warehouseUser = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']

    #debugPrint(path)

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
    elif os.path.isdir(path):
        os.chown(path, uid, gid)
        os.chmod(path, 0755)

        for item in os.listdir(path):
            itempath = os.path.join(path, item)
            if os.path.isdir(itempath):
                try:
                    if not setOwnerGroupPermissions(worker, itempath):
                        return False
                except OSError:
                    return False
            elif os.path.isfile(itempath):
                try:
                    debugPrint("Setting ownership for", itempath, "to", warehouseUser + ":" + warehouseUser)
                    os.chown(itempath, uid, gid)
                    os.chmod(itempath, 0644)
                except OSError:
                    errPrint("Unable to set file permissions for", itempath)
                    return False
    return True


def build_MD5Summary_MD5(worker):

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)

    md5SummaryFilepath = os.path.join(cruiseDir, md5SummaryFN)
    md5SummaryMD5Filepath = os.path.join(cruiseDir, md5SummaryMD5FN)
    md5SummaryMD5Hash = hashlib.md5(md5SummaryFilepath).hexdigest()
    
    try:
        #debugPrint("Opening MD5 Summary MD5 file")
        MD5SummaryMD5File = open(md5SummaryMD5Filepath, 'w')

        #debugPrint("Saving MD5 Summary MD5 file")
        MD5SummaryMD5File.write(md5SummaryMD5Hash)

    except IOError:
        errPrint("Error Saving MD5 Summary MD5 file")
        return False

    finally:
        MD5SummaryMD5File.close()
        setOwnerGroupPermissions(worker, md5SummaryMD5Filepath)

    return True


class OVDMGearmanWorker(gearman.GearmanWorker):
    
    def __init__(self, host_list=None):
        self.stop = False
        self.quit = False
        self.OVDM = openvdm.OpenVDM()
        self.cruiseID = ''
        self.shipboardDataWarehouseConfig = {}
        self.task = None
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])


    def get_task(self, current_job):
        tasks = self.OVDM.getTasks()
        for task in tasks:
            if task['name'] == current_job.task:
                self.task = task
                return True
        
        for task in customTaskLookup:
            if task['name'] == current_job.task:
                self.task = task
                return True

        self.task = None
        return False

    
    def on_job_execute(self, current_job):
        self.get_task(current_job)
        payloadObj = json.loads(current_job.data)
        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()

        self.cruiseID = self.OVDM.getCruiseID()
        if len(payloadObj) > 0:
            try:
                payloadObj['cruiseID']
            except KeyError:
                self.cruiseID = self.OVDM.getCruiseID()
            else:
                self.cruiseID = payloadObj['cruiseID']

        if int(self.task['taskID']) > 0:

            self.OVDM.setRunning_task(self.task['taskID'], os.getpid(), current_job.handle)
        else:
            self.OVDM.trackGearmanJob(self.task['longName'], os.getpid(), current_job.handle)

        errPrint("Job:", current_job.handle + ",", self.task['longName'], "started at:  ", time.strftime("%D %T", time.gmtime()))
        
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)


    def on_job_exception(self, current_job, exc_info):
        errPrint("Job:", current_job.handle + ",", self.task['longName'], "failed at:   ", time.strftime("%D %T", time.gmtime()))
        
        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail"}]))
        if int(self.task['taskID']) > 0:
            self.OVDM.setError_task(self.task['taskID'], "Worker crashed")
        else:
            self.OVDM.sendMsg(self.task['longName'] + ' failed', 'Worker crashed')
        
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        errPrint(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)

    
    def on_job_complete(self, current_job, job_results):
        resultsObj = json.loads(job_results)

        if len(resultsObj['parts']) > 0:
            if resultsObj['parts'][-1]['result'] == "Fail": # Final Verdict
                if int(self.task['taskID']) > 0:
                    self.OVDM.setError_task(self.task['taskID'], resultsObj['parts'][-1]['partName'])
                else:
                    self.OVDM.sendMsg(self.task['longName'] + ' failed', resultsObj['parts'][-1]['partName'])
            else:
                if int(self.task['taskID']) > 0:
                    self.OVDM.setIdle_task(self.task['taskID'])
        else:
            if int(self.task['taskID']) > 0:
                self.OVDM.setIdle_task(self.task['taskID'])
        
        debugPrint('Job Results:', json.dumps(resultsObj['parts'], indent=2))
            
        errPrint("Job:", current_job.handle + ",", self.task['longName'], "completed at:", time.strftime("%D %T", time.gmtime()))
            
        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_results)

    def after_poll(self, any_activity):
        self.stop = False
        self.taskID = '0'
        if self.quit:
            errPrint("Quitting")
            self.shutdown()
        else:
            self.quit - False
        return True


    def stopTask(self):
        self.stop = True
        debugPrint("Stopping current task...")


    def quitWorker(self):
        self.stop = True
        self.quit = True
        debugPrint("Quitting worker...")


def task_updateMD5Summary(worker, job):

    job_results = {'parts':[]}

    payloadObj = json.loads(job.data)
    debugPrint('Payload:', json.dumps(payloadObj, indent=2))

    worker.send_job_status(job, 1, 10)

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    md5SummaryFilepath = os.path.join(cruiseDir, md5SummaryFN)
    
    debugPrint("Building filelist")
    fileList = []
    
    if payloadObj['files']['new'] or payloadObj['files']['updated']:
        fileList = payloadObj['files']['new']
        fileList += payloadObj['files']['updated']
        job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Pass"})

    else:
        job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Pass"})
        return json.dumps(job_results)

    fileList = [worker.cruiseID + '/' + filename for filename in fileList]    
    debugPrint('File list:', json.dumps(fileList, indent=2))

    worker.send_job_status(job, 2, 10)

    debugPrint("Building hashes")
    newHashes = build_hashes(worker, job, fileList)    
    debugPrint('Hashes:', json.dumps(newHashes, indent=2))

    worker.send_job_status(job, 8, 10)
        
    if worker.stop:
        return json.dumps(job_results)
    else:
        job_results['parts'].append({"partName": "Calculate Hashes", "result": "Pass"})
    
    existingHashes = []

    debugPrint("Processing existing MD5 summary file")
    
    try:
        MD5SummaryFile = open(md5SummaryFilepath, 'r')

        for line in MD5SummaryFile:
            (md5Hash, filename) = line.split(' ', 1)
            existingHashes.append({'hash': md5Hash, 'filename': filename.rstrip('\n')})

    except IOError:
        errPrint("Error Reading MD5 Summary file")
        job_results['parts'].append({"partName": "Reading pre-existing MD5 Summary file", "result": "Fail"})
        return json.dumps(job_results)

    finally:
        MD5SummaryFile.close()
        #debugPrint('Existing Hashes:', json.dumps(existingHashes, indent=2))
        job_results['parts'].append({"partName": "Reading pre-existing MD5 Summary file", "result": "Pass"})

    row_added = 0
    row_updated = 0

    for newHash in newHashes:
        updated = False
        for existingHash in existingHashes:
            if newHash['filename'] == existingHash['filename']:
                existingHash['hash'] = newHash['hash']
                updated = True
                row_updated += 1
                break
        
        if not updated:
            existingHashes.append({'hash': newHash['hash'], 'filename': newHash['filename']})
            row_added += 1
        
    if row_added > 0:
        debugPrint(row_added, "row(s) added")
    if row_updated > 0:
        debugPrint(row_updated, "row(s) updated")

    worker.send_job_status(job, 85, 100)

    #debugPrint("Sorting hashes")
    sortedHashes = sorted(existingHashes, key=lambda hashes: hashes['filename'])

    debugPrint("Building MD5 Summary file")
    try:
        #print "Open MD5 Summary file"
        MD5SummaryFile = open(md5SummaryFilepath, 'w')

        #print "Saving MD5 Summary file"
        for filehash in sortedHashes:
            MD5SummaryFile.write(filehash['hash'] + ' ' + filehash['filename'] + '\n')

    except IOError:
        errPrint("Error updating MD5 Summary file")
        job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Fail"})
        MD5SummaryFile.close()
        return json.dumps(job_results)    

    finally:
        MD5SummaryFile.close()
        setOwnerGroupPermissions(worker, md5SummaryFilepath)
        job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Pass"})
    
    worker.send_job_status(job, 9, 10)

    debugPrint("Building MD5 Summary MD5 file")
    if build_MD5Summary_MD5(worker):
        job_results['parts'].append({"partName": "Writing MD5 Summary MD5 file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Writing MD5 Summary MD5 file", "result": "Fail"})

    worker.send_job_status(job, 10, 10)
    return json.dumps(job_results)
    
def task_rebuildMD5Summary(worker, job):

    job_results = {'parts':[]}

    payloadObj = json.loads(job.data)
    #print 'DECODED payloadObj:', json.dumps(payloadObj, indent=2)

    worker.send_job_status(job, 1, 10)
    
    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    md5SummaryFilepath = os.path.join(cruiseDir, md5SummaryFN)
    
    fileList = build_filelist(worker)
    debugPrint('Filelist:', json.dumps(fileList, indent=2))
    
    job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Pass"})
    
    worker.send_job_status(job, 2, 10)

    debugPrint("Building hashes")
    newHashes = build_hashes(worker, job, fileList)
    
    worker.send_job_status(job, 8, 10)
    
    if worker.stop:
        job_results['parts'].append({"partName": "Calculate Hashes", "result": "Fail"})
        return json.dumps(job_results)
    else:
        job_results['parts'].append({"partName": "Calculate Hashes", "result": "Pass"})
                
    sortedHashes = sorted(newHashes, key=lambda hashes: hashes['filename'])
    
    debugPrint("Building MD5 Summary file")
    try:
        #debugPrint("Saving new MD5 Summary file")
        MD5SummaryFile = open(md5SummaryFilepath, 'w')

        for filehash in sortedHashes:
            MD5SummaryFile.write(filehash['hash'] + ' ' + filehash['filename'] + '\n')

    except IOError:
        errPrint("Error saving MD5 Summary file")
        job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Fail"})
        MD5SummaryFile.close()
        return json.dumps(job_results)    

    finally:
        MD5SummaryFile.close()
        setOwnerGroupPermissions(worker, md5SummaryFilepath)
        job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Pass"})
    
    worker.send_job_status(job, 9, 10)

    debugPrint("Building MD5 Summary MD5 file")
    if build_MD5Summary_MD5(worker):
        job_results['parts'].append({"partName": "Writing MD5 Summary MD5 file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Writing MD5 Summary MD5 file", "result": "Fail"})

    worker.send_job_status(job, 10, 10)
    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Main function of the script should it be run as a stand-alone utility.
# -------------------------------------------------------------------------------------
def main(argv):

    parser = argparse.ArgumentParser(description='Handle MD5 Summary related tasks')
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

    new_worker.set_client_id('md5Summary.py')

    debugPrint('Registering worker tasks...')
    debugPrint('   Task:', 'updateMD5Summary')
    new_worker.register_task("updateMD5Summary", task_updateMD5Summary)
    debugPrint('   Task:', 'rebuildMD5Summary')
    new_worker.register_task("rebuildMD5Summary", task_rebuildMD5Summary)

    debugPrint('Waiting for jobs...')
    new_worker.work()

# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])
