<?php

namespace Models\Config;
use Core\Model;

class CruiseDataTransfers extends Model {

    public function getCruiseDataTransfers(){
        return $this->db->select("SELECT * FROM ".PREFIX."CruiseDataTransfers WHERE required = :required ORDER BY name", array(':required' => '0'));
    }
    
    public function getCruiseDataTransfersStatuses(){
        return $this->db->select("SELECT cruiseDataTransferID, name, longName, status, enable FROM ".PREFIX."CruiseDataTransfers WHERE required = :required ORDER BY name", array(':required' => '0'));
    }

    public function getRequiredCruiseDataTransfers(){
        return $this->db->select("SELECT * FROM ".PREFIX."CruiseDataTransfers WHERE required = :required ORDER BY name", array(':required' => '1'));
    }
    
    public function getRequiredCruiseDataTransfersStatuses(){
        return $this->db->select("SELECT cruiseDataTransferID, name, longName, status, enable FROM ".PREFIX."CruiseDataTransfers WHERE required = :required ORDER BY name", array(':required' => '1'));
    }
    
    public function getCruiseDataTransfer($id){
        return $this->db->select("SELECT * FROM ".PREFIX."CruiseDataTransfers WHERE cruiseDataTransferID = :id",array(':id' => $id));
    }

    public function getRequiredCruiseDataTransfer($id){
        return $this->db->select("SELECT * FROM ".PREFIX."CruiseDataTransfers WHERE cruiseDataTransferID = :id",array(':id' => $id));
    }
    
    public function insertCruiseDataTransfer($data){
        $this->db->insert(PREFIX."CruiseDataTransfers",$data);
    }
    
    public function updateCruiseDataTransfer($data,$where){
        $this->db->update(PREFIX."CruiseDataTransfers",$data, $where);
    }
    
    public function deleteCruiseDataTransfer($where){
        $cruiseDataTransfer = $this->db->select("SELECT * FROM ".PREFIX."CruiseDataTransfers WHERE cruiseDataTransferID = :id",array(':id' => $where['cruiseDataTransferID']))[0];
        if(strcmp($cruiseDataTransfer->required,'0') === 0 ){
            $this->db->delete(PREFIX."CruiseDataTransfers", $where);
        } 
    }

    public function clearCollectionSystemTransfer($collectionSystemTransferID) {
        $cruiseDataTransfers = $this->db->select("SELECT * FROM ".PREFIX."CruiseDataTransfers");
        foreach ($cruiseDataTransfers as $key => $value) {
            $excludedCollectionSystems = explode(',', $value->excludedCollectionSystems);
            $keyToRemove = array_keys($excludedCollectionSystems,$collectionSystemTransferID);
            if (sizeof($keyToRemove) > 0) {
                unset($excludedCollectionSystems[$keyToRemove[0]]);
                $data = [];
                if (sizeof($excludedCollectionSystems) > 0) {
                    $data = array('excludedCollectionSystems' => join(',',$excludedCollectionSystems));
                } else {
                    $data = array('excludedCollectionSystems' => "0");
                }
                $where = array('cruiseDataTransferID' => $value->cruiseDataTransferID);
                $this->db->update(PREFIX."CruiseDataTransfers",$data, $where);
            }
        }
    }

    public function clearExtraDirectory($extraDirectoryID) {
        $cruiseDataTransfers = $this->db->select("SELECT * FROM ".PREFIX."CruiseDataTransfers");
        foreach ($cruiseDataTransfers as $key => $value) {
            $excludedExtraDirectories = explode(',', $value->excludedExtraDirectories);
            $keyToRemove = array_keys($excludedExtraDirectories,$extraDirectoryID);
            if (sizeof($keyToRemove) > 0) {
                unset($excludedExtraDirectories[$keyToRemove[0]]);
                $data = [];
                if (sizeof($excludedExtraDirectories) > 0) {
                    $data = array('excludedExtraDirectories' => join(',',$excludedExtraDirectories));
                } else {
                    $data = array('excludedExtraDirectories' => "0");
                }
                $where = array('cruiseDataTransferID' => $value->cruiseDataTransferID);
                $this->db->update(PREFIX."CruiseDataTransfers",$data, $where);
            }
        }
    }
    
    public function setErrorCruiseDataTransfer($id){
        $data = array('status' => '3', 'pid' => '0');
        $where = array('cruiseDataTransferID' => $id);
        $this->db->update(PREFIX."CruiseDataTransfers",$data, $where);
    }

    public function setStoppingCruiseDataTransfer($id){
        $data = array('status' => '5');
        $where = array('cruiseDataTransferID' => $id);
        $this->db->update(PREFIX."CruiseDataTransfers",$data, $where);
    }


    public function setStartingCruiseDataTransfer($id){
        $data = array('status' => '6');
        $where = array('cruiseDataTransferID' => $id);
        $this->db->update(PREFIX."CruiseDataTransfers",$data, $where);
    }


    public function setRunningCruiseDataTransfer($id, $pid){
        $data = array('status' => '1', 'pid' => $pid);
        $where = array('cruiseDataTransferID' => $id);
        $this->db->update(PREFIX."CruiseDataTransfers",$data, $where);
    }

    public function setIdleCruiseDataTransfer($id){
//        $data = array();
        $data = array('status' => '2', 'pid' => '0');
        $row = $this->getCruiseDataTransfer($id);
//        if (strcmp($row[0]->enable,'1') === 0) {
//            $data = array('status' => '2', 'pid' => '0');
//        } else {
//            $data = array('status' => '4', 'pid' => '0');
//        }
        $where = array('cruiseDataTransferID' => $id);
        $this->db->update(PREFIX."CruiseDataTransfers",$data, $where);
    }
    
    public function setOffCruiseDataTransfer($id){
//        $data = array();
        $data = array('status' => '4');
        $row = $this->getCruiseDataTransfer($id);
//        if (strcmp($row[0]->status,'2') === 0) {
//            $data = array('status' => '4');
//        }
        $where = array('cruiseDataTransferID' => $id);
        $this->db->update(PREFIX."CruiseDataTransfers",$data, $where);
    }

    
    public function enableCruiseDataTransfer($id){
        $data = array('enable' => 1);
        $row = $this->getCruiseDataTransfer($id);
//        if (strcmp($row[0]->status,'4') === 0) {
//            $data['status'] = '2';
//        }
        $where = array('cruiseDataTransferID' => $id);
        $this->db->update(PREFIX."CruiseDataTransfers",$data, $where);
    }
    
    public function disableCruiseDataTransfer($id){
        $data = array('enable' => 0);
        $row = $this->getCruiseDataTransfer($id);
//        if (strcmp($row[0]->status,'2') === 0) {
//            $data['status'] = '4';
//        }
        $where = array('cruiseDataTransferID' => $id);
        $this->db->update(PREFIX."CruiseDataTransfers",$data, $where);
    }
    
    public function getCruiseDataTransfersConfig(){
        return $this->db->select("SELECT * FROM ".PREFIX."CruiseDataTransfers ORDER BY cruiseDataTransferID");
    }

}
