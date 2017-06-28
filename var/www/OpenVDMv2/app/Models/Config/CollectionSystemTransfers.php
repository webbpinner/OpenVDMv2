<?php

namespace Models\Config;
use Core\Model;

class CollectionSystemTransfers extends Model {

    public function getCollectionSystemTransfers(){
        return $this->db->select("SELECT * FROM ".PREFIX."CollectionSystemTransfers ORDER BY name");
    }
    
    public function getCollectionSystemTransfersStatuses(){
        return $this->db->select("SELECT collectionSystemTransferID, name, longName, status, enable FROM ".PREFIX."CollectionSystemTransfers ORDER BY name");
    }

    public function getCruiseOnlyCollectionSystemTransfers(){
        return $this->db->select("SELECT * FROM ".PREFIX."CollectionSystemTransfers WHERE cruiseOrLowering = :cruiseOrLowering ORDER BY name", array(':cruiseOrLowering' => 0));
    }

    public function getLoweringOnlyCollectionSystemTransfers(){
        return $this->db->select("SELECT * FROM ".PREFIX."CollectionSystemTransfers WHERE cruiseOrLowering = :cruiseOrLowering ORDER BY name", array(':cruiseOrLowering' => 1));
    }
    
    public function getCollectionSystemTransfer($id){
        return $this->db->select("SELECT * FROM ".PREFIX."CollectionSystemTransfers WHERE collectionSystemTransferID = :id",array(':id' => $id));
    }
    
    public function insertCollectionSystemTransfer($data){
        $this->db->insert(PREFIX."CollectionSystemTransfers",$data);
    }
    
    public function updateCollectionSystemTransfer($data,$where){
        $this->db->update(PREFIX."CollectionSystemTransfers",$data, $where);
    }
    
    public function deleteCollectionSystemTransfer($where){
        $this->db->delete(PREFIX."CollectionSystemTransfers", $where);
    }
    
    public function setErrorCollectionSystemTransfer($id){
        $data = array('status' => '3', 'pid' => '0');
        $where = array('collectionSystemTransferID' => $id);
        $this->db->update(PREFIX."CollectionSystemTransfers",$data, $where);
    }

    public function setRunningCollectionSystemTransfer($id,$pid){
        $data = array('status' => '1', 'pid' => $pid);
        $where = array('collectionSystemTransferID' => $id);
        $this->db->update(PREFIX."CollectionSystemTransfers",$data, $where);
    }

    public function setIdleCollectionSystemTransfer($id){
        $data = array();
        $row = $this->getCollectionSystemTransfer($id);
        if (strcmp($row[0]->enable,'1') === 0) {
            $data = array('status' => '2', 'pid' => '0');
        } else {
            $data = array('status' => '4', 'pid' => '0');
        }
        $where = array('collectionSystemTransferID' => $id);
        $this->db->update(PREFIX."CollectionSystemTransfers",$data, $where);
    }
    
    public function setOffCollectionSystemTransfer($id){
        $data = array();
        $row = $this->getCollectionSystemTransfer($id);
        if (strcmp($row[0]->status,'2') === 0) {
            $data['status'] = '4';
        }
        $where = array('collectionSystemTransferID' => $id);
        $this->db->update(PREFIX."CollectionSystemTransfers",$data, $where);
    }
    
    public function enableCollectionSystemTransfer($id){
        $data = array('enable' => 1);
        $row = $this->getCollectionSystemTransfer($id);
        if (strcmp($row[0]->status,'4') === 0) {
            $data['status'] = '2';
        }
        $where = array('collectionSystemTransferID' => $id);
        $this->db->update(PREFIX."CollectionSystemTransfers",$data, $where);
    }
    
    public function disableCollectionSystemTransfer($id){
        $data = array('enable' => 0); 
        $row = $this->getCollectionSystemTransfer($id);
        if (strcmp($row[0]->status,'2') === 0) {
            $data['status'] = '4';
        }
        $where = array('collectionSystemTransferID' => $id);
        $this->db->update(PREFIX."CollectionSystemTransfers",$data, $where);
    }
    
    public function getCollectionSystemTransfersConfig(){
        return $this->db->select("SELECT * FROM ".PREFIX."CollectionSystemTransfers ORDER BY collectionSystemTransferID");
    }
}