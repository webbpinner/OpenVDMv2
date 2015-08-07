<?php

namespace Models\Config;
use Core\Model;

class TransferTypes extends Model {

    public function getTransferTypes(){
        return $this->db->select("SELECT * FROM ".PREFIX."TransferTypes ORDER BY transferTypeID");
    }
    
    public function getTransferType($id){
        return $this->db->select("SELECT * FROM ".PREFIX."TransferTypes WHERE transferTypeID = :id",array(':id' => $id));
    }
    
//    public function insert_transferType($data){
//        $this->db->insert(PREFIX."TransferTypes",$data);
//    }
    
//    public function update_transferType($data,$where){
//        $this->db->update(PREFIX."TransferTypes",$data, $where);
//    }
    
//    public function delete_transferType($where){
//        $this->db->delete(PREFIX."TransferTypes", $where);
//    }
}