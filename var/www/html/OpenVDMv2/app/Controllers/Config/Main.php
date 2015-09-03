<?php

namespace Controllers\Config;
use Core\Controller;
use Core\View;
use Helpers\Session;
use Helpers\Url;

class Main extends Controller {
    
    private $_warehouseModel;
    private $_tasksModel;
    private $_collectionSystemTransfersModel;
    private $_extraDirectoriesModel;
    private $_cruiseDataTransfersModel;
    
    public function __construct(){
        
        if(!Session::get('loggedin')){
            Url::redirect('config/login');
        }
        
        $this->_warehouseModel = new \Models\Warehouse();
        $this->_tasksModel = new \Models\Config\Tasks();
        $this->_collectionSystemTransfersModel = new \Models\Config\CollectionSystemTransfers();
        $this->_extraDirectoriesModel = new \Models\Config\ExtraDirectories();
        $this->_cruiseDataTransfersModel = new \Models\Config\CruiseDataTransfers();
    }

    public function index(){
            
        $data['title'] = 'Configuration';
        $data['javascript'] = array('main_config', 'tabs_config');
        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['cruiseStartDate'] = $this->_warehouseModel->getCruiseStartDate();
        $data['systemStatus'] = $this->_warehouseModel->getSystemStatus();
        $data['shipToShoreTransfersStatus'] = $this->_warehouseModel->getShipToShoreTransferStatus();
        $data['tasks'] = $this->_tasksModel->getTasks();
        $data['collectionSystemTransfers'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfers();
        $data['requiredCruiseDataTransfers'] = $this->_cruiseDataTransfersModel->getRequiredCruiseDataTransfers();
        $data['cruiseDataTransfers'] = $this->_cruiseDataTransfersModel->getCruiseDataTransfers();
        
        View::rendertemplate('header',$data);
        View::render('Config/main',$data);
        View::rendertemplate('footer',$data);
    }
    
    public function editCruiseID(){

        $data['title'] = 'Configuration';
        $data['css'] = array('bootstrap-datepicker');
        $data['javascript'] = array('tabs_config', 'bootstrap-datepicker');
        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['cruiseStartDate'] = $this->_warehouseModel->getCruiseStartDate();

        
        if(isset($_POST['submit'])) {
            $cruiseID = $_POST['cruiseID'];
            $cruiseStartDate = $_POST['cruiseStartDate'];

            if($cruiseID == ''){
                $error[] = 'Cruise ID is required';
            } elseif(!preg_match('/([0-9]{2})\/([0-9]{2})\/([0-9]{4})/', $cruiseStartDate)){
                $error[] = 'Valid Cruise Start Date is required';                
            } else {
                $warehouseData = $this->_warehouseModel->getShipboardDataWarehouseConfig();
                
                if (!is_dir($warehouseData['shipboardDataWarehouseBaseDir'] . '/' . $cruiseID)) {
                    $error[] = 'A Cruise Data Directory for that Cruise ID does not exist';
                }
            }
            
            if(!$error){
                $this->_warehouseModel->setCruiseID(array('value' => $cruiseID));
                $this->_warehouseModel->setCruiseStartDate(array('value' => $cruiseStartDate));
                Session::set('message','Cruise ID Updated');
                Url::redirect('config');
            } else {
                $data['cruiseID'] = $cruiseID;
                $data['cruiseStartDate'] = $cruiseStartDate;
            }
        }
        
        View::rendertemplate('header',$data);
        View::render('Config/editCruiseID',$data, $error);
        View::rendertemplate('footer',$data);
    }
    
    public function enableSystem() {

        $this->_warehouseModel->enableSystem();
        Url::redirect('config');
    }
    
    public function disableSystem() {

        $this->_warehouseModel->disableSystem();
        Url::redirect('config');
    }
    
    public function enableShipToShoreTransfers() {

        $requiredCruiseDataTransfers = $this->_cruiseDataTransfersModel->getRequiredCruiseDataTransfers();
        foreach($requiredCruiseDataTransfers as $row) {
            if(strcmp($row->name, 'SSDW') === 0 ) {
                $this->_cruiseDataTransfersModel->enableCruiseDataTransfer($row->cruiseDataTransferID);
                break;
            }
        }
        Url::redirect('config');
    }
    
    public function disableShipToShoreTransfers() {

        $requiredCruiseDataTransfers = $this->_cruiseDataTransfersModel->getRequiredCruiseDataTransfers();
        foreach($requiredCruiseDataTransfers as $row) {
            if(strcmp($row->name, 'SSDW') === 0 ) {
                $this->_cruiseDataTransfersModel->disableCruiseDataTransfer($row->cruiseDataTransferID);
                break;
            }
        }
        Url::redirect('config');
    }
    
    public function rebuildCruiseDirectory() {

        $_warehouseModel = new \models\warehouse();
        $gmData['siteRoot'] = DIR;
        $gmData['shipboardDataWarehouse'] = $_warehouseModel->getShipboardDataWarehouseConfig();
        $gmData['cruiseID'] = $_warehouseModel->getCruiseID();
        
        # create the gearman client
        $gmc= new \GearmanClient();

        # add the default server (localhost)
        $gmc->addServer();

        #submit job to Gearman
        #$job_handle = $gmc->doBackground("updateCruiseDirectory", json_encode($gmData));
        $data['jobResults'] = json_decode($gmc->doNormal("rebuildCruiseDirectory", json_encode($gmData)));
    
        #additional data needed for view
        $data['title'] = 'Configuration';
        $data['javascript'] = array('main_config', 'tabs_config');
        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['cruiseStartDate'] = $this->_warehouseModel->getCruiseStartDate();
        $data['systemStatus'] = $this->_warehouseModel->getSystemStatus();
        $data['shipToShoreTransfersStatus'] = $this->_warehouseModel->getShipToShoreTransferStatus();
        $data['tasks'] = $this->_tasksModel->getTasks();
        $data['collectionSystemTransfers'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfers();
        $data['requiredCruiseDataTransfers'] = $this->_cruiseDataTransfersModel->getRequiredCruiseDataTransfers();
        $data['cruiseDataTransfers'] = $this->_cruiseDataTransfersModel->getCruiseDataTransfers();

        $data['jobName'] = 'Rebuild Cruise Directory';

        View::rendertemplate('header',$data);
        View::render('Config/main',$data);
        View::rendertemplate('footer',$data);
    }
    
    public function rebuildMD5Summary() {

        $_warehouseModel = new \Models\Warehouse();
        $gmData['siteRoot'] = DIR;
        $gmData['shipboardDataWarehouse'] = $_warehouseModel->getShipboardDataWarehouseConfig();
        $gmData['cruiseID'] = $_warehouseModel->getCruiseID();
        
        # create the gearman client
        $gmc= new \GearmanClient();

        # add the default server (localhost)
        $gmc->addServer();

        #submit job to Gearman
        $job_handle = $gmc->doBackground("rebuildMD5Summary", json_encode($gmData));
    
        sleep(1);
        
        Url::redirect('config');
    }

    public function rebuildTransferLogSummary() {

        $_warehouseModel = new \Models\Warehouse();
        $gmData['siteRoot'] = DIR;
        $gmData['shipboardDataWarehouse'] = $_warehouseModel->getShipboardDataWarehouseConfig();
        $gmData['cruiseID'] = $_warehouseModel->getCruiseID();
        
        # create the gearman client
        $gmc= new \GearmanClient();

        # add the default server (localhost)
        $gmc->addServer();

        #submit job to Gearman
        $job_handle = $gmc->doBackground("rebuildTransferLogSummary", json_encode($gmData));
    
        sleep(1);

        Url::redirect('config');
    }
    
    public function rebuildDataDashboard() {

        $_warehouseModel = new \Models\Warehouse();
        $gmData['siteRoot'] = DIR;
        $gmData['shipboardDataWarehouse'] = $_warehouseModel->getShipboardDataWarehouseConfig();
        $gmData['cruiseID'] = $_warehouseModel->getCruiseID();
        
        # create the gearman client
        $gmc= new \GearmanClient();

        # add the default server (localhost)
        $gmc->addServer();

        #submit job to Gearman
        $job_handle = $gmc->doBackground("rebuildDataDashboard", json_encode($gmData));
    
        sleep(1);

        Url::redirect('config');
    }
    
    public function setupNewCruise() {

        $data['title'] = 'Configuration';
        $data['css'] = array('bootstrap-datepicker');
        $data['javascript'] = array('tabs_config', 'bootstrap-datepicker');
        $data['cruiseID'] = '';
        $data['cruiseStartDate'] = '';
//        $error = array();

        if(isset($_POST['submit'])){
            $cruiseID = $_POST['cruiseID'];
            $cruiseStartDate = $_POST['cruiseStartDate'];

            if($cruiseID == ''){
                $error[] = 'Cruise ID is required';
            } elseif(!preg_match('/([0-9]{2})\/([0-9]{2})\/([0-9]{4})/', $cruiseStartDate)){
                $error[] = 'Valid Cruise Start Date is required';
            } else {
                $warehouseData = $this->_warehouseModel->getShipboardDataWarehouseConfig();  
                if (is_dir($warehouseData['shipboardDataWarehouseBaseDir'] . '/' . $cruiseID)) {
                    $error[] = 'A Cruise Data Directory for that Cruise ID already exists';
                }
            }
                
            if(!$error){
                
                $this->_warehouseModel->setCruiseID(array('value' => $cruiseID));
                $this->_warehouseModel->setCruiseStartDate(array('value' => $cruiseStartDate));
                $gmData['siteRoot'] = DIR;
                $gmData['shipboardDataWarehouse'] = $this->_warehouseModel->getShipboardDataWarehouseConfig();
                $gmData['cruiseID'] = $this->_warehouseModel->getCruiseID();
        
                # create the gearman client
                $gmc= new \GearmanClient();

                # add the default server (localhost)
                $gmc->addServer();

                #submit job to Gearman
                #$job_handle = $gmc->doBackground("rebuildCruiseDirectory", json_encode($gmData));
                $data['jobResults'] = json_decode($gmc->doNormal("setupNewCruise", json_encode($gmData)));
    
        
                #additional data needed for view
                $data['title'] = 'Configuration';
                $data['javascript'] = array('main_config', 'tabs_config');
                $data['cruiseID'] = $this->_warehouseModel->getCruiseID();                                                           
                $data['systemStatus'] = $this->_warehouseModel->getSystemStatus();
                $data['shipToShoreTransfersStatus'] = $this->_warehouseModel->getShipToShoreTransferStatus();
                $data['tasks'] = $this->_tasksModel->getTasks();
                $data['collectionSystemTransfers'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfers();
                $data['requiredCruiseDataTransfers'] = $this->_cruiseDataTransfersModel->getRequiredCruiseDataTransfers();
                $data['cruiseDataTransfers'] = $this->_cruiseDataTransfersModel->getCruiseDataTransfers();
                
                $data['jobName'] = 'Setup New Cruise';

                View::rendertemplate('header',$data);
                View::render('Config/main',$data);
                View::rendertemplate('footer',$data);
            } else {
                $data['cruiseID'] = $cruiseID;
                $data['cruiseStartDate'] = $cruiseStartDate;
            }
        }
        
        View::rendertemplate('header',$data);
        View::render('Config/newCruiseID',$data, $error);
        View::rendertemplate('footer',$data);
    }
    
    public function finalizeCurrentCruise() {

        $gmData['siteRoot'] = DIR;
        $gmData['shipboardDataWarehouse'] = $this->_warehouseModel->getShipboardDataWarehouseConfig();
        $gmData['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $gmData['cruiseStartDate'] = $this->_warehouseModel->getCruiseStartDate();
        $gmData['systemStatus'] = "On";
        $gmData['collectionSystemTransfers'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfers();
        $extraDirectories = $this->_extraDirectoriesModel->getRequiredExtraDirectories();
                    
        foreach($extraDirectories as $row) {
            if(strcmp($row->name, 'Science') === 0 ) {
                $gmData['scienceDir'] = $row->destDir;
                break;
            }
        }
        
        # create the gearman client
        $gmc= new \GearmanClient();

        # add the default server (localhost)
        $gmc->addServer();

        #submit job to Gearman
        #$job_handle = $gmc->doBackground("rebuildCruiseDirectory", json_encode($gmData));
        $data['jobResults'] = json_decode($gmc->doBackground("finalizeCurrentCruise", json_encode($gmData)));
        
        sleep(1);

        Url::redirect('config');
    
    }
    
    public function exportOVDMConfig() {

        $gmData['siteRoot'] = DIR;
        $gmData['shipboardDataWarehouse'] = $this->_warehouseModel->getShipboardDataWarehouseConfig();
        $gmData['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $gmData['cruiseStartDate'] = $this->_warehouseModel->getCruiseStartDate();
        $gmData['systemStatus'] = "On";
        $gmData['collectionSystemTransfers'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfers();
        $extraDirectories = $this->_extraDirectoriesModel->getRequiredExtraDirectories();
                    
        foreach($extraDirectories as $row) {
            if(strcmp($row->name, 'Science') === 0 ) {
                $gmData['scienceDir'] = $row->destDir;
                break;
            }
        }
        
        # create the gearman client
        $gmc= new \GearmanClient();

        # add the default server (localhost)
        $gmc->addServer();

        #submit job to Gearman
        #$job_handle = $gmc->doBackground("rebuildCruiseDirectory", json_encode($gmData));
        $data['jobResults'] = json_decode($gmc->doBackground("exportOVDMConfig", json_encode($gmData)));
        
        sleep(1);

        Url::redirect('config');
    
    }
}
