<?php

namespace controllers\config;
use Core\Controller;
use Core\View;
use Helpers\Url;
use Helpers\Session;

class CollectionSystemTransfers extends Controller {

    private $_collectionSystemTransfersModel,
            $_transferTypesModel,
            $_messagesModel;
    
    private function _buildTransferTypesOptions() {
        $transferTypes = $this->_transferTypesModel->getTransferTypes();
        
        $output = array();
        $i=1;

        foreach($transferTypes as $row){
            $option = array('id'=>'transferType'.$i++, 'name'=>'transferType', 'value'=>$row->transferTypeID, 'label'=>$row->transferType);
            array_push($output, $option);
        }
        
        return $output;
    }
    
    private function _buildSSHOptions() {
        
        $trueFalse = array(array('id'=>'rsyncUseSSH0', 'name'=>'rsyncUseSSH', 'value'=>'0', 'label'=>'No'), array('id'=>'rsyncUseSSH1', 'name'=>'rsyncUseSSH', 'value'=>'1', 'label'=>'Yes'));
        return $trueFalse;
    }
    
    private function _buildStalenessOptions() {
        
        $trueFalse = array(array('id'=>'staleness0', 'name'=>'staleness', 'value'=>'0', 'label'=>'No'), array('id'=>'staleness1', 'name'=>'staleness', 'value'=>'5', 'label'=>'Yes'));
        return $trueFalse;
    }
    
    private function updateCruiseDirectory() {
        $_warehouseModel = new \Models\Warehouse();
        $warehouseConfig = $_warehouseModel->getShipboardDataWarehouseConfig();
        $cruiseID = $_warehouseModel->getCruiseID();
        if(is_dir($warehouseConfig['shipboardDataWarehouseBaseDir'] . '/' . $cruiseID)) {
            $gmData['siteRoot'] = DIR;
            $gmData['shipboardDataWarehouse'] = $warehouseConfig;
            $gmData['cruiseID'] = $cruiseID;
        
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

        $this->_collectionSystemTransfersModel = new \Models\Config\CollectionSystemTransfers();
        $this->_transferTypesModel = new \Models\Config\TransferTypes();
        $this->_messagesModel = new \Models\Config\Messages();
    }
        
    public function index(){
        $data['title'] = 'Configuration';
        $data['collectionSystemTransfers'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfers();
        $data['javascript'] = array('collectionSystemTransfers', 'tabs_config');
        View::rendertemplate('header',$data);
        View::render('Config/collectionSystemTransfers',$data);
        View::rendertemplate('footer',$data);
    }

    public function add(){
        $data['title'] = 'Collection System Transfers';
        $data['javascript'] = array('collectionSystemTransfersFormHelper', 'tabs_config');
        $data['transferTypeOptions'] = $this->_buildTransferTypesOptions();
        $data['rsyncUseSSHOptions'] = $this->_buildSSHOptions();
        $data['stalenessOptions'] = $this->_buildStalenessOptions();

        if(isset($_POST['submit'])){
            $name = $_POST['name'];
            $longName = $_POST['longName'];
            $transferType = $_POST['transferType'];
            $sourceDir = $_POST['sourceDir'];
            $destDir = $_POST['destDir'];
            $staleness = $_POST['staleness'];
            $rsyncServer = $_POST['rsyncServer'];
            $rsyncUseSSH = $_POST['rsyncUseSSH'];
            $rsyncUser = $_POST['rsyncUser'];
            $rsyncPass = $_POST['rsyncPass'];
            $smbServer = $_POST['smbServer'];
            $smbUser = $_POST['smbUser'];
            $smbPass = $_POST['smbPass'];
            $smbDomain = $_POST['smbDomain'];
            $includeFilter = $_POST['includeFilter'];
            $excludeFilter = $_POST['excludeFilter'];
            $ignoreFilter = $_POST['ignoreFilter'];
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

            if($sourceDir == ''){
                $error[] = 'Source Directory is required';
            } 

            if($destDir == ''){
                $error[] = 'Destination Directory is required';
            }
            
            if($includeFilter == ''){
                $includeFilter = '*';
            }

            
            if ($transferType == 1) { //local directory
                $smbServer = '';
                $smbUser = '';
                $smbDomain = '';
                $smbPass = '';
                $rsyncServer = '';
                $rsyncUser = '';
                $rsyncPass = '';
            
            } elseif ($transferType == 2) { // Rsync Server
                $rsyncDataCheck = true;
                if($rsyncServer == ''){
                    $error[] = 'Rsync Server is required';
                    $rsyncDataCheck = false;
                } 

                if($rsyncUser == ''){
                    $error[] = 'Rsync Username is required';
                    $rsyncDataCheck = false;

                } 

                if(($rsyncUseSSH == 1  && $rsyncPass == '') || ($rsyncUser != 'anonymous' && $rsyncPass == '')){
                    $error[] = 'Rsync Password is required';
                    $rsyncDataCheck = false;
                }
                
                if($rsyncDataCheck) {
                    $smbServer = '';
                    $smbUser = '';
                    $smbDomain = '';
                    $smbPass = '';
                }       

            } elseif ($transferType == 3) { // SMB Share
                $smbDataCheck = true;
                if($smbServer == ''){
                    $error[] = 'SMB Server is required';
                    $smbDataCheck = false;
                } 

                if($smbUser == ''){
                    $error[] = 'SMB Username is required';
                    $smbDataCheck = false;
                } 

                if($smbUser != 'guest' && $smbPass == ''){
                    $error[] = 'SMB Password is required';
                    $smbDataCheck = false;
                }
                
                if($smbDomain == ''){
                    $smbDomain = 'WORKGROUP'; // Default value
                    $smbDataCheck = false;
                }
                
                if($smbDataCheck) {
                    $rsyncServer = '';
                    $rsyncUser = '';
                    $rsyncPass = '';
                }
            }    
            
            if(!$error){
                $postdata = array(
                    'name' => $name,
                    'longName' => $longName,
                    'transferType' => $transferType,
                    'sourceDir' => $sourceDir,
                    'destDir' => $destDir,
                    'staleness' => $staleness,
                    'rsyncServer' => $rsyncServer,
                    'rsyncUseSSH' => $rsyncUseSSH,
                    'rsyncUser' => $rsyncUser,
                    'rsyncPass' => $rsyncPass,
                    'smbServer' => $smbServer,
                    'smbUser' => $smbUser,
                    'smbPass' => $smbPass,
                    'smbDomain' => $smbDomain,
                    'includeFilter' => $includeFilter,
                    'excludeFilter' => $excludeFilter,
                    'ignoreFilter' => $ignoreFilter,
                    'status' => $status,
                    'enable' => $enable,
                );

                $this->_collectionSystemTransfersModel->insertCollectionSystemTransfer($postdata);

                Session::set('message','Collection System Transfer Added');
                Url::redirect('config/collectionSystemTransfers');
            }
        }

        View::rendertemplate('header',$data);
        View::render('Config/addCollectionSystemTransfers',$data,$error);
        View::rendertemplate('footer',$data);
    }
        
    public function edit($id){
        $data['title'] = 'Collection System Transfers';
        $data['javascript'] = array('collectionSystemTransfersFormHelper', 'tabs_config');
        $data['row'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfer($id);
        
        
        if(isset($_POST['submit'])){
            $name = $_POST['name'];
            $longName = $_POST['longName'];
            $transferType = $_POST['transferType'];
            $sourceDir = $_POST['sourceDir'];
            $destDir = $_POST['destDir'];
            $staleness = $_POST['staleness'];
            $rsyncServer = $_POST['rsyncServer'];
            $rsyncUseSSH = $_POST['rsyncUseSSH'];
            $rsyncUser = $_POST['rsyncUser'];
            $rsyncPass = $_POST['rsyncPass'];
            $smbServer = $_POST['smbServer'];
            $smbUser = $_POST['smbUser'];
            $smbPass = $_POST['smbPass'];
            $smbDomain = $_POST['smbDomain'];
            $includeFilter = $_POST['includeFilter'];
            $excludeFilter = $_POST['excludeFilter'];
            $ignoreFilter = $_POST['ignoreFilter'];
//            $status = $_POST['status'];
//            $enable = $_POST['enable'];

            if($name == ''){
                $error[] = 'Name is required';
            } 

            if($longName == ''){
                $error[] = 'Long name is required';
            } 

            if($transferType == ''){
                $error[] = 'Transfer type is required';
            } 

            if($sourceDir == ''){
                $error[] = 'Source Directory is required';
            } 

            if($destDir == ''){
                $error[] = 'Destination Directory is required';
            } 

            if($includeFilter == ''){
                $includeFilter = '*';
            }
            
            if ($transferType == 1) { //local directory
                $smbServer = '';
                $smbUser = '';
                $smbDomain = '';
                $smbPass = '';
                $rsyncServer = '';
                $rsyncUser = '';
                $rsyncPass = '';
            
            } elseif ($transferType == 2) { //rsync
                $rsyncDataCheck = true;
                if($rsyncServer == ''){
                    $error[] = 'Rsync Server is required';
                    $rsyncDataCheck = false;
                } 

                if($rsyncUser == ''){
                    $error[] = 'Rsync Username is required';
                    $rsyncDataCheck = false;
                } 

                if(($rsyncUseSSH == 1  && $rsyncPass == '') || ($rsyncUser != 'anonymous' && $rsyncPass == '')){
                    $error[] = 'Rsync Password is required';
                    $rsyncDataCheck = false;
                }
                
                if($rsyncDataCheck) {
                    $smbServer = '';
                    $smbUser = '';
                    $smbDomain = '';
                    $smbPass = '';
                } 

            } elseif ($transferType == 3) { //smb
                $smbDataCheck = true;
                if($smbServer == ''){
                    $error[] = 'SMB Server is required';
                    $smbDataCheck = false;
                } 

                if($smbUser == ''){
                    $error[] = 'SMB Username is required';
                    $smbDataCheck = false;
                } 

                if($smbUser != 'guest' && $smbPass == ''){
                    $error[] = 'SMB Password is required';
                    $smbDataCheck = false;
                }
                
                if($smbDomain == ''){
                    $smbDomain = 'WORKGROUP';
                    $smbDataCheck = false;
                }
                
                if($smbDataCheck) {
                    $rsyncServer = '';
                    $rsyncUser = '';
                    $rsyncPass = '';
                }
            
//            } elseif ($transferType == 4) { //push
            
            }
                
            if(!$error){
                $postdata = array(
                    'name' => $name,
                    'longName' => $longName,
                    'transferType' => $transferType,
                    'sourceDir' => $sourceDir,
                    'destDir' => $destDir,
                    'staleness' => $staleness,
                    'rsyncServer' => $rsyncServer,
                    'rsyncUseSSH' => $rsyncUseSSH,
                    'rsyncUser' => $rsyncUser,
                    'rsyncPass' => $rsyncPass,
                    'smbServer' => $smbServer,
                    'smbUser' => $smbUser,
                    'smbPass' => $smbPass,
                    'smbDomain' => $smbDomain,
                    'includeFilter' => $includeFilter,
                    'excludeFilter' => $excludeFilter,
                    'ignoreFilter' => $ignoreFilter,
//                    'status' => $status,
//                    'enable' => $enable
                );
            
                
                $where = array('collectionSystemTransferID' => $id);
                $this->_collectionSystemTransfersModel->updateCollectionSystemTransfer($postdata,$where);
                
                if($data['row'][0]->destDir != $destDir){
                    $this->updateCruiseDirectory();
                }
                
                Session::set('message','Collection System Transfers Updated');
                Url::redirect('config/collectionSystemTransfers');
            } else {
                
                $data['row'][0]->name = $name;
                $data['row'][0]->longName = $longName;
                $data['row'][0]->transferType = $transferType;
                $data['row'][0]->sourceDir = $sourceDir;
                $data['row'][0]->destDir = $destDir;
                $data['row'][0]->staleness = $staleness;
                $data['row'][0]->rsyncServer = $rsyncServer;
                $data['row'][0]->rsyncUseSSH = $rsyncUseSSH;
                $data['row'][0]->rsyncUser = $rsyncUser;
                $data['row'][0]->rsyncPass = $rsyncPass;
                $data['row'][0]->smbServer = $smbServer;
                $data['row'][0]->smbUser = $smbUser;
                $data['row'][0]->smbPass = $smbPass;
                $data['row'][0]->smbDomain = $smbDomain;
                $data['row'][0]->includeFilter = $includeFilter;
                $data['row'][0]->excludeFilter = $excludeFilter;
                $data['row'][0]->ignoreFilter = $ignoreFilter;
            }
        } else if(isset($_POST['inlineTest'])){
            $_warehouseModel = new \Models\Warehouse();
            $gmData['siteRoot'] = DIR;
            $gmData['shipboardDataWarehouse'] = $_warehouseModel->getShipboardDataWarehouseConfig();
            $gmData['cruiseID'] = $_warehouseModel->getCruiseID();
            $gmData['collectionSystemTransfer'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfer($id)[0];
            
            $gmData['collectionSystemTransfer']->name = $_POST['name'];
            $gmData['collectionSystemTransfer']->longName = $_POST['longName'];
            $gmData['collectionSystemTransfer']->transferType = $_POST['transferType'];
            $gmData['collectionSystemTransfer']->sourceDir = $_POST['sourceDir'];
            $gmData['collectionSystemTransfer']->destDir = $_POST['destDir'];
            $gmData['collectionSystemTransfer']->staleness = $_POST['staleness'];
            $gmData['collectionSystemTransfer']->rsyncServer = $_POST['rsyncServer'];
            $gmData['collectionSystemTransfer']->rsyncUseSSH = $_POST['rsyncUseSSH'];
            $gmData['collectionSystemTransfer']->rsyncUser = $_POST['rsyncUser'];
            $gmData['collectionSystemTransfer']->rsyncPass = $_POST['rsyncPass'];
            $gmData['collectionSystemTransfer']->smbServer = $_POST['smbServer'];
            $gmData['collectionSystemTransfer']->smbUser = $_POST['smbUser'];
            $gmData['collectionSystemTransfer']->smbPass = $_POST['smbPass'];
            $gmData['collectionSystemTransfer']->smbDomain = $_POST['smbDomain'];
            $gmData['collectionSystemTransfer']->includeFilter = $_POST['includeFilter'];
            $gmData['collectionSystemTransfer']->excludeFilter = $_POST['excludeFilter'];
            $gmData['collectionSystemTransfer']->ignoreFilter = $_POST['ignoreFilter'];
            
            # create the gearman client
            $gmc= new \GearmanClient();

            # add the default server (localhost)
            $gmc->addServer();

            #submit job to Gearman, wait for results
            $data['testResults'] = json_decode($gmc->doNormal("testCollectionSystemTransfer", json_encode($gmData)));

            #$data['title'] = 'Configuration';
            #$data['collectionSystemTransfers'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfers();
            #$data['javascript'] = array('collectionSystemTransfers', 'tabs_config');

            #additional data needed for view
            $data['row'][0]->name = $_POST['name'];
            $data['row'][0]->longName = $_POST['longName'];
            $data['row'][0]->transferType = $_POST['transferType'];
            $data['row'][0]->sourceDir = $_POST['sourceDir'];
            $data['row'][0]->destDir = $_POST['destDir'];
            $data['row'][0]->staleness = $_POST['staleness'];
            $data['row'][0]->rsyncServer = $_POST['rsyncServer'];
            $data['row'][0]->rsyncUseSSH = $_POST['rsyncUseSSH'];
            $data['row'][0]->rsyncUser = $_POST['rsyncUser'];
            $data['row'][0]->rsyncPass = $_POST['rsyncPass'];
            $data['row'][0]->smbServer = $_POST['smbServer'];
            $data['row'][0]->smbUser = $_POST['smbUser'];
            $data['row'][0]->smbPass = $_POST['smbPass'];
            $data['row'][0]->smbDomain = $_POST['smbDomain'];
            $data['row'][0]->includeFilter = $_POST['includeFilter'];
            $data['row'][0]->excludeFilter = $_POST['excludeFilter'];
            $data['row'][0]->ignoreFilter = $_POST['ignoreFilter'];
            
            $data['testCollectionSystemTransferName'] = $gmData['collectionSystemTransfer']->name;      
        }
        
        $data['transferTypeOptions'] = $this->_buildTransferTypesOptions();
        $data['stalenessOptions'] = $this->_buildStalenessOptions();
        $data['rsyncUseSSHOptions'] = $this->_buildSSHOptions();

        View::rendertemplate('header',$data);
        View::render('Config/editCollectionSystemTransfers',$data,$error);
        View::rendertemplate('footer',$data);
    }
    
    public function delete($id){
                
        $where = array('collectionSystemTransferID' => $id);
        $this->_collectionSystemTransfersModel->deleteCollectionSystemTransfer($where);
        Session::set('message','Collection System Transfer Deleted');
        Url::redirect('config/collectionSystemTransfers');
    }
    
    public function enable($id) {
        $this->_collectionSystemTransfersModel->enableCollectionSystemTransfer($id);

        $this->updateCruiseDirectory();

        Url::redirect('config/collectionSystemTransfers');
    }
    
    public function disable($id) {
        $this->_collectionSystemTransfersModel->disableCollectionSystemTransfer($id);
        Url::redirect('config/collectionSystemTransfers');
    }
    
    public function test($id) {
        
        $_warehouseModel = new \Models\Warehouse();
        $gmData['siteRoot'] = DIR;
        $gmData['shipboardDataWarehouse'] = $_warehouseModel->getShipboardDataWarehouseConfig();
        $gmData['cruiseID'] = $_warehouseModel->getCruiseID();
        $gmData['collectionSystemTransfer'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfer($id)[0];
                
        # create the gearman client
        $gmc= new \GearmanClient();

        # add the default server (localhost)
        $gmc->addServer();

        #submit job to Gearman, wait for results
        $data['testResults'] = json_decode($gmc->doNormal("testCollectionSystemTransfer", json_encode($gmData)));

        $data['title'] = 'Configuration';
        $data['collectionSystemTransfers'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfers();
        $data['javascript'] = array('collectionSystemTransfers', 'tabs_config');

        #additional data needed for view
        $data['testCollectionSystemTransferName'] = $gmData['collectionSystemTransfer']->name;

        View::rendertemplate('header',$data);
        View::render('Config/collectionSystemTransfers',$data);
        View::rendertemplate('footer',$data);
    }
    
    public function run($id) {
        
        $_warehouseModel = new \Models\Warehouse();
        $gmData['siteRoot'] = DIR;
        $gmData['shipboardDataWarehouse'] = $_warehouseModel->getshipboardDataWarehouseConfig();
        $gmData['cruiseID'] = $_warehouseModel->getCruiseID();
        $gmData['collectionSystemTransfer'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfer($id)[0];
        $gmData['collectionSystemTransfer']->enable = "1";
        $gmData['systemStatus'] = "On";
        
        # create the gearman client
        $gmc= new \GearmanClient();

        # add the default server (localhost)
        $gmc->addServer();

        #submit job to Gearman
        $job_handle = $gmc->doBackground("runCollectionSystemTransfer", json_encode($gmData));

        sleep(1);

        Url::redirect('config/collectionSystemTransfers');
    }
    
    public function stop($id) {
        
        $_warehouseModel = new \Models\Warehouse();
        $gmData['siteRoot'] = DIR;
        $gmData['pid'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfer($id)[0]->pid;
        
        # create the gearman client
        $gmc= new \GearmanClient();

        # add the default server (localhost)
        $gmc->addServer();

        #submit job to Gearman
        $job_handle = $gmc->doBackground("stopJob", json_encode($gmData));

        sleep(1);

        Url::redirect('config/collectionSystemTransfers');
    }
}