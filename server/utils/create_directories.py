#!/usr/bin/env python3
"""Utilities for determining invalid filenames.
"""
import os
import logging

def create_directories(directoryList):

    reasons = []
    for directory in directoryList:
        try:
            os.makedirs(directory)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                logging.error("Unable to create directory: {}".format(directory))
                reasons.append("Unable to create directory: {}".format(directory))
                
    if len(reasons) > 0:
        return {'verdict': False, 'reason': '\n'.join(reasons)}

    return {'verdict': True}

def create_parent_directories(fileList):
    dirs = list(set([os.path.dirname(filename) for filename in fileList]))

    logging.debug("Directories to create: {}".format(json.dumps(dirs)))
    return create_directories(dirs)
