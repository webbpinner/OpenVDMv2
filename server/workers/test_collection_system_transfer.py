# ----------------------------------------------------------------------------------- #
#
#         FILE:  test_collection_system_transfer.py
#
#  DESCRIPTION:  Gearman worker that handles testing collection system transfer
#                configurations
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.5
#      CREATED:  2015-01-01
#     REVISION:  2021-01-06
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
import subprocess
import signal
import logging

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.lib.openvdm import OpenVDM_API

def build_destDir(gearman_worker):
    
    return gearman_worker.collectionSystemTransfer['destDir'].replace('{cruiseID}', gearman_worker.cruiseID).replace('{loweringID}', gearman_worker.loweringID).replace('{loweringDataBaseDir}', gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir']).rstrip('/')


def build_sourceDir(gearman_worker):
    
    return gearman_worker.collectionSystemTransfer['sourceDir'].replace('{cruiseID}', gearman_worker.cruiseID).replace('{loweringID}', gearman_worker.loweringID).replace('{loweringDataBaseDir}', gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir']).rstrip('/')


def test_localSourceDir(gearman_worker):
    returnVal = []

    sourceDir = build_sourceDir(gearman_worker)
    logging.debug("Source Dir: {}".format(sourceDir))

    if not os.path.isdir(sourceDir):
        returnVal.append({"testName": "Source Directory", "result": "Fail", "reason": "Unable to find source directory: {} on the Data Warehouse".format(sourceDir)})
        if gearman_worker.collectionSystemTransfer['localDirIsMountPoint'] == '1':
            returnVal.append({"testName": "Source Directory is a Mountpoint", "result": "Fail", "reason": "Unable to find source directory: {} on the Data Warehouse".format(sourceDir)})
    else:
        returnVal.append({"testName": "Source Directory", "result": "Pass"})

        if gearman_worker.collectionSystemTransfer['localDirIsMountPoint'] == '1':
            if not os.path.ismount(sourceDir):
                returnVal.append({"testName": "Source Directory is a Mountpoint", "result": "Fail", "reason": "Source directory: {} is not a mountpoint on the Data Warehouse".format(sourceDir)})
            else:
                returnVal.append({"testName": "Source Directory is a Mountpoint", "result": "Pass"})

    return returnVal

    
def test_smbSourceDir(gearman_worker):
    returnVal = []

    # Create temp directory
    tmpdir = tempfile.mkdtemp()


    # Verify the server exists
    server_test_command = ['smbclient', '-L', gearman_worker.collectionSystemTransfer['smbServer'], '-W', gearman_worker.collectionSystemTransfer['smbDomain'], '-m', 'SMB2', '-g', '-N'] if gearman_worker.collectionSystemTransfer['smbUser'] == 'guest' else ['smbclient', '-L', gearman_worker.collectionSystemTransfer['smbServer'], '-W', gearman_worker.collectionSystemTransfer['smbDomain'], '-m', 'SMB2', '-g', '-U', gearman_worker.collectionSystemTransfer['smbUser'] + '%' + gearman_worker.collectionSystemTransfer['smbPass']]
    logging.debug('SMB Server test command: {}'.format(' '.join(server_test_command)))

    proc = subprocess.run(server_test_command, capture_output=True, text=True)

    vers = "2.1"
    foundServer = False
    for line in proc.stdout.splitlines():
        logging.debug('STDOUT Line: {}'.format(line.rstrip('\n'))) # yield line
        if line.startswith( 'Disk' ):
            foundServer = True
            break

    for line in proc.stderr.splitlines():
        logging.debug('STDERR Line: {}'.format(line.rstrip('\n'))) # yield line
        if line.startswith('OS=[Windows 5.1]'):
            vers="1.0"

    if not foundServer:
        logging.warning("Server Test Failed")
        returnVal.extend([
            {"testName": "SMB Server", "result": "Fail", "reason": "Could not connect to SMB Server: {} as {}".format(gearman_worker.collectionSystemTransfer['smbServer'], gearman_worker.collectionSystemTransfer['smbUser'])},
            {"testName": "SMB Share", "result": "Fail", "reason": "Could not connect to SMB Server: {} as {}".format(gearman_worker.collectionSystemTransfer['smbServer'], gearman_worker.collectionSystemTransfer['smbUser'])},
            {"testName": "Source Directory", "result": "Fail", "reason": "Could not connect to SMB Server: {} as {}".format(gearman_worker.collectionSystemTransfer['smbServer'], gearman_worker.collectionSystemTransfer['smbUser'])}
        ])

        return returnVal

    returnVal.append({"testName": "SMB Server", "result": "Pass"})

    # Create mountpoint
    mntPoint = os.path.join(tmpdir, 'mntpoint')
    os.mkdir(mntPoint, 0o755)
    

    # Mount SMB Share
    mount_command = ['sudo', 'mount', '-t', 'cifs', gearman_worker.collectionSystemTransfer['smbServer'], mntPoint, '-o', 'ro'+',guest'+',domain='+gearman_worker.collectionSystemTransfer['smbDomain']+',vers='+vers] if gearman_worker.collectionSystemTransfer['smbUser'] == 'guest' else ['sudo', 'mount', '-t', 'cifs', gearman_worker.collectionSystemTransfer['smbServer'], mntPoint, '-o', 'ro'+',username='+gearman_worker.collectionSystemTransfer['smbUser']+',password='+gearman_worker.collectionSystemTransfer['smbPass']+',domain='+gearman_worker.collectionSystemTransfer['smbDomain']+',vers='+vers]

    logging.debug("Mount command: {}".format(' '.join(mount_command)))

    proc = subprocess.run(mount_command, capture_output=True)

    if proc.returncode != 0:
        logging.warning("Connection test failed")
        returnVal.extend([
            {"testName": "SMB Share", "result": "Fail", "reason": "Could not connect to SMB Share: {} as {}".format( gearman_worker.collectionSystemTransfer['smbServer'],  gearman_worker.collectionSystemTransfer['smbUser'])},
            {"testName": "Source Directory", "result": "Fail", "reason": "Could not connect to SMB Share: {} as {}".format( gearman_worker.collectionSystemTransfer['smbServer'],  gearman_worker.collectionSystemTransfer['smbUser'])}
        ])
    
        # Unmount SMB Share
        if os.path.ismount(mntPoint):
            subprocess.call(['sudo', 'umount', mntPoint])

        # Cleanup
        shutil.rmtree(tmpdir)

        return returnVal

    returnVal.append({"testName": "SMB Share", "result": "Pass"})

    sourceDir = os.path.join(mntPoint, build_sourceDir(gearman_worker))

    logging.debug('Source Dir: {}'.format(sourceDir))
    if os.path.isdir(sourceDir):
        returnVal.append({"testName": "Source Directory", "result": "Pass"})
    else:
        logging.warning("Source Directory Test Failed")
        returnVal.append({"testName": "Source Directory", "result": "Fail", "reason": "Unable to find source directory: {} within the SMB Share: {}".format(sourceDir, gearman_worker.collectionSystemTransfer['smbServer'])})

    # Unmount SMB Share
    if os.path.ismount(mntPoint):
        subprocess.call(['sudo', 'umount', mntPoint])

    # Cleanup
    shutil.rmtree(tmpdir)

    return returnVal


def test_rsyncSourceDir(gearman_worker):
    
    returnVal = []

    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    rsyncPasswordFilePath = os.path.join(tmpdir,'passwordFile')

    try:

        logging.debug("Saving rsync password file {}".format(rsyncPasswordFilePath))
        with open(rsyncPasswordFilePath, 'w') as rsyncPasswordFile:

            if gearman_worker.collectionSystemTransfer['rsyncUser'] != 'anonymous':
                rsyncPasswordFile.write(gearman_worker.collectionSystemTransfer['rsyncPass'])
            else:
                rsyncPasswordFile.write('')                

    except IOError:
        logging.error("Error Saving temporary rsync password file {}".format(rsyncPasswordFilePath))
        returnVal.append({"testName": "Writing temporary rsync password file", "result": "Fail", "reason": "Unable to create temporary rsync password file: {}".format(rsyncPasswordFilePath)})

        # Cleanup
        shutil.rmtree(tmpdir)

        return returnVal

    os.chmod(rsyncPasswordFilePath, 0o600)

    server_test_command = ['rsync', '--no-motd', '--password-file=' + rsyncPasswordFilePath, 'rsync://' + gearman_worker.collectionSystemTransfer['rsyncUser'] + '@' + gearman_worker.collectionSystemTransfer['rsyncServer']]

    logging.debug('Server test command: {}'.format(' '.join(server_test_command)))

    proc = subprocess.run(server_test_command, capture_output=True)

    if proc.returncode != 0:
        logging.warning("Connection test failed")
        returnVal.extend([
            {"testName": "Rsync Connection", "result": "Fail", "reason": "Unable to connect to rsync server: {} as {}".format(gearman_worker.collectionSystemTransfer['rsyncServer'], gearman_worker.collectionSystemTransfer['rsyncUser'])},
            {"testName": "Source Directory", "result": "Fail", "reason": "Unable to connect to rsync server: {} as {}".format(gearman_worker.collectionSystemTransfer['rsyncServer'], gearman_worker.collectionSystemTransfer['rsyncUser'])}
        ])

    else:
        returnVal.append({"testName": "Rsync Connection", "result": "Pass"})

        sourceDir = build_sourceDir(gearman_worker)
        logging.debug('Source Dir: {}'.format(sourceDir))

        source_test_command = ['rsync', '--no-motd', '--password-file=' + rsyncPasswordFilePath, 'rsync://' + gearman_worker.collectionSystemTransfer['rsyncUser'] + '@' + gearman_worker.collectionSystemTransfer['rsyncServer'] + sourceDir]

        logging.debug('Source test command: {}'.format(' '.join(source_test_command)))

        proc = subprocess.run(source_test_command, capture_output=True)

        if proc.returncode != 0:
            logging.warning("Source Directory Test Failed")
            returnVal.append({"testName": "Source Directory", "result": "Fail", "reason": "Unable to find source directory: " + sourceDir + " on the Rsync Server: " + gearman_worker.collectionSystemTransfer['rsyncServer']})
        else:
            returnVal.append({"testName": "Source Directory", "result": "Pass"})

    # Cleanup
    shutil.rmtree(tmpdir)
        
    return returnVal


def test_sshSourceDir(gearman_worker):
    
    returnVal = []

    server_test_command = ['ssh', gearman_worker.collectionSystemTransfer['sshServer'], '-l', gearman_worker.collectionSystemTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PasswordAuthentication=no', 'ls'] if gearman_worker.collectionSystemTransfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.collectionSystemTransfer['sshPass'], 'ssh', gearman_worker.collectionSystemTransfer['sshServer'], '-l', gearman_worker.collectionSystemTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PubkeyAuthentication=no', 'ls']

    logging.debug('Server test command: {}'.format(' '.join(server_test_command)))
    
    proc = subprocess.run(server_test_command, capture_output=True)

    if proc.returncode != 0:
        logging.warning("Connection test failed")
        returnVal.extend([
            {"testName": "SSH Connection", "result": "Fail", "reason": "Unable to connect to ssh server: {} as {}".format(gearman_worker.collectionSystemTransfer['sshServer'], gearman_worker.collectionSystemTransfer['sshUser'])},
            {"testName": "Source Directory", "result": "Fail", "reason":"Unable to connect to ssh server: {} as {}".format(gearman_worker.collectionSystemTransfer['sshServer'], gearman_worker.collectionSystemTransfer['sshUser'])}
        ])

        return returnVal
    else:
        returnVal.append({"testName": "SSH Connection", "result": "Pass"})

        sourceDir = build_sourceDir(gearman_worker)
        logging.debug('Source Dir: {}'.format(sourceDir))

        source_test_command = ['ssh', gearman_worker.collectionSystemTransfer['sshServer'], '-l', gearman_worker.collectionSystemTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PasswordAuthentication=no', 'ls', sourceDir] if gearman_worker.collectionSystemTransfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.collectionSystemTransfer['sshPass'], 'ssh', gearman_worker.collectionSystemTransfer['sshServer'], '-l', gearman_worker.collectionSystemTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PubkeyAuthentication=no', 'ls', sourceDir]
        
        logging.debug('Source test command: {}'.format(' '.join(source_test_command)))
    
        proc = subprocess.run(source_test_command, capture_output=True)

        if proc.returncode != 0:
            logging.warning("Source directory test failed")
            returnVal.append({"testName": "Source Directory", "result": "Fail", "reason": "Unable to find source directory: {} on the SSH Server: {}".format(sourceDir, gearman_worker.collectionSystemTransfer['sshServer'])})
        else:
            returnVal.append({"testName": "Source Directory", "result": "Pass"})
        
    return returnVal


def test_destDir(gearman_worker):

    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)

    destDir = os.path.join(cruiseDir, build_destDir(gearman_worker))

    if gearman_worker.collectionSystemTransfer['cruiseOrLowering'] == '1':
        if gearman_worker.loweringID == '':
            return [{"testName": "Destination Directory", "result": "Fail", "reason": "Lowering ID is undefined" }]

        destDir = os.path.join(cruiseDir, gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir'], gearman_worker.loweringID, build_destDir(gearman_worker))

    logging.debug('Destination Directory: {}'.format(destDir))

    return [{"testName": "Destination Directory", "result": "Pass"}] if os.path.isdir(destDir) else [{"testName": "Destination Directory", "result": "Fail", "reason": "Unable to find destination directory: {} on Data Warehouse".format(destDir)}]

    
class OVDMGearmanWorker(python3_gearman.GearmanWorker):

    def __init__(self):
        self.stop = False
        self.OVDM = OpenVDM_API()
        self.cruiseID = ''
        self.loweringID = ''
        self.collectionSystemTransfer = {}
        self.shipboardDataWarehouseConfig = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])
        
        
    def on_job_execute(self, current_job):
        logging.debug("current_job: {}".format(current_job))

        payloadObj = json.loads(current_job.data)

        try:
            self.collectionSystemTransfer = self.OVDM.getCollectionSystemTransfer(payloadObj['collectionSystemTransfer']['collectionSystemTransferID'])

            if not self.collectionSystemTransfer:
                return super(OVDMGearmanWorker, self).on_job_complete(current_job, json.dumps({'parts':[{"partName": "Located Collection System Tranfer Data", "result": "Fail", "reason": "Could not find configuration data for collection system transfer"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

        except:
            return super(OVDMGearmanWorker, self).on_job_complete(current_job, json.dumps({'parts':[{"partName": "Located Collection System Tranfer Data", "result": "Fail", "reason": "Could not find retrieve data for collection system transfer from OpenVDM API"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

        self.collectionSystemTransfer.update(payloadObj['collectionSystemTransfer'])
        self.cruiseID = payloadObj['cruiseID'] if 'cruiseID' in payloadObj else self.OVDM.getCruiseID()
        self.loweringID = payloadObj['loweringID'] if 'loweringID' in payloadObj else self.OVDM.getLoweringID()

        logging.info("Job: {}, {} transfer test started at: {}".format(current_job.handle, self.collectionSystemTransfer['name'], time.strftime("%D %T", time.gmtime())))

        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()
        
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)


    def on_job_exception(self, current_job, exc_info):
        logging.error("Job: {}, {} transfer test failed at: {}".format(current_job.handle, self.collectionSystemTransfer['name'], time.strftime("%D %T", time.gmtime())))
        
        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail", "reason": "Unknown"}]))
        self.OVDM.setError_collectionSystemTransferTest(self.collectionSystemTransfer['collectionSystemTransferID'], 'Worker crashed')

        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)

    
    def on_job_complete(self, current_job, job_results):
        resultsObj = json.loads(job_results)

        if len(resultsObj['parts']) > 0:
            if resultsObj['parts'][-1]['result'] == "Fail": # Final Verdict
                self.OVDM.setError_collectionSystemTransferTest(self.collectionSystemTransfer['collectionSystemTransferID'], resultsObj['parts'][-1]['reason'])
            else:
                self.OVDM.clearError_collectionSystemTransfer(self.collectionSystemTransfer['collectionSystemTransferID'], self.collectionSystemTransfer['status'])
        else:
            self.OVDM.clearError_collectionSystemTransfer(self.collectionSystemTransfer['collectionSystemTransferID'], self.collectionSystemTransfer['status'])

        logging.debug("Job Results: {}".format(json.dumps(resultsObj, indent=2)))
        logging.info("Job: {}, {} transfer test completed at: {}".format(current_job.handle, self.collectionSystemTransfer['name'], time.strftime("%D %T", time.gmtime())))
            
        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_results)

    
    def stopTask(self):
        self.stop = True
        logging.warning("Stopping current task...")

    
    def quitWorker(self):
        self.stop = True
        logging.warning("Quitting worker...")
        self.shutdown()

    
def task_testCollectionSystemTransfer(gearman_worker, current_job):

    job_results = {'parts':[]}

    gearman_worker.OVDM.setRunning_collectionSystemTransferTest(gearman_worker.collectionSystemTransfer['collectionSystemTransferID'], os.getpid(), current_job.handle)

    gearman_worker.send_job_status(current_job, 1, 4)
    
    logging.info("Testing Source Directory")
    if gearman_worker.collectionSystemTransfer['transferType'] == "1": # Local Directory
        job_results['parts'] = test_localSourceDir(gearman_worker)
    elif  gearman_worker.collectionSystemTransfer['transferType'] == "2": # Rsync Server
        job_results['parts'] += test_rsyncSourceDir(gearman_worker)
    elif  gearman_worker.collectionSystemTransfer['transferType'] == "3": # SMB Share
        job_results['parts'] += test_smbSourceDir(gearman_worker)
    elif  gearman_worker.collectionSystemTransfer['transferType'] == "4": # SSH Server
        job_results['parts'] += test_sshSourceDir(gearman_worker)

    gearman_worker.send_job_status(current_job, 2, 4)

    if gearman_worker.collectionSystemTransfer['enable'] == '1':
        logging.info("Testing Destination Directory")
        job_results['parts'] += test_destDir(gearman_worker)
        gearman_worker.send_job_status(current_job, 3, 4)
        
    verdict = True
    for test in job_results['parts']:
        if test['result'] == "Fail":
            verdict = False
            job_results['parts'].append({"testName": "Final Verdict", "result": "Fail", "reason": test['reason']})
            break

    if verdict:
        job_results['parts'].append({"testName": "Final Verdict", "result": "Pass"})

    gearman_worker.send_job_status(current_job, 4, 4)

    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle collection system transfer connection test related tasks')
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

    logging.info("\tTask: testCollectionSystemTransfer")
    new_worker.register_task("testCollectionSystemTransfer", task_testCollectionSystemTransfer)

    logging.info("Waiting for jobs...")
    new_worker.work()
