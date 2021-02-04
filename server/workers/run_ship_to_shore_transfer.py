#!/usr/bin/env python3
"""
     FILE:  run_ship_to_shore_transfer.py

DESCRIPTION:  Gearman worker that handles the transfer of data from the
Shipboard Data Warehouse to a Shoreside Data Warehouse.

     BUGS:
    NOTES:
   AUTHOR:  Webb Pinner
  COMPANY:  Capable Solutions
  VERSION:  2.5
  CREATED:  2015-01-01
 REVISION:  2021-01-05

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

from server.utils.output_json_data_to_file import output_json_data_to_file
from server.utils.set_owner_group_permissions import set_owner_group_permissions
from server.lib.openvdm import OpenVDM

def build_filelist(gearman_worker):
    """
    Build the list of files for the ship-to-shore transfer
    """

    logging.debug("Building filters")
    raw_filters = {'includeFilter':[]}
    ship_to_shore_transfers = gearman_worker.ovdm.get_ship_to_shore_transfers() + gearman_worker.ovdm.get_required_ship_to_shore_transfers()

    logging.debug('shipToShoreTransfers: %s', json.dumps(ship_to_shore_transfers, indent=2))

    for priority in range(1, 6):
        for ship_to_shore_transfer in ship_to_shore_transfers:
            if ship_to_shore_transfer['priority'] == str(priority) and ship_to_shore_transfer['enable'] == '1':
                if not ship_to_shore_transfer['collectionSystem'] == "0":
                    collection_system = gearman_worker.ovdm.get_collection_system_transfer(ship_to_shore_transfer['collectionSystem'])
                    raw_filters['includeFilter'] += ['*/' + gearman_worker.cruise_id + '/' + collection_system['destDir'] + '/' + ship_to_shore_filter for ship_to_shore_filter in ship_to_shore_transfer['includeFilter'].split(',')]
                elif not ship_to_shore_transfer['extraDirectory'] == "0":
                    extra_directory = gearman_worker.ovdm.get_extra_directory(ship_to_shore_transfer['extraDirectory'])
                    raw_filters['includeFilter'] += ['*/' + gearman_worker.cruise_id + '/' + extra_directory['destDir'] + '/' + ship_to_shore_filter for ship_to_shore_filter in ship_to_shore_transfer['includeFilter'].split(',')]
                else:
                    raw_filters['includeFilter'] += ['*/' + gearman_worker.cruise_id + '/' + ship_to_shore_filter for ship_to_shore_filter in ship_to_shore_transfer['includeFilter'].split(',')]

    logging.debug("Raw Filters: %s", json.dumps(raw_filters, indent=2))

    proc_filters = build_filters(gearman_worker, raw_filters)
    logging.debug("Processed Filters: %s", json.dumps(raw_filters, indent=2))

    cruise_dir = os.path.join(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], gearman_worker.cruise_id)

    return_files = {'include':[], 'new':[], 'updated':[], 'exclude':[]}
    for root, _, filenames in os.walk(cruise_dir):
        for filename in filenames:
            for include_filter in proc_filters['includeFilter']:
                if fnmatch.fnmatch(os.path.join(root, filename), include_filter):
                    return_files['include'].append(os.path.join(root, filename))

    return_files['include'] = [filename.replace(cruise_dir + '/', '', 1) for filename in return_files['include']]

    logging.debug("Returned Files: %s", json.dumps(return_files, indent=2))

    return { 'verdict': True, 'files': return_files }


def build_logfile_dirpath(gearman_worker):
    """
    Build the path for saving the transfer logfile
    """
    cruise_dir = os.path.join(gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], gearman_worker.cruise_id)

    return os.path.join(cruise_dir, gearman_worker.ovdm.get_required_extra_directory_by_name('Transfer_Logs')['destDir'])


def build_filters(gearman_worker, raw_filters):
    """
    Replace any wildcards in the provided filters
    """

    return_filters = raw_filters
    return_filters['includeFilter'] = [include_filter.replace('{cruiseID}', gearman_worker.cruise_id) for include_filter in return_filters['includeFilter']]

    return return_filters


def transfer_ssh_dest_dir(gearman_worker, gearman_job):
    """
    Transfer the files to a destination on a ssh server
    """

    logging.debug("Transfer to SSH Server")

    logging.debug("Building file list")
    output_results = build_filelist(gearman_worker)

    if not output_results['verdict']:
        logging.error("Building list of files to transfer failed: %s", output_results['reason'])
        return output_results

    files = output_results['files']

    dest_dir = gearman_worker.cruise_data_transfer['destDir'].rstrip('/')

    # Create temp directory
    tmpdir = tempfile.mkdtemp()

    ssh_includelist_filepath = os.path.join(tmpdir, 'sshIncludeList.txt')

    file_index = 0
    file_count = len(files['include'])

    try:
        with open(ssh_includelist_filepath, 'w') as ssh_include_filelist_filepath:
            ssh_include_filelist_filepath.write('\n'.join([os.path.join(gearman_worker.cruise_id, filename) for filename in files['include']]))

    except IOError:
        logging.debug("Error Saving temporary ssh include filelist file")

        # Cleanup
        shutil.rmtree(tmpdir)

        return {'verdict': False, 'reason': 'Error Saving temporary ssh exclude filelist file: ' + ssh_includelist_filepath, 'files':[]}

    bw_limit = '--bwlimit=' + gearman_worker.cruise_data_transfer['bandwidthLimit'] if gearman_worker.cruise_data_transfer['bandwidthLimit'] != '0' else '--bwlimit=20000000' # 20GB/s a.k.a. stupid big

    command = ['rsync', '-trim', bw_limit, '--files-from=' + ssh_includelist_filepath, '-e', 'ssh', gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], gearman_worker.cruise_data_transfer['sshUser'] + '@' + gearman_worker.cruise_data_transfer['sshServer'] + ':' + dest_dir] if gearman_worker.cruise_data_transfer['sshUseKey'] == '1' else ['sshpass', '-p', gearman_worker.cruise_data_transfer['sshPass'], 'rsync', '-trim', bw_limit, '--files-from=' + ssh_includelist_filepath, '-e', 'ssh', gearman_worker.shipboard_data_warehouse_config['shipboardDataWarehouseBaseDir'], gearman_worker.cruise_data_transfer['sshUser'] + '@' + gearman_worker.cruise_data_transfer['sshServer'] + ':' + dest_dir]

    logging.debug("Transfer Command: %s", ' '.join(command))

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)

    while True:

        line = proc.stdout.readline().rstrip('\n')

        if proc.poll() is not None:
            break

        if not line:
            continue

        logging.debug("Line: %s", line)
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

    # files['new'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/').rstrip('/'),filename) for filename in files['new']]
    # files['updated'] = [os.path.join(destDir.replace(cruiseDir, '').lstrip('/').rstrip('/'),filename) for filename in files['updated']]

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
        self.transfer_start_date = None
        self.cruise_data_transfer = self._get_cruise_data_transfer()
        self.shipboard_data_warehouse_config = self.ovdm.get_shipboard_data_warehouse_config()
        super().__init__(host_list=[self.ovdm.get_gearman_server()])

    def _get_cruise_data_transfer(self):
        """
        Fetch the ship-to-shore transfer configuration
        """

        try:
            return list(filter(lambda transfer: transfer['name'] == 'SSDW', self.ovdm.get_required_cruise_data_transfers()))[0]
        except Exception as err:
            logging.error("Could not find SSDW transfer configuration")
            logging.debug(str(err))
        return None

    def on_job_execute(self, current_job):
        """
        Function run whenever a new job arrives
        """

        logging.debug("current_job: %s", current_job)

        self.stop = False
        payload_obj = json.loads(current_job.data)

        self.cruise_data_transfer = self._get_cruise_data_transfer()
        if not self.cruise_data_transfer:
            return self.on_job_complete(current_job, json.dumps({'parts':[{"partName": "Transfer Found", "result": "Fail", "reason": "Transfer configuration not found"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

        if 'cruiseDataTransfer' in payload_obj:
            self.cruise_data_transfer.update(payload_obj['cruiseDataTransfer'])

        self.system_status = payload_obj['systemStatus'] if 'systemStatus' in payload_obj else self.ovdm.get_system_status()

        if self.system_status == "Off" or self.cruise_data_transfer['enable'] == '0':
            logging.info("Ship-to-shore Transfer job skipped because ship-to-shore transfers are currently disabled")
            return self.on_job_complete(current_job, json.dumps({'parts':[{"partName": "Transfer Enabled", "result": "Ignore", "reason": "Transfer is disabled"}], 'files':{'new':[],'updated':[], 'exclude':[]}}))

        bw_limit_status = payload_obj['bandwidthLimitStatus'] if 'bandwidthLimitStatus' in payload_obj else self.ovdm.get_ship_to_shore_bw_limit_status()
        if not bw_limit_status:
            self.cruise_data_transfer['bandwidthLimit'] = '0'

        self.cruise_id = payload_obj['cruiseID'] if 'cruiseID' in payload_obj else self.ovdm.get_cruise_id()
        self.transfer_start_date = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

        logging.info("Job: %s, Ship-to-Shore transfer started at: %s", current_job.handle, time.strftime("%D %T", time.gmtime()))

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


def task_run_ship_to_shore_transfer(gearman_worker, current_job): # pylint: disable=too-many-statements
    """
    Perform the ship-to-shore transfer
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
    if  gearman_worker.cruise_data_transfer['transferType'] == "4": # SSH Server
        output_results = transfer_ssh_dest_dir(gearman_worker, current_job)
    else:
        logging.error("Unknown Transfer Type")
        job_results['parts'].append({"partName": "Transfer Files", "result": "Fail", "reason": "Unknown transfer type"})
        return json.dumps(job_results)

    if not output_results['verdict']:
        logging.error("Transfer of remote files failed: %s", output_results['reason'])
        job_results['parts'].append({"partName": "Transfer Files", "result": "Fail", "reason": output_results['reason']})
        return job_results

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

    if job_results['files']['new'] or job_results['files']['updated']:

        logging.debug("Building logfiles")

        logfile_filename = gearman_worker.cruise_data_transfer['name'] + '_' + gearman_worker.transfer_start_date + '.log'

        log_contents = {
            'files': {
                'new': job_results['files']['new'],
                'updated': job_results['files']['updated']
            }
        }

        output_results = output_json_data_to_file(os.path.join(build_logfile_dirpath(gearman_worker), logfile_filename), log_contents['files'])

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

    gearman_worker.send_job_status(current_job, 10, 10)

    time.sleep(2)

    return json.dumps(job_results)


# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle ship-to-shore transfer related tasks')
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

    logging.info("\tTask: runShipToShoreTransfer")
    new_worker.register_task("runShipToShoreTransfer", task_run_ship_to_shore_transfer)

    logging.info("Waiting for jobs...")
    new_worker.work()
