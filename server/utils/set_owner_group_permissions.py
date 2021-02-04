#!/usr/bin/env python3
"""Utilities for setting file permissions/ownership.
"""
from os import chown, chmod, walk
from os.path import isfile, join, basename, dirname
from grp import getgrnam
from pwd import getpwnam
import logging

def remove_prefix(text, prefix):
    """
    Remove the specified prefix from the provided text if it exists
    """
    return text[text.startswith(prefix) and len(prefix):]

def set_owner_group_permissions(user, path):
    """
    Recursively set the ownership and permissions for the files and sub-
    directories for the given path.
    """
    reasons = []

    basename_path = basename(path)
    root_dirname = dirname(path)
    uid = getpwnam(user).pw_uid
    gid = getgrnam(user).gr_gid
    # Set the file permission and ownership for the current directory

    logging.debug("Setting ownership/permissions for %s", basename_path)
    if isfile(path):
        try:
            chown(path, uid, gid)
            chmod(path, 0o644)
        except OSError:
            logging.error("Unable to set ownership/permissions for /%s", basename_path)
            reasons.append("Unable to set ownership/permissions for /{}".format(basename_path))

    else: #directory
        try:
            chown(path, uid, gid)
            chmod(path, 0o755)
        except OSError:
            logging.error("Unable to set ownership/permissions for /%s", basename_path)
            reasons.append("Unable to set ownership/permissions for /{}".format(basename_path))

        for root, dirs, files in walk(path):
            for file in files:
                fname = join(root, file)
                logging.debug("Setting ownership/permissions for %s", remove_prefix(join(root,file), root_dirname))
                try:
                    chown(fname, uid, gid)
                    chmod(fname, 0o644)
                except OSError:
                    logging.error("Unable to set ownership/permissions for %s", remove_prefix(join(root,file), root_dirname))
                    reasons.append("Unable to set ownership/permissions for {}".format(remove_prefix(join(root,file), root_dirname)))

            for directory in dirs:
                dname = join(root, directory)
                logging.debug("Setting ownership/permissions for %s", remove_prefix(join(root,directory),root_dirname))
                try:
                    chown(dname, uid, gid)
                    chmod(dname, 0o755)
                except OSError:
                    logging.error("Unable to set ownership/permissions for %s", remove_prefix(join(root,directory), root_dirname))
                    reasons.append("Unable to set ownership/permissions for {}".format(remove_prefix(join(root,directory), root_dirname)))

    if len(reasons) > 0:
        return {'verdict': False, 'reason': '\n'.join(reasons)}

    return {'verdict': True}
