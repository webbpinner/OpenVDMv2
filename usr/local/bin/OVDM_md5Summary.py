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
#     REVISION:  2015-06-09
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
import gearman
import shutil
import json
import requests
import hashlib
import signal
import fnmatch
import pwd
import grp

tasks = {
    "rebuildMD5Summary": "Rebuild MD5 Summary",
    "updateMD5Summary": "Update MD5 Summary"
}


def build_filelist(sourceDir):

    returnFiles = []
    for root, dirnames, filenames in os.walk(sourceDir):
        for filename in filenames:
            if not filename == 'MD5_Summary.txt' and not filename == 'MD5_Summary.md5':
                returnFiles.append(os.path.join(root, filename))
                
    returnFiles = [filename.replace(sourceDir + '/', '', 1) for filename in returnFiles]
    return returnFiles

def build_hashes(sourceDir, worker, job, fileList):
    filesizeLimit = get_md5FilesizeLimit(job)
    filesizeLimitStatus = get_md5FilesizeLimitStatus(job) 

    hashes = []
    
    fileCount = len(fileList)
    index = 1
    for filename in fileList:
        if filesizeLimitStatus and not filesizeLimit == "0":
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
    md5SummaryFilename = cruiseDir+'/'+'MD5_Summary.txt'
    md5SummaryMD5Filename = cruiseDir+'/'+'MD5_Summary.md5'
    md5SummaryMD5Hash = hashlib.md5(md5SummaryFilename).hexdigest()
    
    try:
        #print "Open MD5 Summary MD5 file"
        MD5SummaryMD5File = open(md5SummaryMD5Filename, 'w')

        #print "Saving MD5 Summary MD5 file"
        MD5SummaryMD5File.write(md5SummaryMD5Hash)

    except IOError:
        print "Error Saving MD5 Summary MD5 file"
        return False

    finally:
        #print "Closing MD5 Summary MD5 file"
        MD5SummaryMD5File.close()
        os.chown(md5SummaryMD5Filename, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)

    return True

def get_md5FilesizeLimit(job):
    dataObj = json.loads(job.data)

    # Set Error for current tranfer in DB via API
    
    url = dataObj['siteRoot'] + 'api/warehouse/getMD5FilesizeLimit'
    r = requests.get(url)
    returnObj = json.loads(r.text)
    return returnObj['md5FilesizeLimit']

def get_md5FilesizeLimitStatus(job):
    dataObj = json.loads(job.data)

    # Set Error for current tranfer in DB via API
    
    url = dataObj['siteRoot'] + 'api/warehouse/getMD5FilesizeLimitStatus'
    r = requests.get(url)
    returnObj = json.loads(r.text)
    if returnObj['md5FilesizeLimitStatus'] == "On":
        return True

    return False

def setError_task(job, taskID):
    dataObj = json.loads(job.data)

    # Set Error for current tranfer in DB via API
    url = dataObj['siteRoot'] + 'api/tasks/setErrorTask/' + taskID
    r = requests.get(url)
    
    url = dataObj['siteRoot'] + 'api/messages/newMessage'
    payload = {'message': 'Error: ' + job.task}
    r = requests.post(url, data=payload)

def setRunning_task(job, taskID):
    dataObj = json.loads(job.data)
    jobPID = os.getpid()

    # Set Error for the task in DB via API
    url = dataObj['siteRoot'] + 'api/tasks/setRunningTask/' + taskID
    payload = {'jobPid': jobPID}
    r = requests.post(url, data=payload)

    # Add Job to DB via API
    url = dataObj['siteRoot'] + 'api/gearman/newJob/' + job.handle
    payload = {'jobName': tasks[job.task], 'jobPid': jobPID}
    r = requests.post(url, data=payload)

def setIdle_task(job, taskID):
    dataObj = json.loads(job.data)

    # Set Error for the task in DB via API
    url = dataObj['siteRoot'] + 'api/tasks/setIdleTask/' + taskID
    r = requests.get(url)

def clearError_task(job, taskID):
    dataObj = json.loads(job.data)
    url = dataObj['siteRoot'] + 'api/tasks/getTask/' + taskID
    r = requests.get(url)
    for task in r.json():
        if task['status'] == '3':
            # Clear Error for the task in DB via API
            url = dataObj['siteRoot'] + 'api/tasks/setIdleTask/' + taskID
            r = requests.get(url)

def sendMsg(dataObj, message):
    
    url = dataObj['siteRoot'] + 'api/messages/newMessage'
    payload = {'message': message}
    r = requests.post(url, data=payload)

class CustomGearmanWorker(gearman.GearmanWorker):
    
    def __init__(self, host_list=None):
        super(CustomGearmanWorker, self).__init__(host_list=host_list)
        self.stop = False
        self.taskID = "0"

    def get_taskID(self, current_job):
        dataObj = json.loads(current_job.data)
        url = dataObj['siteRoot'] + 'api/tasks/getTasks'
        r = requests.get(url)
        for task in r.json():
            if task['name'] == current_job.task:
                self.taskID = task['taskID']
                return True
        
        self.taskID = "0"
        return False
    
    def on_job_execute(self, current_job):
        print "Job started: " + current_job.handle
        self.get_taskID(current_job)
        setRunning_task(current_job, self.taskID)
        return super(CustomGearmanWorker, self).on_job_execute(current_job)
            

    def on_job_exception(self, current_job, exc_info):
        print "Job failed, CAN stop last gasp GEARMAN_COMMAND_WORK_FAIL"
        self.send_job_data(current_job, json.dumps([{"partName": "Unknown Part of Tasks", "result": "Fail"}]))
        setError_task(current_job, self.taskID)
        print exc_info
        return super(CustomGearmanWorker, self).on_job_exception(current_job, exc_info)

    def on_job_complete(self, current_job, job_result):
        resultObj = json.loads(job_result)
        print "Job complete, CAN stop last gasp GEARMAN_COMMAND_WORK_COMPLETE"
        
        if resultObj['parts'][-1]['result'] == "Fail": # Final Verdict
            setError_task(current_job,  self.taskID)
            print "but something prevented the task from successfully completing..."
        else:
            setIdle_task(current_job, self.taskID)
            
        return super(CustomGearmanWorker, self).send_job_complete(current_job, job_result)

    def after_poll(self, any_activity):
        self.stop = False
        self.taskID = "0"
        return True
    
    def stopTransfer(self):
        self.stop = True


def task_callback(gearman_worker, job):

    job_results = {'parts':[]}

    dataObj = json.loads(job.data)
    #print 'DECODED:', json.dumps(dataObj, indent=2)

    gearman_worker.send_job_status(job, 1, 10)

    cruiseDir = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+dataObj['cruiseID']
    warehouseUser = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseUsername']
    md5SummaryFilename = cruiseDir + '/' + 'MD5_Summary.txt'
    
    if dataObj['files']['new'] or dataObj['files']['updated']:
        fileList = dataObj['files']['new']
        fileList += dataObj['files']['updated']
        job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Success"})

    else:
        job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Success"})
        #print "No new or updated files to process"
        return json.dumps(job_results)
    
    gearman_worker.send_job_status(job, 2, 10)
    #print 'DECODED:', json.dumps(fileList, indent=2)
    
    newHashes = build_hashes(cruiseDir, gearman_worker, job, fileList)

    #print 'DECODED newHashes:', json.dumps(newHashes, indent=2)
    gearman_worker.send_job_status(job, 8, 10)
        
    if gearman_worker.stop:
        job_results['parts'].append({"partName": "Calculate Hashes", "result": "Fail"})
        return json.dumps(job_results)
    else:
        job_results['parts'].append({"partName": "Calculate Hashes", "result": "Success"})
    
    existingHashes = []
    
    try:
        #print "Open MD5 Summary file: " + md5SummaryFilename
        MD5SummaryFile = open(md5SummaryFilename, 'r')

        for line in MD5SummaryFile:
            (md5Hash, filename) = line.split(' ', 1)
            existingHashes.append({'hash': md5Hash, 'filename': filename.replace('\n', '', 1)})
        

    except IOError:
        print "Error Reading MD5 Summary file"
        job_results['parts'].append({"partName": "Reading pre-existing MD5 Summary file", "result": "Fail"})
        return json.dumps(job_results)

    finally:
        #print "Closing MD5 Summary file"
        MD5SummaryFile.close()
        job_results['parts'].append({"partName": "Reading pre-existing MD5 Summary file", "result": "Success"})

    #gearman_worker.send_job_status(job, 8, 10)
    #print 'DECODED existingHashes:', json.dumps(existingHashes, indent=2)

    for newRow in newHashes:
        updated = False
        for existingRow in existingHashes:
            if newRow['filename'] == existingRow['filename']:
                #print "Row Updated"
                existingRow['hash'] = newRow['hash']
                updated = True
                break
        
        if not updated:
            #print "Row Added"
            existingHashes.append({'hash': newRow['hash'], 'filename': dataObj['cruiseID'] + '/' + newRow['filename']})
        
    #print 'DECODED updatedHashes:', json.dumps(existingHashes, indent=2)
    gearman_worker.send_job_status(job, 85, 100)
    
    try:
        #print "Open MD5 Summary file"
        MD5SummaryFile = open(md5SummaryFilename, 'w')

        #print "Saving MD5 Summary file"
        #sorted(student_tuples, key=itemgetter(2))
        for filehash in existingHashes:
            MD5SummaryFile.write(filehash['hash'] + ' ' + filehash['filename'] + '\n')

    except IOError:
        print "Error Saving MD5 Summary file"
        job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Fail"})
        MD5SummaryFile.close()
        return json.dumps(job_results)    

    finally:
        #print "Closing MD5 Summary file"
        MD5SummaryFile.close()
        os.chown(md5SummaryFilename, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)
        job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Success"})
        
    gearman_worker.send_job_status(job, 9, 10)

    #print "Building MD5 Summary MD5 file"
    if build_MD5Summary_MD5(cruiseDir, warehouseUser):
        job_results['parts'].append({"partName": "Writing MD5 Summary MD5 file", "result": "Success"})
    else:
        job_results['parts'].append({"partName": "Writing MD5 Summary MD5 file", "result": "Fail"})

    gearman_worker.send_job_status(job, 10, 10)
    return json.dumps(job_results)    
        
def task_callback2(gearman_worker, job):

    job_results = {'parts':[]}

    dataObj = json.loads(job.data)
    #print 'DECODED:', json.dumps(dataObj, indent=2)

    gearman_worker.send_job_status(job, 1, 10)
    
    cruiseDir = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+dataObj['cruiseID']
    warehouseUser = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseUsername']
    md5SummaryFilename = cruiseDir + '/' + 'MD5_Summary.txt'
    
    fileList = build_filelist(cruiseDir)
    #print 'DECODED:', json.dumps(fileList, indent=2)
    
    job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Success"})
    
    gearman_worker.send_job_status(job, 2, 10)

    hashes = build_hashes(cruiseDir, gearman_worker, job, fileList)
    #print 'DECODED:', json.dumps(hashes, indent=2)
    
    gearman_worker.send_job_status(job, 8, 10)
    
    if gearman_worker.stop:
        job_results['parts'].append({"partName": "Calculate Hashes", "result": "Fail"})
    else:
        job_results['parts'].append({"partName": "Calculate Hashes", "result": "Success"})
                
        try:
            #print "Open MD5 Summary file"
            MD5SummaryFile = open(md5SummaryFilename, 'w')

            #print "Saving MD5 Summary file"
            for filehash in hashes:
                MD5SummaryFile.write(filehash['hash'] + ' ' + dataObj['cruiseID'] + '/' + filehash['filename'] + '\n')
                
        except IOError:
            print "Error Saving MD5 Summary file"
            job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Fail"})
            MD5SummaryFile.close()
            return json.dumps(job_results)

        finally:
            #print "Closing MD5 Summary file"
            MD5SummaryFile.close()
            os.chown(md5SummaryFilename, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)
            job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Success"})
            
        gearman_worker.send_job_status(job, 9, 10)
    
        #print "Building MD5 Summary MD5 file"
        if build_MD5Summary_MD5(cruiseDir, warehouseUser):
            job_results['parts'].append({"partName": "Writing MD5 Summary MD5 file", "result": "Success"})
        else:
            job_results['parts'].append({"partName": "Writing MD5 Summary MD5 file", "result": "Fail"})

    gearman_worker.send_job_status(job, 10, 10)
    
    return json.dumps(job_results)

global new_worker
new_worker = CustomGearmanWorker(['localhost:4730'])

def sigquit_handler(_signo, _stack_frame):
    print "Stopping"
    new_worker.stopTransfer()
    
signal.signal(signal.SIGQUIT, sigquit_handler)

new_worker.set_client_id('md5Summary.py')
new_worker.register_task("updateMD5Summary", task_callback)
new_worker.register_task("rebuildMD5Summary", task_callback2)
new_worker.work()