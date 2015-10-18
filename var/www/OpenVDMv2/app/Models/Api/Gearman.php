<?php

namespace Models\Api;
use Core\Model;

class Gearman extends Model {
    
    
    private function updateJobs() {
        
        $gmclient= new \GearmanClient();

        /* add the default server */
        $gmclient->addServer();

        $jobs = $this->db->select("SELECT jobID, jobHandle FROM ".PREFIX."Gearman ORDER BY jobID DESC LIMIT 100");

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
        
        return $this->db->select("SELECT * FROM ".PREFIX."Gearman ORDER BY jobID DESC LIMIT 10");
    }
    
    public function getJob($id){
        
        $this->updateJobs();
        
        return $this->db->select("SELECT * FROM ".PREFIX."Gearman WHERE jobID = :id",array(':id' => $id));
    }
    
    public function insertJob($data){
        
        $this->updateJobs();
        
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
    
    public function clearAllJobsFromDB(){
        
        $clearingJobs = true;
        while($clearingJobs){
            $jobs = $this->db->select("SELECT jobID FROM ".PREFIX."Gearman ORDER BY jobID DESC LIMIT 25");

            if(sizeof($jobs) > 0){
                foreach($jobs as $row) {
                    $where = array("jobID" => $row->jobID);
                    $this->deleteJob($where);
                }
            } else {
                $clearingJobs = false;
                break;
            }
        }
        
        return array("Success");
    }
}