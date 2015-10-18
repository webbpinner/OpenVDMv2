<?php

namespace Controllers\Config;
use Core\Controller;
use Core\View;
use Helpers\Url;
use Helpers\Session;

class CruiseDataTransfers extends Controller {

    private $_cruiseDataTransfersModel,
            $_transferTypesModel;
    
    private function _buildTransferTypesOptions($checkedType = null) {
        $transferTypes = $this->_transferTypesModel->getTransferTypes();
        
        $output = array();
        $i=1;

        foreach($transferTypes as $row){
            $option = array('id'=>'transferType'.$i++, 'name'=>'transferType', 'value'=>$row->transferTypeID, 'label'=>$row->transferType);
            if($checkedType === $row->transferTypeID) {
                $option['checked']='1';
            }
            array_push($output, $option);
        }

        if(!isset($checkedType)) {
            $output[0]['checked']='1';
        }        
        return $output;
    }
    
    private function _buildSSHOptions() {
        
        $trueFalse = array(array('id'=>'rsyncUseSSH0', 'name'=>'rsyncUseSSH', 'value'=>0, 'label'=>'false'), array('id'=>'rsyncUseSSH1', 'name'=>'rsyncUseSSH', 'value'=>1, 'label'=>'true'));
        return $trueFalse;
    }
    
    public function __construct(){
        if(!Session::get('loggedin')){
            Url::redirect('config/login');
        }

        $this->_cruiseDataTransfersModel = new \Models\Config\CruiseDataTransfers();
        $this->_transferTypesModel = new \Models\Config\TransferTypes();
    }

    public function index(){
        $data['title'] = 'Configuration';
        $data['javascript'] = array('cruiseDataTransfers', 'tabs_config');
        $data['cruiseDataTransfers'] = $this->_cruiseDataTransfersModel->getCruiseDataTransfers();
        View::rendertemplate('header',$data);
        View::render('Config/cruiseDataTransfers',$data);
        View::rendertemplate('footer',$data);
    }

    public function add(){
        $data['title'] = 'Add Cruise Data Transfer';
        $data['javascript'] = array('cruiseDataTransfersFormHelper', 'tabs_config');
        $data['transferTypeOptions'] = $this->_buildTransferTypesOptions($_POST['transferType']);

        if(isset($_POST['submit'])){
            $name = $_POST['name'];
            $longName = $_POST['longName'];
            $transferType = $_POST['transferType'];
            $destDir = $_POST['destDir'];
            $rsyncServer = $_POST['rsyncServer'];
            $rsyncUser = $_POST['rsyncUser'];
            $rsyncPass = $_POST['rsyncPass'];
            $smbServer = $_POST['smbServer'];
            $smbUser = $_POST['smbUser'];
            $smbPass = $_POST['smbPass'];
            $smbDomain = $_POST['smbDomain'];
            $status = 3;
            $enable = 0;

            if($name == ''){
                $error[] = 'Name is required';
            } 

            if($longName == ''){
                $error[] = 'Long name is required';
            } 

            if($transferType == ''){
                $error[] = 'Transfer type is required';
            } 

            if($destDir == ''){
                $error[] = 'Destination Directory is required';
            } 

            if ($transferType == 2) { // Rsync Server
                if($rsyncServer == ''){
                    $error[] = 'Rsync Server is required';
                } 

                if($rsyncUser == ''){
                    $error[] = 'Rsync Username is required';
                } 

                if($rsyncPass == ''){
                    $error[] = 'Rsync Password is required';
                } 

            } elseif ($transferType == 3) { // SMB Share
                if($smbServer == ''){
                    $error[] = 'SMB Server is required';
                } 

                if($smbUser == ''){
                    $error[] = 'SMB Username is required';
                } 

                if($smbPass == ''){
                    $error[] = 'SMB Password is required';
                } 
            
                if($smbDomain == ''){
                    $smbDomain = 'WORKGROUP';
                } 
            
//            } elseif ($transferType == 4) { //push
            
            }

            if(!$error){
                $postdata = array(
                    'name' => $name,
                    'longName' => $longName,
                    'transferType' => $transferType,
                    'destDir' => $destDir,
                    'rsyncServer' => $rsyncServer,
                    'rsyncUser' => $rsyncUser,
                    'rsyncPass' => $rsyncPass,
                    'smbServer' => $smbServer,
                    'smbUser' => $smbUser,
                    'smbPass' => $smbPass,
                    'smbDomain' => $smbDomain,
                    'status' => $status,
                    'enable' => $enable
                );

                $this->_cruiseDataTransfersModel->insertCruiseDataTransfer($postdata);
                Session::set('message','Cruise Data Transfer Added');
                Url::redirect('config/cruiseDataTransfers');
            }
        } elseif(isset($_POST['inlineTest'])){
            $name = $_POST['name'];
            $longName = $_POST['longName'];
            $transferType = $_POST['transferType'];
            $destDir = $_POST['destDir'];
            $rsyncServer = $_POST['rsyncServer'];
            $rsyncUser = $_POST['rsyncUser'];
            $rsyncPass = $_POST['rsyncPass'];
            $smbServer = $_POST['smbServer'];
            $smbUser = $_POST['smbUser'];
            $smbPass = $_POST['smbPass'];
            $smbDomain = $_POST['smbDomain'];
            $status = 3;
            $enable = 0;

            if($name == ''){
                $error[] = 'Name is required';
            } 

            if($longName == ''){
                $error[] = 'Long name is required';
            } 

            if($transferType == ''){
                $error[] = 'Transfer type is required';
            } 

            if($destDir == ''){
                $error[] = 'Destination Directory is required';
            } 

            if ($transferType == 2) { // Rsync Server
                if($rsyncServer == ''){
                    $error[] = 'Rsync Server is required';
                } 

                if($rsyncUser == ''){
                    $error[] = 'Rsync Username is required';
                } 

                if($rsyncPass == ''){
                    $error[] = 'Rsync Password is required';
                } 

            } elseif ($transferType == 3) { // SMB Share
                if($smbServer == ''){
                    $error[] = 'SMB Server is required';
                } 

                if($smbUser == ''){
                    $error[] = 'SMB Username is required';
                } 

                if($smbPass == ''){
                    $error[] = 'SMB Password is required';
                } 
            
                if($smbDomain == ''){
                    $smbDomain = 'WORKGROUP';
                } 
            
//            } elseif ($transferType == 4) { //push
            
            }

            if(!$error){
                $_warehouseModel = new \Models\Warehouse();
                $gmData['siteRoot'] = DIR;
                $gmData['shipboardDataWarehouse'] = $_warehouseModel->getShipboardDataWarehouseConfig();
                $gmData['cruiseID'] = $_warehouseModel->getCruiseID();
                $gmData['cruiseDataTransfer'] = (object)array(
                    'name' => $name,
                    'longName' => $longName,
                    'transferType' => $transferType,
                    'destDir' => $destDir,
                    'rsyncServer' => $rsyncServer,
                    'rsyncUser' => $rsyncUser,
                    'rsyncPass' => $rsyncPass,
                    'smbServer' => $smbServer,
                    'smbUser' => $smbUser,
                    'smbPass' => $smbPass,
                    'smbDomain' => $smbDomain,
                    'status' => '4',
                    'enable' => '0'
                    );
            
                # create the gearman client
                $gmc= new \GearmanClient();

                # add the default server (localhost)
                $gmc->addServer();

                #submit job to Gearman, wait for results
                $data['testResults'] = json_decode($gmc->doNormal("testCruiseDataTransfer", json_encode($gmData)));

                #$data['title'] = 'Configuration';
                #$data['collectionSystemTransfers'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfers();
                #$data['javascript'] = array('collectionSystemTransfers', 'tabs_config');

                #additional data needed for view
                #$data['row'][0]->name = $_POST['name'];
                #$data['row'][0]->longName = $_POST['longName'];
                #$data['row'][0]->transferType = $_POST['transferType'];
                #$data['row'][0]->destDir = $_POST['destDir'];
                #$data['row'][0]->rsyncServer = $_POST['rsyncServer'];
                #$data['row'][0]->rsyncUser = $_POST['rsyncUser'];
                #$data['row'][0]->rsyncPass = $_POST['rsyncPass'];
                #$data['row'][0]->smbServer = $_POST['smbServer'];
                #$data['row'][0]->smbUser = $_POST['smbUser'];
                #$data['row'][0]->smbPass = $_POST['smbPass'];
                #$data['row'][0]->smbDomain = $_POST['smbDomain'];
            
                $data['testCruiseDataTransferName'] = $gmData['cruiseDataTransfer']->name;     
            }
        }

        View::rendertemplate('header',$data);
        View::render('Config/addCruiseDataTransfers',$data,$error);
        View::rendertemplate('footer',$data);
    }
        
    public function edit($id){
        $data['title'] = 'Edit Cruise Data Transfer';
        $data['javascript'] = array('cruiseDataTransfersFormHelper', 'tabs_config');
        $data['transferTypeOptions'] = $this->_buildTransferTypesOptions($data['row'][0]->transferType);
        $data['rsyncUseSSHOptions'] = $this->_buildSSHOptions();
        $data['row'] = $this->_cruiseDataTransfersModel->getCruiseDataTransfer($id);

        if(isset($_POST['submit'])){
            $name = $_POST['name'];
            $longName = $_POST['longName'];
            $transferType = $_POST['transferType'];
            $destDir = $_POST['destDir'];
            $rsyncServer = $_POST['rsyncServer'];
            $rsyncUser = $_POST['rsyncUser'];
            $rsyncPass = $_POST['rsyncPass'];
            $smbServer = $_POST['smbServer'];
            $smbUser = $_POST['smbUser'];
            $smbPass = $_POST['smbPass'];
            $smbDomain = $_POST['smbDomain'];

            if($name == ''){
                $error[] = 'Name is required';
            } 

            if($longName == ''){
                $error[] = 'Long name is required';
            } 

            if($transferType == ''){
                $error[] = 'Transfer type is required';
            } 

            if($destDir == ''){
                $error[] = 'Destination Directory is required';
            } 

            if ($transferType == 2) { //rsync
                if($rsyncServer == ''){
                    $error[] = 'Rsync Server is required';
                } 

                if($rsyncUser == ''){
                    $error[] = 'Rsync Username is required';
                } 

                if($rsyncPass == ''){
                    $error[] = 'Rsync Password is required';
                } 

            } elseif ($transferType == 3) { //smb
                if($smbServer == ''){
                    $error[] = 'SMB Server is required';
                } 

                if($smbUser == ''){
                    $error[] = 'SMB Username is required';
                } 

                if($smbPass == ''){
                    $error[] = 'SMB Password is required';
                } 
                        
                if($smbDomain == ''){
                    $smbDomain = 'WORKGROUP';
                } 
            }
                
            if(!$error){
                $postdata = array(
                    'name' => $name,
                    'longName' => $longName,
                    'transferType' => $transferType,
                    'destDir' => $destDir,
                    'rsyncServer' => $rsyncServer,
                    'rsyncUser' => $rsyncUser,
                    'rsyncPass' => $rsyncPass,
                    'smbServer' => $smbServer,
                    'smbUser' => $smbUser,
                    'smbPass' => $smbPass,
                    'smbDomain' => $smbDomain,
                );
            
                
                $where = array('cruiseDataTransferID' => $id);
                $this->_cruiseDataTransfersModel->updateCruiseDataTransfer($postdata,$where);
                Session::set('message','Cruise Data Transfers Updated');
                Url::redirect('config/cruiseDataTransfers');
            } else {
                
                $data['row'][0]->name = $name;
                $data['row'][0]->longName = $longName;
                $data['row'][0]->transferType = $transferType;
                $data['row'][0]->destDir = $destDir;
                $data['row'][0]->rsyncServer = $rsyncServer;
                $data['row'][0]->rsyncUser = $rsyncUser;
                $data['row'][0]->rsyncPass = $rsyncPass;
                $data['row'][0]->smbServer = $smbServer;
                $data['row'][0]->smbUser = $smbUser;
                $data['row'][0]->smbPass = $smbPass;
                $data['row'][0]->smbDomain = $smbDomain;
            }
        } else if(isset($_POST['inlineTest'])){
            $_warehouseModel = new \Models\Warehouse();
            $gmData['siteRoot'] = DIR;
            $gmData['shipboardDataWarehouse'] = $_warehouseModel->getShipboardDataWarehouseConfig();
            $gmData['cruiseID'] = $_warehouseModel->getCruiseID();
            $gmData['cruiseDataTransfer'] = $this->_cruiseDataTransfersModel->getCruiseDataTransfer($id)[0];
            
            $gmData['cruiseDataTransfer']->name = $_POST['name'];
            $gmData['cruiseDataTransfer']->longName = $_POST['longName'];
            $gmData['cruiseDataTransfer']->transferType = $_POST['transferType'];
            $gmData['cruiseDataTransfer']->destDir = $_POST['destDir'];
            $gmData['cruiseDataTransfer']->rsyncServer = $_POST['rsyncServer'];
            $gmData['cruiseDataTransfer']->rsyncUser = $_POST['rsyncUser'];
            $gmData['cruiseDataTransfer']->rsyncPass = $_POST['rsyncPass'];
            $gmData['cruiseDataTransfer']->smbServer = $_POST['smbServer'];
            $gmData['cruiseDataTransfer']->smbUser = $_POST['smbUser'];
            $gmData['cruiseDataTransfer']->smbPass = $_POST['smbPass'];
            $gmData['cruiseDataTransfer']->smbDomain = $_POST['smbDomain'];
            
            # create the gearman client
            $gmc= new \GearmanClient();

            # add the default server (localhost)
            $gmc->addServer();

            #submit job to Gearman, wait for results
            $data['testResults'] = json_decode($gmc->doNormal("testCruiseDataTransfer", json_encode($gmData)));

            #$data['title'] = 'Configuration';
            #$data['collectionSystemTransfers'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfers();
            #$data['javascript'] = array('collectionSystemTransfers', 'tabs_config');

            #additional data needed for view
            $data['row'][0]->name = $_POST['name'];
            $data['row'][0]->longName = $_POST['longName'];
            $data['row'][0]->transferType = $_POST['transferType'];
            $data['row'][0]->destDir = $_POST['destDir'];
            $data['row'][0]->rsyncServer = $_POST['rsyncServer'];
            $data['row'][0]->rsyncUser = $_POST['rsyncUser'];
            $data['row'][0]->rsyncPass = $_POST['rsyncPass'];
            $data['row'][0]->smbServer = $_POST['smbServer'];
            $data['row'][0]->smbUser = $_POST['smbUser'];
            $data['row'][0]->smbPass = $_POST['smbPass'];
            $data['row'][0]->smbDomain = $_POST['smbDomain'];
            
            $data['testCruiseDataTransferName'] = $gmData['cruiseDataTransfer']->name;      
        }
        
        View::rendertemplate('header',$data);
        View::render('Config/editCruiseDataTransfers',$data,$error);
        View::rendertemplate('footer',$data);
    }
    
    public function test($id) {
        
        $_warehouseModel = new \Models\Warehouse();
        $gmData['siteRoot'] = DIR;
        $gmData['shipboardDataWarehouse'] = $_warehouseModel->getShipboardDataWarehouseConfig();
        $gmData['cruiseID'] = $_warehouseModel->getCruiseID();
        $gmData['cruiseDataTransfer'] = $this->_cruiseDataTransfersModel->getCruiseDataTransfer($id)[0];
                
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
        $data['cruiseDataTransfers'] = $this->_cruiseDataTransfersModel->getCruiseDataTransfers();
        $data['javascript'] = array('cruiseDataTransfers', 'tabs_config');

        #additional data needed for view
        $data['testCruiseDataTransferName'] = $gmData['cruiseDataTransfer']->longName;

        View::rendertemplate('header',$data);
        View::render('Config/cruiseDataTransfers',$data);
        View::rendertemplate('footer',$data);
    }
    
    public function run($id) {
        
        $_warehouseModel = new \Models\Warehouse();
        $gmData['siteRoot'] = DIR;
        $gmData['shipboardDataWarehouse'] = $_warehouseModel->getShipboardDataWarehouseConfig();
        $gmData['cruiseID'] = $_warehouseModel->getCruiseID();
        $gmData['cruiseDataTransfer'] = $this->_cruiseDataTransfersModel->getCruiseDataTransfer($id)[0];
        $gmData['cruiseDataTransfer']->enable = "1";
        $gmData['systemStatus'] = "On";

        
        # create the gearman client
        $gmc= new \GearmanClient();

        # add the default server (localhost)
        $gmc->addServer();

        #submit job to Gearman
        $job_handle = $gmc->doBackground("runCruiseDataTransfer", json_encode($gmData));
    
    //    $done = false;
    //    do
    //    {
            sleep(1);
    //        $stat = $gmc->jobStatus($job_handle);
    //        if ($stat[0]) // the job is known so it has been added to gearman 
    //            $done = true;
    //    }
    //    while(!$done);
        
        Url::redirect('config/cruiseDataTransfers');
    }
        
    public function stop($id) {
        
        $_warehouseModel = new \Models\Warehouse();
        $gmData['siteRoot'] = DIR;
        $gmData['pid'] = $this->_cruiseDataTransfersModel->getCruiseDataTransfer($id)[0]->pid;
        
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
        
        Url::redirect('config/cruiseDataTransfers');
    }
    
    public function delete($id){
                
        $where = array('cruiseDataTransferID' => $id);
        $this->_cruiseDataTransfersModel->deleteCruiseDataTransfer($where);
        Session::set('message','Collection System Transfer Deleted');
        Url::redirect('config/cruiseDataTransfers');
    }
    
    public function enable($id) {

        $this->_cruiseDataTransfersModel->enableCruiseDataTransfer($id);
        Url::redirect('config/cruiseDataTransfers');
    }
    
    public function disable($id) {

        $this->_cruiseDataTransfersModel->disableCruiseDataTransfer($id);
        Url::redirect('config/cruiseDataTransfers');
    }

}