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
#      VERSION:  2.0
#      CREATED:  2015-01-01
#     REVISION:  2016-02-05
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

taskLookup = {
    "rebuildMD5Summary": "Rebuild MD5 Summary",
    "updateMD5Summary": "Update MD5 Summary"
}

md5SummaryFN = 'MD5_Summary.txt'
md5SummaryMD5FN = 'MD5_Summary.md5'


def build_filelist(sourceDir):

    returnFiles = []
    for root, dirnames, filenames in os.walk(sourceDir):
        for filename in filenames:
            if not filename == md5SummaryFN and not filename == md5SummaryMD5FN:
                returnFiles.append(os.path.join(root, filename))
                
    returnFiles = [filename.replace(sourceDir + '/', '', 1) for filename in returnFiles]
    return returnFiles


def build_hashes(sourceDir, worker, job, fileList):
    
    filesizeLimit = worker.OVDM.getMD5FilesizeLimit()
    filesizeLimitStatus = worker.OVDM.getMD5FilesizeLimitStatus() 
    
    hashes = []
    
    fileCount = len(fileList)
    index = 1
    for filename in fileList:
        #print filename
        if filesizeLimitStatus == 'On' and not filesizeLimit == '0':
            if os.stat(sourceDir+'/'+filename).st_size < int(filesizeLimit) * 1000000:
                hashes.append({'hash': hashlib.md5(sourceDir+'/'+filename).hexdigest(), 'filename': filename})
            else:
                #print 'Skipping File: ' + filename
                hashes.append({'hash': '********************************', 'filename': filename})
        else:
            hashes.append({'hash': hashlib.md5(sourceDir+'/'+filename).hexdigest(), 'filename': filename})
        
        worker.send_job_status(job, int(round(20 + (60*index/fileCount),0)), 100)

        if worker.stop:
            print "Stopping"
            break

        index += 1

    return hashes


def build_MD5Summary_MD5(cruiseDir, warehouseUser):
    md5SummaryFilepath = cruiseDir + '/' + md5SummaryFN
    md5SummaryMD5Filepath = cruiseDir + '/' + md5SummaryMD5FN
    md5SummaryMD5Hash = hashlib.md5(md5SummaryFilepath).hexdigest()
    
    try:
        #print "Open MD5 Summary MD5 file"
        MD5SummaryMD5File = open(md5SummaryMD5Filepath, 'w')

        #print "Saving MD5 Summary MD5 file"
        MD5SummaryMD5File.write(md5SummaryMD5Hash)

    except IOError:
        print "Error Saving MD5 Summary MD5 file"
        return False

    finally:
        #print "Closing MD5 Summary MD5 file"
        MD5SummaryMD5File.close()
        os.chown(md5SummaryMD5Filepath, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)

    return True


class OVDMGearmanWorker(gearman.GearmanWorker):
    
    def __init__(self, host_list=None):
        self.stop = False
        self.quit = False
        self.OVDM = openvdm.OpenVDM()
        self.cruiseID = ''
        self.taskID = '0'
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])

        
    def get_taskID(self, current_job):
        tasks = self.OVDM.getTasks()
        for task in tasks:
            if task['name'] == current_job.task:
                self.taskID = task['taskID']
                return True
        self.taskID = '0'
        return False

    
    def on_job_execute(self, current_job):
        self.get_taskID(current_job)
        payloadObj = json.loads(current_job.data)
        
        self.cruiseID = self.OVDM.getCruiseID()
        if len(payloadObj) > 0:
            try:
                payloadObj['cruiseID']
            except KeyError:
                self.cruiseID = self.OVDM.getCruiseID()
            else:
                self.cruiseID = payloadObj['cruiseID']
            
        if int(self.taskID) > 0:
            self.OVDM.setRunning_task(self.taskID, os.getpid(), current_job.handle)
        else:
            self.OVDM.trackGearmanJob(taskLookup[current_job.task], os.getpid(), current_job.handle)
            
        print "Job: " + current_job.handle + ", " + taskLookup[current_job.task] + " started at:   " + time.strftime("%D %T", time.gmtime())
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)
            

    def on_job_exception(self, current_job, exc_info):
        print "Job: " + current_job.handle + ", " + taskLookup[current_job.task] + " failed at:    " + time.strftime("%D %T", time.gmtime())
        
        self.send_job_data(current_job, json.dumps([{"partName": "Unknown Part of Task", "result": "Fail"}]))
        if int(self.taskID) > 0:
            self.OVDM.setError_task(self.taskID, "Unknown Part of Task")
        else:
            self.OVDM.sendMsg(taskLookup[current_job.task] + ' failed: Unknown Part of Task')
        
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)

    
    def on_job_complete(self, current_job, job_result):
        resultObj = json.loads(job_result)
        
        if len(resultObj['parts']) > 0:
            if resultObj['parts'][-1]['result'] == "Fail": # Final Verdict
                if int(self.taskID) > 0:
                    self.OVDM.setError_task(self.taskID, resultObj['parts'][-1]['partName'])
                else:
                    self.OVDM.sendMsg(taskLookup[current_job.task] + ' failed: ' + resultObj['parts'][-1]['partName'])
            else:
                self.OVDM.setIdle_task(self.taskID)
        else:
            self.OVDM.setIdle_task(self.taskID)    
            
        print "Job: " + current_job.handle + ", " + taskLookup[current_job.task] + " completed at: " + time.strftime("%D %T", time.gmtime())
            
        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_result)

    
    def after_poll(self, any_activity):
        self.stop = False
        self.taskID = '0'
        if self.quit:
            print "Quitting"
            self.shutdown()
        else:
            self.quit - False
        return True
    
    
    def stopTask(self):
        self.stop = True

        
    def quitWorker(self):
        self.stop = True
        self.quit = True


def task_updateMD5Summary(worker, job):

    job_results = {'parts':[]}

    payloadObj = json.loads(job.data)
    #print 'DECODED:', json.dumps(payloadObj, indent=2)

    worker.send_job_status(job, 1, 10)

    shipboardDataWarehouseConfig = worker.OVDM.getShipboardDataWarehouseConfig()
    baseDir = shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = baseDir + '/' + worker.cruiseID
    warehouseUser = shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    md5SummaryFilepath = cruiseDir + '/' + md5SummaryFN
    
    #build filelist
    fileList = []
    
    if payloadObj['files']['new'] or payloadObj['files']['updated']:
        fileList = payloadObj['files']['new']
        fileList += payloadObj['files']['updated']
        job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Pass"})

    else:
        job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Pass"})
        #print "No new or updated files to process"
        return json.dumps(job_results)
    
    worker.send_job_status(job, 2, 10)
    #print 'DECODED:', json.dumps(fileList, indent=2)
    
    newHashes = build_hashes(cruiseDir, worker, job, fileList)

    #print 'DECODED newHashes:', json.dumps(newHashes, indent=2)
    worker.send_job_status(job, 8, 10)
        
    if worker.stop:
        #job_results['parts'].append({"partName": "Calculate Hashes", "result": "Fail"})
        return json.dumps(job_results)
    else:
        job_results['parts'].append({"partName": "Calculate Hashes", "result": "Pass"})
    
    existingHashes = []
    
    try:
        #print "Open MD5 Summary file: " + md5SummaryFilepath
        MD5SummaryFile = open(md5SummaryFilepath, 'r')

        for line in MD5SummaryFile:
            #print line.rstrip('\n')
            (md5Hash, filename) = line.split(' ', 1)
            #print md5Hash + ', ' + filename
            existingHashes.append({'hash': md5Hash, 'filename': filename.rstrip('\n')})

    except IOError:
        print "Error Reading MD5 Summary file"
        job_results['parts'].append({"partName": "Reading pre-existing MD5 Summary file", "result": "Fail"})
        return json.dumps(job_results)

    finally:
        #print "Closing MD5 Summary file"
        MD5SummaryFile.close()
        job_results['parts'].append({"partName": "Reading pre-existing MD5 Summary file", "result": "Pass"})
        #print 'DECODED existingHashes:', json.dumps(existingHashes, indent=2)

    #worker.send_job_status(job, 8, 10)
    #print 'DECODED existingHashes:', json.dumps(existingHashes, indent=2)
    
    for newRow in newHashes:
        updated = False
        for existingRow in existingHashes:
            if worker.cruiseID + '/' + newRow['filename'] == existingRow['filename']:
                #print "Row Updated"
                existingRow['hash'] = newRow['hash']
                updated = True
                break
        
        if not updated:
            #print "Row Added"
            existingHashes.append({'hash': newRow['hash'], 'filename': worker.cruiseID + '/' + newRow['filename']})
        
    #print 'DECODED updatedHashes:', json.dumps(existingHashes, indent=2)
    worker.send_job_status(job, 85, 100)
    
    try:
        #print "Open MD5 Summary file"
        MD5SummaryFile = open(md5SummaryFilepath, 'w')

        #print "Saving MD5 Summary file"
        #sorted(student_tuples, key=itemgetter(2))
        for filehash in sorted(existingHashes, key=lambda hashes: hashes['filename']):
            MD5SummaryFile.write(filehash['hash'] + ' ' + filehash['filename'] + '\n')

    except IOError:
        print "Error Saving MD5 Summary file"
        job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Fail"})
        MD5SummaryFile.close()
        return json.dumps(job_results)    

    finally:
        #print "Closing MD5 Summary file"
        MD5SummaryFile.close()
        os.chown(md5SummaryFilepath, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)
        job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Pass"})
        
    worker.send_job_status(job, 9, 10)

    #print "Building MD5 Summary MD5 file"
    if build_MD5Summary_MD5(cruiseDir, warehouseUser):
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
    
    shipboardDataWarehouseConfig = worker.OVDM.getShipboardDataWarehouseConfig()
    baseDir = shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    warehouseUser = shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    cruiseDir = baseDir + '/' + worker.cruiseID
    md5SummaryFilepath = cruiseDir + '/' + md5SummaryFN
    
    fileList = build_filelist(cruiseDir)
    #print 'DECODED:', json.dumps(fileList, indent=2)
    
    job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Pass"})
    
    worker.send_job_status(job, 2, 10)

    hashes = build_hashes(cruiseDir, worker, job, fileList)
    #print 'DECODED:', json.dumps(hashes, indent=2)
    
    worker.send_job_status(job, 8, 10)
    
    if worker.stop:
        job_results['parts'].append({"partName": "Calculate Hashes", "result": "Fail"})
    else:
        job_results['parts'].append({"partName": "Calculate Hashes", "result": "Pass"})
                
        try:
            #print "Open MD5 Summary file"
            MD5SummaryFile = open(md5SummaryFilepath, 'w')

            #print "Saving MD5 Summary file"
            for filehash in hashes:
                MD5SummaryFile.write(filehash['hash'] + ' ' + worker.cruiseID + '/' + filehash['filename'] + '\n')
                
        except IOError:
            print "Error Saving MD5 Summary file"
            job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Fail"})
            MD5SummaryFile.close()
            return json.dumps(job_results)

        finally:
            #print "Closing MD5 Summary file"
            MD5SummaryFile.close()
            os.chown(md5SummaryFilepath, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)
            job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Pass"})
            
        worker.send_job_status(job, 9, 10)
    
        #print "Building MD5 Summary MD5 file"
        if build_MD5Summary_MD5(cruiseDir, warehouseUser):
            job_results['parts'].append({"partName": "Writing MD5 Summary MD5 file", "result": "Pass"})
        else:
            job_results['parts'].append({"partName": "Writing MD5 Summary MD5 file", "result": "Fail"})

    worker.send_job_status(job, 10, 10)
    
    return json.dumps(job_results)


global new_worker
new_worker = OVDMGearmanWorker()


def sigquit_handler(_signo, _stack_frame):
    print "Stopping"
    new_worker.stopTransfer()

    
def sigint_handler(_signo, _stack_frame):
    print "Quitting"
    new_worker.quitWorker()
    
    
signal.signal(signal.SIGQUIT, sigquit_handler)
signal.signal(signal.SIGINT, sigint_handler)

new_worker.set_client_id('md5Summary.py')
new_worker.register_task("updateMD5Summary", task_updateMD5Summary)
new_worker.register_task("rebuildMD5Summary", task_rebuildMD5Summary)
new_worker.work()