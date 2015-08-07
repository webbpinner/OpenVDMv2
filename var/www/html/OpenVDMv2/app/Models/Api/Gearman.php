<?php

namespace Models\Api;
use Core\Model;

class Gearman extends Model {
    
    
    private function updateJobs() {
 
        $jobs = $this->db->select("SELECT * FROM ".PREFIX."Gearman ORDER BY jobID DESC");
        
        $gmclient= new \GearmanClient();

        /* add the default server */
        $gmclient->addServer();
        
        foreach($jobs as $row) {
            $stat = $gmclient->jobStatus($row->jobHandle);
            if (!$stat[0]) {
                $this->db->delete(PREFIX."Gearman", array("jobID" => $row->jobID));
            } else {
                $data['jobNumerator'] = $stat[2]; 
                ($stat[3] === 0 ? $data['jobDenominator'] = 1 : $data['jobDenominator'] = $stat[3]);
                $this->db->update(PREFIX."Gearman", $data, array("jobID" => $row->jobID));               
            }
        }
    }
    
    public function getJobs(){
        
        $this->updateJobs();
        
        return $this->db->select("SELECT * FROM ".PREFIX."Gearman ORDER BY jobID DESC");
    }
    
    public function getJob($id){
        
        $this->updateJobs();
        
        return $this->db->select("SELECT * FROM ".PREFIX."Gearman WHERE jobID = :id",array(':id' => $id));
    }
    
    public function insertJob($data){
        
        # create the gearman client
        $gmclient= new \GearmanClient();

        # add the default server (localhost)
        $gmclient->addServer();
        
        $stat = $gmclient->jobStatus($data['jobHandle']);
        if ($stat[0]) {
            $data['jobRunning'] = $stat[1];
            $data['jobNumerator'] = $stat[2]; 
            ($stat[3] === 0 ? $data['jobDenominator'] = 1 : $data['jobDenominator'] = $stat[3]);
            $this->db->insert(PREFIX."Gearman",$data);
        }
    }

    public function updateJob($data,$where){
        $this->db->update(PREFIX."Gearman",$data, $where);
    }
    
    public function deleteJob($where){
        $this->db->delete(PREFIX."Gearman", $where);
    }

}