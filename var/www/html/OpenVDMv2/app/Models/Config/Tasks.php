<?php

namespace Models\Config;
use Core\Model;

class Tasks extends Model {

    public function getTasks(){
        return $this->db->select("SELECT * FROM ".PREFIX."Tasks ORDER BY taskID");
    }
    
    public function getTaskStatuses(){
        return $this->db->select("SELECT taskID, name, status FROM ".PREFIX."Tasks ORDER BY taskID");
    }
    
    public function getTask($id){
        return $this->db->select("SELECT * FROM ".PREFIX."Tasks WHERE taskID = :id",array(':id' => $id));
    }
    
    public function insertTask($data){
        $this->db->insert(PREFIX."Tasks",$data);
    }
    
    public function updateTask($data,$where){
        $this->db->update(PREFIX."Tasks",$data, $where);
    }
    
    public function deleteTask($where){
        $this->db->delete(PREFIX."Tasks", $where);
    }
    
    public function setErrorTask($id){
        $data = array('status' => '3', 'pid' => '0');
        $where = array('taskID' => $id);
        $this->db->update(PREFIX."Tasks",$data, $where);
    }

    public function setRunningTask($id,$pid){
        $data = array('status' => '1', 'pid' => $pid);
        $where = array('taskID' => $id);
        $this->db->update(PREFIX."Tasks",$data, $where);
    }

    public function setIdleTask($id){
        $data = array();
        $row = $this->getTask($id);
        if (strcmp($row[0]->enable,'1') === 0) {
            $data = array('status' => '2', 'pid' => '0');
        } else {
            $data = array('status' => '4', 'pid' => '0');
        }
        $where = array('taskID' => $id);
        $this->db->update(PREFIX."Tasks",$data, $where);
    }
    
    public function setOffTask($id){
        $data = array();
        $row = $this->getTask($id);
        if (strcmp($row[0]->status,'2') === 0) {
            $data['status'] = '4';
            $data['pid'] = '0';
        }
        $where = array('taskID' => $id);
        $this->db->update(PREFIX."Tasks",$data, $where);
    }
    
    public function enableTask($id){
        $data = array('enable' => 1);
        $row = $this->getTask($id);
        if (strcmp($row[0]->status,'4') === 0) {
            $data['status'] = '2';
        }
        $where = array('taskID' => $id);
        $this->db->update(PREFIX."Tasks",$data, $where);
    }
    
    public function disableTask($id){
        $data = array('enable' => 0); 
        $row = $this->getTask($id);
        if (strcmp($row[0]->status,'2') === 0) {
            $data['status'] = '4';
        }
        $where = array('taskID' => $id);
        $this->db->update(PREFIX."Tasks",$data, $where);
    }

}