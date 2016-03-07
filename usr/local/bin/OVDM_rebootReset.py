# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_rebootReset.py
#
#  DESCRIPTION:  This program reset OVDM state information in the database.
#
#        USAGE: OVDM_rebootReset.py <siteRoot>
#
#    ARGUMENTS: <siteRoot> The base URL to the OpenVDM installation on the Shipboard
#                     Data Warehouse.
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.1rc
#      CREATED:  2015-06-22
#     REVISION:  2016-03-07
#
# LICENSE INFO: Open Vessel Data Management (OpenVDM) Copyright (C) 2016  Webb Pinner
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
import openvdm
    
def main(argv):
    
    openVDM = openvdm.OpenVDM()
    
    time.sleep(5)
        
    tasks = openVDM.getTasks()
    for task in tasks:
        openVDM.setIdle_task(task['taskID'])
    
    collectionSystemTransfers = openVDM.getCollectionSystemTransfers()
    for collectionSystemTransfer in collectionSystemTransfers:
        if not collectionSystemTransfer['status'] == '3':
            openVDM.setIdle_collectionSystemTransfer(collectionSystemTransfer['collectionSystemTransferID'])
            
    cruiseDataTransfers = openVDM.getCruiseDataTransfers()
    for cruiseDataTransfer in cruiseDataTransfers:
        if not cruiseDataTransfer['status'] == '3':
            openVDM.setIdle_cruiseDataTransfer(cruiseDataTransfer['cruiseDataTransferID'])
            
    requiredCruiseDataTransfers = openVDM.getRequiredCruiseDataTransfers()
    for requiredCruiseDataTransfer in requiredCruiseDataTransfers:
        if not requiredCruiseDataTransfer['status'] == '3':
            openVDM.setIdle_cruiseDataTransfer(requiredCruiseDataTransfer['cruiseDataTransferID'])

    openVDM.clearGearmanJobsFromDB()

if __name__ == "__main__":
    main(sys.argv[1:])
