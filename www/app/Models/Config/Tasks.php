<?php

namespace Models\Config;
use Core\Model;

class Tasks extends Model {

    private function buildTaskName($task) {
        $task->longName = str_replace('{lowering_name}', LOWERING_NAME, $task->longName);
        return $task;
    }

    public function getTasks(){
        $tasks = $this->db->select("SELECT * FROM ".PREFIX."Tasks ORDER BY taskID");

        foreach ($tasks as $task){
            $task = $this->buildTaskName($task);
        }
        return $tasks;
    }

    public function getActiveTasks(){

        $_warehouseModel = new \Models\Warehouse();
        if ($_warehouseModel->getShowLoweringComponents()) {
            $tasks = $this->db->select("SELECT * FROM ".PREFIX."Tasks WHERE enable = :enable ORDER BY taskID", array(':enable' => 1));
            foreach ($tasks as $task){
                $task = $this->buildTaskName($task);
            }
            return $tasks;
        }

        $tasks = $this->db->select("SELECT * FROM ".PREFIX."Tasks WHERE cruiseOrLowering = :cruiseOrLowering AND enable = :enable ORDER BY taskID", array(':cruiseOrLowering' => 0, ':enable' => 1));
        foreach ($tasks as $task){
            $task = $this->buildTaskName($task);
        }
        return $tasks;
    }

    public function getCruiseOnlyTasks(){
        $tasks = $this->db->select("SELECT * FROM ".PREFIX."Tasks WHERE cruiseOrLowering = :cruiseOrLowering ORDER BY taskID", array(':cruiseOrLowering' => 0));
        foreach ($tasks as $task){
            $task = $this->buildTaskName($task);
        }
        return $tasks;
    }
    
    public function getLoweringOnlyTasks(){
        $tasks = $this->db->select("SELECT * FROM ".PREFIX."Tasks WHERE cruiseOrLowering = :cruiseOrLowering ORDER BY taskID", array(':cruiseOrLowering' => 1));
        foreach ($tasks as $task){
            $task = $this->buildTaskName($task);
        }
        return $tasks;
    }

    public function getTaskStatuses(){
        return $this->db->select("SELECT taskID, name, status FROM ".PREFIX."Tasks ORDER BY taskID");
    }
    
    public function getTask($id){
        $tasks = $this->db->select("SELECT * FROM ".PREFIX."Tasks WHERE taskID = :id",array(':id' => $id));
        foreach ($tasks as $task){
            $task = $this->buildTaskName($task);
        }
        return $tasks;
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
