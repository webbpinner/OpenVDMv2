<?php

namespace models\config;
use Core\Model;

class ExtraDirectories extends Model {

    public function getExtraDirectories(){
        return $this->db->select("SELECT * FROM ".PREFIX."ExtraDirectories WHERE required = :required ORDER BY name", array(':required' => '0'));
    }

    public function getRequiredExtraDirectories(){
        return $this->db->select("SELECT * FROM ".PREFIX."ExtraDirectories WHERE required = :required ORDER BY name", array(':required' => '1'));
    }

    public function getExtraDirectory($id){
        return $this->db->select("SELECT * FROM ".PREFIX."ExtraDirectories WHERE extraDirectoryID = :id",array(':id' => $id));
    }
    
    public function getExtraDirectoryByName($name){
        return $this->db->select("SELECT * FROM ".PREFIX."ExtraDirectories WHERE name = :name",array(':name' => $name));
    }
    
    public function insertExtraDirectory($data){
        $this->db->insert(PREFIX."ExtraDirectories",$data);
    }
    
    public function updateExtraDirectory($data,$where){
        $this->db->update(PREFIX."ExtraDirectories",$data, $where);
    }
    
    public function deleteExtraDirectory($where){
        $extraDirectory = $this->db->select("SELECT * FROM ".PREFIX."ExtraDirectories WHERE extraDirectoryID = :id",array(':id' => $where['extraDirectoryID']))[0];
        if(strcmp($extraDirectory->required, '0') === 0 ){
            $this->db->delete(PREFIX."ExtraDirectories", $where);
        } 
    }
    
    public function enableExtraDirectory($id){
        $data = array('enable' => 1); 
        $where = array('extraDirectoryID' => $id);
        $this->db->update(PREFIX."ExtraDirectories",$data, $where);
    }
    
    public function disableExtraDirectory($id){
        $data = array('enable' => 0); 
        $where = array('extraDirectoryID' => $id);
        $this->db->update(PREFIX."ExtraDirectories",$data, $where);
    }
    
    public function getExtraDirectoriesConfig(){
        return $this->db->select("SELECT * FROM ".PREFIX."ExtraDirectories ORDER BY extraDirectoryID");
    }

}