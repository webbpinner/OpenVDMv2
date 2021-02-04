#!/usr/bin/env python3
"""Utilities for reading/processing JSON data.
"""
import logging

try:
    from yaml import load, YAMLError, FullLoader
except ModuleNotFoundError:
    pass


def parse_yaml(source):
    """Read the passed text/stream assuming it's YAML or JSON (a subset of
    YAML) and try to parse it into a Python dict.
    """
    try:
        return load(source, Loader=FullLoader)
    except NameError as name_error:
        raise ImportError('No YAML module available. Please ensure that '
                          'PyYAML or equivalent is installed (e.g. via '
                          '"pip3 install PyYAML"') from name_error
    except YAMLError as err:
        logging.error("Unable to parse configuration file: %s", source)
        raise err
    except Exception as err: # handle other exceptions such as attribute errors
        raise err


def read_config(filename):
    """Read the passed text/stream assuming it's a valid OpenVDM configuration
    file
    """
    try:
        with open(filename, 'r') as file:
            return parse_yaml(file)
    except IOError as err:
        logging.error("Unable to open configuration file: %s", filename)
        raise err
    except Exception as err: # handle other exceptions such as attribute errors
        raise err
