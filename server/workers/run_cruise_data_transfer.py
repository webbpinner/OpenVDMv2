# ----------------------------------------------------------------------------------- #
#
#         FILE:  run_cruise_data_transfer.py
#
#  DESCRIPTION:  Gearman worker that handles the transfer of all cruise data from the
#                Shipboard Data Warehouse to a second location.
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.5
#      CREATED:  2015-01-01
#     REVISION:  2021-01-04
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
import fnmatch
import subprocess
import signal
import logging
from random import randint

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.utils.output_JSONDataToFile import output_JSONDataToFile
from server.utils.set_ownerGroupPermissions import set_ownerGroupPermissions
from server.utils.create_directories import create_directories, create_parent_directories
from server.lib.openvdm import OpenVDM_API, DEFAULT_CRUISE_CONFIG_FN


def isascii(s):
    """Check if the characters in string s are in ASCII, U+0-U+7F."""
    return len(s) == len(s.encode())


def build_filelist(gearman_worker, sourceDir):

    returnFiles = {'include':[], 'exclude':[], 'new':[], 'updated':[], 'filesize':[]}

    logging.debug("returnFiles: {}".format(json.dumps(returnFiles, indent=2)))

    filters = build_filters(gearman_worker)

    for root, dirnames, filenames in os.walk(sourceDir):
        for filename in filenames:

            if os.path.islink(os.path.join(root, filename)):
                logging.debug("{} is a symlink, skipping".format(filename))
                continue

            exclude = False
            ignore = False
            include = False
            for filt in filters['ignoreFilter'].split(','):
                #logging.debug(filt)
                if fnmatch.fnmatch(os.path.join(root, filename), filt):
                    logging.debug("{} ignored by ignore filter".format(filename))
                    ignore = True
                    break
            if not ignore:
                for filt in filters['includeFilter'].split(','): 
                    if fnmatch.fnmatch(filename, filt):
                        for filt in filters['excludeFilter'].split(','): 
                            if fnmatch.fnmatch(filename, filt):
                                logging.debug("{} excluded by exclude filter".format(filename))
                                returnFiles['exclude'].append(os.path.join(root, filename))
                                exclude = True
                                break
                        if not exclude:
                            if not isascii(filename):
                                logging.debug("{} is not an ascii-encoded unicode string".format(filename))
                                returnFiles['exclude'].append(os.path.join(root, filename))
                                exclude = True
                            else:
                                logging.debug("{} is a valid file for transfer".format(os.path.join(root, filename)))
                                returnFiles['include'].append(os.path.join(root, filename))
                                include = True

                if include or exclude or ignore:
                    logging.debug("{} excluded because file does not match any of the filters".format(filename))
                    returnFiles['exclude'].append(os.path.join(root, filename))

    returnFiles['include'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['include']]
    returnFiles['exclude'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['exclude']]

    return returnFiles

# def build_destDirectories(destDir, files):
#     files = [filename.replace(os.path.join(destDir, filename)) for filename in files]
#     dirs = list(set([os.path.dirname(filename) for filename in files]))

#     logging.debug("Directories to create: {}".format(json.dumps(dirs)))
#     return create_directories(dirs)

def build_filters(gearman_worker):

    return = {
        'includeFilter': '*',
        'excludeFilter': ','.join(build_excludeList(gearman_worker)),
        'ignoreFilter': ''
    }


def build_excludeList(gearman_worker):
    
    excludedFilterArray = []

    if gearman_worker.cruiseDataTransfer['includeOVDMFiles'] == '0':
        dashboardDataDir = gearman_worker.OVDM.getRequiredExtraDirectoryByName("Dashboard_Data")
        excludedFilterArray.append("*/{}/{}/*".format(gearman_worker.cruiseID, dashboardDataDir['destDir']))

        transferLogs = gearman_worker.OVDM.getRequiredExtraDirectoryByName("Transfer_Logs")
        excludedFilterArray.append("*/{}/{}/*".format(gearman_worker.cruiseID, transferLogs['destDir']))

    if gearman_worker.cruiseDataTransfer['includePublicDataFiles'] == '0':
        fromPublicDataDir = gearman_worker.OVDM.getRequiredExtraDirectoryByName("From_PublicData")
        excludedFilterArray.append("*/{}/{}/*".format(gearman_worker.cruiseID, fromPublicDataDir['destDir']))

    excludedCollectionSystemIDs = gearman_worker.cruiseDataTransfer['excludedCollectionSystems'].split(',')
    for collectionSystemID in excludedCollectionSystemIDs:
        cruiseDataTransfer = gearman_worker.OVDM.getCollectionSystemTransfer(collectionSystemID)
        try:
            if cruiseDataTransfer['cruiseOrLowering'] == '0':
                excludedFilterArray.append("*/{}/{}/*".format(gearman_worker.cruiseID, cruiseDataTransfer['destDir']))
            else:
                lowerings = gearman_worker.OVDM.getLowerings()
                for lowering in lowerings:
                    # excludedFilterArray.append("*/{cruiseID}/*/" + lowering + "/" + cruiseDataTransfer['destDir'].replace('{loweringID}', lowering) + "/*")
                    excludedFilterArray.append("*/{}/*/{}/{}/*".format(gearman_worker.cruiseID, lowering, cruiseDataTransfer['destDir'].replace('{cruiseID}', gearman_worker.cruiseID).replace('{loweringID}', lowering)))
        except:
            logging.warning("Could not retrieve collection system transfer {}".format(collectionSystemID))
            pass

    excludedExtraDirectoryIDs = gearman_worker.cruiseDataTransfer['excludedExtraDirectories'].split(',')
    for excludedExtraDirectoryID in excludedExtraDirectoryIDs:
        extraDirectory = gearman_worker.OVDM.getExtraDirectory(excludedExtraDirectoryID)
        try:
            excludedFilterArray.append("*/{}/{}/*".format(gearman_worker.cruiseID, extraDirectory['destDir'].replace('{cruiseID}', gearman_worker.cruiseID)))
        except:
            logging.warning("Could not retrieve extra directory {}".format(collectionSystemID))
            pass

    logging.debug("Exclude filters: {}".format(json.dumps(excludedFilterArray, indent=2)))

    return excludedFilterArray

            
def transfer_localDestDir(gearman_worker, gearman_job):

    logging.debug("Transfer to Local Directory")
    
    warehouseUser = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)
    destDir = os.path.join(gearman_worker.cruiseDataTransfer['destDir'], gearman_worker.cruiseID)

    logging.debug('Destination Dir: {}'.format(destDir))

    output_results = create_directories([destDir])

    if not output_results['verdict']:
        return output_results

    logging.debug("Building file list")
    files = build_filelist(gearman_worker, cruiseDir)
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncExcludeListPath = os.path.join(tmpdir, 'rsyncExcludeList.txt')
        
    try:
        with open(rsyncExcludeListPath, 'w') as rsyncExcludeListFile:
            rsyncExcludeListFile.write('\n'.join(files['exclude']))

    except IOError:
        logging.error("Error Saving temporary rsync filelist file")
            
        # Cleanup
        shutil.rmtree(tmpdir)
        return False

    bandwidthLimit = '--bwlimit=' + gearman_worker.cruiseDataTransfer['bandwidthLimit'] if gearman_worker.cruiseDataTransfer['bandwidthLimit'] != '0' else '--bwlimit=20000000' # 20GB/s a.k.a. stupid big
    
    command = ['rsync', '-trim', bandwidthLimit, '--exclude-from=' + rsyncExcludeListPath, cruiseDir + '/', destDir]

    logging.debug('Transfer Command: {}'.format(' '.join(command)))
    
     proc = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)
    while True:

        line = proc.stdout.readline().rstrip('\n')

        if proc.poll() is not None:
            break

        if not line:
            continue
        
        logging.debug("Line: {}".format(line))
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1]
            files['new'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1]
            files['updated'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
            
        if gearman_worker.stop:
            logging.debug("Stopping")
            proc.terminate()
            break

    files['new'] = [os.path.join('/', gearman_worker.cruiseID, filename) for filename in files['new']]
    files['updated'] = [os.path.join('/', gearman_worker.cruiseID, filename) for filename in files['updated']]

    logging.info("Setting file permissions")
    output_results = set_ownerGroupPermissions(warehouseUser, destDir)

    # Cleanup
    shutil.rmtree(tmpdir)    

    if not output_results['verdict']:
        logging.error("Error setting ownership/permissions for transfer logfile: {}".format(logfileName))
        return output_results

    return { verdict: True, files: files }


def transfer_smbDestDir(gearman_worker, gearman_job):
    
    logging.debug("Transfer from SMB Source")

    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)
    
    logging.debug("Building file list")
    files = build_filelist(gearman_worker, cruiseDir)

    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    # Create mountpoint
    mntPoint = os.path.join(tmpdir, 'mntpoint')
    os.mkdir(mntPoint, 0o755)

    # Mount SMB Share
    logging.debug("Mounting SMB Share")

    ver_test_command = ['smbclient', '-L', gearman_worker.cruiseDataTransfer['smbServer'], '-W', gearman_worker.cruiseDataTransfer['smbDomain'], '-m', 'SMB2', '-g', '-N'] if gearman_worker.cruiseDataTransfer['smbUser'] == 'guest' else ['smbclient', '-L', gearman_worker.cruiseDataTransfer['smbServer'], '-W', gearman_worker.cruiseDataTransfer['smbDomain'], '-m', 'SMB2', '-g', '-U', gearman_worker.cruiseDataTransfer['smbUser'] + '%' + gearman_worker.cruiseDataTransfer['smbPass']]
    logging.debug("SMB version test command: {}".format(' '.join(ver_test_command)))

    vers="2.1"
    proc = subprocess.run(ver_test_command, capture_output=True, text=True)

    for line in proc.stdout.splitlines():
        if line.startswith('OS=[Windows 5.1]'):
            vers="1.0"
            break

    mount_command = ['sudo', 'mount', '-t', 'cifs', gearman_worker.cruiseDataTransfer['smbServer'], mntPoint, '-o', 'ro' + ',guest' + ',domain=' + gearman_worker.cruiseDataTransfer['smbDomain'] + ',vers=' + vers] if gearman_worker.cruiseDataTransfer['smbUser'] == 'guest' else ['sudo', 'mount', '-t', 'cifs', gearman_worker.cruiseDataTransfer['smbServer'], mntPoint, '-o', 'ro' + ',username=' + gearman_worker.cruiseDataTransfer['smbUser'] + ',password=' + gearman_worker.cruiseDataTransfer['smbPass'] + ',domain=' + gearman_worker.cruiseDataTransfer['smbDomain'] + ',vers=' + vers]
    logging.debug("Mount command: {}".format(' '.join(mount_command)))
    
    mount_proc = subprocess.run(mount_command, capture_output=True, text=True)

    destDir = os.path.join(mntPoint, gearman_worker.cruiseDataTransfer['destDir'], gearman_worker.cruiseID)
    output_results = create_directories([destDir])

    if not output_results['verdict']:
        return output_results
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncExcludeListPath = os.path.join(tmpdir, 'rsyncExcludeList.txt')
        
    try:
        with open(rsyncExcludeListPath, 'w') as rsyncExcludeListFile:
            rsyncExcludeListFile.write('\n'.join(files['exclude']))

    except IOError:
        logging.error("Error Saving temporary rsync filelist file")
            
        # Cleanup
        shutil.rmtree(tmpdir)
        return False

    bandwidthLimit = '--bwlimit=' + gearman_worker.cruiseDataTransfer['bandwidthLimit'] if gearman_worker.cruiseDataTransfer['bandwidthLimit'] != '0' else '--bwlimit=20000000' # 20GB/s a.k.a. stupid big
    
    command = ['rsync', '-trim', bandwidthLimit, '--exclude-from=' + rsyncExcludeListPath, cruiseDir + '/', destDir]

    logging.debug('Transfer Command: {}'.format(' '.join(command)))
    
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)
    while True:

        line = proc.stdout.readline().rstrip('\n')

        if proc.poll() is not None:
            break

        if not line:
            continue
        
        logging.debug("Line: {}".format(line))
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1]
            files['new'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1]
            files['updated'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
            
        if gearman_worker.stop:
            logging.debug("Stopping")
            proc.terminate()
            break

    files['new'] = [os.path.join('/', gearman_worker.cruiseID, filename) for filename in files['new']]
    files['updated'] = [os.path.join('/', gearman_worker.cruiseID, filename) for filename in files['updated']]

    #print "Cleanup"
    time.sleep(2)

    logging.debug("Unmount SMB Share")
    subprocess.call(['umount', mntPoint])
    shutil.rmtree(tmpdir)

    return { verdict: True, files: files }


def transfer_rsyncDestDir(gearman_worker, gearman_job):

    logging.debug("Transfer from RSYNC Server")

    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)
    
    logging.debug("Building file list")
    files = build_filelist(gearman_worker, cruiseDir)

    destDir = gearman_worker.cruiseDataTransfer['destDir'].rstrip('/')
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    fileIndex = 0
    fileCount = len(files['include'])
    
    rsyncPasswordFilePath = os.path.join(tmpdir, 'passwordFile')

    try:
        with open(rsyncPasswordFilePath, 'w') as rsyncPasswordFile:
            rsyncPasswordFile.write(gearman_worker.cruiseDataTransfer['rsyncPass'])

        os.chmod(rsyncPasswordFilePath, 0o600)

    except IOError:
        logging.error("Error Saving temporary rsync password file")
        rsyncPasswordFile.close()

        # Cleanup
        shutil.rmtree(tmpdir)

        return {'verdict': False, 'reason': 'Error Saving temporary rsync password file: ' + rsyncPasswordFilePath}
    
    rsyncExcludeListPath = os.path.join(tmpdir, 'rsyncExcludeList.txt')
        
    if not output_results['verdict']:
        return output_results
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncExcludeListPath = os.path.join(tmpdir, 'rsyncExcludeList.txt')
        
    try:
        with open(rsyncExcludeListPath, 'w') as rsyncExcludeListFile:
            rsyncExcludeListFile.write('\n'.join(files['exclude']))

    except IOError:
        logging.error("Error Saving temporary rsync filelist file")
            
        # Cleanup
        shutil.rmtree(tmpdir)
        return False
    
    bandwidthLimit = '--bwlimit=' + gearman_worker.cruiseDataTransfer['bandwidthLimit'] if gearman_worker.cruiseDataTransfer['bandwidthLimit'] != '0' else '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    # # Work around to create CruiseID at the destination
    # os.mkdir(os.path.join(tmpdir, gearman_worker.cruiseID))
    # command = ['rsync', '-a', bandwidthLimit, '--no-motd', '--password-file=' + rsyncPasswordFilePath, os.path.join(tmpdir, gearman_worker.cruiseID), 'rsync://' + gearman_worker.cruiseDataTransfer['rsyncUser'] + '@' + gearman_worker.cruiseDataTransfer['rsyncServer'] + destDir + '/']
    # popen = subprocess.Popen(command, stdout=subprocess.PIPE)

    command = ['rsync', '-trim', bandwidthLimit, '--no-motd', '--exclude-from=' + rsyncExcludeListPath, '--password-file=' + rsyncPasswordFilePath, cruiseDir, 'rsync://' + gearman_worker.cruiseDataTransfer['rsyncUser'] + '@' + gearman_worker.cruiseDataTransfer['rsyncServer'] + destDir + '/']
    
    logging.debug('Transfer Command: {}'.format(' '.join(command)))

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)

    while True:

        line = proc.stdout.readline().rstrip('\n')

        if proc.poll() is not None:
            break

        if not line:
            continue
        
        logging.debug('Line: {}'.format(line))
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1]
            files['new'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
        elif line.startswith( '>f.' ):
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


def transfer_sshDestDir(gearman_worker, gearman_job):

    logging.debug("Transfer from SSH Server")

    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)
    
    logging.debug("Building file list")
    files = build_filelist(gearman_worker, cruiseDir)

    destDir = gearman_worker.cruiseDataTransfer['destDir'].rstrip('/')
            
    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    sshExcludeListPath = os.path.join(tmpdir, 'sshExcludeList.txt')
    
    fileIndex = 0
    fileCount = len(files['include'])

    try:
        with open(sshExcludeListPath, 'w') as sshExcludeFileListFile:
            sshExcludeFileListFile.write('\n'.join(files['exclude']))

    except IOError:
        logging.debug("Error Saving temporary ssh exclude filelist file")
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return {'verdict': False, 'reason': 'Error Saving temporary ssh exclude filelist file: ' + sshExcludeListPath, 'files':[]}

    bandwidthLimit = '--bwlimit=' + gearman_worker.cruiseDataTransfer['bandwidthLimit'] if gearman_worker.cruiseDataTransfer['bandwidthLimit'] != '0' else '--bwlimit=20000000' # 20GB/s a.k.a. stupid big
    
    # command = ['ssh', gearman_worker.cruiseDataTransfer['sshServer'], '-l', gearman_worker.cruiseDataTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', 'PasswordAuthentication=no', 'mkdir ' + os.path.join(destDir, gearman_worker.cruiseID)] if gearman_worker.cruiseDataTransfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.cruiseDataTransfer['sshPass'], 'ssh', gearman_worker.cruiseDataTransfer['sshServer'], '-l', gearman_worker.cruiseDataTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PubkeyAuthentication=no', 'mkdir ' + os.path.join(destDir, gearman_worker.cruiseID)]

    # proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    # proc.communicate()

    command = ['rsync', '-trim', bandwidthLimit, '--exclude-from=' + sshExcludeListPath, '-e', 'ssh', cruiseDir, gearman_worker.cruiseDataTransfer['sshUser'] + '@' + gearman_worker.cruiseDataTransfer['sshServer'] + ':' + destDir] if gearman_worker.cruiseDataTransfer['sshUseKey'] == '1' else command = ['sshpass', '-p', gearman_worker.cruiseDataTransfer['sshPass'], 'rsync', '-trim', bandwidthLimit, '--exclude-from=' + sshExcludeListPath, '-e', 'ssh', cruiseDir, gearman_worker.cruiseDataTransfer['sshUser'] + '@' + gearman_worker.cruiseDataTransfer['sshServer'] + ':' + destDir]
    
    logging.debug("Transfer Command: {}".format(' '.join(command)))
    
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)
    
    while True:

        line = proc.stdout.readline().rstrip('\n')

        if proc.poll() is not None:
            break

        if not line:
            continue
        
        logging.debug("Line: {}".format(line))
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1]
            files['new'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
        elif line.startswith( '>f.' ):
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
    
        
class OVDMGearmanWorker(gearman.GearmanWorker):

    def __init__(self):
        self.stop = False
        self.OVDM = OpenVDM_API()
        self.cruiseID = ''
        self.systemStatus = ''
        self.cruiseDataTransfer = {}
        self.shipboardDataWarehouseConfig = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])
        
        
    def on_job_execute(self, current_job):
        logging.debug("current_job: {}".format(current_job))

        payloadObj = json.loads(current_job.data)

        try:
            self.cruiseDataTransfer = self.OVDM.getCollectionSystemTransfer(payloadObj['cruiseDataTransfer']['cruiseDataTransferID'])

            if not self.cruiseDataTransfer:
                return super(OVDMGearmanWorker, self).on_job_complete(current_job, json.dumps({'parts':[{"partName": "Located Cruise Data Tranfer Data", "result": "Fail", "reason": "Could not find configuration data for cruise data transfer"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))
            elif self.cruiseDataTransfer['status'] == "1": #not running
                logging.info("Transfer job for {} skipped because a transfer for that cruise data destination is already in-progress".format(self.cruiseDataTransfer['name']))
                return super(OVDMGearmanWorker, self).on_job_complete(current_job, json.dumps({'parts':[{"partName": "Transfer In-Progress", "result": "Fail", "reason": "Transfer is already in-progress"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

        except:
            return super(OVDMGearmanWorker, self).on_job_complete(current_job, json.dumps({'parts':[{"partName": "Located Cruise Data Tranfer Data", "result": "Fail", "reason": "Could not find retrieve data for cruise data transfer from OpenVDM API"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))


        self.systemStatus = payloadObj['systemStatus'] if 'systemStatus' in payloadObj else self.OVDM.getSystemStatus()

        if self.systemStatus == "Off":
            logging.info("Transfer job for {} skipped because that cruise data transfer is currently disabled".format(self.cruiseDataTransfer['name']))
            return super(OVDMGearmanWorker, self).on_job_complete(current_job, json.dumps({'parts':[{"partName": "Transfer Enabled", "result": "Fail", "reason": "Transfer is disabled"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

        self.cruiseDataTransfer.update(payloadObj['cruiseDataTransfer'])
        self.cruiseID = self.OVDM.getCruiseID()
        
        logging.info("Job: {}, {} transfer started at: {}".format(current_job.handle, self.cruiseDataTransfer['name'], time.strftime("%D %T", time.gmtime())))

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
        
        
def task_runCruiseDataTransfer(gearman_worker, current_job):

    time.sleep(randint(0,2))
    
    job_results = {
        'parts': [
            {"partName": "Transfer In-Progress", "result": "Pass"},
            {"partName": "Transfer Enabled", "result": "Pass"}
        ],
        'files':[]
    }

    #debugPrint("Set transfer status to 'Running'")
    worker.OVDM.setRunning_cruiseDataTransfer(worker.cruiseDataTransfer['cruiseDataTransferID'], os.getpid(), job.handle)
   
    debugPrint("Testing configuration")
    worker.send_job_status(job, 1, 10)

    gm_client = gearman.GearmanClient([worker.OVDM.getGearmanServer()])
    
    gmData = {
        'cruiseDataTransfer': worker.cruiseDataTransfer,
        'cruiseID': worker.cruiseID
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

    worker.send_job_status(current_job, 2, 10)
    
    logging.info("Transferring files")
    output_results = None
    if gearman_worker.cruiseDataTransfer['transferType'] == "1": # Local Directory
        output_results = transfer_localDestDir(gearman_worker, current_job)
    elif  gearman_worker.cruiseDataTransfer['transferType'] == "2": # Rsync Server
        output_results = transfer_rsyncDestDir(gearman_worker, current_job)
    elif  gearman_worker.cruiseDataTransfer['transferType'] == "3": # SMB Server
        output_results = transfer_smbDestDir(gearman_worker, current_job)
    elif  gearman_worker.cruiseDataTransfer['transferType'] == "4": # SSH Server
        output_results = transfer_sshDestDir(gearman_worker, current_job)
    
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

    worker.send_job_status(job, 9, 10)

    time.sleep(2)

    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle cruise data transfer related tasks')
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

    logging.info("\tTask: runCruiseDataTransfer")
    new_worker.register_task("runCruiseDataTransfer", task_runCruiseDataTransfer)

    logging.info("Waiting for jobs...")
    new_worker.work()

