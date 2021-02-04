#!/usr/bin/env python3
"""

FILE:  size_cacher.py

DESCRIPTION:  This program handles calculating the cruise and lowering
                directory sizes.

USAGE: size_cacher.py [--interval <interval>]

ARGUMENTS: --interval <interval> The minimum interval in second between directory
    size calculations.

     BUGS:
    NOTES:
   AUTHOR:  Webb Pinner
  COMPANY:  Capable Solutions
  VERSION:  2.5
  CREATED:  2017-09-30
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

import sys
import time
import datetime
import argparse
import subprocess
import logging

from os.path import dirname, realpath, join, isdir
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.lib.openvdm import OpenVDM

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='OpenVDM Directory Size Cacher')
    parser.add_argument('--interval', default=10, metavar='interval', type=int, help='Maximum update rate in seconds')
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

    while True:

        start_t = datetime.datetime.utcnow()

        warehouse_config = openVDM.get_shipboard_data_warehouse_config()
        cruise_dir = join(warehouse_config['shipboardDataWarehouseBaseDir'], openVDM.get_cruise_id())

        lowering_id = openVDM.get_lowering_id() if openVDM.get_show_lowering_components() else None
        lowering_dir = join(cruise_dir, warehouse_config['loweringDataBaseDir'], lowering_id) if lowering_id else None

        logging.debug("Cruise Directory: %s", cruise_dir)
        logging.debug("Lowering Directory: %s", lowering_dir)

        if isdir(cruise_dir):
            logging.debug("Calculating Cruise Size...")
            cruise_size_proc = subprocess.run(['du','-sb', cruise_dir], capture_output=True, text=True, check=False)
            if cruise_size_proc.returncode == 0:
                logging.info("Cruise Size: %s", cruise_size_proc.stdout.split()[0])
                openVDM.set_cruise_size(cruise_size_proc.stdout.split()[0])

        if lowering_dir and isdir(lowering_dir):
            logging.debug("Calculating Lowering Size...")
            loweringSizeProc = subprocess.run(['du','-sb', lowering_dir], capture_output=True, text=True, check=False)
            if loweringSizeProc.returncode == 0:
                logging.info("Lowering Size: %s", loweringSizeProc.stdout.split()[0])
                openVDM.set_lowering_size(loweringSizeProc.stdout.split()[0])

        end_t = datetime.datetime.utcnow()

        elapse_t = end_t - start_t
        logging.debug("Total Seconds: %s", elapse_t.total_seconds())

        if (elapse_t.total_seconds()) >= parsed_args.interval:
            continue

        logging.info("Calculating size again in %s seconds", parsed_args.interval - elapse_t.total_seconds())
        time.sleep(parsed_args.interval - elapse_t.total_seconds())
