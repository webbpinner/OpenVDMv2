# =================================================================================== #
#
#         FILE:  scs_dataDashboard.py
#
#        USAGE:  scs_dashboard.py [-h] [--dataType] <dataFile>
#
#  DESCRIPTION:  This python script interprets raw files collected by the SCS Data
#                Acquision System.  Depending on the command-line arguments, the script
#                returns the data type of the file or a sub-sampled and json-formatted
#                version of the original file to stdout.  The json-formatted file is
#                used by OpenVDM as part of it's Data dashboard. 
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
import argparse
import json
import fnmatch
import csv
from geopy.distance import great_circle

# -------------------------------------------------------------------------------------
# This array defines the various dataTypes collected by SCS and the cooresponding file
# regex expression.
# -------------------------------------------------------------------------------------
fileTypeFilters = [
    {"dataType":"gga",   "regex": "*NAV/POSMV-GGA_*.Raw"},
    {"dataType":"met",   "regex": "*METOC/MET-M01_*.Raw"},
    {"dataType":"tsg",   "regex": "*METOC/TSG-RAW_*.Raw"},
    {"dataType":"twind", "regex": "*METOC/TrueWind-RAW_*.Raw"},
    {"dataType":"svp",   "regex": "*METOC/Sound-Velocity-Probe_*.Raw"}
]

outputJSON = {
    "visualizerData":[],
    "qualityTests":[],
    "stats":[]
}


# -------------------------------------------------------------------------------------
# These statement define the format used by SCS to represent date and time
# -------------------------------------------------------------------------------------
DATE_FORMAT="%m/%d/%Y"
TIME_FORMAT="%H:%M:%S.%f"

# -------------------------------------------------------------------------------------
# The number of minutes to average the raw data file.  In the case of dataType: 'gga'
# the script will employ closest-neighbor.
# -------------------------------------------------------------------------------------
AVERAGE=1

MAX_DELTA_T=10 # Max time between data rows (seconds)
FAIL_THRESHOLD = 10.0 # % of values that fail bounds test

START_EPOCH = 0
END_EPOCH = 1
    
MIN_BOUNDS = 0
MAX_BOUNDS = 1
    
VALID = 0
INVALID = 1

NORTHBOUNDS = 0
EASTBOUNDS = 1
SOUTHBOUNDS = 2
WESTBOUNDS = 3    

DEBUG = False

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
    
    if dataType == 'gga':
        return procGGA(filePath)
        
    elif dataType == 'met':
        return procMET(filePath)

    elif dataType == 'tsg':
        return procTSG(filePath)

    elif dataType == 'twind':
        return procTWIND(filePath)

    elif dataType == 'svp':
        return procSVP(filePath)

    else:
        return False

# -------------------------------------------------------------------------------------
# Function to calculate the NMEA checksum for the given string 
# -------------------------------------------------------------------------------------
def verifyChecksum(scsSentence):
    dateTime, nmeadataCksum = scsSentence.split('$', 1)
    nmeadata, cksum = scsSentence.split('*', 1)
    nmeadata = '$' + nmeadata
    calc_cksum = reduce(operator.xor, (ord(s) for s in nmeadata), 0)
    
    if calc_cksum == cksum:
        return True
    else:
        return False

# -------------------------------------------------------------------------------------
# Function to process files of the 'gga' dataType.  The function is passed the path to
# the raw datafile.  Since 'gga' is a geographical dataset, the output is formatted as
# geoJson.
#
# If the raw datafile cannot be processed the function returns false.
# -------------------------------------------------------------------------------------
def procGGA(filePath):
    
    gga_velocity_MAX = 13.8 #Max speed of vessel (mph)
    gga_latitude_MIN = -60.0
    gga_latitude_MAX = 60.0
    gga_longitude_MIN = -180.0
    gga_longitude_MAX = 180.0
    
    ROWINTEGRITY_TEST = 0
    CHECKSUM_TEST = 1
    DELTAT_TEST = 2
    VELOCITY_TEST = 3
    BOUNDS_TEST = 4
    
    TEMPERALBOUNDS_STAT = 0
    GEOGRAPHICBOUNDS_STAT = 1
    TOTALDISTANCE_STAT = 2
    VELOCITYBOUNDS_STAT = 3
    TEMPERALVALIDITY_STAT = 4
    VELOCITYVALIDITY_STAT = 5    
    LATITUDEVALIDITY_STAT = 6
    LONGITUDEVALIDITY_STAT = 7
    #CHECKSUMVALIDITY_STAT = 8
    ROWVALIDITY_STAT = 8
    
    # List of column names for the raw csv-formatted datafile
    fieldNames = ('SCS Date',
                  'SCS Time',
                  'Sentence Identifier',
                  'GPS Time',
                  'Latitude',
                  'Hemisphere (N/S)',
                  'Longitude',
                  'Hemisphere (E/W)',
                  'Fix Quality',
                  '# of Satellites',
                  'Horizontal Dilution of Precision',
                  'Altitude',
                  'Altitude Units (m)',
                  'Height over WGS84 Ellipsoid',
                  'Height Units (m)',
                  'Time since last DGPS update',
                  'DGPS Station',
                  'NMEA Checksum'
                 )
    
    # Blank geoJson object
    visualizerDataObj = [
        {
            'type':'FeatureCollection',
            'features':[
                {
                    'type':'Feature',
                    'geometry':{
                        'type':'LineString',
                        'coordinates':[]
                    },
                    'properties': {
                        'name': filePath
                    }
                }
            ]
        }
    ]
    
    qualityTestsObj = [
        {'testName':'Row Integrity', 'results':'Passed'},
        {'testName':'Checksums', 'results':'Passed'},
        {'testName':'Delta-T', 'results':'Passed'},
        {'testName':'Velocity', 'results':'Passed'},
        {'testName':'Bounds', 'results':'Passed'},
        
    ]
    
    statsObj = [
        {'statName':'Temperal Bounds','statType':'timeBounds','statData':[0.0,0.0],'statUnit':'seconds'},       #Start and end times
        {'statName':'Geographic Bounds','statType':'geoBounds','statData':[0.0,0.0,0.0,0.0],'statUnit':'ddeg'}, #Geographic bounding box
        {'statName':'Total Distance','statType':'totalValue','statData':[0.0],'statUnit':'miles'},              #Total distance traveled
        {'statName':'Velocity Bounds','statType':'bounds','statData':[gga_velocity_MAX,0.0],'statUnit':'mph'},  #Min/Max Velocities        
        {'statName':'Temperal Validity','statType':'valueValidity','statData':[0,0]},                           #Number of valid and invalid time gaps
        {'statName':'Velocity Validity','statType':'valueValidity','statData':[0,0]},                           #Number of valid and invalid velocity readings        
        {'statName':'Latitude Validity','statType':'valueValidity','statData':[0,0]},                           #Number of valid and invalid latitude readings
        {'statName':'Longitude Validity','statType':'valueValidity','statData':[0,0]},                          #Number of valid and invalid longitude readings
        #{'statName':'Checksum Validity','statType':'rowValidity','statData':[0,0]},                          #Number of valid and invalid longitude readings
        {'statName':'Row Validity','statType':'rowValidity','statData':[0,0]}                                   #Number of valid and invalid rows
        
    ]
    
    # Open the raw datafile
    try:
        csvfile = open(filePath, 'r')
        reader = csv.DictReader( csvfile, fieldNames)
        
        prev_epoch = 0.0
        avg_epoch = 0.0
        
        prev_lon = 0.0
        prev_lat = 0.0
        
        longitude_degrees = 0.0
        longitude_dminutes = 0.0
        lon_hemisphere = 1.0
        
        latitude_degrees = 0.0
        latitude_dminutes = 0.0
        lat_hemisphere = 1.0
        
        init = True
        while(init):
            firstRow = reader.next()
            try:
                prev_epoch = formatDateTime(firstRow['SCS Date'],firstRow['SCS Time'])
                avg_epoch = prev_epoch
                longitude_degrees = float(firstRow['Longitude'][:3])
                longitude_dminutes = float(firstRow['Longitude'][3:])/60
                lon_hemisphere = 1.0
		
                if firstRow['Hemisphere (E/W)'] == 'W':
                    lon_hemisphere = -1.0

                latitude_degrees = float(firstRow['Latitude'][:2])
                latitude_dminutes = float(firstRow['Latitude'][2:])/60
                lat_hemisphere = 1.0
		
                if firstRow['Hemisphere (N/S)'] == 'S':
                    lat_hemisphere = -1.0
                
                #Add to output array
                visualizerDataObj[0]['features'][0]['geometry']['coordinates'].append([(longitude_degrees + longitude_dminutes) * lon_hemisphere, (latitude_degrees + latitude_dminutes) * lat_hemisphere])
                
                #Run tests
                if longitude_degrees + longitude_dminutes > gga_longitude_MAX or longitude_degrees + longitude_dminutes < gga_longitude_MIN:
                    statsObj[LONGITUDEVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[LONGITUDEVALIDITY_STAT]['statData'][VALID] += 1
                    statsObj[GEOGRAPHICBOUNDS_STAT]['statData'][NORTHBOUNDS] = (latitude_degrees + latitude_dminutes) * lat_hemisphere
                    statsObj[GEOGRAPHICBOUNDS_STAT]['statData'][SOUTHBOUNDS] = (latitude_degrees + latitude_dminutes) * lat_hemisphere
                    prev_lat = (latitude_degrees + latitude_dminutes) * lat_hemisphere

                if latitude_degrees + latitude_dminutes > gga_latitude_MAX or latitude_degrees + latitude_dminutes < gga_latitude_MIN:
                    statsObj[LATITUDEVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[LATITUDEVALIDITY_STAT]['statData'][VALID] += 1
                    statsObj[GEOGRAPHICBOUNDS_STAT]['statData'][EASTBOUNDS] = (longitude_degrees + longitude_dminutes) * lon_hemisphere
                    statsObj[GEOGRAPHICBOUNDS_STAT]['statData'][WESTBOUNDS] = (longitude_degrees + longitude_dminutes) * lon_hemisphere
                    prev_lon = (longitude_degrees + longitude_dminutes) * lon_hemisphere
                    
                #print ','.join(firstRow)
                #if verifyChecksum(','.join(firstRow)):
                #    statsObj[CHECKSUMVALIDITY_STAT]['statsData'][VALID] += 1
                #else:
                #    statsObj[CHECKSUMVALIDITY_STAT]['statsData'][INVALID] += 1                
                    
                #Initialize Stats
                statsObj[TEMPERALBOUNDS_STAT]['statData'][START_EPOCH] = prev_epoch
                statsObj[TEMPERALBOUNDS_STAT]['statData'][END_EPOCH] = prev_epoch
                statsObj[TEMPERALVALIDITY_STAT]['statData'][VALID] += 1
                statsObj[VELOCITYVALIDITY_STAT]['statData'][VALID] += 1
                
                init = False
                statsObj[ROWVALIDITY_STAT]['statData'][VALID] += 1
                    
            except:
                if DEBUG:
                    print "Unexpected init error:", sys.exc_info()
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                statsObj[ROWVALIDITY_STAT]['statData'][INVALID] += 1
                continue
        
        # Process each row of the raw datafile
        for row in reader:

            # Attempt to convert values to numerical representations, If there are any
            # problems, the row is skipped
            try:
                
                lat_valid = True
                lon_valid = True
                distance = 0.0
                
                epoch = formatDateTime(row['SCS Date'],row['SCS Time'])
                longitude_degrees = float(row['Longitude'][:3])
                longitude_dminutes = float(row['Longitude'][3:])/60
                lon_hemisphere = 1.0
		
                if row['Hemisphere (E/W)'] == 'W':
                    lon_hemisphere = -1.0

                latitude_degrees = float(row['Latitude'][:2])
                latitude_dminutes = float(row['Latitude'][2:])/60
                lat_hemisphere = 1.0
		
                if row['Hemisphere (N/S)'] == 'S':
                    lat_hemisphere = -1.0

                    
                # Subsample the file based on the defined interval.  In the case of 'gga' the algorithm uses closest-neighbor  
                if (epoch-avg_epoch > AVERAGE*60):
                    visualizerDataObj[0]['features'][0]['geometry']['coordinates'].append([(longitude_degrees + longitude_dminutes) * lon_hemisphere, (latitude_degrees + latitude_dminutes) * lat_hemisphere])

                    avg_epoch = epoch

                #Run tests
                if epoch - prev_epoch > MAX_DELTA_T:
                    statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[TEMPERALVALIDITY_STAT]['statData'][VALID] += 1
                    
                if longitude_degrees + longitude_dminutes > gga_longitude_MAX or longitude_degrees + longitude_dminutes < gga_longitude_MIN:
                    lon_valid = False
                    statsObj[LONGITUDEVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[LONGITUDEVALIDITY_STAT]['statData'][VALID] += 1
                    if (longitude_degrees + longitude_dminutes) * lon_hemisphere > statsObj[1]['statData'][EASTBOUNDS]:
                        statsObj[GEOGRAPHICBOUNDS_STAT]['statData'][EASTBOUNDS] = (longitude_degrees + longitude_dminutes) * lon_hemisphere
                    elif (longitude_degrees + longitude_dminutes) * lon_hemisphere < statsObj[1]['statData'][WESTBOUNDS]:
                        statsObj[GEOGRAPHICBOUNDS_STAT]['statData'][WESTBOUNDS] = (longitude_degrees + longitude_dminutes) * lon_hemisphere
    
                if latitude_degrees + latitude_dminutes > gga_latitude_MAX or latitude_degrees + latitude_dminutes < gga_latitude_MIN:
                    lat_valid = False
                    statsObj[LATITUDEVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[LATITUDEVALIDITY_STAT]['statData'][VALID] += 1
                    if (latitude_degrees + latitude_dminutes) * lat_hemisphere > statsObj[1]['statData'][NORTHBOUNDS]:
                        statsObj[GEOGRAPHICBOUNDS_STAT]['statData'][NORTHBOUNDS] = (latitude_degrees + latitude_dminutes) * lat_hemisphere
                    elif (latitude_degrees + latitude_dminutes) * lat_hemisphere < statsObj[1]['statData'][SOUTHBOUNDS]:
                        statsObj[GEOGRAPHICBOUNDS_STAT]['statData'][SOUTHBOUNDS] = (latitude_degrees + latitude_dminutes) * lat_hemisphere

                if lat_valid and lon_valid:
                    distance = great_circle((prev_lat, prev_lon), ((latitude_degrees + latitude_dminutes) * lat_hemisphere,(longitude_degrees + longitude_dminutes) * lon_hemisphere)).miles
                    statsObj[TOTALDISTANCE_STAT]['statData'][0] += distance
                    prev_lat = (latitude_degrees + latitude_dminutes) * lat_hemisphere
                    prev_lon = (longitude_degrees + longitude_dminutes) * lon_hemisphere
                    
                velocity = distance/(epoch-prev_epoch)*60*60
                if velocity > gga_velocity_MAX:
                    statsObj[VELOCITYVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[VELOCITYVALIDITY_STAT]['statData'][VALID] += 1
                    
                if velocity < statsObj[VELOCITYBOUNDS_STAT]['statData'][MIN_BOUNDS]:
                    statsObj[VELOCITYBOUNDS_STAT]['statData'][MIN_BOUNDS] = velocity
                
                elif velocity > statsObj[VELOCITYBOUNDS_STAT]['statData'][MAX_BOUNDS]:
                    statsObj[VELOCITYBOUNDS_STAT]['statData'][MAX_BOUNDS] = velocity
                    
                #if verifyChecksum(','.join(row)):
                #    statsObj[CHECKSUMVALIDITY_STAT]['statsData'][VALID] += 1
                #else:
                #    statsObj[CHECKSUMVALIDITY_STAT]['statsData'][INVALID] += 1 
                    
                prev_epoch = epoch
                
                statsObj[ROWVALIDITY_STAT]['statData'][VALID] += 1                
    
            except:
                if DEBUG:
                    print "Unexpected row error:", sys.exc_info()
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                statsObj[ROWVALIDITY_STAT]['statData'][INVALID] += 1
                continue
        
        #final row
        if epoch != prev_epoch:
            visualizerDataObj[0]['features'][0]['geometry']['coordinates'].append([(longitude_degrees + longitude_dminutes) * lon_hemisphere, (latitude_degrees + latitude_dminutes) * lat_hemisphere])

        statsObj[TEMPERALBOUNDS_STAT]['statData'][END_EPOCH] = epoch
            
    # If the file cannot be processed return false.
    except Exception as e:
        if DEBUG:
            print "Unexpected file error:", sys.exc_info()
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
        return False
    
    # Close the raw datafile
    finally:
        csvfile.close()
            
    # Calulate test results
    
    # Row Integrity Test
    if float(statsObj[ROWVALIDITY_STAT]['statData'][INVALID])/float(statsObj[ROWVALIDITY_STAT]['statData'][INVALID] + statsObj[ROWVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[ROWINTEGRITY_TEST]['results'] = 'Failed'
    elif statsObj[ROWVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[ROWINTEGRITY_TEST]['results'] = 'Warning'
        
    # CheckSum Validity Test
    #if float(statsObj[CHECKSUMVALIDITY_STAT]['statData'][INVALID])/float(statsObj[CHECKSUMVALIDITY_STAT]['statData'][INVALID] + statsObj[CHECKSUMVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
    #    qualityTestsObj[CHECKSUMVALIDITY_TEST]['results'] = 'Failed'
    #elif statsObj[CHECKSUMVALIDITY_STAT]['statData'][INVALID] > 0:
    #    qualityTestsObj[CHECKSUMVALIDITY_TEST]['results'] = 'Warning'
        
    # Delta T Test
    if float(statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID])/float(statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID] + statsObj[TEMPERALVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[DELTAT_TEST]['results'] = 'Failed'
    elif statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[DELTAT_TEST]['results'] = 'Warning'

    # Velocity Test
    if float(statsObj[VELOCITYVALIDITY_STAT]['statData'][INVALID])/float(statsObj[VELOCITYVALIDITY_STAT]['statData'][INVALID] + statsObj[VELOCITYVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[VELOCITY_TEST]['results'] = 'Failed'
    elif statsObj[VELOCITYVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[VELOCITY_TEST]['results'] = 'Warning'

    # Bounds Test
    if float(statsObj[LATITUDEVALIDITY_STAT]['statData'][INVALID])/float(statsObj[LATITUDEVALIDITY_STAT]['statData'][INVALID] + statsObj[LATITUDEVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Failed'
    elif statsObj[LATITUDEVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Warning'
        
    if float(statsObj[LONGITUDEVALIDITY_STAT]['statData'][INVALID])/float(statsObj[LONGITUDEVALIDITY_STAT]['statData'][INVALID] + statsObj[LONGITUDEVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Failed'
    elif statsObj[LONGITUDEVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Warning'

    
    outputJSON['visualizerData'] = visualizerDataObj
    outputJSON['qualityTests'] = qualityTestsObj
    outputJSON['stats'] = statsObj

    # If processing is successful, return the json object 
    return outputJSON
    
# -------------------------------------------------------------------------------------
# Function to process files of the 'met' dataType.  The function is passed the path to
# the raw datafile.
#
# If the raw datafile cannot be processed the function returns false.
# -------------------------------------------------------------------------------------
def procMET(filePath):

    met_baro_MIN = 900.0
    met_baro_MAX = 1100.0
    met_humidity_MIN = 0.0
    met_humidity_MAX = 100.0
    met_temp_MIN = 0.0
    met_temp_MAX = 60.0
    
    ROWINTEGRITY_TEST = 0
    DELTAT_TEST = 1
    BOUNDS_TEST = 2
    
    TEMPERALBOUNDS_STAT = 0
    PRESSUREBOUNDS_STAT = 1
    HUMIDITYBOUNDS_STAT = 2
    TEMPERATUREBOUNDS_STAT = 3
    TEMPERALVALIDITY_STAT = 4
    PRESSUREVALIDITY_STAT = 5
    HUMIDITYVALIDITY_STAT = 6
    TEMPERATUREVALIDITY_STAT = 7
    ROWVALIDITY_STAT = 8
    
    # List of column names for the raw csv-formatted datafile
    fieldNames = ('SCS Date',
                  'SCS Time',
                  'Sentence Identifier',
                  'Sensor Date',
                  'Sensor Time',
                  'Barometer (mBar)',
                  'Barometer Sensor Height',
                  'Barometer Data Quality',
                  'Air Temperature (C)',
                  'Air Temperature Sensor Height',
                  'Air Temperature Data Quality',
                  'Relative Humidity (%)',
                  'Relative Humidity Sensor Height',
                  'Relative Humidity Data Quality',
                  'Vector Wind Speed (m/s)',
                  'Vector Wind Direction (degrees, Relative to Bow)',
                  'Scalar Wind Speed (m/s)',
                  'Maximum Wind Speed (m/s)',
                  'Wind Sensor Height',
                  'Wind Sensor Data Quality',
                  'Shortwave Irradiance (Wm-2)',
                  'Shortwave Irradiance Sensor Height',
                  'Shortwave Irradiance Data Quality',
                  'Longwave Irradiance (Wm-2)',
                  'PIR Thermopile Voltage (mV)',
                  'PIR Case Temperature (C)',
                  'PIR Dome Temperature (C)',
                  'PIR Sensor Height above sea level',
                  'NMEA Checksum'
                 )
    
    visualizerDataObj = [
        {"label":"Pressure",    "unit":"mBar", "data":[]},
        {"label":"Humidity",    "unit":"%",   "data":[]},
        {"label":"Temperature", "unit":"C",   "data":[]}
    ]
    
    qualityTestsObj = [
        {'testName':'Row Integrity', 'results':'Passed'},
        {'testName':'Delta-T', 'results':'Passed'},
        {'testName':'Bounds', 'results':'Passed'}
    ]
    
    statsObj = [
        {'statName':'Temperal Bounds','statType':'timeBounds','statData':[0.0,0.0],'statUnit':'seconds'},                   #Start and end times
        {'statName':'Pressure Bounds','statType':'bounds','statData':[met_baro_MAX,met_baro_MIN],'statUnit':'mBar'},        #Min/Max Pressure        
        {'statName':'Humidity Bounds','statType':'bounds','statData':[met_humidity_MAX,met_humidity_MIN],'statUnit':'%'},   #Min/Max Humidity
        {'statName':'Temperature Bounds','statType':'bounds','statData':[met_temp_MAX,met_temp_MIN],'statUnit':'C'},        #Min/Max Temperature
        {'statName':'Temperal Validity','statType':'valueValidity','statData':[0,0]},                                       #Number of valid and invalid time gaps
        {'statName':'Pressure Validity','statType':'valueValidity','statData':[0,0]},                                       #Number of valid and invalid pressure readings        
        {'statName':'Humidity Validity','statType':'valueValidity','statData':[0,0]},                                       #Number of valid and invalid humidity readings
        {'statName':'Temperature Validity','statType':'valueValidity','statData':[0,0]},                                    #Number of valid and invalid temperature readings
        {'statName':'Row Validity','statType':'rowValidity','statData':[0,0]}                                               #Number of valid and invalid rows
    ]

    # Open the raw datafile
    try:
        csvfile = open(filePath, 'r')
        reader = csv.DictReader( csvfile, fieldNames)
    
        prev_epoch = 0.0
        avg_epoch = 0.0
        temp_sum = 0.0
        baro_sum = 0.0
        humid_sum = 0.0
        avg_count = 1

        init = True
        while(init):
            firstRow = reader.next()
            try:
                prev_epoch = formatDateTime(firstRow['SCS Date'],firstRow['SCS Time'])
                avg_epoch = prev_epoch
                temp_sum = float(firstRow['Air Temperature (C)'])
                baro_sum = float(firstRow['Barometer (mBar)'])
                humid_sum = float(firstRow['Relative Humidity (%)'])
                
                # Add to visualizer data array
                visualizerDataObj[0]['data'].append([int(prev_epoch*1000), round(baro_sum/avg_count,2)])
                visualizerDataObj[1]['data'].append([int(prev_epoch*1000), round(humid_sum/avg_count,2)])
                visualizerDataObj[2]['data'].append([int(prev_epoch*1000), round(temp_sum/avg_count,2)])
                
                # Initialize Stats
                statsObj[TEMPERALBOUNDS_STAT]['statData'][START_EPOCH] = prev_epoch
                statsObj[TEMPERALBOUNDS_STAT]['statData'][END_EPOCH] = prev_epoch
                
                # Update Min/Max Stats
                statsObj[PRESSUREBOUNDS_STAT]['statData'][MIN_BOUNDS] = baro_sum
                statsObj[PRESSUREBOUNDS_STAT]['statData'][MAX_BOUNDS] = baro_sum

                statsObj[HUMIDITYBOUNDS_STAT]['statData'][MIN_BOUNDS] = humid_sum
                statsObj[HUMIDITYBOUNDS_STAT]['statData'][MAX_BOUNDS] = humid_sum

                statsObj[TEMPERATUREBOUNDS_STAT]['statData'][MIN_BOUNDS] = temp_sum
                statsObj[TEMPERATUREBOUNDS_STAT]['statData'][MAX_BOUNDS] = temp_sum

                # Update Validity Stats
                if temp_sum > met_temp_MAX or temp_sum < met_temp_MIN:
                    statsObj[TEMPERATUREVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[TEMPERATUREVALIDITY_STAT]['statData'][VALID] += 1

                if baro_sum > met_baro_MAX or baro_sum < met_baro_MIN:
                    statsObj[PRESSUREVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[PRESSUREVALIDITY_STAT]['statData'][VALID] += 1
                
                if humid_sum > met_humidity_MAX or humid_sum < met_humidity_MIN:
                    statsObj[HUMIDITYVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[HUMIDITYVALIDITY_STAT]['statData'][VALID] += 1
                    
                init = False
                statsObj[ROWVALIDITY_STAT]['statData'][VALID] += 1
                    
            except:
                if DEBUG:
                    print "Unexpected init error:", sys.exc_info()
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                statsObj[ROWVALIDITY_STAT]['statData'][INVALID] += 1
                continue
                
        # Process each row of the raw datafile
        for row in reader:
            epoch = formatDateTime(row['SCS Date'],row['SCS Time'])

            # Attempt to convert values to numerical representations, If there are any
            # problems, the row is skipped
            try:
                temp = float(row['Air Temperature (C)'])
                baro = float(row['Barometer (mBar)'])
                humid = float(row['Relative Humidity (%)'])

                temp_sum += temp
                baro_sum += baro
                humid_sum += humid
                avg_count += 1
                
                # Subsample the file based on the defined interval.  
                if (epoch-avg_epoch > AVERAGE*60):
                    visualizerDataObj[0]['data'].append([int(epoch*1000), round(baro_sum/avg_count,2)])
                    visualizerDataObj[1]['data'].append([int(epoch*1000), round(humid_sum/avg_count,2)])
                    visualizerDataObj[2]['data'].append([int(epoch*1000), round(temp_sum/avg_count,2)])

                    temp_sum = 0.0
                    baro_sum = 0.0
                    humid_sum = 0.0
                
                    avg_count = 0
                    avg_epoch = epoch

                # Update Min/Max Stats
                if baro < statsObj[PRESSUREBOUNDS_STAT]['statData'][MIN_BOUNDS]:
                    statsObj[PRESSUREBOUNDS_STAT]['statData'][MIN_BOUNDS] = baro
                elif baro > statsObj[PRESSUREBOUNDS_STAT]['statData'][MAX_BOUNDS]:
                    statsObj[PRESSUREBOUNDS_STAT]['statData'][MAX_BOUNDS] = baro

                if humid < statsObj[HUMIDITYBOUNDS_STAT]['statData'][MIN_BOUNDS]:
                    statsObj[HUMIDITYBOUNDS_STAT]['statData'][MIN_BOUNDS] = humid
                elif humid > statsObj[HUMIDITYBOUNDS_STAT]['statData'][MAX_BOUNDS]:
                    statsObj[HUMIDITYBOUNDS_STAT]['statData'][MAX_BOUNDS] = humid

                if temp < statsObj[TEMPERATUREBOUNDS_STAT]['statData'][MIN_BOUNDS]:
                    statsObj[TEMPERATUREBOUNDS_STAT]['statData'][MIN_BOUNDS] = temp
                elif temp > statsObj[TEMPERATUREBOUNDS_STAT]['statData'][MAX_BOUNDS]:
                    statsObj[TEMPERATUREBOUNDS_STAT]['statData'][MAX_BOUNDS] = temp

                # Update Validity Stats
                if epoch - prev_epoch > MAX_DELTA_T:
                    statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[TEMPERALVALIDITY_STAT]['statData'][VALID] += 1
                
                if baro > met_baro_MAX or baro < met_baro_MIN:
                    statsObj[PRESSUREVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[PRESSUREVALIDITY_STAT]['statData'][VALID] += 1
                
                if humid > met_humidity_MAX or humid < met_humidity_MIN:
                    statsObj[HUMIDITYVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[HUMIDITYVALIDITY_STAT]['statData'][VALID] += 1
                    
                if temp > met_temp_MAX or temp < met_temp_MIN:
                    statsObj[TEMPERATUREVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[TEMPERATUREVALIDITY_STAT]['statData'][VALID] += 1

                prev_epoch = epoch
                
                statsObj[ROWVALIDITY_STAT]['statData'][VALID] += 1
                
            except:
                if DEBUG:
                    print "Unexpected row error:", sys.exc_info()
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                statsObj[ROWVALIDITY_STAT]['statData'][INVALID] += 1
                continue
                
        
        #final row
        if epoch != avg_epoch:
            visualizerDataObj[0]['data'].append([int(epoch*1000), round(baro_sum/avg_count,2)])
            visualizerDataObj[1]['data'].append([int(epoch*1000), round(humid_sum/avg_count,2)])
            visualizerDataObj[2]['data'].append([int(epoch*1000), round(temp_sum/avg_count,2)])

        statsObj[TEMPERALBOUNDS_STAT]['statData'][END_EPOCH] = epoch
            
    # If the file cannot be processed return false.
    except:
        if DEBUG:
            print "Unexpected file error:", sys.exc_info()
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
        return False
    
    # Close the raw datafile
    finally:
        csvfile.close()
        
    # Calulate test results
    
    # Row Integrity Test
    if float(statsObj[ROWVALIDITY_STAT]['statData'][INVALID])/float(statsObj[ROWVALIDITY_STAT]['statData'][INVALID] + statsObj[ROWVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[ROWINTEGRITY_TEST]['results'] = 'Failed'
    elif statsObj[ROWVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[ROWINTEGRITY_TEST]['results'] = 'Warning'
        
    # Delta T Test
    if float(statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID])/float(statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID] + statsObj[TEMPERALVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[DELTAT_TEST]['results'] = 'Failed'
    elif statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[DELTAT_TEST]['results'] = 'Warning'
    
    # Bounds Test
    if float(statsObj[PRESSUREVALIDITY_STAT]['statData'][INVALID])/float(statsObj[PRESSUREVALIDITY_STAT]['statData'][INVALID] + statsObj[PRESSUREVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Failed'
    elif statsObj[PRESSUREVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Warning'
        
    if float(statsObj[HUMIDITYVALIDITY_STAT]['statData'][INVALID])/float(statsObj[HUMIDITYVALIDITY_STAT]['statData'][INVALID] + statsObj[HUMIDITYVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Failed'
    elif statsObj[HUMIDITYVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Warning'
        
    if float(statsObj[TEMPERATUREVALIDITY_STAT]['statData'][INVALID])/float(statsObj[TEMPERATUREVALIDITY_STAT]['statData'][INVALID] + statsObj[TEMPERATUREVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Failed'
    elif statsObj[TEMPERATUREVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Warning'
        
    outputJSON['visualizerData'] = visualizerDataObj
    outputJSON['qualityTests'] = qualityTestsObj
    outputJSON['stats'] = statsObj
    
    # If processing is successful, return the json object 
    return outputJSON

# -------------------------------------------------------------------------------------
# Function to process files of the 'tsg' dataType.  The function is passed the path to
# the raw datafile.
#
# If the raw datafile cannot be processed the function returns false.
# -------------------------------------------------------------------------------------
def procTSG(filePath):

    tsg_intTemp_MIN = 0.0
    tsg_intTemp_MAX = 60.0
    tsg_conductivity_MIN = -2.0
    tsg_conductivity_MAX = 6.0
    tsg_salinity_MIN = -10.0
    tsg_salinity_MAX = 50.0
    tsg_soundVel_MIN = 1400.0
    tsg_soundVel_MAX = 1600.0
    tsg_extTemp_MIN = 0.0
    tsg_extTemp_MAX = 60.0
    
    ROWINTEGRITY_TEST = 0
    DELTAT_TEST = 1
    BOUNDS_TEST = 2
    
    TEMPERALBOUNDS_STAT = 0
    INTTEMPBOUNDS_STAT = 1
    CONDUCTIVITYBOUNDS_STAT = 2
    SALINITYBOUNDS_STAT = 3
    SOUNDVELBOUNDS_STAT = 4
    EXTTEMPBOUNDS_STAT = 5
    TEMPERALVALIDITY_STAT = 6
    INTTEMPVALIDITY_STAT = 7
    CONDUCTIVITYVALIDITY_STAT = 8
    SALINITYVALIDITY_STAT = 9
    SOUNDVELVALIDITY_STAT = 10
    EXTTEMPVALIDITY_STAT = 11
    ROWVALIDITY_STAT = 12
    
    # List of column names for the raw csv-formatted datafile
    fieldNames = ('SCS Date',
                  'SCS Time',
                  'Internal Temp (C)',
                  'Conductivity (S/m)',
                  'Salinity (PSU)',
                  'Sound Velocity (m/s)',
                  'External Temp (C)'
                 )
    
    visualizerDataObj = [
        {"label":"Internal Temp",     "unit":"C",   "data":[]},
        {"label":"Conductivity", "unit":"S/m", "data":[]},
        {"label":"Salinity", "unit":"PSU", "data":[]},
        {"label":"SV", "unit":"m/s", "data":[]},
        {"label":"External Temp", "unit":"C", "data":[]},
    ]
    
    qualityTestsObj = [
        {'testName':'Row Integrity', 'results':'Passed'},
        {'testName':'Delta-T', 'results':'Passed'},
        {'testName':'Bounds', 'results':'Passed'}
    ]
    
    statsObj = [
        {'statName':'Temperal Bounds','statType':'timeBounds','statData':[0.0,0.0],'statUnit':'seconds'},                       #Start and end times
        {'statName':'IntTemp Bounds','statType':'bounds','statData':[tsg_intTemp_MAX,tsg_intTemp_MIN],'statUnit':'C'},                #Min/Max IntTemp        
        {'statName':'Conductivty Bounds','statType':'bounds','statData':[tsg_conductivity_MAX,tsg_conductivity_MIN],'statUnit':'S/m'},  #Min/Max Conductivity
        {'statName':'Salinity Bounds','statType':'bounds','statData':[tsg_salinity_MAX,tsg_salinity_MIN],'statUnit':'PSU'},             #Min/Max Salinity
        {'statName':'Sound Vel. Bounds','statType':'bounds','statData':[tsg_soundVel_MAX,tsg_soundVel_MIN],'statUnit':'m/s'},           #Min/Max Sound Velocity
        {'statName':'ExtTemp Bounds','statType':'bounds','statData':[tsg_extTemp_MAX,tsg_extTemp_MIN],'statUnit':'C'},                #Min/Max ExtTemp
        {'statName':'Temperal Validity','statType':'valueValidity','statData':[0,0]},       #Number of valid and invalid time gaps
        {'statName':'Int. Temp. Validity','statType':'valueValidity','statData':[0,0]},     #Number of valid and invalid int. temp readings
        {'statName':'Conductivity Validity','statType':'valueValidity','statData':[0,0]},   #Number of valid and invalid conductivity readings
        {'statName':'Salinity Validity','statType':'valueValidity','statData':[0,0]},       #Number of valid and invalid salinity readings        
        {'statName':'Sound Vel. Validity','statType':'valueValidity','statData':[0,0]},     #Number of valid and invalid sound velocity readings
        {'statName':'Ext. Temp. Validity','statType':'valueValidity','statData':[0,0]},     #Number of valid and invalid ext. temp readings
        {'statName':'Row Validity','statType':'rowValidity','statData':[0,0]}               #Number of valid and invalid rows
    ]

    # Open the raw datafile
    try:
        csvfile = open(filePath, 'r')
        reader = csv.DictReader( csvfile, fieldNames)
    
        # Add the remaining rows, including a preceding comma
        prev_epoch = 0.0
        avg_epoch = 0.0
        intTemp_sum = 0.0
        conductivity_sum = 0.0
        salinity_sum = 0.0
        soundVel_sum = 0.0
        extTemp_sum = 0.0
        avg_count = 1

        init = True
        while(init):
            firstRow = reader.next()
            try:
#                print firstRow
                prev_epoch = formatDateTime(firstRow['SCS Date'],firstRow['SCS Time'])
                avg_epoch = prev_epoch

                intTemp_sum = float(firstRow['Internal Temp (C)'].split('=', 1)[1])
                conductivity_sum = float(firstRow['Conductivity (S/m)'].split('=', 1)[1])
                salinity_sum = float(firstRow['Salinity (PSU)'].split('=', 1)[1])
                soundVel_sum = float(firstRow['Sound Velocity (m/s)'].split('=', 1)[1])
                extTemp_sum = float(firstRow['External Temp (C)'].split('=', 1)[1])

                # Add to array
                visualizerDataObj[0]['data'].append([int(prev_epoch*1000), round(intTemp_sum/avg_count,2)])
                visualizerDataObj[1]['data'].append([int(prev_epoch*1000), round(conductivity_sum/avg_count,2)])
                visualizerDataObj[2]['data'].append([int(prev_epoch*1000), round(salinity_sum/avg_count,2)])
                visualizerDataObj[3]['data'].append([int(prev_epoch*1000), round(soundVel_sum/avg_count,2)])
                visualizerDataObj[4]['data'].append([int(prev_epoch*1000), round(extTemp_sum/avg_count,2)])
                
                # Initialize Stats
                statsObj[TEMPERALBOUNDS_STAT]['statData'][START_EPOCH] = prev_epoch
                statsObj[TEMPERALBOUNDS_STAT]['statData'][END_EPOCH] = prev_epoch
                
                # Update Min/Max Stats
                statsObj[INTTEMPBOUNDS_STAT]['statData'][MIN_BOUNDS] = intTemp_sum
                statsObj[INTTEMPBOUNDS_STAT]['statData'][MAX_BOUNDS] = intTemp_sum
                
                statsObj[CONDUCTIVITYBOUNDS_STAT]['statData'][MIN_BOUNDS] = conductivity_sum
                statsObj[CONDUCTIVITYBOUNDS_STAT]['statData'][MAX_BOUNDS] = conductivity_sum
                
                statsObj[SALINITYBOUNDS_STAT]['statData'][MIN_BOUNDS] = salinity_sum
                statsObj[SALINITYBOUNDS_STAT]['statData'][MAX_BOUNDS] = salinity_sum
                
                statsObj[SOUNDVELBOUNDS_STAT]['statData'][MIN_BOUNDS] = soundVel_sum
                statsObj[SOUNDVELBOUNDS_STAT]['statData'][MAX_BOUNDS] = soundVel_sum
                
                statsObj[EXTTEMPBOUNDS_STAT]['statData'][MIN_BOUNDS] = extTemp_sum
                statsObj[EXTTEMPBOUNDS_STAT]['statData'][MAX_BOUNDS] = extTemp_sum
                
                # Update Validity Stats
                if intTemp_sum > tsg_intTemp_MAX or intTemp_sum < tsg_intTemp_MIN:
                    statsObj[INTTEMPVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[INTTEMPVALIDITY_STAT]['statData'][VALID] += 1
                    
                if conductivity_sum > tsg_conductivity_MAX or conductivity_sum < tsg_conductivity_MIN:
                    statsObj[CONDUCTIVITYVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[CONDUCTIVITYVALIDITY_STAT]['statData'][VALID] += 1
                
                if salinity_sum > tsg_salinity_MAX or salinity_sum < tsg_salinity_MIN:
                    statsObj[SALINITYVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[SALINITYVALIDITY_STAT]['statData'][VALID] += 1
                    
                if soundVel_sum > tsg_soundVel_MAX or soundVel_sum < tsg_soundVel_MIN:
                    statsObj[SOUNDVELVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[SOUNDVELVALIDITY_STAT]['statData'][VALID] += 1
                    
                if extTemp_sum > tsg_extTemp_MAX or extTemp_sum < tsg_extTemp_MIN:
                    statsObj[EXTTEMPVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[EXTTEMPVALIDITY_STAT]['statData'][VALID] += 1
            
                init = False
                statsObj[ROWVALIDITY_STAT]['statData'][VALID] += 1
                    
            except:
                if DEBUG:
                    print "Unexpected init error:", sys.exc_info()
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                statsObj[ROWVALIDITY_STAT]['statData'][INVALID] += 1
                continue

        # Process each row of the raw datafile
        for row in reader:
            epoch = formatDateTime(row['SCS Date'],row['SCS Time'])

            # Attempt to convert values to numerical representations, If there are any
            # problems, the row is skipped
            try:
                intTemp = float(row['Internal Temp (C)'].split('=', 1)[1])
                conductivity = float(row['Conductivity (S/m)'].split('=', 1)[1])
                salinity = float(row['Salinity (PSU)'].split('=', 1)[1])
                soundVel = float(row['Sound Velocity (m/s)'].split('=', 1)[1])
                extTemp = float(row['External Temp (C)'].split('=', 1)[1])
                
                intTemp_sum += intTemp
                conductivity_sum += conductivity
                salinity_sum += salinity
                soundVel_sum += soundVel
                extTemp_sum += extTemp
                avg_count += 1
                
                statsObj[ROWVALIDITY_STAT]['statData'][VALID] += 1
                
                # Subsample the file based on the defined interval.  
                if (epoch-avg_epoch > AVERAGE*60):
                    visualizerDataObj[0]['data'].append([int(epoch*1000), round(intTemp_sum/avg_count,2)])
                    visualizerDataObj[1]['data'].append([int(epoch*1000), round(conductivity_sum/avg_count,2)])
                    visualizerDataObj[2]['data'].append([int(epoch*1000), round(salinity_sum/avg_count,2)])
                    visualizerDataObj[3]['data'].append([int(epoch*1000), round(soundVel_sum/avg_count,2)])
                    visualizerDataObj[4]['data'].append([int(epoch*1000), round(extTemp_sum/avg_count,2)])

                    intTemp_sum = 0.0
                    conductivity_sum = 0.0
                    salinity_sum = 0.0
                    soundVel_sum = 0.0
                    extTemp_sum = 0.0
                
                    avg_count = 0
                    avg_epoch = epoch
            
                # Update Min/Max Stats
                if intTemp < statsObj[INTTEMPBOUNDS_STAT]['statData'][MIN_BOUNDS]:
                    statsObj[INTTEMPBOUNDS_STAT]['statData'][MIN_BOUNDS] = intTemp
                elif intTemp > statsObj[INTTEMPBOUNDS_STAT]['statData'][MAX_BOUNDS]:
                    statsObj[INTTEMPBOUNDS_STAT]['statData'][MAX_BOUNDS] = intTemp

                if conductivity < statsObj[CONDUCTIVITYBOUNDS_STAT]['statData'][MIN_BOUNDS]:
                    statsObj[CONDUCTIVITYBOUNDS_STAT]['statData'][MIN_BOUNDS] = conductivity
                elif conductivity > statsObj[CONDUCTIVITYBOUNDS_STAT]['statData'][MAX_BOUNDS]:
                    statsObj[CONDUCTIVITYBOUNDS_STAT]['statData'][MAX_BOUNDS] = conductivity

                if salinity < statsObj[SALINITYBOUNDS_STAT]['statData'][MIN_BOUNDS]:
                    statsObj[SALINITYBOUNDS_STAT]['statData'][MIN_BOUNDS] = salinity
                elif salinity > statsObj[SALINITYBOUNDS_STAT]['statData'][MAX_BOUNDS]:
                    statsObj[SALINITYBOUNDS_STAT]['statData'][MAX_BOUNDS] = salinity

                if soundVel < statsObj[SOUNDVELBOUNDS_STAT]['statData'][MIN_BOUNDS]:
                    statsObj[SOUNDVELBOUNDS_STAT]['statData'][MIN_BOUNDS] = soundVel
                elif soundVel > statsObj[SOUNDVELBOUNDS_STAT]['statData'][MAX_BOUNDS]:
                    statsObj[SOUNDVELBOUNDS_STAT]['statData'][MAX_BOUNDS] = soundVel

                if extTemp < statsObj[EXTTEMPBOUNDS_STAT]['statData'][MIN_BOUNDS]:
                    statsObj[EXTTEMPBOUNDS_STAT]['statData'][MIN_BOUNDS] = extTemp
                elif extTemp > statsObj[EXTTEMPBOUNDS_STAT]['statData'][MAX_BOUNDS]:
                    statsObj[EXTTEMPBOUNDS_STAT]['statData'][MAX_BOUNDS] = extTemp
                
                # Update Validity Stats
                if epoch - prev_epoch > MAX_DELTA_T:
                    statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[TEMPERALVALIDITY_STAT]['statData'][VALID] += 1
                
                if intTemp > tsg_intTemp_MAX or intTemp < tsg_intTemp_MIN:
                    statsObj[INTTEMPVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[INTTEMPVALIDITY_STAT]['statData'][VALID] += 1
                
                if conductivity > tsg_conductivity_MAX or conductivity < tsg_conductivity_MIN:
                    statsObj[CONDUCTIVITYVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[CONDUCTIVITYVALIDITY_STAT]['statData'][VALID] += 1
                
                if salinity > tsg_salinity_MAX or salinity < tsg_salinity_MIN:
                    statsObj[SALINITYVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[SALINITYVALIDITY_STAT]['statData'][VALID] += 1
                
                if soundVel > tsg_soundVel_MAX or soundVel < tsg_soundVel_MIN:
                    statsObj[SOUNDVELVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[SOUNDVELVALIDITY_STAT]['statData'][VALID] += 1
            
                if extTemp > tsg_extTemp_MAX or extTemp < tsg_extTemp_MIN:
                    statsObj[EXTTEMPVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[EXTTEMPVALIDITY_STAT]['statData'][VALID] += 1

                prev_epoch = epoch
                
            except:
                if DEBUG:
                    print "Unexpected row error:", sys.exc_info()
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                statsObj[ROWVALIDITY_STAT]['statData'][INVALID] += 1
                continue            

        #final row
        if epoch != avg_epoch:
            visualizerDataObj[0]['data'].append([int(epoch*1000), round(intTemp_sum/avg_count,2)])
            visualizerDataObj[1]['data'].append([int(epoch*1000), round(conductivity_sum/avg_count,2)])
            visualizerDataObj[2]['data'].append([int(epoch*1000), round(salinity_sum/avg_count,2)])
            visualizerDataObj[3]['data'].append([int(epoch*1000), round(soundVel_sum/avg_count,2)])
            visualizerDataObj[4]['data'].append([int(epoch*1000), round(extTemp_sum/avg_count,2)])

        statsObj[TEMPERALBOUNDS_STAT]['statData'][END_EPOCH] = epoch

    # If the file cannot be processed return false.
    except:
        if DEBUG:
            print "Unexpected file error:", sys.exc_info()
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
        return False
    
    # Close the raw datafile
    finally:
        csvfile.close()
    
    # Calulate test results
    
    # Row Integrity Test
    if float(statsObj[ROWVALIDITY_STAT]['statData'][INVALID])/float(statsObj[ROWVALIDITY_STAT]['statData'][INVALID] + statsObj[ROWVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[ROWINTEGRITY_TEST]['results'] = 'Failed'
    elif statsObj[ROWVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[ROWINTEGRITY_TEST]['results'] = 'Warning'
        
    # Delta T Test
    if float(statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID])/float(statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID] + statsObj[TEMPERALVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[DELTAT_TEST]['results'] = 'Failed'
    elif statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[DELTAT_TEST]['results'] = 'Warning'
    
    # Bounds Test
    if float(statsObj[INTTEMPVALIDITY_STAT]['statData'][INVALID])/float(statsObj[INTTEMPVALIDITY_STAT]['statData'][INVALID] + statsObj[INTTEMPVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Failed'
    elif statsObj[INTTEMPVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Warning'
    
    if float(statsObj[CONDUCTIVITYVALIDITY_STAT]['statData'][INVALID])/float(statsObj[CONDUCTIVITYVALIDITY_STAT]['statData'][INVALID] + statsObj[CONDUCTIVITYVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Failed'
    elif statsObj[CONDUCTIVITYVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Warning'
    
    if float(statsObj[SALINITYVALIDITY_STAT]['statData'][INVALID])/float(statsObj[SALINITYVALIDITY_STAT]['statData'][INVALID] + statsObj[SALINITYVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Failed'
    elif statsObj[SALINITYVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Warning'
        
    if float(statsObj[SOUNDVELVALIDITY_STAT]['statData'][INVALID])/float(statsObj[SOUNDVELVALIDITY_STAT]['statData'][INVALID] + statsObj[SOUNDVELVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Failed'
    elif statsObj[SOUNDVELVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Warning'
        
    if float(statsObj[EXTTEMPVALIDITY_STAT]['statData'][INVALID])/float(statsObj[EXTTEMPVALIDITY_STAT]['statData'][INVALID] + statsObj[EXTTEMPVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Failed'
    elif statsObj[EXTTEMPVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Warning'
        
    outputJSON['visualizerData'] = visualizerDataObj
    outputJSON['qualityTests'] = qualityTestsObj
    outputJSON['stats'] = statsObj
    
    # If processing is successful, return the json object 
    return outputJSON

# -------------------------------------------------------------------------------------
# Function to process files of the 'twind' dataType.  The function is passed the path
# to the raw datafile.
#
# If the raw datafile cannot be processed the function returns false.
# -------------------------------------------------------------------------------------
def procTWIND(filePath):

    twind_speed_MIN =0.0
    twind_speed_MAX = 100.0
    twind_direction_MIN = 0.0
    twind_direction_MAX = 359.99
    
    ROWINTEGRITY_TEST = 0
    DELTAT_TEST = 1
    BOUNDS_TEST = 2
    
    TEMPERALBOUNDS_STAT = 0
    SPEEDBOUNDS_STAT = 1
    DIRECTIONBOUNDS_STAT = 2
    TEMPERALVALIDITY_STAT = 3
    SPEEDVALIDITY_STAT = 4
    DIRECTIONVALIDITY_STAT = 5
    ROWVALIDITY_STAT = 6
    
    # List of column names for the raw csv-formatted datafile
    fieldNames = ('SCS Date',
                  'SCS Time',
                  'NMEA HDR',
                  'Speed (knots)',
                  'Direction (deg)'
                 )
    
    visualizerDataObj = [
        {"label":"Speed",     "unit":"knots",   "data":[]},
        {"label":"Direction", "unit":"degrees", "data":[]},
    ]
    
    qualityTestsObj = [
        {'testName':'Row Integrity', 'results':'Passed'},
        {'testName':'Delta-T', 'results':'Passed'},
        {'testName':'Bounds', 'results':'Passed'}
    ]
    
    statsObj = [
        {'statName':'Temperal Bounds','statType':'timeBounds','statData':[0.0,0.0],'statUnit':'seconds'},                           #Start and end times
        {'statName':'Speed Bounds','statType':'bounds','statData':[twind_speed_MAX,twind_speed_MIN],'statUnit':'knots'},            #Min/Max Wind speed        
        {'statName':'Direction Bounds','statType':'bounds','statData':[twind_direction_MAX,twind_direction_MIN],'statUnit':'deg'},  #Min/Max Wind Direction
        {'statName':'Temperal Validity','statType':'valueValidity','statData':[0,0]},   #Number of valid and invalid time gaps
        {'statName':'Speed Validity','statType':'valueValidity','statData':[0,0]},      #Number of valid and invalid pressure readings        
        {'statName':'Direction Validity','statType':'valueValidity','statData':[0,0]},  #Number of valid and invalid humidity readings
        {'statName':'Row Validity','statType':'rowValidity','statData':[0,0]}           #Number of valid and invalid rows
    ]

    # Open the raw datafile
    try:
        csvfile = open(filePath, 'r')
        reader = csv.DictReader( csvfile, fieldNames)
    
        prev_epoch = 0.0
        avg_epoch = 0.0
        speed_sum = 0.0
        direction_sum = 0.0
        avg_count = 1

        init = True
        while(init):
            firstRow = reader.next()
            try:
                prev_epoch = formatDateTime(firstRow['SCS Date'],firstRow['SCS Time'])
                avg_epoch = prev_epoch
                speed_sum = float(firstRow['Speed (knots)'])
                direction_sum = float(firstRow['Direction (deg)'])
                
                # Add to visualizer data array
                visualizerDataObj[0]['data'].append([int(prev_epoch*1000), round(speed_sum/avg_count,2)])
                visualizerDataObj[1]['data'].append([int(prev_epoch*1000), round(direction_sum/avg_count,2)])
                
                # Initialize Stats
                statsObj[TEMPERALBOUNDS_STAT]['statData'][START_EPOCH] = prev_epoch
                statsObj[TEMPERALBOUNDS_STAT]['statData'][END_EPOCH] = prev_epoch
                
                # Update Min/Max Stats
                statsObj[SPEEDBOUNDS_STAT]['statData'][MIN_BOUNDS] = speed_sum
                statsObj[SPEEDBOUNDS_STAT]['statData'][MAX_BOUNDS] = speed_sum

                statsObj[DIRECTIONBOUNDS_STAT]['statData'][MIN_BOUNDS] = direction_sum
                statsObj[DIRECTIONBOUNDS_STAT]['statData'][MAX_BOUNDS] = direction_sum

                # Update Validity Stats
                if speed_sum > twind_speed_MAX or speed_sum < twind_speed_MIN:
                    statsObj[SPEEDVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[SPEEDVALIDITY_STAT]['statData'][VALID] += 1

                if direction_sum > twind_direction_MAX or direction_sum < twind_direction_MIN:
                    statsObj[DIRECTIONVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[DIRECTIONVALIDITY_STAT]['statData'][VALID] += 1
                    
                init = False
                statsObj[ROWVALIDITY_STAT]['statData'][VALID] += 1
                    
            except:
                if DEBUG:
                    print "Unexpected init error:", sys.exc_info()
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                statsObj[ROWVALIDITY_STAT]['statData'][INVALID] += 1
                continue
                
        # Process each row of the raw datafile
        for row in reader:
            epoch = formatDateTime(row['SCS Date'],row['SCS Time'])

            # Attempt to convert values to numerical representations, If there are any
            # problems, the row is skipped
            try:
                speed = float(row['Speed (knots)'])
                direction = float(row['Direction (deg)'])

                speed_sum += speed
                direction_sum += direction
                avg_count += 1
                
                # Subsample the file based on the defined interval.  
                if (epoch-avg_epoch > AVERAGE*60):
                    visualizerDataObj[0]['data'].append([int(epoch*1000), round(speed_sum/avg_count,2)])
                    visualizerDataObj[1]['data'].append([int(epoch*1000), round(direction_sum/avg_count,2)])

                    speed_sum = 0.0
                    direction_sum = 0.0
                    
                    avg_count = 0
                    avg_epoch = epoch

                # Update Min/Max Stats
                if speed < statsObj[SPEEDBOUNDS_STAT]['statData'][MIN_BOUNDS]:
                    statsObj[SPEEDBOUNDS_STAT]['statData'][MIN_BOUNDS] = speed
                elif speed > statsObj[SPEEDBOUNDS_STAT]['statData'][MAX_BOUNDS]:
                    statsObj[SPEEDBOUNDS_STAT]['statData'][MAX_BOUNDS] = speed

                if direction < statsObj[DIRECTIONBOUNDS_STAT]['statData'][MIN_BOUNDS]:
                    statsObj[DIRECTIONBOUNDS_STAT]['statData'][MIN_BOUNDS] = direction
                elif direction > statsObj[DIRECTIONBOUNDS_STAT]['statData'][MAX_BOUNDS]:
                    statsObj[DIRECTIONBOUNDS_STAT]['statData'][MAX_BOUNDS] = direction

                # Update Validity Stats
                if epoch - prev_epoch > MAX_DELTA_T:
                    statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[TEMPERALVALIDITY_STAT]['statData'][VALID] += 1
                
                if speed > twind_speed_MAX or speed < twind_speed_MIN:
                    statsObj[SPEEDVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[SPEEDVALIDITY_STAT]['statData'][VALID] += 1
                
                if direction > twind_direction_MAX or direction < twind_direction_MIN:
                    statsObj[DIRECTIONVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[DIRECTIONVALIDITY_STAT]['statData'][VALID] += 1
                    
                prev_epoch = epoch
                
                statsObj[ROWVALIDITY_STAT]['statData'][VALID] += 1
                
            except:
                if DEBUG:
                    print "Unexpected row error:", sys.exc_info()
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                statsObj[ROWVALIDITY_STAT]['statData'][INVALID] += 1
                continue
                
        
        #final row
        if epoch != avg_epoch:
            visualizerDataObj[0]['data'].append([int(epoch*1000), round(speed_sum/avg_count,2)])
            visualizerDataObj[1]['data'].append([int(epoch*1000), round(direction_sum/avg_count,2)])

        statsObj[TEMPERALBOUNDS_STAT]['statData'][END_EPOCH] = epoch
            
    # If the file cannot be processed return false.
    except:
        if DEBUG:
            print "Unexpected file error:", sys.exc_info()
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
        return False
    
    # Close the raw datafile
    finally:
        csvfile.close()
        
    # Calulate test results
    
    # Row Integrity Test
    if float(statsObj[ROWVALIDITY_STAT]['statData'][INVALID])/float(statsObj[ROWVALIDITY_STAT]['statData'][INVALID] + statsObj[ROWVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[ROWINTEGRITY_TEST]['results'] = 'Failed'
    elif statsObj[ROWVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[ROWINTEGRITY_TEST]['results'] = 'Warning'
        
    # Delta T Test
    if float(statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID])/float(statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID] + statsObj[TEMPERALVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[DELTAT_TEST]['results'] = 'Failed'
    elif statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[DELTAT_TEST]['results'] = 'Warning'
    
    # Bounds Test
    if float(statsObj[SPEEDVALIDITY_STAT]['statData'][INVALID])/float(statsObj[SPEEDVALIDITY_STAT]['statData'][INVALID] + statsObj[SPEEDVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Failed'
    elif statsObj[SPEEDVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Warning'
        
    if float(statsObj[DIRECTIONVALIDITY_STAT]['statData'][INVALID])/float(statsObj[DIRECTIONVALIDITY_STAT]['statData'][INVALID] + statsObj[DIRECTIONVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Failed'
    elif statsObj[DIRECTIONVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Warning'
        
    outputJSON['visualizerData'] = visualizerDataObj
    outputJSON['qualityTests'] = qualityTestsObj
    outputJSON['stats'] = statsObj
    
    # If processing is successful, return the json object 
    return outputJSON

# -------------------------------------------------------------------------------------
# Function to process files of the 'svp' dataType.  The function is passed the path to
# the raw datafile.
#
# If the raw datafile cannot be processed the function returns false.
# -------------------------------------------------------------------------------------
def procSVP(filePath):

    svp_soundVel_MIN =1400.0
    svp_soundVel_MAX = 1600.0
    
    fieldNames = ('SCS Date',
                  'SCS Time',
                  'Sound Velocity (m/s)',
                 )

    visualizerDataObj = [
        {"label":"Sound Velocity", "unit":"m/s", "data":[]},
    ]
    
    qualityTestsObj = [
        {'testName':'Row Integrity', 'results':'Passed'},
        {'testName':'Delta-T', 'results':'Passed'},
        {'testName':'Bounds', 'results':'Passed'}
    ]
    
    statsObj = [
        {'statName':'Temperal Bounds','statType':'timeBounds','statData':[0.0,0.0],'statUnit':'seconds'},                   #Start and end times
        {'statName':'Sound Vel. Bounds','statType':'bounds','statData':[svp_soundVel_MAX,svp_soundVel_MIN],'statUnit':'m/s'},   #Min/Max sound velocity        
        {'statName':'Temperal Validity','statType':'valueValidity','statData':[0,0]},   #Number of valid and invalid time gaps
        {'statName':'Sound Vel. Validity','statType':'valueValidity','statData':[0,0]}, #Number of valid and invalid sound velocity readings        
        {'statName':'Row Validity','statType':'rowValidity','statData':[0,0]}           #Number of valid and invalid rows
    ]
    
    ROWINTEGRITY_TEST = 0
    DELTAT_TEST = 1
    BOUNDS_TEST = 2
    
    TEMPERALBOUNDS_STAT = 0
    SOUNDVELBOUNDS_STAT = 1
    TEMPERALVALIDITY_STAT = 2
    SOUNDVELVALIDITY_STAT = 3
    ROWVALIDITY_STAT = 4

    # Open the raw datafile
    try:
        csvfile = open(filePath, 'r')
        reader = csv.DictReader( csvfile, fieldNames)
    
        prev_epoch = 0.0
        avg_epoch = 0.0
        soundVel_sum = 0.0
        avg_count = 1

        init = True
        while(init):
            firstRow = reader.next()
            try:
                prev_epoch = formatDateTime(firstRow['SCS Date'],firstRow['SCS Time'])
                avg_epoch = prev_epoch
                soundVel_sum = float(firstRow['Sound Velocity (m/s)'])
                
                # Add to visualizer data array
                visualizerDataObj[0]['data'].append([int(prev_epoch*1000), round(soundVel_sum/avg_count,2)])
                
                # Initialize Stats
                statsObj[TEMPERALBOUNDS_STAT]['statData'][START_EPOCH] = prev_epoch
                statsObj[TEMPERALBOUNDS_STAT]['statData'][END_EPOCH] = prev_epoch
                
                # Update Min/Max Stats
                statsObj[SOUNDVELBOUNDS_STAT]['statData'][MIN_BOUNDS] = soundVel_sum
                statsObj[SOUNDVELBOUNDS_STAT]['statData'][MAX_BOUNDS] = soundVel_sum

                # Update Validity Stats
                if soundVel_sum > svp_soundVel_MAX or soundVel_sum < svp_soundVel_MIN:
                    statsObj[SOUNDVELVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[SOUNDVELVALIDITY_STAT]['statData'][VALID] += 1

                init = False
                statsObj[ROWVALIDITY_STAT]['statData'][VALID] += 1
                    
            except:
                if DEBUG:
                    print "Unexpected init error:", sys.exc_info()
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                statsObj[ROWVALIDITY_STAT]['statData'][INVALID] += 1
                continue
                
        # Process each row of the raw datafile
        for row in reader:
            epoch = formatDateTime(row['SCS Date'],row['SCS Time'])

            # Attempt to convert values to numerical representations, If there are any
            # problems, the row is skipped
            try:
                soundVel = float(row['Sound Velocity (m/s)'])

                soundVel_sum += soundVel
                avg_count += 1
                
                # Subsample the file based on the defined interval.  
                if (epoch-avg_epoch > AVERAGE*60):
                    visualizerDataObj[0]['data'].append([int(epoch*1000), round(soundVel_sum/avg_count,2)])

                    soundVel_sum = 0.0
                    
                    avg_count = 0
                    avg_epoch = epoch

                # Update Min/Max Stats
                if soundVel < statsObj[SOUNDVELBOUNDS_STAT]['statData'][MIN_BOUNDS]:
                    statsObj[SOUNDVELBOUNDS_STAT]['statData'][MIN_BOUNDS] = soundVel
                elif soundVel > statsObj[SOUNDVELBOUNDS_STAT]['statData'][MAX_BOUNDS]:
                    statsObj[SOUNDVELBOUNDS_STAT]['statData'][MAX_BOUNDS] = soundVel

                # Update Validity Stats
                if epoch - prev_epoch > MAX_DELTA_T:
                    statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[TEMPERALVALIDITY_STAT]['statData'][VALID] += 1
                
                if soundVel > svp_soundVel_MAX or soundVel < svp_soundVel_MIN:
                    statsObj[SOUNDVELVALIDITY_STAT]['statData'][INVALID] += 1
                else:
                    statsObj[SOUNDVELVALIDITY_STAT]['statData'][VALID] += 1
                    
                prev_epoch = epoch
                
                statsObj[ROWVALIDITY_STAT]['statData'][VALID] += 1
                
            except:
                if DEBUG:
                    print "Unexpected row error:", sys.exc_info()
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                statsObj[ROWVALIDITY_STAT]['statData'][INVALID] += 1
                continue
                
        
        #final row
        if epoch != avg_epoch:
            visualizerDataObj[0]['data'].append([int(epoch*1000), round(soundVel_sum/avg_count,2)])

        statsObj[TEMPERALBOUNDS_STAT]['statData'][END_EPOCH] = epoch
            
    # If the file cannot be processed return false.
    except:
        if DEBUG:
            print "Unexpected file error:", sys.exc_info()
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
        return False
    
    # Close the raw datafile
    finally:
        csvfile.close()
        
    # Calulate test results
    
    # Row Integrity Test
    if float(statsObj[ROWVALIDITY_STAT]['statData'][INVALID])/float(statsObj[ROWVALIDITY_STAT]['statData'][INVALID] + statsObj[ROWVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[ROWINTEGRITY_TEST]['results'] = 'Failed'
    elif statsObj[ROWVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[ROWINTEGRITY_TEST]['results'] = 'Warning'
        
    # Delta T Test
    if float(statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID])/float(statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID] + statsObj[TEMPERALVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[DELTAT_TEST]['results'] = 'Failed'
    elif statsObj[TEMPERALVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[DELTAT_TEST]['results'] = 'Warning'
    
    # Bounds Test
    if float(statsObj[SOUNDVELVALIDITY_STAT]['statData'][INVALID])/float(statsObj[SOUNDVELVALIDITY_STAT]['statData'][INVALID] + statsObj[SOUNDVELVALIDITY_STAT]['statData'][VALID]) > FAIL_THRESHOLD/100.0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Failed'
    elif statsObj[SOUNDVELVALIDITY_STAT]['statData'][INVALID] > 0:
        qualityTestsObj[BOUNDS_TEST]['results'] = 'Warning'
        
    outputJSON['visualizerData'] = visualizerDataObj
    outputJSON['qualityTests'] = qualityTestsObj
    outputJSON['stats'] = statsObj
    
    # If processing is successful, return the json object 
    return outputJSON

    
# -------------------------------------------------------------------------------------
# Main function of the script should it be run as a stand-alone utility.
# -------------------------------------------------------------------------------------
def main(argv):
    
    parser = argparse.ArgumentParser(description='SCS dataDashboard Processing Utilty')
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