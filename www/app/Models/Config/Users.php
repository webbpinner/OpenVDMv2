<?php

namespace Models\Config;
use Core\Model;


class Users extends Model {

    public function getUsers(){
        return $this->db->select("SELECT * FROM ".PREFIX."Users ORDER BY username");
    }
    
    public function getUser($id){
        return $this->db->select("SELECT * FROM ".PREFIX."Users WHERE userID = :id",array(':id' => $id));
    }
    
    public function insertUser($data){
        $this->db->insert(PREFIX."Users",$data);
    }
    
    public function updateUser($data,$where){
        $this->db->update(PREFIX."Users",$data, $where);
    }
    
    public function deleteUser($where){
        $this->db->delete(PREFIX."Users", $where);
    }
}