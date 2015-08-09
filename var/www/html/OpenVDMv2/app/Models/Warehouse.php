<?php

namespace models;
use Core\Model;

class Warehouse extends Model {

    public function getFreeSpace() {
        $baseDir = $this->getShipboardDataWarehouseBaseDir();
        if (is_dir($baseDir)){
            $data['freeSpace'] = disk_free_space($baseDir);
        } else {
            $data['error'] = '(getFreeSpace) Base Directory: ' . $baseDir . ' is not a directory';            
        }
        
        return $data;
    }
    
   	public function getCruiseSize() {
        $baseDir = $this->getShipboardDataWarehouseBaseDir();
        $cruiseID = $this->getCruiseID();
        if (is_dir($baseDir . '/' . $cruiseID)){
            $output = exec('du -sk ' . $baseDir . '/' . $cruiseID);
            $data['cruiseSize'] = trim(str_replace($file_directory, '', $output)) * 1024;
        } else {
            $data['error'] = '(getCruiseSize) Cruise Directory: ' . $baseDir . '/' . $cruiseID . ' is not a directory';            
        }
        
        return $data;
    }

    public function getSystemStatus(){
        $row = $this->db->select("SELECT * FROM ".PREFIX."CoreVars WHERE name = 'systemStatus'");
        if(strcmp($row[0]->value, "On") == 0 ){
            return true;
        } else {
            return false;
        }
    }
    
    public function getShipboardDataWarehouseStatus(){
        $row = $this->db->select("SELECT * FROM ".PREFIX."CoreVars WHERE name = 'shipboardDataWarehouseStatus'");
        return $row[0]->value;
    }
    
    public function getShipToShoreTransferStatus(){
        $row = $this->db->select("SELECT * FROM ".PREFIX."CoreVars WHERE name = 'shipToShoreTransfersStatus'");
        if(strcmp($row[0]->value, "On") == 0 ){
            return true;
        } else {
            return false;
        }
    }
    
    public function getCruiseID(){
        $row = $this->db->select("SELECT * FROM ".PREFIX."CoreVars WHERE name = 'cruiseID'");
        return $row[0]->value;
    }
    
    public function getCruiseStartDate(){
        $row = $this->db->select("SELECT * FROM ".PREFIX."CoreVars WHERE name = 'cruiseStartDate'");
        return $row[0]->value;
    }
    
    public function getShipToShoreBWLimit(){
        $row = $this->db->select("SELECT * FROM ".PREFIX."CoreVars WHERE name = 'shipToShoreBWLimit'");
        return $row[0]->value;
    }
    
    public function getShipToShoreBWLimitStatus(){
        $row = $this->db->select("SELECT * FROM ".PREFIX."CoreVars WHERE name = 'shipToShoreBWLimitStatus'");
        return $row[0]->value;
    }

    public function getMd5FilesizeLimit(){
        $row = $this->db->select("SELECT * FROM ".PREFIX."CoreVars WHERE name = 'md5FilesizeLimit'");
        return $row[0]->value;
    }
    
    public function getMd5FilesizeLimitStatus(){
        $row = $this->db->select("SELECT * FROM ".PREFIX."CoreVars WHERE name = 'md5FilesizeLimitStatus'");
        return $row[0]->value;
    }

    public function getShipboardDataWarehouseBaseDir(){
        $row = $this->db->select("SELECT * FROM ".PREFIX."CoreVars WHERE name = 'shipboardDataWarehouseBaseDir'");
        return $row[0]->value;
    }

     public function getShipboardDataWarehouseConfig(){
         $row = $this->db->select("SELECT * FROM ".PREFIX."CoreVars WHERE name = 'shipboardDataWarehouseIP'");
         $shipboardDataWarehouseIP = $row[0]->value;
         $row = $this->db->select("SELECT * FROM ".PREFIX."CoreVars WHERE name = 'shipboardDataWarehouseBaseDir'"); 
         $shipboardDataWarehouseBaseDir = $row[0]->value;
         $row = $this->db->select("SELECT * FROM ".PREFIX."CoreVars WHERE name = 'shipboardDataWarehouseUsername'");
         $shipboardDataWarehouseUsername = $row[0]->value;
         $row = $this->db->select("SELECT * FROM ".PREFIX."CoreVars WHERE name = 'shipboardDataWarehousePublicDataDir'");
         $shipboardDataWarehousePublicDataDir = $row[0]->value;
         
         return array(
                    'shipboardDataWarehouseIP' => $shipboardDataWarehouseIP,
                    'shipboardDataWarehouseBaseDir' => $shipboardDataWarehouseBaseDir,
                    'shipboardDataWarehouseUsername' => $shipboardDataWarehouseUsername,
                    'shipboardDataWarehousePublicDataDir' => $shipboardDataWarehousePublicDataDir,
         );
    }
    
    public function enableSystem(){
        $data = array('value' => 'On');   
        $where = array('name' => 'systemStatus');
        $this->db->update(PREFIX."CoreVars",$data, $where);
    }

    public function disableSystem(){
        $data = array('value' => 'Off');   
        $where = array('name' => 'systemStatus');
        $this->db->update(PREFIX."CoreVars",$data, $where);
    }
    
    public function enableShipToShoreTransfers(){
        $data = array('value' => 'On');   
        $where = array('name' => 'shipToShoreTransfersStatus');
        $this->db->update(PREFIX."CoreVars",$data, $where);
    }

    public function disableShipToShoreTransfers(){
        $data = array('value' => 'Off');   
        $where = array('name' => 'shipToShoreTransfersStatus');
        $this->db->update(PREFIX."CoreVars",$data, $where);
    }
    
    public function setShipToShoreBWLimit($data){
        $where = array('name' => 'shipToShoreBWLimit');
        $this->db->update(PREFIX."CoreVars",$data, $where);
    }
    
    public function enableShipToShoreBWLimit(){
        $data = array('value' => 'On');   
        $where = array('name' => 'shipToShoreBWLimitStatus');
        $this->db->update(PREFIX."CoreVars",$data, $where);
    }

    public function disableShipToShoreBWLimit(){
        $data = array('value' => 'Off');   
        $where = array('name' => 'shipToShoreBWLimitStatus');
        $this->db->update(PREFIX."CoreVars",$data, $where);
    }

    public function setMd5FilesizeLimit($data){
        $where = array('name' => 'md5FilesizeLimit');
        $this->db->update(PREFIX."CoreVars",$data, $where);
    }
    
    public function enableMd5FilesizeLimit(){
        $data = array('value' => 'On');   
        $where = array('name' => 'md5FilesizeLimitStatus');
        $this->db->update(PREFIX."CoreVars",$data, $where);
    }

    public function disableMd5FilesizeLimit(){
        $data = array('value' => 'Off');   
        $where = array('name' => 'md5FilesizeLimitStatus');
        $this->db->update(PREFIX."CoreVars",$data, $where);
    }

    public function setCruiseID($data){
        $where = array('name' => 'cruiseID');
        $this->db->update(PREFIX."CoreVars",$data, $where);
    }
    
    public function setCruiseStartDate($data){
        $where = array('name' => 'cruiseStartDate');
        $this->db->update(PREFIX."CoreVars",$data, $where);
    }

    public function setShipboardDataWarehouseBaseDir($data){
        $where = array('name' => 'shipbardDataWarehouseBaseDir');
        $this->db->update(PREFIX."CoreVars",$data, $where);
    }
    
    public function setShipboardDataWarehouseConfig($data){
        $where = array('name' => 'shipboardDataWarehouseIP');
        $this->db->update(PREFIX."CoreVars", array('value' => $data['shipboardDataWarehouseIP']), $where);
        $where = array('name' => 'shipboardDataWarehouseBaseDir');
        $this->db->update(PREFIX."CoreVars", array('value' => $data['shipboardDataWarehouseBaseDir']), $where);
        $where = array('name' => 'shipboardDataWarehouseUsername');
        $this->db->update(PREFIX."CoreVars", array('value' => $data['shipboardDataWarehouseUsername']), $where);
    }
    
    public function setErrorShipboardDataWarehouseStatus(){
        $where = array('name' => 'shipboardDataWarehouseStatus');
        $this->db->update(PREFIX."CoreVars", array('value' => '3'), $where);
    }
    
    public function clearErrorShipboardDataWarehouseStatus(){
        $where = array('name' => 'shipboardDataWarehouseStatus');
        $this->db->update(PREFIX."CoreVars", array('value' => '2'), $where);
    } 

}