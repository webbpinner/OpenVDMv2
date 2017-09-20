# ************************************************************
# Sequel Pro SQL dump
# Version 4541
#
# http://www.sequelpro.com/
# https://github.com/sequelpro/sequelpro
#
# Host: 127.0.0.1 (MySQL 5.7.17-0ubuntu0.16.04.1)
# Database: OpenVDMv2
# Generation Time: 2017-03-26 13:09:58 +0000
# ************************************************************


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


# Dump of table ODVM_Status
# ------------------------------------------------------------

DROP TABLE IF EXISTS `ODVM_Status`;

CREATE TABLE `ODVM_Status` (
  `statusID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `status` tinytext,
  PRIMARY KEY (`statusID`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;

LOCK TABLES `ODVM_Status` WRITE;
/*!40000 ALTER TABLE `ODVM_Status` DISABLE KEYS */;

INSERT INTO `ODVM_Status` (`statusID`, `status`)
VALUES
  (1,'Running'),
  (2,'Idle'),
  (3,'Error'),
  (4,'Off');

/*!40000 ALTER TABLE `ODVM_Status` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table OVDM_CollectionSystemTransfers
# ------------------------------------------------------------

DROP TABLE IF EXISTS `OVDM_CollectionSystemTransfers`;

CREATE TABLE `OVDM_CollectionSystemTransfers` (
  `collectionSystemTransferID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` tinytext NOT NULL,
  `longName` text,
  `cruiseOrLowering` int(1) unsigned NOT NULL DEFAULT '0',
  `sourceDir` tinytext,
  `destDir` tinytext,
  `staleness` int(11) DEFAULT '0',
  `useStartDate` tinyint(1) DEFAULT '0',
  `transferType` int(11) unsigned NOT NULL,
  `localDirIsMountPoint` int(1) unsigned NOT NULL DEFAULT '0',
  `rsyncServer` tinytext,
  `rsyncUser` tinytext,
  `rsyncPass` tinytext,
  `smbServer` tinytext,
  `smbUser` tinytext,
  `smbPass` tinytext,
  `smbDomain` tinytext,
  `sshServer` tinytext,
  `sshUser` tinytext,
  `sshUseKey` int(1) unsigned NOT NULL DEFAULT '0',
  `sshPass` tinytext,
  `nfsServer` tinytext,
  `nfsUser` tinytext,
  `nfsPass` tinytext,
  `includeFilter` text,
  `excludeFilter` text,
  `ignoreFilter` text,
  `status` int(11) unsigned NOT NULL DEFAULT '3',
  `enable` tinyint(1) NOT NULL DEFAULT '0',
  `pid` int(11) unsigned DEFAULT '0',
  `bandwidthLimit` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`collectionSystemTransferID`),
  KEY `CollectionSystemTransferStatus` (`status`),
  KEY `CollectionSystemTransferType` (`transferType`),
  CONSTRAINT `CollectionSystemTransferStatus` FOREIGN KEY (`status`) REFERENCES `ODVM_Status` (`statusID`),
  CONSTRAINT `CollectionSystemTransferType` FOREIGN KEY (`transferType`) REFERENCES `OVDM_TransferTypes` (`transferTypeID`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;


# Dump of table OVDM_CoreVars
# ------------------------------------------------------------

DROP TABLE IF EXISTS `OVDM_CoreVars`;

CREATE TABLE `OVDM_CoreVars` (
  `coreVarID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` tinytext NOT NULL,
  `value` tinytext,
  PRIMARY KEY (`coreVarID`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8;

LOCK TABLES `OVDM_CoreVars` WRITE;
/*!40000 ALTER TABLE `OVDM_CoreVars` DISABLE KEYS */;

INSERT INTO `OVDM_CoreVars` (`coreVarID`, `name`, `value`)
VALUES
  (1,'shipboardDataWarehouseIP','127.0.0.1'),
  (2,'shipboardDataWarehouseUsername','survey'),
  (3,'shipboardDataWarehousePublicDataDir','/vault/FTPRoot/PublicData'),
  (4,'shipboardDataWarehouseStatus','2'),
  (5,'cruiseID','CS1601'),
  (6,'cruiseStartDate','2017/01/01 00:00'),
  (7,'cruiseEndDate',''),
  (8,'loweringID','CS-001'),
  (9,'loweringStartDate','2017/01/01 00:00'),
  (10,'loweringEndDate',''),
  (11,'systemStatus','Off'),
  (12,'shipToShoreBWLimit','128'),
  (13,'shipToShoreBWLimitStatus','Off'),
  (14,'md5FilesizeLimit','10'),
  (15,'md5FilesizeLimitStatus','On'),
  (16,'showLoweringComponents','No');
  

/*!40000 ALTER TABLE `OVDM_CoreVars` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table OVDM_CruiseDataTransfers
# ------------------------------------------------------------

DROP TABLE IF EXISTS `OVDM_CruiseDataTransfers`;

CREATE TABLE `OVDM_CruiseDataTransfers` (
  `cruiseDataTransferID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` tinytext NOT NULL,
  `longName` text,
  `transferType` int(11) unsigned NOT NULL,
  `destDir` tinytext,
  `localDirIsMountPoint` int(1) unsigned NOT NULL DEFAULT '0',
  `rsyncServer` tinytext,
  `rsyncUser` tinytext,
  `rsyncPass` tinytext,
  `smbServer` tinytext,
  `smbUser` tinytext,
  `smbPass` tinytext,
  `smbDomain` tinytext,
  `sshServer` tinytext,
  `sshUser` tinytext,
  `sshUseKey` int(1) unsigned NOT NULL DEFAULT '0',
  `sshPass` tinytext,
  `nfsServer` tinytext,
  `nfsUser` tinytext,
  `nfsPass` tinytext CHARACTER SET utf8 COLLATE utf8_bin,
  `status` int(11) unsigned NOT NULL DEFAULT '3',
  `enable` tinyint(1) NOT NULL DEFAULT '0',
  `required` tinyint(1) NOT NULL DEFAULT '0',
  `pid` int(11) unsigned DEFAULT '0',
  PRIMARY KEY (`cruiseDataTransferID`),
  KEY `CruiseDataTransferStatus` (`status`),
  KEY `CruiseDataTransferType` (`transferType`),
  CONSTRAINT `CruiseDataTransferStatus` FOREIGN KEY (`status`) REFERENCES `ODVM_Status` (`statusID`),
  CONSTRAINT `CruiseDataTransferType` FOREIGN KEY (`transferType`) REFERENCES `OVDM_TransferTypes` (`transferTypeID`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;

LOCK TABLES `OVDM_CruiseDataTransfers` WRITE;
/*!40000 ALTER TABLE `OVDM_CruiseDataTransfers` DISABLE KEYS */;

INSERT INTO `OVDM_CruiseDataTransfers` (`cruiseDataTransferID`, `name`, `longName`, `transferType`, `destDir`, `localDirIsMountPoint`, `rsyncServer`, `rsyncUser`, `rsyncPass`, `smbServer`, `smbUser`, `smbPass`, `smbDomain`, `sshServer`, `sshUser`, `sshUseKey`, `sshPass`, `nfsServer`, `nfsUser`, `nfsPass`, `status`, `enable`, `required`, `pid`)
VALUES
  (1,'SSDW','Shoreside Data Warehouse',4,'/shoreside',0,'','','','','','','','127.0.0.1','survey',1,NULL,NULL,NULL,NULL,2,0,1,0),
  (2,'SBDA','Shipboard NAS (SMB Share)',3,'/',0,'','','','//127.0.0.1/NASBackup','survey','password','WORKGROUP','','',0,'','','','',2,0,0,0),
  (3,'USBhd','USB HDD for P.I. (Local Directory)',1,'/LocalBackup',0,'','','','','','','','','',0,'','',NULL,NULL,2,0,0,0);

/*!40000 ALTER TABLE `OVDM_CruiseDataTransfers` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table OVDM_ExtraDirectories
# ------------------------------------------------------------

DROP TABLE IF EXISTS `OVDM_ExtraDirectories`;

CREATE TABLE `OVDM_ExtraDirectories` (
  `extraDirectoryID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` tinytext NOT NULL,
  `longName` tinytext,
  `destDir` tinytext NOT NULL,
  `enable` tinyint(1) DEFAULT '0',
  `required` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`extraDirectoryID`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;

LOCK TABLES `OVDM_ExtraDirectories` WRITE;
/*!40000 ALTER TABLE `OVDM_ExtraDirectories` DISABLE KEYS */;

INSERT INTO `OVDM_ExtraDirectories` (`extraDirectoryID`, `name`, `longName`, `destDir`, `enable`, `required`)
VALUES
  (1,'Transfer Logs','Transfer Logs','OpenVDM/TransferLogs',1,1),
  (2,'Dashboard Data','Dashboard Data','OpenVDM/DashboardData',1,1),
  (3,'Science','Misc. cruise docs, pictures and data. ','Science',1,1),
  (4,'Tracklines','Cruise Tracklines','Vessel/PROC/Tracklines',0,0);

/*!40000 ALTER TABLE `OVDM_ExtraDirectories` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table OVDM_Gearman
# ------------------------------------------------------------

DROP TABLE IF EXISTS `OVDM_Gearman`;

CREATE TABLE `OVDM_Gearman` (
  `jobID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `jobHandle` tinytext,
  `jobKnown` tinyint(11) unsigned DEFAULT '1',
  `jobRunning` tinyint(11) unsigned DEFAULT '1',
  `jobNumerator` tinyint(11) unsigned DEFAULT '0',
  `jobDenominator` tinyint(11) unsigned DEFAULT '0',
  `jobName` tinytext,
  `jobPid` int(11) unsigned DEFAULT NULL,
  PRIMARY KEY (`jobID`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;


# Dump of table OVDM_Links
# ------------------------------------------------------------

DROP TABLE IF EXISTS `OVDM_Links`;

CREATE TABLE `OVDM_Links` (
  `linkID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` tinytext NOT NULL,
  `url` tinytext NOT NULL,
  `enable` tinyint(1) NOT NULL DEFAULT '0',
  `private` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`linkID`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;

LOCK TABLES `OVDM_Links` WRITE;
/*!40000 ALTER TABLE `OVDM_Links` DISABLE KEYS */;

INSERT INTO `OVDM_Links` (`linkID`, `name`, `url`, `enable`, `private`)
VALUES
  (1,'Supervisord','http://{hostIP}:9001',1,1),
  (2,'Gearman','http://{hostIP}/gearman-ui/',1,1),
  (3,'Cruise Data','http://{hostIP}/CruiseData/{cruiseID}/',1,0),
  (4,'Public Data','http://{hostIP}/PublicData/',1,0),
  (5,'Visitor Information','http://{hostIP}/VisitorInformation/',1,0),
  (6,'MapProxy','http://{hostIP}/mapproxy/demo/',1,0);

/*!40000 ALTER TABLE `OVDM_Links` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table OVDM_Messages
# ------------------------------------------------------------

DROP TABLE IF EXISTS `OVDM_Messages`;

CREATE TABLE `OVDM_Messages` (
  `messageID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `messageTitle` tinytext NOT NULL,
  `messageBody` text,
  `messageTS` datetime NOT NULL,
  `messageViewed` tinyint(1) NOT NULL,
  PRIMARY KEY (`messageID`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;


# Dump of table OVDM_ShipToShoreTransfers
# ------------------------------------------------------------

DROP TABLE IF EXISTS `OVDM_ShipToShoreTransfers`;

CREATE TABLE `OVDM_ShipToShoreTransfers` (
  `shipToShoreTransferID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` tinytext,
  `longName` tinytext,
  `priority` int(11) DEFAULT NULL,
  `collectionSystem` int(11) unsigned DEFAULT NULL,
  `extraDirectory` int(11) unsigned DEFAULT NULL,
  `includeFilter` tinytext,
  `enable` tinyint(1) NOT NULL DEFAULT '0',
  `required` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`shipToShoreTransferID`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;

LOCK TABLES `OVDM_ShipToShoreTransfers` WRITE;
/*!40000 ALTER TABLE `OVDM_ShipToShoreTransfers` DISABLE KEYS */;

INSERT INTO `OVDM_ShipToShoreTransfers` (`shipToShoreTransferID`, `name`, `longName`, `priority`, `collectionSystem`, `extraDirectory`, `includeFilter`, `enable`, `required`)
VALUES
  (1,'DashboardData','Dashboard Data',1,0,2,'*',1,1),
  (2,'TransferLogs','Transfer Logs',1,0,1,'*',0,1),
  (3,'MD5Summary','MD5 Summary',1,0,0,'MD5_Summary.txt MD5_Summary.md5 ',1,1),
  (4,'OVDM_Config','OpenVDM Configuration',1,0,0,'ovdmConfig.json',1,1),
  (5,'Tracklines','Cruise Tracklines',1,0,4,'*',0,0);

/*!40000 ALTER TABLE `OVDM_ShipToShoreTransfers` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table OVDM_Tasks
# ------------------------------------------------------------

DROP TABLE IF EXISTS `OVDM_Tasks`;

CREATE TABLE `OVDM_Tasks` (
  `taskID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` tinytext NOT NULL,
  `longName` tinytext NOT NULL,
  `cruiseOrLowering` tinyint(1) NOT NULL DEFAULT '0',
  `status` int(11) unsigned NOT NULL DEFAULT '3',
  `enable` tinyint(1) NOT NULL DEFAULT '0',
  `pid` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`taskID`),
  KEY `ProcessStatus` (`status`),
  CONSTRAINT `ProcessStatus` FOREIGN KEY (`status`) REFERENCES `ODVM_Status` (`statusID`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8;

LOCK TABLES `OVDM_Tasks` WRITE;
/*!40000 ALTER TABLE `OVDM_Tasks` DISABLE KEYS */;

INSERT INTO `OVDM_Tasks` (`taskID`, `name`, `longName`, `status`, `enable`, `pid`)
VALUES
  (1,'setupNewCruise','Setup New Cruise',0,2,1,0),
  (2,'finalizeCurrentCruise','Finalize Current Cruise',0,2,1,0),
  (3,'rebuildMD5Summary','Rebuild MD5 Summary',0,2,1,0),
  (4,'rebuildDataDashboard','Rebuild Data Dashboard',0,2,1,0),
  (5,'rebuildCruiseDirectory','Rebuild Cruise Directory',0,2,1,0),
  (6,'exportOVDMConfig','Re-export the OpenVDM Configuration',0,2,1,0),
  (7,'rsyncPublicDataToCruiseData','Copy PublicData to Cruise Data',0,2,1,0),
  (8,'setupNewLowering','Setup New Lowering',1,2,1,0),
  (9,'finalizeCurrentCruise','Finalize Current Cruise',1,2,1,0),
  (10,'rebuildLoweringDirectory','Rebuild Lowering Directory',1,2,1,0),
  (11,'exportLoweringConfig','Re-export the Lowering Configuration',1,2,1,0);

/*!40000 ALTER TABLE `OVDM_Tasks` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table OVDM_TransferTypes
# ------------------------------------------------------------

DROP TABLE IF EXISTS `OVDM_TransferTypes`;

CREATE TABLE `OVDM_TransferTypes` (
  `transferTypeID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `transferType` tinytext,
  PRIMARY KEY (`transferTypeID`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;

LOCK TABLES `OVDM_TransferTypes` WRITE;
/*!40000 ALTER TABLE `OVDM_TransferTypes` DISABLE KEYS */;

INSERT INTO `OVDM_TransferTypes` (`transferTypeID`, `transferType`)
VALUES
  (1,'Local Directory'),
  (2,'Rsync Server'),
  (3,'SMB Share'),
  (4,'SSH Server');

/*!40000 ALTER TABLE `OVDM_TransferTypes` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table OVDM_Users
# ------------------------------------------------------------

DROP TABLE IF EXISTS `OVDM_Users`;

CREATE TABLE `OVDM_Users` (
  `userID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(255) DEFAULT '',
  `password` varchar(255) DEFAULT '',
  `lastLogin` datetime DEFAULT NULL,
  PRIMARY KEY (`userID`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

LOCK TABLES `OVDM_Users` WRITE;
/*!40000 ALTER TABLE `OVDM_Users` DISABLE KEYS */;

INSERT INTO `OVDM_Users` (`userID`, `username`, `password`, `lastLogin`)
VALUES
  (1,'admin','$2y$12$JviETOQPkNzqZxQpswLb1ONtTLxsqdzQJEoaWjlNzb0/.xfIOVM/C','2017-03-26 14:06:30');

/*!40000 ALTER TABLE `OVDM_Users` ENABLE KEYS */;
UNLOCK TABLES;



/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
