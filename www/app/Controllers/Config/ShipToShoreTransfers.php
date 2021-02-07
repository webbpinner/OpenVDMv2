<?php

namespace Controllers\Config;
use Core\Controller;
use Core\View;
use Helpers\Url;
use Helpers\Session;

class shipToShoreTransfers extends Controller {

    private $_shipToShoreTransfersModel;
    private $_cruiseDataTransfersModel;
    private $_collectionSystemTransfersModel;
    private $_extraDirectoriesModel;
    private $_ssdwConfig;

    private function _buildTransferPriorityOptions($checkedType = null) {
        
        $output = array();

        for( $i=1; $i<=5; $i++){
            $option = array('id'=>(string)$i, 'name'=>'priority', 'value'=>(string)$i, 'label'=>(string)$i);
            if(strcmp($checkedType, (string)$i) === 0) {
                $option['checked']='1';
            }
            array_push($output, $option);
        }

        if(!isset($checkedType)) {
            $output[sizeOf($output)-1]['checked']='1';
        }        
        return $output;
    }
    
    private function _buildCollectionSystemOptions($selectedCollectionSystemTransferID = null) {
        
        $collectionSystemTransfers = $this->_collectionSystemTransfersModel->getCollectionSystemTransfers();
        
        $output = array();

	$data = array("0" => "");
        foreach($collectionSystemTransfers as $row){
            $data[$row->collectionSystemTransferID] = $row->name;
        }

        $output['data'] = $data;
        $output['name'] = "collectionSystemTransfer";
        $output['class'] = "form-control";
        
        //var_dump($output['data']);
        if(isset($selectedCollectionSystemTransferID)) {
            $output['value'] = $selectedCollectionSystemTransferID;
        }
	//var_dump($output['data'][1]);
        return $output;
    }
    
    private function _buildExtraDirectoryOptions($selectedExtraDirectoryID = null) {
        
        $extraDirectories = $this->_extraDirectoriesModel->getExtraDirectories();
        
        $output = array();

        $data = array("0" => "");
        foreach($extraDirectories as $row){
            $data[$row->extraDirectoryID] = $row->name;
        }

        $output['data'] = $data;
        $output['name'] = "extraDirectory";
        $output['class'] = "form-control";
        
        if(isset($selectedExtraDirectoryID)) {
            $output['value'] = $selectedExtraDirectoryID;
        }
        return $output;
    }
    
    public function __construct(){
        if(!Session::get('loggedin')){
            Url::redirect('config/login');
        }

        $this->_shipToShoreTransfersModel = new \Models\Config\ShipToShoreTransfers();
        $this->_cruiseDataTransferModel = new \Models\Config\CruiseDataTransfers();
        $this->_collectionSystemTransfersModel = new \Models\Config\CollectionSystemTransfers();
        $this->_extraDirectoriesModel = new \Models\Config\ExtraDirectories();
        
        $requiredCruiseDataTransfers = $this->_cruiseDataTransferModel->getRequiredCruiseDataTransfers();
        
        foreach($requiredCruiseDataTransfers as $requiredCruiseDataTransfer) {
            if(strcmp($requiredCruiseDataTransfer->name, 'SSDW') === 0) {
                $this->_ssdwConfig = $requiredCruiseDataTransfer;
                break;
            }
        }
    }

    public function index(){
        $data['title'] = 'Configuration';
        $data['javascript'] = array('shipToShoreTransfers');
        $data['shipToShoreTransfers'] = $this->_shipToShoreTransfersModel->getShipToShoreTransfers();
        $data['ssdwID'] = $this->_ssdwConfig->cruiseDataTransferID;
        $data['ssdwEnable'] = $this->_ssdwConfig->enable;
        $data['ssdwStatus'] = $this->_ssdwConfig->status;

        View::rendertemplate('header',$data);
        View::render('Config/shipToShoreTransfers',$data);
        View::rendertemplate('footer',$data);
    }

    public function add(){
        $data['title'] = 'Add Ship-to-Shore Transfer';
        $data['javascript'] = array('shipToShoreTransfersFormHelper');
        $data['transferPriorityOptions'] = $this->_buildTransferPriorityOptions($_POST['priority']);
        $data['collectionSystemOptions'] = $this->_buildCollectionSystemOptions($_POST['collectionSystemTransfer']);
        $data['extraDirectoryOptions'] = $this->_buildExtraDirectoryOptions($_POST['extraDirectory']);

        if(isset($_POST['submit'])){
            $name = $_POST['name'];
            $longName = $_POST['longName'];
            $priority = $_POST['priority'];
            $collectionSystem = $_POST['collectionSystemTransfer'];
            $extraDirectory = $_POST['extraDirectory'];
            $includeFilter = $_POST['includeFilter'];
            $enable = 0;

            if($name == ''){
                $error[] = 'Name is required';
            } 

            if($longName == ''){
                $error[] = 'Long name is required';
            } 

            if($priority == ''){
                $error[] = 'Priority is required';
            }
            
            if($collectionSystem == 0 && $extraDirectory == 0){
                $error[] = 'Select a Collections System and/or Extra Directory';
            }
            
            if($includeFilter == ''){
                $includeFilter = '*';
            } else {
                $includeFilter = preg_replace("/\s*,\s*/", ",",$includeFilter);
            }

            if(!$error){
                $postdata = array(
                    'name' => $name,
                    'longName' => $longName,
                    'priority' => $priority,
                    'collectionSystem' => $collectionSystem,
                    'extraDirectory' => $extraDirectory,
                    'includeFilter' => $includeFilter,
                    'enable' => $enable
                );

                $this->_shipToShoreTransfersModel->insertShipToShoreTransfer($postdata);
                Session::set('message','Ship-to-Shore Transfer Added');
                Url::redirect('config/shipToShoreTransfers');
            }
        }

        View::rendertemplate('header',$data);
        View::render('Config/addShipToShoreTransfers',$data,$error);
        View::rendertemplate('footer',$data);
    }
        
    public function edit($id){
        $data['title'] = 'Edit Ship-to-Shore Transfer';
        $data['javascript'] = array('shipToShoreTransfersFormHelper');
        $data['row'] = $this->_shipToShoreTransfersModel->getShipToShoreTransfer($id);

        if(isset($_POST['submit'])){
            $name = $_POST['name'];
            $longName = $_POST['longName'];
            $priority = $_POST['priority'];
            $collectionSystem = $_POST['collectionSystemTransfer'];
            $extraDirectory = $_POST['extraDirectory'];
            $includeFilter = $_POST['includeFilter'];

            if($name == ''){
                $error[] = 'Name is required';
            } 

            if($longName == ''){
                $error[] = 'Long name is required';
            } 

            if($priority == ''){
                $error[] = 'Priority is required';
            } 

            if($collectionSystem == 0 && $extraDirectory == 0){
                $error[] = 'Select a Collections System and/or Extra Directory';
            } 
            
            if($includeFilter == ''){
                $includeFilter = '*';
            } else {
                $includeFilter = preg_replace("/\s*,\s*/", ",",$includeFilter);
            }
                
            if(!$error){
                $postdata = array(
                    'name' => $name,
                    'longName' => $longName,
                    'priority' => $priority,
                    'collectionSystem' => $collectionSystem,
                    'extraDirectory' => $extraDirectory,
                    'includeFilter' => $includeFilter,
                );
            
                
                $where = array('shipToShoreTransferID' => $id);
                $this->_shipToShoreTransfersModel->updateShipToShoreTransfer($postdata,$where);
                Session::set('message','Ship-to-Shore Transfers Updated');
                Url::redirect('config/shipToShoreTransfers');
            } else {
                
                $data['row'][0]->name = $name;
                $data['row'][0]->longName = $longName;
                $data['row'][0]->priority = $priority;
                $data['row'][0]->collectionSystem = $collectionSystem;
                $data['row'][0]->extraDirectory = $extraDirectory;
                $data['row'][0]->includeFilter = $includeFilter;
            }
        }

        $data['transferPriorityOptions'] = $this->_buildTransferPriorityOptions($data['row'][0]->priority);
        $data['collectionSystemOptions'] = $this->_buildCollectionSystemOptions($data['row'][0]->collectionSystem);
        $data['extraDirectoryOptions'] = $this->_buildExtraDirectoryOptions($data['row'][0]->extraDirectory);

        View::rendertemplate('header',$data);
        View::render('Config/editShipToShoreTransfers',$data,$error);
        View::rendertemplate('footer',$data);
    }
    
    public function delete($id){
                
        $where = array('shipToShoreTransferID' => $id);
        $this->_shipToShoreTransfersModel->deleteShipToShoreTransfer($where);
        Session::set('message','Ship-to-Shore Transfer Deleted');
        Url::redirect('config/shipToShoreTransfers');
    }
    
    public function enable($id) {

        $this->_shipToShoreTransfersModel->enableShipToShoreTransfer($id);
        Url::redirect('config/shipToShoreTransfers');
    }
    
    public function disable($id) {

        $this->_shipToShoreTransfersModel->disableShipToShoreTransfer($id);
        Url::redirect('config/shipToShoreTransfers');
    }
    
    public function run() {
        
        $_warehouseModel = new \Models\Warehouse();
        $gmData = array(
            'cruiseDataTransfer' => array(
                'enable' => '1'
            ),
            'systemStatus' => "On"
        );

        
        # create the gearman client
        $gmc= new \GearmanClient();

        # add the default server (localhost)
        $gmc->addServer();

        #submit job to Gearman
        $job_handle = $gmc->doBackground("runShipToShoreTransfer", json_encode($gmData));
    
    //    $done = false;
    //    do
    //    {
            sleep(1);
    //        $stat = $gmc->jobStatus($job_handle);
    //        if ($stat[0]) // the job is known so it has been added to gearman 
    //            $done = true;
    //    }
    //    while(!$done);
        
        Url::redirect('config/shipToShoreTransfers');
    }

    public function stop() {
        
        $_warehouseModel = new \Models\Warehouse();
        $gmData['pid'] = $this->_ssdwConfig->pid;
        
        # create the gearman client
        $gmc= new \GearmanClient();

        # add the default server (localhost)
        $gmc->addServer();

        #submit job to Gearman
        $job_handle = $gmc->doBackground("stopJob", json_encode($gmData));
    
    //    $done = false;
    //    do
    //    {
            sleep(1);
    //        $stat = $gmc->jobStatus($job_handle);
    //        if ($stat[0]) // the job is known so it has been added to gearman 
    //            $done = true;
    //    }
    //    while(!$done);
        
        Url::redirect('config/shipToShoreTransfers');
    }
    
    public function enableShipToShoreTransfers() {

        //$this->_cruiseDataTransfersModel->enableCruiseDataTransfer($id);
        $this->_cruiseDataTransferModel->enableCruiseDataTransfer($this->_ssdwConfig->cruiseDataTransferID);
        //Url::redirect('config/cruiseDataTransfers');
        Url::redirect('config/shipToShoreTransfers');
    }
    
    public function disableShipToShoreTransfers() {

        $this->_cruiseDataTransferModel->disableCruiseDataTransfer($this->_ssdwConfig->cruiseDataTransferID);
        Url::redirect('config/shipToShoreTransfers');
    }
    
}
