#!/usr/bin/env python3
"""Utilities for determining invalid filenames.
"""
import logging

def is_ascii(test_str):
    """Check if the characters in string s are in ASCII, U+0-U+7F."""
    return len(test_str) == len(test_str.encode())

def bad_filename(filename):
    """Verify the filename contains only valid ASCii characters"""
    try:
        str(filename)
    except Exception as err:
        logging.debug(str(err))
        return True
    return False

def bad_filenames(files):
    """
    Return a list of files that contain non-ASCii chanacters from the
    list of provided filenames
    """

    problem_files = list(filter(bad_filename, files))

    if len(problem_files) > 0:
        logging.debug("Problem Files:")
        logging.debug("\t %s", "\n\t".join(problem_files))

    return problem_files
