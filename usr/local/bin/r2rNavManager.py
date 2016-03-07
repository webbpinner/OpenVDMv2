# ----------------------------------------------------------------------------------- #
#
#         FILE:  r2rNavManager.py
#
#        USAGE:  r2rNavManager.py [-h] [-c cruiseID] [-s skip] collectionSystem
#
#  REQUIRED ARGUMENTS:
#                collectionSystem  name of OpenVDM-defined collection system to process
#
#  OPTIONAL ARGUMENTS:
#                -h, --help        show this help message and exit
#                -c cruiseID       the cruiseID to process
#                -s skip           json-formatted array of files to NOT include for
#                                  processing
#
#  DESCRIPTION:  Example script demostrating OpenVDM's hook architecture.  The purpose
#                of this script is to process all of the defined navigation data using
#                the r2r NavManager package per the instructions provided in the
#                NavManager Cookbook.
#
#                The resulting files are put in a folder called "NavManager" within
#                the OpenVDM defined extra directory "r2r"
#
#                This script is designed to be called from the 
#                postCollectionSystemTransfer hook, specifically for the SCS Collection
#                System Transfer but has been written to allow this same script to
#                easily work for GGA files collected by other collection systems.
#
# PREREQUISITES: The script requires that a modified version of the rvdata/NavManager
#                software package be installed on the data warehouse.  The requried
#                modified version is available from:
#                https://github.com/webbpinner/NavManager
#
#                Once the git repo had been cloned to the data warehouse, install
#                using the instructions provided in the NavManager Cookbook
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  1.0
#      CREATED:  2016-03-06
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
import os
import sys
import shutil
import tempfile
import argparse
import json
import subprocess
import glob
import openvdm

def main(argv):
    
    AllGPSSources = [
        {
            "CollectionSystem":"SCS",
            "GPSSources": [
                {
                    "device":"POSMV",
                    "regex":"NAV/POSMV-GGA_*.Raw"
                },
                {
                    "device":"CNAV",
                    "regex":"NAV/CNAV-GGA_*.Raw"
                }
            ]
        },
        {
            "CollectionSystem":"USBL",
            "GPSSources": [
                {
                    "device":"POSMV",
                    "regex":"USBL-GGA_*.Raw"
                }
            ]
        }
    ]
    
    openVDM = openvdm.OpenVDM()
    
    parser = argparse.ArgumentParser(description='r2rNavManager post-transfer processing script')
    parser.add_argument('-c', default=openVDM.getCruiseID(), metavar='cruiseID', help='the cruiseID to process')
    parser.add_argument('-s', metavar='skip', help='json-formatted array of files to NOT include for processing')
    parser.add_argument('collectionSystem', help='json-formatted array of files to NOT include for processing')
    

    args = parser.parse_args()
    
    #get the warehouse config
    shipboardDataWarehouseConfig = openVDM.getShipboardDataWarehouseConfig()

    # construct the root of the cruise data directory 
    cruiseDir = shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'] + '/' + openVDM.getCruiseID()
    
    #get the name of the SCS directory
    collectionSystem = openVDM.getCollectionSystemTransferByName(args.collectionSystem)
    
    if not collectionSystem:
        print "ERROR: Collection System: '" + args.collectionSystem + "' not found"
        return -1
    
    #get the name of the r2r directory
    r2rDirectory = openVDM.getExtraDirectoryByName('r2r')
    if not r2rDirectory:
        print "ERROR: 'r2r' directory not found"
        return -1

    #if NavManager directory in r2r directory does not exist, create it
    try:
        os.mkdir(cruiseDir + '/' + r2rDirectory['destDir'] + '/NavManager')
    except OSError:
        print "NavManager directory already exists"
        
    for GPSSources in AllGPSSources:
        if GPSSources['CollectionSystem'] == args.collectionSystem:
    
            #create a temp directory
            tmpdir = tempfile.mkdtemp()

            #foreach GGA Source Device
            for GPSSource in GPSSources['GPSSources']:
                print "Processing " + GPSSource['device']
                #copy GGA Files to tmpdir

                files = glob.glob(cruiseDir + '/' + collectionSystem['destDir'] + '/' + GPSSource['regex'])

                #if there are no files, continue to the next GGA type
                if len(files) > 0:
                    for file in files:
                        #print file
                        shutil.copy(file, tmpdir)
                else:
                    continue

                #if device directory does not exists in r2r/NavManager directory, create it
                deviceDir = cruiseDir + '/' + r2rDirectory['destDir'] + '/NavManager' + '/' + GPSSource['device']
                try:
                    os.mkdir(deviceDir)
                except OSError:
                    print "NavManager/" + GPSSource['device'] + " directory already exists"

                print "Running navcopy.php..."
                command = ['php', '/usr/local/bin/NavManager/bin/navcopy.php', '-f', 'nav2', '-d', tmpdir, '-o', deviceDir + '/bestres_raw.r2rnav']
                proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                out, err = proc.communicate()

                print "Running navinfo.php..."
                command = ['php', '/usr/local/bin/NavManager/bin/navinfo.php', '-i', deviceDir + '/bestres_raw.r2rnav', '-l', deviceDir + '/navinfo_report.txt']
                proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                out, err = proc.communicate()

                print "Running navqa.php..."
                command = ['php', '/usr/local/bin/NavManager/bin/navqa.php', '-i', deviceDir + '/bestres_raw.r2rnav', '-l', deviceDir + '/navqa_report.txt']
                proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                out, err = proc.communicate()

                print "Running navqc.php..."
                command = ['php', '/usr/local/bin/NavManager/bin/navqc.php', '-i', deviceDir + '/bestres_raw.r2rnav', '-o', deviceDir + '/bestres_qc.r2rnav', '-l', deviceDir + '/navqc_report.txt']
                proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                out, err = proc.communicate()

            #cleanup
            shutil.rmtree(tmpdir)
    
if __name__ == "__main__":
    main(sys.argv[1:])