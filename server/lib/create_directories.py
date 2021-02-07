#!/usr/bin/env python3
"""Utilities for determining invalid filenames.
"""
import os
import json
import errno
import logging

def create_directories(directory_list):
    """
    Create the directories defined in the directory_list
    """
    reasons = []
    for directory in directory_list:
        try:
            os.makedirs(directory)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                logging.error("Unable to create directory: %s", directory)
                reasons.append("Unable to create directory: %s", directory)

    if len(reasons) > 0:
        return {'verdict': False, 'reason': '\n'.join(reasons)}

    return {'verdict': True}

def create_parent_directories(file_list):
    """
    Create the parent directories for the directories defined in the
    directory_list
    """
    dirs = list({os.path.dirname(filename) for filename in file_list})

    logging.debug("Directories to create: %s", json.dumps(dirs))
    return create_directories(dirs)
