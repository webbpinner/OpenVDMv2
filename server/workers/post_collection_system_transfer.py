# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_post_collection_system_transfer.py
#
#  DESCRIPTION:  Gearman worker that run user-defined scripts following the completion
#                of the runCollectionSystemTransfer tasks.
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.5
#      CREATED:  2016-02-09
#     REVISION:  2020-12-30
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
import signal
import time
import subprocess
import logging

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.lib.openvdm import OpenVDM_API
from server.utils.read_config import read_config

customTasks = [
    {
        "taskID": "0",
        "name": "postCollectionSystemTransfer",
        "longName": "Post Collection System Transfer",
    }
]

commandFile = '/usr/local/etc/openvdm/postCollectionSystemTransfer.yaml'


def getCommands(gearman_worker):

    try:
        commandsFromFile = read_config(commandFile)

    except Exception as err:
        logging.error(str(err))
        return {"verdict": False, "reason": "Could not process command file: " + commandFile}
    
    returnCommandList = list(filter(lambda collectionSystem: collectionSystem['collectionSystemTransferName'] == gearman_worker.collectionSystemTransfer['name'], commandsFromFile))
    returnCommandList = returnCommandList[0]['commandList'] if len(returnCommandList) > 0 and 'commandList' in returnCommandList[0] else []

    for command in returnCommandList:
        logging.debug("Raw Command: {}".format(json.dumps(command)))
        command['command'] = [arg.replace('{cruiseID}', gearman_worker.cruiseID) for arg in command['command']]
        command['command'] = [arg.replace('{loweringID}', gearman_worker.loweringID) for arg in command['command']]
        command['command'] = [arg.replace('{collectionSystemTransferID}', gearman_worker.collectionSystemTransfer['collectionSystemTransferID']) for arg in command['command']]
        command['command'] = [arg.replace('{collectionSystemTransferName}', gearman_worker.collectionSystemTransfer['name']) for arg in command['command']]
        command['command'] = [arg.replace('{newFiles}', json.dumps(gearman_worker.files['new'])) for arg in command['command']]
        command['command'] = [arg.replace('{updatedFiles}', json.dumps(gearman_worker.files['updated']) ) for arg in command['command']]
                
        logging.debug("Processed Command: {}".format(json.dumps(returnCommandList)))

    return {"verdict": True, "commandList": returnCommandList}
    

def runCommands(gearman_worker, commands):    

    reasons = []

    for command in commands: 
        try:
            logging.info("Executing: {}".format(' '.join(command['command'])))
            proc = subprocess.run(command['command'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if len(proc.stdout) > 0:
                logging.debug("stdout: {}".format(proc.stdout))
                
            if len(proc.stderr) > 0:
                logging.debug("stderr: {}".format(proc.stderr))

        except:
            logging.error("Error executing the {} command: ()".format(command['name'], ' '.join(command['command'])))
            gearman_worker.OVDM.sendMsg("Error executing postCollectionSystemTransfer script", command['name'])
            reasons.append("Error executing postCollectionSystemTransfer script: " + command['name'])

    if len(reasons) > 0:
        return {"verdict": False, "reason": reasons.join("\n")}

    return {"verdict": True}

class OVDMGearmanWorker(python3_gearman.GearmanWorker):
    
    def __init__(self, host_list=None):
        self.stop = False
        self.OVDM = OpenVDM_API()
        self.task = None
        self.files = {}
        self.cruiseID = ''
        self.loweringID = ''
        self.collectionSystemTransfer = {}
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
            self.OVDM.trackGearmanJob(self.task['longName'], os.getpid(), current_job.handle)

        logging.info("Job: {} ({}) started at: {}".format(self.task['longName'], current_job.handle, time.strftime("%D %T", time.gmtime())))
        
        self.files = payloadObj['files'] if 'files' in payloadObj else { 'new':[], 'updated':[] } 
        self.cruiseID = payloadObj['cruiseID'] if 'cruiseID' in payloadObj else self.OVDM.getCruiseID()
        self.loweringID = payloadObj['loweringID'] if 'loweringID' in payloadObj else self.OVDM.getLoweringID()
        self.collectionSystemTransfer =  self.OVDM.getCollectionSystemTransfer(payloadObj['collectionSystemTransferID']) if 'collectionSystemTransferID' in payloadObj else {'name': 'Unknown'}
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

        
def task_postCollectionSystemTransfer(gearman_worker, gearman_job):

    job_results = {'parts':[]}

    payloadObj = json.loads(gearman_job.data)
    logging.debug("Payload: {}".format(json.dumps(payloadObj, indent=2)))
    
    gearman_worker.send_job_status(gearman_job, 1, 10)
    
    #check to see if file exists, if False, end task.
    if not os.path.isfile(commandFile):
        logging.warning("Command file not found: {}".format(commandFile))
        return json.dumps(job_results)

    gearman_worker.send_job_status(gearman_job, 2, 10)

    logging.info("Retrieving Commands")
    output_results = getCommands(gearman_worker)
    
    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Get Commands", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    job_results['parts'].append({"partName": "Get Commands", "result": "Pass"})
        
    gearman_worker.send_job_status(gearman_job, 3, 10)

    logging.info("Running Commands")
    output_results = runCommands(gearman_worker, output_results['commandList'])

    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Running commands", "result": "Fail", "reason": output_results['reason']})
    else:
        job_results['parts'].append({"partName": "Running commands", "result": "Pass"})

    gearman_worker.send_job_status(gearman_job, 10, 10)

    return json.dumps(job_results)   


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle Post Collection System Transfer related tasks')
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

    logging.info("\tTask: postCollectionSystemTransfer")
    new_worker.register_task("postCollectionSystemTransfer", task_postCollectionSystemTransfer)

    logging.info("Waiting for jobs...")
    new_worker.work()
