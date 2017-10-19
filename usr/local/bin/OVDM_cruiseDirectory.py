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
#      VERSION:  2.3
#      CREATED:  2015-01-01
#     REVISION:  2017-10-05
#
# LICENSE INFO: Open Vessel Data Management v2.3 (OpenVDMv2)
#               Copyright (C) OceanDataRat 2017
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
import errno
import gearman
import json
import time
import signal
import pwd
import grp
import openvdm

customTaskLookup = [
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

DEBUG = False
new_worker = None


def debugPrint(*args, **kwargs):
    if DEBUG:
        errPrint(*args, **kwargs)


def errPrint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def build_destDir(worker, destDir):
    
    returnDestDir = destDir.replace('{loweringID}', worker.loweringID)
    returnDestDir = returnDestDir.replace('{loweringDataBaseDir}', worker.shipboardDataWarehouseConfig['loweringDataBaseDir'],)
    returnDestDir = returnDestDir.replace('{cruiseID}', worker.cruiseID)
    return returnDestDir


def build_directorylist(worker):

    returnDirectories = []
    cruiseDir = os.path.join(worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'], worker.cruiseID)

    #debugPrint(worker.OVDM.getShowLoweringComponents())

    if worker.OVDM.getShowLoweringComponents():
      returnDirectories.append(os.path.join(cruiseDir, worker.shipboardDataWarehouseConfig['loweringDataBaseDir']))

    collectionSystemTransfers = worker.OVDM.getActiveCollectionSystemTransfers()

    for collectionSystemTransfer in collectionSystemTransfers:
        if collectionSystemTransfer['enable'] == "1" and collectionSystemTransfer['cruiseOrLowering'] == "0":
            destDir = build_destDir(worker, collectionSystemTransfer['destDir'])
            returnDirectories.append(os.path.join(cruiseDir, destDir))

    requiredExtraDirectories = worker.OVDM.getRequiredExtraDirectories()
    for requiredExtraDirectory in requiredExtraDirectories:
        destDir = build_destDir(worker, requiredExtraDirectory['destDir'])
        returnDirectories.append(os.path.join(cruiseDir, destDir))

    extraDirectories = worker.OVDM.getExtraDirectories()
    if extraDirectories:
        for extraDirectory in extraDirectories:
            if extraDirectory['enable'] == "1":
                destDir = build_destDir(worker, extraDirectory['destDir'])
                returnDirectories.append(os.path.join(cruiseDir, destDir))

    return returnDirectories


def create_directories(worker, directoryList):

    reason = []
    for directory in directoryList:
        try:
            os.makedirs(directory)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                errPrint("Unable to create directory:", directory)
                reason.append("Unable to create directory " + directory)
                
    if len(reason) > 0:
        return {'verdict': False, 'reason': reason.join('\n')}

    return {'verdict': True}


def setOwnerGroupPermissions(worker, path):

    warehouseUser = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']

    #debugPrint(warehouseUser)

    reason = []

    uid = pwd.getpwnam(warehouseUser).pw_uid
    gid = grp.getgrnam(warehouseUser).gr_gid
    # Set the file permission and ownership for the current directory

    if os.path.isfile(path):
        try:
            debugPrint("Setting ownership/permissions for", path)
            os.chown(path, uid, gid)
            os.chmod(path, 0644)
        except OSError:
            errPrint("Unable to set ownership/permissions for", path)
            reason.append("Unable to set ownership/permissions for " + path)

    else: #directory
        try:
            debugPrint("Setting ownership/permissions for", path)
            os.chown(path, uid, gid)
            os.chmod(path, 0755)
        except OSError:
            errPrint("Unable to set ownership/permissions for", path)
            reason.append("Unable to set ownership/permissions for " + path)

        for root, dirs, files in os.walk(path):
            for file in files:
                fname = os.path.join(root, file)
                try:
                    debugPrint("Setting ownership/permissions for", file)
                    os.chown(fname, uid, gid)
                    os.chmod(fname, 0644)
                except OSError:
                    errPrint("Unable to set ownership/permissions for", file)
                    reason.append("Unable to set ownership/permissions for " + file)

            for momo in dirs:
                dname = os.path.join(root, momo)
                try:
                    debugPrint("Setting ownership/permissions for", momo)
                    os.chown(dname, uid, gid)
                    os.chmod(dname, 0755)
                except OSError:
                    errPrint("Unable to set ownership/permissions for", momo)
                    reason.append("Unable to set ownership/permissions for " + momo)

    if len(reason) > 0:
        return {'verdict': False, 'reason': reason.join('\n')}

    return {'verdict': True}


def lockdown_directory(worker):
    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir,worker.cruiseID)
#    debugPrint('cruiseDir:', cruiseDir)

    dirContents = [ os.path.join(baseDir,f) for f in os.listdir(baseDir)]
    files = filter(os.path.isfile, dirContents)
    for file in files:
        os.chmod(file, 0600)

    directories = filter(os.path.isdir, dirContents)
    for directory in directories:
        if not directory == cruiseDir:
            os.chmod(directory, 0700)
#        else:
#            debugPrint('Skipping:', directory)


class OVDMGearmanWorker(gearman.GearmanWorker):

    def __init__(self, host_list=None):
        self.stop = False
        self.quit = False
        self.OVDM = openvdm.OpenVDM()
        self.cruiseID = ''
        self.loweringID = ''
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
        self.cruiseStartDate = self.OVDM.getCruiseStartDate()
        self.systemStatus = self.OVDM.getSystemStatus()
        if len(payloadObj) > 0:
            try:
                payloadObj['cruiseID']
            except KeyError:
                self.cruiseID = self.OVDM.getCruiseID()
            else:
                self.cruiseID = payloadObj['cruiseID']

            try:
                payloadObj['loweringID']
            except KeyError:
                self.loweringID = self.OVDM.getLoweringID()
            else:
                self.loweringID = payloadObj['loweringID']

        if int(self.task['taskID']) > 0:

            self.OVDM.setRunning_task(self.task['taskID'], os.getpid(), current_job.handle)
#        else:
#            self.OVDM.trackGearmanJob(taskLookup[current_job.task], os.getpid(), current_job.handle)

        errPrint("Job:", current_job.handle + ",", self.task['longName'], "started at:  ", time.strftime("%D %T", time.gmtime()))

        return super(OVDMGearmanWorker, self).on_job_execute(current_job)


    def on_job_exception(self, current_job, exc_info):
        errPrint("Job:", current_job.handle + ",", self.task['longName'], "failed at:   ", time.strftime("%D %T", time.gmtime()))

        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail", "reason": "Unknown"}]))
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
                    self.OVDM.setError_task(self.task['taskID'], resultsObj['parts'][-1]['reason'])
                else:
                    self.OVDM.sendMsg(self.task['longName'] + ' failed', resultsObj['parts'][-1]['reason'])
            else:
                if int(self.task['taskID']) > 0:
                    self.OVDM.setIdle_task(self.task['taskID'])
        else:
            if int(self.task['taskID']) > 0:
                self.OVDM.setIdle_task(self.task['taskID'])

        debugPrint('Job Results:', json.dumps(resultsObj, indent=2))

        errPrint("Job:", current_job.handle + ",", self.task['longName'], "completed at:", time.strftime("%D %T", time.gmtime()))

        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_results)


    def after_poll(self, any_activity):
        self.stop = False
        self.task = None
        if self.quit:
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


def task_createCruiseDirectory(worker, job):

    job_results = {'parts':[]}

    payloadObj = json.loads(job.data)
    debugPrint('Payload:', json.dumps(payloadObj, indent=2))

    worker.send_job_status(job, 1, 10)

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)


    if os.path.exists(baseDir):
        job_results['parts'].append({"partName": "Verify Base Directory exists", "result": "Pass"})
    else:
        errPrint("Failed to find base directory:", baseDir)
        job_results['parts'].append({"partName": "Verify Base Directory exists", "result": "Fail", "reason": "Failed to find base directory: " + baseDir})
        return json.dumps(job_results)


    if not os.path.exists(cruiseDir):
        job_results['parts'].append({"partName": "Verify Cruise Directory does not exists", "result": "Pass"})
    else:
        errPrint("Cruise directory already exists:", cruiseDir)
        job_results['parts'].append({"partName": "Verify Cruise Directory does not exists", "result": "Fail", "reason": "Cruise directory " + cruiseDir + " already exists"})
        return json.dumps(job_results)

    worker.send_job_status(job, 2, 10)

    directoryList = build_directorylist(worker)

    debugPrint('Directory List:', json.dumps(directoryList, indent=2))

    if len(directoryList) > 0:
        job_results['parts'].append({"partName": "Build Directory List", "result": "Pass"})
    else:
        errPrint("Directory list is empty")
        job_results['parts'].append({"partName": "Build Directory List", "result": "Fail", "reason": "Unable to build list of directories to create"})
        return json.dumps(job_results)

    worker.send_job_status(job, 5, 10)

    output_results = create_directories(worker, directoryList)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Create Directories", "result": "Pass"})
    else:
        errPrint("Failed to create any/all of the cruise data directory structure")
        job_results['parts'].append({"partName": "Create Directories", "result": "Fail", "reason": output_results['reason']})

    worker.send_job_status(job, 7, 10)

    if worker.OVDM.showOnlyCurrentCruiseDir():
        debugPrint("Clear read permissions for all cruise directories")
        lockdown_directory(worker)
        job_results['parts'].append({"partName": "Clear CruiseData Directory Read Permissions", "result": "Pass"})

    worker.send_job_status(job, 8, 10)

    output_results = setOwnerGroupPermissions(worker, cruiseDir)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set Directory Permissions", "result": "Pass"})
    else:
        errPrint("Failed to set directory ownership")
        job_results['parts'].append({"partName": "Set Directory Permissions", "result": "Fail", "reason": output_results['reason']})

    worker.send_job_status(job, 10, 10)

    return json.dumps(job_results)


def task_setCruiseDataDirectoryPermissions(worker, job):

    job_results = {'parts':[]}

    payloadObj = json.loads(job.data)
    debugPrint('Payload:', json.dumps(payloadObj, indent=2))

    worker.send_job_status(job, 5, 10)

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir,worker.cruiseID)
    
    if worker.OVDM.showOnlyCurrentCruiseDir():
        debugPrint("Clear read permissions")
        lockdown_directory(worker)
        job_results['parts'].append({"partName": "Clear CruiseData Directory Read Permissions", "result": "Pass"})

    worker.send_job_status(job, 8, 10)

    if os.path.isdir(cruiseDir):
        debugPrint("Clear read permissions")
        setOwnerGroupPermissions(worker, cruiseDir)
        job_results['parts'].append({"partName": "Set Directory Permissions for current cruise", "result": "Pass"})
        
    job_results['parts'].append({"partName": "Set CruiseData Directory Permissions", "result": "Pass"})
    worker.send_job_status(job, 10, 10)

    return json.dumps(job_results)

def task_rebuildCruiseDirectory(worker, job):

    job_results = {'parts':[]}

    payloadObj = json.loads(job.data)
    debugPrint('Payload:', json.dumps(payloadObj, indent=2))

    worker.send_job_status(job, 1, 10)

    if worker.OVDM.showOnlyCurrentCruiseDir():
        debugPrint("Clear read permissions")
        lockdown_directory(worker)
        job_results['parts'].append({"partName": "Clear CruiseData Directory Read Permissions", "result": "Pass"})

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    
    if os.path.exists(cruiseDir):
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Pass"})
    else:
        errPrint("Cruise directory not found")
        job_results['parts'].append({"partName": "Verify Cruise Directory exists", "result": "Fail", "reason": "Unable to locate the cruise directory: " + cruiseDir})
        return json.dumps(job_results)

    worker.send_job_status(job, 2, 10)

    debugPrint("Build directory list")
    directoryList = build_directorylist(worker)
    debugPrint('Directory List:', json.dumps(directoryList, indent=2))
    
    if len(directoryList) > 0:
        job_results['parts'].append({"partName": "Build Directory List", "result": "Pass"})
    else:
        errPrint("Directory list is empty")
        job_results['parts'].append({"partName": "Build Directory List", "result": "Fail", "reason": "Unable to build list of directories to create"})
        return json.dumps(job_results)
    
    worker.send_job_status(job, 5, 10)
    
    debugPrint("Create directories")

    output_results = create_directories(worker, directoryList)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Create Directories", "result": "Pass"})
    else:
        errPrint("Failed to create any/all of the cruise data directory structure")
        job_results['parts'].append({"partName": "Create Directories", "result": "Fail", "reason": output_results['reason']})

    worker.send_job_status(job, 7, 10)
    
    debugPrint("Set directory permissions")

    output_results = setOwnerGroupPermissions(worker, cruiseDir)

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Set Directory Permissions", "result": "Pass"})
    else:
        errPrint("Failed to set directory ownership")
        job_results['parts'].append({"partName": "Set Directory Permissions", "result": "Fail", "reason": output_results['reason']})

    worker.send_job_status(job, 10, 10)
    
    return json.dumps(job_results)

# -------------------------------------------------------------------------------------
# Main function of the script should it be run as a stand-alone utility.
# -------------------------------------------------------------------------------------
def main(argv):

    parser = argparse.ArgumentParser(description='Handle Cruise data directory related tasks')
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

    new_worker.set_client_id('cruiseDirectory.py')

    debugPrint('Registering worker tasks...')
    debugPrint('   Task:', 'createCruiseDirectory')
    new_worker.register_task("createCruiseDirectory", task_createCruiseDirectory)
    debugPrint('   Task:', 'setCruiseDataDirectoryPermissions')
    new_worker.register_task("setCruiseDataDirectoryPermissions", task_setCruiseDataDirectoryPermissions)
    debugPrint('   Task:', 'rebuildCruiseDirectory')
    new_worker.register_task("rebuildCruiseDirectory", task_rebuildCruiseDirectory)

    debugPrint('Waiting for jobs...')
    new_worker.work()

# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])

