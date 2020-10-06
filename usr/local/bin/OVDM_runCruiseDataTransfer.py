# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_runCruiseDataTransfer.py
#
#  DESCRIPTION:  Gearman worker that handles the transfer of all cruise data from the
#                Shipboard Data Warehouse to a second location.
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
import fnmatch
import subprocess
import signal
import grp
import pwd
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


def setOwnerGroupPermissions(worker, path):

    if worker.stop:
        return {'verdict': True}

    warehouseUser = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']

    #debugPrint(path)

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
                    #debugPrint("Setting ownership/permissions for", fname)
                    os.chown(fname, uid, gid)
                    os.chmod(fname, 0644)
                except OSError:
                    errPrint("Unable to set ownership/permissions for", fname)
                    reason.append("Unable to set ownership/permissions for " + fname)

                if worker.stop:
                    debugPrint("Stopping")
                    break

            for momo in dirs:
                dname = os.path.join(root, momo)
                try:
                    debugPrint("Setting ownership/permissions for", dname)
                    os.chown(dname, uid, gid)
                    os.chmod(dname, 0755)
                except OSError:
                    errPrint("Unable to set ownership/permissions for", dname)
                    reason.append("Unable to set ownership/permissions for " + dname)

                if worker.stop:
                    debugPrint("Stopping")
                    break

            if worker.stop:
                #debugPrint("Stopping")
                break

    if len(reason) > 0:
        return {'verdict': False, 'reason': '\n'.join(reason)}

    return {'verdict': True}


def build_filelist(worker, sourceDir):

    returnFiles = {'include':[], 'exclude':[], 'new':[], 'updated':[]}

    #debugPrint(returnFiles)

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
                    if fnmatch.fnmatch(os.path.join(root, filename), filt):
                        for filt in filters['excludeFilter'].split(','): 
                            if fnmatch.fnmatch(os.path.join(root, filename), filt):
                                debugPrint(filename, "excluded")
                                returnFiles['exclude'].append(os.path.join(root, filename))
                                exclude = True
                                break
                        if not exclude:
                            if os.path.islink(os.path.join(root, filename)):
                                continue

                            #debugPrint(filename, "included")
                            returnFiles['include'].append(os.path.join(root, filename))
                            include = True

                if not include and not exclude:
                    debugPrint(filename, "excluded")
                    returnFiles['exclude'].append(os.path.join(root, filename))

    returnFiles['include'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['include']]
    returnFiles['exclude'] = [filename.split(sourceDir + '/',1).pop() for filename in returnFiles['exclude']]

    debugPrint(returnFiles)
    return returnFiles


def build_destDirectories(destDir, files):
    files = [filename.replace(filename, destDir + filename, 1) for filename in files]

    for dirname in set(os.path.dirname(p) for p in files):
        if not os.path.isdir(dirname):
            debugPrint("Creating Directory:", dirname)
            os.makedirs(dirname)


def build_filters(worker):
    
    returnFilters = {'includeFilter': '*','excludeFilter': '','ignoreFilter': ''}

    excludedFilterArray = []

    if worker.cruiseDataTransfer['includeOVDMFiles'] == '0':
        dashboardDataDir = worker.OVDM.getRequiredExtraDirectoryByName("Dashboard Data")
        excludedFilterArray.append("*/{cruiseID}/" + dashboardDataDir['destDir'] + "/*")

        transferLogs = worker.OVDM.getRequiredExtraDirectoryByName("Transfer Logs")
        excludedFilterArray.append("*/{cruiseID}/" + transferLogs['destDir'] + "/*")


    excludedCollectionSystems = worker.cruiseDataTransfer['excludedCollectionSystems'].split(',')
    for excludedCollectionSystem in excludedCollectionSystems:
        collectionSystemTransfer = worker.OVDM.getCollectionSystemTransfer(excludedCollectionSystem)
        if collectionSystemTransfer:
            if collectionSystemTransfer['cruiseOrLowering'] == '0':
                excludedFilterArray.append("*/{cruiseID}/" + collectionSystemTransfer['destDir'] + "/*")
            else:
                lowerings = worker.OVDM.getLowerings()
                for lowering in lowerings:
                    excludedFilterArray.append("*/{cruiseID}/*/" + lowering + "/" + collectionSystemTransfer['destDir'].replace('{loweringID}', lowering) + "/*")

    excludedExtraDirectories = worker.cruiseDataTransfer['excludedExtraDirectories'].split(',')
    #debugPrint(excludedExtraDirectories)
    for excludedExtraDirectory in excludedExtraDirectories:
        extraDirectory = worker.OVDM.getExtraDirectory(excludedExtraDirectory)
        if extraDirectory:
            excludedFilterArray.append("*/{cruiseID}/" + extraDirectory['destDir'] + "/*")

    returnFilters['excludeFilter'] = ','.join(excludedFilterArray)

    returnFilters['includeFilter'] = returnFilters['includeFilter'].replace('{cruiseID}', worker.cruiseID)
    returnFilters['excludeFilter'] = returnFilters['excludeFilter'].replace('{cruiseID}', worker.cruiseID)
    returnFilters['ignoreFilter'] =  returnFilters['ignoreFilter'].replace('{cruiseID}', worker.cruiseID)

    returnFilters['includeFilter'] = returnFilters['includeFilter'].replace('{loweringID}', worker.loweringID)
    returnFilters['excludeFilter'] = returnFilters['excludeFilter'].replace('{loweringID}', worker.loweringID)
    returnFilters['ignoreFilter'] =  returnFilters['ignoreFilter'].replace('{loweringID}', worker.loweringID)
    
    debugPrint(returnFilters)
    return returnFilters


def build_excludeList(worker):
    
    excludedFilterArray = []

    if worker.cruiseDataTransfer['includeOVDMFiles'] == '0':
        dashboardDataDir = worker.OVDM.getRequiredExtraDirectoryByName("Dashboard Data")
        excludedFilterArray.append("/" + dashboardDataDir['destDir'])

        transferLogs = worker.OVDM.getRequiredExtraDirectoryByName("Transfer Logs")
        excludedFilterArray.append("/" + transferLogs['destDir'])

    excludedCollectionSystems = worker.cruiseDataTransfer['excludedCollectionSystems'].split(',')

    for excludedCollectionSystem in excludedCollectionSystems:
        collectionSystemTransfer = worker.OVDM.getCollectionSystemTransfer(excludedCollectionSystem)
        if collectionSystemTransfer:
            if collectionSystemTransfer['cruiseOrLowering'] == '0':
                excludedFilterArray.append("/" + collectionSystemTransfer['destDir'])
            else:
                lowerings = worker.OVDM.getLowerings()
                for lowering in lowerings:
                    excludedFilterArray.append("/" + worker.shipboardDataWarehouseConfig['loweringDataBaseDir'] + "/" + lowering + "/" + collectionSystemTransfer['destDir'].replace('{loweringID}', lowering))

    excludedExtraDirectories = worker.cruiseDataTransfer['excludedExtraDirectories'].split(',')
    debugPrint(excludedExtraDirectories)

    for excludedExtraDirectory in excludedExtraDirectories:
        extraDirectory = worker.OVDM.getExtraDirectory(excludedExtraDirectory)
        if extraDirectory:
            excludedFilterArray.append("/" + extraDirectory['destDir'])

    excludedFilterArray = [s.replace('{cruiseID}', worker.cruiseID) for s in excludedFilterArray]
    excludedFilterArray = [s.replace('{loweringID}', worker.loweringID) for s in excludedFilterArray]

    #excludedFilterArray = ["--exclude=\"" + s + "\"" for s in excludedFilterArray]

    #debugPrint("\n".join(excludedFilterArray))
    return excludedFilterArray

            
def transfer_localDestDir(worker, job):

    debugPrint("Transfer to Local Directory")
    filters = {'includeFilter': '*','excludeFilter': '','ignoreFilter': ''}
    
    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    destDir = os.path.join(worker.cruiseDataTransfer['destDir'], worker.cruiseID)

    debugPrint('destDir:', destDir)

    try:
        if not os.path.exists(destDir):
            debugPrint("Creating Cruise folder within destinstation directory")
            os.mkdir(destDir)
    except IOError:
        errPrint("Error Creating cruise directory at destinstation location")
        return False

    debugPrint("Build file list")
    #files = build_filelist(worker, cruiseDir)
    files = {'include':[], 'exclude':[], 'new':[], 'updated':[]}
    excludeList = build_excludeList(worker)
    
    # fileIndex = 0
    # fileCount = len(files['include'])
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsyncExcludeListPath = os.path.join(tmpdir, 'rsyncExcludeList.txt')
        
    try:
        rsyncExcludeListFile = open(rsyncExcludeListPath, 'w')
        rsyncExcludeListFile.write('\n'.join([str(x) for x in excludeList]))
        debugPrint('\n'.join([str(x) for x in excludeList]))

    except IOError:
        errPrint("Error Saving temporary rsync filelist file")
        rsyncExcludeListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
        return False

    finally:
        #debugPrint("Closing rsync filelist file")
        rsyncExcludeListFile.close()

    bandwidthLimit = '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    if worker.cruiseDataTransfer['bandwidthLimit'] != '0':
        bandwidthLimit = '--bwlimit=' + worker.cruiseDataTransfer['bandwidthLimit']
    
    command = ['rsync', '-tri', bandwidthLimit, '--exclude-from=' + rsyncExcludeListPath, cruiseDir + '/', destDir]
    # command = ['rsync', '-tri', bandwidthLimit, '--files-from=' + rsyncFileListPath, baseDir, destDir]
    # command = ['rsync', '-tri',               '--files-from=' + rsyncFileListPath, baseDir, destDir]

    s = ' '
    debugPrint('Transfer Command:', s.join(command))
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
    	# debugPrint('line:', line.rstrip('\n'))
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['new'].append(filename)
#            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
#            fileIndex += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['updated'].append(filename)
#            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
#            fileIndex += 1
            
        if worker.stop:
            debugPrint("Stopping")
            break    

    files['new'] = [os.path.join('/', worker.cruiseID, filename) for filename in files['new']]
    files['updated'] = [os.path.join('/', worker.cruiseID, filename) for filename in files['updated']]

    debugPrint("Setting file permissions")
    setOwnerGroupPermissions(worker, os.path.join(destDir))

    # Cleanup
    shutil.rmtree(tmpdir)    
    return files


def transfer_smbDestDir(worker, job):
    
    debugPrint("Transfer from SMB Source")

    filters = {'includeFilter': '*','excludeFilter': '','ignoreFilter': ''}

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
 
    # Create mountpoint
    mntPoint = os.path.join(tmpdir, 'mntpoint')
    os.mkdir(mntPoint, 0755)

    # Mount SMB Share
    debugPrint("Mounting SMB Share")
    if worker.cruiseDataTransfer['smbUser'] == 'guest':

        command = ['smbclient', '-L', worker.cruiseDataTransfer['smbServer'], '-W', worker.cruiseDataTransfer['smbDomain'], '-m', 'SMB2','-g', '-N']
    
        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        stderr_iterator = iter(proc.stderr.readline, b"")
        vers = ",vers=2.1"
        for line in stderr_iterator:
            if line.startswith('OS=[Windows 5.1]'):
                vers=",vers=1.0"
        
        command = ['mount', '-t', 'cifs', worker.cruiseDataTransfer['smbServer'], mntPoint, '-o', 'rw' + ',guest' +  'domain=' + worker.cruiseDataTransfer['smbDomain']+vers]
        
        s = ' '
        debugPrint(s.join(command))

        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

    else:

        command = ['smbclient', '-L', worker.cruiseDataTransfer['smbServer'], '-W', worker.cruiseDataTransfer['smbDomain'], '-m', 'SMB2','-g', '-U', worker.cruiseDataTransfer['smbUser'] + '%' + worker.cruiseDataTransfer['smbPass']]
    
        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        stderr_iterator = iter(proc.stderr.readline, b"")
        vers = ",vers=2.1"
        for line in stderr_iterator:
            if line.startswith('OS=[Windows 5.1]'):
                vers=",vers=1.0"

        command = ['mount', '-t', 'cifs', worker.cruiseDataTransfer['smbServer'], mntPoint, '-o', 'rw' + ',username=' + worker.cruiseDataTransfer['smbUser'] + ',password='+worker.cruiseDataTransfer['smbPass'] + ',domain='+worker.cruiseDataTransfer['smbDomain']+vers]
        
        s = ' '
        debugPrint(s.join(command))

        proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.communicate()

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)

    sourceDir = cruiseDir
    destDir = os.path.join(mntPoint, worker.cruiseID)

    if not worker.cruiseDataTransfer['destDir'] == '/':
        destDir = os.path.join(mntPoint, worker.cruiseDataTransfer['destDir'], worker.cruiseID)        

    debugPrint("destDir:", destDir)

    try:
        if not os.path.exists(destDir):
            debugPrint("Creating Cruise folder within destinstation directory")
            os.mkdir(destDir)
    except IOError:
        errPrint("Error Creating cruise directory at destinstation location")
        return False


    debugPrint("Build file list")
#    files = build_filelist(worker, cruiseDir)
    files = {'include':[], 'exclude':[], 'new':[], 'updated':[]}
    excludeList = build_excludeList(worker)
    #fileIndex = 0
    #fileCount = len(files['include'])
    
    rsyncExcludeListPath = os.path.join(tmpdir, 'rsyncExcludeList.txt')
        
    try:
        rsyncExcludeListFile = open(rsyncExcludeListPath, 'w')
        rsyncExcludeListFile.write('\n'.join([str(x) for x in excludeList]))
        debugPrint('\n'.join([str(x) for x in excludeList]))

    except IOError:
        errPrint("Error Saving temporary rsync filelist file")
        rsyncExcludeListFile.close()
            
        # Cleanup
        time.sleep(2)
        subprocess.call(['umount', mntPoint])
        shutil.rmtree(tmpdir)
            
        return False

    finally:
        rsyncExcludeListFile.close()
    

    bandwidthLimit = '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    if worker.cruiseDataTransfer['bandwidthLimit'] != '0':
        bandwidthLimit = '--bwlimit=' + worker.cruiseDataTransfer['bandwidthLimit']

    command = ['rsync', '-tri', bandwidthLimit, '--exclude-from=' + rsyncExcludeListPath, cruiseDir + '/', destDir]
    #command = ['rsync', '-tri', bandwidthLimit, '--files-from=' + rsyncFileListPath, sourceDir, destDir]
    #command = ['rsync', '-tri',                '--files-from=' + rsyncFileListPath, sourceDir, destDir]
    
    s = ' '
    debugPrint('Transfer Command:', s.join(command))

    popen = subprocess.Popen(command, stdout=subprocess.PIPE)

    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        # debugPrint('line', line.rstrip('\n'))
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['new'].append(filename)
#            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
#            fileIndex += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['updated'].append(filename)
#            worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
#            fileIndex += 1
            
        if worker.stop:
            debugPrint("Stopping")
            break
    
    files['new'] = [os.path.join('/', worker.cruiseID,filename) for filename in files['new']]
    files['updated'] = [os.path.join('/', worker.cruiseID,filename) for filename in files['updated']]

    #print "Cleanup"
    time.sleep(2)
    debugPrint("Unmount SMB Share")
    subprocess.call(['umount', mntPoint])
    shutil.rmtree(tmpdir)

    return files


def transfer_rsyncDestDir(worker, job):

    debugPrint("Transfer to Rsync Server")
    filters = {'includeFilter': '*','excludeFilter': '','ignoreFilter': ''}

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)

    sourceDir = cruiseDir
    destDir = worker.cruiseDataTransfer['destDir'].rstrip('/')

    #debugPrint("Source Dir:", sourceDir)
    #debugPrint("Destinstation Dir:", destDir)
    
    debugPrint("Build file list")
    files = {'include':[], 'exclude':[], 'new':[], 'updated':[]}
    excludeList = build_excludeList(worker)
    #files = build_filelist(worker, sourceDir)
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    
    #fileIndex = 0
    #fileCount = len(files['include'])
    
    rsyncPasswordFilePath = os.path.join(tmpdir, 'passwordFile')

    try:
        rsyncPasswordFile = open(rsyncPasswordFilePath, 'w')
        rsyncPasswordFile.write(worker.cruiseDataTransfer['rsyncPass'])

    except IOError:
        errPrint("Error Saving temporary rsync password file")
        rsyncPasswordFile.close()

        # Cleanup
        shutil.rmtree(tmpdir)

        return False

    finally:
        rsyncPasswordFile.close()
        os.chmod(rsyncPasswordFilePath, 0600)
    
    rsyncExcludeListPath = os.path.join(tmpdir, 'rsyncExcludeList.txt')
        
    try:
        rsyncExcludeListFile = open(rsyncExcludeListPath, 'w')
        rsyncExcludeListFile.write('\n'.join([str(x) for x in excludeList]))
        debugPrint('\n'.join([str(x) for x in excludeList]))

    except IOError:
        errPrint("Error Saving temporary rsync filelist file")
        rsyncExcludeListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return False

    finally:
        rsyncFileListFile.close()
    
    bandwidthLimit = '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    if worker.cruiseDataTransfer['bandwidthLimit'] != '0':
        bandwidthLimit = '--bwlimit=' + worker.cruiseDataTransfer['bandwidthLimit']

    # Work around to create CruiseID at the destination
    os.mkdir(os.path.join(tmpdir, worker.cruiseID))
    command = ['rsync', '-a', bandwidthLimit, '--no-motd', '--password-file=' + rsyncPasswordFilePath, os.path.join(tmpdir, worker.cruiseID), 'rsync://' + worker.cruiseDataTransfer['rsyncUser'] + '@' + worker.cruiseDataTransfer['rsyncServer'] + destDir + '/']
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)


    command = ['rsync', '-tri', bandwidthLimit, '--no-motd', '--exclude-from=' + rsyncExcludeListPath, '--password-file=' + rsyncPasswordFilePath, cruiseDir + '/', 'rsync://' + worker.cruiseDataTransfer['rsyncUser'] + '@' + worker.cruiseDataTransfer['rsyncServer'] + destDir + '/' + worker.cruiseID + '/']
    #command = ['rsync', '-tri', bandwidthLimit, '--no-motd', '--files-from=' + rsyncFileListPath, '--password-file=' + rsyncPasswordFilePath, sourceDir, 'rsync://' + worker.cruiseDataTransfer['rsyncUser'] + '@' + worker.cruiseDataTransfer['rsyncServer'] + destDir + '/']
    #command = ['rsync', '-tri',                '--no-motd', '--files-from=' + rsyncFileListPath, '--password-file=' + rsyncPasswordFilePath, sourceDir, 'rsync://' + worker.cruiseDataTransfer['rsyncUser'] + '@' + worker.cruiseDataTransfer['rsyncServer'] + destDir + '/']
    
    s = ' '
    debugPrint('Transfer Command:', s.join(command))

    popen = subprocess.Popen(command, stdout=subprocess.PIPE)

    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #debugPrint('line', line.rstrip('\n'))
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['new'].append(filename)
            # worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            # fileIndex += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['updated'].append(filename)
            # worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            # fileIndex += 1
            
        if worker.stop:
            debugPrint("Stopping")
            break

    files['new'] = [os.path.join(baseDir,filename) for filename in files['new']]
    files['updated'] = [os.path.join(baseDir,filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return files


def transfer_sshDestDir(worker, job):

    debugPrint("Transfer from SSH Server")

    filters = {'includeFilter': '*','excludeFilter': '','ignoreFilter': ''}

    baseDir = worker.shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir']
    cruiseDir = os.path.join(baseDir, worker.cruiseID)
    
    sourceDir = cruiseDir
    destDir = worker.cruiseDataTransfer['destDir'].rstrip('/')
    
    debugPrint("Source Dir:", sourceDir)
    debugPrint("Destinstation Dir:", destDir)

    debugPrint("Build file list")
    #files = build_filelist(worker, sourceDir)
    files = {'include':[], 'exclude':[], 'new':[], 'updated':[]}
    excludeList = build_excludeList(worker)
        
    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    sshExcludeListPath = os.path.join(tmpdir, 'sshExcludeList.txt')
    
    # fileIndex = 0
    # fileCount = len(files['include'])

    try:
        sshExcludeListFile = open(sshExcludeListPath, 'w')
        sshExcludeListFile.write('\n'.join([str(x) for x in excludeList]))
        debugPrint('\n'.join([str(x) for x in excludeList]))

    except IOError:
        errPrint("Error Saving temporary ssh filelist file")
        sshExcludeListFile.close()
            
        # Cleanup
        shutil.rmtree(tmpdir)
            
        return False

    finally:
        sshExcludeListFile.close()

    bandwidthLimit = '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    if worker.cruiseDataTransfer['bandwidthLimit'] != '0':
        bandwidthLimit = '--bwlimit=' + worker.cruiseDataTransfer['bandwidthLimit']
    
    command = ''

    if worker.cruiseDataTransfer['sshUseKey'] == '1':
        command = ['ssh', worker.cruiseDataTransfer['sshServer'], '-l', worker.cruiseDataTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', 'PasswordAuthentication=no', 'mkdir ' + os.path.join(destDir, worker.cruiseID)]
    else:
        command = ['sshpass', '-p', worker.cruiseDataTransfer['sshPass'], 'ssh', worker.cruiseDataTransfer['sshServer'], '-l', worker.cruiseDataTransfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PubkeyAuthentication=no', 'mkdir ' + os.path.join(destDir, worker.cruiseID)]

    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    proc.communicate()

    if worker.cruiseDataTransfer['sshUseKey'] == '1':
        command = ['rsync', '-tri', bandwidthLimit, '--exclude-from=' + sshExcludeListPath, '-e', 'ssh', cruiseDir + '/', worker.cruiseDataTransfer['sshUser'] + '@' + worker.cruiseDataTransfer['sshServer'] + ':' + os.path.join(destDir, worker.cruiseID)]
        #command = ['rsync', '-tri',                '--files-from=' + sshExcludeListPath, '-e', 'ssh', baseDir, worker.cruiseDataTransfer['sshUser'] + '@' + worker.cruiseDataTransfer['sshServer'] + ':' + destDir]        
    else:
        command = ['sshpass', '-p', worker.cruiseDataTransfer['sshPass'], 'rsync', '-tri', bandwidthLimit, '--exclude-from=' + sshExcludeListPath, '-e', 'ssh', cruiseDir + '/', worker.cruiseDataTransfer['sshUser'] + '@' + worker.cruiseDataTransfer['sshServer'] + ':' + os.path.join(destDir, worker.cruiseID)]
        #command = ['sshpass', '-p', worker.cruiseDataTransfer['sshPass'], 'rsync', '-tri',                '--files-from=' + sshFileListPath, '-e', 'ssh', baseDir, worker.cruiseDataTransfer['sshUser'] + '@' + worker.cruiseDataTransfer['sshServer'] + ':' + destDir]
    
    s = ' '
    debugPrint('Transfer Command:',s.join(command))
    
    popen = subprocess.Popen(command, stdout=subprocess.PIPE)
   
    lines_iterator = iter(popen.stdout.readline, b"")
    for line in lines_iterator:
        #debugPrint('line', line.rstrip('\n'))
        if line.startswith( '<f+++++++++' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['new'].append(filename)
            # worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            # fileIndex += 1
        elif line.startswith( '<f.' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['updated'].append(filename)
            # worker.send_job_status(job, int(20 + 70*float(fileIndex)/float(fileCount)), 100)
            # fileIndex += 1
            
        if worker.stop:
            debugPrint("Stopping")
            break

    files['new'] = [os.path.join('/', worker.cruiseID, filename) for filename in files['new']]
    files['updated'] = [os.path.join('/', worker.cruiseID, filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return files
    
        
class OVDMGearmanWorker(gearman.GearmanWorker):

    def __init__(self):
        self.stop = False
        self.quit = False
        self.OVDM = openvdm.OpenVDM()
        self.cruiseID = ''
        self.loweringID = ''
        self.systemStatus = ''
        self.cruiseDataTransfer = {}
        self.shipboardDataWarehouseConfig = {}
        super(OVDMGearmanWorker, self).__init__(host_list=[self.OVDM.getGearmanServer()])
        
        
    def on_job_execute(self, current_job):
        payloadObj = json.loads(current_job.data)
        self.shipboardDataWarehouseConfig = self.OVDM.getShipboardDataWarehouseConfig()
        self.cruiseDataTransfer = self.OVDM.getCruiseDataTransfer(payloadObj['cruiseDataTransfer']['cruiseDataTransferID'])
        self.cruiseDataTransfer.update(payloadObj['cruiseDataTransfer'])
        
        self.cruiseID = self.OVDM.getCruiseID()
        self.loweringID = self.OVDM.getLoweringID()
        self.systemStatus = self.OVDM.getSystemStatus()
        if len(payloadObj) > 0:
            try:
                payloadObj['cruiseID']
            except KeyError:
                self.cruiseID = self.OVDM.getCruiseID()
            else:
                self.cruiseID = payloadObj['cruiseID']

            try:
                payloadObj['loweringID']
            except KeyError:
                self.loweringID = self.OVDM.getLoweringID()
            else:
                self.loweringID = payloadObj['loweringID']

            try:
                payloadObj['systemStatus']
            except KeyError:
                self.systemStatus = self.OVDM.getSystemStatus()
            else:
                self.systemStatus = payloadObj['systemStatus']

        errPrint("Job:", current_job.handle + ",", self.cruiseDataTransfer['name'], "transfer started at:  ", time.strftime("%D %T", time.gmtime()))
        
        return super(OVDMGearmanWorker, self).on_job_execute(current_job)

    
    def on_job_exception(self, current_job, exc_info):
        errPrint("Job:", current_job.handle + ",", self.cruiseDataTransfer['name'], "transfer failed at:  ", time.strftime("%D %T", time.gmtime()))
        
        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail", 'reason': 'Unknown'}]))
        self.OVDM.setError_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'], 'Worker crashed')
        
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        errPrint(exc_type, fname, exc_tb.tb_lineno)
        return super(OVDMGearmanWorker, self).on_job_exception(current_job, exc_info)

    
    def on_job_complete(self, current_job, job_results):
        resultsObj = json.loads(job_results)
        
        # If the last part of the results failed
        if len(resultsObj['parts']) > 0:
            if resultsObj['parts'][-1]['result'] == "Fail": # Final Verdict
                if resultsObj['parts'][-1]['partName'] != "Transfer In-Progress" and resultsObj['parts'][-1]['partName'] != "Transfer Enabled": # A failed Transfer in-progress or Transfer enabled test should not cause an error.
                    self.OVDM.setError_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'], resultsObj['parts'][-1]['reason'])
            else: # last test passed
                self.OVDM.setIdle_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'])
        else: # there were no results
            self.OVDM.setIdle_cruiseDataTransfer(self.cruiseDataTransfer['cruiseDataTransferID'])

        debugPrint('Job Results:', json.dumps(resultsObj, indent=2))

        errPrint("Job:", current_job.handle + ",", self.cruiseDataTransfer['name'], "transfer completed at:  ", time.strftime("%D %T", time.gmtime()))
            
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

        
        
def task_runCruiseDataTransfer(worker, job):

    time.sleep(randint(0,2))
    
    job_results = {'parts':[], 'files':[]}

    if worker.cruiseDataTransfer['enable'] == "1" and worker.systemStatus == "On":
        debugPrint("Transfer Enabled")
        job_results['parts'].append({"partName": "Transfer Enabled", "result": "Pass"})
    else:
        debugPrint("Transfer Disabled")
        job_results['parts'].append({"partName": "Transfer Enabled", "result": "Fail", "reason": "Transfer is disabled"})
        return json.dumps(job_results)

    if worker.cruiseDataTransfer['status'] == "1": #running
        debugPrint("Transfer is already in-progress")
        job_results['parts'].append({"partName": "Transfer In-Progress", "result": "Fail", "reason": "Transfer is already in-progress"})
        return json.dumps(job_results)
    else: #not running
        debugPrint("Transfer is not already in-progress")
        job_results['parts'].append({"partName": "Transfer In-Progress", "result": "Pass"})

    #debugPrint("Set transfer status to 'Running'")
    worker.OVDM.setRunning_cruiseDataTransfer(worker.cruiseDataTransfer['cruiseDataTransferID'], os.getpid(), job.handle)
   
    debugPrint("Testing configuration")
    worker.send_job_status(job, 1, 10)

    gm_client = gearman.GearmanClient([worker.OVDM.getGearmanServer()])
    
    gmData = {}
    gmData['cruiseDataTransfer'] = worker.cruiseDataTransfer
    gmData['cruiseID'] = worker.cruiseID
    
    completed_job_request = gm_client.submit_job("testCruiseDataTransfer", json.dumps(gmData))
    resultsObj = json.loads(completed_job_request.result)

    debugPrint('Connection Test Results:', json.dumps(resultsObj, indent=2))

    if resultsObj['parts'][-1]['result'] == "Pass": # Final Verdict
        debugPrint("Connection Test: Passed")
        job_results['parts'].append({'partName': 'Connection Test', 'result': 'Pass'})
    else:
        debugPrint("Connection Test: Failed")
        job_results['parts'].append({'partName': 'Connection Test', 'result': 'Fail', 'reason': resultsObj['parts'][-1]['reason']})

    worker.send_job_status(job, 2, 10)
    
    debugPrint("Start Transfer")
    if worker.cruiseDataTransfer['transferType'] == "1": # Local Directory
        job_results['files'] = transfer_localDestDir(worker, job)
    elif  worker.cruiseDataTransfer['transferType'] == "2": # Rsync Server
        job_results['files'] = transfer_rsyncDestDir(worker, job)
    elif  worker.cruiseDataTransfer['transferType'] == "3": # SMB Server
        job_results['files'] = transfer_smbDestDir(worker, job)
    elif  worker.cruiseDataTransfer['transferType'] == "4": # SSH Server
        job_results['files'] = transfer_sshDestDir(worker, job)
    
    debugPrint("Transfer Complete")
    if len(job_results['files']['new']) > 0:
        debugPrint(len(job_results['files']['new']), 'file(s) added')
    if len(job_results['files']['updated']) > 0:
        debugPrint(len(job_results['files']['updated']), 'file(s) updated')
    if len(job_results['files']['exclude']) > 0:
        debugPrint(len(job_results['files']['exclude']), 'file(s) intentionally skipped')

    job_results['parts'].append({"partName": "Transfer Files", "result": "Pass"})

    worker.send_job_status(job, 9, 10)

    time.sleep(2)

    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Main function of the script should it be run as a stand-alone utility.
# -------------------------------------------------------------------------------------
def main(argv):

    parser = argparse.ArgumentParser(description='Handle cruise data transfer related tasks')
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

    new_worker.set_client_id('runCruiseDataTransfer.py')

    debugPrint('Registering worker tasks...')
    debugPrint('   Task:', 'runCruiseDataTransfer')
    new_worker.register_task("runCruiseDataTransfer", task_runCruiseDataTransfer)

    debugPrint('Waiting for jobs...')
    new_worker.work()


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])
