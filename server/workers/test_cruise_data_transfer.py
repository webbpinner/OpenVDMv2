#!/usr/bin/env python3
"""
FILE:  test_cruise_data_transfer.py

DESCRIPTION:  Gearman worker that handles testing cruise data transfer
                configurations

     BUGS:
    NOTES:
   AUTHOR:  Webb Pinner
  COMPANY:  Capable Solutions
  VERSION:  2.5
  CREATED:  2015-01-01
 REVISION:  2021-01-06

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
import subprocess
import signal
import logging
import python3_gearman

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.lib.openvdm import OpenVDM

def write_test(dest_dir):
    """
    Verify the current user has write permissions to the dest_dir
    """
    if os.path.isdir(dest_dir):
        try:
            filepath = os.path.join(dest_dir, 'writeTest.txt')
            with open(filepath, 'w') as filehandle:
                filehandle.write("this file tests if the parent directory can be written to.  You can delete this file if desired")

            os.remove(filepath)
        except Exception as err:
            logging.warning("Unable to write to %s", dest_dir)
            logging.warning(str(err))
            return False
        return True
    return False


def test_local_dest_dir(gearman_worker):
    """
    Verify the destination directory exists for a local directory transfer
    """

    return_val = []

    dest_dir = gearman_worker.cruise_data_transfer['destDir']

    if not os.path.isdir(dest_dir):
        return_val.append({"partName": "Destination Directory", "result": "Fail", "reason": "Unable to locate destination directory: {}".format(dest_dir)})
        if gearman_worker.cruise_data_transfer['localDirIsMountPoint'] == '1':
            return_val.append({"partName": "Destination Directory is a Mountpoint", "result": "Fail", "reason": "Unable to locate destination directory: {}".format(dest_dir)})
        return_val.append({"partName": "Write Test", "result": "Fail", "reason": "Unable to locate destination directory: {}".format(dest_dir)})

        return return_val

    return_val.append({"partName": "Destination Directory", "result": "Pass"})

    if gearman_worker.cruise_data_transfer['localDirIsMountPoint'] == '1':
        if not os.path.ismount(dest_dir):
            return_val.extend([
                {"partName": "Destination Directory is a Mountpoint", "result": "Fail", "reason": "Destination directory: {} is not a mountpoint".format(dest_dir)},
                {"partName": "Write Test", "result": "Fail", "reason": "Destination directory: {} is not a mountpoint".format(dest_dir)}
            ])

            return return_val

        return_val.append({"partName": "Destination Directory is a Mountpoint", "result": "Pass"})

    if not write_test(dest_dir):
        return_val.append({"partName": "Write Test", "result": "Fail", "reason": "Unable to write data to desination directory: " + dest_dir})
        return return_val

    return_val.append({"partName": "Write Test", "result": "Pass"})

    return return_val


def test_smb_dest_dir(gearman_worker):
    """
    Verify the destination directory exists for a smb server transfer
    """

    return_val = []

    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    # Verify the server exists
    server_test_command = ['smbclient', '-L', gearman_worker.cruise_data_transfer['smbServer'], '-W', gearman_worker.cruise_data_transfer['smbDomain'], '-m', 'SMB2', '-g', '-N'] if gearman_worker.cruise_data_transfer['smbUser'] == 'guest' else ['smbclient', '-L', gearman_worker.cruise_data_transfer['smbServer'], '-W', gearman_worker.cruise_data_transfer['smbDomain'], '-m', 'SMB2', '-g', '-U', gearman_worker.cruise_data_transfer['smbUser'] + '%' + gearman_worker.cruise_data_transfer['smbPass']]
    logging.debug("Server test command: %s", ' '.join(server_test_command))

    proc = subprocess.run(server_test_command, capture_output=True, text=True, check=False)

    vers = "2.1"
    found_server = False
    for line in proc.stdout.splitlines():
        logging.debug("STDOUT Line: %s", line.rstrip('\n')) # yield line
        if line.startswith( "Disk" ):
            found_server = True
            break

    for line in proc.stderr.splitlines():
        logging.debug("STDERR Line: %s", line.rstrip('\n')) # yield line
        if line.startswith("OS=[Windows 5.1]"):
            vers="1.0"

    if not found_server:
        return_val.extend([
            {"partName": "SMB Server", "result": "Fail", "reason": "Could not connect to SMB Server: {} as {}".format(gearman_worker.cruise_data_transfer['smbServer'], gearman_worker.cruise_data_transfer['smbUser'])},
            {"partName": "SMB Share", "result": "Fail", "reason": "Could not connect to SMB Server: {} as {}".format(gearman_worker.cruise_data_transfer['smbServer'], gearman_worker.cruise_data_transfer['smbUser'])},
            {"partName": "Destination Directory", "result": "Fail", "reason": "Could not connect to SMB Server: {} as {}".format(gearman_worker.cruise_data_transfer['smbServer'], gearman_worker.cruise_data_transfer['smbUser'])},
            {"partName": "Write Test", "result": "Fail", "reason": "Could not connect to SMB Server: {} as {}".format(gearman_worker.cruise_data_transfer['smbServer'], gearman_worker.cruise_data_transfer['smbUser'])},
        ])

        return return_val

    return_val.append({"partName": "SMB Server", "result": "Pass"})

    # Create mountpoint
    mntpoint = os.path.join(tmpdir, 'mntpoint')
    os.mkdir(mntpoint, 0o755)

    # Mount SMB Share
    mount_command = ['mount', '-t', 'cifs', gearman_worker.cruise_data_transfer['smbServer'], mntpoint, '-o', 'rw'+',guest'+',domain='+gearman_worker.cruise_data_transfer['smbDomain']+',vers='+vers] if gearman_worker.cruise_data_transfer['smbUser'] == 'guest' else ['mount', '-t', 'cifs', gearman_worker.cruise_data_transfer['smbServer'], mntpoint, '-o', 'rw'+',username='+gearman_worker.cruise_data_transfer['smbUser']+',password='+gearman_worker.cruise_data_transfer['smbPass']+',domain='+gearman_worker.cruise_data_transfer['smbDomain']+',vers='+vers]

    logging.debug("Mount command: %s", ' '.join(mount_command))

    proc = subprocess.run(mount_command, capture_output=True, check=False)

    if proc.returncode != 0:
        return_val.extend([
            {"partName": "SMB Share", "result": "Fail", "reason": "Could not connect to SMB Share: {} as {}".format(gearman_worker.cruise_data_transfer['smbServer'], gearman_worker.cruise_data_transfer['smbUser'])},
            {"partName": "Destination Directory", "result": "Fail", "reason": "Could not connect to SMB Share: {} as {}".format(gearman_worker.cruise_data_transfer['smbServer'], gearman_worker.cruise_data_transfer['smbUser'])},
            {"partName": "Write Test", "result": "Fail", "reason": "Could not connect to SMB Share: {} as {}".format(gearman_worker.cruise_data_transfer['smbServer'], gearman_worker.cruise_data_transfer['smbUser'])}
        ])

        # Cleanup
        shutil.rmtree(tmpdir)

        return return_val

    return_val.append({"partName": "SMB Share", "result": "Pass"})

    dest_dir = os.path.join(mntpoint, gearman_worker.cruise_data_transfer['destDir'])
    if not os.path.isdir(dest_dir):
        return_val.append({"partName": "Destination Directory", "result": "Fail", "reason": "Unable to find destination directory: {} within the SMB Share: {}".format(gearman_worker.cruise_data_transfer['destDir'], gearman_worker.cruise_data_transfer['smbServer'])})
        return_val.append({"partName": "Write Test", "result": "Fail", "reason": "Unable to find destination directory: {} within the SMB Share: {}".format(gearman_worker.cruise_data_transfer['destDir'], gearman_worker.cruise_data_transfer['smbServer'])})

    else:
        return_val.append({"partName": "Destination Directory", "result": "Pass"})

        if not write_test(dest_dir):
            return_val.append({"partName": "Write Test", "result": "Fail", "reason": "Unable to write to destination directory: {} within the SMB Share: {}".format(dest_dir, gearman_worker.cruise_data_transfer['smbServer'])})
        else:
            return_val.append({"partName": "Write Test", "result": "Pass"})


    # Unmount SMB Share
    if os.path.ismount(mntpoint):
        subprocess.call(['sudo', 'umount', mntpoint])

    # Cleanup
    shutil.rmtree(tmpdir)

    return return_val


def test_rsync_dest_dir(gearman_worker):
    """
    Verify the destination directory exists for a rsync server transfer
    """

    return_val = []

    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    rsync_password_filepath = os.path.join(tmpdir,'passwordFile')

    try:
        with open(rsync_password_filepath, 'w') as rsync_password_file:

            if gearman_worker.cruise_data_transfer['rsyncUser'] != 'anonymous':
                rsync_password_file.write(gearman_worker.cruise_data_transfer['rsyncPass'])
            else:
                rsync_password_file.write('')

    except IOError:
        logging.error("Error Saving temporary rsync password file %s", rsync_password_filepath)
        return_val.append({"partName": "Writing temporary rsync password file", "result": "Fail", "reason": "Unable to create temporary rsync password file: {}".format(rsync_password_filepath)})

        # Cleanup
        shutil.rmtree(tmpdir)

        return return_val

    os.chmod(rsync_password_filepath, 0o600)

    server_test_command = ['rsync', '--no-motd', '--password-file=' + rsync_password_filepath, 'rsync://' + gearman_worker.cruise_data_transfer['rsyncUser'] + '@' + gearman_worker.cruise_data_transfer['rsyncServer']]

    logging.debug("Server test command: %s", ' '.join(server_test_command))

    proc = subprocess.run(server_test_command, capture_output=True, check=False)

    if proc.returncode != 0:
        return_val.extend([
            {"partName": "Rsync Connection", "result": "Fail", "reason": "Unable to connect to rsync server: {} as {}".format(gearman_worker.cruise_data_transfer['rsyncServer'], gearman_worker.cruise_data_transfer['rsyncUser'])},
            {"partName": "Destination Directory", "result": "Fail", "reason": "Unable to connect to rsync server: {} as {}".format(gearman_worker.cruise_data_transfer['rsyncServer'], gearman_worker.cruise_data_transfer['rsyncUser'])},
            {"partName": "Write Test", "result": "Fail", "reason": "Unable to connect to rsync server: {} as {}".format(gearman_worker.cruise_data_transfer['rsyncServer'], gearman_worker.cruise_data_transfer['rsyncUser'])}
        ])

        # Cleanup
        shutil.rmtree(tmpdir)

        return return_val

    return_val.append({"partName": "Rsync Connection", "result": "Pass"})

    dest_dir = gearman_worker.cruise_data_transfer['destDir']

    dest_test_command = ['rsync', '--no-motd', '--password-file=' + rsync_password_filepath, 'rsync://' + gearman_worker.cruise_data_transfer['rsyncUser'] + '@' + gearman_worker.cruise_data_transfer['rsyncServer'] + dest_dir]

    logging.debug("Destination test command: %s", ' '.join(dest_test_command))

    proc = subprocess.run(dest_test_command, capture_output=True, check=False)

    if proc.returncode != 0:
        return_val.extend([
            {"partName": "Destination Directory", "result": "Fail", "reason": "Unable to find destination directory: {} on the Rsync Server: {}".format(dest_dir, gearman_worker.cruise_data_transfer['rsyncServer'])},
            {"partName": "Write Test", "result": "Fail", "reason": "Unable to find destination directory: {} on the Rsync Server: {}".format(dest_dir, gearman_worker.cruise_data_transfer['rsyncServer'])}
        ])

        # Cleanup
        shutil.rmtree(tmpdir)

        return return_val

    return_val.append({"partName": "Destination Directory", "result": "Pass"})

    write_test_file = os.path.join(tmpdir, 'writeTest.txt')
    with open(write_test_file, 'a') as write_test_file_handle:
        write_test_file_handle.write("This file proves this directory can be written to by OpenVDM")

    write_test_command = ['rsync', '-vi', '--no-motd', '--password-file=' + rsync_password_filepath, write_test_file, 'rsync://' + gearman_worker.cruise_data_transfer['rsyncUser'] + '@' + gearman_worker.cruise_data_transfer['rsyncServer'] + dest_dir]

    logging.debug("Server Test Command: %s", ' '.join(write_test_command))

    proc = subprocess.run(write_test_command, capture_output=True, check=False)

    if proc.returncode != 0:
        return_val.append({"partName": "Write Test", "result": "Fail", "reason": "Unable to write to destination directory: {} on the Rsync Server: {}".format(dest_dir, gearman_worker.cruise_data_transfer['rsyncServer'])})

    else:

        os.remove(write_test_file)
        write_cleanup_command = ['rsync', '-vir', '--no-motd', '--password-file=' + rsync_password_filepath, '--delete', '--include=writeTest.txt', '--exclude=*', tmpdir + '/', 'rsync://' + gearman_worker.cruise_data_transfer['rsyncUser'] + '@' + gearman_worker.cruise_data_transfer['rsyncServer'] + dest_dir]

        logging.debug("Write test cleanup command: %s", ' '.join(write_cleanup_command))

        proc = subprocess.run(write_cleanup_command, capture_output=True, text=True, check=False)

        logging.debug(proc.stderr)

        if proc.returncode != 0:
            return_val.append({"partName": "Write Test", "result": "Fail", "reason": "Unable to write to destination directory: {} on the Rsync Server: {}".format(dest_dir, gearman_worker.cruise_data_transfer['rsyncServer'])})

        else:
            return_val.append({"partName": "Write Test", "result": "Pass"})

    # Cleanup
    shutil.rmtree(tmpdir)

    return return_val


def test_ssh_dest_dir(gearman_worker):
    """
    Verify the destination directory exists for a ssh server transfer
    """

    return_val = []

    server_test_command = ['ssh', gearman_worker.cruise_data_transfer['sshServer'], '-l', gearman_worker.cruise_data_transfer['sshUser'], '-o', 'StrictHostKeyChecking=no', 'PasswordAuthentication=no', 'ls'] if gearman_worker.cruise_data_transfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.cruise_data_transfer['sshPass'], 'ssh', gearman_worker.cruise_data_transfer['sshServer'], '-l', gearman_worker.cruise_data_transfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PubkeyAuthentication=no', 'ls']

    logging.debug("Connection test command: %s", ' '.join(server_test_command))

    proc = subprocess.run(server_test_command, capture_output=True, check=False)

    if proc.returncode != 0:
        return_val.extend([
            {"partName": "SSH Connection", "result": "Fail", "reason": "Unable to connect to ssh server: {} as {}".format(gearman_worker.cruise_data_transfer['sshServer'], gearman_worker.cruise_data_transfer['sshUser'])},
            {"partName": "Destination Directory", "result": "Fail", "reason": "Unable to connect to ssh server: {} as {}".format(gearman_worker.cruise_data_transfer['sshServer'], gearman_worker.cruise_data_transfer['sshUser'])},
            {"partName": "Write Test", "result": "Fail", "reason": "Unable to connect to ssh server: {} as {}".format(gearman_worker.cruise_data_transfer['sshServer'], gearman_worker.cruise_data_transfer['sshUser'])}
        ])
        return return_val

    return_val.append({"partName": "SSH Connection", "result": "Pass"})

    dest_dir = gearman_worker.cruise_data_transfer['destDir']

    dest_test_command = ['ssh', gearman_worker.cruise_data_transfer['sshServer'], '-l', gearman_worker.cruise_data_transfer['sshUser'], '-o', 'StrictHostKeyChecking=no', 'PasswordAuthentication=no', 'ls', dest_dir] if gearman_worker.cruise_data_transfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.cruise_data_transfer['sshPass'], 'ssh', gearman_worker.cruise_data_transfer['sshServer'], '-l', gearman_worker.cruise_data_transfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PubkeyAuthentication=no', 'ls', dest_dir]

    logging.debug("Destination test command: %s", dest_test_command)

    proc = subprocess.run(dest_test_command, capture_output=True, check=False)

    if proc.returncode != 0:
        return_val.extend([
            {"partName": "Destination Directory", "result": "Fail", "reason": "Unable to find destination directory: {} on the SSH Server: {}".format(dest_dir,gearman_worker.cruise_data_transfer['sshServer'])},
            {"partName": "Write Test", "result": "Fail", "reason": "Unable to find destination directory: {} on the SSH Server: {}".format(dest_dir,gearman_worker.cruise_data_transfer['sshServer'])}
        ])

        return return_val

    return_val.append({"partName": "Destination Directory", "result": "Pass"})

    write_test_command = ['ssh', gearman_worker.cruise_data_transfer['sshServer'], '-l', gearman_worker.cruise_data_transfer['sshUser'], '-o', 'StrictHostKeyChecking=no', 'PasswordAuthentication=no', 'touch ' + os.path.join(dest_dir, 'writeTest.txt')] if gearman_worker.cruise_data_transfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.cruise_data_transfer['sshPass'], 'ssh', gearman_worker.cruise_data_transfer['sshServer'], '-l', gearman_worker.cruise_data_transfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PubkeyAuthentication=no', 'touch ' + os.path.join(dest_dir, 'writeTest.txt')]

    logging.debug("Write test command: %s", write_test_command)

    proc = subprocess.run(write_test_command, capture_output=True, check=False)

    if proc.returncode != 0:
        return_val.append({"partName": "Write Test", "result": "Fail", "reason": "Unable to write to destination directory: {} on the SSH Server: {}".format(dest_dir, gearman_worker.cruise_data_transfer['sshServer'])})

        return return_val

    write_cleanup_command = ['ssh', gearman_worker.cruise_data_transfer['sshServer'], '-l', gearman_worker.cruise_data_transfer['sshUser'], '-o', 'StrictHostKeyChecking=no', 'PasswordAuthentication=no', 'rm ' + os.path.join(dest_dir, 'writeTest.txt')] if gearman_worker.cruise_data_transfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.cruise_data_transfer['sshPass'], 'ssh', gearman_worker.cruise_data_transfer['sshServer'], '-l', gearman_worker.cruise_data_transfer['sshUser'], '-o', 'StrictHostKeyChecking=no', '-o', 'PubkeyAuthentication=no', 'rm ' + os.path.join(dest_dir, 'writeTest.txt')]

    logging.debug("Write test cleanup command: %s", ' '.join(write_cleanup_command))

    proc = subprocess.run(write_cleanup_command, capture_output=True, check=False)

    if proc.returncode != 0:
        return_val.append({"partName": "Write Test", "result": "Fail", "reason": "Unable to cleanup test file from destination directory: {} on the SSH Server: {}".format(dest_dir, gearman_worker.cruise_data_transfer['sshServer'])})

        return return_val

    return_val.append({"partName": "Write Test", "result": "Pass"})

    return return_val


def test_source_dir(gearman_worker):
    """
    Verify the cruise directory exists
    """

    cruise_dir = os.path.join(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], gearman_worker.cruise_id)

    return [{"partName": "Source Directory", "result": "Pass"}] if os.path.isdir(cruise_dir) else [{"partName": "Source Directory", "result": "Fail", "reason": "Unable to find cruise directory: {} on the Data Warehouse".format(cruise_dir)}]


class OVDMGearmanWorker(python3_gearman.GearmanWorker):
    """
    Class for the current Gearman worker
    """

    def __init__(self):
        self.stop = False
        self.ovdm = OpenVDM()
        self.cruise_id = self.ovdm.get_cruise_id()
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

        if 'cruiseDataTransferID' in payload_obj['cruiseDataTransfer']:
            self.cruise_data_transfer = self.ovdm.get_cruise_data_transfer(payload_obj['cruiseDataTransfer']['cruiseDataTransferID'])

            if not self.cruise_data_transfer:
                logging.error("could not find configuration data")
                return self.on_job_complete(current_job, json.dumps({'parts':[{"partName": "Located Cruise Data Tranfer Data", "result": "Fail", "reason": "Could not find configuration data for cruise data transfer"},{"partName": "Final Verdict", "result": "Fail", "reason": "Could not find configuration data for cruise data transfer"}]}))

            self.cruise_data_transfer.update(payload_obj['cruiseDataTransfer'])

        else:
            self.cruise_data_transfer = payload_obj['cruiseDataTransfer']

        self.cruise_id = self.ovdm.get_cruise_id()

        logging.info("Job: %s, %s transfer test started at: %s", current_job.handle, self.cruise_data_transfer['name'], time.strftime("%D %T", time.gmtime()))

        self.shipboard_data_warehouse_config = self.ovdm.get_shipboard_data_warehouse_config()

        return super().on_job_execute(current_job)


    def on_job_exception(self, current_job, exc_info):
        """
        Function run whenever the current job has an exception
        """

        logging.error("Job: %s, %s transfer test failed at: %s", current_job.handle, self.cruise_data_transfer['name'], time.strftime("%D %T", time.gmtime()))

        self.send_job_data(current_job, json.dumps([{"partName": "Worker crashed", "result": "Fail", "reason": "Unknown"}]))

        if 'cruiseDataTransferID' in self.cruise_data_transfer:
            self.ovdm.set_error_cruise_data_transfer_test(self.cruise_data_transfer['cruiseDataTransferID'], 'Worker crashed')

        exc_type, _, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error(exc_type, fname, exc_tb.tb_lineno)
        return super().on_job_exception(current_job, exc_info)



    def on_job_complete(self, current_job, job_results):
        """
        Function run whenever the current job completes
        """

        results_obj = json.loads(job_results)

        if 'cruiseDataTransferID' in self.cruise_data_transfer:
            if len(results_obj['parts']) > 0:
                if results_obj['parts'][-1]['result'] == "Fail": # Final Verdict
                    self.ovdm.set_error_cruise_data_transfer_test(self.cruise_data_transfer['cruiseDataTransferID'], results_obj['parts'][-1]['reason'])
                else:
                    self.ovdm.clear_error_cruise_data_transfer(self.cruise_data_transfer['cruiseDataTransferID'], self.cruise_data_transfer['status'])
            else:
                self.ovdm.clear_error_cruise_data_transfer(self.cruise_data_transfer['cruiseDataTransferID'], self.cruise_data_transfer['status'])

        logging.debug("Job Results: %s", json.dumps(results_obj, indent=2))
        logging.info("Job: %s, %s transfer test completed at: %s", current_job.handle, self.cruise_data_transfer['name'], time.strftime("%D %T", time.gmtime()))

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


def task_test_cruise_data_transfer(gearman_worker, current_job):
    """
    Test the cruise data transfer
    """

    job_results = {'parts':[]}

    if 'cruiseDataTransferID' in gearman_worker.cruise_data_transfer:
        gearman_worker.ovdm.set_running_cruise_data_transfer_test(gearman_worker.cruise_data_transfer['cruiseDataTransferID'], os.getpid(), current_job.handle)

    gearman_worker.send_job_status(current_job, 1, 4)

    logging.info("Test Source Directory")
    job_results['parts'] = test_source_dir(gearman_worker)

    gearman_worker.send_job_status(current_job, 2, 4)

    logging.info("Test Destination Directory")
    if gearman_worker.cruise_data_transfer['transferType'] == "1": # Local Directory
        job_results['parts'] += test_local_dest_dir(gearman_worker)
    elif  gearman_worker.cruise_data_transfer['transferType'] == "2": # Rsync Server
        job_results['parts'] += test_rsync_dest_dir(gearman_worker)
    elif  gearman_worker.cruise_data_transfer['transferType'] == "3": # SMB Share
        job_results['parts'] += test_smb_dest_dir(gearman_worker)
    elif  gearman_worker.cruise_data_transfer['transferType'] == "4": # SSH Server
        job_results['parts'] += test_ssh_dest_dir(gearman_worker)

    gearman_worker.send_job_status(current_job, 3, 4)

    verdict = True
    for test in job_results['parts']:
        if test['result'] == "Fail":
            verdict = False
            job_results['parts'].append({"partName": "Final Verdict", "result": "Fail", "reason": test['reason']})
            break

    if verdict:
        job_results['parts'].append({"partName": "Final Verdict", "result": "Pass"})

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

    logging.info("\tTask: testCruiseDataTransfer")
    new_worker.register_task("testCruiseDataTransfer", task_test_cruise_data_transfer)

    logging.info("Waiting for jobs...")
    new_worker.work()
