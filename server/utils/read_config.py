#!/usr/bin/env python3
"""Utilities for reading/processing JSON data.
"""
import logging

try:
    from yaml import load, YAMLError, FullLoader
except ModuleNotFoundError:
    pass


def parse(source):
    """Read the passed text/stream assuming it's YAML or JSON (a subset of
    YAML) and try to parse it into a Python dict.
    """
    try:
        return load(source, Loader=FullLoader)
    except NameError:
        raise ImportError('No YAML module available. Please ensure that '
                          'PyYAML or equivalent is installed (e.g. via '
                          '"pip3 install PyYAML"')
    except YAMLError as e:
        logging.error("Unable to parse configuration file: {}".format(source))
        raise e
    except Exception as e: #handle other exceptions such as attribute errors
        raise e


def read_config(filename):

    try:
        with open(filename, 'r') as file:
            return parse(file)
    except IOError as e:
        logging.error("Unable to open configuration file: {}".format(filename))
        raise e
    except Exception as e: #handle other exceptions such as attribute errors
        raise e
