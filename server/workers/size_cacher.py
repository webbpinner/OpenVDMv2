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
import python3_gearman

from os.path import dirname, realpath
append(dirname(dirname(dirname(realpath(__file__)))))

from server.lib.openvdm import OpenVDM_API

openVDM = openvdm.OpenVDM()


def getCruiseDir():

    global openVDM

    warehouse = openVDM.getShipboardDataWarehouseConfig()
    cruiseID = openVDM.getCruiseID()
    cruiseDir = os.path.join(warehouse['shipboardDataWarehouseBaseDir'], cruiseID)

    # print cruiseDir;
    if os.path.isdir(cruiseDir):
        return cruiseDir;

    return False

def getLoweringDir():

    global openVDM

    warehouse = openVDM.getShipboardDataWarehouseConfig()
    cruiseID = openVDM.getCruiseID()
    loweringID = openVDM.getLoweringID()
    loweringDir = os.path.join(warehouse['shipboardDataWarehouseBaseDir'], cruiseID, warehouse['loweringDataBaseDir'], loweringID)

    # print loweringDir;
    if os.path.isdir(loweringDir):
        return loweringDir;

    return False
    
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='OpenVDM Directory Size Cacher')
    parser.add_argument('--interval', default=openVDM.getTransferInterval(), metavar='interval', type=int, help='Maximum update rate in seconds')
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

        warehouseBaseDir = warehouse['shipboardDataWarehouseBaseDir']
        cruiseDir = os.path.join(warehouseBaseDir, openVDM.getCruiseID())
        loweringDir = os.path.join(warehouseBaseDir, warehouse['loweringDataBaseDir'], openVDM.getLoweringID())

        if os.path.isdir(cruiseDir):
            logging.info("Calculating Cruise Size...")
            # pre_cruise_size_t = start_t
            cruiseSize = subprocess.check_output(['du','-sb', cruiseDir]).split()[0].decode('utf-8')
            logging.debug("Cruise Size: {}", cruiseSize)
            openVDM.set_cruiseSize(cruiseSize)

            # existingCruiseSize = openVDM.getCruiseSize()
            # print existingCruiseSize['cruiseSizeUpdated']

            # existing_cruise_size_t = datetime.datetime.strptime(existingCruiseSize['cruiseSizeUpdated'], "%Y/%m/%d %H:%M:%S")

            # elapse_t = existing_cruise_size_t - pre_cruise_size_t
            # print "Total Seconds:", elapse_t.total_seconds()
            # if elapse_t.total_seconds() < 0:
                # openVDM.set_cruiseSize(cruiseSize)
            # else:
                # print "size in db is more recent"

        # else:
        #     print "Cruise directory not found"
        #     openVDM.set_cruiseSize('')
        
        # loweringDir = getLoweringDir()

        if os.path.isdir(loweringDir):
            logging.info("Calculating Lowering Size...")
            # pre_lowering_size_t = start_t
            loweringSize = subprocess.check_output(['du','-sb', loweringDir]).split()[0].decode('utf-8')
            logging.debug("Lowering Size: {}", loweringSize)
            openVDM.set_loweringSize(loweringSize)
            # print loweringSize

        #     existingLoweringSize = openVDM.getLoweringSize()
        #     # print existingLoweringSize['loweringSizeUpdated']

        #     existing_lowering_size_t = datetime.datetime.strptime(existingLoweringSize['loweringSizeUpdated'], "%Y/%m/%d %H:%M:%S")

        #     elapse_t = existing_lowering_size_t - pre_lowering_size_t
        #     # print "Total Seconds:", elapse_t.total_seconds()
        #     if elapse_t.total_seconds() < 0:
        #         openVDM.set_loweringSize(loweringSize)
        #     else:
        #         print "size in db is more recent"

        # else:
        #     print "Lowering directory not found"
        #     openVDM.set_loweringSize('')

        end_t = datetime.datetime.utcnow()

        elapse_t = end_t - start_t
        lowering.debug("Total Seconds: {}".format(elapse_t.total_seconds()))
        if (elapse_t.total_seconds()) >= parsed_args.interval:
            continue;
        else:
            time.sleep(parsed_args.interval - elapse_t.total_seconds())
