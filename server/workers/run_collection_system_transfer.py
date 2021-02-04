#!/usr/bin/env python3
"""

FILE:  run_collection_system_transfer.py

DESCRIPTION:  Gearman worker that handles the transfer of data from the Collection
    System to the Shipboard Data Warehouse.

     BUGS:
    NOTES:
   AUTHOR:  Webb Pinner
  COMPANY:  Capable Solutions
  VERSION:  2.5
  CREATED:  2015-01-01
 REVISION:  2021-01-02

LICENSE INFO: Open Vessel Data Management v2.5 (OpenVDMv2)
Copyright (C) OceanDataRat.org 2021

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/gpl-3.0.html>.

"""

import argparse
import os
import sys
import tempfile
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
import python3_gearman

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.utils.check_filenames import is_ascii
from server.utils.output_json_data_to_file import output_json_data_to_file
from server.utils.set_owner_group_permissions import set_owner_group_permissions
from server.lib.openvdm import OpenVDM


def build_filelist(gearman_worker, source_dir): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """
    Build the list of files to include, exclude or ignore
    """

    return_files = {'include':[], 'exclude':[], 'new':[], 'updated':[], 'filesize':[]}

    staleness = int(gearman_worker.collection_system_transfer['staleness']) * 60 #5 Mintues
    logging.debug("Staleness: %s", staleness)

    threshold_time = time.time() - staleness
    logging.debug("Threshold: %s", threshold_time)

    data_start_time = calendar.timegm(time.strptime(gearman_worker.data_start_date, "%Y/%m/%d %H:%M"))
    logging.debug("Start: %s", data_start_time)

    data_end_time = calendar.timegm(time.strptime(gearman_worker.dataEndDate, "%Y/%m/%d %H:%M"))
    logging.debug("End: %s", data_end_time)

    filters = build_filters(gearman_worker)

    for root, _, filenames in os.walk(source_dir): # pylint: disable=too-many-nested-blocks
        for filename in filenames:
            filepath = os.path.join(root, filename)

            if os.path.islink(filepath):
                logging.debug("%s is a symlink, skipping", filepath)
                continue

            exclude = False
            ignore = False
            include = False
            for ignore_filter in filters['ignoreFilter'].split(','):
                #logging.debug(ignore_filter)
                if fnmatch.fnmatch(filepath, ignore_filter):
                    logging.debug("%s ignored by ignore filter", filepath)
                    ignore = True
                    break

            if ignore:
                continue

            if not is_ascii(filename):
                logging.debug("%s is not an ascii-encoded unicode string", filepath)
                return_files['exclude'].append(filepath)
                exclude = True
                continue

            for include_filter in filters['includeFilter'].split(','):
                if fnmatch.fnmatch(filepath, include_filter):
                    for exclude_filter in filters['excludeFilter'].split(','):
                        if fnmatch.fnmatch(filepath, exclude_filter):
                            logging.debug("%s excluded by exclude filter", filepath)
                            return_files['exclude'].append(filepath)
                            exclude = True
                            break

                    if exclude:
                        break

                    file_mod_time = os.stat(filepath).st_mtime
                    logging.debug("file_mod_time: %s", file_mod_time)

                    if file_mod_time < data_start_time or file_mod_time > data_end_time:
                        logging.debug("%s ignored for time reasons", filepath)
                        ignore = True
                        break

                    logging.debug("%s is a valid file for transfer", filepath)
                    include = True
                    break

            if include:
                return_files['include'].append(filepath)
                return_files['filesize'].append(os.stat(filepath).st_size)

            elif not exclude:
                logging.debug("%s excluded because file does not match any of the filters", filepath)
                return_files['exclude'].append(filepath)

    if not gearman_worker.collection_system_transfer['staleness'] == '0':
        logging.debug("Checking for changing filesizes")
        time.sleep(5)
        for idx, filepath in enumerate(return_files['include']):
            if not os.stat(filepath).st_size == return_files['filesize'][idx]:
                logging.debug("file %s has changed size, removing from include list", filepath)
                del return_files['include'][idx]
                del return_files['filesize'][idx]

    del return_files['filesize']

    return_files['include'] = [filename.split(source_dir + '/',1).pop() for filename in return_files['include']]
    return_files['exclude'] = [filename.split(source_dir + '/',1).pop() for filename in return_files['exclude']]

    return {'verdict': True, 'files': return_files}


def build_rsync_filelist(gearman_worker, source_dir): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """
    Build the list of files to include, exclude or ignore, for an rsync server
    transfer
    """

    return_files = {'include':[], 'exclude':[], 'new':[], 'updated':[], 'filesize':[]}

    staleness = int(gearman_worker.collection_system_transfer['staleness']) * 60
    threshold_time = time.time() - staleness # 5 minutes
    epoch = datetime.datetime.strptime('1970/01/01 00:00:00', "%Y/%m/%d %H:%M:%S")
    data_start_time = calendar.timegm(time.strptime(gearman_worker.data_start_date, "%Y/%m/%d %H:%M"))
    data_end_time = calendar.timegm(time.strptime(gearman_worker.dataEndDate, "%Y/%m/%d %H:%M"))

    logging.debug("Threshold: %s", threshold_time)
    logging.debug("    Start: %s", data_start_time)
    logging.debug("      End: %s", data_end_time)

    filters = build_filters(gearman_worker)

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsync_password_filepath = os.path.join(tmpdir, 'passwordFile')

    try:
        with open(rsync_password_filepath, 'w') as rsync_password_file:
            rsync_password_file.write(gearman_worker.collection_system_transfer['rsyncPass'])
        os.chmod(rsync_password_filepath, 0o600)

    except IOError:
        logging.error("Error Saving temporary rsync password file")

        # Cleanup
        shutil.rmtree(tmpdir)

        return {'verdict': False, 'reason': 'Error Saving temporary rsync password file: ' + rsync_password_filepath}

    command = ['rsync', '-r', '--password-file=' + rsync_password_filepath, '--no-motd', 'rsync://' + gearman_worker.collection_system_transfer['rsyncUser'] + '@' + gearman_worker.collection_system_transfer['rsyncServer'] + source_dir + '/']

    logging.debug("Command: %s", ' '.join(command))

    proc = subprocess.run(command, capture_output=True, text=True, check=False)

    logging.debug("proc.stdout: %s", proc.stdout)

    for line in proc.stdout.splitlines(): # pylint: disable=too-many-nested-blocks
        logging.debug('line: %s', line.rstrip('\n'))
        file_or_dir, size, mdate, mtime, filepath = line.split(None, 4)
        if file_or_dir.startswith('-'):
            exclude = False
            ignore = False
            include = False
            for ignore_filter in filters['ignoreFilter'].split(','):
                #logging.debug("ignore_filter")
                if fnmatch.fnmatch(filepath, ignore_filter):
                    logging.debug("%s ignored because file matched ignore filter", filepath)
                    ignore = True
                    break

            if ignore:
                continue

            if not is_ascii(filepath):
                logging.debug("%s is not an ascii-encoded unicode string", filepath)
                return_files['exclude'].append(filepath)
                exclude = True
                continue

            for include_filter in filters['includeFilter'].split(','):
                if fnmatch.fnmatch(filepath, include_filter):
                    for exclude_filter in filters['excludeFilter'].split(','):
                        if fnmatch.fnmatch(filepath, exclude_filter):
                            logging.debug("%s excluded because file matches exclude filter", filepath)
                            return_files['exclude'].append(filepath)
                            exclude = True
                            break

                    if exclude:
                        break

                    file_mod_time = datetime.datetime.strptime(mdate + ' ' + mtime, "%Y/%m/%d %H:%M:%S")
                    file_mod_time_seconds = (file_mod_time - epoch).total_seconds()
                    logging.debug("file_mod_time_seconds: %s", file_mod_time_seconds)
                    if file_mod_time_seconds > data_start_time and file_mod_time_seconds < threshold_time and file_mod_time_seconds < data_end_time:  # pylint: disable=chained-comparison
                        logging.debug("%s is a valid file for transfer", filepath)
                        include = True
                    else:
                        logging.debug("%s ignored for time reasons", filepath)

            if include:
                return_files['include'].append(filepath)
                return_files['filesize'].append(size)

            elif not exclude:
                logging.debug("%s excluded because file does not match any include or ignore filters", filepath)
                return_files['exclude'].append(filepath)

    if not gearman_worker.collection_system_transfer['staleness'] == '0':
        logging.debug("Checking for changing filesizes")
        time.sleep(5)
        proc = subprocess.run(command, capture_output=True, text=True, check=False)

        for line in proc.stdout.splitlines():
            file_or_dir, size, mdate, mtime, filepath = line.split(None, 4)

            try:
                younger_file_idx = return_files['include'].index(filepath)
                if return_files['filesize'][younger_file_idx] != size:
                    logging.debug("file %s has changed size, removing from include list", filepath)
                    del return_files['filesize'][younger_file_idx]
                    del return_files['include'][younger_file_idx]
            except ValueError:
                pass
            except Exception as err:
                logging.error(str(err))

    del return_files['filesize']

    # Cleanup
    shutil.rmtree(tmpdir)

    return_files['include'] = [filename.split(source_dir + '/',1).pop() for filename in return_files['include']]
    return_files['exclude'] = [filename.split(source_dir + '/',1).pop() for filename in return_files['exclude']]

    logging.debug('return_files: %s', json.dumps(return_files, indent=2))

    return {'verdict': True, 'files': return_files}


def build_ssh_filelist(gearman_worker, source_dir): # pylint: disable=too-many-branches,too-many-statements,too-many-locals
    """
    Build the list of files to include, exclude or ignore for a ssh server
    transfer
    """

    return_files = {'include':[], 'exclude':[], 'new':[], 'updated':[], 'filesize':[]}

    staleness = int(gearman_worker.collection_system_transfer['staleness']) * 60
    threshold_time = time.time() - staleness # 5 minutes
    epoch = datetime.datetime.strptime('1970/01/01 00:00:00', "%Y/%m/%d %H:%M:%S")
    data_start_time = calendar.timegm(time.strptime(gearman_worker.data_start_date, "%Y/%m/%d %H:%M"))
    data_end_time = calendar.timegm(time.strptime(gearman_worker.dataEndDate, "%Y/%m/%d %H:%M"))

    logging.debug("Threshold: %s", threshold_time)
    logging.debug("    Start: %s", data_start_time)
    logging.debug("      End: %s", data_end_time)

    filters = build_filters(gearman_worker)

    command = ['rsync', '-r', '-e', 'ssh', gearman_worker.collection_system_transfer['sshUser'] + '@' + gearman_worker.collection_system_transfer['sshServer'] + ':' + source_dir + '/'] if gearman_worker.collection_system_transfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.collection_system_transfer['sshPass'], 'rsync', '-r', '-e', 'ssh', gearman_worker.collection_system_transfer['sshUser'] + '@' + gearman_worker.collection_system_transfer['sshServer'] + ':' + source_dir + '/']
    logging.debug("Command: %s", ' '.join(command))

    proc = subprocess.run(command, capture_output=True, text=True, check=False)

    for line in proc.stdout.splitlines(): # pylint: disable=too-many-nested-blocks
        logging.debug('line: %s', line.rstrip('\n'))
        file_or_dir, size, mdate, mtime, filepath = line.split(None, 4)
        if file_or_dir.startswith('-'):
            exclude = False
            ignore = False
            include = False
            for ignore_filter in filters['ignoreFilter'].split(','):
                #logging.debug("filt")
                if fnmatch.fnmatch(filepath, ignore_filter):
                    logging.debug("%s ignored because file matched ignore filter", filepath)
                    ignore = True
                    break

            if ignore:
                continue

            if not is_ascii(filepath):
                logging.debug("%s is not an ascii-encoded unicode string", filepath)
                return_files['exclude'].append(filepath)
                exclude = True
                continue

            for include_filter in filters['includeFilter'].split(','):
                if fnmatch.fnmatch(filepath, include_filter):
                    for exclude_filter in filters['excludeFilter'].split(','):
                        if fnmatch.fnmatch(filepath, exclude_filter):
                            logging.debug("%s excluded because file matches exclude filter", filepath)
                            return_files['exclude'].append(filepath)
                            exclude = True
                            break

                    if exclude:
                        break

                    file_mod_time = datetime.datetime.strptime(mdate + ' ' + mtime, "%Y/%m/%d %H:%M:%S")
                    file_mod_time_seconds = (file_mod_time - epoch).total_seconds()
                    logging.debug("file_mod_time_seconds: %s", file_mod_time_seconds)
                    if file_mod_time_seconds > data_start_time and file_mod_time_seconds < threshold_time and file_mod_time_seconds < data_end_time: # pylint: disable=chained-comparison
                        logging.debug("%s is a valid file for transfer", filepath)
                        include = True
                    else:
                        logging.debug("%s ignored for time reasons", filepath)

            if include:
                return_files['include'].append(filepath)
                return_files['filesize'].append(size)

            elif not exclude:
                logging.debug("%s excluded because file does not match any include or ignore filters", filepath)
                return_files['exclude'].append(filepath)

    if not gearman_worker.collection_system_transfer['staleness'] == '0':
        logging.debug("Checking for changing filesizes")
        time.sleep(5)
        proc = subprocess.run(command, capture_output=True, text=True, check=False)

        for line in proc.stdout.splitlines():
            file_or_dir, size, mdate, mtime, filepath = line.split(None, 4)

            try:
                younger_file_idx = return_files['include'].index(filepath)
                if return_files['filesize'][younger_file_idx] != size:
                    logging.debug("file %s has changed size, removing from include list", filepath)
                    del return_files['filesize'][younger_file_idx]
                    del return_files['include'][younger_file_idx]
            except ValueError:
                pass
            except Exception as err:
                logging.error(str(err))

    del return_files['filesize']

    return_files['include'] = [filename.split(source_dir + '/',1).pop() for filename in return_files['include']]
    return_files['exclude'] = [filename.split(source_dir + '/',1).pop() for filename in return_files['exclude']]

    logging.debug('return_files: %s', json.dumps(return_files, indent=2))

    return {'verdict': True, 'files': return_files}


def build_filters(gearman_worker):
    """
    Replace wildcard string in filters
    """
    return {
        'includeFilter': gearman_worker.collection_system_transfer['includeFilter'].replace('{cruiseID}', gearman_worker.cruise_id).replace('{loweringID}', gearman_worker.lowering_id),
        'excludeFilter': gearman_worker.collection_system_transfer['excludeFilter'].replace('{cruiseID}', gearman_worker.cruise_id).replace('{loweringID}', gearman_worker.lowering_id),
        'ignoreFilter': gearman_worker.collection_system_transfer['ignoreFilter'].replace('{cruiseID}', gearman_worker.cruise_id).replace('{loweringID}', gearman_worker.lowering_id)
    }


def build_dest_dir(gearman_worker):
    """
    Replace wildcard string in destDir
    """

    return gearman_worker.collection_system_transfer['destDir'].replace('{cruiseID}', gearman_worker.cruise_id).replace('{loweringID}', gearman_worker.lowering_id).replace('{loweringDataBaseDir}', gearman_worker.shipboard_data_warehouse_config['loweringDataBaseDir']).rstrip('/')


def build_source_dir(gearman_worker):
    """
    Replace wildcard string in sourceDir
    """

    return gearman_worker.collection_system_transfer['sourceDir'].replace('{cruiseID}', gearman_worker.cruise_id).replace('{loweringID}', gearman_worker.lowering_id).replace('{loweringDataBaseDir}', gearman_worker.shipboard_data_warehouse_config['loweringDataBaseDir']).rstrip('/')


def build_logfile_dirpath(gearman_worker):
    """
    build the path to save transfer logfiles
    """

    cruise_dir = os.path.join(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], gearman_worker.cruise_id)
    return os.path.join(cruise_dir, gearman_worker.ovdm.get_required_extra_directory_by_name('Transfer_Logs')['destDir'])


def transfer_local_source_dir(gearman_worker, gearman_job): # pylint: disable=too-many-locals,too-many-statements
    """
    Preform a collection system transfer from a local directory
    """

    logging.debug("Transfer from Local Directory")

    cruise_dir = os.path.join(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], gearman_worker.cruise_id)

    if gearman_worker.collection_system_transfer['cruiseOrLowering'] == "1":
        dest_dir = os.path.join(cruise_dir, gearman_worker.shipboard_data_warehouse_config['loweringDataBaseDir'], gearman_worker.lowering_id, build_dest_dir(gearman_worker))
    else:
        dest_dir = os.path.join(cruise_dir, build_dest_dir(gearman_worker))

    source_dir = build_source_dir(gearman_worker)
    logging.debug("Source Dir: %s", source_dir)
    logging.debug("Destination Dir: %s", dest_dir)

    logging.debug("Build file list")
    output_results = build_filelist(gearman_worker, source_dir)
    if not output_results['verdict']:
        return { 'verdict': False, 'reason': "Error building filelist", 'files':[] }
    files = output_results['files']

    logging.debug("Files: %s", json.dumps(files['include'], indent=2))

    file_index = 0
    file_count = len(files['include'])

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsync_filelist_filepath = os.path.join(tmpdir, 'rsyncFileList.txt')

    logging.debug("Mod file list")
    local_transfer_filelist = files['include']
    local_transfer_filelist = [filename.replace(source_dir, '', 1) for filename in local_transfer_filelist]

    logging.debug("Start")
    try:
        with open(rsync_filelist_filepath, 'w') as rsync_filelist_file:
            for file in local_transfer_filelist:
                try:
                    rsync_filelist_file.write(str(file) + '\n')
                except Exception as err:
                    logging.warning("File not ascii: %s", file)
                    logging.debug(str(err))

    except IOError:
        logging.error("Error Saving temporary rsync filelist file %s", rsync_filelist_filepath)

        # Cleanup
        shutil.rmtree(tmpdir)
        return {'verdict': False, 'reason': 'Error Saving temporary rsync filelist file: ' + rsync_filelist_filepath, 'files': []}

    logging.debug("Done")

    bandwidth_limit = '--bwlimit=' + gearman_worker.collection_system_transfer['bandwidthLimit'] if gearman_worker.collection_system_transfer['bandwidthLimit'] != '0' else '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    command = ['rsync', '-tri', bandwidth_limit, '--files-from=' + rsync_filelist_filepath, source_dir + '/', dest_dir]

    logging.debug('Transfer Command: %s', ' '.join(command))

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)
    while True:

        line = proc.stdout.readline().rstrip('\n')

        if proc.poll() is not None:
            break

        if not line:
            continue

        logging.debug("Line: %s", line)
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1]
            files['new'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(file_index)/float(file_count)), 100)
            file_index += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1]
            files['updated'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(file_index)/float(file_count)), 100)
            file_index += 1

        if gearman_worker.stop:
            logging.debug("Stopping")
            proc.terminate()
            break

    files['new'] = [os.path.join(dest_dir.replace(cruise_dir, '').lstrip('/'), filename) for filename in files['new']]
    files['updated'] = [os.path.join(dest_dir.replace(cruise_dir, '').lstrip('/'), filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return {'verdict': True, 'files': files}


def transfer_smb_source_dir(gearman_worker, gearman_job): # pylint: disable=too-many-locals,too-many-statements
    """
    Preform a collection system transfer from a samba server
    """

    logging.debug("Transfer from SMB Source")

    cruise_dir = os.path.join(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], gearman_worker.cruise_id)

    # filters = build_filters(gearman_worker)

    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    # Create mountpoint
    mntpoint = os.path.join(tmpdir, 'mntpoint')
    os.mkdir(mntpoint, 0o755)

    dest_dir = os.path.join(cruise_dir, gearman_worker.shipboard_data_warehouse_config['loweringDataBaseDir'], gearman_worker.lowering_id, build_dest_dir(gearman_worker)) if gearman_worker.collection_system_transfer['cruiseOrLowering'] == "1" else  os.path.join(cruise_dir, build_dest_dir(gearman_worker))
    source_dir = os.path.join(mntpoint, build_source_dir(gearman_worker)).rstrip('/')
    logging.debug("Source Dir: %s", source_dir)
    logging.debug("Destinstation Dir: %s", dest_dir)

    # Mount SMB Share
    logging.debug("Mounting SMB Share")

    ver_test_command = ['smbclient', '-L', gearman_worker.collection_system_transfer['smbServer'], '-W', gearman_worker.collection_system_transfer['smbDomain'], '-m', 'SMB2', '-g', '-N'] if gearman_worker.collection_system_transfer['smbUser'] == 'guest' else ['smbclient', '-L', gearman_worker.collection_system_transfer['smbServer'], '-W', gearman_worker.collection_system_transfer['smbDomain'], '-m', 'SMB2', '-g', '-U', gearman_worker.collection_system_transfer['smbUser'] + '%' + gearman_worker.collection_system_transfer['smbPass']]
    logging.debug("SMB version test command: %s", ' '.join(ver_test_command))

    vers="2.1"
    proc = subprocess.run(ver_test_command, capture_output=True, text=True, check=False)

    for line in proc.stdout.splitlines():
        if line.startswith('OS=[Windows 5.1]'):
            vers="1.0"
            break

    mount_command = ['sudo', 'mount', '-t', 'cifs', gearman_worker.collection_system_transfer['smbServer'], mntpoint, '-o', 'ro' + ',guest' + ',domain=' + gearman_worker.collection_system_transfer['smbDomain'] + ',vers=' + vers] if gearman_worker.collection_system_transfer['smbUser'] == 'guest' else ['sudo', 'mount', '-t', 'cifs', gearman_worker.collection_system_transfer['smbServer'], mntpoint, '-o', 'ro' + ',username=' + gearman_worker.collection_system_transfer['smbUser'] + ',password=' + gearman_worker.collection_system_transfer['smbPass'] + ',domain=' + gearman_worker.collection_system_transfer['smbDomain'] + ',vers=' + vers]
    logging.debug("Mount command: %s", ' '.join(mount_command))

    proc = subprocess.call(mount_command)

    logging.debug("Build file list")
    output_results = build_filelist(gearman_worker, source_dir)
    if not output_results['verdict']:
        return { 'verdict': False, 'reason': "Error building filelist", 'files':[] }
    files = output_results['files']

    logging.debug("File List: %s", json.dumps(files['include'], indent=2))

    file_index = 0
    file_count = len(files['include'])

    rsync_filelist_filepath = os.path.join(tmpdir, 'rsyncFileList.txt')

    try:
        with open(rsync_filelist_filepath, 'w') as rsync_filelist_file:
            rsync_filelist_file.write('\n'.join(files['include']))

    except IOError:
        logging.error("Error Saving temporary rsync filelist file")

        # Cleanup
        time.sleep(2)
        subprocess.call(['umount', mntpoint])
        shutil.rmtree(tmpdir)

        return {'verdict': False, 'reason': 'Error Saving temporary rsync filelist file: ' + rsync_filelist_filepath, 'files': []}

    bandwidth_limit = '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    if gearman_worker.collection_system_transfer['bandwidthLimit'] != '0':
        bandwidth_limit = '--bwlimit=' + gearman_worker.collection_system_transfer['bandwidthLimit']

    command = ['rsync', '-trim', bandwidth_limit, '--files-from=' + rsync_filelist_filepath, source_dir, dest_dir]

    logging.debug("Transfer Command: %s", ' '.join(command))

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)

    while True:

        line = proc.stdout.readline().rstrip('\n')

        if proc.poll() is not None:
            break

        if not line:
            continue

        logging.debug('line %s', line)
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['new'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(file_index)/float(file_count)), 100)
            file_index += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1].rstrip('\n')
            files['updated'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(file_index)/float(file_count)), 100)
            file_index += 1

        if gearman_worker.stop:
            logging.debug("Stopping")
            proc.terminate()
            break

    files['new'] = [os.path.join(dest_dir.replace(cruise_dir, '').lstrip('/').rstrip('/'),filename) for filename in files['new']]
    files['updated'] = [os.path.join(dest_dir.replace(cruise_dir, '').lstrip('/').rstrip('/'),filename) for filename in files['updated']]

    # Cleanup
    time.sleep(2)
    logging.debug('Unmounting SMB Share')
    subprocess.call(['umount', mntpoint])
    shutil.rmtree(tmpdir)

    return {'verdict': True, 'files': files}

def transfer_rsync_source_dir(gearman_worker, gearman_job): # pylint: disable=too-many-locals,too-many-statements
    """
    Preform a collection system transfer from a rsync server
    """

    logging.debug("Transfer from RSYNC Server")

    cruise_dir = os.path.join(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], gearman_worker.cruise_id)

    dest_dir = os.path.join(cruise_dir, gearman_worker.shipboard_data_warehouse_config['loweringDataBaseDir'], gearman_worker.lowering_id, build_dest_dir(gearman_worker)) if gearman_worker.collection_system_transfer['cruiseOrLowering'] == "1" else os.path.join(cruise_dir, build_dest_dir(gearman_worker))

    source_dir = build_source_dir(gearman_worker)

    logging.debug("Source Dir: %s", source_dir)
    logging.debug("Destinstation Dir: %s", dest_dir)

    logging.debug("Build file list")
    output_results = build_rsync_filelist(gearman_worker, source_dir)

    if not output_results['verdict']:
        return {'verdict': False, 'reason': output_results['reason'], 'files':[]}

    files = output_results['files']

    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    file_index = 0
    file_count = len(files['include'])

    rsync_password_filepath = os.path.join(tmpdir, 'passwordFile')

    try:
        with open(rsync_password_filepath, 'w') as rsync_password_file:
            rsync_password_file.write(gearman_worker.collection_system_transfer['rsyncPass'])

        os.chmod(rsync_password_filepath, 0o600)

    except IOError:
        logging.error("Error Saving temporary rsync password file")
        rsync_password_file.close()

        # Cleanup
        shutil.rmtree(tmpdir)

        return {'verdict': False, 'reason': 'Error Saving temporary rsync password file: ' + rsync_password_filepath}

    rsync_filelist_filepath = os.path.join(tmpdir, 'rsyncFileList.txt')

    try:
        with open(rsync_filelist_filepath, 'w') as rsync_filelist_file:
            rsync_filelist_file.write('\n'.join(files['include']))

    except IOError:
        logging.error("Error Saving temporary rsync filelist file")

        # Cleanup
        shutil.rmtree(tmpdir)

        return {'verdict': False, 'reason': 'Error Saving temporary rsync filelist file: ' + rsync_filelist_filepath, 'files':[]}

    bandwidth_limit = '--bwlimit=' + gearman_worker.collection_system_transfer['bandwidthLimit'] if gearman_worker.collection_system_transfer['bandwidthLimit'] != '0' else '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    command = ['rsync', '-tri', bandwidth_limit, '--no-motd', '--files-from=' + rsync_filelist_filepath, '--password-file=' + rsync_password_filepath, 'rsync://' + gearman_worker.collection_system_transfer['rsyncUser'] + '@' + gearman_worker.collection_system_transfer['rsyncServer'] + source_dir, dest_dir]

    logging.debug('Transfer Command: %s', ' '.join(command))

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)

    while True:

        line = proc.stdout.readline().rstrip('\n')

        if proc.poll() is not None:
            break

        if not line:
            continue

        logging.debug('Line: %s', line)
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1]
            files['new'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(file_index)/float(file_count)), 100)
            file_index += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1]
            files['updated'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(file_index)/float(file_count)), 100)
            file_index += 1

        if gearman_worker.stop:
            logging.debug("Stopping")
            proc.terminate()
            break

    files['new'] = [os.path.join(dest_dir.replace(cruise_dir, '').lstrip('/').rstrip('/'),filename) for filename in files['new']]
    files['updated'] = [os.path.join(dest_dir.replace(cruise_dir, '').lstrip('/').rstrip('/'),filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return {'verdict': True, 'files': files}


def transfer_ssh_source_dir(gearman_worker, gearman_job): # pylint: disable=too-many-locals
    """
    Preform a collection system transfer from a ssh server
    """

    logging.debug("Transfer from SSH Server")

    cruise_dir = os.path.join(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], gearman_worker.cruise_id)

    dest_dir = os.path.join(cruise_dir, gearman_worker.shipboard_data_warehouse_config['loweringDataBaseDir'], gearman_worker.lowering_id, build_dest_dir(gearman_worker)) if gearman_worker.collection_system_transfer['cruiseOrLowering'] == "1" else os.path.join(cruise_dir, build_dest_dir(gearman_worker))

    source_dir = build_source_dir(gearman_worker)

    logging.debug("Source Dir: %s", source_dir)
    logging.debug("Destinstation Dir: %s", dest_dir)

    logging.debug("Build file list")
    output_results = build_ssh_filelist(gearman_worker, source_dir)
    if not output_results['verdict']:
        return {'verdict': False, 'reason': output_results['reason'], 'files':[]}

    files = output_results['files']

    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    ssh_filelist_filepath = os.path.join(tmpdir, 'sshFileList.txt')

    file_index = 0
    file_count = len(files['include'])

    try:
        with open(ssh_filelist_filepath, 'w') as ssh_filelist_file:
            ssh_filelist_file.write('\n'.join(files['include']))

    except IOError:
        logging.debug("Error Saving temporary ssh filelist file")

        # Cleanup
        shutil.rmtree(tmpdir)

        return {'verdict': False, 'reason': 'Error Saving temporary rsync filelist file: ' + ssh_filelist_filepath, 'files':[]}

    bandwidth_limit = '--bwlimit=' + gearman_worker.collection_system_transfer['bandwidthLimit'] if gearman_worker.collection_system_transfer['bandwidthLimit'] != '0' else '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    command = ['rsync', '-tri', bandwidth_limit, '--files-from=' + ssh_filelist_filepath, '-e', 'ssh', gearman_worker.collection_system_transfer['sshUser'] + '@' + gearman_worker.collection_system_transfer['sshServer'] + ':' + source_dir, dest_dir] if gearman_worker.collection_system_transfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.collection_system_transfer['sshPass'], 'rsync', '-tri', bandwidth_limit, '--files-from=' + ssh_filelist_filepath, '-e', 'ssh', gearman_worker.collection_system_transfer['sshUser'] + '@' + gearman_worker.collection_system_transfer['sshServer'] + ':' + source_dir, dest_dir]

    logging.debug("Transfer Command: %s", ' '.join(command))

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)

    while True:

        line = proc.stdout.readline().rstrip('\n')

        if proc.poll() is not None:
            break

        if not line:
            continue

        logging.debug("Line: %s", line)
        if line.startswith( '>f+++++++++' ):
            filename = line.split(' ',1)[1]
            files['new'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(file_index)/float(file_count)), 100)
            file_index += 1
        elif line.startswith( '>f.' ):
            filename = line.split(' ',1)[1]
            files['updated'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(file_index)/float(file_count)), 100)
            file_index += 1

        if gearman_worker.stop:
            logging.debug("Stopping")
            proc.terminate()
            break

    files['new'] = [os.path.join(dest_dir.replace(cruise_dir, '').lstrip('/').rstrip('/'),filename) for filename in files['new']]
    files['updated'] = [os.path.join(dest_dir.replace(cruise_dir, '').lstrip('/').rstrip('/'),filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return {'verdict': True, 'files': files}


class OVDMGearmanWorker(python3_gearman.GearmanWorker):  # pylint: disable=too-many-instance-attributes
    """
    Class for the current Gearman worker
    """

    def __init__(self):
        self.stop = False
        self.ovdm = OpenVDM()
        self.transfer_start_date = None
        self.cruise_id = self.ovdm.get_cruise_id()
        self.lowering_id = self.ovdm.get_lowering_id()
        self.data_start_date = None
        self.data_end_date = None
        self.system_status = self.ovdm.get_system_status()
        self.collection_system_transfer = {}
        self.shipboard_data_warehouse_config = self.ovdm.get_shipboard_data_warehouse_config()
        super().__init__(host_list=[self.ovdm.get_gearman_server()])

    def on_job_execute(self, current_job):
        """
        Function run whenever a new job arrives
        """

        logging.debug("current_job: %s", current_job)

        payload_obj = json.loads(current_job.data)

        try:
            self.collection_system_transfer = self.ovdm.get_collection_system_transfer(payload_obj['collectionSystemTransfer']['collectionSystemTransferID'])

            if not self.collection_system_transfer:
                return self.on_job_complete(current_job, json.dumps({'parts':[{"partName": "Located Collection System Tranfer Data", "result": "Fail", "reason": "Could not find configuration data for collection system transfer"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

            if self.collection_system_transfer['status'] == "1": #not running
                logging.info("Transfer job for %s skipped because a transfer for that collection system is already in-progress", self.collection_system_transfer['name'])
                return self.on_job_complete(current_job, json.dumps({'parts':[{"partName": "Transfer In-Progress", "result": "Fail", "reason": "Transfer is already in-progress"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

        except Exception as err:
            logging.debug(str(err))
            return self.on_job_complete(current_job, json.dumps({'parts':[{"partName": "Located Collection System Tranfer Data", "result": "Fail", "reason": "Could not find retrieve data for collection system transfer from OpenVDM API"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

        self.system_status = payload_obj['systemStatus'] if 'systemStatus' in payload_obj else self.ovdm.get_system_status()
        self.collection_system_transfer.update(payload_obj['collectionSystemTransfer'])

        if self.system_status == "Off" or self.collection_system_transfer['enable'] == '0':
            logging.info("Transfer job for %s skipped because that collection system transfer is currently disabled", self.collection_system_transfer['name'])
            return self.on_job_complete(current_job, json.dumps({'parts':[{"partName": "Transfer Enabled", "result": "Fail", "reason": "Transfer is disabled"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

        self.cruise_id = payload_obj['cruiseID'] if 'cruiseID' in payload_obj else self.ovdm.get_cruise_id()
        self.lowering_id = payload_obj['loweringID'] if 'loweringID' in payload_obj else self.ovdm.get_lowering_id()

        logging.info("Job: %s, %s transfer started at: %s", current_job.handle, self.collection_system_transfer['name'], time.strftime("%D %T", time.gmtime()))

        self.transfer_start_date = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

        # set temporal bounds for transfer

        # if temporal bands are not used then set to absolute min/max
        if self.collection_system_transfer['useStartDate'] == '0':
            self.data_start_date = "1970/01/01 00:00"
            self.data_end_date = "9999/12/31 23:59"

        # if temporal bands are used then set to specified bounds for the corresponding cruise/lowering
        else:
            if self.collection_system_transfer['cruiseOrLowering'] == "0":
                logging.debug("Using cruise Time bounds")
                self.data_start_date = self.cruiseStartDate if 'cruiseStartDate' in payload_obj and payload_obj['cruiseStartDate'] != '' else "1970/01/01 00:00"
                self.data_end_date = self.cruiseEndDate if 'cruiseEndDate' in payload_obj and payload_obj['cruiseEndDate'] != '' else "9999/12/31 23:59"
            else:
                logging.debug("Using lowering Time bounds")
                self.data_start_date = self.loweringStartDate if 'loweringStartDate' in payload_obj and payload_obj['loweringStartDate'] != '' else "1970/01/01 00:00"
                self.data_end_date = self.loweringEndDate if 'loweringEndDate' in payload_obj and payload_obj['loweringEndDate'] != '' else "9999/12/31 23:59"

        logging.debug("Start date/time filter: %s", self.data_start_date)
        logging.debug("End date/time filter: %s", self.data_end_date)

        self.shipboard_data_warehouse_config = self.ovdm.get_shipboard_data_warehouse_config()

        return super().on_job_execute(current_job)


    def on_job_exception(self, current_job, exc_info):
        """
        Function run whenever the current job has an exception
        """

        logging.error("Job: %s, %s transfer failed at: %s", current_job.handle, self.collection_system_transfer['name'], time.strftime("%D %T", time.gmtime()))

        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail", "reason": "Unknown"}]))
        self.ovdm.set_error_collection_system_transfer(self.collection_system_transfer['collectionSystemTransferID'], 'Worker crashed')

        exc_type, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error(exc_type, fname, exc_tb.tb_lineno)

        return super().on_job_exception(current_job, exc_info)


    def on_job_complete(self, current_job, job_results):
        """
        Function run whenever the current job completes
        """

        results_obj = json.loads(job_results)

        if results_obj['files']['new'] or results_obj['files']['updated']:

            logging.debug("Preparing subsequent Gearman jobs")
            gm_client = python3_gearman.GearmanClient([self.ovdm.get_gearman_server()])

            job_data = {
                'cruiseID': self.cruise_id,
                'collectionSystemTransferID': self.collection_system_transfer['collectionSystemTransferID'],
                'files': results_obj['files']
            }

            for task in self.ovdm.get_tasks_for_hook('runCollectionSystemTransfer'):
                logging.info("Adding post task: %s", task)
                gm_client.submit_job(task, json.dumps(job_data), background=True)

        if len(results_obj['parts']) > 0:
            if results_obj['parts'][-1]['result'] == "Fail": # Final Verdict
                self.ovdm.set_error_collection_system_transfer(self.collection_system_transfer['collectionSystemTransferID'], results_obj['parts'][-1]['reason'])
            else:
                self.ovdm.set_idle_collection_system_transfer(self.collection_system_transfer['collectionSystemTransferID'])
        else:
            self.ovdm.set_idle_collection_system_transfer(self.collection_system_transfer['collectionSystemTransferID'])

        logging.debug("Job Results: %s", json.dumps(results_obj, indent=2))
        logging.info("Job: %s, %s transfer completed at: %s", current_job.handle, self.collection_system_transfer['name'], time.strftime("%D %T", time.gmtime()))

        return super().send_job_complete(current_job, job_results)


    def stop_task(self):
        """
        Function to stop the current job
        """
        self.stop = True
        logging.warning("Stopping current task...")


    def quit_worker(self):
        """
        Function to quit the worker
        """
        self.stop = True
        logging.warning("Quitting worker...")
        self.shutdown()


def task_run_collection_system_transfer(gearman_worker, current_job): # pylint: disable=too-many-return-statements,too-many-branches,too-many-statements
    """
    Run the collection system transfer
    """

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

    cruise_dir = os.path.join(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], gearman_worker.cruise_id)
    collection_system_dest_dir = os.path.join(cruise_dir, gearman_worker.shipboard_data_warehouse_config['loweringDataBaseDir'], gearman_worker.lowering_id, build_dest_dir(gearman_worker)) if gearman_worker.collection_system_transfer['cruiseOrLowering'] == "1" else os.path.join(cruise_dir, build_dest_dir(gearman_worker))
    # collection_system_source_dir = build_source_dir(gearman_worker)

    logging.debug("Setting transfer status to 'Running'")
    gearman_worker.ovdm.set_running_collection_system_transfer(gearman_worker.collection_system_transfer['collectionSystemTransferID'], os.getpid(), current_job.handle)

    logging.info("Testing connection")
    gearman_worker.send_job_status(current_job, 1, 10)

    gm_client = python3_gearman.GearmanClient([gearman_worker.ovdm.get_gearman_server()])

    gm_data = {
        'collectionSystemTransfer': gearman_worker.collection_system_transfer,
        'cruiseID': gearman_worker.cruise_id
    }

    completed_job_request = gm_client.submit_job("testCollectionSystemTransfer", json.dumps(gm_data))
    results_obj = json.loads(completed_job_request.result)

    logging.debug('Connection Test Results: %s', json.dumps(results_obj, indent=2))

    if results_obj['parts'][-1]['result'] == "Pass": # Final Verdict
        logging.debug("Connection test passed")
        job_results['parts'].append({"partName": "Connection Test", "result": "Pass"})
    else:
        logging.warning("Connection test failed, quitting job")
        job_results['parts'].append({"partName": "Connection Test", "result": "Fail", "reason": results_obj['parts'][-1]['reason']})
        return json.dumps(job_results)

    gearman_worker.send_job_status(current_job, 2, 10)

    logging.info("Transferring files")
    output_results = None
    if gearman_worker.collection_system_transfer['transferType'] == "1": # Local Directory
        output_results = transfer_local_source_dir(gearman_worker, current_job)
    elif  gearman_worker.collection_system_transfer['transferType'] == "2": # Rsync Server
        output_results = transfer_rsync_source_dir(gearman_worker, current_job)
    elif  gearman_worker.collection_system_transfer['transferType'] == "3": # SMB Server
        output_results = transfer_smb_source_dir(gearman_worker, current_job)
    elif  gearman_worker.collection_system_transfer['transferType'] == "4": # SSH Server
        output_results = transfer_ssh_source_dir(gearman_worker, current_job)
    else:
        logging.error("Unknown Transfer Type")
        job_results['parts'].append({"partName": "Transfer Files", "result": "Fail", "reason": "Unknown transfer type"})
        return json.dumps(job_results)

    if not output_results['verdict']:
        logging.error("Transfer of remote files failed: %s", output_results['reason'])
        job_results['parts'].append({"partName": "Transfer Files", "result": "Fail", "reason": output_results['reason']})
        return json.dumps(job_results)

    logging.debug("Transfer completed successfully")
    job_results['files'] = output_results['files']
    job_results['parts'].append({"partName": "Transfer Files", "result": "Pass"})

    if len(job_results['files']['new']) > 0:
        logging.debug("%s file(s) added", len(job_results['files']['new']))
    if len(job_results['files']['updated']) > 0:
        logging.debug("%s file(s) updated", len(job_results['files']['updated']))
    if len(job_results['files']['exclude']) > 0:
        logging.warning("%s misnamed file(s) encountered", len(job_results['files']['exclude']))

    gearman_worker.send_job_status(current_job, 9, 10)

    if job_results['files']['new'] or job_results['files']['updated']:

        logging.info("Setting file permissions")

        output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], os.path.join(build_logfile_dirpath(gearman_worker), collection_system_dest_dir))

        if not output_results['verdict']:
            logging.error("Error setting destination directory file/directory ownership/permissions: %s", collection_system_dest_dir)
            job_results['parts'].append({"partName": "Setting file/directory ownership/permissions", "result": "Fail", "reason": output_results['reason']})

        job_results['parts'].append({"partName": "Setting file/directory ownership/permissions", "result": "Pass"})

        logging.debug("Building logfiles")

        logfile_filename = gearman_worker.collection_system_transfer['name'] + '_' + gearman_worker.transfer_start_date + '.log'

        logfile_contents = {
            'files': {
                'new': job_results['files']['new'],
                'updated': job_results['files']['updated']
            }
        }

        output_results = output_json_data_to_file(os.path.join(build_logfile_dirpath(gearman_worker), logfile_filename), logfile_contents['files'])

        if output_results['verdict']:
            job_results['parts'].append({"partName": "Write transfer logfile", "result": "Pass"})
        else:
            logging.error("Error writing transfer logfile: %s", logfile_filename)
            job_results['parts'].append({"partName": "Write transfer logfile", "result": "Fail", "reason": output_results['reason']})
            return json.dumps(job_results)

        output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], os.path.join(build_logfile_dirpath(gearman_worker), logfile_filename))

        if not output_results['verdict']:
            job_results['parts'].append({"partName": "Set OpenVDM config file ownership/permissions", "result": "Fail", "reason": output_results['reason']})
            return json.dumps(job_results)

    logfile_filename = gearman_worker.collection_system_transfer['name'] + '_Exclude.log'
    logfile_contents = {
        'files': {
            'exclude': job_results['files']['exclude']
        }
    }
    logfile_contents['files']['exclude'] = job_results['files']['exclude']

    output_results = output_json_data_to_file(os.path.join(build_logfile_dirpath(gearman_worker), logfile_filename), logfile_contents['files'])

    if output_results['verdict']:
        job_results['parts'].append({"partName": "Write exclude logfile", "result": "Pass"})
    else:
        logging.error("Error writing transfer logfile: %s", output_results['reason'])
        job_results['parts'].append({"partName": "Write exclude logfile", "result": "Fail", "reason": output_results['reason']})
        return job_results

    output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], os.path.join(build_logfile_dirpath(gearman_worker), logfile_filename))

    if not output_results['verdict']:
        logging.error("Error setting ownership/permissions for transfer logfile: %s", logfile_filename)
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
        """
        Signal Handler for QUIT
        """
        logging.warning("QUIT Signal Received")
        new_worker.stop_task()

    def sigint_handler(_signo, _stack_frame):
        """
        Signal Handler for INT
        """
        logging.warning("INT Signal Received")
        new_worker.quit_worker()

    signal.signal(signal.SIGQUIT, sigquit_handler)
    signal.signal(signal.SIGINT, sigint_handler)

    logging.info("Registering worker tasks...")

    logging.info("\tTask: runCollectionSystemTransfer")
    new_worker.register_task("runCollectionSystemTransfer", task_run_collection_system_transfer)

    logging.info("Waiting for jobs...")
    new_worker.work()
