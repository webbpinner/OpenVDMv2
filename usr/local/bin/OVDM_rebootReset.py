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
#      VERSION:  2.0
#      CREATED:  2015-06-22
#     REVISION:  2016-02-08
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
import requests
import datetime
import argparse
import urlparse
import json
import gearman

def clearGearmanJobsFromDB(siteRoot):
    url = siteRoot + 'api/gearman/clearAllJobsFromDB'
    try:
        r = requests.get(url)
	#print json.dumps(r.json(), indent=2)
        return r.text

    except requests.exceptions.RequestException as e: 
        print "Error retrieving warehouse data, check URL"
        sys.exit(1)


def getWarehouseConfig(siteRoot):
    url = siteRoot + 'api/warehouse/getShipboardDataWarehouseConfig'
    try:
        r = requests.get(url)
        #print r.text
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
        
def getTasks(siteRoot):
    url = siteRoot + 'api/tasks/getTasks'
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
        
def setIdle_task(siteRoot, taskID):
    url = siteRoot + 'api/tasks/setIdleTask/' + taskID
    try:
        r = requests.get(url)

    except requests.exceptions.RequestException as e: 
        print "Error resetting task: " + taskID + ", check URL"
        
def setIdle_collectionSystemTransfer(siteRoot, collectionSystemTransferID):
    url = siteRoot + 'api/collectionSystemTransfers/setIdleCollectionSystemTransfer/' + collectionSystemTransferID
    try:
        r = requests.get(url)

    except requests.exceptions.RequestException as e: 
        print "Error resetting task: " + collectionSystemID + ", check URL"
        
def setIdle_cruiseDataTransfer(siteRoot, cruiseDataTransferID):
    url = siteRoot + 'api/cruiseDataTransfers/setIdleCruiseDataTransfer/' + cruiseDataTransferID
    try:
        r = requests.get(url)

    except requests.exceptions.RequestException as e: 
        print "Error resetting task: " + cruiseDataTransferID + ", check URL"
    
def main(argv):
    parser = argparse.ArgumentParser(description='OpenVDM Reboot Reset Utility')
    parser.add_argument('siteRoot', metavar='siteRoot', help='the base URL for this OpenVDM installation')
    
    args = parser.parse_args()
    #print args.siteRoot
    parsed_url = urlparse.urlparse(args.siteRoot)
    #print parsed_url
    if not bool(parsed_url.scheme) or not bool(parsed_url.netloc):
        print args.siteRoot + " is not a valid URL" 
        sys.exit(1)
    
    time.sleep(5)
    
    warehouseConfig = getWarehouseConfig(args.siteRoot)
    #print json.dumps(warehouseConfig, indent=2)
    
    tasks = getTasks(args.siteRoot)
    for task in tasks:
        setIdle_task(args.siteRoot, task['taskID'])
    
    collectionSystemTransfers = getCollectionSystemTransfers(args.siteRoot)
    for collectionSystemTransfer in collectionSystemTransfers:
        if not collectionSystemTransfer['status'] == '3':
            setIdle_collectionSystemTransfer(args.siteRoot, collectionSystemTransfer['collectionSystemTransferID'])
            
    cruiseDataTransfers = getCruiseDataTransfers(args.siteRoot)
    for cruiseDataTransfer in cruiseDataTransfers:
        if not cruiseDataTransfer['status'] == '3':
            setIdle_cruiseDataTransfer(args.siteRoot, cruiseDataTransfer['cruiseDataTransferID'])
            
    requiredCruiseDataTransfers = getRequiredCruiseDataTransfers(args.siteRoot)
    for requiredCruiseDataTransfer in requiredCruiseDataTransfers:
        if not requiredCruiseDataTransfer['status'] == '3':
            setIdle_cruiseDataTransfer(args.siteRoot, requiredCruiseDataTransfer['cruiseDataTransferID'])

    clearGearmanJobsFromDB(args.siteRoot)

if __name__ == "__main__":
    main(sys.argv[1:])
