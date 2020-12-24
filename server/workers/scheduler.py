# ----------------------------------------------------------------------------------- #
#
#         FILE:  OVDM_scheduler.py
#
#  DESCRIPTION:  This program handles the scheduling of the transfer-related Gearman
#                tasks.
#
#        USAGE: OVDM_scheduler.py [--interval <interval>] <siteRoot>
#
#    ARGUMENTS: --interval <interval> The interval in minutes between transfer job
#                    submissions.  If this argument is not provided the default inteval
#                    is 5 minutes
#
#                <siteRoot> The base URL to the OpenVDM installation on the Shipboard
#                     Data Warehouse.
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.4
#      CREATED:  2015-01-01
#     REVISION:  2020-11-19
#
# LICENSE INFO: Open Vessel Data Management v2.4 (OpenVDMv2)
#               Copyright (C) OceanDataRat.org 2020
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
#import urlparse
import json
import gearman
import openvdm
    
def main(argv):
    
    time.sleep(10)
    
    openVDM = openvdm.OpenVDM()
    
    parser = argparse.ArgumentParser(description='OpenVDM Data Transfer Scheduler')
    #parser.add_argument('--siteRoot', default=openVDM.getSiteRoot(), metavar='siteRoot', help='the base URL for this OpenVDM installation')
    parser.add_argument('--interval', default=openVDM.getTransferInterval(), metavar='interval', type=int, help='Delay in minutes')

    args = parser.parse_args()
    #print args.siteRoot
    #parsed_url = urlparse.urlparse(args.siteRoot)
    #print parsed_url
    #if not bool(parsed_url.scheme) or not bool(parsed_url.netloc):
    #    print args.siteRoot + " is not a valid URL" 
    #    sys.exit(1)
    
    gm_client = gearman.GearmanClient([openVDM.getGearmanServer()])
    
    while True:
        
        current_sec = 0
        while True:
            t = time.gmtime()
            if current_sec < t.tm_sec:
                current_sec = t.tm_sec
                time.sleep(60-t.tm_sec)
            else:
                break

        collectionSystemTransfers = openVDM.getActiveCollectionSystemTransfers()
        for collectionSystemTransfer in collectionSystemTransfers:
            print 'Submitting collection system transfer job for: ' + collectionSystemTransfer['longName']

            gmData = {}
            gmData['collectionSystemTransfer'] = {}
            gmData['collectionSystemTransfer']['collectionSystemTransferID'] = collectionSystemTransfer['collectionSystemTransferID']
            #print json.dumps(gmData, indent=2)

            completed_job_request = gm_client.submit_job("runCollectionSystemTransfer", json.dumps(gmData), background=True)
            #resultsObj = json.loads(completed_job_request.result)
            time.sleep(2)

            
        cruiseDataTransfers = openVDM.getCruiseDataTransfers()
        for cruiseDataTransfer in cruiseDataTransfers:
            print 'Submitting cruise data transfer job for: ' + cruiseDataTransfer['longName']

            gmData = {}
            gmData['cruiseDataTransfer'] = {}
            gmData['cruiseDataTransfer']['cruiseDataTransferID'] = cruiseDataTransfer['cruiseDataTransferID']
            #print json.dumps(gmData, indent=2)

            completed_job_request = gm_client.submit_job("runCruiseDataTransfer", json.dumps(gmData), background=True)
            #resultsObj = json.loads(completed_job_request.result)
            time.sleep(2)
            
        requiredCruiseDataTransfers = openVDM.getRequiredCruiseDataTransfers()
        for requiredCruiseDataTransfer in requiredCruiseDataTransfers:
            if requiredCruiseDataTransfer['name'] == 'SSDW':
                print 'Submitting cruise data transfer job for: ' + requiredCruiseDataTransfer['longName']

                gmData = {}
                completed_job_request = gm_client.submit_job("runShipToShoreTransfer", json.dumps(gmData), background=True)
                #resultsObj = json.loads(completed_job_request.result)

            time.sleep(2)
        
        delay = args.interval * 60 - len(collectionSystemTransfers) * 2 - len(cruiseDataTransfers) * 2 - 2
        #print delay
        time.sleep(delay)

if __name__ == "__main__":
    main(sys.argv[1:])
