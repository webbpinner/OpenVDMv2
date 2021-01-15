
import os
import json
import logging
import subprocess
import numpy as np
import pandas as pd
from itertools import (takewhile, repeat)


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

    def __init__(self, start_dt=None, stop_dt=None):
        self.start_dt = start_dt
        self.stop_dt = stop_dt
        self.tmpdir = None
        super().__init__()


    def crop_data(self, df):
        try:
            if self.start_dt is not None:
                logging.debug("  start_dt: {}".format(self.start_dt))
                df = df[(df['date_time'] >= self.start_dt)]

            if self.stop_dt is not None:
                logging.debug("  stop_dt: {}".format(self.stop_dt))
                df = df[(df['date_time'] <= self.stop_dt)]
        except Exception as err:
            logging.error("Could not crop data")
            logging.error(str(err))
            raise err

        return df


    def resample_data(self, df, resample_interval='1T'):
        # resample data
        try:
            resample_df = df.resample(resample_interval, label='right', closed='right').mean()
        except Exception as err:
            logging.error("Could not resample data")
            logging.error(str(err))
            raise err

        # reset index
        return resample_df.reset_index()


    def round_data(self, df, precision={}):

        if bool(precision):
            try:
                decimals = pd.Series(precision.values(), index=precision.keys())
                return df.round(decimals)
            except Exception as err:
                logging.error("Could not round data")
                logging.error(str(err))
                raise err
        return df

    def toJSON(self):
        return json.dumps(self.get_plugin_data(), cls=NpEncoder)

