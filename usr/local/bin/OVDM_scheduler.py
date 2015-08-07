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
#      VERSION:  2.0
#      CREATED:  2015-01-01
#     REVISION:  2015-06-09
#
# LICENSE INFO: Open Vessel Data Management (OpenVDM) Copyright (C) 2015  Webb Pinner
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
import requests
import datetime
import argparse
import urlparse
import json
import gearman

def getWarehouseConfig(siteRoot):
    url = siteRoot + 'api/warehouse/getShipboardDataWarehouseConfig'
    try:
        r = requests.get(url)
	#print json.dumps(r.json(), indent=2)
        return r.json()

    except requests.exceptions.RequestException as e: 
        print "Error retrieving warehouse data, check URL"
        sys.exit(1)

def getCollectionSystemTransfers(siteRoot):
    url = siteRoot + 'api/collectionSystemTransfers/getCollectionSystemTransfers'
    try:
        r = requests.get(url)
        return r.json()

    except requests.exceptions.RequestException as e: 
        print "Error retrieving collectionSystemTransfer data, check URL"
        sys.exit(1)
        
def getCruiseDataTransfers(siteRoot):
    url = siteRoot + 'api/cruiseDataTransfers/getCruiseDataTransfers'
    try:
        r = requests.get(url)
        return r.json()

    except requests.exceptions.RequestException as e: 
        print "Error retrieving cruiseDataTransfer data, check URL"
        sys.exit(1)
        
def getRequiredCruiseDataTransfers(siteRoot):
    url = siteRoot + 'api/cruiseDataTransfers/getRequiredCruiseDataTransfers'
    try:
        r = requests.get(url)
        return r.json()

    except requests.exceptions.RequestException as e: 
        print "Error retrieving cruiseDataTransfer data, check URL"
        sys.exit(1)

def getCruiseID(siteRoot):
    url = siteRoot + 'api/warehouse/getCruiseID'
    try:
        r = requests.get(url)
        return r.json()

    except requests.exceptions.RequestException as e: 
        print "Error retrieving warehouse data, check URL"
        sys.exit(1)
        
def getSystemStatus(siteRoot):
    url = siteRoot + 'api/warehouse/getSystemStatus'
    try:
        r = requests.get(url)
        return r.json()

    except requests.exceptions.RequestException as e: 
        print "Error retrieving warehouse data, check URL"
        sys.exit(1)
    
def main(argv):
    parser = argparse.ArgumentParser(description='OpenVDM Data Transfer Scheduler')
    parser.add_argument('siteRoot', metavar='siteRoot', help='the base URL for this OpenVDM installation')
    parser.add_argument('--interval', type=int, default=5, help='Delay in minutes')

    args = parser.parse_args()
    #print args.siteRoot
    parsed_url = urlparse.urlparse(args.siteRoot)
    #print parsed_url
    if not bool(parsed_url.scheme) or not bool(parsed_url.netloc):
        print args.siteRoot + " is not a valid URL" 
        sys.exit(1)
    
    warehouseConfig = getWarehouseConfig(args.siteRoot)
    #print json.dumps(warehouseConfig, indent=2)
    
    while True:
        
        current_sec = 0
        while True:
            t = time.gmtime()
            if current_sec < t.tm_sec:
                current_sec = t.tm_sec
                time.sleep(60-t.tm_sec)
            else:
                break

        collectionSystemTransfers = getCollectionSystemTransfers(args.siteRoot)
        for collectionSystemTransfer in collectionSystemTransfers:
            #print 'Submitting data transfer job for: ' + collectionSystemTransfer['name']

            gmData = {}
            gmData['siteRoot'] = args.siteRoot
            gmData['cruiseID'] = getCruiseID(args.siteRoot)['cruiseID']
            gmData['systemStatus'] = getSystemStatus(args.siteRoot)['systemStatus']
            gmData['collectionSystemTransfer'] = collectionSystemTransfer
            gmData['shipboardDataWarehouse'] = getWarehouseConfig(args.siteRoot)
            #print json.dumps(gmData, indent=2)

            gm_client = gearman.GearmanClient(['localhost:4730'])
            completed_job_request = gm_client.submit_job("runCollectionSystemTransfer", json.dumps(gmData), background=True)
            #resultsObj = json.loads(completed_job_request.result)
            time.sleep(2)
            
        cruiseDataTransfers = getCruiseDataTransfers(args.siteRoot)
                         
        for cruiseDataTransfer in cruiseDataTransfers:
            #print 'Submitting data transfer job for: ' + cruiseDataTransfer['name']

            gmData = {}
            gmData['siteRoot'] = args.siteRoot
            gmData['cruiseID'] = getCruiseID(args.siteRoot)['cruiseID']
            gmData['systemStatus'] = getSystemStatus(args.siteRoot)['systemStatus']
            gmData['cruiseDataTransfer'] = cruiseDataTransfer
            gmData['shipboardDataWarehouse'] = getWarehouseConfig(args.siteRoot)
            #print json.dumps(gmData, indent=2)

            gm_client = gearman.GearmanClient(['localhost:4730'])
            completed_job_request = gm_client.submit_job("runCruiseDataTransfer", json.dumps(gmData), background=True)
            #resultsObj = json.loads(completed_job_request.result)
            time.sleep(2)
            
        requiredCruiseDataTransfers = getRequiredCruiseDataTransfers(args.siteRoot)
        #print json.dumps(cruiseDataTransfers, indent=2)
        
        for requiredCruiseDataTransfer in requiredCruiseDataTransfers:
            if requiredCruiseDataTransfer['name'] == 'SSDW':
                #print 'Submitting data transfer job for: ' + requiredCruiseDataTransfer['name']

                gmData = {}
                gmData['siteRoot'] = args.siteRoot
                gmData['cruiseID'] = getCruiseID(args.siteRoot)['cruiseID']
                gmData['systemStatus'] = getSystemStatus(args.siteRoot)['systemStatus']
                gmData['cruiseDataTransfer'] = requiredCruiseDataTransfer
                gmData['shipboardDataWarehouse'] = getWarehouseConfig(args.siteRoot)
                #print json.dumps(gmData, indent=2)

                gm_client = gearman.GearmanClient(['localhost:4730'])
                completed_job_request = gm_client.submit_job("runShipToShoreTransfer", json.dumps(gmData), background=True)
                #resultsObj = json.loads(completed_job_request.result)

            time.sleep(2)
        
        delay = args.interval * 60 - len(collectionSystemTransfers) * 2 - len(cruiseDataTransfers) * 2 - 2
        #print delay
        time.sleep(delay)

if __name__ == "__main__":
    main(sys.argv[1:])
