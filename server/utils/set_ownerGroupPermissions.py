#!/usr/bin/env python3
"""Utilities for setting file permissions/ownership.
"""
from os import chown, chmod, walk
from os.path import isfile, join, basename
from grp import getgrnam
from pwd import getpwnam
import logging

def set_ownerGroupPermissions(user, path):

    reasons = []

    basenamePath = basename(path)
    uid = getpwnam(user).pw_uid
    gid = getgrnam(user).gr_gid
    # Set the file permission and ownership for the current directory

    logging.debug("Setting ownership/permissions for {}".format(basenamePath))
    if isfile(path):
        try:
            chown(path, uid, gid)
            chmod(path, 0o644)
        except OSError:
            logging.error("Unable to set ownership/permissions for {}".format(basenamePath))
            reasons.append("Unable to set ownership/permissions for {}".format(basenamePath))

    else: #directory
        try:
            chown(path, uid, gid)
            chmod(path, 0o755)
        except OSError:
            logging.error("Unable to set ownership/permissions for {}".format(basenamePath))
            reasons.append("Unable to set ownership/permissions for {}".format(basenamePath))

        for root, dirs, files in walk(path):
            for file in files:
                fname = join(root, file)
                logging.debug("Setting ownership/permissions for {}".format(join(basenamePath,file)))
                try:
                    chown(fname, uid, gid)
                    chmod(fname, 0o644)
                except OSError:
                    logging.error("Unable to set ownership/permissions for {}".format(join(basenamePath,file)))
                    reasons.append("Unable to set ownership/permissions for {}".format(join(basenamePath,file)))

            for directory in dirs:
                dname = join(root, directory)
                logging.debug("Setting ownership/permissions for {}".format(join(basenamePath,directory)))
                try:
                    chown(dname, uid, gid)
                    chmod(dname, 0o755)
                except OSError:
                    logging.error("Unable to set ownership/permissions for {}".format(join(basenamePath,directory)))
                    reasons.append("Unable to set ownership/permissions for {}".format(join(basenamePath,directory)))

    if len(reasons) > 0:
        return {'verdict': False, 'reason': '\n'.join(reasons)}

    return {'verdict': True}
