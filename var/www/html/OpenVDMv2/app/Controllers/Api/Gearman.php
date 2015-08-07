<?php

namespace Controllers\Api;
use Core\Controller;

class Gearman extends Controller {

    private $_model;

    public function __construct(){
        $this->_model = new \Models\Api\Gearman();
    }

    public function newJob($handle){

        $return = array();
        if(isset($_POST['jobPid'])){
            $data['jobHandle'] = $handle;
            $data['jobPid'] = $_POST['jobPid'];
        
            (isset($_POST['jobName']) ? $data['jobName'] = $_POST['jobName'] : $data['jobName'] = $handle );
            $this->_model->insertJob($data);
            $return['status'] = 'success';
        } else {
            $return['status'] = 'error';
            $return['message'] = 'missing POST data';
        }
        echo json_encode($return);
    }
    
    public function getJob($id){

        echo json_encode($this->_model->getJob($id));
        
    }
    
    public function getJobs(){

        echo json_encode($this->_model->getJobs());
    }

}