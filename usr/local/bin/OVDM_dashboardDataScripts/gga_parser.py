# =================================================================================== #
#
#         FILE:  gga_parser.py
#
#        USAGE:  gga_parser.py [-h] [-c] <dataFile>
#
#  DESCRIPTION:  Parse the supplied NMEA-formtted GGA file (w/ SCS formatted timestamp)
#                and return the json-formatted string used by OpenVDM as part of it's
#                Data dashboard.
#
#      OPTIONS:  [-h] Return the help message.
#                [-c] Use CSVkit to clean the datafile prior to processing
#                <dataFile> Full or relative path of the data file to process.
#
# REQUIREMENTS:  python2.7, Python Modules: sys, os, argparse, json, pandas
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  1.0
#      CREATED:  2016-08-29
#     REVISION:  2016-10-30
#
# LICENSE INFO:  Open Vessel Data Management v2.2 (OpenVDMv2)
#                Copyright (C) 2017 OceanDataRat.org
#
#        NOTES:  Requires Pandas v0.18 or higher
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
from __future__ import print_function
import pandas as pd
import numpy as np
import json
import argparse
import subprocess
import tempfile
import sys
import copy
import os
import shutil
import csv
from geopy.distance import great_circle
from itertools import (takewhile,repeat)

# visualizerDataObj = {'data':[], 'unit':'', 'label':''}
# statObj = {'statName':'', 'statUnit':'', 'statType':'', 'statData':[]}
# qualityTestObj = {"testName": "", "results": ""}

RAW_COLUMNS = ['date','time','hdr','gps_time','latitude','NS','longitude','EW','fix_quality','num_satellites','hdop','altitude','altitude_m','height_wgs84','height_wgs84_m','last_update','dgps_station_checksum']
PROC_COLUMNS = ['date_time','latitude','longitude','num_satellites','hdop','altitude','height_wgs84']
CROP_COLUMNS = ['date_time','latitude','longitude']

MAX_VELOCITY = 13.8 #Max speed of vessel (mph)

MIN_LATITUDE= -60.0
MAX_LATITUDE = 60.0
MIN_LONGITUDE = -180.0
MAX_LONGITUDE = 180.0

MAX_DELTA_T = pd.Timedelta('10 seconds')

RESAMPLE_INTERVAL = '1T' # 1 minute

DEBUG = False
CSVKIT = False

def debugPrint(*args, **kwargs):
    if DEBUG:
        errPrint(*args, **kwargs)

def errPrint(*args, **kwargs):
        print(*args, file=sys.stderr, **kwargs)

def rawincount(filename):
    f = open(filename, 'rb')
    bufgen = takewhile(lambda x: x, (f.read(1024*1024) for _ in repeat(None)))
    return sum( buf.count(b'\n') for buf in bufgen )

def csvCleanup(filepath):

    command = ['csvclean', filepath]
    errors = 0

    s = ' '
    debugPrint(s.join(command))

    proc = subprocess.Popen(command,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = proc.communicate()

    (dirname, basename) = os.path.split(filepath)

    debugPrint("Dirname:" + dirname)
    debugPrint("Basename:" + basename)

    outfile = os.path.join(dirname, os.path.splitext(basename)[0] + '_out.csv')
    errfile = os.path.join(dirname, os.path.splitext(basename)[0] + '_err.csv')

    debugPrint("Outfile: " + outfile)
    debugPrint("Errfile: " + errfile)

    if os.path.isfile(errfile):
        errors = rawincount(errfile)-1

    return (errors, outfile)

def parseFile(filePath):
    output = {}
    output['visualizerData'] = []
    output['qualityTests'] = []
    output['stats'] = []

    tmpdir = tempfile.mkdtemp()
    
    outfile = filePath
    errors = 0

    if CSVKIT:
        shutil.copy(filePath, tmpdir)
        (errors, outfile) = csvCleanup(os.path.join(tmpdir, os.path.basename(filePath)))
        debugPrint('Error: ', errors)
    
    rawIntoDf = {'date_time':[],'latitude':[],'longitude':[],'num_satellites':[],'hdop':[],'altitude':[],'height_wgs84':[]}

    csvfile = open(outfile, 'r')
    reader = csv.DictReader( csvfile, RAW_COLUMNS)

    for line in reader:

        try:

            line_date_time = line['date'] + ' ' + line['time']

            longitude_degrees = float(line['longitude'][:3])
            longitude_dminutes = float(line['longitude'][3:])/60
            lon_hemisphere = 1.0

            if line['EW'] == 'W':
                lon_hemisphere = -1.0

            line_longitude = ((longitude_degrees + longitude_dminutes) * lon_hemisphere)

            latitude_degrees = float(line['latitude'][:2])
            latitude_dminutes = float(line['latitude'][2:])/60
            lat_hemisphere = 1.0

            if line['NS'] == 'S':
                lat_hemisphere = -1.0

            line_latitude = ((latitude_degrees + latitude_dminutes) * lat_hemisphere)

            line_num_satellites = int(line['num_satellites'])
            line_hdop = float(line['hdop'])

            if line['altitude'] == '':
                line_altitude = float(0)
            else:
                line_altitude = float(line['altitude'])

            if line['height_wgs84'] == '':
                line_height_wgs84 = float(0)
            else:
                line_height_wgs84 = float(line['height_wgs84'])

        except:
            debugPrint('Parsing error: ', line)
            errors += 1
        else:

            if line_latitude == 0.0 and line_longitude == 0.0:
                continue

            if line_latitude == 0.0 or line_longitude == 0.0:
                errors += 1
                continue

            if line_latitude < MIN_LATITUDE or line_latitude > MAX_LATITUDE:
                errors += 1
                continue

            if line_longitude < MIN_LONGITUDE or line_longitude > MAX_LONGITUDE:
                errors += 1
                continue

            rawIntoDf['date_time'].append(line_date_time)
            rawIntoDf['latitude'].append(line_latitude)
            rawIntoDf['longitude'].append(line_longitude)
            rawIntoDf['num_satellites'].append(line_num_satellites)
            rawIntoDf['hdop'].append(line_hdop)
            rawIntoDf['altitude'].append(line_altitude)
            rawIntoDf['height_wgs84'].append(line_height_wgs84)

    shutil.rmtree(tmpdir)

    if len(rawIntoDf['date_time']) == 0:
        return None

    df_proc = pd.DataFrame(rawIntoDf)

    df_proc['date_time'] = pd.to_datetime(df_proc['date_time'], infer_datetime_format=True)

    df_proc = df_proc.join(df_proc['date_time'].diff().to_frame(name='deltaT'))

    distance = df_proc[['latitude', 'longitude']]

    distance = distance.join(distance.shift(), rsuffix = "_prev")

    df_proc['distance'] = distance.apply(lambda row: (great_circle((row['latitude_prev'], row['longitude_prev']), (row['latitude'], row['longitude']))).nm, axis=1)

    df_proc['velocity'] = df_proc['distance'] / (df_proc.deltaT.dt.total_seconds() / 3600)

    #debugPrint(df_proc.head())
    #debugPrint(df_proc.dtypes)

    rowValidityStat = {'statName':'Row Validity', 'statType':'rowValidity', 'statData':[len(df_proc), errors]}
    output['stats'].append(rowValidityStat)

    geographicPositionStat = {'statName': 'Geographic Bounds','statUnit': 'ddeg', 'statType':'geoBounds', 'statData':[round(df_proc.latitude.max(),3),round(df_proc.longitude.max(),3),round(df_proc.latitude.min(),3),round(df_proc.longitude.min(),3)]}
    output['stats'].append(geographicPositionStat)

    #latitudeValidityStat = {'statName':'Latitude Validity', 'statType':'valueValidity', 'statData':[len(df_proc[(df_proc['latitude'] >= MIN_LATITUDE) & (df_proc['latitude'] <= MAX_LATITUDE)]),len(df_proc[(df_proc['latitude'] < MIN_LATITUDE) & (df_proc['latitude'] > MAX_LATITUDE)])]}
    #output['stats'].append(latitudeValidityStat)

    #longitudeValidityStat = {'statName':'Longitude Validity', 'statType':'valueValidity', 'statData':[len(df_proc[(df_proc['longitude'] >= MIN_LONGITUDE) & (df_proc['longitude'] <= MAX_LONGITUDE)]),len(df_proc[(df_proc['longitude'] < MIN_LONGITUDE) & (df_proc['longitude'] > MAX_LONGITUDE)])]}
    #output['stats'].append(longitudeValidityStat)

    if np.isinf(df_proc.velocity.max()):
        velocityStat = {'statName': 'Velocity Bounds','statUnit': 'kts', 'statType':'bounds', 'statData':[round(df_proc.velocity.min(),3), 999999.999]}
        debugPrint("They've gone to plaid")
    else:
        velocityStat = {'statName': 'Velocity Bounds','statUnit': 'kts', 'statType':'bounds', 'statData':[round(df_proc.velocity.min(),3), round(df_proc.velocity.max(),3)]}
    output['stats'].append(velocityStat)

    velocityValidityStat = {'statName':'Velocity Validity', 'statType':'valueValidity', 'statData':[len(df_proc[(df_proc['velocity'] <= MAX_VELOCITY)]),len(df_proc[(df_proc['velocity'] > MAX_VELOCITY)])]}
    output['stats'].append(velocityValidityStat)

    distanceStat = {'statName': 'Distance Traveled','statUnit': 'nm', 'statType':'totalValue', 'statData':[round(df_proc.distance.sum(axis=0),3)]}
    output['stats'].append(distanceStat)

    temporalStat = {'statName': 'Temporal Bounds','statUnit': 'seconds', 'statType':'timeBounds', 'statData':[df_proc.date_time.min().strftime('%s'), df_proc.date_time.max().strftime('%s')]}
    output['stats'].append(temporalStat)

    deltaTStat = {"statName": "Delta-T Bounds","statUnit": "seconds","statType": "bounds","statData": [round(df_proc.deltaT.min().total_seconds(),3), round(df_proc.deltaT.max().total_seconds(),3)]}
    output['stats'].append(deltaTStat)

    deltaTValidityStat = {'statName':'DeltaT Validity', 'statType':'valueValidity', 'statData':[len(df_proc[(df_proc['deltaT'] <= MAX_DELTA_T)]),len(df_proc[(df_proc['deltaT'] > MAX_DELTA_T)])]}
    output['stats'].append(deltaTValidityStat)

    num_satellitesStat = {'statName': 'Number of Satellites','statUnit': 'sats', 'statType':'bounds', 'statData':[round(df_proc.num_satellites.min(),3), round(df_proc.num_satellites.max(),3)]}
    output['stats'].append(num_satellitesStat)

    hdopStat = {'statName': 'Horizontal Degree of Precision','statUnit': '', 'statType':'bounds', 'statData':[round(df_proc.hdop.min(),3), round(df_proc.hdop.max(),3)]}
    output['stats'].append(hdopStat)

    altitudeStat = {'statName': 'Altitude','statUnit': 'm', 'statType':'bounds', 'statData':[round(df_proc.altitude.min(),3), round(df_proc.altitude.max(),3)]}
    output['stats'].append(altitudeStat)

    height_wgs84Stat = {'statName': 'Height WGS84','statUnit': 'm', 'statType':'bounds', 'statData':[round(df_proc.height_wgs84.min(),3), round(df_proc.height_wgs84.max(),3)]}
    output['stats'].append(height_wgs84Stat)


    rowQualityTest = {"testName": "Rows", "results": "Passed"}
    if rowValidityStat['statData'][1] > 0:
        if rowValidityStat['statData'][1]/rowValidityStat['statData'][0] > .10:
            rowQualityTest['results'] = "Failed"
        else:
            rowQualityTest['results'] = "Warning"
    output['qualityTests'].append(rowQualityTest)

    deltaTQualityTest = {"testName": "DeltaT", "results": "Passed"}
    if deltaTValidityStat['statData'][1] > 0:
        if deltaTValidityStat['statData'][1]/len(df_proc) > .10:
            deltaTQualityTest['results'] = "Failed"
        else:
            deltaTQualityTest['results'] = "Warning"
    output['qualityTests'].append(deltaTQualityTest)

    #latitudeQualityTest = {"testName": "Latitude", "results": "Passed"}
    #if latitudeValidityStat['statData'][1] > 0:
    #    if latitudeValidityStat['statData'][1]/len(df_proc) > .10:
    #        latitudeQualityTest['results'] = "Failed"
    #    else:
    #        latitudeQualityTest['results'] = "Warning"
    #output['qualityTests'].append(latitudeQualityTest)

    #longitudeQualityTest = {"testName": "Longitude", "results": "Passed"}
    #if longitudeValidityStat['statData'][1] > 0:
    #    if longitudeValidityStat['statData'][1]/len(df_proc) > .10:
    #        longitudeQualityTest['results'] = "Failed"
    #    else:
    #        longitudeQualityTest['results'] = "Warning"
    #output['qualityTests'].append(longitudeQualityTest)

    velocityQualityTest = {"testName": "Velocity", "results": "Passed"}
    if velocityValidityStat['statData'][1] > 0:
        if velocityValidityStat['statData'][1]/len(df_proc) > .10:
            velocityQualityTest['results'] = "Failed"
        else:
            velocityQualityTest['results'] = "Warning"
    output['qualityTests'].append(velocityQualityTest)

    #remove rows with bad data

    #debugPrint(df_proc[(df_proc['longitude'] < MIN_LONGITUDE) & (df_proc['longitude'] > MAX_LONGITUDE)])
    #debugPrint(df_proc[(df_proc['latitude'] < MIN_LATITUDE) & (df_proc['latitude'] > MAX_LATITUDE)])

    #df_proc = df_proc.drop(df_proc[(df_proc['longitude'] < MIN_LONGITUDE) & (df_proc['longitude'] > MAX_LONGITUDE)].index)
    #df_proc = df_proc.drop(df_proc[(df_proc['latitude'] < MIN_LATITUDE) & (df_proc['latitude'] > MAX_LATITUDE)].index)

    df_crop = df_proc[CROP_COLUMNS]

    #errPrint('Created df_crop')
    #errPrint(df_crop.head())

    df_crop = df_crop.set_index('date_time')

    #errPrint('Set index to date_time')
    #errPrint(df_crop.head())

    df_crop = df_crop.resample(RESAMPLE_INTERVAL, label='right', closed='right').mean()

    #errPrint('Resample')
    #errPrint(df_crop.head())

    df_crop = df_crop.reset_index()

    #errPrint('Reset Index')
    #errPrint(df_crop.head())

    decimals = pd.Series([8,8], index=['latitude', 'longitude'])
    df_crop = df_crop.round(decimals)

    events = np.split(df_crop, np.where(np.isnan(df_crop.latitude))[0])

    # removing NaN entries
    events = [ev[~np.isnan(ev.latitude)] for ev in events if not isinstance(ev, np.ndarray)]

    # removing empty DataFrames
    events = [ev for ev in events if not ev.empty]

    visualizerDataObj = {
        'type':'FeatureCollection',
        'features': []
    }

    for ev in events:
        debugPrint("EV: ", ev)
        feature = {
            'type':'Feature',
            'geometry':{
                'type':'LineString',
                'coordinates':json.loads(ev[['longitude','latitude']].to_json(orient='values'))
            },
            'properties': {
                'coordTimes': json.loads(ev['date_time'].to_json(orient='values')),
                'name': filePath
            }
        }
        #print(feature)
        visualizerDataObj['features'].append(feature)

    output['visualizerData'].append(visualizerDataObj)

    return output

# -------------------------------------------------------------------------------------
# Main function of the script should it be run as a stand-alone utility.
# -------------------------------------------------------------------------------------
def main(argv):

    parser = argparse.ArgumentParser(description='Parse NMEA GGA data')
    parser.add_argument('dataFile', metavar='dataFile', help='the raw data file to process')
    parser.add_argument('-d', '--debug', action='store_true', help=' display debug messages')
    parser.add_argument('-c', '--csvkit', action='store_true', help=' clean datafile using CSVKit')

    args = parser.parse_args()
    if args.debug:
        global DEBUG
        DEBUG = True
        debugPrint("Running in debug mode")

    if args.csvkit:
        global CSVKIT
        CSVKIT = True
        debugPrint("Using CSVKit to clean data file prior to processing")

    if not os.path.isfile(args.dataFile):
        errPrint('ERROR: File not found\n')
        sys.exit(1)

    jsonObj = parseFile(args.dataFile)
    if jsonObj:
        print(json.dumps(jsonObj))
        sys.exit(0)
    else:
        sys.exit(1)

# -------------------------------------------------------------------------------------
# Required python code for running the script as a stand-alone utility
# -------------------------------------------------------------------------------------
if __name__ == "__main__":
    main(sys.argv[1:])
