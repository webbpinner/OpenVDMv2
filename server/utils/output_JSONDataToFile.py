#!/usr/bin/env python3
"""Utilities for writing JSON-formatted data to file.
"""

def output_JSONDataToFile(filePath, contents):
    
    try:
        os.makedirs(os.path.dirname(filePath))
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            logging.error("Unable to create parent directory for data file")
            return {'verdict': False, 'reason': 'Unable to create parent directory(ies) for data file: {}'.format(filePath) }
    except Exception as e:
        raise e
    
    with open(filePath, 'w') as JSONFile:
        logging.debug("Saving JSON file: {}".format(filePath))
        try:
            json.dump(contents, JSONFile, indent=4)

        except IOError:
            logging.error("Error Saving JSON file: {}".format(filePath))
            return {'verdict': False, 'reason': 'Unable to create data file: {}'.format(filePath) }

    return {'verdict': True}