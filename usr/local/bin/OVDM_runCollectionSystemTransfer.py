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
#      VERSION:  2.2
#      CREATED:  2015-01-01
#     REVISION:  2017-01-24
#
# LICENSE INFO: Open Vessel Data Management (OpenVDMv2)
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

    staleness = int(worker.collectionSystemTransfer['staleness']) * 60 #5 Mintues
    threshold_time = time.time() - staleness
    cruiseStart_time = calendar.timegm(time.strptime(worker.cruiseStartDate, "%Y/%m/%d %H:%M"))
    cruiseEnd_time = calendar.timegm(time.strptime(worker.cruiseEndDate, "%Y/%m/%d %H:%M"))

    debugPrint("Start:", cruiseStart_time)
    debugPrint("End:", cruiseEnd_time)
    debugPrint("Threshold:", threshold_time)
    
    filters = build_filters(worker)
    
    for root, dirnames, filenames in os.walk(sourceDir):
        for filename in filenames:
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
                                returnFiles['exclude'].append(os.path.join(root, filename))
                                exclude = True
                                break
                        if not exclude:
                            if os.path.islink(os.path.join(root, filename)):
                                continue
                            #debugPrint('Filename:', os.path.join(root, filename))
                            file_mod_time = os.stat(os.path.join(root, filename)).st_mtime
                            #debugPrint("file_mod_time:",file_mod_time)
                            if file_mod_time > cruiseStart_time and file_mod_time < cruiseEnd_time:
                                debugPrint(filename, "included")
                                returnFiles['include'].append(os.path.join(root, filename))
                                returnFiles['filesize'].append(os.stat(os.path.join(root, filename)).st_size)
                            else:
                                debugPrint(filename, "skipped for time reasons")

                            include = True

                if not include:
                    debugPrint(filename, "excluded")
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

        return False    

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

    return returnFiles


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
    returnFilters['excludeFilter'] = returnFilters['excludeFilter'].replace('{cruiseID}', worker.cruiseID)
    returnFilters['ignoreFilter'] =  returnFilters['ignoreFilter'].replace('{cruiseID}', worker.cruiseID)
    
    #print json.dumps(returnFilters, indent=2)
    return returnFilters


def build_destDir(worker):
    
    returnDestDir = worker.collectionSystemTransfer['destDir'].replace('{cruiseID}', worker.cruiseID)

    return returnDestDir


def build_sourceDir(worker):
    
    returnSourceDir = worker.collectionSystemTransfer['sourceDir'].replace('{cruiseID}', worker.cruiseID)

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

    #debugPrint(path)

    uid = pwd.getpwnam(warehouseUser).pw_uid
    gid = grp.getgrnam(warehouseUser).gr_gid
    # Set the file permission and ownership for the current directory

    
    if os.path.isfile(path):
        try:
            debugPrint("Setting ownership for", path, "to", warehouseUser + ":" + warehouseUser)
            os.chown(path, uid, gid)
            os.chmod(path, 0644)
        except OSError:
            errPrint("Unable to set file permissions for", path)
            return False
    elif os.path.isdir(path):
        os.chown(path, uid, gid)
        os.chmod(path, 0755)
        for item in os.listdir(path):
            itempath = os.path.join(path, item)
            if os.path.isdir(itempath):
                try:
                    if not setOwnerGroupPermissions(worker, itempath):
                        return False
                except OSError:
                    return False
            elif os.path.isfile(itempath):
                try:
                    debugPrint("Setting ownership for", itempath, "to", warehouseUser + ":" + warehouseUser)
                    os.chown(itempath, uid, gid)
                    os.chmod(itempath, 0644)
                except OSError:
                    errPrint("Unable to set file permissions for", itempath)
                    return False
    else:
        errPrint("Unable to find directory or file:", path)
        return False

    return True


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
        return False

    finally:
        #print "Closing MD5 Summary MD5 file"
        Logfile.close()
        setOwnerGroupPermissions(worker, logfilePath)

    return True
    

def transfer_localSourceDir(worker, job):

    debugPrint("Transfer from Local Directory")
    
    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)

    destDir = os.path.join(cruiseDir, build_destDir(worker).rstrip('/'))    
    sourceDir = build_sourceDir(worker).rstrip('/')
    debugPrint("Source Dir:", sourceDir)
    debugPrint("Destinstation Dir:", destDir)

    debugPrint("Build file list")
    files = build_filelist(worker, sourceDir)
    debugPrint("Files:", json.dumps(files['include'], indent=2))

    fileIndex = 0
    fileCount = len(files['include'])
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncFileListPath = os.path.join(tmpdir, 'rsyncFileList.txt')
        
    localTransferFileList = files['include']
    localTransferFileList = [filename.replace(sourceDir, '', 1) for filename in localTransferFileList]

    try:
        rsyncFileListFile = open(rsyncFileListPath, 'w')
        rsyncFileListFile.write('\n'.join([str(file) for file in localTransferFileList]))

    except IOError:
        errPrint("Error Saving temporary rsync filelist file")
        rsyncFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)            
        return False

    finally:
        #debugPrint("Closing rsync filelist file")
        rsyncFileListFile.close()
    
    command = ['rsync', '-tri', '--files-from=' + rsyncFileListPath, sourceDir + '/', destDir]
    
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
    
    files['new'] = [os.path.join(worker.collectionSystemTransfer['destDir'].rstrip('/'),filename) for filename in files['new']]
    files['updated'] = [os.path.join(worker.collectionSystemTransfer['destDir'].rstrip('/'),filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)
    return files


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

    destDir = os.path.join(cruiseDir, build_destDir(worker).rstrip('/'))    
    sourceDir = os.path.join(mntPoint, build_sourceDir(worker).rstrip('/')).rstrip('/')
    debugPrint("Source Dir:", sourceDir)
    debugPrint("Destinstation Dir:", destDir)


    # Mount SMB Share
    debugPrint("Mounting SMB Share")
    if worker.collectionSystemTransfer['smbUser'] == 'guest':
        
        command = ['sudo', 'mount', '-t', 'cifs', worker.collectionSystemTransfer['smbServer'], mntPoint, '-o', 'ro'+ ',guest' + ',domain='+worker.collectionSystemTransfer['smbDomain']]
        
        s = ' '
        debugPrint(s.join(command))
    
        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()
        
    else:
        command = ['sudo', 'mount', '-t', 'cifs', worker.collectionSystemTransfer['smbServer'], mntPoint, '-o', 'ro'+ ',username='+worker.collectionSystemTransfer['smbUser']+',password='+worker.collectionSystemTransfer['smbPass']+',domain='+worker.collectionSystemTransfer['smbDomain']]
        
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
        subprocess.call(['sudo', 'umount', mntPoint])
        shutil.rmtree(tmpdir)
            
        return False

    finally:
        rsyncFileListFile.close()

    command = ['rsync', '-trim', '--files-from=' + rsyncFileListPath, sourceDir, destDir]

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
    
    files['new'] = [os.path.join(worker.collectionSystemTransfer['destDir'].rstrip('/'),filename) for filename in files['new']]
    files['updated'] = [os.path.join(worker.collectionSystemTransfer['destDir'].rstrip('/'),filename) for filename in files['updated']]

    # Cleanup
    debugPrint('Unmounting SMB Share')
    subprocess.call(['sudo', 'umount', mntPoint])
    shutil.rmtree(tmpdir)

    return files

def transfer_rsyncSourceDir(worker, job):

    debugPrint("Transfer from RSYNC Server")

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    destDir = os.path.join(cruiseDir, build_destDir(worker).rstrip('/'))
    sourceDir = '/' + build_sourceDir(worker).rstrip('/')
    
    debugPrint("Source Dir:", sourceDir)
    debugPrint("Destinstation Dir:", destDir)
    
    debugPrint("Build file list")
    files = build_rsyncFilelist(worker, sourceDir)
    
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

        return False    

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
            
        return False

    finally:
        rsyncFileListFile.close()
    
    command = ['rsync', '-ti', '--no-motd', '--files-from=' + rsyncFileListPath, '--password-file=' + rsyncPasswordFilePath, 'rsync://' + worker.collectionSystemTransfer['rsyncUser'] + '@' + worker.collectionSystemTransfer['rsyncServer'] + sourceDir, destDir]

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
    
    files['new'] = [os.path.join(worker.collectionSystemTransfer['destDir'].rstrip('/'),filename) for filename in files['new']]
    files['updated'] = [os.path.join(worker.collectionSystemTransfer['destDir'].rstrip('/'),filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return files


def transfer_sshSourceDir(worker, job):

    debugPrint("Transfer from SSH Server")

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    
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
            
        return False

    finally:
        sshFileListFile.close()
    
    #command = ['sshpass', '-p', worker.collectionSystemTransfer['sshPass'], 'rsync', '-ti', '--files-from=' + sshFileListPath, '-e', 'ssh -c arcfour', worker.collectionSystemTransfer['sshUser'] + '@' + worker.collectionSystemTransfer['sshServer'] + ':' + sourceDir, destDir]
    command = ['sshpass', '-p', worker.collectionSystemTransfer['sshPass'], 'rsync', '-ti', '--files-from=' + sshFileListPath, '-e', 'ssh', worker.collectionSystemTransfer['sshUser'] + '@' + worker.collectionSystemTransfer['sshServer'] + ':' + sourceDir, destDir]

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
    
    files['new'] = [os.path.join(worker.collectionSystemTransfer['destDir'].rstrip('/'),filename) for filename in files['new']]
    files['updated'] = [os.path.join(worker.collectionSystemTransfer['destDir'].rstrip('/'),filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return files


def transfer_nfsSourceDir(worker, job):

    debugPrint("Transfer from NFS Server")

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)

    tmpdir = tempfile.mkdtemp()
    mntPoint = os.path.join(tmpdir, 'mntpoint')
    os.mkdir(mntPoint, 0755)

    debugPrint("Mount NFS Server")
        
    command = ['sudo', 'mount', '-t', 'nfs', worker.collectionSystemTransfer['nfsServer'], mntPoint, '-o', 'ro'+ ',vers=2' + ',hard' + ',intr']

    s = ' '
    debugPrint('Mount Command:', s.join(command))

    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    proc.communicate()
        
    destDir = os.path.join(cruiseDir, build_destDir(worker).rstrip('/'))    
    sourceDir = os.path.join(mntPoint, build_sourceDir(worker).rstrip('/')).rstrip('/')
    debugPrint("Source Dir:", sourceDir)
    debugPrint("Destinstation Dir:", destDir)
    
    debugPrint("Build file list")
    files = build_filelist(worker, sourceDir)
    
    fileIndex = 0
    fileCount = len(files['include'])
    
    rsyncFileListPath = os.path.join(tmpdir, '/rsyncFileList.txt')
        
    try:
        rsyncFileListFile = open(rsyncFileListPath, 'w')
        rsyncFileListFile.write('\n'.join(files['include']))

    except IOError:
        errPrint("Error Saving temporary rsync filelist file")
        rsyncFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return False

    finally:
        rsyncFileListFile.close()
    
    command = ['rsync', '-trim', '--files-from=' + rsyncFileListPath, sourceDir, destDir]
    
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
    
    files['new'] = [os.path.join(worker.collectionSystemTransfer['destDir'].rstrip('/'),filename) for filename in files['new']]
    files['updated'] = [os.path.join(worker.collectionSystemTransfer['destDir'].rstrip('/'),filename) for filename in files['updated']]

    # Cleanup
    debugPrint('Unmounting NFS Share')
    subprocess.call(['sudo', 'umount', mntPoint])
    shutil.rmtree(tmpdir)

    return files



class OVDMGearmanWorker(gearman.GearmanWorker):
    
    def __init__(self):
        self.stop = False
        self.quit = False
        self.OVDM = openvdm.OpenVDM()
        self.cruiseID = ''
        self.transferStartDate = ''
        self.cruiseStartDate = ''
        self.cruiseEndDate = ''
        self.systemStatus = ''
        self.collectionSystemTransfer = {}
        self.shipboardDataWarehouseConfig = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])
    
    
    def on_job_execute(self, current_job):
        payloadObj = json.loads(current_job.data)
        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()
        self.collectionSystemTransfer = self.OVDM.getCollectionSystemTransfer(payloadObj['collectionSystemTransfer']['collectionSystemTransferID'])
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
                payloadObj['systemStatus']
            except KeyError:
                self.systemStatus = self.OVDM.getSystemStatus()
            else:
                self.systemStatus = payloadObj['systemStatus']

        if self.collectionSystemTransfer['useStartDate'] == "0":
            self.cruiseStartDate = "1970/01/01 00:00"
            self.cruiseEndDate = "9999/12/31 23:59"
        
        errPrint("Job:", current_job.handle + ",", self.collectionSystemTransfer['name'], "transfer started at:  ", time.strftime("%D %T", time.gmtime()))
        
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)

    
    def on_job_exception(self, current_job, exc_info):
        errPrint("Job:", current_job.handle + ",", self.collectionSystemTransfer['name'], "transfer failed at:   ", time.strftime("%D %T", time.gmtime()))
        
        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail"}]))
        self.OVDM.setError_collectionSystemTransfer(self.collectionSystemTransfer['collectionSystemTransferID'], 'Reason: Worker crashed')
        
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
                    for test in resultsObj['parts']:
                        if test['result'] == "Fail":
                            self.OVDM.setError_collectionSystemTransfer(self.collectionSystemTransfer['collectionSystemTransferID'], 'Reason: ' +  test['partName'])
                            break
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

    time.sleep(randint(0,5))
    
    job_results = {'parts':[], 'files':{'new':[],'updated':[], 'exclude':[]}}

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)

    collectionSystemDestDir = os.path.join(cruiseDir, build_destDir(worker).rstrip('/'))
    collectionSystemSourceDir = build_sourceDir(worker).rstrip('/')
    
    if worker.collectionSystemTransfer['status'] != "1": #not running
        debugPrint("Transfer is not already in-progress")
        job_results['parts'].append({"partName": "Transfer In-Progress", "result": "Pass"})
    else:
        debugPrint("Transfer is already in-progress")
        job_results['parts'].append({"partName": "Transfer In-Progress", "result": "Fail"})
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
        job_results['parts'].append({"partName": "Connection Test", "result": "Fail"})
        return json.dumps(job_results)

    worker.send_job_status(job, 2, 10)
        
    debugPrint("Start Transfer")
    if worker.collectionSystemTransfer['transferType'] == "1": # Local Directory
        job_results['files'] = transfer_localSourceDir(worker, job)
    elif  worker.collectionSystemTransfer['transferType'] == "2": # Rsync Server
        job_results['files'] = transfer_rsyncSourceDir(worker, job)
    elif  worker.collectionSystemTransfer['transferType'] == "3": # SMB Server
        job_results['files'] = transfer_smbSourceDir(worker, job)
    elif  worker.collectionSystemTransfer['transferType'] == "4": # SSH Server
        job_results['files'] = transfer_sshSourceDir(worker, job)
    elif  worker.collectionSystemTransfer['transferType'] == "5": # NFS Server
        job_results['files'] = transfer_nfsSourceDir(worker, job)

    debugPrint("Transfer Complete")
    if len(job_results['files']['new']) > 0:
        debugPrint(len(job_results['files']['new']), 'file(s) added')
    if len(job_results['files']['updated']) > 0:
        debugPrint(len(job_results['files']['updated']), 'file(s) updated')
    if len(job_results['files']['exclude']) > 0:
        debugPrint(len(job_results['files']['exclude']), 'misnamed file(s) encounted')

    job_results['parts'].append({"partName": "Transfer Files", "result": "Pass"})

    worker.send_job_status(job, 9, 10)
    
    if job_results['files']['new'] or job_results['files']['updated']:

        debugPrint("Setting file permissions")

        permission_status = True
        for filename in job_results['files']['new']:
            if not setOwnerGroupPermissions(worker, os.path.join(cruiseDir, filename)):
                errPrint("Error Setting file/directory ownership:", filename)
                permission_status = False
    
        for filename in job_results['files']['updated']:
            if not setOwnerGroupPermissions(worker, os.path.join(cruiseDir, filename)):
                errPrint("Error Setting file/directory ownership:", filename)
                permission_status = False

        if permission_status:
            job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Pass"})
        else:
            job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Fail"})

        debugPrint("Building Logfiles")

        logfileName = worker.collectionSystemTransfer['name'] + '_' + worker.transferStartDate + '.log'
        #print logfileName

        logContents = {'files':{'new':[], 'updated':[]}}
        logContents['files']['new'] = job_results['files']['new']
        logContents['files']['updated'] = job_results['files']['updated']

        #debugPrint('logContents',logContents)

        if writeLogFile(worker, logfileName, logContents['files']):
            job_results['parts'].append({"partName": "Write transfer logfile", "result": "Pass"})
        else:
            job_results['parts'].append({"partName": "Write transfer logfile", "result": "Fail"})
            return job_results
            
    #if job_results['files']['exclude']:
    # Format exclude files for transfer log
    job_results['files']['exclude'] = [worker.collectionSystemTransfer['destDir'].rstrip('/') + '/' + filename for filename in job_results['files']['exclude']]
    
    logfileName = worker.collectionSystemTransfer['name'] + '_Exclude.log'
    #print filenameErrorLogfileName
    logContents = {'files':{'exclude':[]}}
    logContents['files']['exclude'] = job_results['files']['exclude']

    if writeLogFile(worker, logfileName, logContents['files']):
        job_results['parts'].append({"partName": "Write exclude logfile", "result": "Pass"})
    else:
        job_results['parts'].append({"partName": "Write exclude logfile", "result": "Fail"})
        return job_results

    worker.send_job_status(job, 10, 10)
    
    time.sleep(5)

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
