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
#      VERSION:  2.0
#      CREATED:  2015-01-01
#     REVISION:  2015-07-18
#
# LICENSE INFO: Open Vessel Data Management (OpenVDM) Copyright (C) 2015  Webb Pinner
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
import requests
import time
import calendar
import datetime
import fnmatch
import subprocess
import signal
import pwd
import grp
from random import randint

def build_filelist(sourceDir, filters, stalness, cruiseStartDate):

    #print "Filter sourceDir: " + sourceDir
    #print "Build file list"
    #find . -path ./archive -prune -o -type f -mmin +5 -print

    returnFiles = {'include':[], 'exclude':[], 'new':[], 'updated':[]}
    threshold_time = time.time() - (int(stalness) * 60) # 5 minutes
    cruiseStart_time = calendar.timegm(time.strptime(cruiseStartDate, "%m/%d/%Y"))
    
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
            
    returnFiles['include'] = [filename.replace(sourceDir+'/', '', 1) for filename in returnFiles['include']]
    returnFiles['exclude'] = [filename.replace(sourceDir+'/', '', 1) for filename in returnFiles['exclude']]
    
    #print 'DECODED fileList:', json.dumps(returnFiles, indent=2)  
    
    return returnFiles

def build_rsyncFilelist(data, filters, stalness, cruiseStartDate):

    #print "Build file list"

    returnFiles = {'include':[], 'exclude':[], 'new':[], 'updated':[]}
    #print "Calculate now"
    threshold_time = time.time() - (int(stalness) * 60) # 5 minutes
    cruiseStart_time = calendar.timegm(time.strptime(cruiseStartDate, "%m/%d/%Y"))
    
    rawSourceDir = data['collectionSystemTransfer']['sourceDir'].rstrip('/')
    sourceDir = build_sourceDir(rawSourceDir, data).rstrip('/')
    #print "sourceDir: " + sourceDir

    #print threshold_time
    rsyncFileList = ''
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncPasswordFilePath = tmpdir + '/passwordFile'

    try:
        #print "Open rsync password file"
        rsyncPasswordFile = open(rsyncPasswordFilePath, 'w')

        #print "Saving rsync password file"
        rsyncPasswordFile.write(data['collectionSystemTransfer']['rsyncPass'])

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

    
    command = ['rsync', '-r', '--password-file=' + rsyncPasswordFilePath, '--no-motd', 'rsync://' + data['collectionSystemTransfer']['rsyncUser'] + '@' + data['collectionSystemTransfer']['rsyncServer'] + sourceDir + '/']
    
    #s = ' '
    #print s.join(command)
    
    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = proc.communicate()
    rsyncFileList = out

    # Cleanup
    shutil.rmtree(tmpdir)
        
    #print "rsyncFileListOut: " + rsyncFileList
    
#    root = data['collectionSystemTransfer']['sourceDir']
#    baseDir = os.path.basename(data['collectionSystemTransfer']['sourceDir'])
    threshold_time = time.time() - (int(stalness) * 60) # 5 minutes
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

    returnFiles['include'] = [filename.replace(sourceDir, '', 1) for filename in returnFiles['include']]
    returnFiles['exclude'] = [filename.replace(sourceDir, '', 1) for filename in returnFiles['exclude']]
    
    #print 'DECODED returnFiles:', json.dumps(returnFiles, indent=2)  
    
    return returnFiles

def build_sshFilelist(data, filters, stalness, cruiseStartDate):

    #print "Build file list"

    returnFiles = {'include':[], 'exclude':[], 'new':[], 'updated':[]}
    #print "Calculate now"
    threshold_time = time.time() - (int(stalness) * 60) # 5 minutes
    cruiseStart_time = calendar.timegm(time.strptime(cruiseStartDate, "%m/%d/%Y"))
    
    rawSourceDir = data['collectionSystemTransfer']['sourceDir'].rstrip('/')
    sourceDir = build_sourceDir(rawSourceDir, data).rstrip('/')
    #print "sourceDir: " + sourceDir

    #print threshold_time
    rsyncFileList = ''
    
    command = ['sshpass', '-p', data['collectionSystemTransfer']['sshPass'], 'rsync', '-r', '-e', 'ssh -c arcfour', data['collectionSystemTransfer']['sshUser'] + '@' + data['collectionSystemTransfer']['sshServer'] + ':' + sourceDir + '/']
    
    #s = ' '
    #print s.join(command)
        
    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = proc.communicate()
    rsyncFileList = out
        
    #print "rsyncFileListOut: " + rsyncFileList
    
#    root = data['collectionSystemTransfer']['sourceDir']
#    baseDir = os.path.basename(data['collectionSystemTransfer']['sourceDir'])
    threshold_time = time.time() - (int(stalness) * 60) # 5 minutes
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

    returnFiles['include'] = [filename.replace(sourceDir, '', 1) for filename in returnFiles['include']]
    returnFiles['exclude'] = [filename.replace(sourceDir, '', 1) for filename in returnFiles['exclude']]
    
    #print 'DECODED returnFiles:', json.dumps(returnFiles, indent=2)  
    
    return returnFiles

def build_filters(raw_filters, data):
    
    returnFilters = raw_filters
    #print json.dumps(raw_filters, indent=2)
    
    returnFilters['includeFilter'] = returnFilters['includeFilter'].replace('{cruiseID}', data['cruiseID'])
    returnFilters['excludeFilter'] = returnFilters['excludeFilter'].replace('{cruiseID}', data['cruiseID'])
    returnFilters['ignoreFilter'] =  returnFilters['ignoreFilter'].replace('{cruiseID}', data['cruiseID'])
    
    #print json.dumps(returnFilters, indent=2)
    return returnFilters

def build_destDir(raw_destDir, data):
    
    #print raw_destDir
    
    returnDestDir = raw_destDir.replace('{cruiseID}', data['cruiseID'])

    return returnDestDir

def build_sourceDir(raw_sourceDir, data):
    
    #print raw_sourceDir
    
    returnSourceDir = raw_sourceDir.replace('{cruiseID}', data['cruiseID'])

    return returnSourceDir
    
def build_destDirectories(destDir, files):
    files = [filename.replace(filename, destDir + '/' + filename, 1) for filename in files]
    #print 'DECODED Files:', json.dumps(files, indent=2)

    for dirname in set(os.path.dirname(p) for p in files):
        if not os.path.isdir(dirname):
            #print "Creating Directory: " + dirname
            os.makedirs(dirname)

def build_logfileDirPath(warehouseBaseDir, siteRoot):

    url = siteRoot + 'api/extraDirectories/getRequiredExtraDirectories'
    r = requests.get(url)
    transferLogDir = ''
    for directory in r.json():
        if directory['name'] == 'Transfer Logs':
            transferLogDir = warehouseBaseDir + '/' + directory['destDir']
            break
    
    return transferLogDir

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
    

def get_collectionSystemTransfer(job, collectionSystemTransferID):
    dataObj = json.loads(job.data)
    # Set Error for current tranfer in DB via API
    
    url = dataObj['siteRoot'] + 'api/collectionSystemTransfers/getCollectionSystemTransfer/' + collectionSystemTransferID
    r = requests.get(url)
    returnVal = json.loads(r.text)
    return returnVal[0]

def transfer_localSourceDir(data, worker, job):

    #print "Transfer from Local Directory"
    rawFilters = {'includeFilter': data['collectionSystemTransfer']['includeFilter'],'excludeFilter': data['collectionSystemTransfer']['excludeFilter'],'ignoreFilter': data['collectionSystemTransfer']['ignoreFilter']}
    
    staleness = data['collectionSystemTransfer']['staleness']
    cruiseStartDate = data['cruiseStartDate']
    
    filters = build_filters(rawFilters, data)
    
    destDir = data['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+data['cruiseID']+'/'+data['collectionSystemTransfer']['destDir'].rstrip('/')
    sourceDir = data['collectionSystemTransfer']['sourceDir'].rstrip('/')+'/'
    
    #print "Build file list"
    files = build_filelist(sourceDir, filters, staleness, cruiseStartDate)

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
    
    command = ['rsync', '-tri', '--files-from=' + rsyncFileListPath, sourceDir, destDir]
    
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

def transfer_smbSourceDir(data, worker, job):

#    print 'DECODED Data:', json.dumps(data, indent=2)
    staleness = data['collectionSystemTransfer']['staleness']
    cruiseStartDate = data['cruiseStartDate']

    #print "Transfer from SMB Server"
    rawFilters = {'includeFilter': data['collectionSystemTransfer']['includeFilter'],'excludeFilter': data['collectionSystemTransfer']['excludeFilter'],'ignoreFilter': data['collectionSystemTransfer']['ignoreFilter']}
    filters = build_filters(rawFilters, data)

    # Create temp directory
    #print "Create Temp Directory"
    tmpdir = tempfile.mkdtemp()
 
    # Create mountpoint
    #print "Create Mountpoint"
    mntPoint = tmpdir + '/mntpoint'
    os.mkdir(mntPoint, 0755)

    # Mount SMB Share
    #print "Mount SMB Share"
    if data['collectionSystemTransfer']['smbUser'] == 'guest':
        
        command = ['sudo', 'mount', '-t', 'cifs', data['collectionSystemTransfer']['smbServer'], mntPoint, '-o', 'ro'+ ',guest' + ',domain='+data['collectionSystemTransfer']['smbDomain']]
        
        #s = ' '
        #print s.join(command)
    
        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()
        
    else:
        command = ['sudo', 'mount', '-t', 'cifs', data['collectionSystemTransfer']['smbServer'], mntPoint, '-o', 'ro'+ ',username='+data['collectionSystemTransfer']['smbUser']+',password='+data['collectionSystemTransfer']['smbPass']+',domain='+data['collectionSystemTransfer']['smbDomain']]
        
        #s = ' '
        #print s.join(command)
    
        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

    rawDestDir = data['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+data['cruiseID']+'/'+data['collectionSystemTransfer']['destDir'].rstrip('/')
    destDir = build_destDir(rawDestDir, data)
    rawSourceDir = mntPoint+'/'+data['collectionSystemTransfer']['sourceDir'].rstrip('/')
    sourceDir = build_sourceDir(rawSourceDir, data).rstrip('/')
    
    #print "Source Dir: " + sourceDir
    #print "Destinstation Dir: " + destDir
    
    #print "Build file list"
    files = build_filelist(sourceDir, filters, staleness, cruiseStartDate)
    
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


def transfer_rsyncSourceDir(data, worker, job):

    #print "Transfer from RSYNC Server"
#    print 'DECODED Data:', json.dumps(data, indent=2)
    staleness = data['collectionSystemTransfer']['staleness']
    cruiseStartDate = data['cruiseStartDate']

    #print "Build Raw Filters"
    rawFilters = {'includeFilter': data['collectionSystemTransfer']['includeFilter'],'excludeFilter': data['collectionSystemTransfer']['excludeFilter'],'ignoreFilter': data['collectionSystemTransfer']['ignoreFilter']}

    #print "Build Processed Filters"
    filters = build_filters(rawFilters, data)

    rawDestDir = data['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+data['cruiseID']+'/'+data['collectionSystemTransfer']['destDir'].rstrip('/')
    destDir = build_destDir(rawDestDir, data).rstrip('/')
    rawSourceDir = data['collectionSystemTransfer']['sourceDir'].rstrip('/')
    sourceDir = build_sourceDir(rawSourceDir, data).rstrip('/')
    
    #print "Build file list"    
    files = build_rsyncFilelist(data, filters, staleness, cruiseStartDate)
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    count = 1
    fileCount = len(files['include'])
    
    rsyncPasswordFilePath = tmpdir + '/passwordFile'

    try:
        #print "Open temporary rsync password file"
        rsyncPasswordFile = open(rsyncPasswordFilePath, 'w')

        #print "Saving temporary rsync password file"
        rsyncPasswordFile.write(data['collectionSystemTransfer']['rsyncPass'])

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
    
    
    command = ['rsync', '-ti', '--no-motd', '--files-from=' + rsyncFileListPath, '--password-file=' + rsyncPasswordFilePath, 'rsync://' + data['collectionSystemTransfer']['rsyncUser'] + '@' + data['collectionSystemTransfer']['rsyncServer'] + sourceDir, destDir]
        
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

def transfer_sshSourceDir(data, worker, job):

#    print 'DECODED Data:', json.dumps(data, indent=2)

    #print "Transfer from SSH Server"
    staleness = data['collectionSystemTransfer']['staleness']
    cruiseStartDate = data['cruiseStartDate']

    #print "Build Raw Filters"
    rawFilters = {'includeFilter': data['collectionSystemTransfer']['includeFilter'],'excludeFilter': data['collectionSystemTransfer']['excludeFilter'],'ignoreFilter': data['collectionSystemTransfer']['ignoreFilter']}

    #print "Build Processed Filters"
    filters = build_filters(rawFilters, data)

    rawDestDir = data['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+data['cruiseID']+'/'+data['collectionSystemTransfer']['destDir'].rstrip('/')
    destDir = build_destDir(rawDestDir, data).rstrip('/')
    rawSourceDir = data['collectionSystemTransfer']['sourceDir'].rstrip('/')
    sourceDir = build_sourceDir(rawSourceDir, data).rstrip('/')
        
    files = build_sshFilelist(data, filters, staleness, cruiseStartDate)
    
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
    
    
    command = ['sshpass', '-p', data['collectionSystemTransfer']['sshPass'], 'rsync', '-ti', '--files-from=' + sshFileListPath, '-e', 'ssh -c arcfour', data['collectionSystemTransfer']['sshUser'] + '@' + data['collectionSystemTransfer']['sshServer'] + ':' + sourceDir, destDir]

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

def transfer_nfsSourceDir(data, worker, job):

#    print 'DECODED Data:', json.dumps(data, indent=2)
    staleness = data['collectionSystemTransfer']['staleness']
    cruiseStartDate = data['cruiseStartDate']

    #print "Transfer from NFS Server"
    rawFilters = {'includeFilter': data['collectionSystemTransfer']['includeFilter'],'excludeFilter': data['collectionSystemTransfer']['excludeFilter'],'ignoreFilter': data['collectionSystemTransfer']['ignoreFilter']}
    filters = build_filters(rawFilters, data)

    # Create temp directory
    #print "Create Temp Directory"
    tmpdir = tempfile.mkdtemp()
 
    # Create mountpoint
    #print "Create Mountpoint"
    mntPoint = tmpdir + '/mntpoint'
    os.mkdir(mntPoint, 0755)

    # Mount NFS Server
    #print "Mount NFS Server"
        
    command = ['sudo', 'mount', '-t', 'nfs', data['collectionSystemTransfer']['nfsServer'], mntPoint, '-o', 'ro'+ ',vers=2' + ',hard' + ',intr']

    #s = ' '
    #print s.join(command)

    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    proc.communicate()
        
    rawDestDir = data['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']+'/'+data['cruiseID']+'/'+data['collectionSystemTransfer']['destDir'].rstrip('/')
    destDir = build_destDir(rawDestDir, data)
    rawSourceDir = mntPoint+'/'+data['collectionSystemTransfer']['sourceDir'].rstrip('/')
    sourceDir = build_sourceDir(rawSourceDir, data).rstrip('/')
    
    #print "Source Dir: " + sourceDir
    #print "Destinstation Dir: " + destDir
    
    #print "Build file list"
    files = build_filelist(sourceDir, filters, staleness, cruiseStartDate)
    
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
    
    #print "Unmount NFS Server"
    subprocess.call(['sudo', 'umount', mntPoint])
    
    #print "Cleanup"
    shutil.rmtree(tmpdir)

    #print 'DECODED Files:', json.dumps(files, indent=2)
    return files

def setError_collectionSystemTransfer(job, reason=''):
    dataObj = json.loads(job.data)

    # Set Error for current tranfer in DB via API
    url = dataObj['siteRoot'] + 'api/collectionSystemTransfers/setErrorCollectionSystemTransfer/' + dataObj['collectionSystemTransfer']['collectionSystemTransferID']
    r = requests.get(url)
    
    if not reason == '':
        url = dataObj['siteRoot'] + 'api/messages/newMessage'
        payload = {'message': dataObj['collectionSystemTransfer']['name'] + ' Data Transfer: ' + reason}
        r = requests.post(url, data=payload)

def setRunning_collectionSystemTransfer(job):
    dataObj = json.loads(job.data)
    jobPID = os.getpid()

    # Set Error for current tranfer in DB via API
    url = dataObj['siteRoot'] + 'api/collectionSystemTransfers/setRunningCollectionSystemTransfer/' + dataObj['collectionSystemTransfer']['collectionSystemTransferID']
    payload = {'jobPid': jobPID}
    r = requests.post(url, data=payload)

    # Add Job to DB via API
    url = dataObj['siteRoot'] + 'api/gearman/newJob/' + job.handle
    payload = {'jobName': 'Run Transfer for ' + dataObj['collectionSystemTransfer']['name'],'jobPid': jobPID}
    r = requests.post(url, data=payload)

def setIdle_collectionSystemTransfer(job):
    dataObj = json.loads(job.data)

    # Set Error for current tranfer in DB via API
    url = dataObj['siteRoot'] + 'api/collectionSystemTransfers/setIdleCollectionSystemTransfer/' + dataObj['collectionSystemTransfer']['collectionSystemTransferID']
    r = requests.get(url)

def clearError_collectionSystemTransfer(job):
    dataObj = json.loads(job.data)
    if dataObj['collectionSystemTransfer']['status'] == "3":
        # Clear Error for current tranfer in DB via API
        url = dataObj['siteRoot'] + 'api/collectionSystemTransfers/setIdleCollectionSystemTransfer/' + dataObj['collectionSystemTransfer']['collectionSystemTransferID']
        r = requests.get(url)

class CustomGearmanWorker(gearman.GearmanWorker):
    
    def __init__(self, host_list=None):
        super(CustomGearmanWorker, self).__init__(host_list=host_list)
        self.startTime = time.gmtime(0)
        self.stop = False
        self.quit = False
    
    def on_job_execute(self, current_job):
        print "Job started: " + current_job.handle
        self.startTime = time.gmtime()
        return super(CustomGearmanWorker, self).on_job_execute(current_job)

    def on_job_exception(self, current_job, exc_info):
        print "Job failed, CAN stop last gasp GEARMAN_COMMAND_WORK_FAIL"
        self.send_job_data(current_job, json.dumps([{"partName": "Unknown Part of Transfer", "result": "Fail"}]))
        setError_collectionSystemTransfer(current_job, "Unknown Part of Transfer Failed")
        print exc_info
        return super(CustomGearmanWorker, self).on_job_exception(current_job, exc_info)

    def on_job_complete(self, current_job, job_result):
        resultObj = json.loads(job_result)
        dataObj = json.loads(current_job.data)
        print "Job complete, CAN stop last gasp GEARMAN_COMMAND_WORK_COMPLETE"
        
        if resultObj['parts'][-1]['partName'] != "Transfer Enabled" and resultObj['parts'][-1]['partName'] != "Transfer In-Progress": # Final Verdict
            if resultObj['parts'][-1]['result'] == "Fail": # Final Verdict
                print resultObj['parts'][-1]['partName']
                if resultObj['parts'][-1]['partName'] != "Transfer Enabled" and resultObj['parts'][-1]['partName'] != "Transfer In-Progress Test":
                    setError_collectionSystemTransfer(current_job, resultObj['parts'][-1]['partName'] + " Failed")
                    print "but something prevented the transfer from successfully completing..."
                else:
                    if dataObj['collectionSystemTransfer']['status'] == '3':
                        setError_collectionSystemTransfer(current_job)
                    else:
                        setIdle_collectionSystemTransfer(current_job)
            else:
                setIdle_collectionSystemTransfer(current_job)
            
                #print 'DECODED:', json.dumps(resultObj, indent=2)
                gm_client = gearman.GearmanClient(['localhost:4730'])

                jobData = {'shipboardDataWarehouse':{}, 'cruiseID':'', 'files':{}}
                jobData['siteRoot'] = dataObj['siteRoot']
                jobData['shipboardDataWarehouse'] = dataObj['shipboardDataWarehouse']
                jobData['cruiseID'] = dataObj['cruiseID']
                destDir = build_destDir(dataObj['collectionSystemTransfer']['destDir'], dataObj)
                jobData['files'] = resultObj['files']
                jobData['files']['new'] = [destDir + '/' + filename for filename in jobData['files']['new']]
                jobData['files']['updated'] = [destDir + '/' + filename for filename in jobData['files']['updated']]
                #jobData['files']['exclude'] = [destDir + filename for filename in jobData['files']['exclude']]

                if resultObj['files']['new'] or resultObj['files']['updated']:
                    #print "Sending transfer results to MD5 Updater worker"
                    submitted_job_request = gm_client.submit_job("updateMD5Summary", json.dumps(jobData), background=True)
                
                    #print "Sending transfer results to Update Data Dashboard worker"
                    jobData['collectionSystemID'] = dataObj['collectionSystemTransfer']['collectionSystemTransferID']
                    submitted_job_request = gm_client.submit_job("updateDataDashboard", json.dumps(jobData), background=True)
                    
        return super(CustomGearmanWorker, self).send_job_complete(current_job, job_result)

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
        
def task_callback(gearman_worker, job):

    time.sleep(randint(0,5))
    
    t = time.mktime(gearman_worker.startTime)
    job_results = {'parts':[], 'files':[], 'startDate':time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(t))}

    dataObj = json.loads(job.data)
    baseDir = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseBaseDir']
    cruiseID = dataObj['cruiseID']
    warehouseUser = dataObj['shipboardDataWarehouse']['shipboardDataWarehouseUsername']  
    collectionSystemDestDir = build_destDir(dataObj['collectionSystemTransfer']['destDir'], dataObj)
    dataObj['collectionSystemTransfer']['destDir'] = build_destDir(dataObj['collectionSystemTransfer']['destDir'], dataObj)
    dataObj['collectionSystemTransfer']['sourceDir'] = build_sourceDir(dataObj['collectionSystemTransfer']['sourceDir'], dataObj)
    #print 'DECODED:', json.dumps(dataObj, indent=2)
    
    if dataObj['collectionSystemTransfer']['enable'] == "1" and dataObj['systemStatus'] == "On":
        #print "Transfer Enabled"
        job_results['parts'].append({"partName": "Transfer Enabled", "result": "Pass"})
    else:
        #print "Transfer Disabled"
        #print "Stopping"
        job_results['parts'].append({"partName": "Transfer Enabled", "result": "Fail"})
        return json.dumps(job_results)

    transfer = get_collectionSystemTransfer(job, dataObj['collectionSystemTransfer']['collectionSystemTransferID'])
    
    if transfer['status'] == "1": #running
        #print "Transfer already in-progress"
        job_results['parts'].append({"partName": "Transfer In-Progress", "result": "Fail"})
        #print "Stopping"
        return json.dumps(job_results)
    else:
        #print "Transfer not already in-progress"
        job_results['parts'].append({"partName": "Transfer In-Progress", "result": "Pass"})
        
    # Set transfer status to "Running"
    setRunning_collectionSystemTransfer(job)
        
    #print "Testing configuration"
    gearman_worker.send_job_status(job, 1, 10)

    # First test to see if the transfer can occur 
    gm_client = gearman.GearmanClient(['localhost:4730'])
    gmData = dataObj
    gmData['collectionSystemTransfer']['status'] = "1"
    completed_job_request = gm_client.submit_job("testCollectionSystemTransfer", json.dumps(gmData))
    resultsObj = json.loads(completed_job_request.result)
    #print 'DECODED Results:', json.dumps(resultsObj, indent=2)

    if resultsObj[-1]['result'] == "Pass": # Final Verdict
        #print "Connection Test: Passed"
        job_results['parts'].append({"partName": "Connection Test", "result": "Pass"})
    else:
        #print "Connection Test: Failed"
        #print "Stopping"
        job_results['parts'].append({"partName": "Connection Test", "result": "Fail"})
        #print json.dumps(job_results, indent=2)
        return json.dumps(job_results)

    gearman_worker.send_job_status(job, 2, 10)
    
    if dataObj['collectionSystemTransfer']['useStartDate'] == "0":
        dataObj['cruiseStartDate'] = "01/01/1970"    
    
    #print "Transfer Data"
    if dataObj['collectionSystemTransfer']['transferType'] == "1": # Local Directory
        job_results['files'] = transfer_localSourceDir(dataObj, gearman_worker, job)
    elif  dataObj['collectionSystemTransfer']['transferType'] == "2": # Rsync Server
        job_results['files'] = transfer_rsyncSourceDir(dataObj, gearman_worker, job)
    elif  dataObj['collectionSystemTransfer']['transferType'] == "3": # SMB Server
        job_results['files'] = transfer_smbSourceDir(dataObj, gearman_worker, job)
    elif  dataObj['collectionSystemTransfer']['transferType'] == "4": # SSH Server
        job_results['files'] = transfer_sshSourceDir(dataObj, gearman_worker, job)
    elif  dataObj['collectionSystemTransfer']['transferType'] == "5": # NFS Server
        job_results['files'] = transfer_nfsSourceDir(dataObj, gearman_worker, job)

    #print "Transfer Complete"
    gearman_worker.send_job_status(job, 9, 10)
    
    if(setDirectoryOwnerGroupPermissions(baseDir + '/' + cruiseID + '/' +  collectionSystemDestDir, pwd.getpwnam(warehouseUser).pw_uid, grp.getgrnam(warehouseUser).gr_gid)):
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Pass"})
    else:
        print "Error Setting file/directory ownership"
        job_results['parts'].append({"partName": "Setting file/directory ownership", "result": "Fail"})
    
    warehouseTransferLogDir = build_logfileDirPath(baseDir + '/' + cruiseID , dataObj['siteRoot'])
    #print warehouseTransferLogDir   

    if job_results['files']['new'] or job_results['files']['updated']:

        #print "Send transfer log"
        if os.path.isdir(warehouseTransferLogDir):
    
            logfileName = warehouseTransferLogDir + '/' + dataObj['collectionSystemTransfer']['name'] + '_' + job_results['startDate'] + '.log'
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
        job_results['files']['exclude'] = [dataObj['collectionSystemTransfer']['destDir'].rstrip('/') + '/' + filename for filename in job_results['files']['exclude']]
        
    #print "Send filename error log"
    if os.path.isdir(warehouseTransferLogDir):

        filenameErrorLogfileName = warehouseTransferLogDir + '/' + dataObj['collectionSystemTransfer']['name'] + '_Exclude.log'
        filenameErrorlogOutput = {'files':{'exclude':[]}}
        filenameErrorlogOutput['files']['exclude'] = job_results['files']['exclude']
        if writeLogFile(filenameErrorLogfileName, warehouseUser, filenameErrorlogOutput['files']):
            job_results['parts'].append({"partName": "Write filename error logfile", "result": "Pass"})
        else:
            job_results['parts'].append({"partName": "Write filename error logfile", "result": "Fail"})
                
    else:
        job_results['parts'].append({"partName": "Logfile directory", "result": "Fail"})

    gearman_worker.send_job_status(job, 10, 10)
    
    time.sleep(5)

    return json.dumps(job_results)

global new_worker
new_worker = CustomGearmanWorker(['localhost:4730'])

def sigquit_handler(_signo, _stack_frame):
    print "QUIT Signal Received"
    new_worker.stopTransfer()
    
def sigint_handler(_signo, _stack_frame):
    print "INT Signal Received"
    new_worker.quitWorker()
    
signal.signal(signal.SIGQUIT, sigquit_handler)
signal.signal(signal.SIGINT, sigint_handler)

new_worker.set_client_id('runCollectionSystemTransfer.py')
new_worker.register_task("runCollectionSystemTransfer", task_callback)

new_worker.work()
