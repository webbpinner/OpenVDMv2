<?php

namespace controllers\config;
use Core\Controller;
use Core\View;
use Helpers\Session;
use Helpers\Url;

class System extends Controller {
    
    private $_coreValuesModel;
    private $_extraDirectoriesModel;
    private $_cruiseDataTransfersModel;
    private $_shipToShoreTransfersModel;

    private function updateCruiseDirectory() {
        if($this->_coreValuesModel->getSystemStatus()) {

            $gmData['siteRoot'] = DIR;
            $gmData['shipboardDataWarehouse'] = $this->_warehouseModel->getShipboardDataWarehouseConfig();
            $gmData['cruiseID'] = $this->_warehouseModel->getCruiseID();
        
            # create the gearman client
            $gmc= new \GearmanClient();

            # add the default server (localhost)
            $gmc->addServer();

            #submit job to Gearman
            $job_handle = $gmc->doBackground("rebuildCruiseDirectory", json_encode($gmData));
        }
    }
    
    public function __construct(){
        
        if(!Session::get('loggedin')){
            Url::redirect('config/login');
        }
        
        $this->_coreValuesModel = new \Models\Warehouse();
        $this->_extraDirectoriesModel = new \Models\Config\ExtraDirectories();
        $this->_cruiseDataTransfersModel = new \Models\Config\CruiseDataTransfers();
        $this->_shipToShoreTransfersModel = new \Models\Config\ShipToShoreTransfers();
    }
    
    public function index(){
            
        $data['title'] = 'Configuration';
        $data['javascript'] = array('system', 'tabs_config');
        $data['requiredCruiseDataTransfers'] = $this->_cruiseDataTransfersModel->getRequiredCruiseDataTransfers();
        $data['requiredShipToShoreTransfers'] = $this->_shipToShoreTransfersModel->getRequiredShipToShoreTransfers();
        $data['requiredExtraDirectories'] = $this->_extraDirectoriesModel->getRequiredExtraDirectories();
        $data['shipboardDataWarehouseStatus'] = $this->_coreValuesModel->getShipboardDataWarehouseStatus();
        $data['shipToShoreBWLimit'] = $this->_coreValuesModel->getShipToShoreBWLimit();
        $data['shipToShoreBWLimitStatus'] = $this->_coreValuesModel->getShipToShoreBWLimitStatus();
        $data['md5FilesizeLimit'] = $this->_coreValuesModel->getMd5FilesizeLimit();
        $data['md5FilesizeLimitStatus'] = $this->_coreValuesModel->getMd5FilesizeLimitStatus();

        $freeSpace = $this->_coreValuesModel->getFreeSpace();
        
        if(isset($freeSpace['error'])){
            $data['freeSpace'] = "Error";
        }
        
        View::rendertemplate('header',$data);
        View::render('Config/system',$data);
        View::rendertemplate('footer',$data);
    }
    
    public function editShipboardDataWarehouse(){

        $data['title'] = 'Configuration';
        $data['javascript'] = array('tabs_config');
        $data['shipboardDataWarehouseConfig'] = $this->_coreValuesModel->getShipboardDataWarehouseConfig();

        if(isset($_POST['submit'])){
            $shipboardDataWarehouseIP = $_POST['shipboardDataWarehouseIP'];
            $shipboardDataWarehouseBaseDir = $_POST['shipboardDataWarehouseBaseDir'];
            $shipboardDataWarehouseUsername = $_POST['shipboardDataWarehouseUsername'];
            $shipboardDataWarehousePublicDataDir = $_POST['shipboardDataWarehousePublicDataDir'];

            if($shipboardDataWarehouseIP == ''){
                $error[] = 'Shipboard Data Warehouse IP is required';
            }

            if($shipboardDataWarehouseBaseDir == ''){
                $error[] = 'Shipboard Data Warehouse Base Directory is required';
            }

            if($shipboardDataWarehouseUsername == ''){
                $error[] = 'Shipboard Data Warehouse Username is required';
            }
            
            if($shipboardDataWarehousePublicDataDir == ''){
                $error[] = 'Shipboard Data Warehouse Public Data Directory is required';
            }

            if(!$error){
                $postdata = array(
                    'shipboardDataWarehouseIP' => $shipboardDataWarehouseIP,
                    'shipboardDataWarehouseBaseDir' => $shipboardDataWarehouseBaseDir,
                    'shipboardDataWarehouseUsername' => $shipboardDataWarehouseUsername,
                    'shipboardDataWarehousePublicDataDir' => $shipboardDataWarehousePublicDataDir,
                );
                
                $this->_coreValuesModel->setShipboardDataWarehouseConfig($postdata);
                Session::set('message','Shipboard Data Warehouse Updated');
                Url::redirect('config/system');
            } else {
                $data['shipboardDataWarehouseConfig'] = array(
                    'shipboardDataWarehouseIP' => $shipboardDataWarehouseIP,
                    'shipboardDataWarehouseBaseDir' => $shipboardDataWarehouseBaseDir,
                    'shipboardDataWarehouseUsername' => $shipboardDataWarehouseUsername,
                    'shipboardDataWarehousePublicDataDir' => $shipboardDataWarehousePublicDataDir,
                );
            }
        }
        
        View::rendertemplate('header',$data);
        View::render('Config/editShipboardDataWarehouse',$data, $error);
        View::rendertemplate('footer',$data);
    }
    
    public function editShoresideDataWarehouse(){

        $data['title'] = 'Configuration';
        $data['javascript'] = array('tabs_config');
        $data['requiredCruiseDataTransfers'] = $this->_cruiseDataTransfersModel->getRequiredCruiseDataTransfers();
        $data['shoresideDataWarehouseConfig'] = array();
        

        foreach($data['requiredCruiseDataTransfers'] as $row) {
            if(strcmp($row->name, 'SSDW') === 0 ) {
                $data['shoresideDataWarehouseConfig']['cruiseDataTransferID'] = $row->cruiseDataTransferID;
                $data['shoresideDataWarehouseConfig']['rsyncServer'] = $row->rsyncServer;
                $data['shoresideDataWarehouseConfig']['rsyncUser'] = $row->rsyncUser;
                $data['shoresideDataWarehouseConfig']['rsyncPass'] = $row->rsyncPass;
                $data['shoresideDataWarehouseConfig']['destDir'] = $row->destDir;
                break;
            }
        }
            
        if(isset($_POST['submit'])){
            $rsyncServer = $_POST['rsyncServer'];
            $rsyncUser = $_POST['rsyncUser'];
            $rsyncPass = $_POST['rsyncPass'];
            $destDir = $_POST['destDir'];

            if($rsyncServer == ''){
                $error[] = 'Shoreside Data Warehouse IP is required';
            }

            if($rsyncUser == ''){
                $error[] = 'Shipboard Data Warehouse Username is required';
            }

            if($rsyncPass == ''){
                $error[] = 'Shipboard Data Warehouse Password is required';
            }

            if($destDir == ''){
                $error[] = 'Shoreside Data Warehouse Base Directory is required';
            }

            if(!$error){
                $postdata = array(
                    'rsyncServer' => $rsyncServer,
                    'rsyncUser' => $rsyncUser,
                    'rsyncPass' => $rsyncPass,
                    'destDir' => $destDir,
                );
                
                $where = array('cruiseDataTransferID' => $data['shoresideDataWarehouseConfig']['cruiseDataTransferID']);
                            
                $this->_cruiseDataTransfersModel->updateCruiseDataTransfer($postdata, $where);
                Session::set('message','Shoreside Data Warehouse Updated');
                Url::redirect('config/system');
            } else {
                $data['shoresideDataWarehouseConfig'] = array(
                    'rsyncServer' => $rsyncServer,
                    'rsyncUser' => $rsyncUser,
                    'rsyncPass' => $rsyncPass,
                    'destDir' => $destDir,
                );
            }
        }
        
        View::rendertemplate('header',$data);
        View::render('Config/editShoresideDataWarehouse',$data, $error);
        View::rendertemplate('footer',$data);
    }
    
    public function editExtraDirectories($id){
        $data['title'] = 'Edit Extra Directory';
        $data['javascript'] = array('extraDirectoriesFormHelper', 'tabs_config');
        $data['row'] = $this->_extraDirectoriesModel->getExtraDirectory($id);

        if(isset($_POST['submit'])){
            $longName = $_POST['longName'];
            $destDir = $_POST['destDir'];

            if($longName == ''){
                $error[] = 'Long name is required';
            } 

            if($destDir == ''){
                $error[] = 'Destination directory is required';
            } 
                
            if(!$error){
                $postdata = array(
                    'longName' => $longName,
                    'destDir' => $destDir,
                );
            
                
                $where = array('extraDirectoryID' => $id);
                $this->_extraDirectoriesModel->updateExtraDirectory($postdata,$where);
                $this->updateCruiseDirectory();
                Session::set('message','Extra Directory Updated');
                Url::redirect('config/system');
            } else {
                
                $data['row'][0]->name = $name;
                $data['row'][0]->longName = $longName;
                $data['row'][0]->destDir = $destDir;
            }
        }

        View::rendertemplate('header',$data);
        View::render('Config/editRequiredExtraDirectories',$data,$error);
        View::rendertemplate('footer',$data);
    }
    
    public function editShipToShoreTransfers($id){
        $data['title'] = 'Edit Ship-to-Shore Transfer';
        $data['javascript'] = array('shipToShoreTransfersFormHelper', 'tabs_config');
        $data['row'] = $this->_shipToShoreTransfersModel->getShipToShoreTransfer($id);

        if(isset($_POST['submit'])){
            $longName = $_POST['longName'];
            $includeFilter = $_POST['includeFilter'];

            if($longName == ''){
                $error[] = 'Long name is required';
            }
            
            if($includeFilter == ''){
                $includeFilter = '*';
            } 

            if(!$error){
                $postdata = array(
                    'longName' => $longName,
                    'includeFilter' => $includeFilter,
                );
            
                
                $where = array('shipToShoreTransferID' => $id);
                $this->_shipToShoreTransfersModel->updateShipToShoreTransfer($postdata,$where);
                Session::set('message','Ship-to-Shore Transfers Updated');
                Url::redirect('config/system');
            } else {
                
                $data['row'][0]->longName = $longName;
                $data['row'][0]->includeFilter = $includeFilter;
            }
        }

        View::rendertemplate('header',$data);
        View::render('Config/editRequiredShipToShoreTransfers',$data,$error);
        View::rendertemplate('footer',$data);
    }
    
    public function enableShipToShoreTransfers($id) {

        $this->_shipToShoreTransfersModel->enableShipToShoreTransfer($id);
        Url::redirect('config/system');
    }
    
    public function disableShipToShoreTransfers($id) {

        $this->_shipToShoreTransfersModel->disableShipToShoreTransfer($id);
        Url::redirect('config/system');
    }
    
    public function editShipToShoreBWLimit(){
        $data['title'] = 'Edit Ship-to-Shore Bandwidth Limit';
        $data['javascript'] = array('tabs_config');
        $data['shipToShoreBWLimit'] = $this->_coreValuesModel->getShipToShoreBWLimit();

        if(isset($_POST['submit'])){
            $shipToShoreBWLimit = $_POST['shipToShoreBWLimit'];

            if($shipToShoreBWLimit == ''){
                $error[] = 'Bandwidth limit is required';
            } elseif (!is_numeric($shipToShoreBWLimit)){
                $error[] = 'Bandwidth limit must be a number';
            }
                
            if(!$error){
                $postdata = array(
                    'value' => $shipToShoreBWLimit
                );

                $this->_coreValuesModel->setShipToShoreBWLimit($postdata);
                Session::set('message','Ship-to-Shore Bandwidth Limit Updated');
                Url::redirect('config/system');
            } else {
                
                $data['shipToShoreBWLimit'] = $shipToShoreBWLimit;
            }
        }

        View::rendertemplate('header',$data);
        View::render('Config/editShipToShoreBWLimit',$data,$error);
        View::rendertemplate('footer',$data);
    }

    public function enableShipToShoreBWLimit() {

        $this->_coreValuesModel->enableShipToShoreBWLimit();
        Url::redirect('config/system');
    }
    
    public function disableShipToShoreBWLimit() {

        $this->_coreValuesModel->disableShipToShoreBWLimit();
        Url::redirect('config/system');
    }
    
    public function editMD5FilesizeLimit(){
        $data['title'] = 'Edit MD5 Checksum Filesize Limit';
        $data['javascript'] = array('tabs_config');
        $data['md5FilesizeLimit'] = $this->_coreValuesModel->getMd5FilesizeLimit();

        if(isset($_POST['submit'])){
            $md5FilesizeLimit = $_POST['md5FilesizeLimit'];

            if($md5FilesizeLimit == ''){
                $error[] = 'MD5 filesize limit is required';
            } elseif (!is_numeric($md5FilesizeLimit)){
                $error[] = 'MD5 filesize limit must be a number';
            }
                
            if(!$error){
                $postdata = array(
                    'value' => $md5FilesizeLimit
                );

                $this->_coreValuesModel->setMd5FilesizeLimit($postdata);
                Session::set('message','MD5 Filesize Limit Updated');
                Url::redirect('config/system');
            } else {
                
                $data['md5FilesizeLimit'] = $md5FilesizeLimit;
            }
        }

        View::rendertemplate('header',$data);
        View::render('Config/editMD5FilesizeLimit',$data,$error);
        View::rendertemplate('footer',$data);
    }
    
    public function enableMD5FilesizeLimit() {

        $this->_coreValuesModel->enableMd5FilesizeLimit();
        Url::redirect('config/system');
    }
    
    public function disableMD5FilesizeLimit() {

        $this->_coreValuesModel->disableMd5FilesizeLimit();
        Url::redirect('config/system');
    }

    public function testShipboardDataWarehouse() {
        
        $_warehouseModel = new \Models\Warehouse();
        $shipboardDataWarehouseConfig = $_warehouseModel->getShipboardDataWarehouseConfig();
        
        $data['testResults'] = array();
        
        $baseDirectoryTest = (object) array();
        $publicDataDirectoryTest = (object) array();
        $usernameTest = (object) array();
        $finalVerdict = (object) array();
        
        $finalVerdict->testName = 'FinalVerdict';
        $finalVerdict->result = 'Pass';
                
        $baseDirectoryTest->testName = 'Base Directory';
        if(is_dir( $shipboardDataWarehouseConfig['shipboardDataWarehouseBaseDir'] )) {
            $baseDirectoryTest->result = 'Pass';
        } else {
            $baseDirectoryTest->result = 'Fail';
            $finalVerdict->result = 'Fail';
        }
        
        array_push($data['testResults'], $baseDirectoryTest);

        $publicDataDirectoryTest->testName = 'Public Data Directory';
        if(is_dir( $shipboardDataWarehouseConfig['shipboardDataWarehousePublicDataDir'] )) {
            $publicDataDirectoryTest->result = 'Pass';
        } else {
            $publicDataDirectoryTest->result = 'Fail';
            $finalVerdict->result = 'Fail';
        }
        
        array_push($data['testResults'], $publicDataDirectoryTest);
        
        $command = 'getent passwd ' . $shipboardDataWarehouseConfig['shipboardDataWarehouseUsername'];
        exec($command,$op);
        
        $usernameTest->testName = 'Username';
        if(isset($op[0])) {
            $usernameTest->result = 'Pass';
        } else {
            $usernameTest->result = 'Fail';
            $finalVerdict->result = 'Fail';
        }
        
        array_push($data['testResults'], $usernameTest);
        array_push($data['testResults'], $finalVerdict);
        
        if (strcmp($finalVerdict->result, "Pass") === 0 ) {
            $_warehouseModel->clearErrorShipboardDataWarehouseStatus();
        } else {
            $_warehouseModel->setErrorShipboardDataWarehouseStatus();
        }
        
        $data['title'] = 'Configuration';
        $data['javascript'] = array('system', 'tabs_config');
        $data['requiredCruiseDataTransfers'] = $this->_cruiseDataTransfersModel->getRequiredCruiseDataTransfers();
        $data['requiredShipToShoreTransfers'] = $this->_shipToShoreTransfersModel->getRequiredShipToShoreTransfers();
        $data['requiredExtraDirectories'] = $this->_extraDirectoriesModel->getRequiredExtraDirectories();
        $data['shipboardDataWarehouseStatus'] = $this->_coreValuesModel->getShipboardDataWarehouseStatus();
        $data['shipToShoreBWLimit'] = $this->_coreValuesModel->getShipToShoreBWLimit();
        $data['shipToShoreBWLimitStatus'] = $this->_coreValuesModel->getShipToShoreBWLimitStatus();
        $data['md5FilesizeLimit'] = $this->_coreValuesModel->getMd5FilesizeLimit();
        $data['md5FilesizeLimitStatus'] = $this->_coreValuesModel->getMd5FilesizeLimitStatus();

        $freeSpace = $this->_coreValuesModel->getFreeSpace();
        
        if(isset($freeSpace['error'])){
            $data['freeSpace'] = "Error";
        }

        #additional data needed for view
        $data['testWarehouseName'] = 'Shipboard Data Warehouse';

        View::rendertemplate('header',$data);
        View::render('Config/system',$data);
        View::rendertemplate('footer',$data);
    }

 
    public function testShoresideDataWarehouse() {
        
        $_warehouseModel = new \Models\Warehouse();
        $gmData['siteRoot'] = DIR;
        $gmData['shipboardDataWarehouse'] = $_warehouseModel->getShipboardDataWarehouseConfig();
        $gmData['cruiseID'] = $_warehouseModel->getCruiseID();
        $requiredCruiseDataTransfers = $this->_cruiseDataTransfersModel->getRequiredCruiseDataTransfers();
        
        foreach($requiredCruiseDataTransfers as $row) {
            if(strcmp($row->name, 'SSDW') === 0 ) {
                $gmData['cruiseDataTransfer'] = $row;
                break;
            }
        }
        
        # create the gearman client
        $gmc= new \GearmanClient();

        # add the default server (localhost)
        $gmc->addServer();

        #submit job to Gearman, wait for results
        $data['testResults'] = json_decode($gmc->doNormal("testCruiseDataTransfer", json_encode($gmData)));
        
        # update collectionSystemTransfer status if needed
        #if(strcmp($data['testResults'][sizeof($data['testResults'])-1]->result, "Fail") === 0) {
        #    $this->_collectionSystemTransfersModel->setError_collectionSystemTransfer($id);
        #} else {
        #    $this->_collectionSystemTransfersModel->setIdle_collectionSystemTransfer($id);
        #}

        $data['title'] = 'Configuration';
        $data['javascript'] = array('system', 'tabs_config');
        $data['requiredCruiseDataTransfers'] = $this->_cruiseDataTransfersModel->getRequiredCruiseDataTransfers();
        $data['requiredShipToShoreTransfers'] = $this->_shipToShoreTransfersModel->getRequiredShipToShoreTransfers();
        $data['requiredExtraDirectories'] = $this->_extraDirectoriesModel->getRequiredExtraDirectories();
        $data['shipToShoreBWLimit'] = $this->_coreValuesModel->getShipToShoreBWLimit();
        $data['shipToShoreBWLimitStatus'] = $this->_coreValuesModel->getShipToShoreBWLimitStatus();
        $data['md5FilesizeLimit'] = $this->_coreValuesModel->getMd5FilesizeLimit();
        $data['md5FilesizeLimitStatus'] = $this->_coreValuesModel->getMd5FilesizeLimitStatus();

        $freeSpace = $this->_coreValuesModel->getFreeSpace();
        
        if(isset($freeSpace['error'])){
            $data['freeSpace'] = "Error";
        }

        #additional data needed for view
        $data['testWarehouseName'] = 'Shoreside Data Warehouse';

        View::rendertemplate('header',$data);
        View::render('Config/system',$data);
        View::rendertemplate('footer',$data);
    }

}
