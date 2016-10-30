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
#      VERSION:  2.2
#      CREATED:  2016-02-02
#     REVISION:  2016-10-30
#
# LICENSE INFO: Open Vessel Data Management v2.2 (OpenVDMv2)
#               Copyright (C) OceanDataRat.org 2016
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

class OpenVDM():

    def __init__(self):

        self.config = {}
        self.config = self.parseOVDMConfig()


    def parseOVDMConfig(self):

        f = open('/usr/local/etc/openvdm/openvdm.yaml', 'r')
        return yaml.load(f.read())


    def clearGearmanJobsFromDB(self):
        url = self.config['siteRoot'] + 'api/gearman/clearAllJobsFromDB'
        r = requests.get(url)
        returnObj = json.loads(r.text)


    def getDashboardDataProcessingScriptDir(self):

        return self.config['dashboardData']['processingScriptDir']


    def showOnlyCurrentCruiseDir(self):

        return self.config['showOnlyCurrentCruiseDir']


    def getOVDMConfig(self):

        url = self.config['siteRoot'] + 'api/warehouse/getCruiseConfig'
        r = requests.get(url)
        returnObj = json.loads(r.text)
        returnObj['configCreatedOn'] = datetime.datetime.utcnow().strftime("%Y/%m/%dT%H:%M:%SZ")
        return returnObj

    
    def getDashboardDataProcessingScriptSuffix(self):
        
        return self.config['dashboardData']['processingScriptSuffix']

    
    def getGearmanServer(self):
        
        return self.config['gearmanServer']

    
    def getSiteRoot(self):
        
        return self.config['siteRoot']
    
    
    def getMD5FilesizeLimit(self):

        url = self.config['siteRoot'] + 'api/warehouse/getMD5FilesizeLimit'
        r = requests.get(url)
        returnObj = json.loads(r.text)
        return returnObj['md5FilesizeLimit']

    
    def getMD5FilesizeLimitStatus(self):

        url = self.config['siteRoot'] + 'api/warehouse/getMD5FilesizeLimitStatus'
        r = requests.get(url)
        returnObj = json.loads(r.text)
        return returnObj['md5FilesizeLimitStatus']
    

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
        r = requests.get(url)
        returnVal = json.loads(r.text)
        return returnVal['cruiseID']
    
    
    def getCruiseStartDate(self):
        
        url = self.config['siteRoot'] + 'api/warehouse/getCruiseStartDate'
        r = requests.get(url)
        returnVal = json.loads(r.text)
        return returnVal['cruiseStartDate']
    
    
    def getExtraDirectory(self, extraDirectoryID):
        
        url = self.config['siteRoot'] + 'api/extraDirectories/getExtraDirectory/' + extraDirectoryID
        r = requests.get(url)
        returnVal = json.loads(r.text)
        return returnVal[0]
    
    def getExtraDirectoryByName(self, extraDirectoryName):

        extraDirectories = self.getExtraDirectories()
        for extraDirectory in extraDirectories:
            if extraDirectory['name'] == extraDirectoryName:
                return extraDirectory
            
        return False
    
    def getExtraDirectories(self):
        
        url = self.config['siteRoot'] + 'api/extraDirectories/getExtraDirectories'
        r = requests.get(url)
        returnVal = json.loads(r.text)
        return returnVal
    
    
    def getRequiredExtraDirectory(self, extraDirectoryID):
        
        url = self.config['siteRoot'] + 'api/extraDirectories/getRequiredExtraDirectory/' + extraDirectoryID
        r = requests.get(url)
        returnVal = json.loads(r.text)
        return returnVal[0]
    
    
    def getRequiredExtraDirectoryByName(self, extraDirectoryName):

        extraDirectories = self.getRequiredExtraDirectories()
        for extraDirectory in extraDirectories:
            if extraDirectory['name'] == extraDirectoryName:
                return extraDirectory
            
        return False
    
    
    def getRequiredExtraDirectories(self):
        
        url = self.config['siteRoot'] + 'api/extraDirectories/getRequiredExtraDirectories'
        r = requests.get(url)
        returnVal = json.loads(r.text)
        return returnVal
    
    
    def getShipboardDataWarehouseConfig(self):
        
        url = self.config['siteRoot'] + 'api/warehouse/getShipboardDataWarehouseConfig'
        r = requests.get(url)
        returnVal = json.loads(r.text)
        return returnVal
    
    
    def getShipToShoreBWLimit(self):
        
        url = self.config['siteRoot'] + 'api/warehouse/getShipToShoreBWLimit'
        r = requests.get(url)
        returnObj = json.loads(r.text)
        return returnObj['shipToShoreBWLimit']


    def getShipToShoreBWLimitStatus(self):

        url = self.config['siteRoot'] + 'api/warehouse/getShipToShoreBWLimitStatus'
        r = requests.get(url)
        returnObj = json.loads(r.text)
        return returnObj['shipToShoreBWLimitStatus'] == "On"
    
    
    def getShipToShoreTransfer(self, shipToShoreTransferID):

        url = self.config['siteRoot'] + 'api/shipToShoreTransfers/getShipToShoreTransfer/' + shipToShoreTransferID
        r = requests.get(url)
        return json.loads(r.text)[0]
    
    
    def getShipToShoreTransfers(self):

        url = self.config['siteRoot'] + 'api/shipToShoreTransfers/getShipToShoreTransfers'
        r = requests.get(url)
        return json.loads(r.text)

    
    def getRequiredShipToShoreTransfers(self):

        url = self.config['siteRoot'] + 'api/shipToShoreTransfers/getRequiredShipToShoreTransfers'
        r = requests.get(url)
        return json.loads(r.text)

    
    def getSystemStatus(self):

        url = self.config['siteRoot'] + 'api/warehouse/getSystemStatus'
        r = requests.get(url)
        returnVal = json.loads(r.text)
        return returnVal['systemStatus']
    
    
    def getTasks(self):

        url = self.config['siteRoot'] + 'api/tasks/getTasks'
        r = requests.get(url)
        returnVal = json.loads(r.text)
        return returnVal

    
    def getTask(self, taskID):

        url = self.config['siteRoot'] + 'api/tasks/getTask/' + taskID
        r = requests.get(url)
        returnVal = json.loads(r.text)

        if len(returnVal) > 0:
            return returnVal[0]
        else:
            return []

        
    def getCollectionSystemTransfers(self):

        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/getCollectionSystemTransfers'
        r = requests.get(url)
        returnVal = json.loads(r.text)
        return returnVal

    
    def getCollectionSystemTransfer(self, collectionSystemTransferID):

        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/getCollectionSystemTransfer/' + collectionSystemTransferID
        r = requests.get(url)
        returnVal = json.loads(r.text)
        return returnVal[0]
    
    def getCollectionSystemTransferByName(self, collectionSystemTransferName):

        collectionSystemTransfers = self.getCollectionSystemTransfers()
        for collectionSystemTransfer in collectionSystemTransfers:
            if collectionSystemTransfer['name'] == collectionSystemTransferName:
                return collectionSystemTransfer
        
        return False
    
    def getCruiseDataTransfers(self):

        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/getCruiseDataTransfers'
        r = requests.get(url)
        returnVal = json.loads(r.text)
        return returnVal
    
    
    def getRequiredCruiseDataTransfers(self):

        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/getRequiredCruiseDataTransfers'
        r = requests.get(url)
        returnVal = json.loads(r.text)
        return returnVal
    
    
    def getCruiseDataTransfer(self, cruiseDataTransferID):

        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/getCruiseDataTransfer/' + cruiseDataTransferID
        r = requests.get(url)
        returnVal = json.loads(r.text)
        return returnVal[0]
    
    
    def sendMsg(self, messageTitle, messageBody=''):

        url = self.config['siteRoot'] + 'api/messages/newMessage'
        payload = {'messageTitle': messageTitle, 'messageBody':messageBody}
        r = requests.post(url, data=payload)
        return r.text

    def clearError_collectionSystemTransfer(self, collectionSystemTransferID, jobStatus):

        if jobStatus == "3":
            # Clear Error for current tranfer in DB via API
            url = self.config['siteRoot'] + 'api/collectionSystemTransfers/setIdleCollectionSystemTransfer/' + collectionSystemTransferID
            r = requests.get(url)
            
            
    def clearError_cruiseDataTransfer(self, cruiseDataTransferID, jobStatus):

        if jobStatus == "3":
            # Clear Error for current tranfer in DB via API
            url = self.config['siteRoot'] + 'api/cruiseDataTransfers/setIdleCruiseDataTransfer/' + cruiseDataTransferID
            r = requests.get(url)
            
            
    def clearError_task(self, taskID):
        
        task = self.getTask(taskID)
        
        if task['status'] == '3':
            self.setIdle_task(taskID)
            
    
    def setError_collectionSystemTransfer(self, collectionSystemTransferID, reason=''):

        # Set Error for current tranfer in DB via API
        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/setErrorCollectionSystemTransfer/' + collectionSystemTransferID
        r = requests.get(url)
    
        collectionSystemTransferName = self.getCollectionSystemTransfer(collectionSystemTransferID)['name']
        
        title = collectionSystemTransferName + ' Data Transfer failed'
            
        self.sendMsg(title, reason)
    
    
    def setError_collectionSystemTransferTest(self, collectionSystemTransferID, reason=''):

        # Set Error for current tranfer test in DB via API
        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/setErrorCollectionSystemTransfer/' + collectionSystemTransferID
        r = requests.get(url)
        
        collectionSystemTransferName = self.getCollectionSystemTransfer(collectionSystemTransferID)['name']
        
        title = collectionSystemTransferName + ' Connection test failed'
            
        self.sendMsg(title, reason)

    
    def setError_cruiseDataTransfer(self, cruiseDataTransferID, reason=''):

        # Set Error for current tranfer in DB via API
        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/setErrorCruiseDataTransfer/' + cruiseDataTransferID
        r = requests.get(url)
    
        cruiseDataTransferName = self.getCruiseDataTransfer(cruiseDataTransferID)['name']
        title = cruiseDataTransferName + ' Data Transfer failed'
        
        self.sendMsg(title, reason)
        
        
    def setError_cruiseDataTransferTest(self, cruiseDataTransferID, reason = ''):

        # Set Error for current tranfer test in DB via API
        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/setErrorCruiseDataTransfer/' + cruiseDataTransferID
        r = requests.get(url)
        
        cruiseDataTransferName = self.getCruiseDataTransfer(cruiseDataTransferID)['name']
        title = cruiseDataTransferName + ' Connection test failed'
           
        self.sendMsg(title, reason)
        
            
    def setError_task(self, taskID, reason=''):
       
        # Set Error for current task in DB via API
        url = self.config['siteRoot'] + 'api/tasks/setErrorTask/' + taskID
        r = requests.get(url)
    
        taskName = self.getTask(taskID)['longName']
        title = taskName + ' failed'
        
        self.sendMsg(title, reason)
        
    
    def setIdle_collectionSystemTransfer(self, collectionSystemTransferID):

        # Set Error for current tranfer in DB via API
        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/setIdleCollectionSystemTransfer/' + collectionSystemTransferID
        r = requests.get(url) 
        
    
    def setIdle_cruiseDataTransfer(self, cruiseDataTransferID):

        # Set Error for current tranfer in DB via API
        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/setIdleCruiseDataTransfer/' + cruiseDataTransferID
        r = requests.get(url) 

    
    def setIdle_task(self, taskID):
        
        # Set Idle for the tasks in DB via API
        url = self.config['siteRoot'] + 'api/tasks/setIdleTask/' + taskID
        r = requests.get(url)
    
    
    def setRunning_collectionSystemTransfer(self, collectionSystemTransferID, jobPID, jobHandle):
        
        collectionSystemTransferName = self.getCollectionSystemTransfer(collectionSystemTransferID)['name']

        #print "Set Running for current tranfer in DB via API"
        url = self.config['siteRoot'] + 'api/collectionSystemTransfers/setRunningCollectionSystemTransfer/' + collectionSystemTransferID
        payload = {'jobPid': jobPID}
        r = requests.post(url, data=payload)

        # Add to gearman job tracker
        self.trackGearmanJob('Transfer for ' + collectionSystemTransferName, jobPID, jobHandle)        

    
    def setRunning_collectionSystemTransferTest(self, collectionSystemTransferID, jobPID, jobHandle):

        collectionSystemTransferName = self.getCollectionSystemTransfer(collectionSystemTransferID)['name']
        
        # Add to gearman job tracker
        self.trackGearmanJob('Transfer test for ' + collectionSystemTransferName, jobPID, jobHandle)  
        
    
    def setRunning_cruiseDataTransfer(self, cruiseDataTransferID, jobPID, jobHandle):
        
        cruiseDataTransferName = self.getCruiseDataTransfer(cruiseDataTransferID)['name']

        #print "Set Running for current tranfer in DB via API"
        url = self.config['siteRoot'] + 'api/cruiseDataTransfers/setRunningCruiseDataTransfer/' + cruiseDataTransferID
        payload = {'jobPid': jobPID}
        r = requests.post(url, data=payload)

        # Add to gearman job tracker
        self.trackGearmanJob('Transfer for ' + cruiseDataTransferName, jobPID, jobHandle) 
        
    
    def setRunning_cruiseDataTransferTest(self, cruiseDataTransferID, jobPID, jobHandle):

        cruiseDataTransferName = self.getCruiseDataTransfer(cruiseDataTransferID)['name']
        
        # Add to gearman job tracker
        self.trackGearmanJob('Transfer test for ' + cruiseDataTransferName, jobPID, jobHandle)  
        
    
    def setRunning_task(self, taskID, jobPID, jobHandle):
        
        taskName = self.getTask(taskID)['longName']
        
        # Set Running for the tasks in DB via API
        url = self.config['siteRoot'] + 'api/tasks/setRunningTask/' + taskID
        payload = {'jobPid': jobPID}
        r = requests.post(url, data=payload)

        # Add to gearman job tracker
        self.trackGearmanJob(taskName, jobPID, jobHandle)        

        
    def trackGearmanJob(self, jobName, jobPID, jobHandle):
        
        # Add Job to DB via API
        url = self.config['siteRoot'] + 'api/gearman/newJob/' + jobHandle
        payload = {'jobName': jobName, 'jobPid': jobPID}
        r = requests.post(url, data=payload)
