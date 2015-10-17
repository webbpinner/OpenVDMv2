# ************************************************************
# Sequel Pro SQL dump
# Version 4499
#
# http://www.sequelpro.com/
# https://github.com/sequelpro/sequelpro
#
# Host: 127.0.0.1 (MySQL 5.5.44-0ubuntu0.14.04.1)
# Database: OpenVDMv2
# Generation Time: 2015-10-17 10:33:19 +0000
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
  `sourceDir` tinytext,
  `destDir` tinytext,
  `staleness` int(11) DEFAULT '0',
  `useStartDate` tinyint(1) DEFAULT '0',
  `transferType` int(11) unsigned NOT NULL,
  `rsyncServer` tinytext,
  `rsyncUseSSH` tinyint(1) DEFAULT '0',
  `rsyncUser` tinytext,
  `rsyncPass` tinytext,
  `smbServer` tinytext,
  `smbUser` tinytext,
  `smbPass` tinytext,
  `smbDomain` tinytext,
  `includeFilter` text,
  `excludeFilter` text,
  `ignoreFilter` text,
  `status` int(11) unsigned NOT NULL DEFAULT '3',
  `enable` tinyint(1) NOT NULL DEFAULT '0',
  `pid` int(11) unsigned DEFAULT '0',
  PRIMARY KEY (`collectionSystemTransferID`),
  KEY `CollectionSystemTransferStatus` (`status`),
  KEY `CollectionSystemTransferType` (`transferType`),
  CONSTRAINT `CollectionSystemTransferStatus` FOREIGN KEY (`status`) REFERENCES `ODVM_Status` (`statusID`),
  CONSTRAINT `CollectionSystemTransferType` FOREIGN KEY (`transferType`) REFERENCES `OVDM_TransferTypes` (`transferTypeID`)
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8;

LOCK TABLES `OVDM_CollectionSystemTransfers` WRITE;
/*!40000 ALTER TABLE `OVDM_CollectionSystemTransfers` DISABLE KEYS */;

INSERT INTO `OVDM_CollectionSystemTransfers` (`collectionSystemTransferID`, `name`, `longName`, `sourceDir`, `destDir`, `staleness`, `useStartDate`, `transferType`, `rsyncServer`, `rsyncUseSSH`, `rsyncUser`, `rsyncPass`, `smbServer`, `smbUser`, `smbPass`, `smbDomain`, `includeFilter`, `excludeFilter`, `ignoreFilter`, `status`, `enable`, `pid`)
VALUES
	(9,'SCS','SCS Underway Data Logger','/','SCS',0,0,3,'',0,'','','//192.168.1.15/SCS','survey','Tethys337813','WORKGROUP','*','','',2,1,0),
	(13,'EK60','EK60 Single-beam echo sounder','/','EK60/RAW/{cruiseID}',0,0,3,'',0,'','','//192.168.1.15/EK60','survey','Tethys337813','WORKGROUP','*.raw','','test.txt',2,1,0),
	(14,'EM302','EM302 Multibeam Mapping System','/','EM302',5,0,3,'',0,'','','//192.168.1.15/EM302','survey','Tethys337813','WORKGROUP','*.tif','','',2,1,0),
	(15,'OS75','Ocean Surveyer 75kHz ADCP','/','OS75',0,0,3,'',0,'','','//192.168.1.12/OS75','survey','Tethys337813','WORKGROUP','*','','',3,0,0),
	(16,'WH300','Workhorse 300kHz ADCP','/mnt/sensors/WH300','WH300',0,0,1,'',0,'','','','','','','*','','',3,0,0),
	(17,'CTD','SBE 911+ CTD','/mnt/sensors/ctd','CTD',5,0,3,'',0,'','','//192.168.1.15/CTD','survey','Tethys337813','WORKGROUP','*','','',3,0,0),
	(19,'XBT','Sippican MK21 XBT (via rsync daemon)','/','XBT',0,0,2,'192.168.1.15/XBT',0,'survey','Tethys337813','','','','','*XBT[0-9][0-9][0-9]*','','',2,1,0),
	(20,'TSAL','Thermo-salinigraph','/mnt/sensors/TSAL','tsal',5,0,1,'',0,'','','','','','','*','','',3,0,0),
	(22,'XBT2','Sippican MK21 XBT (via rsync w/ ssh auth)','/home/survey/data/XBT','XBT_sshAuthentication',0,0,2,'192.168.1.15',1,'survey','Tethys337813','','','','','*XBT[0-9][0-9][0-9]*','','',2,1,0),
	(23,'XBT3','Sippican MK21 XBT (via anonymous rsync)','/','XBT_anonymousRsync',0,0,2,'192.168.1.15/XBT_PUB',0,'anonymous','','','','','','*XBT[0-9][0-9][0-9]*','','',2,1,0);

/*!40000 ALTER TABLE `OVDM_CollectionSystemTransfers` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table OVDM_CoreVars
# ------------------------------------------------------------

DROP TABLE IF EXISTS `OVDM_CoreVars`;

CREATE TABLE `OVDM_CoreVars` (
  `coreVarID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` tinytext NOT NULL,
  `value` tinytext,
  PRIMARY KEY (`coreVarID`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8;

LOCK TABLES `OVDM_CoreVars` WRITE;
/*!40000 ALTER TABLE `OVDM_CoreVars` DISABLE KEYS */;

INSERT INTO `OVDM_CoreVars` (`coreVarID`, `name`, `value`)
VALUES
	(1,'shipboardDataWarehouseIP','192.168.1.6'),
	(2,'shipboardDataWarehouseBaseDir','/mnt/vault/FTPRoot/CruiseData'),
	(3,'shipboardDataWarehouseUsername','survey'),
	(4,'shipboardDataWarehousePublicDataDir','/mnt/vault/FTPRoot/PublicData'),
	(5,'shipboardDataWarehouseStatus','2'),
	(6,'cruiseID','CS1501'),
	(7,'cruiseStartDate','10/16/2015'),
	(8,'systemStatus','On'),
	(9,'shipToShoreBWLimit','128'),
	(10,'shipToShoreBWLimitStatus','On'),
	(11,'md5FilesizeLimit','10'),
	(12,'md5FilesizeLimitStatus','On');

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
  `rsyncServer` tinytext,
  `rsyncUser` tinytext,
  `rsyncPass` tinytext,
  `smbServer` tinytext,
  `smbUser` tinytext,
  `smbPass` tinytext,
  `smbDomain` tinytext,
  `status` int(11) unsigned NOT NULL DEFAULT '3',
  `enable` tinyint(1) NOT NULL DEFAULT '0',
  `required` tinyint(1) NOT NULL DEFAULT '0',
  `pid` int(11) unsigned DEFAULT '0',
  PRIMARY KEY (`cruiseDataTransferID`),
  KEY `CruiseDataTransferStatus` (`status`),
  KEY `CruiseDataTransferType` (`transferType`),
  CONSTRAINT `CruiseDataTransferStatus` FOREIGN KEY (`status`) REFERENCES `ODVM_Status` (`statusID`),
  CONSTRAINT `CruiseDataTransferType` FOREIGN KEY (`transferType`) REFERENCES `OVDM_TransferTypes` (`transferTypeID`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;

LOCK TABLES `OVDM_CruiseDataTransfers` WRITE;
/*!40000 ALTER TABLE `OVDM_CruiseDataTransfers` DISABLE KEYS */;

INSERT INTO `OVDM_CruiseDataTransfers` (`cruiseDataTransferID`, `name`, `longName`, `transferType`, `destDir`, `rsyncServer`, `rsyncUser`, `rsyncPass`, `smbServer`, `smbUser`, `smbPass`, `smbDomain`, `status`, `enable`, `required`, `pid`)
VALUES
	(1,'SSDW','Shoreside Data Warehouse',2,'/mnt/vault/shoreside','192.168.1.6','survey','Tethys337813','','','','',2,1,1,0),
	(2,'SBDA','Shipboard Data Archive (SMB Share)',3,'/','192.168.1.5','survey','Tethys337813','//192.168.1.5/ShipArchive','survey','Tethys337813','WORKGROUP',2,1,0,0),
	(3,'USBhd','USB HDD for P.I. (Local Directory)',1,'/media/survey/MyBackupHDD','','','','','','','',2,1,0,0),
	(4,'RemoteBackup','Remote Backup (Rsync Server)',2,'/mnt/vault/archive','192.168.1.4','survey','Tethys337813','','','','',4,0,0,0);

/*!40000 ALTER TABLE `OVDM_CruiseDataTransfers` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table OVDM_DataDashboardObjects
# ------------------------------------------------------------

DROP TABLE IF EXISTS `OVDM_DataDashboardObjects`;

CREATE TABLE `OVDM_DataDashboardObjects` (
  `dataDashboardObjectID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `dataDashboardObjectFile` varchar(128) DEFAULT NULL,
  `dataDashboardObjectType` varchar(24) DEFAULT NULL,
  `dataDashboardObjectCruise` varchar(24) DEFAULT NULL,
  `dataDashboardRawFile` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`dataDashboardObjectID`)
) ENGINE=InnoDB AUTO_INCREMENT=802 DEFAULT CHARSET=utf8;

LOCK TABLES `OVDM_DataDashboardObjects` WRITE;
/*!40000 ALTER TABLE `OVDM_DataDashboardObjects` DISABLE KEYS */;

INSERT INTO `OVDM_DataDashboardObjects` (`dataDashboardObjectID`, `dataDashboardObjectFile`, `dataDashboardObjectType`, `dataDashboardObjectCruise`, `dataDashboardRawFile`)
VALUES
	(637,'CS1505/OpenVDM/DashboardData/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.json','geotiff','CS1505','CS1505/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.tif'),
	(638,'CS1505/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120428-000000.json','met','CS1505','CS1505/SCS/METOC/MET-M01_20120428-000000.Raw'),
	(639,'CS1505/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120429-000000.json','met','CS1505','CS1505/SCS/METOC/MET-M01_20120429-000000.Raw'),
	(640,'CS1505/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120428-000000.json','svp','CS1505','CS1505/SCS/METOC/Sound-Velocity-Probe_20120428-000000.Raw'),
	(641,'CS1505/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120429-000000.json','svp','CS1505','CS1505/SCS/METOC/Sound-Velocity-Probe_20120429-000000.Raw'),
	(642,'CS1505/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120428-000000.json','tsg','CS1505','CS1505/SCS/METOC/TSG-RAW_20120428-000000.Raw'),
	(643,'CS1505/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120429-000000.json','tsg','CS1505','CS1505/SCS/METOC/TSG-RAW_20120429-000000.Raw'),
	(644,'CS1505/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120428-000000.json','twind','CS1505','CS1505/SCS/METOC/TrueWind-RAW_20120428-000000.Raw'),
	(645,'CS1505/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120429-000000.json','twind','CS1505','CS1505/SCS/METOC/TrueWind-RAW_20120429-000000.Raw'),
	(646,'CS1505/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120428-000000.json','gga','CS1505','CS1505/SCS/NAV/POSMV-GGA_20120428-000000.Raw'),
	(647,'CS1505/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120429-000000.json','gga','CS1505','CS1505/SCS/NAV/POSMV-GGA_20120429-000000.Raw'),
	(659,'CS1507/OpenVDM/DashboardData/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.json','geotiff','CS1507','CS1507/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.tif'),
	(660,'CS1507/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120428-000000.json','met','CS1507','CS1507/SCS/METOC/MET-M01_20120428-000000.Raw'),
	(661,'CS1507/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120429-000000.json','met','CS1507','CS1507/SCS/METOC/MET-M01_20120429-000000.Raw'),
	(662,'CS1507/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120428-000000.json','svp','CS1507','CS1507/SCS/METOC/Sound-Velocity-Probe_20120428-000000.Raw'),
	(663,'CS1507/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120429-000000.json','svp','CS1507','CS1507/SCS/METOC/Sound-Velocity-Probe_20120429-000000.Raw'),
	(664,'CS1507/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120428-000000.json','tsg','CS1507','CS1507/SCS/METOC/TSG-RAW_20120428-000000.Raw'),
	(665,'CS1507/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120429-000000.json','tsg','CS1507','CS1507/SCS/METOC/TSG-RAW_20120429-000000.Raw'),
	(666,'CS1507/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120428-000000.json','twind','CS1507','CS1507/SCS/METOC/TrueWind-RAW_20120428-000000.Raw'),
	(667,'CS1507/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120429-000000.json','twind','CS1507','CS1507/SCS/METOC/TrueWind-RAW_20120429-000000.Raw'),
	(668,'CS1507/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120428-000000.json','gga','CS1507','CS1507/SCS/NAV/POSMV-GGA_20120428-000000.Raw'),
	(669,'CS1507/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120429-000000.json','gga','CS1507','CS1507/SCS/NAV/POSMV-GGA_20120429-000000.Raw'),
	(670,'CS1508/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120428-000000.json','svp','CS1508','CS1508/SCS/METOC/Sound-Velocity-Probe_20120428-000000.Raw'),
	(671,'CS1508/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120429-000000.json','svp','CS1508','CS1508/SCS/METOC/Sound-Velocity-Probe_20120429-000000.Raw'),
	(672,'CS1508/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120428-000000.json','tsg','CS1508','CS1508/SCS/METOC/TSG-RAW_20120428-000000.Raw'),
	(673,'CS1508/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120429-000000.json','tsg','CS1508','CS1508/SCS/METOC/TSG-RAW_20120429-000000.Raw'),
	(674,'CS1508/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120428-000000.json','twind','CS1508','CS1508/SCS/METOC/TrueWind-RAW_20120428-000000.Raw'),
	(675,'CS1508/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120429-000000.json','twind','CS1508','CS1508/SCS/METOC/TrueWind-RAW_20120429-000000.Raw'),
	(676,'CS1508/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120428-000000.json','gga','CS1508','CS1508/SCS/NAV/POSMV-GGA_20120428-000000.Raw'),
	(677,'CS1508/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120429-000000.json','gga','CS1508','CS1508/SCS/NAV/POSMV-GGA_20120429-000000.Raw'),
	(678,'CS1508/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120428-000000.json','met','CS1508','CS1508/SCS/METOC/MET-M01_20120428-000000.Raw'),
	(679,'CS1508/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120429-000000.json','met','CS1508','CS1508/SCS/METOC/MET-M01_20120429-000000.Raw'),
	(680,'CS1508/OpenVDM/DashboardData/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.json','geotiff','CS1508','CS1508/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.tif'),
	(681,'CS1509/OpenVDM/DashboardData/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.json','geotiff','CS1509','CS1509/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.tif'),
	(682,'CS1509/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120428-000000.json','gga','CS1509','CS1509/SCS/NAV/POSMV-GGA_20120428-000000.Raw'),
	(683,'CS1509/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120429-000000.json','gga','CS1509','CS1509/SCS/NAV/POSMV-GGA_20120429-000000.Raw'),
	(684,'CS1509/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120428-000000.json','twind','CS1509','CS1509/SCS/METOC/TrueWind-RAW_20120428-000000.Raw'),
	(685,'CS1509/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120429-000000.json','svp','CS1509','CS1509/SCS/METOC/Sound-Velocity-Probe_20120429-000000.Raw'),
	(686,'CS1509/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120428-000000.json','met','CS1509','CS1509/SCS/METOC/MET-M01_20120428-000000.Raw'),
	(687,'CS1509/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120429-000000.json','met','CS1509','CS1509/SCS/METOC/MET-M01_20120429-000000.Raw'),
	(688,'CS1509/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120428-000000.json','svp','CS1509','CS1509/SCS/METOC/Sound-Velocity-Probe_20120428-000000.Raw'),
	(689,'CS1509/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120428-000000.json','tsg','CS1509','CS1509/SCS/METOC/TSG-RAW_20120428-000000.Raw'),
	(690,'CS1509/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120429-000000.json','tsg','CS1509','CS1509/SCS/METOC/TSG-RAW_20120429-000000.Raw'),
	(691,'CS1509/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120429-000000.json','twind','CS1509','CS1509/SCS/METOC/TrueWind-RAW_20120429-000000.Raw'),
	(692,'CS1510/OpenVDM/DashboardData/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.json','geotiff','CS1510','CS1510/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.tif'),
	(693,'CS1510/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120428-000000.json','met','CS1510','CS1510/SCS/METOC/MET-M01_20120428-000000.Raw'),
	(694,'CS1510/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120429-000000.json','met','CS1510','CS1510/SCS/METOC/MET-M01_20120429-000000.Raw'),
	(695,'CS1510/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120428-000000.json','svp','CS1510','CS1510/SCS/METOC/Sound-Velocity-Probe_20120428-000000.Raw'),
	(696,'CS1510/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120429-000000.json','svp','CS1510','CS1510/SCS/METOC/Sound-Velocity-Probe_20120429-000000.Raw'),
	(697,'CS1510/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120428-000000.json','tsg','CS1510','CS1510/SCS/METOC/TSG-RAW_20120428-000000.Raw'),
	(698,'CS1510/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120429-000000.json','tsg','CS1510','CS1510/SCS/METOC/TSG-RAW_20120429-000000.Raw'),
	(699,'CS1510/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120428-000000.json','twind','CS1510','CS1510/SCS/METOC/TrueWind-RAW_20120428-000000.Raw'),
	(700,'CS1510/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120429-000000.json','twind','CS1510','CS1510/SCS/METOC/TrueWind-RAW_20120429-000000.Raw'),
	(701,'CS1510/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120428-000000.json','gga','CS1510','CS1510/SCS/NAV/POSMV-GGA_20120428-000000.Raw'),
	(702,'CS1510/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120429-000000.json','gga','CS1510','CS1510/SCS/NAV/POSMV-GGA_20120429-000000.Raw'),
	(703,'12345/OpenVDM/DashboardData/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.json','geotiff','12345','12345/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.tif'),
	(704,'12345/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120428-000000.json','met','12345','12345/SCS/METOC/MET-M01_20120428-000000.Raw'),
	(705,'12345/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120429-000000.json','met','12345','12345/SCS/METOC/MET-M01_20120429-000000.Raw'),
	(706,'12345/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120428-000000.json','svp','12345','12345/SCS/METOC/Sound-Velocity-Probe_20120428-000000.Raw'),
	(707,'12345/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120429-000000.json','svp','12345','12345/SCS/METOC/Sound-Velocity-Probe_20120429-000000.Raw'),
	(708,'12345/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120428-000000.json','tsg','12345','12345/SCS/METOC/TSG-RAW_20120428-000000.Raw'),
	(709,'12345/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120429-000000.json','tsg','12345','12345/SCS/METOC/TSG-RAW_20120429-000000.Raw'),
	(710,'12345/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120428-000000.json','twind','12345','12345/SCS/METOC/TrueWind-RAW_20120428-000000.Raw'),
	(711,'12345/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120429-000000.json','twind','12345','12345/SCS/METOC/TrueWind-RAW_20120429-000000.Raw'),
	(712,'12345/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120428-000000.json','gga','12345','12345/SCS/NAV/POSMV-GGA_20120428-000000.Raw'),
	(713,'12345/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120429-000000.json','gga','12345','12345/SCS/NAV/POSMV-GGA_20120429-000000.Raw'),
	(714,'CS1511/OpenVDM/DashboardData/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.json','geotiff','CS1511','CS1511/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.tif'),
	(715,'CS1511/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120428-000000.json','met','CS1511','CS1511/SCS/METOC/MET-M01_20120428-000000.Raw'),
	(716,'CS1511/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120429-000000.json','met','CS1511','CS1511/SCS/METOC/MET-M01_20120429-000000.Raw'),
	(717,'CS1511/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120428-000000.json','svp','CS1511','CS1511/SCS/METOC/Sound-Velocity-Probe_20120428-000000.Raw'),
	(718,'CS1511/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120429-000000.json','svp','CS1511','CS1511/SCS/METOC/Sound-Velocity-Probe_20120429-000000.Raw'),
	(719,'CS1511/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120428-000000.json','tsg','CS1511','CS1511/SCS/METOC/TSG-RAW_20120428-000000.Raw'),
	(720,'CS1511/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120429-000000.json','tsg','CS1511','CS1511/SCS/METOC/TSG-RAW_20120429-000000.Raw'),
	(721,'CS1511/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120428-000000.json','twind','CS1511','CS1511/SCS/METOC/TrueWind-RAW_20120428-000000.Raw'),
	(722,'CS1511/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120429-000000.json','twind','CS1511','CS1511/SCS/METOC/TrueWind-RAW_20120429-000000.Raw'),
	(723,'CS1511/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120428-000000.json','gga','CS1511','CS1511/SCS/NAV/POSMV-GGA_20120428-000000.Raw'),
	(724,'CS1511/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120429-000000.json','gga','CS1511','CS1511/SCS/NAV/POSMV-GGA_20120429-000000.Raw'),
	(725,'CS1512/OpenVDM/DashboardData/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.json','geotiff','CS1512','CS1512/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.tif'),
	(726,'CS1512/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120428-000000.json','met','CS1512','CS1512/SCS/METOC/MET-M01_20120428-000000.Raw'),
	(727,'CS1512/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120429-000000.json','met','CS1512','CS1512/SCS/METOC/MET-M01_20120429-000000.Raw'),
	(728,'CS1512/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120428-000000.json','svp','CS1512','CS1512/SCS/METOC/Sound-Velocity-Probe_20120428-000000.Raw'),
	(729,'CS1512/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120429-000000.json','svp','CS1512','CS1512/SCS/METOC/Sound-Velocity-Probe_20120429-000000.Raw'),
	(730,'CS1512/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120428-000000.json','tsg','CS1512','CS1512/SCS/METOC/TSG-RAW_20120428-000000.Raw'),
	(731,'CS1512/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120429-000000.json','tsg','CS1512','CS1512/SCS/METOC/TSG-RAW_20120429-000000.Raw'),
	(732,'CS1512/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120428-000000.json','twind','CS1512','CS1512/SCS/METOC/TrueWind-RAW_20120428-000000.Raw'),
	(733,'CS1512/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120429-000000.json','twind','CS1512','CS1512/SCS/METOC/TrueWind-RAW_20120429-000000.Raw'),
	(734,'CS1512/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120428-000000.json','gga','CS1512','CS1512/SCS/NAV/POSMV-GGA_20120428-000000.Raw'),
	(735,'CS1512/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120429-000000.json','gga','CS1512','CS1512/SCS/NAV/POSMV-GGA_20120429-000000.Raw'),
	(736,'CS1514/OpenVDM/DashboardData/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.json','geotiff','CS1514','CS1514/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.tif'),
	(737,'CS1514/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120428-000000.json','met','CS1514','CS1514/SCS/METOC/MET-M01_20120428-000000.Raw'),
	(738,'CS1514/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120429-000000.json','met','CS1514','CS1514/SCS/METOC/MET-M01_20120429-000000.Raw'),
	(739,'CS1514/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120428-000000.json','svp','CS1514','CS1514/SCS/METOC/Sound-Velocity-Probe_20120428-000000.Raw'),
	(740,'CS1514/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120429-000000.json','svp','CS1514','CS1514/SCS/METOC/Sound-Velocity-Probe_20120429-000000.Raw'),
	(741,'CS1514/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120428-000000.json','tsg','CS1514','CS1514/SCS/METOC/TSG-RAW_20120428-000000.Raw'),
	(742,'CS1514/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120429-000000.json','tsg','CS1514','CS1514/SCS/METOC/TSG-RAW_20120429-000000.Raw'),
	(743,'CS1514/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120428-000000.json','twind','CS1514','CS1514/SCS/METOC/TrueWind-RAW_20120428-000000.Raw'),
	(744,'CS1514/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120429-000000.json','twind','CS1514','CS1514/SCS/METOC/TrueWind-RAW_20120429-000000.Raw'),
	(745,'CS1514/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120428-000000.json','gga','CS1514','CS1514/SCS/NAV/POSMV-GGA_20120428-000000.Raw'),
	(746,'CS1514/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120429-000000.json','gga','CS1514','CS1514/SCS/NAV/POSMV-GGA_20120429-000000.Raw'),
	(758,'CS1502/OpenVDM/DashboardData/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.json','geotiff','CS1502','CS1502/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.tif'),
	(759,'CS1502/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120428-000000.json','met','CS1502','CS1502/SCS/METOC/MET-M01_20120428-000000.Raw'),
	(760,'CS1502/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120429-000000.json','met','CS1502','CS1502/SCS/METOC/MET-M01_20120429-000000.Raw'),
	(761,'CS1502/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120428-000000.json','svp','CS1502','CS1502/SCS/METOC/Sound-Velocity-Probe_20120428-000000.Raw'),
	(762,'CS1502/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120429-000000.json','svp','CS1502','CS1502/SCS/METOC/Sound-Velocity-Probe_20120429-000000.Raw'),
	(763,'CS1502/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120428-000000.json','tsg','CS1502','CS1502/SCS/METOC/TSG-RAW_20120428-000000.Raw'),
	(764,'CS1502/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120429-000000.json','tsg','CS1502','CS1502/SCS/METOC/TSG-RAW_20120429-000000.Raw'),
	(765,'CS1502/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120428-000000.json','twind','CS1502','CS1502/SCS/METOC/TrueWind-RAW_20120428-000000.Raw'),
	(766,'CS1502/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120429-000000.json','twind','CS1502','CS1502/SCS/METOC/TrueWind-RAW_20120429-000000.Raw'),
	(767,'CS1502/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120428-000000.json','gga','CS1502','CS1502/SCS/NAV/POSMV-GGA_20120428-000000.Raw'),
	(768,'CS1502/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120429-000000.json','gga','CS1502','CS1502/SCS/NAV/POSMV-GGA_20120429-000000.Raw'),
	(769,'CS1503/OpenVDM/DashboardData/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.json','geotiff','CS1503','CS1503/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.tif'),
	(770,'CS1503/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120428-000000.json','svp','CS1503','CS1503/SCS/METOC/Sound-Velocity-Probe_20120428-000000.Raw'),
	(771,'CS1503/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120429-000000.json','svp','CS1503','CS1503/SCS/METOC/Sound-Velocity-Probe_20120429-000000.Raw'),
	(772,'CS1503/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120428-000000.json','tsg','CS1503','CS1503/SCS/METOC/TSG-RAW_20120428-000000.Raw'),
	(773,'CS1503/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120429-000000.json','tsg','CS1503','CS1503/SCS/METOC/TSG-RAW_20120429-000000.Raw'),
	(774,'CS1503/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120428-000000.json','twind','CS1503','CS1503/SCS/METOC/TrueWind-RAW_20120428-000000.Raw'),
	(775,'CS1503/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120429-000000.json','twind','CS1503','CS1503/SCS/METOC/TrueWind-RAW_20120429-000000.Raw'),
	(776,'CS1503/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120428-000000.json','gga','CS1503','CS1503/SCS/NAV/POSMV-GGA_20120428-000000.Raw'),
	(777,'CS1503/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120429-000000.json','gga','CS1503','CS1503/SCS/NAV/POSMV-GGA_20120429-000000.Raw'),
	(778,'CS1503/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120428-000000.json','met','CS1503','CS1503/SCS/METOC/MET-M01_20120428-000000.Raw'),
	(779,'CS1503/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120429-000000.json','met','CS1503','CS1503/SCS/METOC/MET-M01_20120429-000000.Raw'),
	(780,'CS1506/OpenVDM/DashboardData/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.json','geotiff','CS1506','CS1506/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.tif'),
	(781,'CS1506/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120428-000000.json','met','CS1506','CS1506/SCS/METOC/MET-M01_20120428-000000.Raw'),
	(782,'CS1506/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120429-000000.json','met','CS1506','CS1506/SCS/METOC/MET-M01_20120429-000000.Raw'),
	(783,'CS1506/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120428-000000.json','svp','CS1506','CS1506/SCS/METOC/Sound-Velocity-Probe_20120428-000000.Raw'),
	(784,'CS1506/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120429-000000.json','svp','CS1506','CS1506/SCS/METOC/Sound-Velocity-Probe_20120429-000000.Raw'),
	(785,'CS1506/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120428-000000.json','tsg','CS1506','CS1506/SCS/METOC/TSG-RAW_20120428-000000.Raw'),
	(786,'CS1506/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120429-000000.json','tsg','CS1506','CS1506/SCS/METOC/TSG-RAW_20120429-000000.Raw'),
	(787,'CS1506/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120428-000000.json','twind','CS1506','CS1506/SCS/METOC/TrueWind-RAW_20120428-000000.Raw'),
	(788,'CS1506/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120429-000000.json','twind','CS1506','CS1506/SCS/METOC/TrueWind-RAW_20120429-000000.Raw'),
	(789,'CS1506/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120428-000000.json','gga','CS1506','CS1506/SCS/NAV/POSMV-GGA_20120428-000000.Raw'),
	(790,'CS1506/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120429-000000.json','gga','CS1506','CS1506/SCS/NAV/POSMV-GGA_20120429-000000.Raw'),
	(791,'CS1501/OpenVDM/DashboardData/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.json','geotiff','CS1501','CS1501/EM302/proc/CS1401_MB_DLY01_50m_WGS84_20120428.tif'),
	(792,'CS1501/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120428-000000.json','met','CS1501','CS1501/SCS/METOC/MET-M01_20120428-000000.Raw'),
	(793,'CS1501/OpenVDM/DashboardData/SCS/METOC/MET-M01_20120429-000000.json','met','CS1501','CS1501/SCS/METOC/MET-M01_20120429-000000.Raw'),
	(794,'CS1501/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120428-000000.json','svp','CS1501','CS1501/SCS/METOC/Sound-Velocity-Probe_20120428-000000.Raw'),
	(795,'CS1501/OpenVDM/DashboardData/SCS/METOC/Sound-Velocity-Probe_20120429-000000.json','svp','CS1501','CS1501/SCS/METOC/Sound-Velocity-Probe_20120429-000000.Raw'),
	(796,'CS1501/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120428-000000.json','tsg','CS1501','CS1501/SCS/METOC/TSG-RAW_20120428-000000.Raw'),
	(797,'CS1501/OpenVDM/DashboardData/SCS/METOC/TSG-RAW_20120429-000000.json','tsg','CS1501','CS1501/SCS/METOC/TSG-RAW_20120429-000000.Raw'),
	(798,'CS1501/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120428-000000.json','twind','CS1501','CS1501/SCS/METOC/TrueWind-RAW_20120428-000000.Raw'),
	(799,'CS1501/OpenVDM/DashboardData/SCS/METOC/TrueWind-RAW_20120429-000000.json','twind','CS1501','CS1501/SCS/METOC/TrueWind-RAW_20120429-000000.Raw'),
	(800,'CS1501/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120428-000000.json','gga','CS1501','CS1501/SCS/NAV/POSMV-GGA_20120428-000000.Raw'),
	(801,'CS1501/OpenVDM/DashboardData/SCS/NAV/POSMV-GGA_20120429-000000.json','gga','CS1501','CS1501/SCS/NAV/POSMV-GGA_20120429-000000.Raw');

/*!40000 ALTER TABLE `OVDM_DataDashboardObjects` ENABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8;

LOCK TABLES `OVDM_ExtraDirectories` WRITE;
/*!40000 ALTER TABLE `OVDM_ExtraDirectories` DISABLE KEYS */;

INSERT INTO `OVDM_ExtraDirectories` (`extraDirectoryID`, `name`, `longName`, `destDir`, `enable`, `required`)
VALUES
	(1,'Transfer Logs','Transfer Logs','OpenVDM/TransferLogs',1,1),
	(2,'Dashboard Data','Dashboard Data','OpenVDM/DashboardData',1,1),
	(3,'Science','Misc. cruise docs, pictures and data. ','Science',1,1),
	(4,'Products','Cruise Products','Products',1,0),
	(5,'r2r','Rolling Deck to Repository','r2r',1,0);

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
) ENGINE=InnoDB AUTO_INCREMENT=5292 DEFAULT CHARSET=utf8;



# Dump of table OVDM_Messages
# ------------------------------------------------------------

DROP TABLE IF EXISTS `OVDM_Messages`;

CREATE TABLE `OVDM_Messages` (
  `messageID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `message` tinytext NOT NULL,
  `messageTS` datetime NOT NULL,
  `messageViewed` tinyint(1) NOT NULL,
  PRIMARY KEY (`messageID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table OVDM_RecentData
# ------------------------------------------------------------

DROP TABLE IF EXISTS `OVDM_RecentData`;

CREATE TABLE `OVDM_RecentData` (
  `recentDataID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `recentDataName` varchar(255) DEFAULT NULL,
  `recentDataUnit` varchar(24) DEFAULT NULL,
  `recentDataValue` varchar(32) DEFAULT NULL,
  `recentDataDataObjectID` int(11) unsigned DEFAULT NULL,
  `recentDataType` varchar(24) DEFAULT NULL,
  `recentDataDateTime` varchar(16) DEFAULT NULL,
  PRIMARY KEY (`recentDataID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



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
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8;

LOCK TABLES `OVDM_ShipToShoreTransfers` WRITE;
/*!40000 ALTER TABLE `OVDM_ShipToShoreTransfers` DISABLE KEYS */;

INSERT INTO `OVDM_ShipToShoreTransfers` (`shipToShoreTransferID`, `name`, `longName`, `priority`, `collectionSystem`, `extraDirectory`, `includeFilter`, `enable`, `required`)
VALUES
	(1,'DashboardData','Dashboard Data',1,0,2,'*',1,1),
	(2,'TransferLogs','Transfer Logs',1,0,1,'*',0,1),
	(3,'MD5Summary','MD5 Summary',1,0,0,'MD5_Summary.txt MD5_Summary.md5 ',1,1),
	(4,'OVDM_Config','OpenVDM Configuration',1,0,0,'ovdmConfig.json',1,1),
	(5,'KML_Files','KML Files from Cruise Products',2,0,4,'*.kml',0,0),
	(6,'SCS_Met','SCS Met Data',2,9,0,'METOC/*.Raw NAV/*.Raw',0,0),
	(7,'All_GGA_Files','All GGA Files',1,9,0,'*GGA*.raw',0,0);

/*!40000 ALTER TABLE `OVDM_ShipToShoreTransfers` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table OVDM_Tasks
# ------------------------------------------------------------

DROP TABLE IF EXISTS `OVDM_Tasks`;

CREATE TABLE `OVDM_Tasks` (
  `taskID` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` tinytext NOT NULL,
  `longName` tinytext NOT NULL,
  `status` int(11) unsigned NOT NULL DEFAULT '3',
  `enable` tinyint(1) NOT NULL DEFAULT '0',
  `pid` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`taskID`),
  KEY `ProcessStatus` (`status`),
  CONSTRAINT `ProcessStatus` FOREIGN KEY (`status`) REFERENCES `ODVM_Status` (`statusID`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8;

LOCK TABLES `OVDM_Tasks` WRITE;
/*!40000 ALTER TABLE `OVDM_Tasks` DISABLE KEYS */;

INSERT INTO `OVDM_Tasks` (`taskID`, `name`, `longName`, `status`, `enable`, `pid`)
VALUES
	(1,'setupNewCruise','Setup New Cruise',2,1,0),
	(2,'finalizeCurrentCruise','Finalize Current Cruise',2,1,0),
	(3,'rebuildMD5Summary','Rebuild MD5 Summary',2,1,0),
	(4,'rebuildDataDashboard','Rebuild Data Dashboard',2,1,0),
	(5,'rebuildTransferLogSummary','Rebuild Transfer Log Summary',2,1,0),
	(6,'rebuildCruiseDirectory','Rebuild Cruise Directory',2,1,0),
	(7,'exportOVDMConfig','Rebuild the OpenVDM Configuration',2,1,0);

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
	(4,'Remote Push');

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
	(1,'admin','$2y$12$JviETOQPkNzqZxQpswLb1ONtTLxsqdzQJEoaWjlNzb0/.xfIOVM/C','2015-10-16 16:16:29');

/*!40000 ALTER TABLE `OVDM_Users` ENABLE KEYS */;
UNLOCK TABLES;



/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
