#!/usr/bin/env python3
"""
FILE:  openvdm.py

DESCRIPTION:  OpenVDM python module

     BUGS:
    NOTES:
   AUTHOR:  Webb Pinner
  COMPANY:  Capable Solutions
  VERSION:  2.5
  CREATED:  2016-02-02
 REVISION:  2020-12-21

LICENSE INFO: Open Vessel Data Management v2.5 (OpenVDMv2)
Copyright (C) OceanDataRat.org 2021

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/gpl-3.0.html>.
"""

import sys
import json
import datetime
import logging

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))

import requests

from server.utils import read_config


DEFAULT_CONFIG_FILE = './server/etc/openvdm.yaml'

DEFAULT_CRUISE_CONFIG_FN = 'ovdmConfig.json'

DEFAULT_DATA_DASHBOARD_MANIFEST_FN = 'manifest.json'

DEFAULT_LOWERING_CONFIG_FN = 'loweringConfig.json'

DEFAULT_MD5_SUMMARY_FN = 'MD5_Summary.txt'

DEFAULT_MD5_SUMMARY_MD5_FN = 'MD5_Summary.md5'


class OpenVDM():

    """
    Class is a python wrapper around the OpenVDM API
    """

    def __init__(self, config_file = DEFAULT_CONFIG_FILE):

        self.config = read_config.read_config(config_file)


    def clear_gearman_jobs_from_db(self):
        """
        Clear the current Gearman job request queue.
        """

        url = self.config['siteRoot'] + 'api/gearman/clearAllJobsFromDB'

        try:
            requests.get(url)
        except Exception as err:
            logging.error("Unable to clear Gearman Jobs from OpenVDM API")
            raise err


    def get_plugin_dir(self):
        """
        Return the directory containing the OpenVDM plugins.
        """

        return self.config['dashboardData']['pluginDir']


    def show_only_current_cruise_dir(self):
        """
        Return whether OpenVDM is configured to only show the current cruise data
        directory.
        """

        return self.config['showOnlyCurrentCruiseDir']


    def get_show_lowering_components(self):
        """
        Return whether OpenVDM should show lowering-related components
        """

        url = self.config['siteRoot'] + 'api/warehouse/getShowLoweringComponents'

        try:
            req = requests.get(url)
            return req.text == 'true'
        except Exception as err:
            logging.error("Unable to retrieve 'showLoweringComponents' flag from OpenVDM API")
            raise err


    def get_ovdm_config(self):
        """
        Return the current OpenVDM configuration
        """

        url = self.config['siteRoot'] + 'api/warehouse/getCruiseConfig'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return_obj['configCreatedOn'] = datetime.datetime.utcnow().strftime("%Y/%m/%dT%H:%M:%SZ")
            return return_obj
        except Exception as err:
            logging.error("Unable to retrieve cruise configuration from OpenVDM API")
            raise err


    def get_lowering_config(self):
        """
        Return the configuration for the current lowering
        """

        url = self.config['siteRoot'] + 'api/warehouse/getLoweringConfig'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return_obj['configCreatedOn'] = datetime.datetime.utcnow().strftime("%Y/%m/%dT%H:%M:%SZ")
            return return_obj
        except Exception as err:
            logging.error("Unable to retrieve lowering configuration from OpenVDM API")
            raise err


    def get_plugin_suffix(self):
        """
        Return expecting suffix for OpenVDM plugins
        """

        return self.config['dashboardData']['pluginSuffix']


    def get_gearman_server(self):
        """
        Return the ip/port for the Gearman server
        """

        return self.config['gearmanServer']


    def get_site_root(self):
        """
        Return the site root for the OpenVDM data warehouse
        """

        return self.config['siteRoot']

    def get_md5_filesize_limit(self):
        """
        Return the MD5 filesize limit
        """

        url = self.config['siteRoot'] + 'api/warehouse/getMD5FilesizeLimit'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj['md5FilesizeLimit']
        except Exception as err:
            logging.error("Unable to retrieve MD5 filesize limit from OpenVDM API")
            raise err

    def get_md5_filesize_limit_status(self):
        """
        Return whether the MD5 filesize limit should be applied
        """

        url = self.config['siteRoot'] + 'api/warehouse/getMD5FilesizeLimitStatus'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj['md5FilesizeLimitStatus']
        except Exception as err:
            logging.error("Unable to retrieve MD5 filesize limit status from OpenVDM API")
            raise err


    def get_tasks_for_hook(self, hook_name):
        """
        Return the task associated with the given hook
        """

        try:
            self.config['hooks'][hook_name]
        except KeyError:
            return []
        else:
            return self.config['hooks'][hook_name]

    def get_transfer_interval(self):
        """
        Return the transfer interval
        """

        return self.config['transferInterval']


    def get_cruise_id(self):
        """
        Return the current cruise id
        """

        url = self.config['siteRoot'] + 'api/warehouse/getCruiseID'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj['cruiseID']
        except Exception as err:
            logging.error("Unable to retrieve CruiseID from OpenVDM API")
            raise err

    def get_cruise_size(self):
        """
        Return the filesize for the current cruise
        """

        url = self.config['siteRoot'] + 'api/warehouse/getCruiseSize'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj
        except Exception as err:
            logging.error("Unable to retrieve cruise size from OpenVDM API")
            raise err


    def get_cruise_start_date(self):
        """
        Return the start date for the current criuse
        """

        url = self.config['siteRoot'] + 'api/warehouse/getCruiseStartDate'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj['cruiseStartDate']
        except Exception as err:
            logging.error("Unable to retrieve cruise start date from OpenVDM API")
            raise err


    def get_cruise_end_date(self):
        """
        Return the end date for the current criuse
        """

        url = self.config['siteRoot'] + 'api/warehouse/getCruiseEndDate'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj['cruiseEndDate']
        except Exception as err:
            logging.error("Unable to retrieve cruise end date from OpenVDM API")
            raise err


    def get_cruises(self):
        """
        Return a list of cruises stored on the data warehouse
        """

        url = self.config['siteRoot'] + 'api/warehouse/getCruises'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj
        except Exception as err:
            logging.error("Unable to retrieve cruises from OpenVDM API")
            raise err


    def get_lowering_id(self):
        """
        Return the current lowering id
        """

        url = self.config['siteRoot'] + 'api/warehouse/getLoweringID'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj['loweringID'] if return_obj['loweringID'] != '' else None
        except Exception as err:
            logging.error("Unable to retrieve LoweringID from OpenVDM API")
            raise err


    def get_lowering_size(self):
        """
        Return the size of the current lowering
        """

        url = self.config['siteRoot'] + 'api/warehouse/getLoweringSize'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj
        except Exception as err:
            logging.error("Unable to retrieve lowering size from OpenVDM API")
            raise err


    def get_lowering_start_date(self):
        """
        Return the start date for the current lowering
        """

        url = self.config['siteRoot'] + 'api/warehouse/getLoweringStartDate'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj['loweringStartDate']
        except Exception as err:
            logging.error("Unable to retrieve lowering start date from OpenVDM API")
            raise err

    def get_lowering_end_date(self):
        """
        Return the end date for the current lowering
        """

        url = self.config['siteRoot'] + 'api/warehouse/getLoweringEndDate'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj['loweringEndDate']
        except Exception as err:
            logging.error("Unable to retrieve lowering end date from OpenVDM API")
            raise err


    def get_lowerings(self):
        """
        Return the lowerings found for the current cruise
        """

        url = self.config['siteRoot'] + 'api/warehouse/getLowerings'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj
        except Exception as err:
            logging.error("Unable to retrieve lowerings from OpenVDM API")
            raise err


    def get_extra_directory(self, extra_directory_id):
        """
        Return the extra directory configuration based on the extra_directory_id
        """

        url = self.config['siteRoot'] + 'api/extraDirectories/getExtraDirectory/' + extra_directory_id

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj[0] if len(return_obj) > 0 else None
        except Exception as err:
            logging.error("Unable to retrieve extra directory: %s from OpenVDM API", extra_directory_id)
            raise err

    def get_extra_directory_by_name(self, extra_directory_name):
        """
        Return the extra directory configuration based on the extra_directory_name
        """

        extra_directory = list(filter(lambda directory: directory['name'] == extra_directory_name, self.get_extra_directories()))
        return extra_directory[0] if len(extra_directory) > 0 else None

    def get_extra_directories(self):
        """
        Return all extra directory configurations

        """

        url = self.config['siteRoot'] + 'api/extraDirectories/getExtraDirectories'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj
        except Exception as err:
            logging.error("Unable to retrieve extra directories from OpenVDM API")
            raise err

    def get_required_extra_directory(self, extra_directory_id):
        """
        Return the required extra directory configuration based on the extra_directory_id

        """

        url = self.config['siteRoot'] + 'api/extraDirectories/getRequiredExtraDirectory/' + extra_directory_id

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj[0]
        except Exception as err:
            logging.error("Unable to retrieve required extra directory: %s from OpenVDM API", extra_directory_id)
            raise err

    def get_required_extra_directory_by_name(self, extra_directory_name):
        """
        Return the required extra directory configuration based on the extra_directory_name
        """

        extra_directory = list(filter(lambda directory: directory['name'] == extra_directory_name, self.get_required_extra_directories()))
        return extra_directory[0] if len(extra_directory) > 0 else None

    def get_required_extra_directories(self):
        """
        Return all required extra directories
        """

        url = self.config['siteRoot'] + 'api/extraDirectories/getRequiredExtraDirectories'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj
        except Exception as err:
            logging.error("Unable to retrieve required extra directories from OpenVDM API")
            raise err

    def get_shipboard_data_warehouse_config(self):
        """
        Return the shipboard data warehouse configuration
        """

        url = self.config['siteRoot'] + 'api/warehouse/getShipboardDataWarehouseConfig'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj
        except Exception as err:
            logging.error("Unable to retrieve shipboard data warehouse configuration from OpenVDM API")
            raise err


    def get_ship_to_shore_bw_limit_status(self):
        """
        Return the ship-to-shore transfer bandwidth limit
        """

        url = self.config['siteRoot'] + 'api/warehouse/getShipToShoreBWLimitStatus'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj['shipToShoreBWLimitStatus'] == "On"
        except Exception as err:
            logging.error("Unable to retrieve ship-to-shore bandwidth limit status from OpenVDM API")
            raise err

    def get_ship_to_shore_transfer(self, ship_to_shore_transfer_id):
        """
        Return the ship-to-shore configuration based on the ship_to_shore_transfer_id

        """

        url = self.config['siteRoot'] + 'api/shipToShoreTransfers/getShipToShoreTransfer/' + ship_to_shore_transfer_id

        try:
            req = requests.get(url)
            return json.loads(req.text)[0]
        except Exception as err:
            logging.error("Unable to retrieve ship-to-shore transfer: %s from OpenVDM API", ship_to_shore_transfer_id)
            raise err

    def get_ship_to_shore_transfers(self):
        """
        Return all ship-to-shore configurations
        """

        url = self.config['siteRoot'] + 'api/shipToShoreTransfers/getShipToShoreTransfers'

        try:
            req = requests.get(url)
            return json.loads(req.text)
        except Exception as err:
            logging.error("Unable to retrieve ship-to-shore transfers from OpenVDM API")
            raise err


    def get_required_ship_to_shore_transfers(self):
        """
        Return all required ship-to-shore configurations
        """

        url = self.config['siteRoot'] + 'api/shipToShoreTransfers/getRequiredShipToShoreTransfers'

        try:
            req = requests.get(url)
            return json.loads(req.text)
        except Exception as err:
            logging.error("Unable to retrieve required ship-to-shore transfers from OpenVDM API")
            raise err


    def get_system_status(self):
        """
        Return the system status
        """

        url = self.config['siteRoot'] + 'api/warehouse/getSystemStatus'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj['systemStatus']
        except Exception as err:
            logging.error("Unable to retrieve system status from OpenVDM API")
            raise err

    def get_tasks(self):
        """
        Return the list of all available tasks
        """

        url = self.config['siteRoot'] + 'api/tasks/getTasks'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj
        except Exception as err:
            logging.error("Unable to retrieve tasks from OpenVDM API")
            raise err


    def get_active_tasks(self):
        """
        Return the list of all currently active tasks
        """

        url = self.config['siteRoot'] + 'api/tasks/getActiveTasks'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj
        except Exception as err:
            logging.error("Unable to retrieve active tasks from OpenVDM API")
            raise err


    def get_task(self, task_id):
        """
        Return a task based on the task_id
        """

        url = self.config['siteRoot'] + 'api/tasks/getTask/' + task_id

        try:
            req = requests.get(url)
            task = json.loads(req.text)
            return task[0] if len(task) > 0 else None
        except Exception as err:
            logging.error("Unable to retrieve task: %s from OpenVDM API", task_id)
            raise err


    def get_task_by_name(self, task_name):
        """
        Return a task based on the task_name
        """

        url = self.config['siteRoot'] + 'api/tasks/getTasks'

        try:
            req = requests.get(url)
            tasks = json.loads(req.text)
            task = list(filter(lambda task: task['name'] == task_name, tasks))
            return task[0] if len(task) > 0 else None
        except Exception as err:
            logging.error("Unable to retrieve task: %s from OpenVDM API", task_name)
            raise err


    def get_collection_system_transfers(self):
        """
        Return all collection system transfer configurations

        """

        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/getCollectionSystemTransfers'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj
        except Exception as err:
            logging.error("Unable to retrieve collection system transfers from OpenVDM API")
            raise err


    def get_active_collection_system_transfers(self, cruise=True, lowering=True):
        """
        Return all active collection system transfer configurations
        """

        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/getActiveCollectionSystemTransfers'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            if not cruise:
                return_obj = list(filter(lambda transfer: transfer['cruiseOrLowering'] != "0", return_obj))
            if not lowering:
                return_obj = list(filter(lambda transfer: transfer['cruiseOrLowering'] != "1", return_obj))
            return return_obj
        except Exception as err:
            logging.error("Unable to retrieve active collection system transfers from OpenVDM API")
            raise err


    def get_collection_system_transfer(self, collection_system_transfer_id):
        """
        Return the collection system transfer configuration based on the collection_system_transfer_id
        """

        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/getCollectionSystemTransfer/' + collection_system_transfer_id

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj[0] if len(return_obj) > 0 else False
        except Exception as err:
            logging.error("Unable to retrieve collection system transfer: %s from OpenVDM API", collection_system_transfer_id)
            raise err


    def get_collection_system_transfer_by_name(self, collection_system_transfer_name):
        """
        Return the collection system transfer configuration based on the collection_system_transfer_name
        """

        collection_system_transfer = list(filter(lambda transfer: transfer['name'] == collection_system_transfer_name, self.get_collection_system_transfers()))
        return collection_system_transfer[0] if len(collection_system_transfer) > 0 else False


    def get_cruise_data_transfers(self):
        """
        Return all cruise data transfers
        """

        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/getCruiseDataTransfers'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj
        except Exception as err:
            logging.error("Unable to retrieve cruise data transfers from OpenVDM API")
            raise err

    def get_required_cruise_data_transfers(self):
        """
        Return all requried cruise data transfers
        """

        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/getRequiredCruiseDataTransfers'

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj
        except Exception as err:
            logging.error("Unable to retrieve required cruise data transfers from OpenVDM API")
            raise err

    def get_cruise_data_transfer(self, cruise_data_transfer_id):
        """
        Return the cruise data transfer based on the cruise_data_transfer_id
        """

        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/getCruiseDataTransfer/' + cruise_data_transfer_id

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj[0]
        except Exception as err:
            logging.error("Unable to retrieve cruise data transfer: %s from OpenVDM API", cruise_data_transfer_id)
            raise err


    def get_required_cruise_data_transfer(self, cruise_data_transfer_id):
        """
        Return the required cruise data transfer based on the cruise_data_transfer_id
        """

        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/getRequiredCruiseDataTransfer/' + cruise_data_transfer_id

        try:
            req = requests.get(url)
            return_obj = json.loads(req.text)
            return return_obj[0]
        except Exception as err:
            logging.error("Unable to retrieve required cruise data transfer: %s from OpenVDM API", cruise_data_transfer_id)
            raise err

    def get_cruise_data_transfer_by_name(self, cruise_data_transfer_name):
        """
        Return the cruise data transfer based on the cruise_data_transfer_name
        """

        cruise_data_transfer = list(filter(lambda transfer: transfer['name'] == cruise_data_transfer_name, self.get_cruise_data_transfers()))
        return cruise_data_transfer[0] if len(cruise_data_transfer) > 0 else False


    def get_required_cruise_data_transfer_by_name(self, cruise_data_transfer_name):
        """
        Return the required cruise data transfer based on the cruise_data_transfer_name
        """

        cruise_data_transfer = list(filter(lambda transfer: transfer['name'] == cruise_data_transfer_name, self.get_required_cruise_data_transfers()))
        return cruise_data_transfer[0] if len(cruise_data_transfer) > 0 else False


    def send_msg(self, message_title, message_body=''):
        """
        Send a message to OpenVDM
        """

        url = self.config['siteRoot'] + 'api/messages/newMessage'

        try:
            payload = {'messageTitle': message_title, 'messageBody':message_body}
            req = requests.post(url, data=payload)
            return req.text
        except Exception as err:
            logging.error("Unable to send message: \"%s: %s\" with OpenVDM API", message_title, message_body)
            raise err


    def clear_error_collection_system_transfer(self, collection_system_transfer_id, job_status):
        """
        Clear the status flag for the collection system transfer specified by the collection_system_transfer_id
        """

        if job_status == "3":
            # Clear Error for current tranfer in DB via API
            url = self.config['siteRoot'] + 'api/collectionSystemTransfers/setIdleCollectionSystemTransfer/' + collection_system_transfer_id

            try:
                requests.get(url)
            except Exception as err:
                logging.error("Unable to clear error status for collection system transfer: %s with OpenVDM API", collection_system_transfer_id)
                raise err

    def clear_error_cruise_data_transfer(self, cruise_data_transfer_id, job_status):
        """
        Clear the status flag for the cruise data transfer specified by the cruise_data_transfer_id
        """

        if job_status == "3":
            # Clear Error for current tranfer in DB via API
            url = self.config['siteRoot'] + 'api/cruiseDataTransfers/setIdleCruiseDataTransfer/' + cruise_data_transfer_id

            try:
                requests.get(url)
            except Exception as err:
                logging.error("Unable to clear error status for cruise data transfer: %s with OpenVDM API", cruise_data_transfer_id)
                raise err

    def clear_error_task(self, task_id):
        """
        Clear the status flag for the task specified by the task_id
        """

        task = self.get_task(task_id)

        if task['status'] == '3':
            self.set_idle_task(task_id)

    def set_error_collection_system_transfer(self, collection_system_transfer_id, reason=''):
        """
        Set the status flag to error for the collection system transfer specified by the collection_system_transfer_id
        """

        # Set Error for current tranfer in DB via API
        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/setErrorCollectionSystemTransfer/' + collection_system_transfer_id

        try:
            requests.get(url)
            collection_system_transfer_name = self.get_collection_system_transfer(collection_system_transfer_id)['name']
            title = collection_system_transfer_name + ' Data Transfer failed'
            self.send_msg(title, reason)
        except Exception as err:
            logging.error("Unable to set status of collection system transfer: %s to error with OpenVDM API", collection_system_transfer_id)
            raise err

    def set_error_collection_system_transfer_test(self, collection_system_transfer_id, reason=''):
        """
        Set the status flag to error for the cruise data transfer specified by the collection_system_transfer_id
        """

        # Set Error for current tranfer test in DB via API
        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/setErrorCollectionSystemTransfer/' + collection_system_transfer_id

        try:
            requests.get(url)
            collection_system_transfer_name = self.get_collection_system_transfer(collection_system_transfer_id)['name']
            title = collection_system_transfer_name + ' Connection test failed'
            self.send_msg(title, reason)
        except Exception as err:
            logging.error("Unable to set test status of collection system transfer: %s to error with OpenVDM API", collection_system_transfer_id)
            raise err


    def set_error_cruise_data_transfer(self, cruise_data_transfer_id, reason=''):
        """
        Set the status flag to error for the cruise data transfer specified by the cruise_data_transfer_id
        """

        # Set Error for current tranfer in DB via API
        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/setErrorCruiseDataTransfer/' + cruise_data_transfer_id

        try:
            requests.get(url)
            cruise_data_transfer_name = self.get_cruise_data_transfer(cruise_data_transfer_id)['name']
            title = cruise_data_transfer_name + ' Data Transfer failed'
            self.send_msg(title, reason)
        except Exception as err:
            logging.error("Unable to set status of cruise data transfer: %s to error with OpenVDM API", cruise_data_transfer_id)
            raise err

    def set_error_cruise_data_transfer_test(self, cruise_data_transfer_id, reason = ''):
        """
        Set the status flag to error for the cruise data transfer specified by the cruise_data_transfer_id
        """

        # Set Error for current tranfer test in DB via API
        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/setErrorCruiseDataTransfer/' + cruise_data_transfer_id

        try:
            requests.get(url)
            cruise_data_transfer_name = self.get_cruise_data_transfer(cruise_data_transfer_id)['name']
            title = cruise_data_transfer_name + ' Connection test failed'
            self.send_msg(title, reason)
        except Exception as err:
            logging.error("Unable to set test status of cruise data transfer: %s to error with OpenVDM API", cruise_data_transfer_id)
            raise err

    def set_error_task(self, task_id, reason=''):
        """
        Set the status flag to error for the task specified by the task_id
        """

        # Set Error for current task in DB via API
        url = self.config['siteRoot'] + 'api/tasks/setErrorTask/' + task_id

        try:
            requests.get(url)
            task_name = self.get_task(task_id)['longName']
            title = task_name + ' failed'
            self.send_msg(title, reason)
        except Exception as err:
            logging.error("Unable to set error status of task: %s with OpenVDM API", task_id)
            raise err

    def set_idle_collection_system_transfer(self, collection_system_transfer_id):
        """
        Set the status flag to idle for the collection system transfer specified by the collection_system_transfer_id
        """

        # Set Error for current tranfer in DB via API
        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/setIdleCollectionSystemTransfer/' + collection_system_transfer_id

        try:
            requests.get(url)
        except Exception as err:
            logging.error("Unable to set collection system transfer: %s to idle with OpenVDM API", collection_system_transfer_id)
            raise err

    def set_idle_cruise_data_transfer(self, cruise_data_transfer_id):
        """
        Set the status flag to idle for the cruise data transfer specified by the cruise_data_transfer_id
        """

        # Set Error for current tranfer in DB via API
        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/setIdleCruiseDataTransfer/' + cruise_data_transfer_id

        try:
            requests.get(url)
        except Exception as err:
            logging.error("Unable to set cruise data transfer: %s to idle with OpenVDM API", cruise_data_transfer_id)
            raise err


    def set_idle_task(self, task_id):
        """
        Set the status flag to idle for the task specified by the task_id
        """

        # Set Idle for the tasks in DB via API
        url = self.config['siteRoot'] + 'api/tasks/setIdleTask/' + task_id

        try:
            requests.get(url)
        except Exception as err:
            logging.error("Unable to set task: %s to idle with OpenVDM API", task_id)
            raise err

    def set_running_collection_system_transfer(self, collection_system_transfer_id, job_pid, job_handle):
        """
        Set the status flag to running for the collection system transfer specified by the collection_system_transfer_id
        """

        collection_system_transfer_name = self.get_collection_system_transfer(collection_system_transfer_id)['name']
        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/setRunningCollectionSystemTransfer/' + collection_system_transfer_id
        payload = {'jobPid': job_pid}

        try:
            requests.post(url, data=payload)

            # Add to gearman job tracker
            self.track_gearman_job('Transfer for ' + collection_system_transfer_name, job_pid, job_handle)
        except Exception as err:
            logging.error("Unable to set collection system transfer: %s to running with OpenVDM API", collection_system_transfer_name)
            raise err


    def set_running_collection_system_transfer_test(self, collection_system_transfer_id, job_pid, job_handle):
        """
        Set the status flag to running for the collection system transfer specified by the collection_system_transfer_id
        """

        collection_system_transfer_name = self.get_collection_system_transfer(collection_system_transfer_id)['name']

        # Add to gearman job tracker
        self.track_gearman_job('Transfer test for ' + collection_system_transfer_name, job_pid, job_handle)

    def set_running_cruise_data_transfer(self, cruise_data_transfer_id, job_pid, job_handle):
        """
        Set the status flag to running for the cruise data transfer specified by the cruise_data_transfer_id
        """

        cruise_data_transfer_name = self.get_cruise_data_transfer(cruise_data_transfer_id)['name']

        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/setRunningCruiseDataTransfer/' + cruise_data_transfer_id
        payload = {'jobPid': job_pid}

        try:
            req = requests.post(url, data=payload)

            # Add to gearman job tracker
            self.track_gearman_job('Transfer for ' + cruise_data_transfer_name, job_pid, job_handle)

            return req.text
        except Exception as err:
            logging.error("Unable to set cruise data transfer: %s to running with OpenVDM API", cruise_data_transfer_name)
            raise err

    def set_running_cruise_data_transfer_test(self, cruise_data_transfer_id, job_pid, job_handle):
        """
        Set the status flag to running for the cruise data transfer specified by the cruise_data_transfer_id
        """

        cruise_data_transfer_name = self.get_cruise_data_transfer(cruise_data_transfer_id)['name']

        # Add to gearman job tracker
        self.track_gearman_job('Transfer test for ' + cruise_data_transfer_name, job_pid, job_handle)

    def set_running_task(self, task_id, job_pid, job_handle):
        """
        Set the status flag to running for the task specified by the task_id
        """

        task_name = self.get_task(task_id)['longName']

        # Set Running for the tasks in DB via API
        url = self.config['siteRoot'] + 'api/tasks/setRunningTask/' + task_id
        payload = {'jobPid': job_pid}

        try:
            requests.post(url, data=payload)

            # Add to gearman job tracker
            self.track_gearman_job(task_name, job_pid, job_handle)
        except Exception as err:
            logging.error("Unable to set task: %s to running with OpenVDM API", task_name)
            raise err


    def track_gearman_job(self, job_name, job_pid, job_handle):
        """
        Track a gearman task within OpenVDM
        """

        # Add Job to DB via API
        url = self.config['siteRoot'] + 'api/gearman/newJob/' + job_handle
        payload = {'jobName': job_name, 'jobPid': job_pid}

        try:
            requests.post(url, data=payload)
        except Exception as err:
            logging.error("Unable to add new gearman task tracking with OpenVDM API, Task: %s", job_name)
            raise err


    def set_cruise_size(self, size_in_bytes):
        """
        Set the filesize for the current cruise
        """

        # Set Error for current tranfer in DB via API
        url = self.config['siteRoot'] + 'api/warehouse/setCruiseSize'
        payload = {'bytes': size_in_bytes}

        try:
            requests.post(url, data=payload)
        except Exception as err:
            logging.error("Unable to set cruise size with OpenVDM API")
            raise err

    def set_lowering_size(self, size_in_bytes):
        """
        Set the filesize for the current lowering
        """

        # Set Error for current tranfer in DB via API
        url = self.config['siteRoot'] + 'api/warehouse/setLoweringSize'
        payload = {'bytes': size_in_bytes}

        try:
            requests.post(url, data=payload)
        except Exception as err:
            logging.error("Unable to set lowering size with OpenVDM API")
            raise err
