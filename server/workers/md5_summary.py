# ----------------------------------------------------------------------------------- #
#
#         FILE:  md5_summary.py
#
#  DESCRIPTION:  Gearman worker tha handles the creation and update of an MD5 checksum
#                summary.
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.5
#      CREATED:  2015-01-01
#     REVISION:  2020-12-29
#
# LICENSE INFO: Open Vessel Data Management v2.5 (OpenVDMv2)
#               Copyright (C) OceanDataRat.org 2021
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

import argparse
import os
import sys
import python3_gearman
import json
import hashlib
import signal
import time
import logging

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.utils.set_ownerGroupPermissions import set_ownerGroupPermissions
from server.lib.openvdm import OpenVDM_API, DEFAULT_MD5_SUMMARY_FN, DEFAULT_MD5_SUMMARY_MD5_FN


customTasks = [
    {
        "taskID": "0",
        "name": "updateMD5Summary",
        "longName": "Updating MD5 Summary",
    }
]

BUF_SIZE = 65536  # read files in 64kb chunks


def build_filelist(sourceDir):

    logging.debug("sourceDir: {}".format(sourceDir))

    returnFiles = []
    for root, dirnames, filenames in os.walk(sourceDir):
        for filename in filenames:
            if filename != DEFAULT_MD5_SUMMARY_FN and filename != DEFAULT_MD5_SUMMARY_MD5_FN:
                returnFiles.append(os.path.join(root, filename))

    returnFiles = [filename.replace(sourceDir + '/', '', 1) for filename in returnFiles]
    return returnFiles


def hash_file(filepath):
    md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


def build_hashes(gearman_worker, gearman_job, fileList):

    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    filesizeLimit = gearman_worker.OVDM.getMD5FilesizeLimit()
    filesizeLimitStatus = gearman_worker.OVDM.getMD5FilesizeLimitStatus() 

    hashes = []

    for idx, filename in enumerate(fileList):

        if gearman_worker.stop:
            debugPrint("Stopping")
            break

        filepath = os.path.join(baseDir, filename)

        if filesizeLimitStatus == 'On' and not filesizeLimit == '0':
            if os.stat(filepath).st_size < int(filesizeLimit) * 1000000:
                hashes.append({'hash': hash_file(filepath), 'filename': filename})

            else:
                hashes.append({'hash': '********************************', 'filename': filename})
        else:

                hashes.append({'hash': hash_file(filepath), 'filename': filename})

        gearman_worker.send_job_status(gearman_job, int(20 + 60*float(idx)/float(len(fileList))), 100)

    return hashes


def build_MD5Summary_MD5(worker):

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)

    md5SummaryFilepath = os.path.join(cruiseDir, DEFAULT_MD5_SUMMARY_FN)
    md5SummaryMD5Filepath = os.path.join(cruiseDir, DEFAULT_MD5_SUMMARY_MD5_FN)
    
    try:
        with open(md5SummaryMD5Filepath, 'w') as MD5SummaryMD5File:
            MD5SummaryMD5File.write(hash_file(md5SummaryFilepath))

    except IOError:
        logging.error("Error Saving MD5 Summary MD5 file: {}".format(md5SummaryMD5Filepath))
        return {"verdict": False, "reason": "Error Saving MD5 Summary MD5 file: " + md5SummaryMD5Filepath}

    return {"verdict": True}


class OVDMGearmanWorker(python3_gearman.GearmanWorker):
    
    def __init__(self, host_list=None):
        self.stop = False
        self.OVDM = OpenVDM_API()
        self.task = None
        self.cruiseID = ''
        self.shipboardDataWarehouseConfig = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])


    def get_custom_task(self, current_job):
        task = list(filter(lambda task: task['name'] == current_job.task, customTasks))
        return task[0] if len(task) > 0 else None

    
    def on_job_execute(self, current_job):

        logging.debug("current_job: {}".format(current_job))

        payloadObj = json.loads(current_job.data)

        self.task = self.get_custom_task(current_job) if self.get_custom_task(current_job) != None else self.OVDM.getTaskByName(current_job.task)
        logging.debug("task: {}".format(self.task))

        if int(self.task['taskID']) > 0:
            self.OVDM.setRunning_task(self.task['taskID'], os.getpid(), current_job.handle)
        else:
            self.OVDM.trackGearmanJob(taskLookup[current_job.task], os.getpid(), current_job.handle)

        logging.info("Job: {} ({}) started at: {}".format(self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime())))
        
        self.cruiseID = payloadObj['cruiseID'] if 'cruiseID' in payloadObj else self.OVDM.getCruiseID()
        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()        
                
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)


    def on_job_exception(self, current_job, exc_info):
        logging.error("Job: {} ({}) failed at: {}".format(self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime())))

        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail", "reason": "Unknown"}]))
        if int(self.task['taskID']) > 0:
            self.OVDM.setError_task(self.task['taskID'], "Worker crashed")
        else:
            self.OVDM.sendMsg(self.task['longName'] + ' failed', 'Worker crashed')

        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)

    
    def on_job_complete(self, current_job, job_results):
        resultsObj = json.loads(job_results)

        if len(resultsObj['parts']) > 0:
            if resultsObj['parts'][-1]['result'] == "Fail": # Final Verdict
                if int(self.task['taskID']) > 0:
                    self.OVDM.setError_task(self.task['taskID'], resultsObj['parts'][-1]['reason'])
                else:
                    self.OVDM.sendMsg(self.task['longName'] + ' failed', resultsObj['parts'][-1]['reason'])
            else:
                if int(self.task['taskID']) > 0:
                    self.OVDM.setIdle_task(self.task['taskID'])
        else:
            if int(self.task['taskID']) > 0:
                self.OVDM.setIdle_task(self.task['taskID'])

        logging.debug("Job Results: {}".format(json.dumps(resultsObj, indent=2)))
        logging.info("Job: {} ({}) completed at: {}".format(self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime())))
            
        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_results)


    def stopTask(self):
        self.stop = True
        logging.warning("Stopping current task...")


    def quitWorker(self):
        self.stop = True
        logging.warning("Quitting worker...")
        self.shutdown()


def task_updateMD5Summary(gearman_worker, gearman_job):

    job_results = {'parts':[]}

    payloadObj = json.loads(gearman_job.data)
    logging.debug("Payload: {}".format(json.dumps(payloadObj, indent=2)))

    warehouseUser = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir,gearman_worker.cruiseID)
    md5SummaryFilepath = os.path.join(cruiseDir, DEFAULT_MD5_SUMMARY_FN)
    md5SummaryMD5Filepath = os.path.join(cruiseDir, DEFAULT_MD5_SUMMARY_MD5_FN)

    gearman_worker.send_job_status(gearman_job, 1, 10)
    
    logging.debug("Building filelist")
    fileList = []
    
    job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Pass"})

    if payloadObj['files']['new'] or payloadObj['files']['updated']:
        fileList.extend(payloadObj['files']['new'])
        fileList.extend(payloadObj['files']['updated'])
    else:
        return json.dumps(job_results)

    fileList = [os.path.join(worker.cruiseID, filename) for filename in fileList]    
    logging.debug('Filelist: {}'.format(json.dumps(fileList, indent=2)))

    gearman_worker.send_job_status(gearman_job, 2, 10)

    logging.debug("Building hashes")
    newHashes = build_hashes(gearman_worker, gearman_job, fileList)    
    logging.debug('Hashes: {}'.format(json.dumps(newHashes, indent=2)))

    gearman_worker.send_job_status(gearman_job, 8, 10)
        
    if worker.stop:
        return json.dumps(job_results)
    else:
        job_results['parts'].append({"partName": "Calculate Hashes", "result": "Pass"})
    
    existingHashes = []

    logging.debug("Processing existing MD5 summary file")
    
    try:
        with open(md5SummaryFilepath, 'r') as MD5SummaryFile:

            for line in MD5SummaryFile:
                (md5Hash, filename) = line.split(' ', 1)
                existingHashes.append({'hash': md5Hash, 'filename': filename.rstrip('\n')})

    except IOError:
        logging.error("Error Reading pre-existing MD5 Summary file: {}".format(md5SummaryFilepath))
        job_results['parts'].append({"partName": "Reading pre-existing MD5 Summary file", "result": "Fail", "reason": "Error Reading pre-existing MD5 Summary file: " + md5SummaryFilepath})
        return json.dumps(job_results)

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
        logging.debug("{} row(s) added".format(row_added))
    if row_updated > 0:
        logging.debug("{} row(s) updated".format(row_updated))

    gearman_worker.send_job_status(gearman_job, 85, 100)

    #debugPrint("Sorting hashes")
    sortedHashes = sorted(existingHashes, key=lambda hashes: hashes['filename'])

    logging.debug("Building MD5 Summary file")
    try:
        with open(md5SummaryFilepath, 'w') as MD5SummaryFile:

            for filehash in sortedHashes:
                MD5SummaryFile.write(filehash['hash'] + ' ' + filehash['filename'] + '\n')

        job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Pass"})

    except IOError:
        logging.error("Error updating MD5 Summary file: {}".format(md5SummaryFilepath))
        job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Fail", "reason": "Error updating MD5 Summary file: " + md5SummaryFilepath})
        return json.dumps(job_results)    

    set_ownerGroupPermissions(warehouseUser, md5SummaryFilepath)
    
    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set MD5 Summary file ownership/permissions", "result": "Pass"})
    else:
        logging.error("Failed to set directory ownership")
        job_results['parts'].append({"partName": "Set MD5 Summary file ownership/permissions", "result": "Fail", "reason": output_results['reason']})

    gearman_worker.send_job_status(gearman_job, 9, 10)

    logging.debug("Building MD5 Summary MD5 file")

    output_results = build_MD5Summary_MD5(worker)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Writing MD5 Summary MD5 file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Writing MD5 Summary MD5 file", "result": "Fail", "reason": output_results['reason']})

    output_results = set_ownerGroupPermissions(warehouseUser, md5SummaryMD5Filepath)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set MD5 Summary MD5 file ownership/permissions", "result": "Pass"})
    else:
        logging.error("Failed to set directory ownership")
        job_results['parts'].append({"partName": "Set MD5 Summary MD5 file ownership/permissions", "result": "Fail", "reason": output_results['reason']})

   gearman_worker.send_job_status(gearman_job, 10, 10)
    return json.dumps(job_results)


def task_rebuildMD5Summary(gearman_worker, gearman_job):

    job_results = {'parts':[]}

    logging.debug("Payload: {}".format(json.dumps(payloadObj, indent=2)))

    warehouseUser = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir,gearman_worker.cruiseID)
    md5SummaryFilepath = os.path.join(cruiseDir, DEFAULT_MD5_SUMMARY_FN)
    md5SummaryMD5Filepath = os.path.join(cruiseDir, DEFAULT_MD5_SUMMARY_MD5_FN)

    gearman_worker.send_job_status(gearman_job, 1, 10)
    
    if os.path.exists(cruiseDir):
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Pass"})
    else:
        logging.error("Cruise directory not found")
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Fail", "reason": "Unable to locate the cruise directory: " + cruiseDir})
        return json.dumps(job_results)
    
    logging.info("Building filelist")
    fileList = build_filelist(cruiseDir)
    logging.debug('Filelist: {}'.format(json.dumps(fileList, indent=2)))
    
    job_results['parts'].append({"partName": "Retrieve Filelist", "result": "Pass"})
    
    gearman_worker.send_job_status(gearman_job, 2, 10)

    logging.info("Building hashes")
    newHashes = build_hashes(gearman_worker, gearman_job, fileList)
    logging.debug("Hashes: {}".format(json.dumps(newHashes, indent=2)))
        
    if gearman_worker.stop:
        job_results['parts'].append({"partName": "Calculate Hashes", "result": "Fail", "reason": "Job was stopped by user"})
        return json.dumps(job_results)
    else:
        job_results['parts'].append({"partName": "Calculate Hashes", "result": "Pass"})

    gearman_worker.send_job_status(gearman_job, 85, 100)

    logging.debug("Sorting Hashes")   
    sortedHashes = sorted(newHashes, key=lambda hashes: hashes['filename'])
    
    gearman_worker.send_job_status(gearman_job, 9, 10)

    logging.info("Building MD5 Summary file")
    try:
        #debugPrint("Saving new MD5 Summary file")
        with open(md5SummaryFilepath, 'w') as MD5SummaryFile:

            for filehash in sortedHashes:
                MD5SummaryFile.write(filehash['hash'] + ' ' + filehash['filename'] + '\n')

        job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Pass"})

    except IOError:
        logging.error("Error saving MD5 Summary file: {}".format(md5SummaryFilepath))
        job_results['parts'].append({"partName": "Writing MD5 Summary file", "result": "Fail", "reason": "Error saving MD5 Summary file: " + md5SummaryFilepath})
        return json.dumps(job_results)    

    output_results = set_ownerGroupPermissions(warehouseUser, md5SummaryFilepath)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set MD5 Summary file ownership/permissions", "result": "Pass"})
    else:
        logging.error("Failed to set directory ownership")
        job_results['parts'].append({"partName": "Set MD5 Summary file ownership/permissions", "result": "Fail", "reason": output_results['reason']})

    gearman_worker.send_job_status(gearman_job, 95, 100)

    logging.info("Building MD5 Summary MD5 file")

    output_results = build_MD5Summary_MD5(gearman_worker)
    if output_results['verdict']:
        job_results['parts'].append({"partName": "Writing MD5 Summary MD5 file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Writing MD5 Summary MD5 file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)    

    output_results = set_ownerGroupPermissions(warehouseUser, md5SummaryMD5Filepath)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set MD5 Summary MD5 file ownership/permissions", "result": "Pass"})
    else:
        logging.error("Failed to set directory ownership")
        job_results['parts'].append({"partName": "Set MD5 Summary MD5 file ownership/permissions", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)    

    gearman_worker.send_job_status(gearman_job, 10, 10)
    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle MD5 Summary related tasks')
    parser.add_argument('-v', '--verbosity', dest='verbosity',
                        default=0, action='count',
                        help='Increase output verbosity')

    parsed_args = parser.parse_args()

    ############################
    # Set up logging before we do any other argument parsing (so that we
    # can log problems with argument parsing).
    
    LOGGING_FORMAT = '%(asctime)-15s %(levelname)s - %(message)s'
    logging.basicConfig(format=LOGGING_FORMAT)

    LOG_LEVELS = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    parsed_args.verbosity = min(parsed_args.verbosity, max(LOG_LEVELS))
    logging.getLogger().setLevel(LOG_LEVELS[parsed_args.verbosity])

    logging.debug("Creating Worker...")

    new_worker = OVDMGearmanWorker()
    new_worker.set_client_id(__file__)

    logging.debug("Defining Signal Handlers...")
    def sigquit_handler(_signo, _stack_frame):
        logging.warning("QUIT Signal Received")
        new_worker.stopTask()

    def sigint_handler(_signo, _stack_frame):
        logging.warning("INT Signal Received")
        new_worker.quitWorker()

    signal.signal(signal.SIGQUIT, sigquit_handler)
    signal.signal(signal.SIGINT, sigint_handler)

    logging.info("Registering worker tasks...")

    logging.info("\tTask: updateMD5Summary")
    new_worker.register_task("updateMD5Summary", task_updateMD5Summary)
    logging.info("\tTask: rebuildMD5Summary")
    new_worker.register_task("rebuildMD5Summary", task_rebuildMD5Summary)

    logging.info("Waiting for jobs...")
    new_worker.work()
