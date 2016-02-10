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
#      VERSION:  2.1
#      CREATED:  2015-01-01
#     REVISION:  2016-02-03
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


def build_filelist(worker, sourceDir):

    returnFiles = {'include':[], 'exclude':[], 'new':[], 'updated':[]}
    threshold_time = time.time() - (int(worker.collectionSystemTransfer['staleness']) * 60) # 5 minutes
    cruiseStart_time = calendar.timegm(time.strptime(worker.cruiseStartDate, "%m/%d/%Y"))
    filters = build_filters(worker)
    
    for root, dirnames, filenames in os.walk(sourceDir):
        for filename in filenames:
            exclude = False
            ignore = False
            include = False
            for filt in filters['ignoreFilter'].split(','):
                #print filt
                if fnmatch.fnmatch(os.path.join(root, filename), filt):
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
                            #print 'Filename: ' + os.path.join(root, filename)
                            file_mod_time = os.stat(os.path.join(root, filename)).st_mtime
                            if file_mod_time > cruiseStart_time and file_mod_time < threshold_time:
                                returnFiles['include'].append(os.path.join(root, filename))
                            include = True
                            break
                if not include:
                    returnFiles['exclude'].append(os.path.join(root, filename))

    returnFiles['include'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['include']]
    returnFiles['exclude'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['exclude']]

    return returnFiles


def build_rsyncFilelist(worker, sourceDir):

    #print "Build file list"

    returnFiles = {'include':[], 'exclude':[], 'new':[], 'updated':[]}
    threshold_time = time.time() - (int(worker.collectionSystemTransfer['staleness']) * 60) # 5 minutes
    cruiseStart_time = calendar.timegm(time.strptime(worker.cruiseStartDate, "%m/%d/%Y"))
    filters = build_filters(worker)

    #print threshold_time
    rsyncFileList = ''
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncPasswordFilePath = tmpdir + '/passwordFile'

    try:
        #print "Open rsync password file"
        rsyncPasswordFile = open(rsyncPasswordFilePath, 'w')

        #print "Saving rsync password file"
        rsyncPasswordFile.write(worker.collectionSystemTransfer['rsyncPass'])

    except IOError:
        #print "Error Saving temporary rsync password file"
        returnVal.append({"testName": "Writing temporary rsync password file", "result": "Fail"})
        rsyncPasswordFile.close()

        # Cleanup
        shutil.rmtree(tmpdir)

        return returnFiles    

    finally:
        #print "Closing rsync password file"
        rsyncPasswordFile.close()
        os.chmod(rsyncPasswordFilePath, 0600)
        #returnVal.append({"testName": "Writing temporary rsync password file", "result": "Pass"})

    command = ['rsync', '-r', '--password-file=' + rsyncPasswordFilePath, '--no-motd', 'rsync://' + worker.collectionSystemTransfer['rsyncUser'] + '@' + worker.collectionSystemTransfer['rsyncServer'] + sourceDir]
    
    #s = ' '
    #print s.join(command)
    
    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = proc.communicate()
    rsyncFileList = out

    # Cleanup
    shutil.rmtree(tmpdir)
        
    #print "rsyncFileListOut: " + rsyncFileList
    
    threshold_time = time.time() - (int(worker.collectionSystemTransfer['staleness']) * 60) # 5 minutes
    epoch = datetime.datetime.strptime('1970/01/01 00:00:00', "%Y/%m/%d %H:%M:%S")
    
    for line in rsyncFileList.splitlines():
        #print line
        fileOrDir, size, mdate, mtime, name = line.split()
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
                            #print "file_mod_time_SECS: " + str(file_mod_time_SECS)
                            if file_mod_time_SECS > cruiseStart_time and file_mod_time_SECS < threshold_time:
                                #print "include"
                                returnFiles['include'].append(filename)
                            include = True
                            break
                if not include:
                    #print "exclude"
                    returnFiles['exclude'].append(filename)        

    returnFiles['include'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['include']]
    returnFiles['exclude'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['exclude']]

    #print 'DECODED returnFiles:', json.dumps(returnFiles, indent=2)  
    
    return returnFiles


def build_sshFilelist(worker, sourceDir):

    #print "Build file list"

    returnFiles = {'include':[], 'exclude':[], 'new':[], 'updated':[]}
    threshold_time = time.time() - (int(worker.collectionSystemTransfer['staleness']) * 60) # 5 minutes
    cruiseStart_time = calendar.timegm(time.strptime(worker.cruiseStartDate, "%m/%d/%Y"))
    filters = build_filters(worker)
    
    #print threshold_time
    rsyncFileList = ''
    
    command = ['sshpass', '-p', worker.collectionSystemTransfer['sshPass'], 'rsync', '-r', '-e', 'ssh -c arcfour', worker.collectionSystemTransfer['sshUser'] + '@' + worker.collectionSystemTransfer['sshServer'] + ':' + sourceDir + '/']
    
    #s = ' '
    #print s.join(command)
        
    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = proc.communicate()
    rsyncFileList = out
        
    #print "rsyncFileListOut: " + rsyncFileList
    
    threshold_time = time.time() - (int(worker.collectionSystemTransfer['staleness']) * 60) # 5 minutes
    epoch = datetime.datetime.strptime('1970/01/01 00:00:00', "%Y/%m/%d %H:%M:%S")
    
    for line in rsyncFileList.splitlines():
        #print line
        fileOrDir, size, mdate, mtime, name = line.split()
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
                            #print "file_mod_time_SECS: " + str(file_mod_time_SECS)
                            if file_mod_time_SECS > cruiseStart_time and file_mod_time_SECS < threshold_time:
                                #print "include"
                                returnFiles['include'].append(filename)
                            include = True
                            break
                if not include:
                    #print "exclude"
                    returnFiles['exclude'].append(filename)        

    returnFiles['include'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['include']]
    returnFiles['exclude'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['exclude']]

    #print 'DECODED returnFiles:', json.dumps(returnFiles, indent=2)  
    
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

    requiredExtraDirectories = worker.OVDM.getRequiredExtraDirectories()

    for directory in requiredExtraDirectories:
        if directory['name'] == 'Transfer Logs':
            return worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'] + '/' + worker.cruiseID + '/' + directory['destDir']
            break
    
    return ''


def setDirectoryOwnerGroupPermissions(path, uid, gid):
    # Set the file permission and ownership for the current directory
    try:
        os.chown(path, uid, gid)
        os.chmod(path, 0755)
    except OSError:
        print "Unable to set file permissions for " + path
        return False
    
    for item in os.listdir(path):
        itempath = os.path.join(path, item)
        if os.path.isdir(itempath):
            try:
                setDirectoryOwnerGroupPermissions(itempath, uid, gid)
            except OSError:
                return False
        elif os.path.isfile(itempath):
            try:
                os.chown(itempath, uid, gid)
                os.chmod(itempath, 0644)
            except OSError:
                return False
    return True


def writeLogFile(logfileName, warehouseUser, files):
    
    try:
        #print "Open MD5 Summary MD5 file"
        Logfile = open(logfileName, 'w')

        #print "Saving MD5 Summary MD5 file"
        Logfile.write(json.dumps(files))

    except IOError:
        print "Error Saving transfer logfile"
        return False

    finally:
        #print "Closing MD5 Summary MD5 file"
        Logfile.close()
        os.chown(logfileName, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)

    return True
    

def transfer_localSourceDir(worker, job):

    #print "Transfer from Local Directory"
    
    staleness = worker.collectionSystemTransfer['staleness']
    cruiseStartDate = worker.cruiseStartDate
    
    destDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']+'/'+worker.cruiseID+'/'+worker.collectionSystemTransfer['destDir'].rstrip('/')
    sourceDir = worker.collectionSystemTransfer['sourceDir'].rstrip('/')
    
    #print "Build file list"
    files = build_filelist(worker, sourceDir)

    #print "Build destination directories"
    #build_destDirectories(destDir, files['include'])
    
    count = 1
    fileCount = len(files['include'])
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncFileListPath = tmpdir + '/rsyncFileList.txt'
        
    try:
        #print "Open rsync password file"
        rsyncFileListFile = open(rsyncFileListPath, 'w')

        #print "Saving rsync password file"
        localTransferFileList = files['include']
        localTransferFileList = [filename.replace(sourceDir, '', 1) for filename in localTransferFileList]

        #print '\n'.join([str(x) for x in localTransferFileList])
        rsyncFileListFile.write('\n'.join([str(x) for x in localTransferFileList]))

    except IOError:
        print "Error Saving temporary rsync filelist file"
        #returnVal.append({"testName": "Writing temporary rsync password file", "result": "Fail"})
        rsyncFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return files    

    finally:
        #print "Closing rsync filelist file"
        rsyncFileListFile.close()
        #returnVal.append({"testName": "Writing temporary rsync password file", "result": "Pass"})
    
    command = ['rsync', '-tri', '--files-from=' + rsyncFileListPath, sourceDir + '/', destDir]
    
    #s = ' '
    #print s.join(command)
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #print(line) # yield line
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ')[1].rstrip('\n')
            files['new'].append(filename)
            #os.chown(destDir + '/' + filename, pwd.getpwnam(data['shipboardDataWarehouse']['shipboardDataWarehouseUsername']).pw_uid, grp.getgrnam(data['shipboardDataWarehouse']['shipboardDataWarehouseUsername']).gr_gid)
            worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
            count += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ')[1].rstrip('\n')
            files['updated'].append(filename)
            #os.chown(destDir + '/' + filename, pwd.getpwnam(data['shipboardDataWarehouse']['shipboardDataWarehouseUsername']).pw_uid, grp.getgrnam(data['shipboardDataWarehouse']['shipboardDataWarehouseUsername']).gr_gid)
            worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
            count += 1
            
        if worker.stop:
            print "Stopping"
            break
    
    # Cleanup
    shutil.rmtree(tmpdir)    
    return files


def transfer_smbSourceDir(worker, job):

#    print 'DECODED Data:', json.dumps(data, indent=2)
    staleness = worker.collectionSystemTransfer['staleness']
    cruiseStartDate = worker.cruiseStartDate
    filters = build_filters(worker)

    # Create temp directory
    #print "Create Temp Directory"
    tmpdir = tempfile.mkdtemp()
 
    # Create mountpoint
    #print "Create Mountpoint"
    mntPoint = tmpdir + '/mntpoint'
    os.mkdir(mntPoint, 0755)

    # Mount SMB Share
    #print "Mount SMB Share"
    if worker.collectionSystemTransfer['smbUser'] == 'guest':
        
        command = ['sudo', 'mount', '-t', 'cifs', worker.collectionSystemTransfer['smbServer'], mntPoint, '-o', 'ro'+ ',guest' + ',domain='+worker.collectionSystemTransfer['smbDomain']]
        
        #s = ' '
        #print s.join(command)
    
        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()
        
    else:
        command = ['sudo', 'mount', '-t', 'cifs', worker.collectionSystemTransfer['smbServer'], mntPoint, '-o', 'ro'+ ',username='+worker.collectionSystemTransfer['smbUser']+',password='+worker.collectionSystemTransfer['smbPass']+',domain='+worker.collectionSystemTransfer['smbDomain']]
        
        #s = ' '
        #print s.join(command)
    
        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

    destDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'] + '/' + worker.cruiseID + '/' + build_destDir(worker).rstrip('/')
    sourceDir = mntPoint + '/' + build_sourceDir(worker)
    sourceDir = sourceDir.rstrip('/')
    
    #print "Source Dir: " + sourceDir
    #print "Destinstation Dir: " + destDir
    
    #print "Build file list"
    files = build_filelist(worker, sourceDir)
    
    #print "File List:"
    #print json.dumps(files['include'])
    
    count = 1
    fileCount = len(files['include'])
    
    rsyncFileListPath = tmpdir + '/rsyncFileList.txt'
        
    try:
        #print "Open rsync filelist file"
        rsyncFileListFile = open(rsyncFileListPath, 'w')

        #print "Saving rsync filelist file"
        #print '\n'.join(files['include'])
        rsyncFileListFile.write('\n'.join(files['include']))

    except IOError:
        print "Error Saving temporary rsync filelist file"
        #returnVal.append({"testName": "Writing temporary rsync password file", "result": "Fail"})
        rsyncFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return files    

    finally:
        #print "Closing rsync filelist file"
        rsyncFileListFile.close()
        #returnVal.append({"testName": "Writing rsync filelist file", "result": "Pass"})
    
    command = ['rsync', '-trim', '--files-from=' + rsyncFileListPath, sourceDir, destDir]
    #print command
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #print(line) # yield line
        if line.startswith( '>f+++++++++' ):
            files['new'].append(line.split(' ')[1].rstrip('\n'))
        elif line.startswith( '>f.' ):
            files['updated'].append(line.split(' ')[1].rstrip('\n'))
        worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
        count += 1
            
        if worker.stop:
            print "Stopping"
            break
    
    #print "Unmount SMB Share"
    subprocess.call(['sudo', 'umount', mntPoint])
    
    #print "Cleanup"
    shutil.rmtree(tmpdir)

    #print 'DECODED Files:', json.dumps(files, indent=2)
    return files


def transfer_rsyncSourceDir(worker, job):

    #print "Transfer from RSYNC Server"
#    print 'DECODED Data:', json.dumps(data, indent=2)

    destDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'] + '/' + worker.cruiseID + '/' + build_destDir(worker).rstrip('/')
    sourceDir = '/' + build_sourceDir(worker).rstrip('/')
    
    #print destDir
    #print sourceDir
    
    #print "Build file list"    
    files = build_rsyncFilelist(worker, sourceDir)
    
    #print json.dumps(files)
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    count = 1
    fileCount = len(files['include'])
    
    rsyncPasswordFilePath = tmpdir + '/passwordFile'

    try:
        #print "Open temporary rsync password file"
        rsyncPasswordFile = open(rsyncPasswordFilePath, 'w')

        #print "Saving temporary rsync password file"
        rsyncPasswordFile.write(worker.collectionSystemTransfer['rsyncPass'])

    except IOError:
        #print "Error Saving temporary rsync password file"
        returnVal.append({"testName": "Writing temporary rsync password file", "result": "Fail"})
        rsyncPasswordFile.close()

        # Cleanup
        shutil.rmtree(tmpdir)

        return returnVal    

    finally:
        #print "Closing temporary rsync password file"
        rsyncPasswordFile.close()
        os.chmod(rsyncPasswordFilePath, 0600)
        #returnVal.append({"testName": "Writing temporary rsync password file", "result": "Pass"})

    rsyncFileListPath = tmpdir + '/rsyncFileList.txt'
        
    try:
        #print "Open rsync password file"
        rsyncFileListFile = open(rsyncFileListPath, 'w')

        #print "Saving rsync password file"
        #print '\n'.join(files['include'])
        rsyncFileListFile.write('\n'.join(files['include']))

    except IOError:
        print "Error Saving temporary rsync filelist file"
        returnVal.append({"testName": "Writing temporary rsync filelist file", "result": "Fail"})
        rsyncFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return files    

    finally:
        #print "Closing rsync filelist file"
        rsyncFileListFile.close()
        #returnVal.append({"testName": "Writing temporary rsync filelist file", "result": "Pass"})
    
    
    command = ['rsync', '-ti', '--no-motd', '--files-from=' + rsyncFileListPath, '--password-file=' + rsyncPasswordFilePath, 'rsync://' + worker.collectionSystemTransfer['rsyncUser'] + '@' + worker.collectionSystemTransfer['rsyncServer'] + sourceDir, destDir]
        
    #print command
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #print(line) # yield line
        if line.startswith( '>f+++++++++' ):
            files['new'].append(line.split(' ')[1].rstrip('\n'))
        elif line.startswith( '>f.' ):
            files['updated'].append(line.split(' ')[1].rstrip('\n'))
        worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
        count += 1
            
        if worker.stop:
            print "Stopping"
            break
    
    # Cleanup
    shutil.rmtree(tmpdir)    
    return files


def transfer_sshSourceDir(worker, job):

    #print "Transfer from SSH Server"
    destDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'] + '/' + worker.cruiseID + '/' + build_destDir(worker).rstrip('/')
    sourceDir = build_sourceDir(worker).rstrip('/')
    
    #print destDir
    #print sourceDir   
    
    files = build_sshFilelist(worker, sourceDir)
    
    #print json.dumps(files)

    count = 1
    fileCount = len(files['include'])
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    sshFileListPath = tmpdir + '/sshFileList.txt'
        
    try:
        #print "Open rsync password file"
        sshFileListFile = open(sshFileListPath, 'w')

        #print "Saving ssh password file"
        #print '\n'.join(files['include'])
        sshFileListFile.write('\n'.join(files['include']))

    except IOError:
        print "Error Saving temporary ssh filelist file"
        returnVal.append({"testName": "Writing temporary ssh filelist", "result": "Fail"})
        sshFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return files    

    finally:
        #print "Closing ssh filelist file"
        sshFileListFile.close()
        #returnVal.append({"testName": "Writing temporary ssh filelist file", "result": "Pass"})
    
    
    command = ['sshpass', '-p', worker.collectionSystemTransfer['sshPass'], 'rsync', '-ti', '--files-from=' + sshFileListPath, '-e', 'ssh -c arcfour', worker.collectionSystemTransfer['sshUser'] + '@' + worker.collectionSystemTransfer['sshServer'] + ':' + sourceDir, destDir]

    #s = ' '
    #print s.join(command)
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #print(line) # yield line
        if line.startswith( '>f+++++++++' ):
            files['new'].append(line.split(' ')[1].rstrip('\n'))
        elif line.startswith( '>f.' ):
            files['updated'].append(line.split(' ')[1].rstrip('\n'))
        worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
        count += 1
            
        if worker.stop:
            print "Stopping"
            break
    
    # Cleanup
    shutil.rmtree(tmpdir)    
    return files


def transfer_nfsSourceDir(worker, job):

    #print 'DECODED Data:', json.dumps(job.data, indent=2)
    staleness = worker.collectionSystemTransfer['staleness']
    cruiseStartDate = worker.cruiseStartDate
    filters = build_filters(worker)

    # Create temp directory
    #print "Create Temp Directory"
    tmpdir = tempfile.mkdtemp()
 
    # Create mountpoint
    #print "Create Mountpoint"
    mntPoint = tmpdir + '/mntpoint'
    os.mkdir(mntPoint, 0755)

    # Mount NFS Server
    #print "Mount NFS Server"
        
    command = ['sudo', 'mount', '-t', 'nfs', worker.collectionSystemTransfer['nfsServer'], mntPoint, '-o', 'ro'+ ',vers=2' + ',hard' + ',intr']

    #s = ' '
    #print s.join(command)

    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    proc.communicate()
        
    destDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'] + '/' + worker.cruiseID + '/' + build_destDir(worker).rstrip('/')
    sourceDir = mntPoint + '/' + build_sourceDir(worker)
    sourceDir = sourceDir.rstrip('/')
    
    #print "Source Dir: " + sourceDir
    #print "Destinstation Dir: " + destDir
    
    #print "Build file list"
    files = build_filelist(worker, sourceDir)
    
    #print "Raw File List:"
    #print json.dumps(files['include'])
    
    count = 1
    fileCount = len(files['include'])
    
    rsyncFileListPath = tmpdir + '/rsyncFileList.txt'
        
    #print "Proc File List:"
    try:
        #print "Open rsync filelist file"
        rsyncFileListFile = open(rsyncFileListPath, 'w')

        #print "Saving rsync filelist file"
        #print '\n'.join(files['include'])
        rsyncFileListFile.write('\n'.join(files['include']))

    except IOError:
        print "Error Saving temporary rsync filelist file"
        #returnVal.append({"testName": "Writing temporary rsync password file", "result": "Fail"})
        rsyncFileListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return files    

    finally:
        #print "Closing rsync filelist file"
        rsyncFileListFile.close()
        #returnVal.append({"testName": "Writing rsync filelist file", "result": "Pass"})
    
    command = ['rsync', '-trim', '--files-from=' + rsyncFileListPath, sourceDir, destDir]
    
    #s = ' '
    #print s.join(command)
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #print(line) # yield line
        if line.startswith( '>f+++++++++' ):
            files['new'].append(line.split(' ')[1].rstrip('\n'))
        elif line.startswith( '>f.' ):
            files['updated'].append(line.split(' ')[1].rstrip('\n'))
        worker.send_job_status(job, int(round(20 + (70*count/fileCount),0)), 100)
        count += 1
            
        if worker.stop:
            print "Stopping"
            break
    
    #print "Unmount NFS Server"
    subprocess.call(['sudo', 'umount', mntPoint])
    
    #print "Cleanup"
    shutil.rmtree(tmpdir)

    #print 'DECODED Files:', json.dumps(files, indent=2)
    return files


class OVDMGearmanWorker(gearman.GearmanWorker):
    
    def __init__(self):
        self.stop = False
        self.quit = False
        self.OVDM = openvdm.OpenVDM()
        self.cruiseID = ''
        self.cruiseStartDate = ''
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
        self.cruiseStartDate = self.OVDM.getCruiseStartDate()
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
                payloadObj['systemStatus']
            except KeyError:
                self.systemStatus = self.OVDM.getSystemStatus()
            else:
                self.systemStatus = payloadObj['systemStatus']
        
        print "Job: " + current_job.handle + ", " + self.collectionSystemTransfer['name'] + " transfer started at:   " + time.strftime("%D %T", time.gmtime())
        
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)

    
    def on_job_exception(self, current_job, exc_info):
        print "Job: " + current_job.handle + ", " + self.collectionSystemTransfer['name'] + " transfer failed at:    " + time.strftime("%D %T", time.gmtime())
        
        self.send_job_data(current_job, json.dumps([{"partName": "Unknown Part of Transfer", "result": "Fail"}]))
        self.OVDM.setError_collectionSystemTransfer(self.collectionSystemTransfer['collectionSystemTransferID'], "Unknown Part of Transfer Failed")
        
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)

    
    def on_job_complete(self, current_job, job_result):
        resultObj = json.loads(job_result)
        
        if resultObj['files']['new'] or resultObj['files']['updated']:

            jobData = {'cruiseID':'', 'collectionSystemTransferID':'', 'files':{}}
            jobData['cruiseID'] = self.cruiseID
            jobData['collectionSystemTransferID'] = self.collectionSystemTransfer['collectionSystemTransferID']

            destDir = build_destDir(self).rstrip('/')
            jobData['files'] = resultObj['files']
            jobData['files']['new'] = [destDir + '/' + filename for filename in jobData['files']['new']]
            jobData['files']['updated'] = [destDir + '/' + filename for filename in jobData['files']['updated']]
                
            gm_client = gearman.GearmanClient([self.OVDM.getGearmanServer()])
            
            for task in self.OVDM.getTasksForHook('runCollectionSystemTransfer'):
                #print task
                submitted_job_request = gm_client.submit_job(task, json.dumps(jobData), background=True)
        
        # If the last part of the results failed
        if len(resultObj['parts']) > 0:
            if resultObj['parts'][-1]['result'] == "Fail": # Final Verdict
                #print "...but there was an error:"
                print json.dumps(resultObj['parts'])
                self.OVDM.setError_collectionSystemTransfer(self.collectionSystemTransfer['collectionSystemTransferID'])
            else:
                self.OVDM.setIdle_collectionSystemTransfer(self.collectionSystemTransfer['collectionSystemTransferID'])
        else:
            self.OVDM.setIdle_collectionSystemTransfer(self.collectionSystemTransfer['collectionSystemTransferID'])

        print "Job: " + current_job.handle + ", " + self.collectionSystemTransfer['name'] + " transfer completed at: " + time.strftime("%D %T", time.gmtime())
            
        return super(OVDMGearmanWorker, self).send_job_complete(current_job, job_result)

    
    def after_poll(self, any_activity):
        self.stop = False
        if self.quit:
            print "Quitting"
            self.shutdown()
        return True
    
    
    def stopTransfer(self):
        self.stop = True

        
    def quitWorker(self):
        self.stop = True
        self.quit = True


def task_runCollectionSystemTransfer(worker, job):

    time.sleep(randint(0,5))
    
    job_results = {'parts':[], 'files':{'new':[],'updated':[], 'exclude':[]}, 'startDate':time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())}

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseID = worker.cruiseID
    warehouseUser = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']  
    collectionSystemDestDir = build_destDir(worker).rstrip('/')
    collectionSystemSourceDir = build_sourceDir(worker).rstrip('/')
    
    #print "Is transfer enabled?"
    if worker.collectionSystemTransfer['enable'] == "1" and worker.systemStatus == "On":
        #print "Transfer Enabled"
        job_results['parts'].append({"partName": "Transfer Enabled", "result": "Pass"})
    else:
        #print "Transfer Disabled"
        #print "Stopping"
        #job_results['parts'].append({"partName": "Transfer Enabled", "result": "Fail"})
        return json.dumps(job_results)
    
    #print "Is transfer for this collection system already running?"
    if worker.collectionSystemTransfer['status'] != "1": #not running
        #print "Transfer is not already in-progress"
        job_results['parts'].append({"partName": "Transfer In-Progress", "result": "Pass"})
    else:
        #print "Transfer is already in-progress"
        #job_results['parts'].append({"partName": "Transfer In-Progress", "result": "Fail"})
        #print "Stopping"
        return json.dumps(job_results)
        
    #print "Set transfer status to 'Running'"
    worker.OVDM.setRunning_collectionSystemTransfer(worker.collectionSystemTransfer['collectionSystemTransferID'], os.getpid(), job.handle)
        
    #print "Testing configuration"
    worker.send_job_status(job, 1, 10)

    gm_client = gearman.GearmanClient([worker.OVDM.getGearmanServer()])

    gmData = {}
    gmData['collectionSystemTransfer'] = worker.collectionSystemTransfer
    #gmData['collectionSystemTransfer']['status'] = "1"
    gmData['cruiseID'] = worker.cruiseID
    
    completed_job_request = gm_client.submit_job("testCollectionSystemTransfer", json.dumps(gmData))
    resultsObj = json.loads(completed_job_request.result)
    #print 'DECODED Results:', json.dumps(resultsObj, indent=2)

    if resultsObj[-1]['result'] == "Pass": # Final Verdict
        #print "Connection Test: Passed"
        job_results['parts'].append({"partName": "Connection Test", "result": "Pass"})
    else:
        print "Connection Test: Failed"
        #print "Stopping"
        job_results['parts'].append({"partName": "Connection Test", "result": "Fail"})
        #print json.dumps(job_results, indent=2)
        return json.dumps(job_results)

    worker.send_job_status(job, 2, 10)
    
    if worker.collectionSystemTransfer['useStartDate'] == "0":
        worker.cruiseStartDate = "01/01/1970"    
    
    #print "Transfer Data"
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

    #print "Transfer Complete"
    worker.send_job_status(job, 9, 10)
    
    if(setDirectoryOwnerGroupPermissions(baseDir + '/' + cruiseID + '/' +  collectionSystemDestDir, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)):
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Pass"})
    else:
        print "Error Setting file/directory ownership"
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Fail"})
    
    warehouseTransferLogDir = build_logfileDirPath(worker)
    #print warehouseTransferLogDir   

    if job_results['files']['new'] or job_results['files']['updated']:
    
        #print "Send transfer log"
        if os.path.isdir(warehouseTransferLogDir):
    
            logfileName = warehouseTransferLogDir + '/' + worker.collectionSystemTransfer['name'] + '_' + job_results['startDate'] + '.log'
            #print logfileName

            logOutput = {'files':{'new':[], 'updated':[]}}
            logOutput['files']['new'] = job_results['files']['new']
            logOutput['files']['updated'] = job_results['files']['updated']
            
            #print json.dumps(logOutput);
            
            if writeLogFile(logfileName, warehouseUser, logOutput['files']):
                job_results['parts'].append({"partName": "Write logfile", "result": "Pass"})
            else:
                job_results['parts'].append({"partName": "Write logfile", "result": "Fail"})
                
        else:
            job_results['parts'].append({"partName": "Logfile directory", "result": "Fail"})
    
    #print json.dumps(job_results['files']['exclude'], indent=2)
    if job_results['files']['exclude']:
        # Format exclude files for transfer log
        job_results['files']['exclude'] = [worker.collectionSystemTransfer['destDir'].rstrip('/') + '/' + filename for filename in job_results['files']['exclude']]
        
        #print "Send filename error log"
        if os.path.isdir(warehouseTransferLogDir):

            filenameErrorLogfileName = warehouseTransferLogDir + '/' + worker.collectionSystemTransfer['name'] + '_Exclude.log'
            #print filenameErrorLogfileName
            filenameErrorlogOutput = {'files':{'exclude':[]}}
            filenameErrorlogOutput['files']['exclude'] = job_results['files']['exclude']
            if writeLogFile(filenameErrorLogfileName, warehouseUser, filenameErrorlogOutput['files']):
                job_results['parts'].append({"partName": "Write filename error logfile", "result": "Pass"})
            else:
                job_results['parts'].append({"partName": "Write filename error logfile", "result": "Fail"})

        else:
            job_results['parts'].append({"partName": "Logfile directory", "result": "Fail"})

    worker.send_job_status(job, 10, 10)
    
    time.sleep(5)

    return json.dumps(job_results)


global ovdmWorker
ovdmWorker = OVDMGearmanWorker()

def sigquit_handler(_signo, _stack_frame):
    print "QUIT Signal Received"
    ovdmWorker.stopTransfer()
    
    
def sigint_handler(_signo, _stack_frame):
    print "INT Signal Received"
    ovdmWorker.quitWorker()
    
    
signal.signal(signal.SIGQUIT, sigquit_handler)
signal.signal(signal.SIGINT, sigint_handler)

ovdmWorker.set_client_id('runCollectionSystemTransfer.py')
ovdmWorker.register_task("runCollectionSystemTransfer", task_runCollectionSystemTransfer)

ovdmWorker.work()
