# ----------------------------------------------------------------------------------- #
#
#         FILE:  test_cruise_data_transfer.py
#
#  DESCRIPTION:  Gearman worker that handles testing cruise data transfer
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

def writeTest(destDir):
    if os.path.isdir(destDir):
        try:
            filepath = os.path.join(destDir, 'writeTest.txt')
            with open(filepath, 'w') as filehandle:
                filehandle.write("this file tests if the parent directory can be written to.  You can delete this file if desired")

            os.remove(filepath)
        except Exception as e:
            logging.warning("Unable to write to {}".format(destDir))
            logging.warning(str(e))
            return False
        return True
    return False


def test_localDestDir(gearman_worker):
    returnVal = []

    destDir = gearman_worker.cruiseDataTransfer['destDir']

    if not os.path.isdir(destDir):
        returnVal.append({"testName": "Destination Directory", "result": "Fail", "reason": "Unable to locate destination directory: {}".format(destDir)})
        if gearman_worker.cruiseDataTransfer['localDirIsMountPoint'] == '1':
            returnVal.append({"testName": "Destination Directory is a Mountpoint", "result": "Fail", "reason": "Unable to locate destination directory: {}".format(destDir)})
        returnVal.append({"testName": "Write Test", "result": "Fail", "reason": "Unable to locate destination directory: {}".format(destDir)})

        return returnVal

    returnVal.append({"testName": "Destination Directory", "result": "Pass"})

    if gearman_worker.cruiseDataTransfer['localDirIsMountPoint'] == '1':
        if not os.path.ismount(destDir):
            returnVal.extend([
                {"testName": "Destination Directory is a Mountpoint", "result": "Fail", "reason": "Destination directory: {} is not a mountpoint".format(destDir)},
                {"testName": "Write Test", "result": "Fail", "reason": "Destination directory: {} is not a mountpoint".format(destDir)}
            ])

            return returnVal

        returnVal.append({"testName": "Destination Directory is a Mountpoint", "result": "Pass"})

    if not writeTest(destDir):
        returnVal.append({"testName": "Write Test", "result": "Fail", "reason": "Unable to write data to desination directory: " + destDir})
        return returnVal
    
    returnVal.append({"testName": "Write Test", "result": "Pass"})

    return returnVal

    
def test_smbDestDir(gearman_worker):
    returnVal = []

    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    # Verify the server exists
    server_test_command = ['smbclient', '-L', gearman_worker.cruiseDataTransfer['smbServer'], '-W', gearman_worker.cruiseDataTransfer['smbDomain'], '-m', 'SMB2', '-g', '-N'] if gearman_worker.cruiseDataTransfer['smbUser'] == 'guest' else ['smbclient', '-L', gearman_worker.cruiseDataTransfer['smbServer'], '-W', gearman_worker.cruiseDataTransfer['smbDomain'], '-m', 'SMB2', '-g', '-U', gearman_worker.cruiseDataTransfer['smbUser'] + '%' + gearman_worker.cruiseDataTransfer['smbPass']]
    logging.debug("Server test command: {}".format(' '.join(server_test_command)))
    
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
        returnVal.extend([
            {"testName": "SMB Server", "result": "Fail", "reason": "Could not connect to SMB Server: {} as {}".format(gearman_worker.cruiseDataTransfer['smbServer'], gearman_worker.cruiseDataTransfer['smbUser'])},
            {"testName": "SMB Share", "result": "Fail", "reason": "Could not connect to SMB Server: {} as {}".format(gearman_worker.cruiseDataTransfer['smbServer'], gearman_worker.cruiseDataTransfer['smbUser'])},
            {"testName": "Destination Directory", "result": "Fail", "reason": "Could not connect to SMB Server: {} as {}".format(gearman_worker.cruiseDataTransfer['smbServer'], gearman_worker.cruiseDataTransfer['smbUser'])},
            {"testName": "Write Test", "result": "Fail", "reason": "Could not connect to SMB Server: {} as {}".format(gearman_worker.cruiseDataTransfer['smbServer'], gearman_worker.cruiseDataTransfer['smbUser'])},
        ])

        return returnVal
 
    returnVal.append({"testName": "SMB Server", "result": "Pass"})

    # Create mountpoint
    mntPoint = os.path.join(tmpdir, 'mntpoint')
    os.mkdir(mntPoint, 0o755)

    # Mount SMB Share
    mount_command = ['mount', '-t', 'cifs', gearman_worker.cruiseDataTransfer['smbServer'], mntPoint, '-o', 'rw'+',guest'+',domain='+gearman_worker.cruiseDataTransfer['smbDomain']+',vers='+vers] if gearman_worker.cruiseDataTransfer['smbUser'] == 'guest' else ['mount', '-t', 'cifs', gearman_worker.cruiseDataTransfer['smbServer'], mntPoint, '-o', 'rw'+',username='+gearman_worker.cruiseDataTransfer['smbUser']+',password='+gearman_worker.cruiseDataTransfer['smbPass']+',domain='+gearman_worker.cruiseDataTransfer['smbDomain']+',vers='+vers]

    logging.debug('Mount command: {}'.format(' '.join(mount_command)))

    proc = subprocess.run(mount_command, capture_output=True)

    if proc.returncode != 0:
        returnVal.extend([
            {"testName": "SMB Share", "result": "Fail", "reason": "Could not connect to SMB Share: {} as {}".format(gearman_worker.cruiseDataTransfer['smbServer'], gearman_worker.cruiseDataTransfer['smbUser'])},
            {"testName": "Destination Directory", "result": "Fail", "reason": "Could not connect to SMB Share: {} as {}".format(gearman_worker.cruiseDataTransfer['smbServer'], gearman_worker.cruiseDataTransfer['smbUser'])},
            {"testName": "Write Test", "result": "Fail", "reason": "Could not connect to SMB Share: {} as {}".format(gearman_worker.cruiseDataTransfer['smbServer'], gearman_worker.cruiseDataTransfer['smbUser'])}
        ])

        # Cleanup
        shutil.rmtree(tmpdir)

        return returnVal

    returnVal.append({"testName": "SMB Share", "result": "Pass"})

    destDir = os.path.join(mntPoint, gearman_worker.cruiseDataTransfer['destDir'])
    if not os.path.isdir(destDir):
        returnVal.append({"testName": "Destination Directory", "result": "Fail", "reason": "Unable to find destination directory: {} within the SMB Share: {}".format(gearman_worker.cruiseDataTransfer['destDir'], gearman_worker.cruiseDataTransfer['smbServer'])})
        returnVal.append({"testName": "Write Test", "result": "Fail", "reason": "Unable to find destination directory: {} within the SMB Share: {}".format(gearman_worker.cruiseDataTransfer['destDir'], gearman_worker.cruiseDataTransfer['smbServer'])})

    else:
        returnVal.append({"testName": "Destination Directory", "result": "Pass"})

        if not writeTest(destDir):
            returnVal.append({"testName": "Write Test", "result": "Fail", "reason": "Unable to write to destination directory: {} within the SMB Share: {}".format(destDir, gearman_worker.cruiseDataTransfer['smbServer'])})
        else:
            returnVal.append({"testName": "Write Test", "result": "Pass"})
            

    # Unmount SMB Share
    if os.path.ismount(mntPoint):
        subprocess.call(['sudo', 'umount', mntPoint])

    # Cleanup
    shutil.rmtree(tmpdir)

    return returnVal


def test_rsyncDestDir(gearman_worker):
    
    returnVal = []

    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    rsyncPasswordFilePath = os.path.join(tmpdir,'passwordFile')

    try:
        with open(rsyncPasswordFilePath, 'w') as rsyncPasswordFile:

            if gearman_worker.cruiseDataTransfer['rsyncUser'] != 'anonymous':
                rsyncPasswordFile.write(gearman_worker.cruiseDataTransfer['rsyncPass'])
            else:
                rsyncPasswordFile.write('')                

    except IOError:
        logging.error("Error Saving temporary rsync password file {}".format(rsyncPasswordFilePath))
        returnVal.append({"testName": "Writing temporary rsync password file", "result": "Fail", "reason": "Unable to create temporary rsync password file: {}".format(rsyncPasswordFilePath)})

        # Cleanup
        shutil.rmtree(tmpdir)

        return returnVal    

    os.chmod(rsyncPasswordFilePath, 0o600)
    
    server_test_command = ['rsync', '--no-motd', '--password-file=' + rsyncPasswordFilePath, 'rsync://' + gearman_worker.cruiseDataTransfer['rsyncUser'] + '@' + gearman_worker.cruiseDataTransfer['rsyncServer']]
    
    logging.debug('Server test command: {}'.format(' '.join(server_test_command)))
    
    proc = subprocess.run(server_test_command, capture_output=True)

    if proc.returncode != 0:
        returnVal.extend([
            {"testName": "Rsync Connection", "result": "Fail", "reason": "Unable to connect to rsync server: {} as {}".format(gearman_worker.cruiseDataTransfer['rsyncServer'], gearman_worker.cruiseDataTransfer['rsyncUser'])},
            {"testName": "Destination Directory", "result": "Fail", "reason": "Unable to connect to rsync server: {} as {}".format(gearman_worker.cruiseDataTransfer['rsyncServer'], gearman_worker.cruiseDataTransfer['rsyncUser'])},
            {"testName": "Write Test", "result": "Fail", "reason": "Unable to connect to rsync server: {} as {}".format(gearman_worker.cruiseDataTransfer['rsyncServer'], gearman_worker.cruiseDataTransfer['rsyncUser'])}
        ])

        # Cleanup
        shutil.rmtree(tmpdir)

        return returnVal    

    returnVal.append({"testName": "Rsync Connection", "result": "Pass"})

    destDir = gearman_worker.cruiseDataTransfer['destDir']

    dest_test_command = ['rsync', '--no-motd', '--password-file=' + rsyncPasswordFilePath, 'rsync://' + gearman_worker.cruiseDataTransfer['rsyncUser'] + '@' + gearman_worker.cruiseDataTransfer['rsyncServer'] + destDir]
    
    logging.debug('Destination test command: {}'.format(' '.join(dest_test_command)))

    proc = subprocess.run(dest_test_command, capture_output=True)

    if proc.returncode != 0:
        returnVal.extend([
            {"testName": "Destination Directory", "result": "Fail", "reason": "Unable to find destination directory: {} on the Rsync Server: {}".format(destDir, gearman_worker.cruiseDataTransfer['rsyncServer'])},
            {"testName": "Write Test", "result": "Fail", "reason": "Unable to find destination directory: {} on the Rsync Server: {}".format(destDir, gearman_worker.cruiseDataTransfer['rsyncServer'])}
        ])

        # Cleanup
        shutil.rmtree(tmpdir)

        return returnVal    

    returnVal.append({"testName": "Destination Directory", "result": "Pass"})

    writeTestFile = os.path.join(tmpdir, 'writeTest.txt')
    with open(writeTestFile, 'a') as writeTestFileHandle:
        writeTestFileHandle.write("This file proves this directory can be written to by OpenVDM")

    write_test_command = ['rsync', '-vi', '--no-motd', '--password-file=' + rsyncPasswordFilePath, writeTestFile, 'rsync://' + gearman_worker.cruiseDataTransfer['rsyncUser'] + '@' + gearman_worker.cruiseDataTransfer['rsyncServer'] + destDir]

    logging.debug('Server Test Command: {}'.format(' '.join(write_test_command)))

    proc = subprocess.run(write_test_command, capture_output=True)

    if proc.returncode != 0:
        returnVal.append({"testName": "Write Test", "result": "Fail", "reason": "Unable to write to destination directory: {} on the Rsync Server: {}".format(destDir, gearman_worker.cruiseDataTransfer['rsyncServer'])})
        
    else:

        os.remove(writeTestFile)
        write_cleanup_command = ['rsync', '-vir', '--no-motd', '--password-file=' + rsyncPasswordFilePath, '--delete', '--include=writeTest.txt', '--exclude=*', tmpdir + '/', 'rsync://' + gearman_worker.cruiseDataTransfer['rsyncUser'] + '@' + gearman_worker.cruiseDataTransfer['rsyncServer'] + destDir]
    
        logging.debug('Write test cleanup command: {}'.format(' '.join(write_cleanup_command)))

        proc = subprocess.run(write_cleanup_command, capture_output=True, text=True)

        logging.debug(proc.stderr)
        
        if proc.returncode != 0:
            returnVal.append({"testName": "Write Test", "result": "Fail", "reason": "Unable to write to destination directory: {} on the Rsync Server: {}".format(destDir, gearman_worker.cruiseDataTransfer['rsyncServer'])})

        else:
            returnVal.append({"testName": "Write Test", "result": "Pass"})

    # Cleanup
    shutil.rmtree(tmpdir)
        
    return returnVal


def test_sshDestDir(gearman_worker):
    
    returnVal = []

    server_test_command = ['ssh', gearman_worker.cruiseDataTransfer['sshServer'], '-l', gearman_worker.cruiseDataTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', 'PasswordAuthentication=no', 'ls'] if gearman_worker.cruiseDataTransfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.cruiseDataTransfer['sshPass'], 'ssh', gearman_worker.cruiseDataTransfer['sshServer'], '-l', gearman_worker.cruiseDataTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PubkeyAuthentication=no', 'ls']
    
    logging.debug('Connection test command: {}'.format(' '.join(server_test_command)))
    
    proc = subprocess.run(server_test_command, capture_output=True)

    if proc.returncode != 0:
        returnVal.extend([
            {"testName": "SSH Connection", "result": "Fail", "reason": "Unable to connect to ssh server: {} as {}".format(gearman_worker.cruiseDataTransfer['sshServer'], gearman_worker.cruiseDataTransfer['sshUser'])},
            {"testName": "Destination Directory", "result": "Fail", "reason": "Unable to connect to ssh server: {} as {}".format(gearman_worker.cruiseDataTransfer['sshServer'], gearman_worker.cruiseDataTransfer['sshUser'])},
            {"testName": "Write Test", "result": "Fail", "reason": "Unable to connect to ssh server: {} as {}".format(gearman_worker.cruiseDataTransfer['sshServer'], gearman_worker.cruiseDataTransfer['sshUser'])}
        ])
        return returnVal

    returnVal.append({"testName": "SSH Connection", "result": "Pass"})

    destDir = gearman_worker.cruiseDataTransfer['destDir']

    dest_test_command = ['ssh', gearman_worker.cruiseDataTransfer['sshServer'], '-l', gearman_worker.cruiseDataTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', 'PasswordAuthentication=no', 'ls', destDir] if gearman_worker.cruiseDataTransfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.cruiseDataTransfer['sshPass'], 'ssh', gearman_worker.cruiseDataTransfer['sshServer'], '-l', gearman_worker.cruiseDataTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PubkeyAuthentication=no', 'ls', destDir]
    
    logging.debug("Destination test command: {}".format(dest_test_command))

    proc = subprocess.run(dest_test_command, capture_output=True)

    if proc.returncode != 0:
        returnVal.extend([
            {"testName": "Destination Directory", "result": "Fail", "reason": "Unable to find destination directory: {} on the SSH Server: {}".format(destDir,gearman_worker.cruiseDataTransfer['sshServer'])},
            {"testName": "Write Test", "result": "Fail", "reason": "Unable to find destination directory: {} on the SSH Server: {}".format(destDir,gearman_worker.cruiseDataTransfer['sshServer'])}
        ])

        return returnVal

    returnVal.append({"testName": "Destination Directory", "result": "Pass"})

    write_test_command = ['ssh', gearman_worker.cruiseDataTransfer['sshServer'], '-l', gearman_worker.cruiseDataTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', 'PasswordAuthentication=no', 'touch ' + os.path.join(destDir, 'writeTest.txt')] if gearman_worker.cruiseDataTransfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.cruiseDataTransfer['sshPass'], 'ssh', gearman_worker.cruiseDataTransfer['sshServer'], '-l', gearman_worker.cruiseDataTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PubkeyAuthentication=no', 'touch ' + os.path.join(destDir, 'writeTest.txt')]
        
    logging.debug('Write test command: {}'.format(write_test_command))

    proc = subprocess.run(write_test_command, capture_output=True)

    if proc.returncode != 0:
        returnVal.append({"testName": "Write Test", "result": "Fail", "reason": "Unable to write to destination directory: {} on the SSH Server: {}".format(destDir, gearman_worker.cruiseDataTransfer['sshServer'])})

        return returnVal
        
    write_cleanup_command = ['ssh', gearman_worker.cruiseDataTransfer['sshServer'], '-l', gearman_worker.cruiseDataTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', 'PasswordAuthentication=no', 'rm ' + os.path.join(destDir, 'writeTest.txt')] if gearman_worker.cruiseDataTransfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.cruiseDataTransfer['sshPass'], 'ssh', gearman_worker.cruiseDataTransfer['sshServer'], '-l', gearman_worker.cruiseDataTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PubkeyAuthentication=no', 'rm ' + os.path.join(destDir, 'writeTest.txt')]

    logging.debug("Write test cleanup command: {}".format(' '.join(write_cleanup_command)))

    proc = subprocess.run(write_cleanup_command, capture_output=True)

    if proc.returncode != 0:
        returnVal.append({"testName": "Write Test", "result": "Fail", "reason": "Unable to cleanup test file from destination directory: {} on the SSH Server: {}".format(destDir, gearman_worker.cruiseDataTransfer['sshServer'])})

        return returnVal

    returnVal.append({"testName": "Write Test", "result": "Pass"})

    return returnVal


def test_sourceDir(gearman_worker):

    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)
    
    return [{"testName": "Source Directory", "result": "Pass"}] if os.path.isdir(cruiseDir) else [{"testName": "Source Directory", "result": "Fail", "reason": "Unable to find cruise directory: {} on the Data Warehouse".format(cruiseDir)}]

    
class OVDMGearmanWorker(python3_gearman.GearmanWorker):

    def __init__(self):
        self.stop = False
        self.OVDM = OpenVDM_API()
        self.cruiseID = ''
        self.cruiseDataTransfer = {}
        self.shipboardDataWarehouseConfig = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])
        
        
    def on_job_execute(self, current_job):
        logging.debug("current_job: {}".format(current_job))

        payloadObj = json.loads(current_job.data)

        if 'cruiseDataTransferID' in payloadObj['cruiseDataTransfer']:
            self.cruiseDataTransfer = self.OVDM.getCruiseDataTransfer(payloadObj['cruiseDataTransfer']['cruiseDataTransferID'])

            if not self.cruiseDataTransfer:
                logging.error("could not find configuration data")
                return super(OVDMGearmanWorker, self).on_job_complete(current_job, json.dumps({'parts':[{"partName": "Located Cruise Data Tranfer Data", "result": "Fail", "reason": "Could not find configuration data for cruise data transfer"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))
        
            self.cruiseDataTransfer.update(payloadObj['cruiseDataTransfer'])

        else:
            self.cruiseDataTransfer = payloadObj['cruiseDataTransfer']

        self.cruiseID = self.OVDM.getCruiseID()

        logging.info("Job: {}, {} transfer test started at: {}".format(current_job.handle, self.cruiseDataTransfer['name'], time.strftime("%D %T", time.gmtime())))

        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()
        
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)


    def on_job_exception(self, current_job, exc_info):
        logging.error("Job: {}, {} transfer test failed at: {}".format(current_job.handle, self.cruiseDataTransfer['name'], time.strftime("%D %T", time.gmtime())))
        
        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail", "reason": "Unknown"}]))
        
        if 'cruiseDataTransferID' in self.cruiseDataTransfer:
            self.OVDM.setError_cruiseDataTransferTest(self.cruiseDataTransfer['cruiseDataTransferID'], 'Worker crashed')

        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)


    
    def on_job_complete(self, current_job, job_results):
        resultsObj = json.loads(job_results)

        if 'cruiseDataTransferID' in self.cruiseDataTransfer:
            if len(resultsObj['parts']) > 0:
                if resultsObj['parts'][-1]['result'] == "Fail": # Final Verdict
                    self.OVDM.setError_cruiseDataTransferTest(self.cruiseDataTransfer['cruiseDataTransferID'], resultsObj['parts'][-1]['reason'])
                else:
                    self.OVDM.clearError_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'], self.cruiseDataTransfer['status'])
            else:
                self.OVDM.clearError_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'], self.cruiseDataTransfer['status'])

        logging.debug("Job Results: {}".format(json.dumps(resultsObj, indent=2)))
        logging.info("Job: {}, {} transfer test completed at: {}".format(current_job.handle, self.cruiseDataTransfer['name'], time.strftime("%D %T", time.gmtime())))
            
        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_results)

    
    def stopTask(self):
        self.stop = True
        logging.warning("Stopping current task...")

    
    def quitWorker(self):
        self.stop = True
        logging.warning("Quitting worker...")
        self.shutdown()

    
def task_testCruiseDataTransfer(gearman_worker, current_job):

    job_results = {'parts':[]}

    if 'cruiseDataTransferID' in gearman_worker.cruiseDataTransfer:
        gearman_worker.OVDM.setRunning_cruiseDataTransferTest(gearman_worker.cruiseDataTransfer['cruiseDataTransferID'], os.getpid(), current_job.handle)

    gearman_worker.send_job_status(current_job, 1, 4)
    
    logging.info("Test Source Directory")
    job_results['parts'] = test_sourceDir(gearman_worker)

    gearman_worker.send_job_status(current_job, 2, 4)

    logging.info("Test Destination Directory")
    if gearman_worker.cruiseDataTransfer['transferType'] == "1": # Local Directory
        job_results['parts'] += test_localDestDir(gearman_worker)
    elif  gearman_worker.cruiseDataTransfer['transferType'] == "2": # Rsync Server
        job_results['parts'] += test_rsyncDestDir(gearman_worker)
    elif  gearman_worker.cruiseDataTransfer['transferType'] == "3": # SMB Share
        job_results['parts'] += test_smbDestDir(gearman_worker)
    elif  gearman_worker.cruiseDataTransfer['transferType'] == "4": # SSH Server
        job_results['parts'] += test_sshDestDir(gearman_worker)

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
    parser = argparse.ArgumentParser(description='Handle cruise data transfer connection test related tasks')
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

    logging.info("\tTask: testCruiseDataTransfer")
    new_worker.register_task("testCruiseDataTransfer", task_testCruiseDataTransfer)

    logging.info("Waiting for jobs...")
    new_worker.work()
