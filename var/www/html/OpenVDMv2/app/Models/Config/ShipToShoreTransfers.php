<?php

namespace Models\Config;
use Core\Model;

class ShipToShoreTransfers extends Model {

    public function getShipToShoreTransfers(){
        return $this->db->select("SELECT * FROM ".PREFIX."ShipToShoreTransfers WHERE requried = :requried ORDER BY name", array(':requried' => '0'));
    }

    public function getRequiredShipToShoreTransfers(){
        return $this->db->select("SELECT * FROM ".PREFIX."ShipToShoreTransfers WHERE requried = :requried ORDER BY name", array(':requried' => '1'));
    }

    public function getShipToShoreTransfer($id){
        return $this->db->select("SELECT * FROM ".PREFIX."ShipToShoreTransfers WHERE shipToShoreTransferID = :id",array(':id' => $id));
    }
    
    public function insertShipToShoreTransfer($data){
        $this->db->insert(PREFIX."ShipToShoreTransfers",$data);
    }
    
    public function updateShipToShoreTransfer($data,$where){
        $this->db->update(PREFIX."ShipToShoreTransfers",$data, $where);
    }
    
    public function deleteShipToShoreTransfer($where){
        $shipToShoreTransfer = $this->db->select("SELECT * FROM ".PREFIX."ShipToShoreTransfers WHERE shipToShoreTransferID = :id",array(':id' => $where['shipToShoreTransferID']))[0];
        if(! $shipToShoreTransfer['required'] === 0 ){
            $this->db->delete(PREFIX."ShipToShoreTransfers", $where);
        }
    }
    
    public function enableShipToShoreTransfer($id){
        $data = array('enable' => 1); 
        $where = array('shipToShoreTransferID' => $id);
        $this->db->update(PREFIX."ShipToShoreTransfers",$data, $where);
    }
    
    public function disableShipToShoreTransfer($id){
        $data = array('enable' => 0); 
        $where = array('shipToShoreTransferID' => $id);
        $this->db->update(PREFIX."ShipToShoreTransfers",$data, $where);
    }
    
    public function getShipToShoreTransfersConfig(){
        return $this->db->select("SELECT * FROM ".PREFIX."ShipToShoreTransfers ORDER BY shipToShoreTransferID");
    }

}