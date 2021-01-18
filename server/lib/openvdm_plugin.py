
import os
import json
import fnmatch
import logging
import subprocess
import numpy as np
import pandas as pd
from datetime import datetime
from itertools import (takewhile, repeat)


STAT_TYPES = [
    'bounds',
    'geoBounds',
    'rowValidity',
    'timeBounds',
    'totalValue',
    'valueValidity'
]

QUALITY_TEST_RESULT_TYPES = [
    'Failed',
    'Warning',
    'Passed'
]

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            return super(NpEncoder, self).default(obj)


class OpenVDMParserQualityTest():
    
    def __init__(self, test_name, test_value):

        if test_value not in QUALITY_TEST_RESULT_TYPES:
            raise ValueError("Invalid test result type, must be one of: {}".format(', '.join(QUALITY_TEST_RESULT_TYPES)))
        
        self.test_data = {
            'testName':test_name,
            'results': test_value
        }


    def get_test_data(self):
        return self.test_data


    def toJSON(self):
        return json.dumps(self.get_test_data(), cls=NpEncoder)


class OpenVDMParserQualityTestFailed(OpenVDMParserQualityTest):
    def __init__(self, test_name):
        super().__init__(test_name=test_name, test_value='Failed')


class OpenVDMParserQualityTestWarning(OpenVDMParserQualityTest):
    def __init__(self, test_name):
        super().__init__(test_name=test_name, test_value='Warning')


class OpenVDMParserQualityTestPassed(OpenVDMParserQualityTest):
    def __init__(self, test_name):
        super().__init__(test_name=test_name, test_value='Passed')


class OpenVDMParserStat():
    
    def __init__(self, stat_name, stat_type, stat_value, stat_uom=''):

        if stat_type not in STAT_TYPES:
            raise ValueError("Invalid stat type, must be one of: {}".format(', '.join(STAT_TYPES)))
        elif stat_type == 'bounds':
            if not isinstance(stat_value, list) or len(stat_value) != 2:
                raise ValueError("bounds stat requires list of length 2")
            else:
                for element in stat_value:
                    if not isinstance(element, float) and not isinstance(element, int):
                        raise ValueError("bounds stat requires list of 2 numbers")
        elif stat_type == 'geoBounds':
            if not isinstance(stat_value, list) or len(stat_value) != 4:
                raise ValueError("geoBounds stat requires list of 4 numbers")
            else:
                for element in stat_value:
                    if not isinstance(element, float) and not isinstance(element, int):
                        raise ValueError("geoBounds stat requires list of 4 numbers")
        elif stat_type == 'rowValidity':
            if not isinstance(stat_value, list) or len(stat_value) != 2:
                raise ValueError("rowValidity stat requires list 2 integers")
            else:
                for element in stat_value:
                    if not isinstance(element, int):
                        raise ValueError("rowValidity stat requires list 2 integers")
        elif stat_type == 'timeBounds':
            if not isinstance(stat_value, list) or len(stat_value) != 2:
                raise ValueError("timeBounds stat requires list 2 datetime")
            else:
                for element in stat_value:
                    if not isinstance(element, datetime):
                        logging.debug(type(element))
                        raise ValueError("timeBounds stat requires list 2 datetime objects")
        elif stat_type == 'totalValue':
            if not isinstance(stat_value, list) or len(stat_value) != 1:
                raise ValueError("totalValue stat requires list 1 number")
            else:
                for element in stat_value:
                    if not isinstance(element, float) and not isinstance(element, int):
                        raise ValueError("totalValue stat requires list 1 number")
        elif stat_type == 'valueValidity':
            if not isinstance(stat_value, list) or len(stat_value) != 2:
                raise ValueError("valueValidity stat requires list 2 numbers")
            else:
                for element in stat_value:
                    if not isinstance(element, float) and not isinstance(element, int):
                        raise ValueError("valueValidity stat requires list 2 numbers")
        
        self.stat_data = {
            'statName': stat_name,
            'statType': stat_type,
            'statUnit': stat_uom,      
            'statValue': stat_value
        }


    def get_stat_data(self):
        return self.stat_data


    def toJSON(self):
        return json.dumps(self.get_stat_data(), cls=NpEncoder)


class OpenVDMParserBoundsStat(OpenVDMParserStat):
    def __init__(self, stat_value, stat_name, stat_uom=''):
        super().__init__(stat_name=stat_name, stat_type="bounds", stat_value=stat_value, stat_uom=stat_uom)


class OpenVDMParserGeoBoundsStat(OpenVDMParserStat):
    def __init__(self, stat_value, stat_name='Geographic Bounds', stat_uom='ddeg'):
        super().__init__(stat_name=stat_name, stat_type="geoBounds", stat_value=stat_value, stat_uom=stat_uom)


class OpenVDMParserRowValidityStat(OpenVDMParserStat):
    def __init__(self, stat_value):
        super().__init__(stat_name="Row Validity", stat_type="rowValidity", stat_value=stat_value, stat_uom='')


class OpenVDMParserTimeBoundsStat(OpenVDMParserStat):
    def __init__(self, stat_value, stat_name='Temporal Bounds', stat_uom='seconds'):
        super().__init__(stat_name=stat_name, stat_type="timeBounds", stat_value=stat_value, stat_uom=stat_uom)


class OpenVDMParserTotalValueStat(OpenVDMParserStat):
    def __init__(self, stat_value, stat_name, stat_uom=''):
        super().__init__(stat_name=stat_name, stat_type="totalValue", stat_value=stat_value, stat_uom=stat_uom)


class OpenVDMParserValueValidityStat(OpenVDMParserStat):
    def __init__(self, stat_value, stat_name):
        super().__init__(stat_name=stat_name, stat_type="valueValidity", stat_value=stat_value, stat_uom='')


class OpenVDMParser():
    
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


    def add_quality_test_failed(self, name):
        test = OpenVDMParserQualityTestFailed(name)
        self.plugin_data['qualityTests'].append(test.get_test_data())


    def add_quality_test_warning(self, name):
        test = OpenVDMParserQualityTestWarning(name)
        self.plugin_data['qualityTests'].append(test.get_test_data())


    def add_quality_test_passed(self, name):
        test = OpenVDMParserQualityTestPassed(name)
        self.plugin_data['qualityTests'].append(test.get_test_data())


    def add_bounds_stat(self, value, name, uom=''):
        stat = OpenVDMParserBoundsStat(value, name, uom)
        self.plugin_data['stats'].append(stat.get_stat_data())


    def add_geobounds_stat(self, value, name='Geographic Bounds', uom='ddeg'):
        stat = OpenVDMParserGeoBoundsStat(value, name, uom)
        self.plugin_data['stats'].append(stat.get_stat_data())


    def add_row_validity_stat(self, value):
        stat = OpenVDMParserRowValidityStat(value)
        self.plugin_data['stats'].append(stat.get_stat_data())


    def add_time_bounds_stat(self, value, name='Temporal Bounds', uom='seconds'):
        stat = OpenVDMParserTimeBoundsStat(value, name, uom)
        self.plugin_data['stats'].append(stat.get_stat_data())


    def add_total_value_stat(self, value, name, uom=''):
        stat = OpenVDMParserTotalValueStat(value, name, uom)
        self.plugin_data['stats'].append(stat.get_stat_data())


    def add_value_validity_stat(self, value, name):
        stat = OpenVDMParserValueValidityStat(value, name)
        self.plugin_data['stats'].append(stat.get_stat_data())


class OpenVDMCSVParser(OpenVDMParser):

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


class OpenVDMPlugin():
    
    def __init__(self, file_type_filters):
        self.file_type_filters = file_type_filters


    def get_data_type(self, filePath):

        file_type_filter = list(filter(lambda file_type_filter: fnmatch.fnmatch(filePath, file_type_filter['regex']), self.file_type_filters))

        if len(file_type_filter) == 0:
            return None

        return file_type_filter[0]['data_type']


    def get_parser(self, filePath):
        raise NotImplementedError('process_file must be implemented by subclass')


    def get_json_str(self, filePath):

        parser = self.get_parser(filePath)
        
        if parser is None:
            return None

        parser.process_file(filePath)

        return parser.toJSON()


