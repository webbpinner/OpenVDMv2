# =================================================================================== #
#
#         FILE:  vtg_parser.py
#
#        USAGE:  vtg_parser.py [-h] <dataFile>
#
#  DESCRIPTION:  Parse the supplied NMEA-formtted VTG file (w/ SCS formatted timestamp)
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

RAW_COLUMNS = ['date','time','hdr','cog_t','T','cog_m','M','sog_kts','N','sog_kph','K','checksum']
PROC_COLUMNS = ['date_time','cog_t','cog_m','sog_kts','sog_kph']
CROP_COLUMNS = ['date_time','cog_t','cog_m','sog_kts','sog_kph']

MIN_COG = 0
MAX_COG = 360

MAX_SOG_KTS = 25
MAX_SOG_KPH = MAX_SOG_KTS * 1.852

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

	rawIntoDf = {'date_time':[],'cog_t':[],'cog_m':[],'sog_kts':[],'sog_kph':[]}

	csvfile = open(outfile, 'r')
	reader = csv.DictReader( csvfile, RAW_COLUMNS)

	for line in reader:
		
		try:

			line_date_time = line['date'] + ' ' + line['time']

			line_cog_t = float(line['cog_t'])
			line_cog_m = float(line['cog_m'])
			line_sog_kts = float(line['sog_kts'])
			line_sog_kph = float(line['sog_kph'])

		except:

			debugPrint('Parsing error: ',line)
			errors += 1

		else:
			rawIntoDf['date_time'].append(line_date_time)
			rawIntoDf['cog_t'].append(line_cog_t)
			rawIntoDf['cog_m'].append(line_cog_m)
			rawIntoDf['sog_kts'].append(line_sog_kts)
			rawIntoDf['sog_kph'].append(line_sog_kph)

	shutil.rmtree(tmpdir)

	if len(rawIntoDf['date_time']) == 0:
		return None

	df_proc = pd.DataFrame(rawIntoDf)

	df_proc['date_time'] = pd.to_datetime(df_proc['date_time'], infer_datetime_format=True)

	df_proc = df_proc.join(df_proc['date_time'].diff().to_frame(name='deltaT'))

	rowValidityStat = {'statName':'Row Validity', 'statType':'rowValidity', 'statData':[len(df_proc), errors]}
	output['stats'].append(rowValidityStat)

	cog_tStat = {'statName': 'COG True Bounds','statUnit': 'deg', 'statType':'bounds', 'statData':[round(df_proc['cog_t'].min(),3), round(df_proc['cog_t'].max(),3)]}
	output['stats'].append(cog_tStat)

	cog_tValidityStat = {'statName':'COG True Validity', 'statType':'valueValidity', 'statData':[len(df_proc[(df_proc['cog_t'] >= MIN_COG) & (df_proc['cog_t'] <= MAX_COG)]),len(df_proc[(df_proc['cog_t'] < MIN_COG) & (df_proc['cog_t'] > MAX_COG)])]}
	output['stats'].append(cog_tValidityStat)

	cog_mStat = {'statName': 'COG Mag Bounds','statUnit': 'deg', 'statType':'bounds', 'statData':[round(df_proc['cog_m'].min(),3), round(df_proc['cog_m'].max(),3)]}
	output['stats'].append(cog_mStat)

	cog_mValidityStat = {'statName':'COG Mag Validity', 'statType':'valueValidity', 'statData':[len(df_proc[(df_proc['cog_m'] >= MIN_COG) & (df_proc['cog_m'] <= MAX_COG)]),len(df_proc[(df_proc['cog_m'] < MIN_COG) & (df_proc['cog_m'] > MAX_COG)])]}
	output['stats'].append(cog_mValidityStat)

	sog_ktsStat = {'statName': 'SOG Knots Bounds','statUnit': 'deg', 'statType':'bounds', 'statData':[round(df_proc['sog_kts'].min(),3), round(df_proc['sog_kts'].max(),3)]}
	output['stats'].append(sog_ktsStat)

	sog_ktsValidityStat = {'statName':'COG Mag Validity', 'statType':'valueValidity', 'statData':[len(df_proc[(df_proc['sog_kts'] <= MAX_SOG_KTS)]),len(df_proc[(df_proc['sog_kts'] > MAX_SOG_KTS)])]}
	output['stats'].append(sog_ktsValidityStat)

	sog_kphStat = {'statName': 'SOG Knots Bounds','statUnit': 'deg', 'statType':'bounds', 'statData':[round(df_proc['sog_kph'].min(),3), round(df_proc['sog_kph'].max(),3)]}
	output['stats'].append(sog_kphStat)

	sog_kphValidityStat = {'statName':'COG Mag Validity', 'statType':'valueValidity', 'statData':[len(df_proc[(df_proc['sog_kph'] <= MAX_SOG_KPH)]),len(df_proc[(df_proc['sog_kph'] > MAX_SOG_KPH)])]}
	output['stats'].append(sog_kphValidityStat)

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

	cog_tQualityTest = {"testName": "COG, True", "results": "Passed"}
	if cog_tValidityStat['statData'][1] > 0:
		if cog_tValidityStat['statData'][1]/len(df_proc) > .10:
			cog_tQualityTest['results'] = "Failed"
		else:
			cog_tQualityTest['results'] = "Warning"
	output['qualityTests'].append(cog_tQualityTest)

	cog_mQualityTest = {"testName": "COG ,Magnetic", "results": "Passed"}
	if cog_mValidityStat['statData'][1] > 0:
		if cog_mValidityStat['statData'][1]/len(df_proc) > .10:
			cog_mQualityTest['results'] = "Failed"
		else:
			cog_mQualityTest['results'] = "Warning"
	output['qualityTests'].append(cog_mQualityTest)

	sog_ktsQualityTest = {"testName": "SOG, Knots", "results": "Passed"}
	if sog_ktsValidityStat['statData'][1] > 0:
		if sog_ktsValidityStat['statData'][1]/len(df_proc) > .10:
			sog_ktsQualityTest['results'] = "Failed"
		else:
			sog_ktsQualityTest['results'] = "Warning"
	output['qualityTests'].append(sog_ktsQualityTest)

	sog_kphQualityTest = {"testName": "SOG, kph", "results": "Passed"}
	if sog_kphValidityStat['statData'][1] > 0:
		if sog_kphValidityStat['statData'][1]/len(df_proc) > .10:
			sog_kphQualityTest['results'] = "Failed"
		else:
			sog_kphQualityTest['results'] = "Warning"
	output['qualityTests'].append(sog_kphQualityTest)

	df_crop = df_proc[CROP_COLUMNS]

	df_crop = df_crop.set_index('date_time')

	df_crop = df_crop.resample(RESAMPLE_INTERVAL, label='right', closed='right').mean()

	df_crop = df_crop.reset_index()

	decimals = pd.Series([3, 3, 3, 3], index=['cog_t','cog_m', 'sog_kts', 'sog_kph'])
	df_crop = df_crop.round(decimals)

	visualizerDataObj = {'data':[], 'unit':'', 'label':''}
	visualizerDataObj['data'] = json.loads(df_crop[['date_time','cog_t']].to_json(orient='values'))
	visualizerDataObj['unit'] = 'deg'
	visualizerDataObj['label'] = 'COG, True'
	output['visualizerData'].append(copy.deepcopy(visualizerDataObj))

	visualizerDataObj['data'] = json.loads(df_crop[['date_time','cog_m']].to_json(orient='values'))
	visualizerDataObj['unit'] = 'deg'
	visualizerDataObj['label'] = 'COG, Magnetic'
	output['visualizerData'].append(copy.deepcopy(visualizerDataObj))
	
	visualizerDataObj['data'] = json.loads(df_crop[['date_time','sog_kts']].to_json(orient='values'))
	visualizerDataObj['unit'] = 'kts'
	visualizerDataObj['label'] = 'SOG, kts'
	output['visualizerData'].append(copy.deepcopy(visualizerDataObj))

	visualizerDataObj['data'] = json.loads(df_crop[['date_time','sog_kph']].to_json(orient='values'))
	visualizerDataObj['unit'] = 'kph'
	visualizerDataObj['label'] = 'SOG, kph'
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
