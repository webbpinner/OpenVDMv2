# ----------------------------------------------------------------------------------- #
#
#         FILE:  buildCruiseTracks.py
#
#        USAGE:  buildCruiseTracks.py [-h] [-c cruiseID] collectionSystem
#
#  REQUIRED ARGUMENTS:
#                collectionSystem  name of OpenVDM-defined collection system to process
#
#  OPTIONAL ARGUMENTS:
#                -h, --help        show this help message and exit
#                -c cruiseID       the cruiseID to process
#
#  DESCRIPTION:  Example script demostrating OpenVDM's hook architecture.  The purpose
#                of this script is to combine the various GeoJSON-formatted dashboard-
#                data files created from GGA raw files into a single GeoJSON and KML-
#                formatted cruise track.
#
#                The resulting files are put in a folder called "Tracklines" within
#                the OpenVDM defined extra directory "Products"
#
#                This script is designed to be called from the postDataDashboard hook,
#                specifically for the SCS Collection System Transfer but has been
#                written to allow this same script to easily work for GGA files
#                collected by other collection systems.
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
import pwd
import grp
import shutil
import tempfile
import argparse
import json
import subprocess
import glob
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
import openvdm

# -------------------------------------------------------------------------------------
# Function to combine all the geoJSON-formatted files listed in the 'files' array
# command-line argument.  The function is also passed the cruiseID and device name so 
# that this information can be added as a property to the final geoJSON file.
#
# If the raw datafile cannot be processed the function returns false.  If there were no
# files to process the fuction returns Null.  Otherwise the fuction returns the
# combined geoJSON object
# -------------------------------------------------------------------------------------
def combineGeoJsonFiles(files, cruiseID, deviceName):
    
    # Blank geoJson object
    combinedGeoJsonObj = {
        "type":"FeatureCollection",
        "features":[
            {
                "type":"Feature",
                "geometry":{
                    "type":"LineString",
                    "coordinates":[]
                },
                "properties": {
                    "name": cruiseID + '_' + deviceName
                }
            }
        ]
    }
        
    if len(files) > 0:
        for file in files:
            #print file

            # Open the dashboardData file
            try:
                geoJsonFile = open(file, 'r')
                geoJsonObj = json.load(geoJsonFile)

                #print combinedGeoJsonObj[0]['features'][0]['geometry']['coordinates'] 
                #print geoJsonObj['geodata']['coordinates']

                combinedGeoJsonObj['features'][0]['geometry']['coordinates'] += geoJsonObj['visualizerData'][0]['features'][0]['geometry']['coordinates']


            # If the file cannot be processed return false.
            except:
                print "ERROR: Could not proccess file: " + file
                return False

            # Close the raw datafile
            finally:
                geoJsonFile.close()
    else:
        return

    # If processing is successful, return the (geo)json object 
    return combinedGeoJsonObj


# -------------------------------------------------------------------------------------
# Function to convert a geoJSON object to a KML (v2.2) string.
#
# Function returns a KML-formatted string
# -------------------------------------------------------------------------------------
def convToKML(geoJSONObj):
    kml = Element('kml')
    kml.set('xmlns', 'http://www.opengis.net/kml/2.2')
    kml.set('xmlns:gx','http://www.google.com/kml/ext/2.2')
    kml.set('xmlns:kml','http://www.opengis.net/kml/2.2')
    kml.set('xmlns:atom','http://www.w3.org/2005/Atom')
    document = SubElement(kml, 'Document')
    name = SubElement(document, 'name')
    name.text = geoJSONObj['features'][0]['properties']['name'] + "_trackline.kml"
    placemark = SubElement(document, 'Placemark')
    name2 = SubElement(placemark, 'name')
    name2.text = "path1"
    #styleurl = SubElement(placemark, 'styleUrl')
    #styleurl.text = "http://www.schmidtocean.org/files/style.kml#SecondSargassoSea"
    linestring = SubElement(placemark, 'LineString')
    tessellate = SubElement(linestring, 'tessellate')
    tessellate.text = "1"
    coordinates = SubElement(linestring, 'coordinates')

    coordinatesText = ''
    
    #print json.dumps(geoJSONObj['features'][0]['geometry']['coordinates'])
    
    for coordinate in geoJSONObj['features'][0]['geometry']['coordinates']:
        #print coordinate
        coordinatesText += str(coordinate[0]) + ',' + str(coordinate[1]) + ',0 '

    coordinatesText = coordinatesText.rstrip(' ')
#    coordinatesText = coordinatesText.rstrip(',')
    coordinates.text = coordinatesText

    return '<?xml version=\"1.0\" encoding=\"utf-8\"?>' + tostring(kml)


# -------------------------------------------------------------------------------------
# Function to write a string to a file and set the user/group to the specified user.
# If the specified file cannot be opened then the function returns False.  If
# successful the function returns True.
#
# If the raw datafile cannot be processed the function returns false.
# -------------------------------------------------------------------------------------
def writeToFile(contents, filename, user):
    try:
        fileObj = open(filename, 'w')
        fileObj.write(contents)

    # If the file cannot be processed return false.
    except:
        return False

    # Close the raw datafile and set ownership permissions.
    finally:
        fileObj.close()
        os.chmod(filename, 0644)
        os.chown(filename, pwd.getpwnam(user).pw_uid, grp.getgrnam(user).gr_gid)

    return True

# -------------------------------------------------------------------------------------
# The main function of the script
# -------------------------------------------------------------------------------------
def main(argv):
    

    # Object that defines the GGA dashboardData datasets first by Collection System and
    # then by device.  In this example only the SCS collections system is recording GGA
    # data.
    #
    # In this example there is a dashboardData plugin for the SCS collection system
    # that created geoJSON dashboardData files from two sensors, the POSMV and CNAV.
    # These datasets are defined within the "GPSSources" array.
    #
    # Each element within the "GPSSources" array includes the name of the device (used
    # in the final filename) and a regex string specifying where the dashboardData 
    # are located within the top-level directory for SCS data within the dashboardData
    # directory specified within OpenVDM.  In most cases the dashboardData files reside
    # in the exact same directory structure as the raw data files.
    #
    # i.e.           Raw Files: /cruiseID/SCS/NAV/POSMV-GGA_*.Raw
    #      DashboardData Files: /cruiseID/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_*.json
    #
    AllGPSSources = [
        {
            "CollectionSystem":"SCS",
            "GPSSources": [
                {
                    "device":"POSMV",
                    "regex":"NAV/POSMV-GGA_*.json"
                },
                {
                    "device":"CNAV",
                    "regex":"NAV/CNAV-GGA_*.json"
                }
            ]
        }
    ]    
    
    # Define the command-line structure
    parser = argparse.ArgumentParser(description='build cruise tracklines post-dashboard processing')
    parser.add_argument('-c', dest='cruiseID', metavar='cruiseID', help='the cruiseID to process')
    parser.add_argument('collectionSystem', help='json-formatted array of files to NOT include for processing')
    
    # Process the command-line argumants
    args = parser.parse_args()
    
    # build an OpenVDM object
    openVDM = openvdm.OpenVDM()
    
    # define the cruiseID as the current cruiseID
    cruiseID = openVDM.getCruiseID()

    # if a cruiseID was declared in the command-line aruments, redefine the cruiseID variable
    if not args.cruiseID is None:
        print "Setting CruiseID to " + args.cruiseID
        cruiseID = args.cruiseID        
    
    # Retrieve the shipboard data warehouse configuration
    shipboardDataWarehouseConfig = openVDM.getShipboardDataWarehouseConfig()

    # Construct the full path to the cruise data directory 
    cruiseDir = shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'] + '/' + cruiseID
    
    # Verify the cruise data directory exists
    if not os.path.isdir(cruiseDir):
        print "ERROR: Cruise Data Directory: '" + cruiseDir + "' not found!"
        return -1
    
    # Retrieve the information for the collection system defined in the command-line argument
    collectionSystem = openVDM.getCollectionSystemTransferByName(args.collectionSystem)
    
    if not collectionSystem:
        print "ERROR: Collection System: '" + args.collectionSystem + "' not found!"
        return -1
    
    #get the name of the Products directory
    productsDirectory = openVDM.getExtraDirectoryByName('Products')
    if not productsDirectory:
        print "ERROR: 'Products' directory not found!"
        return -1
    else:
        # Verify the Products directory exists
        if not os.path.isdir(cruiseDir + '/' + productsDirectory['destDir']):
            print "ERROR: Products Directory: '" + cruiseDir + '/' + productsDirectory['destDir'] + "' not found!"
            return -1


    #get the name of the Dashboard Data directory
    dashboardDataDirectory = openVDM.getRequiredExtraDirectoryByName('Dashboard Data')
    if not dashboardDataDirectory:
        print "ERROR: 'Dashboard Data' directory not found!"
        return -1
    else:
        # Verify the Dashboard Data directory for the specified collection system exists
        if not os.path.isdir(cruiseDir + '/' + dashboardDataDirectory['destDir'] + '/' + collectionSystem['destDir']):
            print "ERROR: Dashboard Data Directory for " + args.collectionSystem + ": '" + cruiseDir + '/' + dashboardDataDirectory['destDir'] + '/' + collectionSystem['destDir'] + "' not found!"
            return -1

        
    # Create the Tracklines directory within Products directory if it does not already exist.
    # If the directory needs to be created, also set the ownership permissions
    try:
        os.mkdir(cruiseDir + '/' + productsDirectory['destDir'] + '/Tracklines', 0755)
        os.chown(cruiseDir + '/' + productsDirectory['destDir'] + '/Tracklines', pwd.getpwnam(shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']).pw_uid, grp.getgrnam(shipboardDataWarehouseConfig['shipboardDataWarehouseUsername']).gr_gid)
        
    except OSError:
        print "Tracklines directory already exists"
    
    # Loop through the AllGPSSources object
    for GPSSources in AllGPSSources:
        
        # If the collection system name matches the one in the command-line argrument
        if GPSSources['CollectionSystem'] == args.collectionSystem:
    
            #Build a geoJSON and kml cruisetrack for each GGA Device
            for GPSSource in GPSSources['GPSSources']:
                print "Processing " + GPSSource['device']
                
                # Build the list of files coorsponding to the current device based on the regex provided
                files = glob.glob(cruiseDir + '/' + dashboardDataDirectory['destDir'] + '/' + collectionSystem['destDir'] + '/' + GPSSource['regex'])
                
                # Combind the geoJSON objects
                combineGeoJsonObj = combineGeoJsonFiles(files, cruiseID, GPSSource['device'])
                
                # If there was a problem, exit
                if not combineGeoJsonObj:
                    return -1
                
                # If the combine was successful and there is data
                if combineGeoJsonObj is not None:

                    # Save the combined geoJSON object to file 
                    writeToFile(json.dumps(combineGeoJsonObj), cruiseDir + '/' + productsDirectory['destDir'] + '/' + 'Tracklines' + '/' + cruiseID + '_' + GPSSource['device'] + '_Trackline.json', shipboardDataWarehouseConfig['shipboardDataWarehouseUsername'])
                
                    # Convert the combined geoJSON object to kml and save to file 
                    writeToFile(convToKML(combineGeoJsonObj), cruiseDir + '/' + productsDirectory['destDir'] + '/' + 'Tracklines' + '/' + cruiseID + '_' + GPSSource['device'] + '_Trackline.kml', shipboardDataWarehouseConfig['shipboardDataWarehouseUsername'])
            
            # No need to proceed to another collectionSystem
            break

if __name__ == "__main__":
    main(sys.argv[1:])