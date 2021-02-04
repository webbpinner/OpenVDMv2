#!/usr/bin/env python3
"""Utilities for determining invalid filenames.
"""

import sys
import json
import logging
import subprocess

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))
from server.utils.read_config import read_config
from server.lib.openvdm import DEFAULT_CONFIG_FILE

POST_COLLECTION_SYSTEM_TRANSFER_HOOK_NAME = "postCollectionSystemTransfer"
POST_DATA_DASHBOARD_HOOK_NAME = "postDataDashboard"
POST_SETUP_NEW_CRUISE_HOOK_NAME = "postSetupNewCruise"
POST_SETUP_NEW_LOWERING_HOOK_NAME = "postSetupNewLowering"
POST_FINALIZE_CURRENT_CRUISE_HOOK_NAME = "postFinalizeCurrentCruise"
POST_FINALIZE_CURRENT_LOWERING_HOOK_NAME = "postFinalizeCurrentLowering"


def build_commands(gearman_worker, command_list):
    """
    Process the provided command_list to replace any wild-card strings
    """
    for command in command_list:
        logging.debug("Raw Command: %s", json.dumps(command))
        command['command'] = [arg.replace('{cruiseID}', gearman_worker.cruise_id) for arg in command['command']] if gearman_worker.cruise_id else command['command']
        command['command'] = [arg.replace('{loweringID}', gearman_worker.lowering_id) for arg in command['command']] if gearman_worker.lowering_id else command['command']
        command['command'] = [arg.replace('{collectionSystemTransferID}', gearman_worker.collection_system_transfer['collectionSystemTransferID']) for arg in command['command']] if gearman_worker.collection_system_transfer else command['command']
        command['command'] = [arg.replace('{collectionSystemTransferName}', gearman_worker.collection_system_transfer['name']) for arg in command['command']] if gearman_worker.collection_system_transfer else command['command']
        command['command'] = [arg.replace('{newFiles}', json.dumps(gearman_worker.files['new'])) for arg in command['command']] if gearman_worker.files else command['command']
        command['command'] = [arg.replace('{updatedFiles}', json.dumps(gearman_worker.files['updated']) ) for arg in command['command']] if gearman_worker.files else command['command']

    logging.debug("Processed Command: %s", json.dumps(command_list))

    return command_list


def get_post_hook_commands(gearman_worker, hook_name):
    """
    Retrieve list of commands to for the specified hook_name
    """

    try:
        openvdm_config = read_config(DEFAULT_CONFIG_FILE)
        #logging.debug("openvdm_config: %s", openvdm_config)

        if hook_name == POST_COLLECTION_SYSTEM_TRANSFER_HOOK_NAME:
            commands_from_file = openvdm_config['postHookCommands']['postCollectionSystemTransfer'] if openvdm_config['postHookCommands']['postCollectionSystemTransfer'] is not None else []
            commands_from_file = list(filter(lambda collectionSystem: collectionSystem['collectionSystemTransferName'] == gearman_worker.collection_system_transfer['name'], commands_from_file))
            commands_from_file = commands_from_file[0]['commandList'] if len(commands_from_file) > 0 and 'commandList' in commands_from_file[0] else []
        elif hook_name == POST_DATA_DASHBOARD_HOOK_NAME:
            commands_from_file = openvdm_config['postHookCommands']['postDataDashboard'] if openvdm_config['postHookCommands']['postDataDashboard'] is not None else []
            commands_from_file = list(filter(lambda collectionSystem: collectionSystem['collectionSystemTransferName'] == gearman_worker.collection_system_transfer['name'], commands_from_file))
            commands_from_file = commands_from_file[0]['commandList'] if len(commands_from_file) > 0 and 'commandList' in commands_from_file[0] else []
        elif hook_name == POST_SETUP_NEW_CRUISE_HOOK_NAME:
            commands_from_file = openvdm_config['postHookCommands']['postSetupNewCruise']['commandList'] if openvdm_config['postHookCommands']['postSetupNewCruise'] is not None else []
        elif hook_name == POST_SETUP_NEW_LOWERING_HOOK_NAME:
            commands_from_file = openvdm_config['postHookCommands']['postSetupNewLowering']['commandList'] if openvdm_config['postHookCommands']['postSetupNewLowering'] is not None else []
        elif hook_name == POST_FINALIZE_CURRENT_CRUISE_HOOK_NAME:
            commands_from_file = openvdm_config['postHookCommands']['postFinalizeCurrentCruise']['commandList'] if openvdm_config['postHookCommands']['postFinalizeCurrentCruise'] is not None else []
        elif hook_name == POST_FINALIZE_CURRENT_LOWERING_HOOK_NAME:
            commands_from_file = openvdm_config['postHookCommands']['postFinalizeCurrentLowering']['commandList'] if openvdm_config['postHookCommands']['postFinalizeCurrentLowering'] is not None else []
        else:
            logging.warning("Invalid hook name: '%s'", hook_name)
            return {"verdict": False, "reason": "Invalid hook name: {}".format(hook_name), "commandList": None}

    except Exception as err:
        logging.error(str(err))
        return {"verdict": False, "reason": "Could not process command file: " + DEFAULT_CONFIG_FILE, "commandList": None}

    return {"verdict": True, "commandList": build_commands(gearman_worker, commands_from_file)}


def run_commands(command_list):
    """
    Run the commands in the command_list
    """
    reasons = []

    for command in command_list:
        try:
            logging.info("Executing: %s", ' '.join(command['command']))
            proc = subprocess.run(command['command'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

            if len(proc.stdout) > 0:
                logging.debug("stdout: %s", proc.stdout)

            if len(proc.stderr) > 0:
                logging.debug("stderr: %s", proc.stderr)

        except Exception as err:
            logging.error("Error executing the %s command: %s", command['name'], ' '.join(command['command']))
            logging.debug(str(err))
            reasons.append("Error executing the {} command: {}".format(command['name'], ' '.join(command['command'])))

    if len(reasons) > 0:
        return {"verdict": False, "reason": '\n'.join(reasons)}

    return {"verdict": True}
