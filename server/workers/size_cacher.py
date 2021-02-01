# ----------------------------------------------------------------------------------- #
#
#         FILE:  size_cacher.py
#
#  DESCRIPTION:  This program handles calculating the cruise and lowering
#                    directory sizes.
#
#        USAGE: size_cacher.py [--interval <interval>]
#
#    ARGUMENTS: --interval <interval> The minimum interval in second between directory
#                    size calculations.
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.5
#      CREATED:  2017-09-30
#     REVISION:  2021-01-02
#
# LICENSE INFO: Open Vessel Data Management v2.5 (OpenVDMv2)
#               Copyright (C) OceanDataRat.org 2021
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

import sys
import time
import datetime
import argparse
import subprocess
import json
import logging
import python3_gearman

from os.path import dirname, realpath, join, isdir
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.lib.openvdm import OpenVDM_API

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

    openVDM = OpenVDM_API()

    while True:

        start_t = datetime.datetime.utcnow()

        warehouseConfig = openVDM.getShipboardDataWarehouseConfig()

        warehouseBaseDir = warehouseConfig['shipboardDataWarehouseBaseDir']
        cruiseDir = join(warehouseBaseDir, openVDM.getCruiseID())
        loweringID = openVDM.getLoweringID() if openVDM.getShowLoweringComponents() else None
        loweringDir = join(cruiseDir, warehouseConfig['loweringDataBaseDir'], loweringID) if loweringID else None
        
        logging.debug("Cruise Directory: {}".format(cruiseDir))
        logging.debug("Lowering Directory: {}".format(loweringDir))

        if isdir(cruiseDir):
            logging.debug("Calculating Cruise Size...")
            cruiseSizeProc = subprocess.run(['du','-sb', cruiseDir], capture_output=True, text=True)
            if cruiseSizeProc.returncode == 0:
                logging.info("Cruise Size: {}".format(cruiseSizeProc.stdout.split()[0]))
                openVDM.set_cruiseSize(cruiseSizeProc.stdout.split()[0])

        if loweringID and isdir(loweringDir):
            logging.debug("Calculating Lowering Size...")
            loweringSizeProc = subprocess.run(['du','-sb', loweringDir], capture_output=True, text=True)
            if loweringSizeProc.returncode == 0:
                logging.info("Lowering Size: {}".format(loweringSizeProc.stdout.split()[0]))
                openVDM.set_loweringSize(loweringSizeProc.stdout.split()[0])

        end_t = datetime.datetime.utcnow()

        elapse_t = end_t - start_t
        logging.debug("Total Seconds: {}".format(elapse_t.total_seconds()))
       
        if (elapse_t.total_seconds()) >= parsed_args.interval:
            continue;
        else:
            logging.info("Calculating size again in {} seconds".format(parsed_args.interval - elapse_t.total_seconds()))
            time.sleep(parsed_args.interval - elapse_t.total_seconds())
