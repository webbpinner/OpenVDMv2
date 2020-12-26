# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_cruiseDirectory.py
#
#  DESCRIPTION:  Gearman worker the handles the tasks of creating a new cruise data
#                directory and updating the cruise directory structure when additional
#                subdirectories must be added.
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.5
#      CREATED:  2015-01-01
#     REVISION:  2020-12-26
#
# LICENSE INFO: Open Vessel Data Management v2.5 (OpenVDMv2)
#               Copyright (C) OceanDataRat 2021
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
import errno
import python3_gearman
import json
import time
import signal
import logging

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.utils.set_ownerGroupPermissions import set_ownerGroupPermissions
from server.utils.check_filenames import bad_filename
from server.utils.output_JSONDataToFile import output_JSONDataToFile
from server.utils.stderr_logging import StdErrLoggingHandler, STDERR_FORMATTER
from server.lib.openvdm import OpenVDM_API, DEFAULT_CRUISE_CONFIG_FN


customTasks = [
    {
        "taskID": "0",
        "name": "createCruiseDirectory",
        "longName": "Creating Cruise Directory",
    },
    {
        "taskID": "0",
        "name": "setCruiseDataDirectoryPermissions",
        "longName": "Setting CruiseData Directory Permissions",
    }

]


def build_destDir(gearman_worker, destDir):
    
    returnDestDir = destDir.replace('{loweringID}', gearman_worker.loweringID)
    returnDestDir = returnDestDir.replace('{loweringDataBaseDir}', gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir'],)
    returnDestDir = returnDestDir.replace('{cruiseID}', gearman_worker.cruiseID)
    return returnDestDir


def build_directorylist(gearman_worker):

    returnDirectories = []
    cruiseDir = os.path.join(gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'], gearman_worker.cruiseID)

    if gearman_worker.OVDM.getShowLoweringComponents():
      returnDirectories.append(os.path.join(cruiseDir, gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir']))

    collectionSystemTransfers = gearman_worker.OVDM.getActiveCollectionSystemTransfers()

    for collectionSystemTransfer in collectionSystemTransfers:
        if collectionSystemTransfer['enable'] == "1" and collectionSystemTransfer['cruiseOrLowering'] == "0":
            destDir = build_destDir(gearman_worker, collectionSystemTransfer['destDir'])
            returnDirectories.append(os.path.join(cruiseDir, destDir))

    requiredExtraDirectories = gearman_worker.OVDM.getRequiredExtraDirectories()
    for requiredExtraDirectory in requiredExtraDirectories:
        destDir = build_destDir(gearman_worker, requiredExtraDirectory['destDir'])
        returnDirectories.append(os.path.join(cruiseDir, destDir))

    extraDirectories = gearman_worker.OVDM.getExtraDirectories()
    if extraDirectories:
        for extraDirectory in extraDirectories:
            if extraDirectory['enable'] == "1":
                destDir = build_destDir(gearman_worker, extraDirectory['destDir'])
                returnDirectories.append(os.path.join(cruiseDir, destDir))

    return returnDirectories


def create_directories(directoryList):

    reasons = []
    for directory in directoryList:
        try:
            os.makedirs(directory)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                logging.error("Unable to create directory: {}".format(directory))
                reasons.append("Unable to create directory: {}".format(directory))
                
    if len(reasons) > 0:
        return {'verdict': False, 'reason': '\n'.join(reasons)}

    return {'verdict': True}


def lockdown_directory(baseDir, exemptDir):

    dirContents = [ os.path.join(baseDir,f) for f in os.listdir(baseDir)]
    files = filter(os.path.isfile, dirContents)
    for file in files:
        os.chmod(file, 0o600)

    directories = filter(os.path.isdir, dirContents)
    for directory in directories:
        if not directory == exemptDir:
            os.chmod(directory, 0o700)


class OVDMGearmanWorker(python3_gearman.GearmanWorker):

    def __init__(self, host_list=None):
        self.stop = False
        self.OVDM = OpenVDM_API()
        self.task = None
        self.cruiseID = ''
        self.loweringID = ''
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

        logging.info("Job: {} ({}) started at: {}".format(self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime())))

        self.cruiseID = payloadObj['cruiseID'] if 'cruiseID' in payloadObj else self.OVDM.getCruiseID()
        self.loweringID = payloadObj['loweringID'] if 'loweringID' in payloadObj else self.OVDM.getLoweringID()
        self.systemStatus = self.OVDM.getSystemStatus()

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


def task_createCruiseDirectory(gearman_worker, job):

    job_results = {'parts':[]}

    payloadObj = json.loads(job.data)
    logging.debug("Payload: {}".format(json.dumps(payloadObj, indent=2)))

    gearman_worker.send_job_status(job, 1, 10)

    warehouseUser = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)

    if os.path.exists(baseDir):
        job_results['parts'].append({"partName": "Verify Base Directory exists", "result": "Pass"})
    else:
        logging.error("Failed to find base directory: {}".format(baseDir))
        job_results['parts'].append({"partName": "Verify Base Directory exists", "result": "Fail", "reason": "Failed to find base directory: " + baseDir})
        return json.dumps(job_results)


    if not os.path.exists(cruiseDir):
        job_results['parts'].append({"partName": "Verify Cruise Directory does not exists", "result": "Pass"})
    else:
        debug.error("Cruise directory already exists: {}".format(cruiseDir))
        job_results['parts'].append({"partName": "Verify Cruise Directory does not exists", "result": "Fail", "reason": "Cruise directory " + cruiseDir + " already exists"})
        return json.dumps(job_results)

    gearman_worker.send_job_status(job, 2, 10)

    directoryList = build_directorylist(gearman_worker)

    logging.debug("Directory List: {}".format(json.dumps(directoryList, indent=2)))

    if len(directoryList) > 0:
        job_results['parts'].append({"partName": "Build Directory List", "result": "Pass"})
    else:
        debug.warning("Directory list is empty")
        job_results['parts'].append({"partName": "Build Directory List", "result": "Fail", "reason": "Unable to build list of directories to create"})
        return json.dumps(job_results)

    gearman_worker.send_job_status(job, 5, 10)

    output_results = create_directories(directoryList)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Create Directories", "result": "Pass"})
    else:
        logging.error("Failed to create any/all of the cruise data directory structure")
        job_results['parts'].append({"partName": "Create Directories", "result": "Fail", "reason": output_results['reason']})

    gearman_worker.send_job_status(job, 7, 10)

    if gearman_worker.OVDM.showOnlyCurrentCruiseDir():
        logging.info("Clear read permissions for all cruise directories")
        lockdown_directory(baseDir, cruiseDir)

        job_results['parts'].append({"partName": "Clear CruiseData Directory Read Permissions", "result": "Pass"})

    gearman_worker.send_job_status(job, 8, 10)

    output_results = set_ownerGroupPermissions(warehouseUser, cruiseDir)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set cruise directory ownership/permissions", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Set cruise directory ownership/permissions", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(job, 10, 10)

    return json.dumps(job_results)


def task_setCruiseDataDirectoryPermissions(gearman_worker, job):

    job_results = {'parts':[]}

    payloadObj = json.loads(job.data)
    logging.debug("Payload: {}".format(json.dumps(payloadObj, indent=2)))

    gearman_worker.send_job_status(job, 5, 10)

    warehouseUser = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir,gearman_worker.cruiseID)
    
    if gearman_worker.OVDM.showOnlyCurrentCruiseDir():
        logging.info("Clear read permissions")
        lockdown_directory(baseDir, cruiseDir)
        job_results['parts'].append({"partName": "Clear CruiseData Directory Read Permissions", "result": "Pass"})

    gearman_worker.send_job_status(job, 8, 10)

    if os.path.isdir(cruiseDir):
        logging.info("Clear read permissions")
        set_ownerGroupPermissions(warehouseUser, cruiseDir)
        job_results['parts'].append({"partName": "Set Directory Permissions for current cruise", "result": "Pass"})
        
    job_results['parts'].append({"partName": "Set CruiseData Directory Permissions", "result": "Pass"})
    gearman_worker.send_job_status(job, 10, 10)

    return json.dumps(job_results)


def task_rebuildCruiseDirectory(gearman_worker, job):

    job_results = {'parts':[]}

    payloadObj = json.loads(job.data)
    logging.debug("Payload: {}".format(json.dumps(payloadObj, indent=2)))

    warehouseUser = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir,gearman_worker.cruiseID)

    gearman_worker.send_job_status(job, 1, 10)

    if gearman_worker.OVDM.showOnlyCurrentCruiseDir():
        logging.info("Clear read permissions")
        lockdown_directory(baseDir, cruiseDir)
        job_results['parts'].append({"partName": "Clear CruiseData Directory Read Permissions", "result": "Pass"})

    if os.path.exists(cruiseDir):
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Pass"})
    else:
        errPrint("Cruise directory not found")
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Fail", "reason": "Unable to locate the cruise directory: " + cruiseDir})
        return json.dumps(job_results)

    gearman_worker.send_job_status(job, 2, 10)

    logging.info("Build directory list")
    directoryList = build_directorylist(gearman_worker)
    logging.debug("Directory List:")
    logging.debug(json.dumps(directoryList, indent=2))
    
    if len(directoryList) > 0:
        job_results['parts'].append({"partName": "Build Directory List", "result": "Pass"})
    else:
        errPrint("Directory list is empty")
        job_results['parts'].append({"partName": "Build Directory List", "result": "Fail", "reason": "Unable to build list of directories to create"})
        return json.dumps(job_results)
    
    gearman_worker.send_job_status(job, 5, 10)
    
    logging.info("Create directories")

    output_results = create_directories(directoryList)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Create Directories", "result": "Pass"})
    else:
        errPrint("Failed to create any/all of the cruise data directory structure")
        job_results['parts'].append({"partName": "Create Directories", "result": "Fail", "reason": output_results['reason']})

    gearman_worker.send_job_status(job, 7, 10)
    
    logging.info("Set directory ownership/permissions")

    output_results = set_ownerGroupPermissions(warehouseUser, cruiseDir)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set Directory ownership/permissions", "result": "Pass"})
    else:
        logging.error("Failed to set directory ownership")
        job_results['parts'].append({"partName": "Set Directory ownership/permissions", "result": "Fail", "reason": output_results['reason']})

    gearman_worker.send_job_status(job, 10, 10)
    
    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle Cruise data directory related tasks')
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

    logging.info("\tTask: createCruiseDirectory")
    new_worker.register_task("createCruiseDirectory", task_createCruiseDirectory)

    logging.info("\tTask: setCruiseDataDirectoryPermissions")
    new_worker.register_task("setCruiseDataDirectoryPermissions", task_setCruiseDataDirectoryPermissions)
    
    logging.info("\tTask: rebuildCruiseDirectory")
    new_worker.register_task("rebuildCruiseDirectory", task_rebuildCruiseDirectory)

    logging.info("Waiting for jobs...")
    new_worker.work()
