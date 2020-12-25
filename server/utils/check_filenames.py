#!/usr/bin/env python3
"""Utilities for determining invalid filenames.
"""

def bad_filename(filename):
	try:
	    str(file)
	except:
	    return True
	return False

def bad_filenames(files):

    problemFiles = list(filter(bad_filename, files))

    if len(problemFiles) > 0:
        logging.debug("Problem Files:")
        logging.debug("\t" + "\n\t".join(problemFiles))

    return problemFiles
