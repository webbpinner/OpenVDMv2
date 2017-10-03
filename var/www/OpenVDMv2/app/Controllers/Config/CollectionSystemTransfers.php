<?php

namespace controllers\config;
use Core\Controller;
use Core\View;
use Helpers\Url;
use Helpers\Session;

class CollectionSystemTransfers extends Controller {

    private $_collectionSystemTransfersModel,
            $_transferTypesModel;
    
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
    
    private function _buildStalenessOptions() {
        
        $trueFalse = array(array('id'=>'staleness0', 'name'=>'staleness', 'value'=>'0', 'label'=>'No'), array('id'=>'staleness1', 'name'=>'staleness', 'value'=>'5', 'label'=>'Yes'));
        return $trueFalse;
    }
    
    private function _buildUseStartDateOptions() {
        
        $trueFalse = array(array('id'=>'useStartDate0', 'name'=>'useStartDate', 'value'=>'0', 'label'=>'No'), array('id'=>'useStartDate1', 'name'=>'useStartDate', 'value'=>'1', 'label'=>'Yes'));
        return $trueFalse;
    }
    

    private function _buildUseSSHKeyOptions() {
        
        $trueFalse = array(array('id'=>'useSSHKey0', 'name'=>'sshUseKey', 'value'=>'0', 'label'=>'No'), array('id'=>'useSSHKey1', 'name'=>'sshUseKey', 'value'=>'1', 'label'=>'Yes'));
        return $trueFalse;
    }

    private function _buildUseLocalMountPointOptions() {
        
        $trueFalse = array(array('id'=>'localDirIsMountPoint0', 'name'=>'localDirIsMountPoint', 'value'=>'0', 'label'=>'No'), array('id'=>'localDirIsMountPoint1', 'name'=>'localDirIsMountPoint', 'value'=>'1', 'label'=>'Yes'));
        return $trueFalse;
    }

    private function _buildCruiseOrLoweringOptions() {
        
        $output = array(array('id'=>'cruiseOrLowering0', 'name'=>'cruiseOrLowering', 'value'=>'0', 'label'=>'Cruise'), array('id'=>'cruiseOrLowering1', 'name'=>'cruiseOrLowering', 'value'=>'1', 'label'=>'Lowering'));
        return $output;
    }


    private function updateDestinationDirectory() {
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

            if($_warehouseModel->getShowLoweringComponents()) {
                $gmData['loweringID'] = $_warehouseModel->getLoweringID();
                $job_handle = $gmc->doBackground("rebuildLoweringDirectory", json_encode($gmData));
            }
        }
    }

    public function __construct(){
        if(!Session::get('loggedin')){
            Url::redirect('config/login');
        }

        $this->_collectionSystemTransfersModel = new \Models\Config\CollectionSystemTransfers();
        $this->_transferTypesModel = new \Models\Config\TransferTypes();
    }
        
    public function index(){
        $data['title'] = 'Configuration';
        $data['collectionSystemTransfers'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfers();
        $data['javascript'] = array('collectionSystemTransfers');

        $warehouseModel = new \Models\Warehouse();
        $data['showLoweringComponents'] = $warehouseModel->getShowLoweringComponents();

        View::rendertemplate('header',$data);
        View::render('Config/collectionSystemTransfers',$data);
        View::rendertemplate('footer',$data);
    }

    public function add(){
        $data['title'] = 'Add Collection System Transfers';
        $data['javascript'] = array('collectionSystemTransfersFormHelper');
        $data['transferTypeOptions'] = $this->_buildTransferTypesOptions();
        $data['stalenessOptions'] = $this->_buildStalenessOptions();
        $data['useStartDateOptions'] = $this->_buildUseStartDateOptions();
        $data['useSSHKeyOptions'] = $this->_buildUseSSHKeyOptions();
        $data['useLocalMountPointOptions'] = $this->_buildUseLocalMountPointOptions();
        $data['cruiseOrLoweringOptions'] = $this->_buildCruiseOrLoweringOptions();

        if(isset($_POST['submit'])){
            $name = $_POST['name'];
            $longName = $_POST['longName'];
            $transferType = $_POST['transferType'];
            $sourceDir = $_POST['sourceDir'];
            $destDir = $_POST['destDir'];
            $staleness = $_POST['staleness'];
            $useStartDate = $_POST['useStartDate'];
            $bandwidthLimit = $_POST['bandwidthLimit'];
            $cruiseOrLowering = isset($_POST['cruiseOrLowering']) ? $_POST['cruiseOrLowering'] : '0';
            $localDirIsMountPoint = $_POST['localDirIsMountPoint'];
            $rsyncServer = $_POST['rsyncServer'];
            $rsyncUser = $_POST['rsyncUser'];
            $rsyncPass = $_POST['rsyncPass'];
            $smbServer = $_POST['smbServer'];
            $smbUser = $_POST['smbUser'];
            $smbPass = $_POST['smbPass'];
            $smbDomain = $_POST['smbDomain'];
            $sshServer = $_POST['sshServer'];
            $sshUser = $_POST['sshUser'];
            $sshUseKey = $_POST['sshUseKey'];
            $sshPass = $_POST['sshPass'];
            $includeFilter = $_POST['includeFilter'];
            $excludeFilter = $_POST['excludeFilter'];
            $ignoreFilter = $_POST['ignoreFilter'];
            $status = 4;
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

            if(!((string)(int)$bandwidthLimit == $bandwidthLimit) || ($bandwidthLimit === '')){
                $error[] = 'Transfer limit must be an integer';
            }
            
            if ($transferType == 1) { //local directory
                $smbServer = '';
                $smbUser = '';
                $smbPass = '';
                $smbDomain = '';
                $rsyncServer = '';
                $rsyncUser = '';
                $rsyncPass = '';
                $sshServer = '';
                $sshUser = '';
                $sshUseKey = '0';
                $sshPass = '';
            
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

                if($rsyncUser != 'anonymous' && $rsyncPass == ''){
                    $error[] = 'Rsync Password is required';
                    $rsyncDataCheck = false;
                }
                
                if($rsyncDataCheck) {
                    $smbServer = '';
                    $smbUser = '';
                    $smbDomain = '';
                    $smbPass = '';
                    $sshServer = '';
                    $sshUser = '';
                    $sshUseKey = '0';
                    $sshPass = '';
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

//                if($smbUser != 'guest' && $smbPass == ''){
//                    $error[] = 'SMB Password is required';
//                    $smbDataCheck = false;
//                }
                
                if($smbDomain == ''){
                    $smbDomain = 'WORKGROUP'; // Default value
                    $smbDataCheck = false;
                }
                
                if($smbDataCheck) {
                    $rsyncServer = '';
                    $rsyncUser = '';
                    $rsyncPass = '';
                    $sshServer = '';
                    $sshUser = '';
                    $sshUseKey = '0';
                    $sshPass = '';
                }
            } elseif ($transferType == 4) { // SSH Server
                $sshDataCheck = true;
                if($sshServer == ''){
                    $error[] = 'SSH Server is required';
                    $sshDataCheck = false;
                } 

                if($sshUser == ''){
                    $error[] = 'Rsync Username is required';
                    $sshDataCheck = false;

                } 

                if(($sshPass == '') && ($sshUseKey == "0")){
                    $error[] = 'SSH Password is required';
                    $sshDataCheck = false;
                }
                
                if($sshDataCheck) {
                    $localDirIsMountPoint = '0';
                    $smbServer = '';
                    $smbUser = '';
                    $smbDomain = '';
                    $smbPass = '';
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
                    'useStartDate' => $useStartDate,
                    'bandwidthLimit' => (int)$bandwidthLimit,
                    'cruiseOrLowering' => $cruiseOrLowering,
                    'localDirIsMountPoint' => $localDirIsMountPoint,
                    'rsyncServer' => $rsyncServer,
                    'rsyncUser' => $rsyncUser,
                    'rsyncPass' => $rsyncPass,
                    'smbServer' => $smbServer,
                    'smbUser' => $smbUser,
                    'smbPass' => $smbPass,
                    'smbDomain' => $smbDomain,
                    'sshServer' => $sshServer,
                    'sshUser' => $sshUser,
                    'sshUseKey' => $sshUseKey,
                    'sshPass' => $sshPass,
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
        } else if(isset($_POST['inlineTest'])){
            $name = $_POST['name'];
            $longName = $_POST['longName'];
            $transferType = $_POST['transferType'];
            $sourceDir = $_POST['sourceDir'];
            $destDir = $_POST['destDir'];
            $staleness = $_POST['staleness'];
            $useStartDate = $_POST['useStartDate'];
            $bandwidthLimit = $_POST['bandwidthLimit'];
            $cruiseOrLowering = isset($_POST['cruiseOrLowering']) ? $_POST['cruiseOrLowering'] : '0';
            $localDirIsMountPoint = $_POST['localDirIsMountPoint'];
            $rsyncServer = $_POST['rsyncServer'];
            $rsyncUser = $_POST['rsyncUser'];
            $rsyncPass = $_POST['rsyncPass'];
            $smbServer = $_POST['smbServer'];
            $smbUser = $_POST['smbUser'];
            $smbPass = $_POST['smbPass'];
            $smbDomain = $_POST['smbDomain'];
            $sshServer = $_POST['sshServer'];
            $sshUser = $_POST['sshUser'];
            $sshUseKey = $_POST['sshUseKey'];
            $sshPass = $_POST['sshPass'];
            $includeFilter = $_POST['includeFilter'];
            $excludeFilter = $_POST['excludeFilter'];
            $ignoreFilter = $_POST['ignoreFilter'];
            $status = 4;
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
            
            if(!((string)(int)$bandwidthLimit == $bandwidthLimit) || ($bandwidthLimit === '')){
                $error[] = 'Transfer limit must be an integer';
            }
            
            if ($transferType == 1) { //local directory
                $smbServer = '';
                $smbUser = '';
                $smbDomain = '';
                $smbPass = '';
                $rsyncServer = '';
                $rsyncUser = '';
                $rsyncPass = '';
                $sshServer = '';
                $sshUser = '';
                $sshUseKey = '0';
                $sshPass = '';
            
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

                if($rsyncUser != 'anonymous' && $rsyncPass == ''){
                    $error[] = 'Rsync Password is required';
                    $rsyncDataCheck = false;
                }
                
                if($rsyncDataCheck) {
                    $localDirIsMountPoint = '0';
                    $smbServer = '';
                    $smbUser = '';
                    $smbPass = '';
                    $smbDomain = '';
                    $sshServer = '';
                    $sshUser = '';
                    $sshUseKey = '0';
                    $sshPass = '';
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

//                if($smbUser != 'guest' && $smbPass == ''){
//                    $error[] = 'SMB Password is required';
//                    $smbDataCheck = false;
//                }
                
                if($smbDomain == ''){
                    $smbDomain = 'WORKGROUP'; // Default value
                    $smbDataCheck = false;
                }
                
                if($smbDataCheck) {
                    $localDirIsMountPoint = '0';
                    $rsyncServer = '';
                    $rsyncUser = '';
                    $rsyncPass = '';
                    $sshServer = '';
                    $sshUser = '';
                    $sshUseKey = '0';
                    $sshPass = '';
                }
            } elseif ($transferType == 4) { // SSH Server
                $sshDataCheck = true;
                if($sshServer == ''){
                    $error[] = 'SSH Server is required';
                    $sshDataCheck = false;
                } 

                if($sshUser == ''){
                    $error[] = 'Rsync Username is required';
                    $sshDataCheck = false;

                } 

                if($sshPass == ''){
                    $error[] = 'SSH Password is required';
                    $sshDataCheck = false;
                }
                
                if($sshDataCheck) {
                    $localDirIsMountPoint = '0';
                    $smbServer = '';
                    $smbUser = '';
                    $smbDomain = '';
                    $smbPass = '';
                    $rsyncServer = '';
                    $rsyncUser = '';
                    $rsyncPass = '';
                }
            }    
            
            if(!$error){
                $_warehouseModel = new \Models\Warehouse();
                $gmData['collectionSystemTransfer'] = (object)array(
                   # 'collectionSystemTransferID' => '0',
                    'name' => $name,
                    'longName' => $longName,
                    'transferType' => $transferType,
                    'sourceDir' => $sourceDir,
                    'destDir' => $destDir,
                    'staleness' => $staleness,
                    'useStartDate' => $useStartDate,
                    'bandwidthLimit' => (int)$bandwidthLimit,
                    'cruiseOrLowering' => $cruiseOrLowering,
                    'localDirIsMountPoint' => $localDirIsMountPoint,
                    'rsyncServer' => $rsyncServer,
                    'rsyncUser' => $rsyncUser,
                    'rsyncPass' => $rsyncPass,
                    'smbServer' => $smbServer,
                    'smbUser' => $smbUser,
                    'smbPass' => $smbPass,
                    'smbDomain' => $smbDomain,
                    'sshServer' => $sshServer,
                    'sshUser' => $sshUser,
                    'sshUseKey' => $sshUseKey,
                    'sshPass' => $sshPass,
                    'includeFilter' => $includeFilter,
                    'excludeFilter' => $excludeFilter,
                    'ignoreFilter' => $ignoreFilter,
                    'status' => '4',
                    'enable' => '0',
                );
                
                # create the gearman client
                $gmc= new \GearmanClient();

                # add the default server (localhost)
                $gmc->addServer();

                #submit job to Gearman, wait for results
                $data['testResults'] = json_decode($gmc->doNormal("testCollectionSystemTransfer", json_encode($gmData)), true);
            
                $data['testCollectionSystemTransferName'] = $gmData['collectionSystemTransfer']->name;
            }
        }

        View::rendertemplate('header',$data);
        View::render('Config/addCollectionSystemTransfers',$data,$error);
        View::rendertemplate('footer',$data);
    }
        
    public function edit($id) {
        $data['title'] = 'Collection System Transfers';
        $data['javascript'] = array('collectionSystemTransfersFormHelper');
        $data['transferTypeOptions'] = $this->_buildTransferTypesOptions();
        $data['stalenessOptions'] = $this->_buildStalenessOptions();
        $data['useStartDateOptions'] = $this->_buildUseStartDateOptions();
        $data['useSSHKeyOptions'] = $this->_buildUseSSHKeyOptions();
        $data['useLocalMountPointOptions'] = $this->_buildUseLocalMountPointOptions();
        $data['cruiseOrLoweringOptions'] = $this->_buildCruiseOrLoweringOptions();

        $data['row'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfer($id);        
        
        if(isset($_POST['submit'])){
            $name = $_POST['name'];
            $longName = $_POST['longName'];
            $transferType = $_POST['transferType'];
            $sourceDir = $_POST['sourceDir'];
            $destDir = $_POST['destDir'];
            $staleness = $_POST['staleness'];
            $useStartDate = $_POST['useStartDate'];
            $bandwidthLimit = $_POST['bandwidthLimit'];
            $cruiseOrLowering = isset($_POST['cruiseOrLowering']) ? $_POST['cruiseOrLowering'] : '0';
            $localDirIsMountPoint = $_POST['localDirIsMountPoint'];
            $rsyncServer = $_POST['rsyncServer'];
            $rsyncUser = $_POST['rsyncUser'];
            $rsyncPass = $_POST['rsyncPass'];
            $smbServer = $_POST['smbServer'];
            $smbUser = $_POST['smbUser'];
            $smbPass = $_POST['smbPass'];
            $smbDomain = $_POST['smbDomain'];
            $sshServer = $_POST['sshServer'];
            $sshUser = $_POST['sshUser'];
            $sshUseKey = $_POST['sshUseKey'];
            $sshPass = $_POST['sshPass'];
            $includeFilter = $_POST['includeFilter'];
            $excludeFilter = $_POST['excludeFilter'];
            $ignoreFilter = $_POST['ignoreFilter'];

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
            
            if(!((string)(int)$bandwidthLimit == $bandwidthLimit) || ($bandwidthLimit === '')){
                $error[] = 'Transfer limit must be an integer';
            }

            if ($transferType == 1) { //local directory
                $smbServer = '';
                $smbUser = '';
                $smbDomain = '';
                $smbPass = '';
                $rsyncServer = '';
                $rsyncUser = '';
                $rsyncPass = '';
                $sshServer = '';
                $sshUser = '';
                $sshUseKey = '0';
                $sshPass = '';
            
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

                if($rsyncUser != 'anonymous' && $rsyncPass == ''){
                    $error[] = 'Rsync Password is required';
                    $rsyncDataCheck = false;
                }
                
                if($rsyncDataCheck) {
                    $localDirIsMountPoint = '0';
                    $smbServer = '';
                    $smbUser = '';
                    $smbDomain = '';
                    $smbPass = '';
                    $sshServer = '';
                    $sshUser = '';
                    $sshUseKey = '0';
                    $sshPass = '';
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

//                if($smbUser != 'guest' && $smbPass == ''){
//                    $error[] = 'SMB Password is required';
//                    $smbDataCheck = false;
//                }
                
                if($smbDomain == ''){
                    $smbDomain = 'WORKGROUP'; // Default value
                    $smbDataCheck = false;
                }
                
                if($smbDataCheck) {
                    $localDirIsMountPoint = '0';
                    $rsyncServer = '';
                    $rsyncUser = '';
                    $rsyncPass = '';
                    $sshServer = '';
                    $sshUser = '';
                    $sshUseKey = '0';
                    $sshPass = '';
                }
            } elseif ($transferType == 4) { // SSH Server
                $sshDataCheck = true;
                if($sshServer == ''){
                    $error[] = 'SSH Server is required';
                    $sshDataCheck = false;
                } 

                if($sshUser == ''){
                    $error[] = 'SSH Username is required';
                    $sshDataCheck = false;
                } 

                if(($sshPass == '') && ($sshUseKey == '0')){
                    $error[] = 'SSH Password is required';
                    $sshDataCheck = false;
                }
                
                if($sshDataCheck) {
                    $localDirIsMountPoint = '0';
                    $smbServer = '';
                    $smbUser = '';
                    $smbDomain = '';
                    $smbPass = '';
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
                    'useStartDate' => $useStartDate,
                    'bandwidthLimit' => (int)$bandwidthLimit,
                    'cruiseOrLowering' => $cruiseOrLowering,
                    'localDirIsMountPoint' => $localDirIsMountPoint,
                    'rsyncServer' => $rsyncServer,
                    'rsyncUser' => $rsyncUser,
                    'rsyncPass' => $rsyncPass,
                    'smbServer' => $smbServer,
                    'smbUser' => $smbUser,
                    'smbPass' => $smbPass,
                    'smbDomain' => $smbDomain,
                    'sshServer' => $sshServer,
                    'sshUser' => $sshUser,
                    'sshUseKey' => $sshUseKey,
                    'sshPass' => $sshPass,
                    'includeFilter' => $includeFilter,
                    'excludeFilter' => $excludeFilter,
                    'ignoreFilter' => $ignoreFilter,
                );
            
                
                $where = array('collectionSystemTransferID' => $id);
                $this->_collectionSystemTransfersModel->updateCollectionSystemTransfer($postdata,$where);
                
                if($data['row'][0]->destDir != $destDir){
                    $this->updateDestinationDirectory();
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
                $data['row'][0]->useStartDate = $useStartDate;
                $data['row'][0]->bandwidthLimit = $bandwidthLimit;
                $data['row'][0]->cruiseOrLowering = $cruiseOrLowering;
                $data['row'][0]->localDirIsMountPoint = $localDirIsMountPoint;
                $data['row'][0]->rsyncServer = $rsyncServer;
                $data['row'][0]->rsyncUser = $rsyncUser;
                $data['row'][0]->rsyncPass = $rsyncPass;
                $data['row'][0]->smbServer = $smbServer;
                $data['row'][0]->smbUser = $smbUser;
                $data['row'][0]->smbPass = $smbPass;
                $data['row'][0]->smbDomain = $smbDomain;
                $data['row'][0]->sshServer = $sshServer;
                $data['row'][0]->sshUser = $sshUser;
                $data['row'][0]->sshUseKey = $sshUseKey;
                $data['row'][0]->sshPass = $sshPass;
                $data['row'][0]->includeFilter = $includeFilter;
                $data['row'][0]->excludeFilter = $excludeFilter;
                $data['row'][0]->ignoreFilter = $ignoreFilter;
            }
        } else if(isset($_POST['inlineTest'])){

            $name = $_POST['name'];
            $longName = $_POST['longName'];
            $transferType = $_POST['transferType'];
            $sourceDir = $_POST['sourceDir'];
            $destDir = $_POST['destDir'];
            $staleness = $_POST['staleness'];
            $useStartDate = $_POST['useStartDate'];
            $bandwidthLimit = $_POST['bandwidthLimit'];
            $cruiseOrLowering = isset($_POST['cruiseOrLowering']) ? $_POST['cruiseOrLowering'] : '0';
            $localDirIsMountPoint = $_POST['localDirIsMountPoint'];
            $rsyncServer = $_POST['rsyncServer'];
            $rsyncUser = $_POST['rsyncUser'];
            $rsyncPass = $_POST['rsyncPass'];
            $smbServer = $_POST['smbServer'];
            $smbUser = $_POST['smbUser'];
            $smbPass = $_POST['smbPass'];
            $smbDomain = $_POST['smbDomain'];
            $sshServer = $_POST['sshServer'];
            $sshUser = $_POST['sshUser'];
            $sshUseKey = $_POST['sshUseKey'];
            $sshPass = $_POST['sshPass'];
            $includeFilter = $_POST['includeFilter'];
            $excludeFilter = $_POST['excludeFilter'];
            $ignoreFilter = $_POST['ignoreFilter'];
            
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
            
            if(!((string)(int)$bandwidthLimit == $bandwidthLimit) || ($bandwidthLimit === '')){
                $error[] = 'Transfer limit must be an integer';
            }

            if ($transferType == 1) { //local directory
                $smbServer = '';
                $smbUser = '';
                $smbDomain = '';
                $smbPass = '';
                $rsyncServer = '';
                $rsyncUser = '';
                $rsyncPass = '';
                $sshServer = '';
                $sshUser = '';
                $sshUseKey = '0';
                $sshPass = '';
            
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

                if($rsyncUser != 'anonymous' && $rsyncPass == ''){
                    $error[] = 'Rsync Password is required';
                    $rsyncDataCheck = false;
                }
                
                if($rsyncDataCheck) {
                    $localDirIsMountPoint = '0';
                    $smbServer = '';
                    $smbUser = '';
                    $smbDomain = '';
                    $smbPass = '';
                    $sshServer = '';
                    $sshUser = '';
                    $sshUseKey = '0';
                    $sshPass = '';
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
                
//                if($smbUser != 'guest' && $smbPass == ''){
//                    $error[] = 'SMB Password is required';
//                    $smbDataCheck = false;
//                }

                if($smbDomain == ''){
                    $smbDomain = 'WORKGROUP'; // Default value
                    $smbDataCheck = false;
                }
                
                if($smbDataCheck) {
                    $localDirIsMountPoint = '0';
                    $rsyncServer = '';
                    $rsyncUser = '';
                    $rsyncPass = '';
                    $sshServer = '';
                    $sshUser = '';
                    $sshUseKey = '0';
                    $sshPass = '';
                }
            } elseif ($transferType == 4) { // SSH Server
                $sshDataCheck = true;
                if($sshServer == ''){
                    $error[] = 'SSH Server is required';
                    $sshDataCheck = false;
                } 

                if($sshUser == ''){
                    $error[] = 'SSH Username is required';
                    $sshDataCheck = false;
                } 

                if(($sshPass == '') && ($sshUseKey == '0')){
                    $error[] = 'SSH Password is required';
                    $sshDataCheck = false;
                }
                
                if($sshDataCheck) {
                    $localDirIsMountPoint = '0';
                    $smbServer = '';
                    $smbUser = '';
                    $smbDomain = '';
                    $smbPass = '';
                    $rsyncServer = '';
                    $rsyncUser = '';
                    $rsyncPass = '';
                }
                        
            }

            if(!$error) {

                $gmData['collectionSystemTransfer'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfer($id)[0];
            
                $gmData['collectionSystemTransfer']->name = $name;
                $gmData['collectionSystemTransfer']->longName = $longName;
                $gmData['collectionSystemTransfer']->transferType = $transferType;
                $gmData['collectionSystemTransfer']->sourceDir = $sourceDir;
                $gmData['collectionSystemTransfer']->destDir = $destDir;
                $gmData['collectionSystemTransfer']->staleness = $staleness;
                $gmData['collectionSystemTransfer']->useStartDate = $useStartDate;
                $gmData['collectionSystemTransfer']->bandwidthLimit = $bandwidthLimit;
                $gmData['collectionSystemTransfer']->cruiseOrLowering = $cruiseOrLowering;
                $gmData['collectionSystemTransfer']->localDirIsMountPoint = $localDirIsMountPoint;
                $gmData['collectionSystemTransfer']->rsyncServer = $rsyncServer;
                $gmData['collectionSystemTransfer']->rsyncUser = $rsyncUser;
                $gmData['collectionSystemTransfer']->rsyncPass = $rsyncPass;
                $gmData['collectionSystemTransfer']->smbServer = $smbServer;
                $gmData['collectionSystemTransfer']->smbUser = $smbUser;
                $gmData['collectionSystemTransfer']->smbPass = $smbPass;
                $gmData['collectionSystemTransfer']->smbDomain = $smbDomain;
                $gmData['collectionSystemTransfer']->sshServer = $sshServer;
                $gmData['collectionSystemTransfer']->sshUser = $sshUser;
                $gmData['collectionSystemTransfer']->sshUseKey = $sshUseKey;
                $gmData['collectionSystemTransfer']->sshPass = $sshPass;
                $gmData['collectionSystemTransfer']->includeFilter = $includeFilter;
                $gmData['collectionSystemTransfer']->excludeFilter = $excludeFilter;
                $gmData['collectionSystemTransfer']->ignoreFilter = $ignoreFilter;

                # create the gearman client
                $gmc= new \GearmanClient();

                # add the default server (localhost)
                $gmc->addServer();

                #submit job to Gearman, wait for results
                $data['testResults'] = json_decode($gmc->doNormal("testCollectionSystemTransfer", json_encode($gmData)), true);
                // $data['testCollectionSystemTransferName'] = $gmData['collectionSystemTransfer']->name;      


            }

            #additional data needed for view
            $data['row'][0]->name = $name;
            $data['row'][0]->longName = $longName;
            $data['row'][0]->transferType = $transferType;
            $data['row'][0]->sourceDir = $sourceDir;
            $data['row'][0]->destDir = $destDir;
            $data['row'][0]->staleness = $staleness;
            $data['row'][0]->useStartDate = $useStartDate;
            $data['row'][0]->bandwidthLimit = $bandwidthLimit;
            $data['row'][0]->cruiseOrLowering = $cruiseOrLowering;
            $data['row'][0]->localDirIsMountPoint = $localDirIsMountPoint;
            $data['row'][0]->rsyncServer = $rsyncServer;
            $data['row'][0]->rsyncUser = $rsyncUser;
            $data['row'][0]->rsyncPass = $rsyncPass;
            $data['row'][0]->smbServer = $smbServer;
            $data['row'][0]->smbUser = $smbUser;
            $data['row'][0]->smbPass = $smbPass;
            $data['row'][0]->smbDomain = $smbDomain;
            $data['row'][0]->sshServer = $sshServer;
            $data['row'][0]->sshUser = $sshUser;
            $data['row'][0]->sshUseKey = $sshUseKey;
            $data['row'][0]->sshPass = $sshPass;
            $data['row'][0]->includeFilter = $includeFilter;
            $data['row'][0]->excludeFilter = $excludeFilter;
            $data['row'][0]->ignoreFilter = $ignoreFilter;
        }

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

        $this->updateDestinationDirectory();

        Url::redirect('config/collectionSystemTransfers');
    }
    
    public function disable($id) {
        $this->_collectionSystemTransfersModel->disableCollectionSystemTransfer($id);
        Url::redirect('config/collectionSystemTransfers');
    }
    
    public function test($id) {
        
        $collectionSystemTransfer = $this->_collectionSystemTransfersModel->getCollectionSystemTransfer($id)[0];
        $gmData = array(
            'collectionSystemTransfer' => array(
                'collectionSystemTransferID' => $collectionSystemTransfer->collectionSystemTransferID
            )
        );
        
        # create the gearman client
        $gmc= new \GearmanClient();

        # add the default server (localhost)
        $gmc->addServer();

        #submit job to Gearman, wait for results
        $data['testResults'] = json_decode($gmc->doNormal("testCollectionSystemTransfer", json_encode($gmData)), true);

        $data['title'] = 'Configuration';
        $data['collectionSystemTransfers'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfers();
        $data['javascript'] = array('collectionSystemTransfers');

        #additional data needed for view
        $data['testCollectionSystemTransferName'] = $gmData['collectionSystemTransfer']->name;

        View::rendertemplate('header',$data);
        View::render('Config/collectionSystemTransfers',$data);
        View::rendertemplate('footer',$data);
    }
    
    public function run($id) {
        
        $collectionSystemTransfer = $this->_collectionSystemTransfersModel->getCollectionSystemTransfer($id)[0];
        
        $gmData = array(
            'collectionSystemTransfer' => array(
                'collectionSystemTransferID' => $collectionSystemTransfer->collectionSystemTransferID,
                'enable' => "1"
            ),
            'systemStatus' => "On"
        );
        
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
        
        $gmData = array(
            'pid' => $this->_collectionSystemTransfersModel->getCollectionSystemTransfer($id)[0]->pid
        );
        
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