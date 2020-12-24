# ----------------------------------------------------------------------------------- #
#
#         FILE:  openvdm.py
#
#  DESCRIPTION:  OpenVDM python module
#
#         BUGS:
#        NOTES:
#       AUTHOR:  Webb Pinner
#      COMPANY:  Capable Solutions
#      VERSION:  2.5
#      CREATED:  2016-02-02
#     REVISION:  2020-12-21
#
# LICENSE INFO: Open Vessel Data Management v2.5 (OpenVDMv2)
#               Copyright (C) OceanDataRat.org 2021
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/gpl-3.0.html>.
#
# ----------------------------------------------------------------------------------- #

import requests
import yaml
import json
import datetime
import logging

configFile = '/usr/local/etc/openvdm/openvdm.yaml'

class OpenVDM():

    def __init__(self):

        self.config = {}
        self.config = self.parseOVDMConfig()
    #     self.logger = logging.getLogger(__file__)


    # def getLogger():
    #     return self.logger


    def parseOVDMConfig(self):
        """
        Read the yaml-formatted OpenVDM configuration file and return the
        configuration as a python dict
        """

        try:
            with open(configFile, 'r') as f:
                try:
                    return yaml.load(f.read(), Loader=yaml.FullLoader)
                except Exception as e:
                    logging.error("Unable to parse configuration file: {}".format(configFile))
                    raise e
        except Exception as e:
            logging.error("Unable to open configuration file: {}".format(configFile))
            raise e


    def clearGearmanJobsFromDB(self):

        url = self.config['siteRoot'] + 'api/gearman/clearAllJobsFromDB'

        try:
            r = requests.get(url)
            returnObj = json.loads(r.text)
        except Exception as e:
            logging.error("Unable to clear Gearman Jobs from OpenVDM API")
            raise e


    def getDashboardDataProcessingScriptDir(self):

        return self.config['dashboardData']['processingScriptDir']


    def showOnlyCurrentCruiseDir(self):

        return self.config['showOnlyCurrentCruiseDir']


    def getShowLoweringComponents(self):

        url = self.config['siteRoot'] + 'api/warehouse/getShowLoweringComponents'

        try:
            r = requests.get(url)
            return True if r.text == 'true' else False
        except Exception as e:
            logging.error("Unable to retrieve 'showLoweringComponents' flag from OpenVDM API")
            raise e


    def getOVDMConfig(self):

        url = self.config['siteRoot'] + 'api/warehouse/getCruiseConfig'

        try:
            r = requests.get(url)
            returnObj = json.loads(r.text)
            returnObj['configCreatedOn'] = datetime.datetime.utcnow().strftime("%Y/%m/%dT%H:%M:%SZ")
            return returnObj
        except Exception as e:
            logging.error("Unable to retrieve cruise configuration from OpenVDM API")
            raise e


    def getLoweringConfig(self):

        url = self.config['siteRoot'] + 'api/warehouse/getLoweringConfig'

        try:
            r = requests.get(url)
            returnObj = json.loads(r.text)
            returnObj['configCreatedOn'] = datetime.datetime.utcnow().strftime("%Y/%m/%dT%H:%M:%SZ")
            return returnObj
        except Exception as e:
            logging.error("Unable to retrieve lowering configuration from OpenVDM API")
            raise e

    
    def getDashboardDataProcessingScriptSuffix(self):
        
        return self.config['dashboardData']['processingScriptSuffix']

    
    def getGearmanServer(self):
        
        return self.config['gearmanServer']

    
    def getSiteRoot(self):
        
        return self.config['siteRoot']
    
    
    def getMD5FilesizeLimit(self):

        url = self.config['siteRoot'] + 'api/warehouse/getMD5FilesizeLimit'

        try:
            r = requests.get(url)
            returnObj = json.loads(r.text)
            return returnObj['md5FilesizeLimit']
        except Exception as e:
            logging.error("Unable to retrieve MD5 filesize limit from OpenVDM API")
            raise e
    
    def getMD5FilesizeLimitStatus(self):

        url = self.config['siteRoot'] + 'api/warehouse/getMD5FilesizeLimitStatus'
        
        try:
            r = requests.get(url)
            returnObj = json.loads(r.text)
            return returnObj['md5FilesizeLimitStatus']
        except Exception as e:
            logging.error("Unable to retrieve MD5 filesize limit status from OpenVDM API")
            raise e


    def getTasksForHook(self, name):        
        
        try:
            self.config['hooks'][name]
        except KeyError:
            return []
        else:
            return self.config['hooks'][name]
        
    
    def getTransferInterval(self):
        
        return self.config['transferInterval']
    

    def getCruiseID(self):
        
        url = self.config['siteRoot'] + 'api/warehouse/getCruiseID'
    
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal['cruiseID']
        except Exception as e:
            logging.error("Unable to retrieve CruiseID from OpenVDM API")
            raise e

    def getCruiseSize(self):
        
        url = self.config['siteRoot'] + 'api/warehouse/getCruiseSize'

        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal
        except Exception as e:
            logging.error("Unable to retrieve cruise size from OpenVDM API")
            raise e

    
    def getCruiseStartDate(self):
        
        url = self.config['siteRoot'] + 'api/warehouse/getCruiseStartDate'
    
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal['cruiseStartDate']
        except Exception as e:
            logging.error("Unable to retrieve cruise start date from OpenVDM API")
            raise e

    
    def getCruiseEndDate(self):
        
        url = self.config['siteRoot'] + 'api/warehouse/getCruiseEndDate'
    
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal['cruiseEndDate']
        except Exception as e:
            logging.error("Unable to retrieve cruise end date from OpenVDM API")
            raise e


    def getCruises(self):

        url = self.config['siteRoot'] + 'api/warehouse/getCruises'

        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal
        except Exception as e:
            logging.error("Unable to retrieve cruises from OpenVDM API")
            raise e


    def getLoweringID(self):
        
        url = self.config['siteRoot'] + 'api/warehouse/getLoweringID'
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal['loweringID']
        except Exception as e:
            logging.error("Unable to retrieve LoweringID from OpenVDM API")
            raise e
    

    def getLoweringSize(self):
        
        url = self.config['siteRoot'] + 'api/warehouse/getLoweringSize'
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal
        except Exception as e:
            logging.error("Unable to retrieve lowering size from OpenVDM API")
            raise e


    def getLoweringStartDate(self):
        
        url = self.config['siteRoot'] + 'api/warehouse/getLoweringStartDate'
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal['loweringStartDate']
        except Exception as e:
            logging.error("Unable to retrieve lowering start date from OpenVDM API")
            raise e
    
    
    def getLoweringEndDate(self):
        
        url = self.config['siteRoot'] + 'api/warehouse/getLoweringEndDate'
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal['loweringEndDate']
        except Exception as e:
            logging.error("Unable to retrieve lowering end date from OpenVDM API")
            raise e
    

    def getLowerings(self):
        url = self.config['siteRoot'] + 'api/warehouse/getLowerings'
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal
        except Exception as e:
            logging.error("Unable to retrieve lowerings from OpenVDM API")
            raise e

    
    def getExtraDirectory(self, extraDirectoryID):
        
        url = self.config['siteRoot'] + 'api/extraDirectories/getExtraDirectory/' + extraDirectoryID
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal[0] if len(returnVal) > 0 else False
        except Exception as e:
            logging.error("Unable to retrieve extra directory: {} from OpenVDM API".format(extraDirectoryID))
            raise e
    
    def getExtraDirectoryByName(self, extraDirectoryName):

        extraDirectory = list(filter(lambda directory: directory['name'] == extraDirectoryName, self.getExtraDirectories()))
        return extraDirectory[0] if len(extraDirectory) > 0 else False
    
    def getExtraDirectories(self):
        
        url = self.config['siteRoot'] + 'api/extraDirectories/getExtraDirectories'
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal
        except Exception as e:
            logging.error("Unable to retrieve extra directories from OpenVDM API")
            raise e
    
    
    def getRequiredExtraDirectory(self, extraDirectoryID):
        
        url = self.config['siteRoot'] + 'api/extraDirectories/getRequiredExtraDirectory/' + extraDirectoryID
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal[0]
        except Exception as e:
            logging.error("Unable to retrieve required extra directory: {} from OpenVDM API".format(extraDirectoryID))
            raise e
    
    
    def getRequiredExtraDirectoryByName(self, extraDirectoryName):

        extraDirectory = list(filter(lambda directory: directory['name'] == extraDirectoryName, self.getRequiredExtraDirectories()))
        return extraDirectory[0] if len(extraDirectory) > 0 else False 
    
    
    def getRequiredExtraDirectories(self):
        
        url = self.config['siteRoot'] + 'api/extraDirectories/getRequiredExtraDirectories'
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal
        except Exception as e:
            logging.error("Unable to retrieve required extra directories from OpenVDM API")
            raise e
    
    
    def getShipboardDataWarehouseConfig(self):
        
        url = self.config['siteRoot'] + 'api/warehouse/getShipboardDataWarehouseConfig'
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal
        except Exception as e:
            logging.error("Unable to retrieve shipboard data warehouse configuration from OpenVDM API")
            raise e


    def getShipToShoreBWLimitStatus(self):

        url = self.config['siteRoot'] + 'api/warehouse/getShipToShoreBWLimitStatus'
        
        try:
            r = requests.get(url)
            returnObj = json.loads(r.text)
            return returnObj['shipToShoreBWLimitStatus'] == "On"
        except Exception as e:
            logging.error("Unable to retrieve ship-to-shore bandwidth limit status from OpenVDM API")
            raise e
    
    
    def getShipToShoreTransfer(self, shipToShoreTransferID):

        url = self.config['siteRoot'] + 'api/shipToShoreTransfers/getShipToShoreTransfer/' + shipToShoreTransferID
        
        try:
            r = requests.get(url)
            return json.loads(r.text)[0]
        except Exception as e:
            logging.error("Unable to retrieve ship-to-shore transfer: {} from OpenVDM API".format(shipToShoreTransferID))
            raise e
    
    
    def getShipToShoreTransfers(self):

        url = self.config['siteRoot'] + 'api/shipToShoreTransfers/getShipToShoreTransfers'
        
        try:
            r = requests.get(url)
            return json.loads(r.text)
        except Exception as e:
            logging.error("Unable to retrieve ship-to-shore transfers from OpenVDM API")
            raise e

    
    def getRequiredShipToShoreTransfers(self):

        url = self.config['siteRoot'] + 'api/shipToShoreTransfers/getRequiredShipToShoreTransfers'
        
        try:
            r = requests.get(url)
            return json.loads(r.text)
        except Exception as e:
            logging.error("Unable to retrieve required ship-to-shore transfers from OpenVDM API")
            raise e

    
    def getSystemStatus(self):

        url = self.config['siteRoot'] + 'api/warehouse/getSystemStatus'
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal['systemStatus']
        except Exception as e:
            logging.error("Unable to retrieve system status from OpenVDM API")
            raise e
    
    
    def getTasks(self):

        url = self.config['siteRoot'] + 'api/tasks/getTasks'
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal
        except Exception as e:
            logging.error("Unable to retrieve tasks from OpenVDM API")
            raise e

    
    def getActiveTasks(self):

        url = self.config['siteRoot'] + 'api/tasks/getActiveTasks'
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal
        except Exception as e:
            logging.error("Unable to retrieve active tasks from OpenVDM API")
            raise e


    def getTask(self, taskID):

        url = self.config['siteRoot'] + 'api/tasks/getTask/' + taskID
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal[0] if len(returnVal) > 0 else []
        except Exception as e:
            logging.error("Unable to retrieve task: {} from OpenVDM API".format(taskID))
            raise e

        
    def getCollectionSystemTransfers(self):

        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/getCollectionSystemTransfers'
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal
        except Exception as e:
            logging.error("Unable to retrieve collection system transfers from OpenVDM API")
            raise e

    
    def getActiveCollectionSystemTransfers(self):

        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/getActiveCollectionSystemTransfers'
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal
        except Exception as e:
            logging.error("Unable to retrieve active collection system transfers from OpenVDM API")
            raise e


    def getCollectionSystemTransfer(self, collectionSystemTransferID):

        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/getCollectionSystemTransfer/' + collectionSystemTransferID
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal[0] if len(returnVal) > 0 else False
        except Exception as e:
            logging.error("Unable to retrieve collection system transfer: {} from OpenVDM API".format(collectionSystemTransferID))
            raise e

    
    def getCollectionSystemTransferByName(self, collectionSystemTransferName):

        collectionSystemTransfer = list(filter(lambda transfer: transfer['name'] == collectionSystemTransferName, self.getCollectionSystemTransfers()))
        return collectionSystemTransfer[0] if len(collectionSystemTransfer) > 0 else False 

    
    def getCruiseDataTransfers(self):

        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/getCruiseDataTransfers'
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal
        except Exception as e:
            logging.error("Unable to retrieve cruise data transfers from OpenVDM API")
            raise e
    
    
    def getRequiredCruiseDataTransfers(self):

        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/getRequiredCruiseDataTransfers'
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal
        except Exception as e:
            logging.error("Unable to retrieve required cruise data transfers from OpenVDM API")
            raise e
    
    
    def getCruiseDataTransfer(self, cruiseDataTransferID):

        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/getCruiseDataTransfer/' + cruiseDataTransferID
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal[0]
        except Exception as e:
            logging.error("Unable to retrieve cruise data transfer: {} from OpenVDM API".format(cruiseDataTransferID))
            raise e


    def getRequiredCruiseDataTransfer(self, cruiseDataTransferID):

        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/getRequiredCruiseDataTransfer/' + cruiseDataTransferID
        
        try:
            r = requests.get(url)
            returnVal = json.loads(r.text)
            return returnVal[0]
        except Exception as e:
            logging.error("Unable to retrieve required cruise data transfer: {} from OpenVDM API".format(cruiseDataTransferID))
            raise e
    
    
    def getCruiseDataTransferByName(self, cruiseDataTransferName):

        cruiseDataTransfer = list(filter(lambda transfer: transfer['name'] == cruiseDataTransferName, self.getCruiseDataTransfers()))
        return cruiseDataTransfer[0] if len(cruiseDataTransfer) > 0 else False 


    def getRequiredCruiseDataTransferByName(self, cruiseDataTransferName):

        cruiseDataTransfer = list(filter(lambda transfer: transfer['name'] == cruiseDataTransferName, self.getRequiredCruiseDataTransfers()))
        return cruiseDataTransfer[0] if len(cruiseDataTransfer) > 0 else False 


    def sendMsg(self, messageTitle, messageBody=''):

        url = self.config['siteRoot'] + 'api/messages/newMessage'
        
        try:
            payload = {'messageTitle': messageTitle, 'messageBody':messageBody}
            r = requests.post(url, data=payload)
            return r.text
        except Exception as e:
            logging.error("Unable to send message: \"{}: {}\" with OpenVDM API".format(messageTitle, messageBody))
            raise e


    def clearError_collectionSystemTransfer(self, collectionSystemTransferID, jobStatus):

        if jobStatus == "3":
            # Clear Error for current tranfer in DB via API
            url = self.config['siteRoot'] + 'api/collectionSystemTransfers/setIdleCollectionSystemTransfer/' + collectionSystemTransferID
            
            try:
                r = requests.get(url)
            except Exception as e:
                logging.error("Unable to clear error status for collection system transfer: {} with OpenVDM API".format(collectionSystemTransferID))
                raise e
        
            
    def clearError_cruiseDataTransfer(self, cruiseDataTransferID, jobStatus):

        if jobStatus == "3":
            # Clear Error for current tranfer in DB via API
            url = self.config['siteRoot'] + 'api/cruiseDataTransfers/setIdleCruiseDataTransfer/' + cruiseDataTransferID
            
            try:
                r = requests.get(url)
            except Exception as e:
                logging.error("Unable to clear error status for cruise data transfer: {} with OpenVDM API".format(cruiseDataTransferID))
                raise e
        
            
    def clearError_task(self, taskID):
        
        task = self.getTask(taskID)
        
        if task['status'] == '3':
            self.setIdle_task(taskID)
            
    
    def setError_collectionSystemTransfer(self, collectionSystemTransferID, reason=''):

        # Set Error for current tranfer in DB via API
        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/setErrorCollectionSystemTransfer/' + collectionSystemTransferID
        
        try:
            r = requests.get(url)
            collectionSystemTransferName = self.getCollectionSystemTransfer(collectionSystemTransferID)['name']
            title = collectionSystemTransferName + ' Data Transfer failed'
            self.sendMsg(title, reason)
        except Exception as e:
            logging.error("Unable to set status of collection system transfer: {} to error with OpenVDM API".format(collectionSystemTransferID))
            raise e
    
    
    def setError_collectionSystemTransferTest(self, collectionSystemTransferID, reason=''):

        # Set Error for current tranfer test in DB via API
        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/setErrorCollectionSystemTransfer/' + collectionSystemTransferID
        
        try:
            r = requests.get(url)
            collectionSystemTransferName = self.getCollectionSystemTransfer(collectionSystemTransferID)['name']
            title = collectionSystemTransferName + ' Connection test failed'
            self.sendMsg(title, reason)
        except Exception as e:
            logging.error("Unable to set test status of collection system transfer: {} to error with OpenVDM API".format(collectionSystemTransferID))
            raise e

    
    def setError_cruiseDataTransfer(self, cruiseDataTransferID, reason=''):

        # Set Error for current tranfer in DB via API
        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/setErrorCruiseDataTransfer/' + cruiseDataTransferID
        
        try:
            r = requests.get(url)
            cruiseDataTransferName = self.getCruiseDataTransfer(cruiseDataTransferID)['name']
            title = cruiseDataTransferName + ' Data Transfer failed'
            self.sendMsg(title, reason)
        except Exception as e:
            logging.error("Unable to set status of cruise data transfer: {} to error with OpenVDM API".format(cruiseDataTransferID))
            raise e
        
        
    def setError_cruiseDataTransferTest(self, cruiseDataTransferID, reason = ''):

        # Set Error for current tranfer test in DB via API
        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/setErrorCruiseDataTransfer/' + cruiseDataTransferID
        
        try:
            r = requests.get(url)
            cruiseDataTransferName = self.getCruiseDataTransfer(cruiseDataTransferID)['name']
            title = cruiseDataTransferName + ' Connection test failed'
            self.sendMsg(title, reason)
        except Exception as e:
            logging.error("Unable to set test status of cruise data transfer: {} to error with OpenVDM API".format(cruiseDataTransferID))
            raise e
        
            
    def setError_task(self, taskID, reason=''):
       
        # Set Error for current task in DB via API
        url = self.config['siteRoot'] + 'api/tasks/setErrorTask/' + taskID
        
        try:
            r = requests.get(url)
            taskName = self.getTask(taskID)['longName']
            title = taskName + ' failed'
            self.sendMsg(title, reason)
        except Exception as e:
            logging.error("Unable to set error status of task: {} with OpenVDM API".format(taskID))
            raise e
        
    
    def setIdle_collectionSystemTransfer(self, collectionSystemTransferID):

        # Set Error for current tranfer in DB via API
        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/setIdleCollectionSystemTransfer/' + collectionSystemTransferID
        
        try:
            r = requests.get(url) 
        except Exception as e:
            logging.error("Unable to set collection system transfer: {} to idle with OpenVDM API".format(collectionSystemTransferID))
            raise e
        
    
    def setIdle_cruiseDataTransfer(self, cruiseDataTransferID):

        # Set Error for current tranfer in DB via API
        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/setIdleCruiseDataTransfer/' + cruiseDataTransferID
        
        try:
            r = requests.get(url) 
        except Exception as e:
            logging.error("Unable to set cruise data transfer: {} to idle with OpenVDM API".format(cruiseDataTransferID))
            raise e

    
    def setIdle_task(self, taskID):
        
        # Set Idle for the tasks in DB via API
        url = self.config['siteRoot'] + 'api/tasks/setIdleTask/' + taskID
        
        try:
            r = requests.get(url)
        except Exception as e:
            logging.error("Unable to set task: {} to idle with OpenVDM API".format(taskID))
            raise e
    
    
    def setRunning_collectionSystemTransfer(self, collectionSystemTransferID, jobPID, jobHandle):
        
        collectionSystemTransferName = self.getCollectionSystemTransfer(collectionSystemTransferID)['name']
        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/setRunningCollectionSystemTransfer/' + collectionSystemTransferID
        payload = {'jobPid': jobPID}
        
        try:
            r = requests.post(url, data=payload)

            # Add to gearman job tracker
            self.trackGearmanJob('Transfer for ' + collectionSystemTransferName, jobPID, jobHandle)        
        except Exception as e:
            logging.error("Unable to set collection system transfer: {} to running with OpenVDM API".format(collectionSystemTransferName))
            raise e

    
    def setRunning_collectionSystemTransferTest(self, collectionSystemTransferID, jobPID, jobHandle):

        collectionSystemTransferName = self.getCollectionSystemTransfer(collectionSystemTransferID)['name']
        
        # Add to gearman job tracker
        self.trackGearmanJob('Transfer test for ' + collectionSystemTransferName, jobPID, jobHandle)  
        
    
    def setRunning_cruiseDataTransfer(self, cruiseDataTransferID, jobPID, jobHandle):
        
        cruiseDataTransferName = self.getCruiseDataTransfer(cruiseDataTransferID)['name']

        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/setRunningCruiseDataTransfer/' + cruiseDataTransferID
        payload = {'jobPid': jobPID}
        
        try:
            r = requests.post(url, data=payload)

            # Add to gearman job tracker
            self.trackGearmanJob('Transfer for ' + cruiseDataTransferName, jobPID, jobHandle)

            return r.text
        except Exception as e:
            logging.error("Unable to set cruise data transfer: {} to running with OpenVDM API".format(cruiseDataTransferName))
            raise e
        
    
    def setRunning_cruiseDataTransferTest(self, cruiseDataTransferID, jobPID, jobHandle):

        cruiseDataTransferName = self.getCruiseDataTransfer(cruiseDataTransferID)['name']
        
        # Add to gearman job tracker
        self.trackGearmanJob('Transfer test for ' + cruiseDataTransferName, jobPID, jobHandle)  
        
    
    def setRunning_task(self, taskID, jobPID, jobHandle):
        
        taskName = self.getTask(taskID)['longName']
        
        # Set Running for the tasks in DB via API
        url = self.config['siteRoot'] + 'api/tasks/setRunningTask/' + taskID
        payload = {'jobPid': jobPID}
        
        try:
            r = requests.post(url, data=payload)

            # Add to gearman job tracker
            self.trackGearmanJob(taskName, jobPID, jobHandle)        
        except Exception as e:
            logging.error("Unable to set task: {} to running with OpenVDM API".format(taskName))
            raise e

        
    def trackGearmanJob(self, jobName, jobPID, jobHandle):
        
        # Add Job to DB via API
        url = self.config['siteRoot'] + 'api/gearman/newJob/' + jobHandle
        payload = {'jobName': jobName, 'jobPid': jobPID}
        
        try:
            r = requests.post(url, data=payload)
        except Exception as e:
            logging.error("Unable to add new gearman task tracking with OpenVDM API, Task: {}".format(jobName))
            raise e


    def set_cruiseSize(self, sizeInBytes):

        # Set Error for current tranfer in DB via API
        url = self.config['siteRoot'] + 'api/warehouse/setCruiseSize'
        payload = {'bytes': sizeInBytes}
        
        try:
            r = requests.post(url, data=payload)
        except Exception as e:
            logging.error("Unable to set cruise size with OpenVDM API")
            raise e

    def set_loweringSize(self, sizeInBytes):

        # Set Error for current tranfer in DB via API
        url = self.config['siteRoot'] + 'api/warehouse/setLoweringSize'
        payload = {'bytes': sizeInBytes}
        
        try:
            r = requests.post(url, data=payload) 
        except Exception as e:
            logging.error("Unable to set lowering size with OpenVDM API")
            raise e
