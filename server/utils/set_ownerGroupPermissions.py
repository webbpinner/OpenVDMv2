#!/usr/bin/env python3
"""Utilities for setting file permissions/ownership.
"""
from os import chown, chmod, walk
from os.path import isfile, join, basename, dirname
from grp import getgrnam
from pwd import getpwnam
import logging

def set_ownerGroupPermissions(user, path):

    reasons = []

    basenamePath = basename(path)
    rootDirname = dirname(path)
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
                logging.debug("Setting ownership/permissions for {}".format(join(root,file).lstrip(rootDirname)))
                try:
                    chown(fname, uid, gid)
                    chmod(fname, 0o644)
                except OSError:
                    logging.error("Unable to set ownership/permissions for {}".format(join(root,file).lstrip(rootDirname)))
                    reasons.append("Unable to set ownership/permissions for {}".format(join(root,file).lstrip(rootDirname)))

            for directory in dirs:
                dname = join(root, directory)
                logging.debug("Setting ownership/permissions for {}".format(join(root,directory).lstrip(rootDirname)))
                try:
                    chown(dname, uid, gid)
                    chmod(dname, 0o755)
                except OSError:
                    logging.error("Unable to set ownership/permissions for {}".format(join(root,directory).lstrip(rootDirname)))
                    reasons.append("Unable to set ownership/permissions for {}".format(join(root,directory).lstrip(rootDirname)))

    if len(reasons) > 0:
        return {'verdict': False, 'reason': '\n'.join(reasons)}

    return {'verdict': True}
