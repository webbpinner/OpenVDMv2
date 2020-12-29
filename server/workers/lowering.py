# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_lowering.py
#
#  DESCRIPTION:  Gearman worker the handles the tasks of initializing a new lowering
#                and finalizing the current lowering.
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.5
#      CREATED:  2015-01-01
#     REVISION:  2020-12-28
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
import subprocess
import python3_gearman
import json
import time
import signal
import shutil
import logging

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.utils.set_ownerGroupPermissions import set_ownerGroupPermissions
from server.utils.check_filenames import bad_filename
from server.utils.output_JSONDataToFile import output_JSONDataToFile
from server.lib.openvdm import OpenVDM_API, DEFAULT_LOWERING_CONFIG_FN


def build_filelist(sourceDir):

    logging.debug("sourceDir: {}".format(sourceDir))

    returnFiles = []
    for root, dirnames, filenames in os.walk(sourceDir):
        for filename in filenames:
            returnFiles.append(os.path.join(root, filename))

    returnFiles = [filename.replace(sourceDir + '/', '', 1) for filename in returnFiles]
    return returnFiles

    
def export_LoweringConfig(gearman_worker, loweringConfigFilePath, finalize=False):
    loweringConfig = gearman_worker.OVDM.getLoweringConfig()

    if finalize:
        loweringConfig['loweringFinalizedOn'] = loweringConfig['configCreatedOn']
    elif os.path.isfile(loweringConfigFilePath):
        logging.info("Reading existing configuration file")
        try:
            with open(loweringConfigFilePath) as json_file:  
                data = json.load(json_file)
                if "loweringFinalizedOn" in data:
                    loweringConfig['loweringFinalizedOn'] = data['loweringFinalizedOn']
        
        except OSError as error:
            return {'verdict': False, 'reason': "Unable to read existing configuration file"}

    for transfer in loweringConfig['collectionSystemTransfersConfig']:
        del transfer['sshPass']
        del transfer['rsyncPass']
        del transfer['smbPass']

    return output_JSONDataToFile(loweringConfigFilePath, loweringConfig)


class OVDMGearmanWorker(python3_gearman.GearmanWorker):
    
    def __init__(self, host_list=None):
        self.stop = False
        self.OVDM = OpenVDM_API()
        self.task = None
        self.cruiseID = ''
        self.loweringID = ''
        self.loweringStartDate = ''
        self.collectionSystemTransfer = {}
        self.shipboardDataWarehouseConfig = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])
    
    
    def on_job_execute(self, current_job):

        logging.debug("current_job: {}".format(current_job))

        payloadObj = json.loads(current_job.data)

        self.task = self.OVDM.getTaskByName(current_job.task)
        logging.debug("task: {}".format(self.task))

        if int(self.task['taskID']) > 0:
            self.OVDM.setRunning_task(self.task['taskID'], os.getpid(), current_job.handle)
#        else:
#            self.OVDM.trackGearmanJob(taskLookup[current_job.task], os.getpid(), current_job.handle)

        logging.info("Job: {} ({}) started at: {}".format(self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime())))
        
        self.cruiseID = payloadObj['cruiseID'] if 'cruiseID' in payloadObj else self.OVDM.getCruiseID()
        self.loweringID = payloadObj['loweringID'] if 'loweringID' in payloadObj else self.OVDM.getLoweringID()
        self.loweringStartDate = payloadObj['loweringStartDate'] if 'loweringStartDate' in payloadObj else self.OVDM.getLoweringStartDate()
        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()        
                
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)
            

    def on_job_exception(self, current_job, exc_info):
        logging.error("Job: {} ({}) failed at: {}".format(self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime())))
        
        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail", "reason": "Worker crashed"}]))
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
        
        jobData = {
            'cruiseID': self.cruiseID,
            'loweringID': self.loweringID,
            'loweringStartDate': self.loweringStartDate
        }

        if current_job.task == 'setupNewLowering':

            gm_client = python3_gearman.GearmanClient([self.OVDM.getGearmanServer()])
        
            for task in self.OVDM.getTasksForHook('setupNewLowering'):
                logging.debug("Adding post task: {}".format(task));
                submitted_job_request = gm_client.submit_job(task, json.dumps(jobData), background=True)
                
        elif current_job.task == 'finalizeCurrentLowering':

            gm_client = python3_gearman.GearmanClient([self.OVDM.getGearmanServer()])
        
            for task in self.OVDM.getTasksForHook('finalizeCurrentLowering'):
                logging.debug("Adding post task: {}".format(task));
                submitted_job_request = gm_client.submit_job(task, json.dumps(jobData), background=True)
        
        if len(resultsObj['parts']) > 0:
            if resultsObj['parts'][-1]['result'] == "Fail": # Final Verdict
                if int(self.task['taskID']) > 0:
                    self.OVDM.setError_task(self.task['taskID'], resultsObj['parts'][-1]['reason'])
                else:
                    self.OVDM.sendMsg(self.task['longName'] + ' failed', resultsObj['parts'][-1]['reason'])
            else:
                self.OVDM.setIdle_task(self.task['taskID'])
        else:
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


def task_setupNewLowering(gearman_worker, gearman_job):

    job_results = {'parts':[]}

    payloadObj = json.loads(gearman_job.data)
    logging.debug("Payload: {}".format(json.dumps(payloadObj, indent=2)))

    warehouseUser = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    cruiseDir = os.path.join(gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'], gearman_worker.cruiseID)  
    loweringDataBaseDir = os.path.join(cruiseDir, gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir'])
    loweringDir = os.path.join(loweringDataBaseDir, gearman_worker.loweringID)
    loweringConfigFilePath = os.path.join(loweringDir, DEFAULT_LOWERING_CONFIG_FN)
    
    gearman_worker.send_job_status(gearman_job, 1, 10)
    
    gm_client = python3_gearman.GearmanClient([gearman_worker.OVDM.getGearmanServer()])

    logging.info("Creating lowering data directory")
    completed_job_request = gm_client.submit_job("createLoweringDirectory", gearman_job.data)
    
    resultObj = json.loads(completed_job_request.result)

    if resultObj['parts'][-1]['result'] == "Pass": # Final Verdict
        job_results['parts'].append({"partName": "Create lowering data directory structure", "result": "Pass"})
    else:
        logging.error("Failed to create lowering data directory")
        job_results['parts'].append({"partName": "Create lowering data directory structure", "result": "Fail", "reason": resultObj['parts'][-1]['reason']})
        return json.dumps(job_results)
    
    gearman_worker.send_job_status(gearman_job, 5, 10)
    
    #build lowering Config file
    logging.info("Exporting Lowering Configuration")
    output_results = export_LoweringConfig(gearman_worker, loweringConfigFilePath)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Export lowering config data to file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Export lowering config data to file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)
    
    output_results = set_ownerGroupPermissions(warehouseUser, loweringConfigFilePath)

    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Set lowering config file ownership/permissions", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 9, 10)

    logging.info("Updating Lowering Size")
    loweringSize = subprocess.check_output(['du','-sb', loweringDir]).split()[0].decode('utf-8')

    gearman_worker.OVDM.set_loweringSize(loweringSize)

    gearman_worker.send_job_status(gearman_job, 10, 10)

    return json.dumps(job_results)
    
    
def task_finalizeCurrentLowering(gearman_worker, gearman_job):

    job_results = {'parts':[]}

    gearman_worker.send_job_status(gearman_job, 1, 10)

    warehouseUser = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)
    loweringDataBaseDir = os.path.join(cruiseDir, gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir'])
    loweringDir = os.path.join(loweringDataBaseDir, gearman_worker.loweringID)

    loweringConfigFilePath = os.path.join(loweringDir, DEFAULT_LOWERING_CONFIG_FN)

    if os.path.exists(loweringDir) and (gearman_worker.loweringID != ''):
        job_results['parts'].append({"partName": "Verify Lowering Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Lowering Directory exists", "result": "Fail", "reason": "Lowering directory: " + loweringDir + " could not be found"})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 3, 10)
    logging.info("Queuing Collection System Transfers")

    gm_client = python3_gearman.GearmanClient([gearman_worker.OVDM.getGearmanServer()])
    
    gmData = {
        'loweringID': gearman_worker.loweringID,
        'loweringStartDate': gearman_worker.loweringStartDate,
        'systemStatus': "On",
        'collectionSystemTransfer': {}
    }
    
    collectionSystemTransferJobs = []
    
    collectionSystemTransfers = gearman_worker.OVDM.getActiveCollectionSystemTransfers(cruise=False)

    for collectionSystemTransfer in collectionSystemTransfers:

        logging.debug("Queuing runCollectionSystemTransfer job for {}".format(collectionSystemTransfer['name']))        
        gmData['collectionSystemTransfer']['collectionSystemTransferID'] = collectionSystemTransfer['collectionSystemTransferID']
        
        collectionSystemTransferJobs.append( {"task": "runCollectionSystemTransfer", "data": json.dumps(gmData)} )

    gearman_worker.send_job_status(gearman_job, 5, 10)

    if len(collectionSystemTransferJobs) > 0:
        logging.info("Submitting runCollectionSystemTransfer jobs")
        submitted_job_request = gm_client.submit_multiple_jobs(collectionSystemTransferJobs, background=False, wait_until_complete=False)
    
        gearman_worker.send_job_status(gearman_job, 7, 10)
    
        time.sleep(1)
        completed_requests = gm_client.wait_until_jobs_completed(submitted_job_request)
        logging.info("Completed runCollectionSystemTransfers jobs")

    gearman_worker.send_job_status(gearman_job, 9, 10)
    
    #build Lowering Config file
    logging.info("Exporting Lowering Configuration")
    output_results = export_LoweringConfig(gearman_worker, loweringConfigFilePath, finalize=True)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Export Lowering config data to file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Export Lowering config data to file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)
    
    output_results = set_ownerGroupPermissions(warehouseUser, loweringConfigFilePath)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set Lowering config file ownership/permissions", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Set Lowering config file ownership/permissions", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    # need to add code for updating MD5

    gearman_worker.send_job_status(gearman_job, 10, 10)
    return json.dumps(job_results)


def task_exportLoweringConfig(gearman_worker, gearman_job):

    job_results = {'parts':[]}

    warehouseUser = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)
    loweringDataBaseDir = os.path.join(cruiseDir, gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir'])
    loweringDir = os.path.join(loweringDataBaseDir, gearman_worker.loweringID)
    loweringConfigFilePath = os.path.join(loweringDir, DEFAULT_LOWERING_CONFIG_FN)

    gearman_worker.send_job_status(gearman_job, 1, 10)

    logging.info("Verifying lowering directory exists")
    if os.path.exists(loweringDir) and (gearman_worker.loweringID != ''):
        job_results['parts'].append({"partName": "Verify Lowering Directory exists", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Verify Lowering Directory exists", "result": "Fail", "result": "Fail", "reason": "Unable to locate the lowering directory: " + loweringDir})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 3, 10)

    #build OpenVDM Config file
    logging.info("Exporting Lowering Configuration")
    output_results = export_LoweringConfig(gearman_worker, loweringConfigFilePath)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Export Lowering config data to file", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Export Lowering config data to file", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 6, 10)

    logging.info("Setting file ownership/permissions")
    output_results = set_ownerGroupPermissions(warehouseUser, loweringConfigFilePath)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set file ownership/permissions", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Set file ownership/permissions", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)
    
    gearman_worker.send_job_status(gearman_job, 10, 10)
    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle Lowering-Level tasks')
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

    # global new_worker
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

    logging.info("\tTask: setupNewLowering")
    new_worker.register_task("setupNewLowering", task_setupNewLowering)
    logging.info("\tTask: finalizeCurrentLowering")
    new_worker.register_task("finalizeCurrentLowering", task_finalizeCurrentLowering)
    logging.info("\tTask: exportLoweringConfig")
    new_worker.register_task("exportLoweringConfig", task_exportLoweringConfig)

    logging.info("Waiting for jobs...")
    new_worker.work()
