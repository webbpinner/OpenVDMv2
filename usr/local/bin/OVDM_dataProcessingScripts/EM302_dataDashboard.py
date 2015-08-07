# =================================================================================== #
#
#         FILE:  EM302_dataDashboard.py
#
#        USAGE:  EM302_dashboard.py [-h] [--dataType] <dataFile>
#
#  DESCRIPTION:  This python script interprets raw files collected by the EM302 Multi-
#                beam Mapping Sonar System.  Depending on the command-line arguments,
#                the script returns the data type of the file or a sub-sampled and 
#                json-formattedversion of the original file to stdout.  The json-
#                formatted file is used by OpenVDM as part of it's Data dashboard. 
#
#      OPTIONS:  [-h] Return the help message.
#                [--dataType] Return the datatype of the file as defined in the
#                    fileTypeFilter array.
#                <dataFile> Full or relative path of the data file to process.
#
# REQUIREMENTS:  python2.7, Python Modules: sys, os, time, argparse, json, fnmatch, csv
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  1.0
#      CREATED:  2015-2-17
#     REVISION:  2015-4-08
#
# LICENSE INFO:  Open Vessel Data Management 2.0 (OpenVDMv2) Copyright (C) 2015 Capable
#                Solutions
#
#    This program is free software: you can redistribute it and/or modify it under the
#    terms of the GNU General Public License as published by the Free Software
#    Foundation, either version 3 of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful, but WITHOUT ANY
#    WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
#    PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License #    along with
#    this program.  If not, see <http://www.gnu.org/licenses/>.
#
# =================================================================================== #

import sys
import os
import time
import tempfile
import argparse
import json
import fnmatch
import csv
import inspect
import requests
import subprocess
from osgeo import gdal

# -------------------------------------------------------------------------------------
# Set the siteRoot for communicating with OpenVDM
# Use the name of the script to determine the Collection System Name
#
# The scriptDir, scriptName variables are not needed in the remainder of the script
# -------------------------------------------------------------------------------------
siteRoot = 'http://capablesolutions.dyndns.org:8180/OpenVDMv2/'
scriptDir, scriptName = os.path.split(inspect.getfile(inspect.currentframe()))
collectionSystemName = scriptName.split("_")[0]

# -------------------------------------------------------------------------------------
# This array defines the various dataTypes collected by SCS and the cooresponding file
# regex expression.
# -------------------------------------------------------------------------------------
fileTypeFilters = [
    {"dataType":"geotiff",   "regex": "*proc/*.tif"}
]

# -------------------------------------------------------------------------------------
# These statement define the format used by SCS to represent date and time
# -------------------------------------------------------------------------------------
DATE_FORMAT="%Y%m%d"
#TIME_FORMAT="%H:%M:%S.%f"

# -------------------------------------------------------------------------------------
# The number of minutes to average the raw data file.  In the case of dataType: 'gga'
# the script will employ closest-neighbor.
# -------------------------------------------------------------------------------------
AVERAGE=1

# -------------------------------------------------------------------------------------
# Function used to retrieve the path to Dashboard Data directory relative to the cruise
# data directory.
# -------------------------------------------------------------------------------------
def getDashboardDataDir():

    # URL for teh API call
    url = siteRoot + 'api/extraDirectories/getRequiredExtraDirectories'
    r = requests.get(url)
    for directory in r.json():
        if directory['name'] == 'Dashboard Data':
            return directory['destDir']
            break
    
    return ''

# -------------------------------------------------------------------------------------
# Function used to retrieve the current cruiseID.
# -------------------------------------------------------------------------------------
def getCruiseID():

    # URL for teh API call
    url = siteRoot + 'api/warehouse/getCruiseID'
    r = requests.get(url)
    return r.json()['cruiseID']

# -------------------------------------------------------------------------------------
# Function used to retrieve the configuration information from the Data Warehouse.
# -------------------------------------------------------------------------------------
def getDataWarehouseConfig():

    # URL for teh API call
    url = siteRoot + 'api/warehouse/getShipboardDataWarehouseConfig'
    r = requests.get(url)
    return r.json()

# -------------------------------------------------------------------------------------
# Function used to translate the raw date/time strings in a floating point number
# representing UNIX epoch
# -------------------------------------------------------------------------------------
def formatDateTime(dateStr, timeStr):
    epoch_subsec = round((float(timeStr.split(".")[1])/1000),2)
    epoch = float(time.mktime(time.strptime(dateStr + timeStr, DATE_FORMAT + TIME_FORMAT))+epoch_subsec)
    return epoch

# -------------------------------------------------------------------------------------
# Function to determine the datatype of the raw datafile.  If the datatype can not be
# determined, the function returns false
# -------------------------------------------------------------------------------------
def getDataType(filePath):
    
    for fileTypeFilter in fileTypeFilters:
        if fnmatch.fnmatch(filePath, fileTypeFilter['regex']):
            return fileTypeFilter['dataType']

    return False
    
# -------------------------------------------------------------------------------------
# Function to process the raw datafile and return a json-formatted representation.  If
# the datatype can not be determined, the function returns false.  With collection 
# systems that contain multiple dataTypes, this function may route the raw datafile to
# a dataType-specific processing sub-routine. 
# -------------------------------------------------------------------------------------
def getJsonObj(filePath):
    
    dataType = getDataType(filePath)
    
    if dataType == 'geotiff':
        return procGEOTIFF(filePath)
        
    else:
        return False
    
    return jsonObj
    
# -------------------------------------------------------------------------------------
# Function to process files of the 'gga' dataType.  The function is passed the path to
# the raw datafile.  Since 'gga' is a geographical dataset, the output is formatted as
# geoJson.
#
# If the raw datafile cannot be processed the function returns false.
# -------------------------------------------------------------------------------------
def procGEOTIFF(filePath):
    
    # parse the filePath to get the name of the file without the file extension
    dirname, filename = os.path.split(filePath)
    label = os.path.splitext(filename)[0]
    
    dataWarehouseConfig = getDataWarehouseConfig()
    dashboardDataDir = getDashboardDataDir()
    cruiseID = getCruiseID()
    collectionSystemDir = dirname.replace(dataWarehouseConfig['shipboardDataWarehouseBaseDir'] + '/' + cruiseID + '/','')
    
    # Create temp directory
    tmpdir = tempfile.mkdtemp()
    
    # Directory where the tiles will go.
    tileDir = dataWarehouseConfig['shipboardDataWarehouseBaseDir'] + '/' + cruiseID + '/' + dashboardDataDir + '/' + collectionSystemDir

    llFilename = label + "_LL.tif"
    #llFilePath = tileDir + "/" + llFilename

    #print "gdalinfo"
    #proc = subprocess.Popen(['gdalinfo', '-proj4', filePath], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    #out, err = proc.communicate()
    #if out:
    #    print "Out: " + out
    #    
    #if err:
    #    print "Err: " + err

    #print "gdalwarp"
    t_srsOptions = "+proj=latlong +datum=WGS84"
    proc = subprocess.Popen(['gdalwarp', '-t_srs', t_srsOptions, filePath, tmpdir + '/' + llFilename], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = proc.communicate()
    #if out:
    #    print "Out: " + out
        
    if err:
        print "Err: " + err
    
    #print "gdalinfo"
    #proc = subprocess.Popen(['gdalinfo', '-proj4', tmpdir + '/' + llFilename], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    #out, err = proc.communicate()
    #if out:
    #    print "Out: " + out
        
    #if err:
    #    print "Err: " + err
        
    # open the ll geoTiff
    ds = gdal.Open(tmpdir + '/' + llFilename)
    #print json.dumps(ds)

    # process the geoTiff
    width = ds.RasterXSize
    height = ds.RasterYSize
    gt = ds.GetGeoTransform()

    # calculate the bounds of the geoTiff
    minx = gt[0]
    miny = gt[3] + width*gt[4] + height*gt[5] 
    maxx = gt[0] + width*gt[1] + height*gt[2]
    maxy = gt[3] 

    #print "gdal_translate"
    #proc = subprocess.Popen(['gdalbuildvrt', '-separate', tmpdir + '/temp.vrt', tmpdir + '/' + llFilename], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    proc = subprocess.Popen(['gdal_translate', '-of', 'vrt', tmpdir + '/' + llFilename, tmpdir + '/temp.vrt'], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = proc.communicate()
    #if out:
    #    print "Out: " + out
        
    #if err:
    #    print "Err: " + err
    
    #print "gdal2tiles.py"
    proc = subprocess.Popen(['gdal2tiles.py', '-v', '--profile=mercator', '--zoom=5-12', '--webviewer=none', tmpdir + '/' + 'temp.vrt', tileDir + '/' + label], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = proc.communicate()
    #if out:
    #    print "Out: " + out
    #    
    #if err:
    #    print "Err: " + err
        
    # Blank geoJson object
    jsonObj = {
        "visualizerData":[
            {
                "label":label,
                "tileDirectory":cruiseID + '/' + dashboardDataDir + '/' + collectionSystemDir + '/' + label,
                "mapBounds":str(minx) + "," + str(miny) + "," + str(maxx) + "," + str(maxy)
            }
        ],
        "qualityTests":[],
        "stats":[
            {'statName':'Geographic Bounds','statType':'geoBounds','statData':[maxy,maxx,miny,minx],'statUnit':'ddeg'}, #Geographic bounding box
        ],
    }
    return jsonObj
    
# -------------------------------------------------------------------------------------
# Main function of the script should it be run as a stand-alone utility.
# -------------------------------------------------------------------------------------
def main(argv):
    
    parser = argparse.ArgumentParser(description=collectionSystemName + ' dataDashboard Processing Utilty')
    parser.add_argument('dataFile', metavar='dataFile', help='the raw data file to process')
    parser.add_argument('--dataType', action='store_true', help='return the dataType of the file')

    args = parser.parse_args()
    if not os.path.isfile(args.dataFile):
        sys.stderr.write('ERROR: File not found\n')
        sys.exit(1)
    
    if args.dataType:
        dataType = getDataType(args.dataFile)
        if dataType:
            print dataType
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        jsonObj = getJsonObj(args.dataFile)
        if jsonObj:
            print json.dumps(jsonObj)
            sys.exit(0)
        else:
            sys.exit(1)
            
# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])
