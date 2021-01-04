# ----------------------------------------------------------------------------------- #
#
#         FILE:  run_collection_system_transfer.py
#
#  DESCRIPTION:  Gearman worker that handles the transfer of data from the Collection
#                System to the Shipboard Data Warehouse.
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.5
#      CREATED:  2015-01-01
#     REVISION:  2021-01-02
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
import io
import os
import sys
import tempfile
import python3_gearman
import shutil
import json
import time
import calendar
import datetime
import fnmatch
import subprocess
import signal
import logging
from random import randint

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.utils.output_JSONDataToFile import output_JSONDataToFile
from server.utils.set_ownerGroupPermissions import set_ownerGroupPermissions
from server.lib.openvdm import OpenVDM_API, DEFAULT_CRUISE_CONFIG_FN


def isascii(s):
    """Check if the characters in string s are in ASCII, U+0-U+7F."""
    return len(s) == len(s.encode())

def build_filelist(gearman_worker, sourceDir):

    returnFiles = {'include':[], 'exclude':[], 'new':[], 'updated':[], 'filesize':[]}

    logging.debug("returnFiles: {}".format(json.dumps(returnFiles, indent=2)))

    staleness = int(gearman_worker.collectionSystemTransfer['staleness']) * 60 #5 Mintues
    logging.debug("Staleness: {}".format(staleness))

    threshold_time = time.time() - staleness
    logging.debug("Threshold: {}".format(threshold_time))

    dataStart_time = calendar.timegm(time.strptime(gearman_worker.dataStartDate, "%Y/%m/%d %H:%M"))
    logging.debug("Start: {}".format(dataStart_time))

    logging.debug("gearman_worker.dataEndDate: {}".format(gearman_worker.dataEndDate))
    dataEnd_time = calendar.timegm(time.strptime(gearman_worker.dataEndDate, "%Y/%m/%d %H:%M"))
    logging.debug("End: {}".format(dataEnd_time))

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
                    logging.debug("{} ignored".format(filename))
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
                            logging.debug('Filename: {}'.format(os.path.join(root, filename)))
                            file_mod_time = os.stat(os.path.join(root, filename)).st_mtime
                            logging.debug("file_mod_time: {}".format(file_mod_time))
                            if not isascii(filename):
                                logging.debug("{} is not an ascii-encoded unicode string".format(filename))
                                returnFiles['exclude'].append(os.path.join(root, filename))
                            else:
                                if file_mod_time > dataStart_time and file_mod_time < dataEnd_time:
                                    logging.debug("{} included".format(filename))
                                    returnFiles['include'].append(os.path.join(root, filename))
                                    returnFiles['filesize'].append(os.stat(os.path.join(root, filename)).st_size)
                                else:
                                    logging.debug("{} ignored for time reasons".format(filename))

                                include = True

                if not include and not exclude:
                    logging.debug("{} excluded because file does not match any include or ignore filters".format(filename))
                    returnFiles['exclude'].append(os.path.join(root, filename))

    if not gearman_worker.collectionSystemTransfer['staleness'] == '0':
        logging.debug("Checking for changing filesizes")
        time.sleep(5)
        for idx, val in enumerate(returnFiles['include']):
            logging.debug("idx: {}, val: {}, filesize: {}".format(idx, val, returnFiles['filesize'][idx]))
            if not os.stat(val).st_size == returnFiles['filesize'][idx]:
                logging.debug("{} removed because it's size is changing".format(val))
                del returnFiles['include'][idx]
                del returnFiles['filesize'][idx]

    del returnFiles['filesize']

    returnFiles['include'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['include']]
    returnFiles['exclude'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['exclude']]

    return returnFiles


def build_rsyncFilelist(gearman_worker, sourceDir):

    returnFiles = {'include':[], 'exclude':[], 'new':[], 'updated':[]}

    staleness = int(gearman_worker.collectionSystemTransfer['staleness']) * 60
    threshold_time = time.time() - staleness # 5 minutes
    epoch = datetime.datetime.strptime('1970/01/01 00:00:00', "%Y/%m/%d %H:%M:%S") 
    dataStart_time = calendar.timegm(time.strptime(gearman_worker.dataStartDate, "%Y/%m/%d %H:%M"))
    dataEnd_time = calendar.timegm(time.strptime(gearman_worker.dataEndDate, "%Y/%m/%d %H:%M"))

    logging.debug("Threshold: {}".format(threshold_time))
    logging.debug("    Start: {}".format(dataStart_time))
    logging.debug("      End: {}".format(dataEnd_time))

    filters = build_filters(gearman_worker)

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncPasswordFilePath = os.path.join(tmpdir, 'passwordFile')

    try:
        with open(rsyncPasswordFilePath, 'w') as rsyncPasswordFile:
            rsyncPasswordFile.write(gearman_worker.collectionSystemTransfer['rsyncPass'])
        os.chmod(rsyncPasswordFilePath, 0o600)

    except IOError:
        logging.error("Error Saving temporary rsync password file")
    
        # Cleanup
        shutil.rmtree(tmpdir)

        return {'verdict': False, 'reason': 'Error Saving temporary rsync password file: ' + rsyncPasswordFilePath}
    
    command = ['rsync', '-r', '--password-file=' + rsyncPasswordFilePath, '--no-motd', 'rsync://' + gearman_worker.collectionSystemTransfer['rsyncUser'] + '@' + gearman_worker.collectionSystemTransfer['rsyncServer'] + sourceDir + '/']

    logging.debug("Command: {}".format(' '.join(command)))

    proc = subprocess.run(command, capture_output=True, text=True)
    rsyncFileList = proc.stdout
    logging.debug("rsyncFileList: {}".format(rsyncFileList))

    # Cleanup
    shutil.rmtree(tmpdir)

    for line in rsyncFileList.splitlines():
        logging.debug('line: {}'.format(line.rstrip('\n')))
        fileOrDir, size, mdate, mtime, filename = line.split(None, 4)
        if fileOrDir.startswith('-'):
            exclude = False
            ignore = False
            include = False
            for filt in filters['ignoreFilter'].split(','):
                #logging.debug("filt")
                if fnmatch.fnmatch(filename, filt):
                    logging.debug("{} ignore".format(filename))
                    ignore = True
                    break
            if not ignore:
                for filt in filters['includeFilter'].split(','): 
                    if fnmatch.fnmatch(filename, filt):
                        for filt in filters['excludeFilter'].split(','): 
                            if fnmatch.fnmatch(filename, filt):
                                #logging.debug("exclude")
                                returnFiles['exclude'].append(filename)
                                exclude = True
                                break
                        if not exclude:
                            if not isascii(filename):
                                logging.debug("{} is not an ascii-encoded unicode string".format(filename))
                                returnFiles['exclude'].append(filename)
                            else:
                                file_mod_time = datetime.datetime.strptime(mdate + ' ' + mtime, "%Y/%m/%d %H:%M:%S")
                                file_mod_time_SECS = (file_mod_time - epoch).total_seconds()
                                logging.debug("file_mod_time_SECS: {}".format(file_mod_time_SECS))
                                if file_mod_time_SECS > dataStart_time and file_mod_time_SECS < threshold_time and file_mod_time_SECS < dataEnd_time:
                                    logging.debug("{} include".format(filename))
                                    returnFiles['include'].append(filename)
                                else:
                                    logging.debug("{} ignored for time reasons".format(filename))

                                include = True

                if not include:
                    logging.debug("{} excluded because file does not match any include or ignore filters".format(filename))
                    returnFiles['exclude'].append(filename)

    returnFiles['include'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['include']]
    returnFiles['exclude'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['exclude']]

    logging.debug('returnFiles: {}'.format(json.dumps(returnFiles, indent=2)))

    return {'verdict': True, 'files': returnFiles}


def build_sshFilelist(gearman_worker, sourceDir):

    returnFiles = {'include':[], 'exclude':[], 'new':[], 'updated':[]}

    staleness = int(gearman_worker.collectionSystemTransfer['staleness']) * 60
    logging.debug("Staleness: {}".format(staleness))

    threshold_time = time.time() - staleness
    logging.debug("Threshold: {}".format(threshold_time))

    dataStart_time = calendar.timegm(time.strptime(gearman_worker.dataStartDate, "%Y/%m/%d %H:%M"))
    logging.debug("Start: {}".format(dataStart_time))

    dataEnd_time = calendar.timegm(time.strptime(gearman_worker.dataEndDate, "%Y/%m/%d %H:%M"))
    logging.debug("End: {}".format(dataEnd_time))

    filters = build_filters(gearman_worker)

    command = ['rsync', '-r', '-e', 'ssh', gearman_worker.collectionSystemTransfer['sshUser'] + '@' + gearman_worker.collectionSystemTransfer['sshServer'] + sourceDir + '/'] if gearman_worker.collectionSystemTransfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.collectionSystemTransfer['sshPass'], 'rsync', '-r', '-e', 'ssh', gearman_worker.collectionSystemTransfer['sshUser'] + '@' + gearman_worker.collectionSystemTransfer['sshServer'] + sourceDir + '/']
    logging.debug("Command: {}".format(' '.join(command)))

    proc = subprocess.run(command, capture_output=True, text=True)

    for line in proc.stdout.splitlines():
        logging.debug("Line: {}".format(line))
        fileOrDir, size, mdate, mtime, name = line.split(None, 4)
        if fileOrDir.startswith('-'):
            filename = name
            logging.debug("file: {}".format(filename))
            exclude = False
            ignore = False
            include = False
            for filt in filters['ignoreFilter'].split(','):
                logging.debug("filt")
                if fnmatch.fnmatch(filename, filt):
                    logging.debug("{} ignore".format(filename))
                    ignore = True
                    break
            if not ignore:
                for filt in filters['includeFilter'].split(','):
                    if fnmatch.fnmatch(filename, filt):
                        for filt in filters['excludeFilter'].split(','):
                            if fnmatch.fnmatch(filename, filt):
                                logging.debug("{} exclude".format(filename))
                                returnFiles['exclude'].append(filename)
                                exclude = True
                                break
                        if not exclude:
                            file_mod_time = (datetime.datetime.strptime(mdate + ' ' + mtime, "%Y/%m/%d %H:%M:%S") - datetime.datetime(1970,1,1,0,0,0)).total_seconds()
                            logging.debug("file_mod_time: {}".format(file_mod_time))
                            if not isascii(filename):
                                logging.debug("{} is not an ascii-encoded unicode string".format(filename))
                                returnFiles['exclude'].append(filename)
                            else:
                                if file_mod_time > dataStart_time and file_mod_time < dataEnd_time:
                                    logging.debug("{} include".format(filename))
                                    returnFiles['include'].append(filename)
                                else:
                                    logging.debug("{} ignored for time reasons".format(filename))

                            include = True

                if not include:
                    logging.debug("{} excluded because file does not match any include or ignore filters".format(filename))
                    returnFiles['exclude'].append(filename)

    returnFiles['include'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['include']]
    returnFiles['exclude'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['exclude']]

    logging.debug('returnFiles: {}'.format(json.dumps(returnFiles, indent=2)))

    return returnFiles


def build_filters(gearman_worker):
    
    return {
        'includeFilter': gearman_worker.collectionSystemTransfer['includeFilter'].replace('{cruiseID}', gearman_worker.cruiseID).replace('{loweringID}', gearman_worker.loweringID),
        'excludeFilter': gearman_worker.collectionSystemTransfer['excludeFilter'].replace('{cruiseID}', gearman_worker.cruiseID).replace('{loweringID}', gearman_worker.loweringID),
        'ignoreFilter': gearman_worker.collectionSystemTransfer['ignoreFilter'].replace('{cruiseID}', gearman_worker.cruiseID).replace('{loweringID}', gearman_worker.loweringID)
    }


def build_destDir(gearman_worker):
    
    return gearman_worker.collectionSystemTransfer['destDir'].replace('{cruiseID}', gearman_worker.cruiseID).replace('{loweringID}', gearman_worker.loweringID).replace('{loweringDataBaseDir}', gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir'])


def build_sourceDir(gearman_worker):
    
    return gearman_worker.collectionSystemTransfer['sourceDir'].replace('{cruiseID}', gearman_worker.cruiseID).replace('{loweringID}', gearman_worker.loweringID).replace('{loweringDataBaseDir}', gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir'])


def build_destDirectories(destDir, filenames):
    files = [os.path.join(destDir, filename) for filename in filenames]

    for file in files:
        parent_dirname = dirname(file)
        try:
            if not os.path.isdir(parent_dirname):
                logging.debug("Creating destination directory: {}".format(parent_dirname))
                os.makedirs(parent_dirname)
        except:
            logging.error("Could not create destination directory: {}".format(parent_dirname))

            
def build_logfileDirPath(gearman_worker):

    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)
    return os.path.join(cruiseDir, gearman_worker.OVDM.getRequiredExtraDirectoryByName('Transfer_Logs')['destDir'])


def transfer_localSourceDir(gearman_worker, gearman_job):

    logging.debug("Transfer from Local Directory")
    
    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)

    if gearman_worker.collectionSystemTransfer['cruiseOrLowering'] == "1":
      destDir = os.path.join(cruiseDir, gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir'], gearman_worker.loweringID, build_destDir(gearman_worker).rstrip('/'))
    else:
      destDir = os.path.join(cruiseDir, build_destDir(gearman_worker).rstrip('/'))

    sourceDir = build_sourceDir(gearman_worker).rstrip('/')
    logging.debug("Source Dir: {}".format(sourceDir))
    logging.debug("Destination Dir: {}".format(destDir))

    logging.debug("Build file list")
    files = build_filelist(gearman_worker, sourceDir)
    logging.debug("Files: {}".format(json.dumps(files['include'], indent=2)))

    fileIndex = 0
    fileCount = len(files['include'])

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncFileListPath = os.path.join(tmpdir, 'rsyncFileList.txt')

    logging.debug("Mod file list")
    localTransferFileList = files['include']
    localTransferFileList = [filename.replace(sourceDir, '', 1) for filename in localTransferFileList]

    logging.debug("Start")
    try:
        with open(rsyncFileListPath, 'w') as rsyncFileListFile:
            for file in localTransferFileList:
                try:
                    rsyncFileListFile.write(str(file) + '\n')
                except Exception as error:
                    logging.warning("File not ascii: {}".format(file))

    except IOError:
        logging.error("Error Saving temporary rsync filelist file {}".format(rsyncFileListPath))

        # Cleanup
        shutil.rmtree(tmpdir)
        return {'verdict': False, 'reason': 'Error Saving temporary rsync filelist file: ' + rsyncFileListPath, 'files': []}

    logging.debug("Done")

    bandwidthLimit = '--bwlimit=' + gearman_worker.collectionSystemTransfer['bandwidthLimit'] if gearman_worker.collectionSystemTransfer['bandwidthLimit'] != '0' else '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    command = ['rsync', '-tri', bandwidthLimit, '--files-from=' + rsyncFileListPath, sourceDir + '/', destDir]

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
    
    files['new'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/'), filename) for filename in files['new']]
    files['updated'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/'), filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return {'verdict': True, 'files': files}


def transfer_smbSourceDir(gearman_worker, gearman_job):

    logging.debug("Transfer from SMB Source")

    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)
    
    filters = build_filters(gearman_worker)

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
 
    # Create mountpoint
    mntPoint = os.path.join(tmpdir, 'mntpoint')
    os.mkdir(mntPoint, 0o755)

    destDir = os.path.join(cruiseDir, gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir'], gearman_worker.loweringID, build_destDir(gearman_worker).rstrip('/')) if gearman_worker.collectionSystemTransfer['cruiseOrLowering'] == "1" else  os.path.join(cruiseDir, build_destDir(gearman_worker).rstrip('/'))
    sourceDir = os.path.join(mntPoint, build_sourceDir(gearman_worker).rstrip('/')).rstrip('/')
    logging.debug("Source Dir: {}".format(sourceDir))
    logging.debug("Destinstation Dir: {}".format(destDir))

    # Mount SMB Share
    logging.debug("Mounting SMB Share")

    ver_test_command = ['smbclient', '-L', gearman_worker.collectionSystemTransfer['smbServer'], '-W', gearman_worker.collectionSystemTransfer['smbDomain'], '-m', 'SMB2', '-g', '-N'] if gearman_worker.collectionSystemTransfer['smbUser'] == 'guest' else ['smbclient', '-L', gearman_worker.collectionSystemTransfer['smbServer'], '-W', gearman_worker.collectionSystemTransfer['smbDomain'], '-m', 'SMB2', '-g', '-U', gearman_worker.collectionSystemTransfer['smbUser'] + '%' + gearman_worker.collectionSystemTransfer['smbPass']]
    logging.debug("SMB version test command: {}".format(' '.join(ver_test_command)))

    vers="2.1"
    proc = subprocess.Popen(ver_test_command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

    while True:

        line = proc.stdout.readline()

        if proc.poll() is not None:
            break

        if not line:
            continue

        if line.startswith('OS=[Windows 5.1]'):
            vers="1.0"
            break

    mount_command = ['sudo', 'mount', '-t', 'cifs', gearman_worker.collectionSystemTransfer['smbServer'], mntPoint, '-o', 'ro' + ',guest' + ',domain=' + gearman_worker.collectionSystemTransfer['smbDomain'] + ',vers=' + vers] if gearman_worker.collectionSystemTransfer['smbUser'] == 'guest' else ['sudo', 'mount', '-t', 'cifs', gearman_worker.collectionSystemTransfer['smbServer'], mntPoint, '-o', 'ro' + ',username=' + gearman_worker.collectionSystemTransfer['smbUser'] + ',password=' + gearman_worker.collectionSystemTransfer['smbPass'] + ',domain=' + gearman_worker.collectionSystemTransfer['smbDomain'] + ',vers=' + vers]
    logging.debug("Mount command: {}".format(' '.join(mount_command)))
    
    proc = subprocess.run(mount_command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    
    logging.debug("Build file list")
    files = build_filelist(gearman_worker, sourceDir)
    
    logging.debug("File List: {}".format(json.dumps(files['include'], indent=2)))
    
    fileIndex = 0
    fileCount = len(files['include'])
    
    rsyncFileListPath = os.path.join(tmpdir, 'rsyncFileList.txt')
        
    try:
        with open(rsyncFileListPath, 'w') as rsyncFileListFile:
            rsyncFileListFile.write('\n'.join(files['include']))

    except IOError:
        logging.error("Error Saving temporary rsync filelist file")
            
        # Cleanup
        time.sleep(2)
        subprocess.call(['umount', mntPoint])
        shutil.rmtree(tmpdir)
            
        return {'verdict': False, 'reason': 'Error Saving temporary rsync filelist file: ' + rsyncFileListPath, 'files': []}

    bandwidthLimit = '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    if gearman_worker.collectionSystemTransfer['bandwidthLimit'] != '0':
        bandwidthLimit = '--bwlimit=' + gearman_worker.collectionSystemTransfer['bandwidthLimit']

    command = ['rsync', '-trim', bandwidthLimit, '--files-from=' + rsyncFileListPath, sourceDir, destDir]

    logging.debug("Transfer Command: {}".format(' '.join(command)))

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)

    while True:
        
        line = proc.stdout.readline().rstrip('\n')
        
        if proc.poll() is not None:
            break

        if not line:
            continue

        logging.debug('line {}'.format(line))
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['new'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['updated'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
            
        if gearman_worker.stop:
            logging.debug("Stopping")
            proc.terminate()
            break
    
    files['new'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/').rstrip('/'),filename) for filename in files['new']]
    files['updated'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/').rstrip('/'),filename) for filename in files['updated']]

    # Cleanup
    time.sleep(2)
    logging.debug('Unmounting SMB Share')
    subprocess.call(['umount', mntPoint])
    shutil.rmtree(tmpdir)

    return {'verdict': True, 'files': files}

def transfer_rsyncSourceDir(gearman_worker, gearman_job):

    logging.debug("Transfer from RSYNC Server")

    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)

    if gearman_worker.collectionSystemTransfer['cruiseOrLowering'] == "1":
      destDir = os.path.join(cruiseDir, gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir'], gearman_worker.loweringID, build_destDir(gearman_worker).rstrip('/'))
    else:
      destDir = os.path.join(cruiseDir, build_destDir(gearman_worker).rstrip('/'))

    sourceDir = build_sourceDir(gearman_worker)
    
    logging.debug("Source Dir: {}".format(sourceDir))
    logging.debug("Destinstation Dir: {}".format(destDir))
    
    logging.debug("Build file list")
    output_results = build_rsyncFilelist(gearman_worker, sourceDir)

    if not output_results['verdict']:
        return {'verdict': False, 'reason': output_results['reason'], 'files':[]}

    files = output_results['files']
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    fileIndex = 0
    fileCount = len(files['include'])
    
    rsyncPasswordFilePath = os.path.join(tmpdir, 'passwordFile')

    try:
        with open(rsyncPasswordFilePath, 'w') as rsyncPasswordFile:
            rsyncPasswordFile.write(gearman_worker.collectionSystemTransfer['rsyncPass'])

        os.chmod(rsyncPasswordFilePath, 0o600)

    except IOError:
        logging.error("Error Saving temporary rsync password file")
        rsyncPasswordFile.close()

        # Cleanup
        shutil.rmtree(tmpdir)

        return {'verdict': False, 'reason': 'Error Saving temporary rsync password file: ' + rsyncPasswordFilePath}

    rsyncFileListPath = os.path.join(tmpdir, 'rsyncFileList.txt')
        
    try:
        with open(rsyncFileListPath, 'w') as rsyncFileListFile:
            rsyncFileListFile.write('\n'.join(files['include']))

    except IOError:
        logging.error("Error Saving temporary rsync filelist file")
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return {'verdict': False, 'reason': 'Error Saving temporary rsync filelist file: ' + rsyncFileListPath, 'files':[]}

    bandwidthLimit = '--bwlimit=' + gearman_worker.collectionSystemTransfer['bandwidthLimit'] if gearman_worker.collectionSystemTransfer['bandwidthLimit'] != '0' else '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    command = ['rsync', '-tri', bandwidthLimit, '--no-motd', '--files-from=' + rsyncFileListPath, '--password-file=' + rsyncPasswordFilePath, 'rsync://' + gearman_worker.collectionSystemTransfer['rsyncUser'] + '@' + gearman_worker.collectionSystemTransfer['rsyncServer'] + sourceDir, destDir]

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
    
    files['new'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/').rstrip('/'),filename) for filename in files['new']]
    files['updated'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/').rstrip('/'),filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return {'verdict': True, 'files': files}


def transfer_sshSourceDir(gearman_worker, gearman_job):

    logging.debug("Transfer from SSH Server")

    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)
    
    if gearman_worker.collectionSystemTransfer['cruiseOrLowering'] == "1":
      destDir = os.path.join(cruiseDir, gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir'], gearman_worker.loweringID, build_destDir(gearman_worker).rstrip('/'))
    else:
      destDir = os.path.join(cruiseDir, build_destDir(gearman_worker).rstrip('/'))

    sourceDir = build_sourceDir(gearman_worker).rstrip('/')
    
    logging.debug("Source Dir: {}".format(sourceDir))
    logging.debug("Destinstation Dir: {}".format(destDir))
    
    logging.debug("Build file list")
    files = build_sshFilelist(gearman_worker, sourceDir)
    logging.debug('Files: {}'.format(files))
        
    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    sshFileListPath = os.path.join(tmpdir, 'sshFileList.txt')

    fileIndex = 0
    fileCount = len(files['include'])
    
    try:
        with open(sshFileListPath, 'w') as sshFileListFile:
            sshFileListFile.write('\n'.join(files['include']))

    except IOError:
        logging.debug("Error Saving temporary ssh filelist file")
        sshFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return {'verdict': False, 'reason': 'Error Saving temporary rsync filelist file: ' + sshFileListPath, 'files':[]}

    bandwidthLimit = '--bwlimit=' + gearman_worker.collectionSystemTransfer['bandwidthLimit'] if gearman_worker.collectionSystemTransfer['bandwidthLimit'] != '0' else '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    command = ['rsync', '-tri', bandwidthLimit, '--files-from=' + sshFileListPath, '-e', 'ssh', gearman_worker.collectionSystemTransfer['sshUser'] + '@' + gearman_worker.collectionSystemTransfer['sshServer'] + ':' + sourceDir, destDir] if gearman_worker.collectionSystemTransfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.collectionSystemTransfer['sshPass'], 'rsync', '-tri', bandwidthLimit, '--files-from=' + sshFileListPath, '-e', 'ssh', gearman_worker.collectionSystemTransfer['sshUser'] + '@' + gearman_worker.collectionSystemTransfer['sshServer'] + ':' + sourceDir, destDir]
    
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
    
    files['new'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/').rstrip('/'),filename) for filename in files['new']]
    files['updated'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/').rstrip('/'),filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return {'verdict': True, 'files': files}


class OVDMGearmanWorker(python3_gearman.GearmanWorker):
    
    def __init__(self):
        self.stop = False
        self.OVDM = OpenVDM_API()
        self.transferStartDate = ''
        self.cruiseID = ''
        self.loweringID = ''
        self.cruiseStartDate = ''
        self.cruiseEndDate = ''
        self.loweringStartDate = ''
        self.loweringEndDate = ''
        self.dataStartDate = ''
        self.dataEndDate = ''
        self.systemStatus = ''
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
            elif self.collectionSystemTransfer['status'] == "1": #not running
                logging.info("Transfer job for {} skipped because a transfer for that collection system is already in-progress".format(self.collectionSystemTransfer['name']))
                return super(OVDMGearmanWorker, self).on_job_complete(current_job, json.dumps({'parts':[{"partName": "Transfer In-Progress", "result": "Fail", "reason": "Transfer is already in-progress"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

        except:
            return super(OVDMGearmanWorker, self).on_job_complete(current_job, json.dumps({'parts':[{"partName": "Located Collection System Tranfer Data", "result": "Fail", "reason": "Could not find retrieve data for collection system transfer from OpenVDM API"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

        self.systemStatus = payloadObj['systemStatus'] if 'systemStatus' in payloadObj else self.OVDM.getSystemStatus()

        if self.systemStatus == "Off":
            logging.info("Transfer job for {} skipped because that collection system transfer is currently disabled".format(self.collectionSystemTransfer['name']))
            return super(OVDMGearmanWorker, self).on_job_complete(current_job, json.dumps({'parts':[{"partName": "Transfer Enabled", "result": "Fail", "reason": "Transfer is disabled"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

        self.collectionSystemTransfer.update(payloadObj['collectionSystemTransfer'])
        self.cruiseID = payloadObj['cruiseID'] if 'cruiseID' in payloadObj else self.OVDM.getCruiseID()
        self.cruiseStartDate = payloadObj['cruiseStartDate'] if 'cruiseStartDate' in payloadObj else self.OVDM.getCruiseStartDate()
        self.cruiseEndDate = payloadObj['cruiseEndDate'] if 'cruiseEndDate' in payloadObj else self.OVDM.getCruiseEndDate()
        self.loweringID = payloadObj['loweringID'] if 'loweringID' in payloadObj else self.OVDM.getLoweringID()
        self.loweringStartDate = payloadObj['loweringStartDate'] if 'loweringStartDate' in payloadObj else self.OVDM.getLoweringStartDate()
        self.loweringEndDate = payloadObj['loweringEndDate'] if 'loweringEndDate' in payloadObj else self.OVDM.getLoweringEndDate()

        logging.info("Job: {}, {} transfer started at: {}".format(current_job.handle, self.collectionSystemTransfer['name'], time.strftime("%D %T", time.gmtime())))

        self.transferStartDate = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

        #set temporal bounds to extremes if temporal bounds should not be used
        self.dataStartDate = "1970/01/01 00:00"
        self.dataEndDate = "9999/12/31 23:59"
        
        #set temporal bounds for transfer based on whether the transfer should use cruise or lowering start/end times
        if self.collectionSystemTransfer['useStartDate'] == '1':
            if self.collectionSystemTransfer['cruiseOrLowering'] == "0":
                logging.debug("Using cruise Time bounds")
                self.dataStartDate = self.cruiseStartDate
                if self.cruiseEndDate != '':
                    self.dataEndDate = self.cruiseEndDate
            else:
                logging.debug("Using lowering Time bounds")
                self.dataStartDate = self.loweringStartDate
                if self.loweringEndDate != '':
                    self.dataEndDate = self.loweringEndDate

        logging.debug("Start date/time filter: {}".format(self.dataStartDate))
        logging.debug("End date/time filter: {}".format(self.dataEndDate))
        
        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()

        return super(OVDMGearmanWorker, self).on_job_execute(current_job)

    
    def on_job_exception(self, current_job, exc_info):
        logging.error("Job: {}, {} transfer failed at: {}".format(current_job.handle, self.collectionSystemTransfer['name'], time.strftime("%D %T", time.gmtime())))
        
        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail", "reason": "Unknown"}]))
        self.OVDM.setError_collectionSystemTransfer(self.collectionSystemTransfer['collectionSystemTransferID'], 'Worker crashed')

        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)

    
    def on_job_complete(self, current_job, job_results):
        resultsObj = json.loads(job_results)

        if resultsObj['files']['new'] or resultsObj['files']['updated']:

            logging.debug("Preparing subsequent Gearman jobs")
            gm_client = python3_gearman.GearmanClient([self.OVDM.getGearmanServer()])

            jobData = {
                'cruiseID': self.cruiseID,
                'collectionSystemTransferID': self.collectionSystemTransfer['collectionSystemTransferID'],
                'files': resultsObj['files']
            }
            
            for task in self.OVDM.getTasksForHook('runCollectionSystemTransfer'):
                logging.info("Adding post task: {}".format(task))
                submitted_job_request = gm_client.submit_job(task, json.dumps(jobData), background=True)


        if len(resultsObj['parts']) > 0:
            if resultsObj['parts'][-1]['result'] == "Fail": # Final Verdict
                self.OVDM.setError_collectionSystemTransfer(self.collectionSystemTransfer['collectionSystemTransferID'], resultsObj['parts'][-1]['reason'])
            else:
                self.OVDM.setIdle_collectionSystemTransfer(self.collectionSystemTransfer['collectionSystemTransferID'])
        else:
            self.OVDM.setIdle_collectionSystemTransfer(self.collectionSystemTransfer['collectionSystemTransferID'])

        logging.debug("Job Results: {}".format(json.dumps(resultsObj, indent=2)))
        logging.info("Job: {}, {} transfer completed at: {}".format(current_job.handle, self.collectionSystemTransfer['name'], time.strftime("%D %T", time.gmtime())))
            
        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_results)

    
    def stopTask(self):
        self.stop = True
        logging.warning("Stopping current task...")

    
    def quitWorker(self):
        self.stop = True
        logging.warning("Quitting worker...")
        self.shutdown()


def task_runCollectionSystemTransfer(gearman_worker, current_job):

    time.sleep(randint(0,2))
    
    job_results = {
        'parts': [
            {"partName": "Transfer In-Progress", "result": "Pass"},
            {"partName": "Transfer Enabled", "result": "Pass"}
        ],
        'files': {
            'new': [],
            'updated':[],
            'exclude':[]
        }
    }

    warehouseUser = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']
    baseDir = gearman_worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, gearman_worker.cruiseID)
    collectionSystemDestDir = os.path.join(cruiseDir, gearman_worker.shipboardDataWarehouseConfig['loweringDataBaseDir'], gearman_worker.loweringID, build_destDir(gearman_worker)) if gearman_worker.collectionSystemTransfer['cruiseOrLowering'] == "1" else os.path.join(cruiseDir, build_destDir(gearman_worker))
    collectionSystemSourceDir = build_sourceDir(gearman_worker).rstrip('/')
    
    logging.debug("Setting transfer status to 'Running'")
    gearman_worker.OVDM.setRunning_collectionSystemTransfer(gearman_worker.collectionSystemTransfer['collectionSystemTransferID'], os.getpid(), current_job.handle)
        
    logging.info("Testing connection")
    gearman_worker.send_job_status(current_job, 1, 10)

    gm_client = python3_gearman.GearmanClient([gearman_worker.OVDM.getGearmanServer()])

    gmData = {}
    gmData['collectionSystemTransfer'] = gearman_worker.collectionSystemTransfer
    gmData['cruiseID'] = gearman_worker.cruiseID
    
    completed_job_request = gm_client.submit_job("testCollectionSystemTransfer", json.dumps(gmData))
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
    if gearman_worker.collectionSystemTransfer['transferType'] == "1": # Local Directory
        output_results = transfer_localSourceDir(gearman_worker, current_job)
    elif  gearman_worker.collectionSystemTransfer['transferType'] == "2": # Rsync Server
        output_results = transfer_rsyncSourceDir(gearman_worker, current_job)
    elif  gearman_worker.collectionSystemTransfer['transferType'] == "3": # SMB Server
        output_results = transfer_smbSourceDir(gearman_worker, current_job)
    elif  gearman_worker.collectionSystemTransfer['transferType'] == "4": # SSH Server
        output_results = transfer_sshSourceDir(gearman_worker, current_job)

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
        logging.warning("{} misnamed file(s) encountered".format(len(job_results['files']['exclude'])))

    gearman_worker.send_job_status(current_job, 9, 10)
    
    if job_results['files']['new'] or job_results['files']['updated']:

        logging.info("Setting file permissions")

        permission_status = True

        output_results = set_ownerGroupPermissions(warehouseUser, os.path.join(build_logfileDirPath(gearman_worker), collectionSystemDestDir))

        if not output_results['verdict']:
            logging.error("Error setting destination directory file/directory ownership/permissions: {}".format(collectionSystemDestDir))
            job_results['parts'].append({"partName": "Setting file/directory ownership/permissions", "result": "Fail", "reason": output_results['reason']})
    
        job_results['parts'].append({"partName": "Setting file/directory ownership/permissions", "result": "Pass"})

        logging.debug("Building logfiles")

        logfileName = gearman_worker.collectionSystemTransfer['name'] + '_' + gearman_worker.transferStartDate + '.log'

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
            return job_results
    
        output_results = set_ownerGroupPermissions(warehouseUser, os.path.join(build_logfileDirPath(gearman_worker), logfileName))

        if not output_results['verdict']:
            job_results['parts'].append({"partName": "Set OpenVDM config file ownership/permissions", "result": "Fail", "reason": output_results['reason']})
            return json.dumps(job_results)

    logfileName = gearman_worker.collectionSystemTransfer['name'] + '_Exclude.log'
    logContents = {
        'files': {
            'exclude': job_results['files']['exclude']
        }
    }
    logContents['files']['exclude'] = job_results['files']['exclude']

    output_results = output_JSONDataToFile(os.path.join(build_logfileDirPath(gearman_worker), logfileName), logContents['files'])

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Write exclude logfile", "result": "Pass"})
    else:
        logging.error("Error writing transfer logfile: {}".format(output_results['reason']))
        job_results['parts'].append({"partName": "Write exclude logfile", "result": "Fail", "reason": output_results['reason']})
        return job_results

    output_results = set_ownerGroupPermissions(warehouseUser, os.path.join(build_logfileDirPath(gearman_worker), logfileName))

    if not output_results['verdict']:
        logging.error("Error setting ownership/permissions for transfer logfile: {}".format(logfileName))
        job_results['parts'].append({"partName": "Set transfer logfile ownership/permissions", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(current_job, 10, 10)
    
    time.sleep(2)

    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle collection system transfer related tasks')
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

    logging.info("\tTask: runCollectionSystemTransfer")
    new_worker.register_task("runCollectionSystemTransfer", task_runCollectionSystemTransfer)

    logging.info("Waiting for jobs...")
    new_worker.work()
