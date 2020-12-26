#!/usr/bin/env python3
"""Utilities for setting file permissions/ownership.
"""
import os
import grp
import pwd
import logging

def set_ownerGroupPermissions(user, path):

    reasons = []

    uid = pwd.getpwnam(user).pw_uid
    gid = grp.getgrnam(user).gr_gid
    # Set the file permission and ownership for the current directory

    logging.debug("Setting ownership/permissions for {}".format(path))
    if os.path.isfile(path):
        try:
            os.chown(path, uid, gid)
            os.chmod(path, 0o644)
        except OSError:
            logging.error("Unable to set ownership/permissions for {}".format(path))
            reasons.append("Unable to set ownership/permissions for {}".format(path))

    else: #directory
        try:
            os.chown(path, uid, gid)
            os.chmod(path, 0o755)
        except OSError:
            logging.error("Unable to set ownership/permissions for {}".format(path))
            reasons.append("Unable to set ownership/permissions for {}".format(path))

        for root, dirs, files in os.walk(path):
            for file in files:
                fname = os.path.join(root, file)
                logging.debug("Setting ownership/permissions for {}".format(file))
                try:
                    os.chown(fname, uid, gid)
                    os.chmod(fname, 0o644)
                except OSError:
                    logging.error("Unable to set ownership/permissions for {}".format(file))
                    reasons.append("Unable to set ownership/permissions for {}".format(file))

            for directory in dirs:
                dname = os.path.join(root, directory)
                logging.debug("Setting ownership/permissions for {}".format(directory))
                try:
                    os.chown(dname, uid, gid)
                    os.chmod(dname, 0o755)
                except OSError:
                    logging.error("Unable to set ownership/permissions for {}".format(directory))
                    reasons.append("Unable to set ownership/permissions for {}".format(directory))

    if len(reasons) > 0:
        return {'verdict': False, 'reason': '\n'.join(reasons)}

    return {'verdict': True}
