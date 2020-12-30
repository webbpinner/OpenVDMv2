#!/usr/bin/env python3
"""Utilities for determining invalid filenames.
"""

import sys
import logging

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


def build_commands(gearman_worker, commandList):

    for command in commandList:
        logging.debug("Raw Command: {}".format(json.dumps(command)))
        command['command'] = [arg.replace('{cruiseID}', gearman_worker.cruiseID) for arg in command['command']] if gearman_worker.cruiseID else command['command']
        command['command'] = [arg.replace('{loweringID}', gearman_worker.loweringID) for arg in command['command']] if gearman_worker.loweringID else command['command']
        command['command'] = [arg.replace('{collectionSystemTransferID}', gearman_worker.collectionSystemTransfer['collectionSystemTransferID']) for arg in command['command']] if gearman_worker.collectionSystemTransfer else command['command']
        command['command'] = [arg.replace('{collectionSystemTransferName}', gearman_worker.collectionSystemTransfer['name']) for arg in command['command']] if gearman_worker.collectionSystemTransfer else command['command']
        command['command'] = [arg.replace('{newFiles}', json.dumps(gearman_worker.files['new'])) for arg in command['command']] if gearman_worker.files else command['command']
        command['command'] = [arg.replace('{updatedFiles}', json.dumps(gearman_worker.files['updated']) ) for arg in command['command']] if gearman_worker.files else command['command']
                
        logging.debug("Processed Command: {}".format(json.dumps(commandList)))

    return commandList


def get_post_hook_commands(gearman_worker, hook_name):

    try:
        openvdmConfig = read_config(DEFAULT_CONFIG_FILE)

        if hook_name == POST_COLLECTION_SYSTEM_TRANSFER_HOOK_NAME:
            commandsFromFile = openvdmConfig['postHookCommands']['postCollectionSystemTransfer']
            commandsFromFile = list(filter(lambda collectionSystem: collectionSystem['collectionSystemTransferName'] == gearman_worker.collectionSystemTransfer['name'], commandsFromFile))
            commandsFromFile = returnCommandList[0]['commandList'] if len(returnCommandList) > 0 and 'commandList' in commandsFromFile[0] else []
        elif hook_name == POST_DATA_DASHBOARD_HOOK_NAME:
            commandsFromFile = openvdmConfig['postHookCommands']['postDataDashboard']
            commandsFromFile = list(filter(lambda collectionSystem: collectionSystem['collectionSystemTransferName'] == gearman_worker.collectionSystemTransfer['name'], commandsFromFile))
            commandsFromFile = returnCommandList[0]['commandList'] if len(returnCommandList) > 0 and 'commandList' in commandsFromFile[0] else []
        elif hook_name == POST_SETUP_NEW_CRUISE_HOOK_NAME:
            commandsFromFile = openvdmConfig['postHookCommands']['postSetupNewCruise']['commandList']
        elif hook_name == POST_SETUP_NEW_LOWERING_HOOK_NAME:
            commandsFromFile = openvdmConfig['postHookCommands']['postSetupNewLowering']['commandList']
        elif hook_name == POST_FINALIZE_CURRENT_CRUISE_HOOK_NAME:
            commandsFromFile = openvdmConfig['postHookCommands']['postFinalizeCurrentCruise']['commandList']
        elif hook_name == POST_FINALIZE_CURRENT_LOWERING_HOOK_NAME:
            commandsFromFile = openvdmConfig['postHookCommands']['postFinalizeCurrentLowering']['commandList']
        else:
            logging.warning("Invalid hook name: '{}' specified".format(hook_name))

    except Exception as err:
        logging.error(str(err))
        return {"verdict": False, "reason": "Could not process command file: " + DEFAULT_CONFIG_FILE, "commandList": []}
    
    returnCommandList = build_commands(gearman_worker, commandsFromFile)

    return {"verdict": True, "commandList": returnCommandList}


def run_commands(commands):    

    reasons = []

    for command in commands: 
        try:
            logging.info("Executing: {}".format(' '.join(command['command'])))
            proc = subprocess.run(command['command'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if len(proc.stdout) > 0:
                logging.debug("stdout: {}".format(proc.stdout))
                
            if len(proc.stderr) > 0:
                logging.debug("stderr: {}".format(proc.stderr))

        except:
            logging.error("Error executing the {} command: ()".format(command['name'], ' '.join(command['command'])))
            reasons.append("Error executing postCollectionSystemTransfer script: " + command['name'])

    if len(reasons) > 0:
        return {"verdict": False, "reason": reasons.join("\n")}

    return {"verdict": True}
