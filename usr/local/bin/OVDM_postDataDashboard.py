# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_postDataDashboard.py
#
#  DESCRIPTION:  Gearman worker that run user-defined scripts following the completion
#                of the updateDataDashboard and rebuildDataDashboard tasks.
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.0
#      CREATED:  2016-02-08
#     REVISION:  
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
import errno
import json
import signal
import time
import subprocess
import openvdm

taskLookup = {
    "postDataDashboard": "Post Data Dashboard Processing",
}

collectionSystemCommands = [
    {
        'collectionSystemTransferName': 'SCS',
        'commandList': [
            {
                'name':'placebo',
                'command':['python', '/usr/local/bin/placebo.py', '{cruiseID}']
            }
        ]
    }
]


def getCommands(worker):
    
    #print json.dumps(collectionSystemCommands)
    for collectionSystemCommand in collectionSystemCommands:
        if collectionSystemCommand['collectionSystemTransferName'] == worker.collectionSystemTransfer['name']:
            #print json.dumps(collectionSystemCommand)
            returnCommandList = collectionSystemCommand['commandList']
            #print json.dumps(returnCommandList) 
            for command in returnCommandList:
                #print json.dumps(command)
                command['command'] = [arg.replace('{cruiseID}', worker.cruiseID) for arg in command['command']]
                command['command'] = [arg.replace('{collectionSystemTransferID}', worker.collectionSystemTransfer['collectionSystemTransferID']) for arg in command['command']]
                command['command'] = [arg.replace('{collectionSystemTransferName}', worker.collectionSystemTransfer['name']) for arg in command['command']]
                
            #print json.dumps(returnCommandList) 
            return returnCommandList

    return []
    

def runCommands(commands):    

    for command in commands:
        
        #s = ' '
        #print s.join(command['command'])
    
        try:
            proc = subprocess.Popen(command['command'], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            out, err = proc.communicate()
            
            print "stdout: " + out
            print "stderr: " + err

        except:
            print "Error executing the " + command['name'] + " script: ", s.join(command['command'])
                        

class OVDMGearmanWorker(gearman.GearmanWorker):
    
    def __init__(self, host_list=None):
        self.stop = False
        self.quit = False
        self.OVDM = openvdm.OpenVDM()
        self.cruiseID = ''
        self.collectionSystemTransfer = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])
    

    def on_job_execute(self, current_job):
        payloadObj = json.loads(current_job.data)
        
        self.cruiseID = self.OVDM.getCruiseID()
        self.collectionSystemTransfer = self.OVDM.getCollectionSystemTransfer(payloadObj['collectionSystemTransferID'])
        if len(payloadObj) > 1:
            try:
                payloadObj['cruiseID']
            except KeyError:
                self.cruiseID = self.OVDM.getCruiseID()
            else:
                self.cruiseID = payloadObj['cruiseID']
    
        self.OVDM.trackGearmanJob(taskLookup[current_job.task], os.getpid(), current_job.handle)
            
        print "Job: " + current_job.handle + ", " + taskLookup[current_job.task] + " started at:   " + time.strftime("%D %T", time.gmtime())
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)
            

    def on_job_exception(self, current_job, exc_info):
        print "Job: " + current_job.handle + ", " + taskLookup[current_job.task] + " failed at:    " + time.strftime("%D %T", time.gmtime())
        
        self.send_job_data(current_job, json.dumps([{"partName": "Unknown Part of Task", "result": "Fail"}]))
        self.OVDM.sendMsg(taskLookup[current_job.task] + ' failed: Unknown Part of Task')
        
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)

    
    def on_job_complete(self, current_job, job_result):
        resultObj = json.loads(job_result)
        
        if len(resultObj['parts']) > 0:
            if resultObj['parts'][-1]['result'] == "Fail": # Final Verdict
                    self.OVDM.sendMsg(taskLookup[current_job.task] + ' failed: ' + resultObj['parts'][-1]['partName'])
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

        
def task_postDataDashboard(worker, job):

    job_results = {'parts':[]}
    
    worker.send_job_status(job, 1, 10)
    
    commandsForCollectionSystem = getCommands(worker)
    runCommands(commandsForCollectionSystem)

    print "done"
    
    worker.send_job_status(job, 10, 10)

    return json.dumps(job_results)    


global new_worker
new_worker = OVDMGearmanWorker()


def sigquit_handler(_signo, _stack_frame):
    print "Stopping"
    new_worker.stopTask()

    
def sigint_handler(_signo, _stack_frame):
    print "Quitting"
    new_worker.quitWorker()
    
    
signal.signal(signal.SIGQUIT, sigquit_handler)
signal.signal(signal.SIGINT, sigint_handler)

new_worker.set_client_id('dataDashboard.py')
new_worker.register_task("postDataDashboard", task_postDataDashboard)
new_worker.work()
