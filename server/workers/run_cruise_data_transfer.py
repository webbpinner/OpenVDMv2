#!/usr/bin/env python3
"""

FILE:  run_cruise_data_transfer.py

DESCRIPTION:  Gearman worker that handles the transfer of all cruise data from
    the Shipboard Data Warehouse to a second location.

     BUGS:
    NOTES:
   AUTHOR:  Webb Pinner
  COMPANY:  Capable Solutions
  VERSION:  2.5
  CREATED:  2015-01-01
 REVISION:  2021-01-04

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
import fnmatch
import subprocess
import signal
import logging
from random import randint
from os.path import dirname, realpath
import python3_gearman

sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.lib.check_filenames import is_ascii
from server.lib.set_owner_group_permissions import set_owner_group_permissions
from server.lib.openvdm import OpenVDM, DEFAULT_CRUISE_CONFIG_FN, DEFAULT_MD5_SUMMARY_FN, DEFAULT_MD5_SUMMARY_MD5_FN


def build_filelist(gearman_worker, source_dir): # pylint: disable=too-many-branches
    """
    Build list of files to transfer
    """

    return_files = {'include':[], 'exclude':[], 'new':[], 'updated':[]}

    filters = build_filters(gearman_worker)

    for root, _, filenames in os.walk(source_dir): # pylint: disable=too-many-nested-blocks
        for filename in filenames:

            filepath = os.path.join(root, filename)

            if os.path.islink(filepath):
                logging.debug("%s is a symlink, skipping", filename)
                continue

            exclude = False
            ignore = False
            for ignore_filter in filters['ignoreFilter'].split(','):
                #logging.debug(filt)
                if fnmatch.fnmatch(filepath, ignore_filter):
                    logging.debug("%s ignored by ignore filter", filename)
                    ignore = True
                    break
            if not ignore:
                for include_filter in filters['includeFilter'].split(','):
                    if fnmatch.fnmatch(filepath, include_filter):
                        for exclude_filter in filters['excludeFilter'].split(','):
                            if fnmatch.fnmatch(filepath, exclude_filter):
                                logging.debug("%s excluded by exclude filter", filename)
                                return_files['exclude'].append(filepath)
                                exclude = True
                                break
                        if not exclude and not is_ascii(filepath):
                            logging.debug("%s is not an ascii-encoded unicode string", filename)
                            return_files['exclude'].append(filepath)
                            exclude = True
                            break

                        if exclude:
                            break

                if not exclude:
                    logging.debug("%s is a valid file for transfer", filepath)
                    return_files['include'].append(filepath)

            # if include or exclude or ignore:
            #     logging.debug("{} excluded because file does not match any of the filters".format(filename))
            #     return_files['exclude'].append(os.path.join(root, filename))

    return_files['include'] = [filename.split(source_dir + '/',1).pop() for filename in return_files['include']]
    return_files['exclude'] = [filename.split(source_dir + '/',1).pop() for filename in return_files['exclude']]

    logging.debug("file list: %s", json.dumps(return_files, indent=2))

    return return_files

def build_filters(gearman_worker):
    """
    Build filters for the transfer
    """

    return {
        'includeFilter': '*',
        'excludeFilter': ','.join(build_exclude_filterlist(gearman_worker)),
        'ignoreFilter': ''
    }


def build_exclude_filterlist(gearman_worker):
    """
    Build exclude filter for the transfer
    """

    exclude_filterlist = []

    if gearman_worker.cruise_data_transfer['includeOVDMFiles'] == '0':
        dashboard_data_dir = gearman_worker.ovdm.get_required_extra_directory_by_name("Dashboard_Data")
        exclude_filterlist.append("*{}*".format(dashboard_data_dir['destDir']))

        transfer_logs = gearman_worker.ovdm.get_required_extra_directory_by_name("Transfer_Logs")
        exclude_filterlist.append("*{}*".format(transfer_logs['destDir']))

        exclude_filterlist.append("*{}*".format(transfer_logs['destDir']))
        exclude_filterlist.append("*{}".format(DEFAULT_CRUISE_CONFIG_FN))
        exclude_filterlist.append("*{}".format(DEFAULT_MD5_SUMMARY_FN))
        exclude_filterlist.append("*{}".format(DEFAULT_MD5_SUMMARY_MD5_FN))

    if gearman_worker.cruise_data_transfer['includePublicDataFiles'] == '0':
        from_publicdata_dir = gearman_worker.ovdm.get_required_extra_directory_by_name("From_PublicData")
        exclude_filterlist.append("*{}*".format(from_publicdata_dir['destDir']))

    excluded_collection_system_ids = gearman_worker.cruise_data_transfer['excludedCollectionSystems'].split(',')
    for collection_system_id in excluded_collection_system_ids:

        if collection_system_id == '0':
            continue

        collection_system_transfer = gearman_worker.ovdm.get_collection_system_transfer(collection_system_id)

        try:
            if collection_system_transfer['cruiseOrLowering'] == '0':
                exclude_filterlist.append("*{}*".format(collection_system_transfer['destDir']))
            else:
                lowerings = gearman_worker.ovdm.get_lowerings()
                for lowering in lowerings:
                    # exclude_filterlist.append("*/{cruiseID}/*/" + lowering + "/" + cruiseDataTransfer['destDir'].replace('{loweringID}', lowering) + "/*")
                    exclude_filterlist.append("*{}/{}*".format(lowering, collection_system_transfer['destDir'].replace('{cruiseID}', gearman_worker.cruise_id).replace('{loweringID}', lowering)))
        except Exception as err:
            logging.warning("Could not retrieve collection system transfer %s", collection_system_id)
            logging.warning(str(err))

    excluded_extra_directory_ids = gearman_worker.cruise_data_transfer['excludedExtraDirectories'].split(',')
    for excluded_extra_directory_id in excluded_extra_directory_ids:

        if excluded_extra_directory_id == '0':
            continue

        extra_directory = gearman_worker.ovdm.getExtraDirectory(excluded_extra_directory_id)
        exclude_filterlist.append("*{}*".format(extra_directory['destDir'].replace('{cruiseID}', gearman_worker.cruise_id)))

    logging.debug("Exclude filters: %s", json.dumps(exclude_filterlist, indent=2))

    return exclude_filterlist


def transfer_local_dest_dir(gearman_worker, gearman_job): # pylint: disable=too-many-locals,too-many-statements
    """
    Copy cruise data to a local directory
    """

    logging.debug("Transfer to Local Directory")

    cruise_dir = os.path.join(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], gearman_worker.cruise_id)
    dest_dir = gearman_worker.cruise_data_transfer['destDir'].rstrip('/')

    logging.debug('Destination Dir: %s', dest_dir)

    logging.debug("Building file list")
    files = build_filelist(gearman_worker, cruise_dir)

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsync_exclude_list_filepath = os.path.join(tmpdir, 'rsyncExcludeList.txt')

    try:
        with open(rsync_exclude_list_filepath, 'w') as rsync_excludelist_file:
            rsync_excludelist_file.write('\n'.join(files['exclude']))

    except IOError:
        logging.error("Error Saving temporary rsync filelist file")

        # Cleanup
        shutil.rmtree(tmpdir)
        return False

    file_index = 0
    file_count = 1 # avoids divide by 0 error
    command = ['rsync', '-trimnv', '--stats', '--exclude-from=' + rsync_exclude_list_filepath, cruise_dir, dest_dir]

    logging.debug('File count Command: %s', ' '.join(command))

    proc = subprocess.run(command, capture_output=True, text=True, check=False)

    for line in proc.stdout:
        if line.startswith('Number of regular files transferred:'):
            file_count = int(line.split(':')[1])

    bandwidth_imit = '--bwlimit=' + gearman_worker.cruise_data_transfer['bandwidthLimit'] if gearman_worker.cruise_data_transfer['bandwidthLimit'] != '0' else '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    command = ['rsync', '-trimv', bandwidth_imit, '--exclude-from=' + rsync_exclude_list_filepath, cruise_dir, dest_dir]

    logging.debug('Transfer Command: %s', ' '.join(command))

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    while True:

        line = proc.stdout.readline().rstrip('\n')
        err_line = proc.stderr.readline().rstrip('\n')

        if err_line:
            logging.warning("Err Line: %s", err_line)
        if line:
            logging.debug("Line: %s", line)

        if proc.poll() is not None:
            break

        # if not line:
        #     continue

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

    # files['new'] = [os.path.join('/', gearman_worker.cruise_id, filename) for filename in files['new']]
    # files['updated'] = [os.path.join('/', gearman_worker.cruise_id, filename) for filename in files['updated']]

    logging.info("Setting file permissions")
    output_results = set_owner_group_permissions(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseUsername'], os.path.join(dest_dir, gearman_worker.cruise_id))

    # Cleanup
    shutil.rmtree(tmpdir)

    if not output_results['verdict']:
        logging.error("Error setting ownership/permissions for cruise data at destination: %s", os.path.join(dest_dir, gearman_worker.cruise_id))
        return output_results

    return { 'verdict': True, 'files': files }


def transfer_smb_dest_dir(gearman_worker, gearman_job): # pylint: disable=too-many-locals,too-many-statements
    """
    Copy cruise data to a samba server
    """

    logging.debug("Transfer to SMB Source")

    cruise_dir = os.path.join(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], gearman_worker.cruise_id)

    logging.debug("Building file list")
    files = build_filelist(gearman_worker, cruise_dir)

    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    # Create mountpoint
    mntpoint = os.path.join(tmpdir, 'mntpoint')
    os.mkdir(mntpoint, 0o755)

    # Mount SMB Share
    logging.debug("Mounting SMB Share")

    ver_test_command = ['smbclient', '-L', gearman_worker.cruise_data_transfer['smbServer'], '-W', gearman_worker.cruise_data_transfer['smbDomain'], '-m', 'SMB2', '-g', '-N'] if gearman_worker.cruise_data_transfer['smbUser'] == 'guest' else ['smbclient', '-L', gearman_worker.cruise_data_transfer['smbServer'], '-W', gearman_worker.cruise_data_transfer['smbDomain'], '-m', 'SMB2', '-g', '-U', gearman_worker.cruise_data_transfer['smbUser'] + '%' + gearman_worker.cruise_data_transfer['smbPass']]
    logging.debug("SMB version test command: %s", ' '.join(ver_test_command))

    vers="2.1"
    proc = subprocess.run(ver_test_command, capture_output=True, text=True, check=False)

    for line in proc.stdout.splitlines():
        if line.startswith('OS=[Windows 5.1]'):
            vers="1.0"
            break

    mount_command = ['sudo', 'mount', '-t', 'cifs', gearman_worker.cruise_data_transfer['smbServer'], mntpoint, '-o', 'rw' + ',guest' + ',domain=' + gearman_worker.cruise_data_transfer['smbDomain'] + ',vers=' + vers] if gearman_worker.cruise_data_transfer['smbUser'] == 'guest' else ['sudo', 'mount', '-t', 'cifs', gearman_worker.cruise_data_transfer['smbServer'], mntpoint, '-o', 'rw' + ',username=' + gearman_worker.cruise_data_transfer['smbUser'] + ',password=' + gearman_worker.cruise_data_transfer['smbPass'] + ',domain=' + gearman_worker.cruise_data_transfer['smbDomain'] + ',vers=' + vers]
    logging.debug("Mount command: %s", ' '.join(mount_command))

    subprocess.run(mount_command, capture_output=True, text=True, check=False)

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsync_exclude_list_filepath = os.path.join(tmpdir, 'rsyncExcludeList.txt')

    try:
        with open(rsync_exclude_list_filepath, 'w') as rsync_excludelist_file:
            rsync_excludelist_file.write('\n'.join(files['exclude']))

        logging.debug('\n'.join(files['exclude']))
    except IOError:
        logging.error("Error Saving temporary rsync filelist file")

        # Cleanup
        shutil.rmtree(tmpdir)
        return False

    file_index = 0
    file_count = 1 # avoids divide by 0 error
    command = ['rsync', '-trimnv', '--stats', '--exclude-from=' + rsync_exclude_list_filepath, cruise_dir, os.path.join(mntpoint, gearman_worker.cruise_data_transfer['destDir']).rstrip('/') if gearman_worker.cruise_data_transfer['destDir'] != '/' else mntpoint]

    logging.debug('File count Command: %s', ' '.join(command))

    proc = subprocess.run(command, capture_output=True, text=True, check=False)

    for line in proc.stdout:
        if line.startswith('Number of regular files transferred:'):
            file_count = int(line.split(':')[1])
            break

    bandwidth_imit = '--bwlimit=' + gearman_worker.cruise_data_transfer['bandwidthLimit'] if gearman_worker.cruise_data_transfer['bandwidthLimit'] != '0' else '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    command = ['rsync', '-trimv', bandwidth_imit, '--exclude-from=' + rsync_exclude_list_filepath, cruise_dir, os.path.join(mntpoint, gearman_worker.cruise_data_transfer['destDir']).rstrip('/') if gearman_worker.cruise_data_transfer['destDir'] != '/' else mntpoint]

    logging.debug('Transfer Command: %s', ' '.join(command))

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    while True:

        line = proc.stdout.readline().rstrip('\n')
        err_line = proc.stderr.readline().rstrip('\n')

        if err_line:
            logging.warning("Err Line: %s", err_line)
        if line:
            logging.debug("Line: %s", line)

        if proc.poll() is not None:
            break

        # if not line:
        #     continue

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

    # Cleanup
    time.sleep(2)

    logging.debug("Unmount SMB Share")
    subprocess.call(['umount', mntpoint])
    shutil.rmtree(tmpdir)

    return { 'verdict': True, 'files': files }


def transfer_rsync_dest_dir(gearman_worker, gearman_job): # pylint: disable=too-many-locals,too-many-statements
    """
    Copy cruise data to a rsync server
    """

    logging.debug("Transfer to RSYNC Server")

    cruise_dir = os.path.join(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], gearman_worker.cruise_id)

    logging.debug("Building file list")
    files = build_filelist(gearman_worker, cruise_dir)

    dest_dir = gearman_worker.cruise_data_transfer['destDir'].rstrip('/')

    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    rsync_password_filepath = os.path.join(tmpdir, 'passwordFile')

    try:
        with open(rsync_password_filepath, 'w') as rsync_password_file:
            rsync_password_file.write(gearman_worker.cruise_data_transfer['rsyncPass'])

        os.chmod(rsync_password_filepath, 0o600)

    except IOError:
        logging.error("Error Saving temporary rsync password file")
        rsync_password_file.close()

        # Cleanup
        shutil.rmtree(tmpdir)

        return {'verdict': False, 'reason': 'Error Saving temporary rsync password file: ' + rsync_password_filepath}

    rsync_exclude_list_filepath = os.path.join(tmpdir, 'rsyncExcludeList.txt')

    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    rsync_exclude_list_filepath = os.path.join(tmpdir, 'rsyncExcludeList.txt')

    try:
        with open(rsync_exclude_list_filepath, 'w') as rsync_excludelist_file:
            rsync_excludelist_file.write('\n'.join(files['exclude']))

    except IOError:
        logging.error("Error Saving temporary rsync filelist file")

        # Cleanup
        shutil.rmtree(tmpdir)
        return False

    file_index = 0
    file_count = 1 # avoids divide by 0 error
    command = ['rsync', '-trimnv', '--stats', '--exclude-from=' + rsync_exclude_list_filepath, '--password-file=' + rsync_password_filepath, cruise_dir, 'rsync://' + gearman_worker.cruise_data_transfer['rsyncUser'] + '@' + gearman_worker.cruise_data_transfer['rsyncServer'] + dest_dir + '/']

    logging.debug('File count Command: %s', ' '.join(command))

    proc = subprocess.run(command, capture_output=True, text=True, check=False)

    for line in proc.stdout:
        if line.startswith('Number of regular files transferred:'):
            file_count = int(line.split(':')[1])
            break

    bandwidth_imit = '--bwlimit=' + gearman_worker.cruise_data_transfer['bandwidthLimit'] if gearman_worker.cruise_data_transfer['bandwidthLimit'] != '0' else '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    # # Work around to create CruiseID at the destination
    # os.mkdir(os.path.join(tmpdir, gearman_worker.cruise_id))
    # command = ['rsync', '-a', bandwidthLimit, '--no-motd', '--password-file=' + rsync_password_filepath, os.path.join(tmpdir, gearman_worker.cruise_id), 'rsync://' + gearman_worker.cruise_data_transfer['rsyncUser'] + '@' + gearman_worker.cruise_data_transfer['rsyncServer'] + dest_dir + '/']
    # popen = subprocess.Popen(command, stdout=subprocess.PIPE)

    command = ['rsync', '-trimv', bandwidth_imit, '--no-motd', '--exclude-from=' + rsync_exclude_list_filepath, '--password-file=' + rsync_password_filepath, cruise_dir, 'rsync://' + gearman_worker.cruise_data_transfer['rsyncUser'] + '@' + gearman_worker.cruise_data_transfer['rsyncServer'] + dest_dir + '/']

    logging.debug('Transfer Command: %s', ' '.join(command))

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    while True:

        line = proc.stdout.readline().rstrip('\n')
        err_line = proc.stderr.readline().rstrip('\n')

        if err_line:
            logging.warning("Err Line: %s", err_line)
        if line:
            logging.debug("Line: %s", line)

        if proc.poll() is not None:
            break

        # if not line:
        #     continue

        if line.startswith( '<f+++++++++' ):
            filename = line.split(' ',1)[1]
            files['new'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(file_index)/float(file_count)), 100)
            file_index += 1
        elif line.startswith( '<f.' ):
            filename = line.split(' ',1)[1]
            files['updated'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(file_index)/float(file_count)), 100)
            file_index += 1

        if gearman_worker.stop:
            logging.debug("Stopping")
            proc.terminate()
            break

    # files['new'] = [os.path.join(dest_dir.replace(cruise_dir, '').lstrip('/').rstrip('/'),filename) for filename in files['new']]
    # files['updated'] = [os.path.join(dest_dir.replace(cruise_dir, '').lstrip('/').rstrip('/'),filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return {'verdict': True, 'files': files}


def transfer_ssh_dest_dir(gearman_worker, gearman_job): # pylint: disable=too-many-locals
    """
    Copy cruise data to a ssh server
    """

    logging.debug("Transfer to SSH Server")

    cruise_dir = os.path.join(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], gearman_worker.cruise_id)

    logging.debug("Building file list")
    files = build_filelist(gearman_worker, cruise_dir)

    dest_dir = gearman_worker.cruise_data_transfer['destDir'].rstrip('/')

    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    ssh_excludelist_filepath = os.path.join(tmpdir, 'sshExcludeList.txt')

    try:
        with open(ssh_excludelist_filepath, 'w') as ssh_exclude_filelist_file:
            ssh_exclude_filelist_file.write('\n'.join(files['exclude']))

    except IOError:
        logging.debug("Error Saving temporary ssh exclude filelist file")

        # Cleanup
        shutil.rmtree(tmpdir)

        return {'verdict': False, 'reason': 'Error Saving temporary ssh exclude filelist file: ' + ssh_excludelist_filepath, 'files':[]}

    file_index = 0
    file_count = 1 # avoids divide by 0 error
    command = ['rsync', '-trimnv', '--stats', '--exclude-from=' + ssh_excludelist_filepath, '-e', 'ssh', cruise_dir, gearman_worker.cruise_data_transfer['sshUser'] + '@' + gearman_worker.cruise_data_transfer['sshServer'] + ':', dest_dir] if gearman_worker.cruise_data_transfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.cruise_data_transfer['sshPass'], 'rsync', '-trimnv', '--exclude-from=' + ssh_excludelist_filepath, '-e', 'ssh', cruise_dir, gearman_worker.cruise_data_transfer['sshUser'] + '@' + gearman_worker.cruise_data_transfer['sshServer'] + ':' + dest_dir]

    logging.debug('File count Command: %s', ' '.join(command))

    proc = subprocess.run(command, capture_output=True, text=True, check=False)

    for line in proc.stdout:
        if line.startswith('Number of regular files transferred:'):
            file_count = int(line.split(':')[1])
            break

    bandwidth_imit = '--bwlimit=' + gearman_worker.cruise_data_transfer['bandwidthLimit'] if gearman_worker.cruise_data_transfer['bandwidthLimit'] != '0' else '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    # command = ['ssh', gearman_worker.cruise_data_transfer['sshServer'], '-l', gearman_worker.cruise_data_transfer['sshUser'], '-o', 'StrictHostKeyChecking=no', 'PasswordAuthentication=no', 'mkdir ' + os.path.join(dest_dir, gearman_worker.cruise_id)] if gearman_worker.cruise_data_transfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.cruise_data_transfer['sshPass'], 'ssh', gearman_worker.cruise_data_transfer['sshServer'], '-l', gearman_worker.cruise_data_transfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PubkeyAuthentication=no', 'mkdir ' + os.path.join(dest_dir, gearman_worker.cruise_id)]

    # proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    # proc.communicate()

    command = ['rsync', '-trimv', bandwidth_imit, '--exclude-from=' + ssh_excludelist_filepath, '-e', 'ssh', cruise_dir, gearman_worker.cruise_data_transfer['sshUser'] + '@' + gearman_worker.cruise_data_transfer['sshServer'] + ':' + dest_dir] if gearman_worker.cruise_data_transfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.cruise_data_transfer['sshPass'], 'rsync', '-trimv', bandwidth_imit, '--exclude-from=' + ssh_excludelist_filepath, '-e', 'ssh', cruise_dir, gearman_worker.cruise_data_transfer['sshUser'] + '@' + gearman_worker.cruise_data_transfer['sshServer'] + ':' + dest_dir]

    logging.debug("Transfer Command: %s", ' '.join(command))

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    while True:

        line = proc.stdout.readline().rstrip('\n')
        err_line = proc.stderr.readline().rstrip('\n')

        if err_line:
            logging.warning("Err Line: %s", err_line)
        if line:
            logging.debug("Line: %s", line)

        if proc.poll() is not None:
            break

        # if not line:
        #    continue

        if line.startswith( '<f+++++++++' ):
            filename = line.split(' ',1)[1]
            files['new'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(file_index)/float(file_count)), 100)
            file_index += 1
        elif line.startswith( '<f.' ):
            filename = line.split(' ',1)[1]
            files['updated'].append(filename)
            gearman_worker.send_job_status(gearman_job, int(20 + 70*float(file_index)/float(file_count)), 100)
            file_index += 1

        if gearman_worker.stop:
            logging.debug("Stopping")
            proc.terminate()
            break

    # files['new'] = [os.path.join(dest_dir.replace(cruise_dir, '').lstrip('/').rstrip('/'),filename) for filename in files['new']]
    # files['updated'] = [os.path.join(dest_dir.replace(cruise_dir, '').lstrip('/').rstrip('/'),filename) for filename in files['updated']]

    # Cleanup
    shutil.rmtree(tmpdir)

    return {'verdict': True, 'files': files}


class OVDMGearmanWorker(python3_gearman.GearmanWorker):
    """
    Class for the current Gearman worker
    """

    def __init__(self):
        self.stop = False
        self.ovdm = OpenVDM()
        self.cruise_id = self.ovdm.get_cruise_id()
        self.system_status = self.ovdm.get_system_status()
        self.cruise_data_transfer = {}
        self.shipboard_data_warehouse_config = self.ovdm.get_shipboard_data_warehouse_config()
        super().__init__(host_list=[self.ovdm.get_gearman_server()])


    def on_job_execute(self, current_job):
        """
        Function run whenever a new job arrives
        """

        logging.debug("current_job: %s", current_job)

        self.stop = False
        payload_obj = json.loads(current_job.data)

        try:
            self.cruise_data_transfer = self.ovdm.get_cruise_data_transfer(payload_obj['cruiseDataTransfer']['cruiseDataTransferID'])

            if not self.cruise_data_transfer:
                return self.on_job_complete(current_job, json.dumps({'parts':[{"partName": "Located Cruise Data Tranfer Data", "result": "Fail", "reason": "Could not find configuration data for cruise data transfer"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

            if self.cruise_data_transfer['status'] == "1": #not running
                logging.info("Transfer job for %s skipped because a transfer for that cruise data destination is already in-progress", self.cruise_data_transfer['name'])
                return self.on_job_complete(current_job, json.dumps({'parts':[{"partName": "Transfer In-Progress", "result": "Fail", "reason": "Transfer is already in-progress"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

        except Exception as err:
            logging.debug(str(err))
            return self.on_job_complete(current_job, json.dumps({'parts':[{"partName": "Located Cruise Data Tranfer Data", "result": "Fail", "reason": "Could not find retrieve data for cruise data transfer from OpenVDM API"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

        self.system_status = payload_obj['systemStatus'] if 'systemStatus' in payload_obj else self.ovdm.get_system_status()
        self.cruise_data_transfer.update(payload_obj['cruiseDataTransfer'])

        if self.system_status == "Off" or self.cruise_data_transfer['enable'] == '0':
            logging.info("Transfer job for %s skipped because that cruise data transfer is currently disabled", self.cruise_data_transfer['name'])
            return self.on_job_complete(current_job, json.dumps({'parts':[{"partName": "Transfer Enabled", "result": "Ignore", "reason": "Transfer is disabled"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

        self.cruise_id = self.ovdm.get_cruise_id()

        logging.info("Job: %s, %s transfer started at: %s", current_job.handle, self.cruise_data_transfer['name'], time.strftime("%D %T", time.gmtime()))

        self.shipboard_data_warehouse_config = self.ovdm.get_shipboard_data_warehouse_config()

        return super().on_job_execute(current_job)


    def on_job_exception(self, current_job, exc_info):
        """
        Function run whenever the current job has an exception
        """

        logging.error("Job: %s, %s transfer failed at: %s", current_job.handle, self.cruise_data_transfer['name'], time.strftime("%D %T", time.gmtime()))

        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail", "reason": "Unknown"}]))
        self.ovdm.set_error_cruise_data_transfer(self.cruise_data_transfer['cruiseDataTransferID'], 'Worker crashed')

        exc_type, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error(exc_type, fname, exc_tb.tb_lineno)
        return super().on_job_exception(current_job, exc_info)


    def on_job_complete(self, current_job, job_result):
        """
        Function run whenever the current job completes
        """

        results_obj = json.loads(job_result)

        if len(results_obj['parts']) > 0:
            if results_obj['parts'][-1]['result'] == "Fail": # Final Verdict
                self.ovdm.set_error_cruise_data_transfer(self.cruise_data_transfer['cruiseDataTransferID'], results_obj['parts'][-1]['reason'])
            else:
                self.ovdm.set_idle_cruise_data_transfer(self.cruise_data_transfer['cruiseDataTransferID'])
        else:
            self.ovdm.set_idle_cruise_data_transfer(self.cruise_data_transfer['cruiseDataTransferID'])

        logging.debug("Job Results: %s", json.dumps(results_obj, indent=2))
        logging.info("Job: %s, %s transfer completed at: %s", current_job.handle, self.cruise_data_transfer['name'], time.strftime("%D %T", time.gmtime()))

        return super().send_job_complete(current_job, job_result)


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


def task_run_cruise_data_transfer(gearman_worker, current_job):
    """
    Run the cruise data transfer
    """

    time.sleep(randint(0,2))

    job_results = {
        'parts': [
            {"partName": "Transfer In-Progress", "result": "Pass"},
            {"partName": "Transfer Enabled", "result": "Pass"}
        ],
        'files':{}
    }

    logging.debug("Setting transfer status to 'Running'")
    gearman_worker.ovdm.set_running_cruise_data_transfer(gearman_worker.cruise_data_transfer['cruiseDataTransferID'], os.getpid(), current_job.handle)

    logging.info("Testing configuration")
    gearman_worker.send_job_status(current_job, 1, 10)

    gm_client = python3_gearman.GearmanClient([gearman_worker.ovdm.get_gearman_server()])

    gm_data = {
        'cruiseDataTransfer': gearman_worker.cruise_data_transfer,
        'cruiseID': gearman_worker.cruise_id
    }

    completed_job_request = gm_client.submit_job("testCruiseDataTransfer", json.dumps(gm_data))
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
    if gearman_worker.cruise_data_transfer['transferType'] == "1": # Local Directory
        output_results = transfer_local_dest_dir(gearman_worker, current_job)
    elif  gearman_worker.cruise_data_transfer['transferType'] == "2": # Rsync Server
        output_results = transfer_rsync_dest_dir(gearman_worker, current_job)
    elif  gearman_worker.cruise_data_transfer['transferType'] == "3": # SMB Server
        output_results = transfer_smb_dest_dir(gearman_worker, current_job)
    elif  gearman_worker.cruise_data_transfer['transferType'] == "4": # SSH Server
        output_results = transfer_ssh_dest_dir(gearman_worker, current_job)
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
        logging.debug("%s file(s) intentionally skipped", len(job_results['files']['exclude']))

    gearman_worker.send_job_status(current_job, 9, 10)

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

    logging.info("\tTask: runCruiseDataTransfer")
    new_worker.register_task("runCruiseDataTransfer", task_run_cruise_data_transfer)

    logging.info("Waiting for jobs...")
    new_worker.work()
