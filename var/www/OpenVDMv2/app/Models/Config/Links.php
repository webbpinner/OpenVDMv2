<?php

namespace models\config;
use Core\Model;

class Links extends Model {

    public function getLinks(){
        return $this->db->select("SELECT * FROM ".PREFIX."Links ORDER BY private");
    }

    public function getLink($id){
        return $this->db->select("SELECT * FROM ".PREFIX."Links WHERE linkID = :id",array(':id' => $id));
    }
    
    public function getLinkByName($name){
        return $this->db->select("SELECT * FROM ".PREFIX."Links WHERE name = :name",array(':name' => $name));
    }
    
    public function insertLink($data){
        $this->db->insert(PREFIX."Links",$data);
    }
    
    public function updateLink($data,$where){
        $this->db->update(PREFIX."Links",$data, $where);
    }
    
    public function deleteLink($where){
        $this->db->delete(PREFIX."Links", $where); 
    }
    
    public function enableLink($id){
        $data = array('enable' => 1); 
        $where = array('linkID' => $id);
        $this->db->update(PREFIX."Links",$data, $where);
    }
    
    public function disableLink($id){
        $data = array('enable' => 0); 
        $where = array('linkID' => $id);
        $this->db->update(PREFIX."Links",$data, $where);
    }
    
    public function privateLink($id){
        $data = array('private' => 1); 
        $where = array('linkID' => $id);
        $this->db->update(PREFIX."Links",$data, $where);
    }
    
    public function publicLink($id){
        $data = array('private' => 0); 
        $where = array('linkID' => $id);
        $this->db->update(PREFIX."Links",$data, $where);
    }
    
    public function processLinkURL($links){
        
        $_warehouseModel = new \Models\Warehouse();
        $cruiseID = $_warehouseModel->getCruiseID();
        
        foreach($links as $row) {
            $row->url = str_replace("{cruiseID}", $cruiseID, $row->url);
        }
    }
    
}