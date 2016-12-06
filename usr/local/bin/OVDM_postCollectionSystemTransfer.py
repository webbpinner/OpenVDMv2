# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_postCollectioSystemTransfer.py
#
#  DESCRIPTION:  Gearman worker that run user-defined scripts following the completion
#                of the runCollectionSystemTransfer tasks.
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.2
#      CREATED:  2016-02-09
#     REVISION:  2016-12-6
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
import gearman
import shutil
import errno
import json
import signal
import time
import subprocess
import yaml
import openvdm


customTaskLookup = [
    {
        "taskID": "0",
        "name": "postCollectionSystemTransfer",
        "longName": "Post Collection System Transfer",
    }
]

commandFile = '/usr/local/etc/openvdm/postCollectionSystemTransfer.yaml'

DEBUG = False
new_worker = None


def debugPrint(*args, **kwargs):
    global DEBUG
    if DEBUG:
        errPrint(*args, **kwargs)


def errPrint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def getCommands(worker):

    try:
        f = open(commandFile, 'r')
        collectionSystemCommands = yaml.load(f.read())
        f.close()
    except:
        errPrint("ERROR: Could not process configuration file:", commandFile + "!")
        return None
    
    if collectionSystemCommands:
        debugPrint("commands to process")
        for collectionSystemCommand in collectionSystemCommands:
            if collectionSystemCommand['collectionSystemTransferName'] == worker.collectionSystemTransfer['name']:
                #debugPrint('CollectionSystem Command:',json.dumps(collectionSystemCommand))
                returnCommandList = collectionSystemCommand['commandList']
                debugPrint(json.dumps(returnCommandList))
                for command in returnCommandList:
                    debugPrint("Raw Command:", json.dumps(command))
                    #print "Replacing cruiseID"
                    command['command'] = [arg.replace('{cruiseID}', worker.cruiseID) for arg in command['command']]
                    #print "Replacing collectionSystemTransferID"
                    command['command'] = [arg.replace('{collectionSystemTransferID}', worker.collectionSystemTransfer['collectionSystemTransferID']) for arg in command['command']]
                    #print "Replacing collectionSystemTransferName"
                    command['command'] = [arg.replace('{collectionSystemTransferName}', worker.collectionSystemTransfer['name']) for arg in command['command']]
                    #print "Replacing newFiles"
                    command['command'] = [arg.replace('{newFiles}', "'" + json.dumps(worker.files['new']) + "'") for arg in command['command']]
                    #print "Replacing updatedFiles"
                    command['command'] = [arg.replace('{updatedFiles}', "'" + json.dumps(worker.files['updated']) + "'" ) for arg in command['command']]
                    
                debugPrint("Processed Command:", json.dumps(returnCommandList))
                return returnCommandList
    else:
        debugPrint('Command list file is empty')

    return []
    

def runCommands(commands, worker):    

    for command in commands:
    
        try:
            s = ' '
            debugPrint("Executing:", s.join(command['command']))
            proc = subprocess.Popen(command['command'], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            out, err = proc.communicate()            
            
            if len(out) > 0:
                debugPrint("stdout:")
                debugPrint(out)
                
            if len(err) > 0:
                errPrint("stderr:")
                errPrint(err)

        except:
            errPrint("Error executing the: " + command['name'] + " script: ", s.join(command['command']))
            worker.OVDM.sendMsg("Error executing postCollectionSystemTransfer script", command['name'])

class OVDMGearmanWorker(gearman.GearmanWorker):
    
    def __init__(self, host_list=None):
        self.stop = False
        self.quit = False
        self.OVDM = openvdm.OpenVDM()
        self.cruiseID = ''
        self.collectionSystemTransfer = {}
        self.files = {}
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
            	debugPrint("Using current CruiseID")
            else:
                self.cruiseID = payloadObj['cruiseID']
                debugPrint('Setting cruiseID to:', self.cruiseID)

        if len(payloadObj) > 0:
            try:
                payloadObj['files']
            except KeyError:
                self.files = {
                    "new": [],
                    "updated": []
                }
            else:
                self.files = payloadObj['files']

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

        
def task_postCollectionSystemTransfer(worker, job):

    job_results = {'parts':[]}

    payloadObj = json.loads(job.data)
    debugPrint('Payload:', json.dumps(payloadObj, indent=2))
    
    worker.send_job_status(job, 1, 10)
    
    #check to see if file exists, if False, end task.
    if not os.path.isfile(commandFile):
        return json.dumps(job_results)

    worker.send_job_status(job, 2, 10)

    
    #print "Get Commands"
    commandsForCollectionSystem = getCommands(worker)
    
    if commandsForCollectionSystem == None:
        job_results['parts'].append({"partName": "Get Commands", "result": "Fail"})
        return json.dumps(job_results)
    else:
        job_results['parts'].append({"partName": "Get Commands", "result": "Pass"})
        debugPrint("Commands:", json.dumps(commandsForCollectionSystem, indent=2))
        if len(commandsForCollectionSystem) == 0:
            #debugPrint("Nothing to do")
            return json.dumps(job_results)
    
    worker.send_job_status(job, 3, 10)

    debugPrint("Run Commands")
    runCommands(commandsForCollectionSystem, worker)

    debugPrint("done")
    
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

    new_worker.set_client_id('postCollectionSystemTransfer.py')

    debugPrint('Registering worker tasks...')
    debugPrint('   Task:', 'postCollectionSystemTransfer')
    new_worker.register_task("postCollectionSystemTransfer", task_postCollectionSystemTransfer)

    debugPrint('Waiting for jobs...')
    new_worker.work()

# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])