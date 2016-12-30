# =================================================================================== #
#
#         FILE:  met_parser.py
#
#        USAGE:  met_parser.py [-h] [-c] <dataFile>
#
#  DESCRIPTION:  Parse the supplied NMEA-formtted MET file (w/ SCS formatted timestamp)
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
#     REVISION:  2016-12-29
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
from itertools import (takewhile,repeat)

# visualizerDataObj = {'data':[], 'unit':'', 'label':''}
# statObj = {'statName':'', 'statUnit':'', 'statType':'', 'statData':[]}
# qualityTestObj = {"testName": "", "results": ""}

RAW_COLUMNS = ['date','time','hdr','Sensor_Date','Sensor_Time','Barometer_(mBar)','Barometer_Sensor_Height','Barometer_Data_Quality','Air_Temperature_(C)','Air_Temperature_Sensor_Height','Air_Temperature_Data_Quality','Relative_Humidity_(%)','Relative_Humidity_Sensor_Height','Relative_Humidity_Data_Quality','Vector_Wind_Speed_(m/s)','Vector_Wind_Direction_(degrees, Relative to Bow)','Scalar_Wind_Speed_(m/s)','Maximum_Wind_Speed_(m/s)','Wind_Sensor_Height','Wind_Sensor_Data_Quality','Shortwave_Irradiance_(Wm-2)','Shortwave_Irradiance_Sensor_Height','Shortwave_Irradiance_Data_Quality','Longwave_Irradiance_(Wm-2)','PIR_Thermopile_Voltage_(mV)','PIR_Case_Temperature_(C)','PIR_Dome_Temperature_(C)','PIR_Sensor_Height','NMEA Checksum']
PROC_COLUMNS = ['date_time','Barometer_(mBar)','Air_Temperature_(C)','Relative_Humidity_(%)','Vector_Wind_Speed_(m/s)','Vector_Wind_Direction_(degrees, Relative to Bow)','Scalar_Wind_Speed_(m/s)','Maximum_Wind_Speed_(m/s)','Shortwave_Irradiance_(Wm-2)','Longwave_Irradiance_(Wm-2)','PIR_Thermopile_Voltage_(mV)','PIR_Case_Temperature_(C)','PIR_Dome_Temperature_(C)']
CROP_COLUMNS = ['date_time','Barometer_(mBar)','Air_Temperature_(C)','Relative_Humidity_(%)','Vector_Wind_Speed_(m/s)','Vector_Wind_Direction_(degrees, Relative to Bow)','Scalar_Wind_Speed_(m/s)']

MAX_DELTA_T = pd.Timedelta('10 seconds')

RESAMPLE_INTERVAL = '1T' # 1 minute

DEBUG = False

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

    rawIntoDf = {
        'date_time':[],
        'Barometer_(mBar)':[],
        'Air_Temperature_(C)':[],
        'Relative_Humidity_(%)':[],
        'Vector_Wind_Speed_(m/s)':[],
        'Vector_Wind_Direction_(degrees, Relative to Bow)':[],
        'Scalar_Wind_Speed_(m/s)':[],
        'Maximum_Wind_Speed_(m/s)':[],
        'Shortwave_Irradiance_(Wm-2)':[],
        'Longwave_Irradiance_(Wm-2)':[],
        'PIR_Thermopile_Voltage_(mV)':[],
        'PIR_Case_Temperature_(C)':[],
        'PIR_Dome_Temperature_(C)':[]
    }

    csvfile = open(outfile, 'r')
    reader = csv.DictReader( csvfile, RAW_COLUMNS)

    for line in reader:

        try:

            line_date_time = line['date'] + ' ' + line['time']

            line_bar = float(line['Barometer_(mBar)'])
            line_air_temp = float(line['Air_Temperature_(C)'])
            line_humid = float(line['Relative_Humidity_(%)'])
            line_vector_wind_speed = float(line['Vector_Wind_Speed_(m/s)'])
            line_vector_wind_dir = float(line['Vector_Wind_Direction_(degrees, Relative to Bow)'])
            line_scalar_wind_speed = float(line['Scalar_Wind_Speed_(m/s)'])
            line_max_wind_speed = float(line['Maximum_Wind_Speed_(m/s)'])
            line_shortwave_ir = float(line['Shortwave_Irradiance_(Wm-2)'])
            line_longwave_ir = float(line['Longwave_Irradiance_(Wm-2)'])
            line_pir_volts = float(line['PIR_Thermopile_Voltage_(mV)'])
            line_case_temp = float(line['PIR_Case_Temperature_(C)'])
            line_dome_temp = float(line['PIR_Dome_Temperature_(C)'])

        except:

            debugPrint('Parsing error: ',line)
            errors += 1

        else:
            rawIntoDf['date_time'].append(line_date_time)
            rawIntoDf['Barometer_(mBar)'].append(line_bar)
            rawIntoDf['Air_Temperature_(C)'].append(line_air_temp)
            rawIntoDf['Relative_Humidity_(%)'].append(line_humid)
            rawIntoDf['Vector_Wind_Speed_(m/s)'].append(line_vector_wind_speed)
            rawIntoDf['Vector_Wind_Direction_(degrees, Relative to Bow)'].append(line_vector_wind_dir)
            rawIntoDf['Scalar_Wind_Speed_(m/s)'].append(line_scalar_wind_speed)
            rawIntoDf['Maximum_Wind_Speed_(m/s)'].append(line_max_wind_speed)
            rawIntoDf['Shortwave_Irradiance_(Wm-2)'].append(line_shortwave_ir)
            rawIntoDf['Longwave_Irradiance_(Wm-2)'].append(line_longwave_ir)
            rawIntoDf['PIR_Thermopile_Voltage_(mV)'].append(line_pir_volts)
            rawIntoDf['PIR_Case_Temperature_(C)'].append(line_case_temp)
            rawIntoDf['PIR_Dome_Temperature_(C)'].append(line_dome_temp)

    shutil.rmtree(tmpdir)

    if len(rawIntoDf['date_time']) == 0:
        return None

    df_proc = pd.DataFrame(rawIntoDf)

    df_proc['date_time'] = pd.to_datetime(df_proc['date_time'], infer_datetime_format=True)

    df_proc = df_proc.join(df_proc['date_time'].diff().to_frame(name='deltaT'))

    rowValidityStat = {'statName':'Row Validity', 'statType':'rowValidity', 'statData':[len(df_proc), errors]}
    output['stats'].append(rowValidityStat)

    barStat = {'statName': 'Barometer Bounds','statUnit': 'mBar', 'statType':'bounds', 'statData':[round(df_proc['Barometer_(mBar)'].min(),3), round(df_proc['Barometer_(mBar)'].max(),3)]}
    output['stats'].append(barStat)

    tempStat = {'statName': 'Air Temperature Bounds','statUnit': 'C', 'statType':'bounds', 'statData':[round(df_proc['Air_Temperature_(C)'].min(),3), round(df_proc['Air_Temperature_(C)'].max(),3)]}
    output['stats'].append(tempStat)

    humidStat = {'statName': 'Humidity Bounds','statUnit': '%', 'statType':'bounds', 'statData':[round(df_proc['Relative_Humidity_(%)'].min(),3), round(df_proc['Relative_Humidity_(%)'].max(),3)]}
    output['stats'].append(humidStat)

    vectorWindSpeedStat = {'statName': 'Vector Wind Spd Bounds','statUnit': 'm/s', 'statType':'bounds', 'statData':[round(df_proc['Vector_Wind_Speed_(m/s)'].min(),3), round(df_proc['Vector_Wind_Speed_(m/s)'].max(),3)]}
    output['stats'].append(vectorWindSpeedStat)

    vectorWindDirStat = {'statName': 'Vector Wind Dir Bounds','statUnit': 'deg', 'statType':'bounds', 'statData':[round(df_proc['Vector_Wind_Direction_(degrees, Relative to Bow)'].min(),3), round(df_proc['Vector_Wind_Direction_(degrees, Relative to Bow)'].max(),3)]}
    output['stats'].append(vectorWindDirStat)

    vectorWindDirValidityStat = {'statName':'Vector Wind Dir Validity', 'statType':'valueValidity', 'statData':[len(df_proc[(df_proc['Vector_Wind_Direction_(degrees, Relative to Bow)'] >= MIN_DIR) & (df_proc['Vector_Wind_Direction_(degrees, Relative to Bow)'] <= MAX_DIR)]),len(df_proc[(df_proc['Vector_Wind_Direction_(degrees, Relative to Bow)'] < MIN_DIR) & (df_proc['Vector_Wind_Direction_(degrees, Relative to Bow)'] > MAX_DIR)])]}
    output['stats'].append(vectorWindDirValidityStat)

    scalarWindSpeedStat = {'statName': 'Scalar Wind Spd','statUnit': 'm/s', 'statType':'bounds', 'statData':[round(df_proc['Scalar_Wind_Speed_(m/s)'].min(),3), round(df_proc['Scalar_Wind_Speed_(m/s)'].max(),3)]}
    output['stats'].append(scalarWindSpeedStat)

    temporalStat = {'statName': 'Temporal Bounds','statUnit': 'seconds', 'statType':'timeBounds', 'statData':[df_proc.date_time.min().strftime('%s'), df_proc.date_time.max().strftime('%s')]}
    output['stats'].append(temporalStat)

    deltaTStat = {"statName": "Delta-T Bounds","statUnit": "seconds","statType": "bounds","statData": [round(df_proc.deltaT.min().total_seconds(),3), round(df_proc.deltaT.max().total_seconds(),3)]}
    output['stats'].append(deltaTStat)

    deltaTValidityStat = {'statName':'Temporal Validity', 'statType':'valueValidity', 'statData':[len(df_proc[(df_proc['deltaT'] <= MAX_DELTA_T)]),len(df_proc[(df_proc['deltaT'] > MAX_DELTA_T)])]}
    output['stats'].append(deltaTValidityStat)

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

    vectorWindDirQualityTest = {"testName": "Vector Wind Dir", "results": "Passed"}
    if vectorWindDirValidityStat['statData'][1] > 0:
        if vectorWindDirValidityStat['statData'][1]/len(df_proc) > .10:
            vectorWindDirQualityTest['results'] = "Failed"
        else:
            vectorWindDirQualityTest['results'] = "Warning"
    output['qualityTests'].append(vectorWindDirQualityTest)

    df_crop = df_proc[CROP_COLUMNS]

    df_crop = df_crop.set_index('date_time')

    df_crop = df_crop.resample(RESAMPLE_INTERVAL, label='right', closed='right').mean()

    df_crop = df_crop.reset_index()

    decimals = pd.Series([1, 2, 1, 1, 1, 1], index=['Barometer_(mBar)','Air_Temperature_(C)','Relative_Humidity_(%)','Vector_Wind_Speed_(m/s)','Vector_Wind_Direction_(degrees, Relative to Bow)','Scalar_Wind_Speed_(m/s)'])
    df_crop = df_crop.round(decimals)

    visualizerDataObj = {'data':[], 'unit':'', 'label':''}
    visualizerDataObj['data'] = json.loads(df_crop[['date_time','Barometer_(mBar)']].to_json(orient='values'))
    visualizerDataObj['unit'] = 'mBar'
    visualizerDataObj['label'] = 'Barometer'
    output['visualizerData'].append(copy.deepcopy(visualizerDataObj))

    visualizerDataObj['data'] = json.loads(df_crop[['date_time','Air_Temperature_(C)']].to_json(orient='values'))
    visualizerDataObj['unit'] = 'C'
    visualizerDataObj['label'] = 'Temperature'
    output['visualizerData'].append(copy.deepcopy(visualizerDataObj))

    visualizerDataObj['data'] = json.loads(df_crop[['date_time','Relative_Humidity_(%)']].to_json(orient='values'))
    visualizerDataObj['unit'] = '%'
    visualizerDataObj['label'] = 'Humidity'
    output['visualizerData'].append(copy.deepcopy(visualizerDataObj))
    
    visualizerDataObj['data'] = json.loads(df_crop[['date_time','Vector_Wind_Speed_(m/s)']].to_json(orient='values'))
    visualizerDataObj['unit'] = 'm/s'
    visualizerDataObj['label'] = 'Vector Wind Spd'
    output['visualizerData'].append(copy.deepcopy(visualizerDataObj))

    visualizerDataObj['data'] = json.loads(df_crop[['date_time','Vector_Wind_Direction_(degrees, Relative to Bow)']].to_json(orient='values'))
    visualizerDataObj['unit'] = 'deg'
    visualizerDataObj['label'] = 'Vector Wind Dir'
    output['visualizerData'].append(copy.deepcopy(visualizerDataObj))

    visualizerDataObj['data'] = json.loads(df_crop[['date_time','Scalar_Wind_Speed_(m/s)']].to_json(orient='values'))
    visualizerDataObj['unit'] = 'm/s'
    visualizerDataObj['label'] = 'Scalar Wind Spd'
    output['visualizerData'].append(copy.deepcopy(visualizerDataObj))

    return output

# -------------------------------------------------------------------------------------
# Main function of the script should it be run as a stand-alone utility.
# -------------------------------------------------------------------------------------
def main(argv):
    
    parser = argparse.ArgumentParser(description='Parse MET data')
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
        sys.stderr.write('ERROR: File not found\n')
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
