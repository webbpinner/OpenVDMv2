#!/usr/bin/env python3
"""

FILE:  scheduler.py

DESCRIPTION:  This program handles the scheduling of the transfer-related Gearman
    tasks.

    USAGE: scheduler.py [--interval <interval>] <siteRoot>

ARGUMENTS: --interval <interval> The interval in minutes between transfer job
            submissions.  If this argument is not provided the default inteval
            is 5 minutes

            <siteRoot> The base URL to the OpenVDM installation on the Shipboard
             Data Warehouse.

     BUGS:
    NOTES:
   AUTHOR:  Webb Pinner
  COMPANY:  Capable Solutions
  VERSION:  2.5
  CREATED:  2015-01-01
 REVISION:  2020-12-31

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
import json
import logging
from os.path import dirname, realpath
from python3_gearman import GearmanClient

sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.lib.openvdm import OpenVDM


if __name__ == "__main__":

    openVDM = OpenVDM()

    parser = argparse.ArgumentParser(description='OpenVDM Data Transfer Scheduler')
    parser.add_argument('-i', '--interval', default=openVDM.get_transfer_interval(), metavar='interval', type=int, help='interval in minutes')
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

    logging.debug("Creating Geaman Client...")
    gm_client = GearmanClient([openVDM.get_gearman_server()])

    time.sleep(10)

    while True:

        CURRENT_SEC = 0
        while True:
            t = time.gmtime()
            if CURRENT_SEC < t.tm_sec:
                CURRENT_SEC = t.tm_sec
                time.sleep(60-t.tm_sec)
            else:
                break

        collection_system_transfers = openVDM.get_active_collection_system_transfers()
        for collection_system_transfer in collection_system_transfers:
            logging.info("Submitting collection system transfer job for: %s", collection_system_transfer['longName'])

            gmData = {
                'collectionSystemTransfer': {
                    'collectionSystemTransferID': collection_system_transfer['collectionSystemTransferID']
                }
            }

            completed_job_request = gm_client.submit_job("runCollectionSystemTransfer", json.dumps(gmData), background=True)

            time.sleep(2)


        cruise_data_transfers = openVDM.get_cruise_data_transfers()
        for cruise_data_transfer in cruise_data_transfers:
            logging.info("Submitting cruise data transfer job for: %s", cruise_data_transfer['longName'])

            gmData = {
                'cruiseDataTransfer': {
                    'cruiseDataTransferID': cruise_data_transfer['cruiseDataTransferID']
                }
            }

            completed_job_request = gm_client.submit_job("runCruiseDataTransfer", json.dumps(gmData), background=True)

            time.sleep(2)

        required_cruise_data_transfers = openVDM.get_required_cruise_data_transfers()
        for required_cruise_data_transfer in required_cruise_data_transfers:
            if required_cruise_data_transfer['name'] == 'SSDW':
                logging.info("Submitting cruise data transfer job for: %s", required_cruise_data_transfer['longName'])

                gmData = {
                }

                completed_job_request = gm_client.submit_job("runShipToShoreTransfer", json.dumps(gmData), background=True)

            time.sleep(2)

        delay = parsed_args.interval * 60 - len(collection_system_transfers) * 2 - len(cruise_data_transfers) * 2 - 2
        logging.info("Waiting %s seconds until next round of tasks are queued", delay)
        time.sleep(delay)
