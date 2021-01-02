# ----------------------------------------------------------------------------------- #
#
#         FILE:  reboot_reset.py
#
#  DESCRIPTION:  This program resets OVDM state information in the database.
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.5
#      CREATED:  2015-06-22
#     REVISION:  2020-12-30
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
import argparse
import logging

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

from server.lib.openvdm import OpenVDM_API

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

    openVDM = OpenVDM_API()
    
    time.sleep(5)
        
    logging.info("Setting all tasks to idle.")
    tasks = openVDM.getTasks()
    for task in tasks:
        openVDM.setIdle_task(task['taskID'])
    
    logging.info("Setting all Collection System Transfers to idle.")
    collectionSystemTransfers = openVDM.getCollectionSystemTransfers()
    for collectionSystemTransfer in collectionSystemTransfers:
        if not collectionSystemTransfer['status'] == '3':
            openVDM.setIdle_collectionSystemTransfer(collectionSystemTransfer['collectionSystemTransferID'])
            
    logging.info("Setting all Cruise Data Transfers to idle.")
    cruiseDataTransfers = openVDM.getCruiseDataTransfers()
    for cruiseDataTransfer in cruiseDataTransfers:
        if not cruiseDataTransfer['status'] == '3':
            openVDM.setIdle_cruiseDataTransfer(cruiseDataTransfer['cruiseDataTransferID'])
            
    requiredCruiseDataTransfers = openVDM.getRequiredCruiseDataTransfers()
    for requiredCruiseDataTransfer in requiredCruiseDataTransfers:
        if not requiredCruiseDataTransfer['status'] == '3':
            openVDM.setIdle_cruiseDataTransfer(requiredCruiseDataTransfer['cruiseDataTransferID'])

    logging.info("Clearing all jobs from Gearman.")
    openVDM.clearGearmanJobsFromDB()

    logging.info("Done!")
