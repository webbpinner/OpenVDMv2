#!/usr/bin/env python3
"""

FILE:  reboot_reset.py

DESCRIPTION:  This program resets OVDM state information in the database.

     BUGS:
    NOTES:
   AUTHOR:  Webb Pinner
  COMPANY:  Capable Solutions
  VERSION:  2.5
  CREATED:  2015-06-22
 REVISION:  2020-12-30

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

import sys
import time
import argparse
import logging

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.lib.openvdm import OpenVDM

# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Handle resetting OpenVDM database after an unscheduled system reboot')
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

    openVDM = OpenVDM()

    time.sleep(5)

    logging.info("Setting all tasks to idle.")
    tasks = openVDM.get_tasks()
    for task in tasks:
        openVDM.set_idle_task(task['taskID'])

    logging.info("Setting all Collection System Transfers to idle.")
    collection_system_transfers = openVDM.get_collection_system_transfers()
    for collection_system_transfer in collection_system_transfers:
        if not collection_system_transfer['status'] == '3':
            openVDM.set_idle_collection_system_transfer(collection_system_transfer['collectionSystemTransferID'])

    logging.info("Setting all Cruise Data Transfers to idle.")
    cruise_data_transfers = openVDM.get_cruise_data_transfers()
    for cruise_data_transfer in cruise_data_transfers:
        if not cruise_data_transfer['status'] == '3':
            openVDM.set_idle_cruise_data_transfer(cruise_data_transfer['cruiseDataTransferID'])

    required_cruise_data_transfers = openVDM.get_required_cruise_data_transfers()
    for required_cruise_data_transfer in required_cruise_data_transfers:
        if not required_cruise_data_transfer['status'] == '3':
            openVDM.set_idle_cruise_data_transfer(required_cruise_data_transfer['cruiseDataTransferID'])

    logging.info("Clearing all jobs from Gearman.")
    openVDM.clear_gearman_jobs_from_db()

    logging.info("Done!")
