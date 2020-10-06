# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_runCollectionSystemTransfer.py
#
#  DESCRIPTION:  Gearman worker that handles the transfer of data from the Collection
#                System to the Shipboard Data Warehouse.
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.3
#      CREATED:  2015-01-01
#     REVISION:  2018-03-19
#
# LICENSE INFO: Open Vessel Data Management v2.3 (OpenVDMv2)
#               Copyright (C) OceanDataRat.org 2017
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
import tempfile
import gearman
import shutil
import json
import time
import calendar
import datetime
import fnmatch
import subprocess
import signal
import pwd
import grp
import openvdm
from random import randint

DEBUG = False
new_worker = None


def debugPrint(*args, **kwargs):
    global DEBUG
    if DEBUG:
        errPrint(*args, **kwargs)


def errPrint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def build_filelist(worker, sourceDir):

    returnFiles = {'include':[], 'exclude':[], 'new':[], 'updated':[], 'filesize':[]}

    debugPrint(returnFiles)

    staleness = int(worker.collectionSystemTransfer['staleness']) * 60 #5 Mintues
    debugPrint("Staleness:", staleness)

    threshold_time = time.time() - staleness
    debugPrint("Threshold:", threshold_time)

    dataStart_time = calendar.timegm(time.strptime(worker.dataStartDate, "%Y/%m/%d %H:%M"))
    debugPrint("Start:", dataStart_time)

    dataEnd_time = calendar.timegm(time.strptime(worker.dataEndDate, "%Y/%m/%d %H:%M"))
    debugPrint("End:", dataEnd_time)

    filters = build_filters(worker)

    for root, dirnames, filenames in os.walk(sourceDir):
        for filename in filenames:

            if os.path.islink(os.path.join(root, filename)):
                debugPrint(filename, "is a symlink, skipping")
                continue

            exclude = False
            ignore = False
            include = False
            for filt in filters['ignoreFilter'].split(','):
                #print filt
                if fnmatch.fnmatch(os.path.join(root, filename), filt):
                    debugPrint(filename, "ignored")
                    ignore = True
                    break
            if not ignore:
                for filt in filters['includeFilter'].split(','): 
                    if fnmatch.fnmatch(filename, filt):
                        for filt in filters['excludeFilter'].split(','): 
                            if fnmatch.fnmatch(filename, filt):
                                debugPrint(filename, "excluded by exclude filter")
                                returnFiles['exclude'].append(os.path.join(root, filename))
                                exclude = True
                                break
                        if not exclude:
                            debugPrint('Filename:', os.path.join(root, filename))
                            file_mod_time = os.stat(os.path.join(root, filename)).st_mtime
                            #debugPrint("file_mod_time:",file_mod_time)
                            try:
                                filename.decode('ascii')
                            except UnicodeEncodeError:
                                debugPrint(filename, "is not an ascii-encoded unicode string")
                                returnFiles['exclude'].append(os.path.join(root, filename))
                            else:
                                if file_mod_time > dataStart_time and file_mod_time < dataEnd_time:
                                    debugPrint(filename, "included")
                                    returnFiles['include'].append(os.path.join(root, filename))
                                    returnFiles['filesize'].append(os.stat(os.path.join(root, filename)).st_size)
                                else:
                                    debugPrint(filename, "ignored for time reasons")

                                include = True

                if not include and not exclude:
                    debugPrint(filename, "excluded because file does not match any include or ignore filters")
                    returnFiles['exclude'].append(os.path.join(root, filename))

    if not worker.collectionSystemTransfer['staleness'] == '0':
        debugPrint("Checking for changing filesizes")
        #debugPrint("Pausing for 5 seconds")
        time.sleep(5)
        for idx, val in enumerate(returnFiles['include']):
            #debugPrint('idx:',idx,'val:',val,'filesize:',returnFiles['filesize'][idx])
            if not os.stat(val).st_size == returnFiles['filesize'][idx]:
                debugPrint(val, "removed because it's size is changing")
                del returnFiles['include'][idx]
                del returnFiles['filesize'][idx]

    del returnFiles['filesize']

    returnFiles['include'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['include']]
    returnFiles['exclude'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['exclude']]

    return returnFiles


def build_rsyncFilelist(worker, sourceDir):

    returnFiles = {'include':[], 'exclude':[], 'new':[], 'updated':[]}

    staleness = int(worker.collectionSystemTransfer['staleness']) * 60
    threshold_time = time.time() - staleness # 5 minutes
    epoch = datetime.datetime.strptime('1970/01/01 00:00:00', "%Y/%m/%d %H:%M:%S") 
    cruiseStart_time = calendar.timegm(time.strptime(worker.cruiseStartDate, "%Y/%m/%d %H:%M"))
    cruiseEnd_time = calendar.timegm(time.strptime(worker.cruiseEndDate, "%Y/%m/%d %H:%M"))

    debugPrint("Threshold:",threshold_time)
    debugPrint("Start:",cruiseStart_time)
    debugPrint("End:",cruiseEnd_time)

    filters = build_filters(worker)

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncPasswordFilePath = os.path.join(tmpdir, 'passwordFile')

    try:
        rsyncPasswordFile = open(rsyncPasswordFilePath, 'w')
        rsyncPasswordFile.write(worker.collectionSystemTransfer['rsyncPass'])

    except IOError:
        errPrint("Error Saving temporary rsync password file")
        rsyncPasswordFile.close()

        # Cleanup
        shutil.rmtree(tmpdir)

        return {'verdict': False, 'reason': 'Error Saving temporary rsync password file: ' + rsyncPasswordFilePath}

    finally:
        rsyncPasswordFile.close()
        os.chmod(rsyncPasswordFilePath, 0600)

    command = ['rsync', '-r', '--password-file=' + rsyncPasswordFilePath, '--no-motd', 'rsync://' + worker.collectionSystemTransfer['rsyncUser'] + '@' + worker.collectionSystemTransfer['rsyncServer'] + sourceDir]

    s = ' '
    debugPrint(s.join(command))

    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = proc.communicate()
    rsyncFileList = out

    # Cleanup
    shutil.rmtree(tmpdir)

    #print "rsyncFileListOut: " + rsyncFileList

    for line in rsyncFileList.splitlines():
        #debugPrint('line:', line.rstrip('\n'))
        fileOrDir, size, mdate, mtime, filename = line.split(None, 4)
        if fileOrDir.startswith('-'):
            exclude = False
            ignore = False
            include = False
            for filt in filters['ignoreFilter'].split(','):
                #print filt
                if fnmatch.fnmatch(filename, filt):
                    #print "ignore"
                    ignore = True
                    break
            if not ignore:
                for filt in filters['includeFilter'].split(','): 
                    if fnmatch.fnmatch(filename, filt):
                        for filt in filters['excludeFilter'].split(','): 
                            if fnmatch.fnmatch(filename, filt):
                                #print "exclude"
                                returnFiles['exclude'].append(filename)
                                exclude = True
                                break
                        if not exclude:
                            try:
                                filename.decode('ascii')
                            except UnicodeEncodeError:
                                debugPrint(filename, "is not an ascii-encoded unicode string")
                                returnFiles['exclude'].append(os.path.join(root, filename))
                            else:
                                file_mod_time = datetime.datetime.strptime(mdate + ' ' + mtime, "%Y/%m/%d %H:%M:%S")
                                file_mod_time_SECS = (file_mod_time - epoch).total_seconds()
                                #debugPrint("file_mod_time_SECS:", str(file_mod_time_SECS))
                                if file_mod_time_SECS > cruiseStart_time and file_mod_time_SECS < threshold_time and file_mod_time_SECS < cruiseEnd_time:
                                    #debugPrint("include")
                                    returnFiles['include'].append(filename)
                                else:
                                    debugPrint(filename, "skipped for time reasons")

                                include = True

                if not include:
                    #print "exclude"
                    returnFiles['exclude'].append(filename)

    returnFiles['include'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['include']]
    returnFiles['exclude'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['exclude']]

    #debugPrint('returnFiles:', json.dumps(returnFiles, indent=2))

    return {'verdict': True, 'files': returnFiles}


def build_sshFilelist(worker, sourceDir):

    returnFiles = {'include':[], 'exclude':[], 'new':[], 'updated':[]}

    staleness = int(worker.collectionSystemTransfer['staleness']) * 60
    threshold_time = time.time() - (int(worker.collectionSystemTransfer['staleness']) * 60) # 5 minutes
    epoch = datetime.datetime.strptime('1970/01/01 00:00:00', "%Y/%m/%d %H:%M:%S")
    cruiseStart_time = calendar.timegm(time.strptime(worker.cruiseStartDate, "%Y/%m/%d %H:%M"))
    cruiseEnd_time = calendar.timegm(time.strptime(worker.cruiseEndDate, "%Y/%m/%d %H:%M"))

    debugPrint("Threshold:",threshold_time)
    debugPrint("Start:",cruiseStart_time)
    debugPrint("End:",cruiseEnd_time)

    filters = build_filters(worker)
    
    rsyncFileList = ''

    if worker.collectionSystemTransfer['sshUseKey'] == '1':
        command = ['rsync', '-r', '-e', 'ssh', worker.collectionSystemTransfer['sshUser'] + '@' + worker.collectionSystemTransfer['sshServer'] + ':' + sourceDir + '/']    
    else:
        command = ['sshpass', '-p', worker.collectionSystemTransfer['sshPass'], 'rsync', '-r', '-e', 'ssh', worker.collectionSystemTransfer['sshUser'] + '@' + worker.collectionSystemTransfer['sshServer'] + ':' + sourceDir + '/']
    
    s = ' '
    debugPrint("Command:",s.join(command))
        
    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = proc.communicate()
    rsyncFileList = out
        
    #debugPrint("rsyncFileListOut:", + rsyncFileList)
        
    for line in rsyncFileList.splitlines():
        #debugPrint("line:", line)
        fileOrDir, size, mdate, mtime, name = line.split(None, 4)
        if fileOrDir.startswith('-'):
            filename = name
            #print name
            exclude = False
            ignore = False
            include = False
            for filt in filters['ignoreFilter'].split(','):
                #print filt
                if fnmatch.fnmatch(filename, filt):
                    #print "ignore"
                    ignore = True
                    break
            if not ignore:
                for filt in filters['includeFilter'].split(','): 
                    if fnmatch.fnmatch(filename, filt):
                        for filt in filters['excludeFilter'].split(','): 
                            if fnmatch.fnmatch(filename, filt):
                                #print "exclude"
                                returnFiles['exclude'].append(filename)
                                exclude = True
                                break
                        if not exclude:
                            file_mod_time = datetime.datetime.strptime(mdate + ' ' + mtime, "%Y/%m/%d %H:%M:%S")
                            file_mod_time_SECS = (file_mod_time - epoch).total_seconds()
                            #debugPrint("file_mod_time_SECS:", str(file_mod_time_SECS))
                            if file_mod_time_SECS > cruiseStart_time and file_mod_time_SECS < threshold_time and file_mod_time_SECS < cruiseEnd_time:
                                #debugPrint("include")
                                returnFiles['include'].append(filename)
                            #else:
                                #debugPrint(filename, "skipped for time reasons")

                            include = True

                if not include:
                    #debugPrint("exclude")
                    returnFiles['exclude'].append(filename)        

    returnFiles['include'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['include']]
    returnFiles['exclude'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['exclude']]

    #debugPrint('returnFiles:', json.dumps(returnFiles, indent=2))

    return returnFiles


def build_filters(worker):
    
    rawFilters = {'includeFilter': worker.collectionSystemTransfer['includeFilter'],'excludeFilter': worker.collectionSystemTransfer['excludeFilter'],'ignoreFilter': worker.collectionSystemTransfer['ignoreFilter']}
    returnFilters = rawFilters
    #print json.dumps(rawFilters, indent=2)
    
    returnFilters['includeFilter'] = returnFilters['includeFilter'].replace('{cruiseID}', worker.cruiseID)
    returnFilters['includeFilter'] = returnFilters['includeFilter'].replace('{loweringID}', worker.loweringID)

    returnFilters['excludeFilter'] = returnFilters['excludeFilter'].replace('{cruiseID}', worker.cruiseID)
    returnFilters['excludeFilter'] = returnFilters['excludeFilter'].replace('{loweringID}', worker.loweringID)
    
    returnFilters['ignoreFilter'] =  returnFilters['ignoreFilter'].replace('{cruiseID}', worker.cruiseID)
    returnFilters['ignoreFilter'] =  returnFilters['ignoreFilter'].replace('{loweringID}', worker.loweringID)
    
    #print json.dumps(returnFilters, indent=2)
    return returnFilters


def build_destDir(worker):
    
    returnDestDir = worker.collectionSystemTransfer['destDir'].replace('{cruiseID}', worker.cruiseID)
    returnDestDir = returnDestDir.replace('{loweringID}', worker.loweringID)
    returnDestDir = returnDestDir.replace('{loweringDataBaseDir}', worker.shipboardDataWarehouseConfig['loweringDataBaseDir'])

    return returnDestDir


def build_sourceDir(worker):
    
    returnSourceDir = worker.collectionSystemTransfer['sourceDir'].replace('{cruiseID}', worker.cruiseID)
    returnSourceDir = returnSourceDir.replace('{loweringID}', worker.loweringID)
    returnSourceDir = returnSourceDir.replace('{loweringDataBaseDir}', worker.shipboardDataWarehouseConfig['loweringDataBaseDir'])

    return returnSourceDir
    

def build_destDirectories(destDir, files):
    files = [filename.replace(filename, destDir + '/' + filename, 1) for filename in files]
    #print 'DECODED Files:', json.dumps(files, indent=2)

    for dirname in set(os.path.dirname(p) for p in files):
        if not os.path.isdir(dirname):
            #print "Creating Directory: " + dirname
            os.makedirs(dirname)

            
def build_logfileDirPath(worker):

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    warehouseTransferLogDir = os.path.join(cruiseDir, worker.OVDM.getRequiredExtraDirectoryByName('Transfer Logs')['destDir'])

    #debugPrint('warehouseTransferLogDir', warehouseTransferLogDir)
    
    return warehouseTransferLogDir


def setOwnerGroupPermissions(worker, path):

    warehouseUser = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']

    debugPrint(path)

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
        return {'verdict': False, 'reason': '\n'.join(reason)}

    return {'verdict': True}

def writeLogFile(worker, logfileName, fileList):

    logfileDir = build_logfileDirPath(worker)
    #debugPrint('logfileDir', logfileDir)
    logfilePath = os.path.join(logfileDir, logfileName)
    
    try:
        #print "Open MD5 Summary MD5 file"
        Logfile = open(logfilePath, 'w')

        #print "Saving MD5 Summary MD5 file"
        Logfile.write(json.dumps(fileList))

    except IOError:
        errPrint("Error Saving transfer logfile")
        return {'verdict': False, 'reason': 'Error Saving transfer logfile: ' + logfilePath}

    finally:
        Logfile.close()

    output_results = setOwnerGroupPermissions(worker, logfilePath)

    if not output_results['verdict']:
        return {'verdict': False, 'reason': output_results['reason']}

    return {'verdict': True}
    

def transfer_localSourceDir(worker, job):

    debugPrint("Transfer from Local Directory")
    
    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)

    if worker.collectionSystemTransfer['cruiseOrLowering'] == "1":
      destDir = os.path.join(cruiseDir, worker.shipboardDataWarehouseConfig['loweringDataBaseDir'], worker.loweringID, build_destDir(worker).rstrip('/'))
    else:
      destDir = os.path.join(cruiseDir, build_destDir(worker).rstrip('/'))

    sourceDir = build_sourceDir(worker).rstrip('/')
    debugPrint("Source Dir:", sourceDir)
    debugPrint("Destination Dir:", destDir)

    debugPrint("Build file list")
    files = build_filelist(worker, sourceDir)
    debugPrint("Files:", json.dumps(files['include'], indent=2))

    fileIndex = 0
    fileCount = len(files['include'])

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncFileListPath = os.path.join(tmpdir, 'rsyncFileList.txt')

    debugPrint("Mod file list")
    localTransferFileList = files['include']
    localTransferFileList = [filename.replace(sourceDir, '', 1) for filename in localTransferFileList]

    debugPrint("Start")
    try:
        rsyncFileListFile = open(rsyncFileListPath, 'w')

    except IOError:
        errPrint("Error Saving temporary rsync filelist file")
        rsyncFileListFile.close()

        # Cleanup
        shutil.rmtree(tmpdir)
        return {'verdict': False, 'reason': 'Error Saving temporary rsync filelist file: ' + rsyncFileListPath, 'files': []}

    debugPrint("Done")

    for file in localTransferFileList:
        try:
            rsyncFileListFile.write(str(file) + '\n')
        except Exception as error:
            debugPrint("File not ascii:", file)
            debugPrint(error)

    #debugPrint("Closing rsync filelist file")
    rsyncFileListFile.close()

    bandwidthLimit = '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    if worker.collectionSystemTransfer['bandwidthLimit'] != '0':
        bandwidthLimit = '--bwlimit=' + worker.collectionSystemTransfer['bandwidthLimit']

    command = ['rsync', '-tri', bandwidthLimit, '--files-from=' + rsyncFileListPath, sourceDir + '/', destDir]

    s = ' '
    debugPrint('Transfer Command:', s.join(command))
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['new'].append(filename)
            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['updated'].append(filename)
            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
            
        if worker.stop:
            debugPrint("Stopping")
            break
    
    files['new'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/').rstrip('/'),filename) for filename in files['new']]
    files['updated'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/').rstrip('/'),filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return {'verdict': True, 'files': files}


def transfer_smbSourceDir(worker, job):

    debugPrint("Transfer from SMB Source")

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    
    filters = build_filters(worker)

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
 
    # Create mountpoint
    mntPoint = os.path.join(tmpdir, 'mntpoint')
    os.mkdir(mntPoint, 0755)

    if worker.collectionSystemTransfer['cruiseOrLowering'] == "1":
      destDir = os.path.join(cruiseDir, worker.shipboardDataWarehouseConfig['loweringDataBaseDir'], worker.loweringID, build_destDir(worker).rstrip('/'))
    else:
      destDir = os.path.join(cruiseDir, build_destDir(worker).rstrip('/'))

    sourceDir = os.path.join(mntPoint, build_sourceDir(worker).rstrip('/')).rstrip('/')
    debugPrint("Source Dir:", sourceDir)
    debugPrint("Destinstation Dir:", destDir)


    # Mount SMB Share
    debugPrint("Mounting SMB Share")
    if worker.collectionSystemTransfer['smbUser'] == 'guest':

        command = ['smbclient', '-L', worker.collectionSystemTransfer['smbServer'], '-W', worker.collectionSystemTransfer['smbDomain'], '-m', 'SMB2', '-g', '-N']

        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        stderr_iterator = iter(proc.stderr.readline, b"")
        vers = ",vers=2.1"
        for line in stderr_iterator:
            if line.startswith('OS=[Windows 5.1]'):
                vers=",vers=1.0"
        
        command = ['sudo', 'mount', '-t', 'cifs', worker.collectionSystemTransfer['smbServer'], mntPoint, '-o', 'ro'+ ',guest' + ',domain='+worker.collectionSystemTransfer['smbDomain']+vers]
        
        s = ' '
        debugPrint(s.join(command))
    
        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()
        
    else:
        command = ['smbclient', '-L', worker.collectionSystemTransfer['smbServer'], '-W', worker.collectionSystemTransfer['smbDomain'], '-m', 'SMB2', '-g', '-U', worker.collectionSystemTransfer['smbUser'] + '%' + worker.collectionSystemTransfer['smbPass']]

        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        stderr_iterator = iter(proc.stderr.readline, b"")
        vers = ",vers=2.1"
        for line in stderr_iterator:
            if line.startswith('OS=[Windows 5.1]'):
                vers=",vers=1.0"

        command = ['sudo', 'mount', '-t', 'cifs', worker.collectionSystemTransfer['smbServer'], mntPoint, '-o', 'ro'+ ',username='+worker.collectionSystemTransfer['smbUser']+',password='+worker.collectionSystemTransfer['smbPass']+',domain='+worker.collectionSystemTransfer['smbDomain']+vers]
        
        s = ' '
        debugPrint(s.join(command))
    
        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()
    
    debugPrint("Build file list")
    files = build_filelist(worker, sourceDir)
    
    debugPrint("File List:", json.dumps(files['include'], indent=2))
    
    fileIndex = 0
    fileCount = len(files['include'])
    
    rsyncFileListPath = os.path.join(tmpdir, 'rsyncFileList.txt')
        
    try:
        rsyncFileListFile = open(rsyncFileListPath, 'w')
        rsyncFileListFile.write('\n'.join(files['include']))

    except IOError:
        errPrint("Error Saving temporary rsync filelist file")
        rsyncFileListFile.close()
            
        # Cleanup
        time.sleep(2)
        subprocess.call(['umount', mntPoint])
        shutil.rmtree(tmpdir)
            
        return {'verdict': False, 'reason': 'Error Saving temporary rsync filelist file: ' + rsyncFileListPath, 'files': []}

    finally:
        rsyncFileListFile.close()

    bandwidthLimit = '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    if worker.collectionSystemTransfer['bandwidthLimit'] != '0':
        bandwidthLimit = '--bwlimit=' + worker.collectionSystemTransfer['bandwidthLimit']


    command = ['rsync', '-trim', bandwidthLimit, '--files-from=' + rsyncFileListPath, sourceDir, destDir]

    s = ' '
    debugPrint('Transfer Command:', s.join(command))

    popen = subprocess.Popen(command, stdout=subprocess.PIPE)

    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #debugPrint('line', line.rstrip('\n')
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['new'].append(filename)
            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['updated'].append(filename)
            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
            
        if worker.stop:
            debugPrint("Stopping")
            break
    
    files['new'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/').rstrip('/'),filename) for filename in files['new']]
    files['updated'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/').rstrip('/'),filename) for filename in files['updated']]

    # Cleanup
    time.sleep(2)
    debugPrint('Unmounting SMB Share')
    subprocess.call(['umount', mntPoint])
    shutil.rmtree(tmpdir)

    return {'verdict': True, 'files': files}

def transfer_rsyncSourceDir(worker, job):

    debugPrint("Transfer from RSYNC Server")

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)

    if worker.collectionSystemTransfer['cruiseOrLowering'] == "1":
      destDir = os.path.join(cruiseDir, worker.shipboardDataWarehouseConfig['loweringDataBaseDir'], worker.loweringID, build_destDir(worker).rstrip('/'))
    else:
      destDir = os.path.join(cruiseDir, build_destDir(worker).rstrip('/'))

    sourceDir = '/' + build_sourceDir(worker).rstrip('/')
    
    debugPrint("Source Dir:", sourceDir)
    debugPrint("Destinstation Dir:", destDir)
    
    debugPrint("Build file list")
    output_results = build_rsyncFilelist(worker, sourceDir)

    if not output_results['verdict']:
        return {'verdict': False, 'reason': output_results['reason'], 'files':[]}

    files = output_results['files']
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    fileIndex = 0
    fileCount = len(files['include'])
    
    rsyncPasswordFilePath = os.path.join(tmpdir, 'passwordFile')

    try:
        rsyncPasswordFile = open(rsyncPasswordFilePath, 'w')
        rsyncPasswordFile.write(worker.collectionSystemTransfer['rsyncPass'])

    except IOError:
        errPrint("Error Saving temporary rsync password file")
        rsyncPasswordFile.close()

        # Cleanup
        shutil.rmtree(tmpdir)

        return {'verdict': False, 'reason': 'Error Saving temporary rsync password file: ' + rsyncPasswordFilePath}

    finally:
        rsyncPasswordFile.close()
        os.chmod(rsyncPasswordFilePath, 0600)

    rsyncFileListPath = os.path.join(tmpdir, 'rsyncFileList.txt')
        
    try:
        rsyncFileListFile = open(rsyncFileListPath, 'w')
        rsyncFileListFile.write('\n'.join(files['include']))

    except IOError:
        errPrint("Error Saving temporary rsync filelist file")
        rsyncFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return {'verdict': False, 'reason': 'Error Saving temporary rsync filelist file: ' + rsyncFileListPath, 'files':[]}

    finally:
        rsyncFileListFile.close()

    bandwidthLimit = '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    if worker.collectionSystemTransfer['bandwidthLimit'] != '0':
        bandwidthLimit = '--bwlimit=' + worker.collectionSystemTransfer['bandwidthLimit']

    
    command = ['rsync', '-ti', bandwidthLimit, '--no-motd', '--files-from=' + rsyncFileListPath, '--password-file=' + rsyncPasswordFilePath, 'rsync://' + worker.collectionSystemTransfer['rsyncUser'] + '@' + worker.collectionSystemTransfer['rsyncServer'] + sourceDir, destDir]

    s = ' '
    debugPrint('Transfer Command:', s.join(command))

    popen = subprocess.Popen(command, stdout=subprocess.PIPE)

    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #debugPrint('line', line.rstrip('\n')
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['new'].append(filename)
            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['updated'].append(filename)
            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
            
        if worker.stop:
            debugPrint("Stopping")
            break
    
    files['new'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/').rstrip('/'),filename) for filename in files['new']]
    files['updated'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/').rstrip('/'),filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return {'verdict': True, 'files': files}


def transfer_sshSourceDir(worker, job):

    debugPrint("Transfer from SSH Server")

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    
    if worker.collectionSystemTransfer['cruiseOrLowering'] == "1":
      destDir = os.path.join(cruiseDir, worker.shipboardDataWarehouseConfig['loweringDataBaseDir'], worker.loweringID, build_destDir(worker).rstrip('/'))
    else:
      destDir = os.path.join(cruiseDir, build_destDir(worker).rstrip('/'))

    sourceDir = build_sourceDir(worker).rstrip('/')
    
    debugPrint("Source Dir:", sourceDir)
    debugPrint("Destinstation Dir:", destDir)
    
    debugPrint("Build file list")
    files = build_sshFilelist(worker, sourceDir)
    #debugPrint('Files', files)
        
    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    sshFileListPath = os.path.join(tmpdir, 'sshFileList.txt')

    fileIndex = 0
    fileCount = len(files['include'])
    
    try:
        sshFileListFile = open(sshFileListPath, 'w')
        sshFileListFile.write('\n'.join(files['include']))

    except IOError:
        debugPrint("Error Saving temporary ssh filelist file")
        sshFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return {'verdict': False, 'reason': 'Error Saving temporary rsync filelist file: ' + sshFileListPath, 'files':[]}

    finally:
        sshFileListFile.close()

    bandwidthLimit = '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    if worker.collectionSystemTransfer['bandwidthLimit'] != '0':
        bandwidthLimit = '--bwlimit=' + worker.collectionSystemTransfer['bandwidthLimit']
    
    command = ''
    
    if worker.collectionSystemTransfer['sshUseKey'] == '1':
        command = ['rsync', '-ti', bandwidthLimit, '--files-from=' + sshFileListPath, '-e', 'ssh', worker.collectionSystemTransfer['sshUser'] + '@' + worker.collectionSystemTransfer['sshServer'] + ':' + sourceDir, destDir]
    else:
        command = ['sshpass', '-p', worker.collectionSystemTransfer['sshPass'], 'rsync', '-ti', bandwidthLimit, '--files-from=' + sshFileListPath, '-e', 'ssh', worker.collectionSystemTransfer['sshUser'] + '@' + worker.collectionSystemTransfer['sshServer'] + ':' + sourceDir, destDir]

    s = ' '
    debugPrint('Transfer Command:',s.join(command))
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #debugPrint('line', line.rstrip('\n')
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['new'].append(filename)
            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['updated'].append(filename)
            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            fileIndex += 1
            
        if worker.stop:
            debugPrint("Stopping")
            break
    
    files['new'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/').rstrip('/'),filename) for filename in files['new']]
    files['updated'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/').rstrip('/'),filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return {'verdict': True, 'files': files}


class OVDMGearmanWorker(gearman.GearmanWorker):
    
    def __init__(self):
        self.stop = False
        self.quit = False
        self.OVDM = openvdm.OpenVDM()
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
        payloadObj = json.loads(current_job.data)
        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()
        self.collectionSystemTransfer = self.OVDM.getCollectionSystemTransfer(payloadObj['collectionSystemTransfer']['collectionSystemTransferID'])
        if not self.collectionSystemTransfer:
            return super(OVDMGearmanWorker, self).on_job_complete(current_job, json.dumps({'parts':[{"partName": "Located Collection System Tranfer Data", "result": "Fail", "reason": "Could not find configuration data for collection system transfer"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

        self.collectionSystemTransfer.update(payloadObj['collectionSystemTransfer'])
        
        self.cruiseID = self.OVDM.getCruiseID()
        self.transferStartDate = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        self.systemStatus = self.OVDM.getSystemStatus()

        if len(payloadObj) > 0:
            try:
                payloadObj['cruiseID']
            except KeyError:
                self.cruiseID = self.OVDM.getCruiseID()
            else:
                self.cruiseID = payloadObj['cruiseID']

            try:
                payloadObj['cruiseStartDate']
            except KeyError:
                self.cruiseStartDate = self.OVDM.getCruiseStartDate()
            else:
                self.cruiseStartDate = payloadObj['cruiseStartDate']

            try:
                payloadObj['cruiseEndDate']
            except KeyError:
                self.cruiseEndDate = self.OVDM.getCruiseEndDate()
                if self.cruiseEndDate == '':
                    self.cruiseEndDate = "9999/12/31 23:59"
            else:
                self.cruiseEndDate = payloadObj['cruiseEndDate']

            try:
                payloadObj['loweringID']
            except KeyError:
                self.loweringID = self.OVDM.getLoweringID()
            else:
                self.loweringID = payloadObj['loweringID']

            try:
                payloadObj['loweringStartDate']
            except KeyError:
                self.loweringStartDate = self.OVDM.getLoweringStartDate()
            else:
                self.loweringStartDate = payloadObj['loweringStartDate']

            try:
                payloadObj['loweringEndDate']
            except KeyError:
                self.loweringEndDate = self.OVDM.getLoweringEndDate()
                if self.loweringEndDate == '':
                    self.loweringEndDate = "9999/12/31 23:59"
            else:
                self.loweringEndDate = payloadObj['loweringEndDate']

            try:
                payloadObj['systemStatus']
            except KeyError:
                self.systemStatus = self.OVDM.getSystemStatus()
            else:
                self.systemStatus = payloadObj['systemStatus']

        #set temporal bounds to extremes if temporal bounds should not be used
        if self.collectionSystemTransfer['useStartDate'] == "0":
            self.dataStartDate = "1970/01/01 00:00"
            self.dataEndDate = "9999/12/31 23:59"
        else:
            #set temporal bounds for transfer based on whether the transfer should use cruise or lowering start/end times
            if self.collectionSystemTransfer['cruiseOrLowering'] == "0":
                debugPrint("Using cruise Time bounds")
                self.dataStartDate = self.cruiseStartDate
                self.dataEndDate = self.cruiseEndDate
            else:
                debugPrint("Using lowering Time bounds")
                self.dataStartDate = self.loweringStartDate
                self.dataEndDate = self.loweringEndDate

        debugPrint("Start:", self.dataStartDate)
        debugPrint("End:", self.dataEndDate)
        
        errPrint("Job:", current_job.handle + ",", self.collectionSystemTransfer['name'], "transfer started at:  ", time.strftime("%D %T", time.gmtime()))
        
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)

    
    def on_job_exception(self, current_job, exc_info):
        errPrint("Job:", current_job.handle + ",", self.collectionSystemTransfer['name'], "transfer failed at:   ", time.strftime("%D %T", time.gmtime()))
        
        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail", "reason": "Unknown"}]))
        self.OVDM.setError_collectionSystemTransfer(self.collectionSystemTransfer['collectionSystemTransferID'], 'Worker crashed')
        
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        errPrint(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)

    
    def on_job_complete(self, current_job, job_results):
        resultsObj = json.loads(job_results)
        
        if resultsObj['files']['new'] or resultsObj['files']['updated']:

            debugPrint("Preparing subsequent Gearman jobs")
            gm_client = gearman.GearmanClient([self.OVDM.getGearmanServer()])

            jobData = {}
            jobData['cruiseID'] = self.cruiseID
            jobData['collectionSystemTransferID'] = self.collectionSystemTransfer['collectionSystemTransferID']
            jobData['files'] = resultsObj['files']
            
            for task in self.OVDM.getTasksForHook('runCollectionSystemTransfer'):
                debugPrint("Adding task:", task)
                submitted_job_request = gm_client.submit_job(task, json.dumps(jobData), background=True)
        
        # If the last part of the results failed
        if len(resultsObj['parts']) > 0:
            if resultsObj['parts'][-1]['result'] == "Fail": # Final Verdict
                if resultsObj['parts'][-1]['partName'] != "Transfer In-Progress": # A failed Transfer in-progress test should not cause an error.
                    self.OVDM.setError_collectionSystemTransfer(self.collectionSystemTransfer['collectionSystemTransferID'], resultsObj['parts'][-1]['reason'])
            else:
                self.OVDM.setIdle_collectionSystemTransfer(self.collectionSystemTransfer['collectionSystemTransferID'])
        else:
            self.OVDM.setIdle_collectionSystemTransfer(self.collectionSystemTransfer['collectionSystemTransferID'])

        debugPrint('Job Results:', json.dumps(resultsObj, indent=2))

        errPrint("Job:", current_job.handle + ",", self.collectionSystemTransfer['name'], "transfer completed at:", time.strftime("%D %T", time.gmtime()))
            
        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_results)

    
    def after_poll(self, any_activity):
        self.stop = False
        if self.quit:
            errPrint("Quitting")
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


def task_runCollectionSystemTransfer(worker, job):

    time.sleep(randint(0,2))
    
    job_results = {'parts':[], 'files':{'new':[],'updated':[], 'exclude':[]}}

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    collectionSystemDestDir = ""

    if worker.collectionSystemTransfer['cruiseOrLowering'] == "1":
      collectionSystemDestDir = os.path.join(cruiseDir, worker.shipboardDataWarehouseConfig['loweringDataBaseDir'], worker.loweringID, build_destDir(worker).rstrip('/'))
    else:
      collectionSystemDestDir = os.path.join(cruiseDir, build_destDir(worker).rstrip('/'))

    collectionSystemSourceDir = build_sourceDir(worker).rstrip('/')

    if worker.collectionSystemTransfer['status'] != "1": #not running
        debugPrint("Transfer is not already in-progress")
        job_results['parts'].append({"partName": "Transfer In-Progress", "result": "Pass"})
    else:
        debugPrint("Transfer is already in-progress")
        job_results['parts'].append({"partName": "Transfer In-Progress", "result": "Fail", "reason": "Transfer is already in-progress"})
        return json.dumps(job_results)
        
    if worker.collectionSystemTransfer['enable'] == "1" and worker.systemStatus == "On":
        debugPrint("Transfer Enabled")
        job_results['parts'].append({"partName": "Transfer Enabled", "result": "Pass"})
    else:
        debugPrint("Transfer Disabled")
        return json.dumps(job_results)
    
    #debugPrint("Setting transfer status to 'Running'")
    worker.OVDM.setRunning_collectionSystemTransfer(worker.collectionSystemTransfer['collectionSystemTransferID'], os.getpid(), job.handle)
        
    debugPrint("Testing connection")
    worker.send_job_status(job, 1, 10)

    gm_client = gearman.GearmanClient([worker.OVDM.getGearmanServer()])

    gmData = {}
    gmData['collectionSystemTransfer'] = worker.collectionSystemTransfer
    gmData['cruiseID'] = worker.cruiseID
    
    completed_job_request = gm_client.submit_job("testCollectionSystemTransfer", json.dumps(gmData))
    resultsObj = json.loads(completed_job_request.result)
    
    debugPrint('Connection Test Results:', json.dumps(resultsObj, indent=2))

    if resultsObj['parts'][-1]['result'] == "Pass": # Final Verdict
        debugPrint("Connection Test: Passed")
        job_results['parts'].append({"partName": "Connection Test", "result": "Pass"})
    else:
        debugPrint("Connection Test: Failed")
        job_results['parts'].append({"partName": "Connection Test", "result": "Fail", "reason": resultsObj['parts'][-1]['reason']})
        return json.dumps(job_results)

    worker.send_job_status(job, 2, 10)
        
    debugPrint("Start Transfer")
    if worker.collectionSystemTransfer['transferType'] == "1": # Local Directory
        output_results = transfer_localSourceDir(worker, job)
    elif  worker.collectionSystemTransfer['transferType'] == "2": # Rsync Server
        output_results = transfer_rsyncSourceDir(worker, job)
    elif  worker.collectionSystemTransfer['transferType'] == "3": # SMB Server
        output_results = transfer_smbSourceDir(worker, job)
    elif  worker.collectionSystemTransfer['transferType'] == "4": # SSH Server
        output_results = transfer_sshSourceDir(worker, job)

    if not output_results['verdict']:
        job_results['parts'].append({"partName": "Transfer Files", "result": "Fail", "reason": output_results['reason']})
        return job_results

    debugPrint("Transfer Complete")
    job_results['files'] = output_results['files']
    job_results['parts'].append({"partName": "Transfer Files", "result": "Pass"})

    if len(job_results['files']['new']) > 0:
        debugPrint(len(job_results['files']['new']), 'file(s) added')
    if len(job_results['files']['updated']) > 0:
        debugPrint(len(job_results['files']['updated']), 'file(s) updated')
    if len(job_results['files']['exclude']) > 0:
        debugPrint(len(job_results['files']['exclude']), 'misnamed file(s) encounted')


    worker.send_job_status(job, 9, 10)
    
    if job_results['files']['new'] or job_results['files']['updated']:

        debugPrint("Setting file permissions")

        permission_status = True
        #for filename in job_results['files']['new']:

        output_results = setOwnerGroupPermissions(worker, collectionSystemDestDir)

        if not output_results['verdict']:
            errPrint("Error Setting file/directory ownership")
            job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Fail", "reason": output_results['reason']})
    
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Pass"})

        debugPrint("Building Logfiles")

        logfileName = worker.collectionSystemTransfer['name'] + '_' + worker.transferStartDate + '.log'
        #print logfileName

        logContents = {'files':{'new':[], 'updated':[]}}
        logContents['files']['new'] = job_results['files']['new']
        logContents['files']['updated'] = job_results['files']['updated']

        #debugPrint('logContents',logContents)

        output_results = writeLogFile(worker, logfileName, logContents['files'])

        if output_results['verdict']:
            job_results['parts'].append({"partName": "Write transfer logfile", "result": "Pass"})
        else:
            job_results['parts'].append({"partName": "Write transfer logfile", "result": "Fail", "reason": output_results['reason']})
            return job_results
            
    #if job_results['files']['exclude']:
    # Format exclude files for transfer log
    job_results['files']['exclude'] = [worker.collectionSystemTransfer['destDir'].rstrip('/') + '/' + filename for filename in job_results['files']['exclude']]
    
    logfileName = worker.collectionSystemTransfer['name'] + '_Exclude.log'
    #print filenameErrorLogfileName
    logContents = {'files':{'exclude':[]}}
    logContents['files']['exclude'] = job_results['files']['exclude']

    output_results =  writeLogFile(worker, logfileName, logContents['files'])

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Write exclude logfile", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Write exclude logfile", "result": "Fail", "reason": output_results['reason']})
        return job_results

    worker.send_job_status(job, 10, 10)
    
    time.sleep(2)

    return json.dumps(job_results)



# -------------------------------------------------------------------------------------
# Main function of the script should it be run as a stand-alone utility.
# -------------------------------------------------------------------------------------
def main(argv):

    parser = argparse.ArgumentParser(description='Handle collection system transfer related tasks')
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

    new_worker.set_client_id('runCollectionSystemTransfer.py')

    debugPrint('Registering worker tasks...')
    debugPrint('   Task:', 'runCollectionSystemTransfer')
    new_worker.register_task("runCollectionSystemTransfer", task_runCollectionSystemTransfer)

    debugPrint('Waiting for jobs...')
    new_worker.work()

# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])
