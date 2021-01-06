# ----------------------------------------------------------------------------------- #
#
#         FILE:  run_ship_to_shore_transfer.py
#
#  DESCRIPTION:  Gearman worker that handles the transfer of data from the Shipboard
#                Data Warehouse to a Shoreside Data Warehouse.
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.5
#      CREATED:  2015-01-01
#     REVISION:  2021-01-05
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
import tempfile
import python3_gearman
import shutil
import json
import time
import calendar
import fnmatch
import subprocess
import signal
import logging
from random import randint

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.utils.output_JSONDataToFile import output_JSONDataToFile
from server.utils.set_ownerGroupPermissions import set_ownerGroupPermissions
from server.lib.openvdm import OpenVDM_API, DEFAULT_CRUISE_CONFIG_FN, DEFAULT_MD5_SUMMARY_FN, DEFAULT_MD5_SUMMARY_MD5_FN

def build_filelist(gearman_worker):

    logging.debug("Building filters")
    rawFilters = {'includeFilter':[]}
    shipToShoreTransfers = gearman_worker.OVDM.getShipToShoreTransfers() + gearman_worker.OVDM.getRequiredShipToShoreTransfers()

    logging.debug('shipToShoreTransfers: {}'.format(json.dumps(shipToShoreTransfers, indent=2)))
    
    for x in range(1, 6):
        for shipToShoreTransfer in shipToShoreTransfers:
            if shipToShoreTransfer['priority'] == str(x) and shipToShoreTransfer['enable'] == '1':
                if not shipToShoreTransfer['collectionSystem'] == "0":
                    collectionSystem = gearman_worker.OVDM.getCollectionSystemTransfer(shipToShoreTransfer['collectionSystem'])
                    rawFilters['includeFilter'] += ['*/' + gearman_worker.cruiseID + '/' + collectionSystem['destDir'] + '/' + shipToShoreFilter for shipToShoreFilter in shipToShoreTransfer['includeFilter'].split(',')]
                elif not shipToShoreTransfer['extraDirectory'] == "0":
                    extraDirectory = gearman_worker.OVDM.getExtraDirectory(shipToShoreTransfer['extraDirectory'])
                    rawFilters['includeFilter'] += ['*/' + gearman_worker.cruiseID + '/' + extraDirectory['destDir'] + '/' + shipToShoreFilter for shipToShoreFilter in shipToShoreTransfer['includeFilter'].split(',')]
                else:
                    rawFilters['includeFilter'] += ['*/' + gearman_worker.cruiseID + '/' + shipToShoreFilter for shipToShoreFilter in shipToShoreTransfer['includeFilter'].split(',')]

    logging.debug("Raw Filters: {}".format(json.dumps(rawFilters, indent=2)))
    
    procfilters = build_filters(gearman_worker, rawFilters)
    logging.debug("Processed Filters: {}".format(json.dumps(rawFilters, indent=2)))

    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)

    returnFiles = {'include':[], 'new':[], 'updated':[], 'exclude':[]}
    for root, dirnames, filenames in os.walk(cruiseDir):
        for filename in filenames:
            for includeFilter in procfilters['includeFilter']:
                if fnmatch.fnmatch(os.path.join(root, filename), includeFilter):
                    returnFiles['include'].append(os.path.join(root, filename))

    returnFiles['include'] = [filename.replace(cruiseDir + '/', '', 1) for filename in returnFiles['include']]

    logging.debug("Returned Files: {}".format(json.dumps(returnFiles, indent=2)))

    return { 'verdict': True, 'files': returnFiles }


def build_logfileDirPath(gearman_worker):

    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)

    return os.path.join(cruiseDir, gearman_worker.OVDM.getRequiredExtraDirectoryByName('Transfer_Logs')['destDir'])


def build_filters(gearman_worker, rawFilters):

    returnFilters = rawFilters
    returnFilters['includeFilter'] = [includeFilter.replace('{cruiseID}', gearman_worker.cruiseID) for includeFilter in returnFilters['includeFilter']]

    return returnFilters


def transfer_sshDestDir(gearman_worker, gearman_job):

    logging.debug("Transfer to SSH Server")

    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)

    logging.debug("Building file list")
    output_results = build_filelist(gearman_worker)

    if not output_results['verdict']:
        logging.error("Building list of files to transfer failed: {}".format(output_results['reason']))
        return output_results
    
    files = output_results['files']

    destDir = gearman_worker.cruiseDataTransfer['destDir'].rstrip('/')
            
    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    sshIncludeListPath = os.path.join(tmpdir, 'sshIncludeList.txt')
    
    fileIndex = 0
    fileCount = len(files['include'])

    try:
        with open(sshIncludeListPath, 'w') as sshIncludeFileListFile:
            sshIncludeFileListFile.write('\n'.join([os.path.join(gearman_worker.cruiseID, filename) for filename in files['include']]))

    except IOError:
        logging.debug("Error Saving temporary ssh include filelist file")
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return {'verdict': False, 'reason': 'Error Saving temporary ssh exclude filelist file: ' + sshIncludeListPath, 'files':[]}

    bandwidthLimit = '--bwlimit=' + gearman_worker.cruiseDataTransfer['bandwidthLimit'] if gearman_worker.cruiseDataTransfer['bandwidthLimit'] != '0' and gearman_worker.bandwidthLimitStatus  else '--bwlimit=20000000' # 20GB/s a.k.a. stupid big
    
    command = ['rsync', '-trim', bandwidthLimit, '--files-from=' + sshIncludeListPath, '-e', 'ssh', baseDir, gearman_worker.cruiseDataTransfer['sshUser'] + '@' + gearman_worker.cruiseDataTransfer['sshServer'] + ':' + destDir] if gearman_worker.cruiseDataTransfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.cruiseDataTransfer['sshPass'], 'rsync', '-trim', bandwidthLimit, '--files-from=' + sshIncludeListPath, '-e', 'ssh', baseDir, gearman_worker.cruiseDataTransfer['sshUser'] + '@' + gearman_worker.cruiseDataTransfer['sshServer'] + ':' + destDir]
    
    logging.debug("Transfer Command: {}".format(' '.join(command)))
    
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)
    
    while True:

        line = proc.stdout.readline().rstrip('\n')

        if proc.poll() is not None:
            break

        if not line:
            continue
        
        logging.debug("Line: {}".format(line))
        if line.startswith( '<f+++++++++' ):
            filename = line.split(' ',1)[1]
            files['new'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
        elif line.startswith( '<f.' ):
            filename = line.split(' ',1)[1]
            files['updated'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
            
        if gearman_worker.stop:
            logging.debug("Stopping")
            proc.terminate()
            break
    
    # files['new'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/').rstrip('/'),filename) for filename in files['new']]
    # files['updated'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/').rstrip('/'),filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return {'verdict': True, 'files': files}

        
class OVDMGearmanWorker(python3_gearman.GearmanWorker):

    def __init__(self):
        self.stop = False
        self.OVDM = OpenVDM_API()
        self.cruiseID = ''
        self.systemStatus = ''
        self.transferStartDate = ''
        self.cruiseDataTransfer = {}
        self.shipboardDataWarehouseConfig = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])
    
    def getShipToShoreTransfer(self):
        try:
            return list(filter(lambda transfer: transfer['name'] == 'SSDW', self.OVDM.getRequiredCruiseDataTransfers()))[0]
        except:
            logging.error("Could not find SSDW transfer configuration")

        return {}
        
    def on_job_execute(self, current_job):
        logging.debug("current_job: {}".format(current_job))

        payloadObj = json.loads(current_job.data)

        self.cruiseDataTransfer = self.getShipToShoreTransfer()
        if 'cruiseDataTransfer' in payloadObj:
            self.cruiseDataTransfer.update(payloadObj['cruiseDataTransfer'])
        self.systemStatus = payloadObj['systemStatus'] if 'systemStatus' in payloadObj else self.OVDM.getSystemStatus()

        if self.systemStatus == "Off" or self.cruiseDataTransfer['enable'] == '0':
            logging.info("Ship-to-shore Transfer job skipped because ship-to-shore transfers are currently disabled")
            return super(OVDMGearmanWorker, self).on_job_complete(current_job, json.dumps({'parts':[{"partName": "Transfer Enabled", "result": "Fail", "reason": "Transfer is disabled"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

        self.bandwidthLimitStatus = payloadObj['bandwidthLimitStatus'] if 'bandwidthLimitStatus' in payloadObj else self.OVDM.getShipToShoreBWLimitStatus()
        self.cruiseID = payloadObj['cruiseID'] if 'cruiseID' in payloadObj else self.OVDM.getCruiseID()
        self.loweringID = payloadObj['loweringID'] if 'loweringID' in payloadObj else self.OVDM.getLoweringID()
        self.transferStartDate = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        
        logging.info("Job: {}, Ship-to-Shore transfer started at: {}".format(current_job.handle, time.strftime("%D %T", time.gmtime())))

        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()

        return super(OVDMGearmanWorker, self).on_job_execute(current_job)

    
    def on_job_exception(self, current_job, exc_info):
        logging.error("Job: {}, {} transfer failed at: {}".format(current_job.handle, self.cruiseDataTransfer['name'], time.strftime("%D %T", time.gmtime())))
        
        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail", "reason": "Unknown"}]))
        self.OVDM.setError_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'], 'Worker crashed')

        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)


    def on_job_complete(self, current_job, job_results):
        resultsObj = json.loads(job_results)
        
        if len(resultsObj['parts']) > 0:
            if resultsObj['parts'][-1]['result'] == "Fail": # Final Verdict
                self.OVDM.setError_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'], resultsObj['parts'][-1]['reason'])
            else:
                self.OVDM.setIdle_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'])
        else:
            self.OVDM.setIdle_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'])

        logging.debug("Job Results: {}".format(json.dumps(resultsObj, indent=2)))
        logging.info("Job: {}, {} transfer completed at: {}".format(current_job.handle, self.cruiseDataTransfer['name'], time.strftime("%D %T", time.gmtime())))
            
        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_results)


    def stopTask(self):
        self.stop = True
        logging.warning("Stopping current task...")

    
    def quitWorker(self):
        self.stop = True
        logging.warning("Quitting worker...")
        self.shutdown()

        
def task_runShipToShoreTransfer(gearman_worker, current_job):

    time.sleep(randint(0,2))
    
    job_results = {
        'parts': [
            {"partName": "Transfer In-Progress", "result": "Pass"},
            {"partName": "Transfer Enabled", "result": "Pass"}
        ],
        'files':[]
    }

    warehouseUser = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']

    logging.debug("Setting transfer status to 'Running'")
    gearman_worker.OVDM.setRunning_cruiseDataTransfer(gearman_worker.cruiseDataTransfer['cruiseDataTransferID'], os.getpid(), current_job.handle)
   
    logging.info("Testing configuration")
    gearman_worker.send_job_status(current_job, 1, 10)

    gm_client = python3_gearman.GearmanClient([gearman_worker.OVDM.getGearmanServer()])
    
    gmData = {
        'cruiseDataTransfer': gearman_worker.cruiseDataTransfer,
        'cruiseID': gearman_worker.cruiseID
    }
    
    completed_job_request = gm_client.submit_job("testCruiseDataTransfer", json.dumps(gmData))
    resultsObj = json.loads(completed_job_request.result)

    logging.debug('Connection Test Results: {}'.format(json.dumps(resultsObj, indent=2)))

    if resultsObj['parts'][-1]['result'] == "Pass": # Final Verdict
        logging.debug("Connection test passed")
        job_results['parts'].append({"partName": "Connection Test", "result": "Pass"})
    else:
        logging.warning("Connection test failed, quitting job")
        job_results['parts'].append({"partName": "Connection Test", "result": "Fail", "reason": resultsObj['parts'][-1]['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(current_job, 2, 10)
    
    logging.info("Transferring files")
    output_results = None
    if  gearman_worker.cruiseDataTransfer['transferType'] == "4": # SSH Server
        output_results = transfer_sshDestDir(gearman_worker, current_job)
    else:
        logging.error("Unknown Transfer Type")
        job_results['parts'].append({"partName": "Transfer Files", "result": "Fail", "reason": "Unknown transfer type"})
        return json.dumps(job_results)
    
    if not output_results['verdict']:
        logging.error("Transfer of remote files failed: {}".format(output_results['reason']))
        job_results['parts'].append({"partName": "Transfer Files", "result": "Fail", "reason": output_results['reason']})
        return job_results

    logging.debug("Transfer completed successfully")
    job_results['files'] = output_results['files']
    job_results['parts'].append({"partName": "Transfer Files", "result": "Pass"})

    if len(job_results['files']['new']) > 0:
        logging.debug("{} file(s) added".format(len(job_results['files']['new'])))
    if len(job_results['files']['updated']) > 0:
        logging.debug("{} file(s) updated".format(len(job_results['files']['updated'])))
    if len(job_results['files']['exclude']) > 0:
        logging.debug("{} file(s) intentionally skipped".format(len(job_results['files']['exclude'])))

    gearman_worker.send_job_status(current_job, 9, 10)

    if job_results['files']['new'] or job_results['files']['updated']:

        logging.debug("Building logfiles")

        logfileName = gearman_worker.cruiseDataTransfer['name'] + '_' + gearman_worker.transferStartDate + '.log'

        logContents = {
            'files': {
                'new': job_results['files']['new'],
                'updated': job_results['files']['updated']
            }
        }

        output_results = output_JSONDataToFile(os.path.join(build_logfileDirPath(gearman_worker), logfileName), logContents['files'])

        if output_results['verdict']:
            job_results['parts'].append({"partName": "Write transfer logfile", "result": "Pass"})
        else:
            logging.error("Error writing transfer logfile: {}".format(logfileName))
            job_results['parts'].append({"partName": "Write transfer logfile", "result": "Fail", "reason": output_results['reason']})
            return json.dumps(job_results)
    
        output_results = set_ownerGroupPermissions(warehouseUser, os.path.join(build_logfileDirPath(gearman_worker), logfileName))

        if not output_results['verdict']:
            job_results['parts'].append({"partName": "Set OpenVDM config file ownership/permissions", "result": "Fail", "reason": output_results['reason']})
            return json.dumps(job_results)

    gearman_worker.send_job_status(current_job, 10, 10)
    
    time.sleep(2)

    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle ship-to-shore transfer related tasks')
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

    logging.info("\tTask: runShipToShoreTransfer")
    new_worker.register_task("runShipToShoreTransfer", task_runShipToShoreTransfer)

    logging.info("Waiting for jobs...")
    new_worker.work()
