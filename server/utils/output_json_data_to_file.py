#!/usr/bin/env python3
"""Utilities for writing JSON-formatted data to file.
"""
import os
import json
import errno
import logging

def output_json_data_to_file(file_path, contents):
    """
    Write contents to the specified file_path.  Assumes contents is a json
    string-able object
    """
    try:
        os.makedirs(os.path.dirname(file_path))
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            logging.error("Unable to create parent directory for data file")
            return {'verdict': False, 'reason': 'Unable to create parent directory(ies) for data file: {}'.format(file_path) }
    except Exception as err:
        raise err

    with open(file_path, 'w') as json_file:
        logging.debug("Saving JSON file: %s", file_path)
        try:
            json.dump(contents, json_file, indent=4)

        except IOError:
            logging.error("Error Saving JSON file: %s", file_path)
            return {'verdict': False, 'reason': 'Unable to create data file: {}'.format(file_path) }

    return {'verdict': True}
