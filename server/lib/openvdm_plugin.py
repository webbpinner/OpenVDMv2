
import os
import json
import logging
import subprocess
import numpy as np
import pandas as pd
from itertools import (takewhile, repeat)

# import numpy as np

# from os.path import dirname, realpath
# sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

def rawincount(filePath):

    try:
        with open(filePath, 'rb') as file:
            bufgen = takewhile(lambda x: x, (file.read(1024*1024) for _ in repeat(None)))

            return sum( buf.count(b'\n') for buf in bufgen )
    
    except Exception as e:
        raise e


def csvCleanup(filePath):

    clean_command = ['csvclean', filePath]
    logging.debug("Clean command: {}".format(' '.join(clean_command)))

    (dirname, basename) = os.path.split(filePath)
    outfile = os.path.join(dirname, os.path.splitext(basename)[0] + '_out.csv')
    errfile = os.path.join(dirname, os.path.splitext(basename)[0] + '_err.csv')

    # logging.debug("Outfile: {}".format(outfile))
    # logging.debug("Errfile: {}".format(errfile))

    proc = subprocess.run(clean_command)

    errors = rawincount(errfile)-1 if os.path.isfile(errfile) else 0

    return (errors, outfile)


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)


class OpenVDMPlugin():
    
    def __init__(self):
        self.plugin_data = {
            'visualizerData': [],
            'qualityTests': [],
            'stats': []
        }


    def get_plugin_data(self):
        return self.plugin_data


    def process_file(self, filePath):
        raise NotImplementedError('process_file must be implemented by subclass')


    def add_visualization_data(self, data):
        self.plugin_data['visualizerData'].append(data)


    def add_quality_test(self, data):
        self.plugin_data['qualityTests'].append(data)


    def add_stat(self, data):
        self.plugin_data['stats'].append(data)


class OpenVDMPluginCSV(OpenVDMPlugin):

    def __init__(self, raw_cols=None, proc_cols=None, crop_cols=None, csvkit=False):
        self.raw_cols = raw_cols or []
        self.proc_cols = proc_cols or []
        self.crop_cols = crop_cols or []
        self.csvkit = csvkit
        super().__init__()


    def set_raw_cols(self, raw_cols):
        self.raw_cols = raw_cols


    def set_proc_cols(self, proc_cols):
        self.proc_cols = proc_cols


    def set_crop_cols(self, crop_cols):
        self.crop_cols = crop_cols


    def resample_data(self, df, resample_interval='1T'):
        # resample data
        resample_df = df.resample(resample_interval, label='right', closed='right').mean()

        # reset index
        return resample_df.reset_index()


    def round_data(self, df, precision={}):

        if bool(precision):
            decimals = pd.Series(precision.values(), index=precision.keys())
            return df.round(decimals)

        return df

