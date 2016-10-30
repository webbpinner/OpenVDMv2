# =================================================================================== #
#
#         FILE:  twind_parser.py
#
#        USAGE:  twind_parser.py [-h] <dataFile>
#
#  DESCRIPTION:  Parse the supplied CSV-formtted TWIND file (w/ SCS formatted timestamp)
#                and return the json-formatted string used by OpenVDM as part of it's
#                Data dashboard. 
#
#      OPTIONS:  [-h] Return the help message.
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
#                Copyright (C) 2016 OceanDataRat.org
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

#	visualizerDataObj = {'data':[], 'unit':'', 'label':''}
#	statObj = {'statName':'', 'statUnit':'', 'statType':'', 'statData':[]}
#	qualityTestObj = {"testName": "", "results": ""}

RAW_COLUMNS = ['date','time','hdr','Wind_Speed_(m/s)','Wind_Direction_(deg, Relative to Bow)','unknown_01','unknown_02','unknown_03','unknown_04','unknown_05',]
PROC_COLUMNS = ['date_time','Wind_Speed_(m/s)','Wind_Direction_(deg, Relative to Bow)']
#RAW_COLUMNS = ['date','time','hdr','cog_t','T','cog_m','M','sog_kts','N','sog_kph','K','checksum']
#PROC_COLUMNS = ['date_time','cog_t','cog_m','sog_kts','sog_kph']
CROP_COLUMNS = ['date_time','Wind_Speed_(m/s)','Wind_Direction_(deg, Relative to Bow)']
#CROP_COLUMNS = ['date_time','cog_t','cog_m','sog_kts','sog_kph']

MIN_DIR = 0
MAX_DIR = 360

#MAX_SOG_KTS = 25
#MAX_SOG_KPH = MAX_SOG_KTS * 1.852

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
	shutil.copy(filePath, tmpdir)
	(errors, outfile) = csvCleanup(os.path.join(tmpdir, os.path.basename(filePath)))

	debugPrint("Errors:", errors)

	rawIntoDf = {
		'date_time':[],
		'Wind_Speed_(m/s)':[],
		'Wind_Direction_(deg, Relative to Bow)':[]
	}

	csvfile = open(outfile, 'r')
	reader = csv.DictReader( csvfile, RAW_COLUMNS)

	for line in reader:

		try:

			line_date_time = line['date'] + ' ' + line['time']

			line_wind_speed = float(line['Wind_Speed_(m/s)'])
			line_wind_dir = float(line['Wind_Direction_(deg, Relative to Bow)'])

		except:

			debugPrint('Parsing error: ',line)
			errors += 1

		else:
			rawIntoDf['date_time'].append(line_date_time)
			rawIntoDf['Wind_Speed_(m/s)'].append(line_wind_speed)
			rawIntoDf['Wind_Direction_(deg, Relative to Bow)'].append(line_wind_dir)

	shutil.rmtree(tmpdir)

	if len(rawIntoDf['date_time']) == 0:
		errPrint("No Input")
		return None

	df_proc = pd.DataFrame(rawIntoDf)

	df_proc['date_time'] = pd.to_datetime(df_proc['date_time'], infer_datetime_format=True)

	df_proc = df_proc.join(df_proc['date_time'].diff().to_frame(name='deltaT'))

	rowValidityStat = {'statName':'Row Validity', 'statType':'rowValidity', 'statData':[len(df_proc), errors]}
	output['stats'].append(rowValidityStat)

	windSpeedStat = {'statName': 'Wind Spd Bounds','statUnit': 'm/s', 'statType':'bounds', 'statData':[round(df_proc['Wind_Speed_(m/s)'].min(),3), round(df_proc['Wind_Speed_(m/s)'].max(),3)]}
	output['stats'].append(windSpeedStat)

	windDirStat = {'statName': 'Wind Dir Bounds','statUnit': 'deg', 'statType':'bounds', 'statData':[round(df_proc['Wind_Direction_(deg, Relative to Bow)'].min(),3), round(df_proc['Wind_Direction_(deg, Relative to Bow)'].max(),3)]}
	output['stats'].append(windDirStat)

	windDirValidityStat = {'statName':'Wind Dir Validity', 'statType':'valueValidity', 'statData':[len(df_proc[(df_proc['Wind_Direction_(deg, Relative to Bow)'] >= MIN_DIR) & (df_proc['Wind_Direction_(deg, Relative to Bow)'] <= MAX_DIR)]),len(df_proc[(df_proc['Wind_Direction_(deg, Relative to Bow)'] < MIN_DIR) & (df_proc['Wind_Direction_(deg, Relative to Bow)'] > MAX_DIR)])]}
	output['stats'].append(windDirValidityStat)

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

	windDirQualityTest = {"testName": "Wind Dir", "results": "Passed"}
	if windDirValidityStat['statData'][1] > 0:
		if windDirValidityStat['statData'][1]/len(df_proc) > .10:
			windDirQualityTest['results'] = "Failed"
		else:
			windDirQualityTest['results'] = "Warning"
	output['qualityTests'].append(windDirQualityTest)

	df_crop = df_proc[CROP_COLUMNS]

	df_crop = df_crop.set_index('date_time')

	df_crop = df_crop.resample(RESAMPLE_INTERVAL, label='right', closed='right').mean()

	df_crop = df_crop.reset_index()

	decimals = pd.Series([2, 1], index=['Wind_Speed_(m/s)','Wind_Direction_(deg, Relative to Bow)'])
	df_crop = df_crop.round(decimals)
	
	visualizerDataObj = {'data':[], 'unit':'', 'label':''}
	visualizerDataObj['data'] = json.loads(df_crop[['date_time','Wind_Speed_(m/s)']].to_json(orient='values'))
	visualizerDataObj['unit'] = 'm/s'
	visualizerDataObj['label'] = 'Wind Spd'
	output['visualizerData'].append(copy.deepcopy(visualizerDataObj))

	visualizerDataObj['data'] = json.loads(df_crop[['date_time','Wind_Direction_(deg, Relative to Bow)']].to_json(orient='values'))
	visualizerDataObj['unit'] = 'deg'
	visualizerDataObj['label'] = 'Wind Dir, relative to bow'
	output['visualizerData'].append(copy.deepcopy(visualizerDataObj))

	return output

# -------------------------------------------------------------------------------------
# Main function of the script should it be run as a stand-alone utility.
# -------------------------------------------------------------------------------------
def main(argv):
    
    parser = argparse.ArgumentParser(description='Parse NMEA HPR data')
    parser.add_argument('dataFile', metavar='dataFile', help='the raw data file to process')
    parser.add_argument('-d', '--debug', action='store_true', help=' display debug messages')

    args = parser.parse_args()
    if args.debug:
        global DEBUG
        DEBUG = True
        debugPrint("Running in debug mode")

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
