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
    }
        
    public function index(){
        $data['title'] = 'Configuration';
        $data['collectionSystemTransfers'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfers();
        $data['javascript'] = array('collectionSystemTransfers');
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

        if(isset($_POST['submit'])){
            $name = $_POST['name'];
            $longName = $_POST['longName'];
            $transferType = $_POST['transferType'];
            $sourceDir = $_POST['sourceDir'];
            $destDir = $_POST['destDir'];
            $staleness = $_POST['staleness'];
            $useStartDate = $_POST['useStartDate'];
            $bandwidthLimit = $_POST['bandwidthLimit'];
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
            $nfsServer = $_POST['nfsServer'];
            //$nfsUser = $_POST['nfsUser'];
            //$nfsPass = $_POST['nfsPass'];
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

            if(!((int)$bandwidthLimit == $bandwidthLimit) && (strlen($bandwidthLimit) > 0)){
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
                $nfsServer = '';
                //$nfsUser = '';
                //$nfsPass = '';
            
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
                    $nfsServer = '';
                    //$nfsUser = '';
                    //$nfsPass = '';
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
                    $nfsServer = '';
                    //$nfsUser = '';
                    //$nfsPass = '';
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
                    $smbServer = '';
                    $smbUser = '';
                    $smbDomain = '';
                    $smbPass = '';
                    $rsyncServer = '';
                    $rsyncUser = '';
                    $rsyncPass = '';
                    $nfsServer = '';
                    //$nfsUser = '';
                    //$nfsPass = '';
                }
            } elseif ($transferType == 5) { // NFS Share
                $nfsDataCheck = true;
                if($nfsServer == ''){
                    $error[] = 'NFS Server is required';
                    $nfsDataCheck = false;
                } 

                //if($nfsUser == ''){
                //    $error[] = 'NFS Username is required';
                //    $nfsDataCheck = false;
                //} 

                //if($nfsUser != 'anonymous' && $nfsPass == ''){
                //    $error[] = 'NFS Password is required';
                //    $nfsDataCheck = false;
                //}
                
                if($nfsDataCheck) {
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
                    'nfsServer' => $nfsServer,
                    //'nfsUser' => $nfsUser,
                    //'nfsPass' => $nfsPass,
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
            $nfsServer = $_POST['nfsServer'];
            //$nfsUser = $_POST['nfsUser'];
            //$nfsPass = $_POST['nfsPass'];
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
            
            if(!((int)$bandwidthLimit == $bandwidthLimit) && (strlen($bandwidthLimit) > 0)){
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
                $nfsServer = '';
                //$nfsUser = '';
                //$nfsPass = '';
            
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
                    $smbPass = '';
                    $smbDomain = '';
                    $sshServer = '';
                    $sshUser = '';
                    $sshUseKey = '0';
                    $sshPass = '';
                    $nfsServer = '';
                    //$nfsUser = '';
                    //$nfsPass = '';
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
                    $nfsServer = '';
                    //$nfsUser = '';
                    //$nfsPass = '';
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
                    $smbServer = '';
                    $smbUser = '';
                    $smbDomain = '';
                    $smbPass = '';
                    $rsyncServer = '';
                    $rsyncUser = '';
                    $rsyncPass = '';
                    $nfsServer = '';
                    //$nfsUser = '';
                    //$nfsPass = '';
                }
            } elseif ($transferType == 5) { // NFS Share
                $nfsDataCheck = true;
                if($nfsServer == ''){
                    $error[] = 'NFS Server is required';
                    $nfsDataCheck = false;
                } 

                //if($nfsUser == ''){
                //    $error[] = 'NFS Username is required';
                //    $nfsDataCheck = false;
                //} 

                //if($nfsUser != 'anonymous' && $nfsPass == ''){
                //    $error[] = 'NFS Password is required';
                //    $nfsDataCheck = false;
                //}
                
                if($nfsDataCheck) {
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
                    'nfsServer' => $nfsServer,
                    //'nfsUser' => $nfsUser,
                    //'nfsPass' => $nfsPass,
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
        $data['row'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfer($id);

        if ($data['row']['bandwidthLimit'] == '0') {
            $data['row']['useBandwidthLimit'] = '0';
        } else {
            $data['row']['useBandwidthLimit'] = '1';
        }
        
        
        if(isset($_POST['submit'])){
            $name = $_POST['name'];
            $longName = $_POST['longName'];
            $transferType = $_POST['transferType'];
            $sourceDir = $_POST['sourceDir'];
            $destDir = $_POST['destDir'];
            $staleness = $_POST['staleness'];
            $useStartDate = $_POST['useStartDate'];
            $bandwidthLimit = $_POST['bandwidthLimit'];
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
            $nfsServer = $_POST['nfsServer'];
            //$nfsUser = $_POST['nfsUser'];
            //$nfsPass = $_POST['nfsPass'];
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
            
            if(!((int)$bandwidthLimit == $bandwidthLimit) && (strlen($bandwidthLimit) > 0)){
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
                $nfsServer = '';
                //$nfsUser = '';
                //$nfsPass = '';
            
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
                    $smbServer = '';
                    $smbUser = '';
                    $smbDomain = '';
                    $smbPass = '';
                    $sshServer = '';
                    $sshUser = '';
                    $sshUseKey = '0';
                    $sshPass = '';
                    $nfsServer = '';
                    //$nfsUser = '';
                    //$nfsPass = '';
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
                    $nfsServer = '';
                    //$nfsUser = '';
                    //$nfsPass = '';
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
                    $smbServer = '';
                    $smbUser = '';
                    $smbDomain = '';
                    $smbPass = '';
                    $rsyncServer = '';
                    $rsyncUser = '';
                    $rsyncPass = '';
                    $nfsServer = '';
                    //$nfsUser = '';
                    //$nfsPass = '';
                }
                        
            } elseif ($transferType == 5) { //nfs
                $nfsDataCheck = true;
                if($nfsServer == ''){
                    $error[] = 'NFS Server is required';
                    $nfsDataCheck = false;
                } 

                //if($nfsUser == ''){
                //    $error[] = 'NFS Username is required';
                //    $nfsDataCheck = false;
                //} 

                //if($nfsUser != 'anonymous' && $nfsPass == ''){
                //    $error[] = 'NFS Password is required';
                //    $nfsDataCheck = false;
                //} 
                
                if($nfsDataCheck) {
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
                    'nfsServer' => $nfsServer,
                    //'nfsUser' => $nfsUser,
                    //'nfsPass' => $nfsPass,
                    'includeFilter' => $includeFilter,
                    'excludeFilter' => $excludeFilter,
                    'ignoreFilter' => $ignoreFilter,
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
                $data['row'][0]->useStartDate = $useStartDate;
                $data['row'][0]->bandwidthLimit = $bandwidthLimit;
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
                $data['row'][0]->nfsServer = $nfsServer;
                //$data['row'][0]->nfsUser = $nfsUser;
                //$data['row'][0]->nfsPass = $nfsPass;
                $data['row'][0]->includeFilter = $includeFilter;
                $data['row'][0]->excludeFilter = $excludeFilter;
                $data['row'][0]->ignoreFilter = $ignoreFilter;
            }
        } else if(isset($_POST['inlineTest'])){
            $_warehouseModel = new \Models\Warehouse();
            $gmData['collectionSystemTransfer'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfer($id)[0];
            
            $gmData['collectionSystemTransfer']->name = $_POST['name'];
            $gmData['collectionSystemTransfer']->longName = $_POST['longName'];
            $gmData['collectionSystemTransfer']->transferType = $_POST['transferType'];
            $gmData['collectionSystemTransfer']->sourceDir = $_POST['sourceDir'];
            $gmData['collectionSystemTransfer']->destDir = $_POST['destDir'];
            $gmData['collectionSystemTransfer']->staleness = $_POST['staleness'];
            $gmData['collectionSystemTransfer']->useStartDate = $_POST['useStartDate'];
            $gmData['collectionSystemTransfer']->bandwidthLimit = $_POST['bandwidthLimit'];
            $gmData['collectionSystemTransfer']->rsyncServer = $_POST['rsyncServer'];
            $gmData['collectionSystemTransfer']->rsyncUser = $_POST['rsyncUser'];
            $gmData['collectionSystemTransfer']->rsyncPass = $_POST['rsyncPass'];
            $gmData['collectionSystemTransfer']->smbServer = $_POST['smbServer'];
            $gmData['collectionSystemTransfer']->smbUser = $_POST['smbUser'];
            $gmData['collectionSystemTransfer']->smbPass = $_POST['smbPass'];
            $gmData['collectionSystemTransfer']->smbDomain = $_POST['smbDomain'];
            $gmData['collectionSystemTransfer']->sshServer = $_POST['sshServer'];
            $gmData['collectionSystemTransfer']->sshUser = $_POST['sshUser'];
            $gmData['collectionSystemTransfer']->sshUseKey = $_POST['sshUseKey'];
            $gmData['collectionSystemTransfer']->sshPass = $_POST['sshPass'];
            $gmData['collectionSystemTransfer']->nfsServer = $_POST['nfsServer'];
            //$gmData['collectionSystemTransfer']->nfsUser = $_POST['nfsUser'];
            //$gmData['collectionSystemTransfer']->nfsPass = $_POST['nfsPass'];
            $gmData['collectionSystemTransfer']->includeFilter = $_POST['includeFilter'];
            $gmData['collectionSystemTransfer']->excludeFilter = $_POST['excludeFilter'];
            $gmData['collectionSystemTransfer']->ignoreFilter = $_POST['ignoreFilter'];
            
            # create the gearman client
            $gmc= new \GearmanClient();

            # add the default server (localhost)
            $gmc->addServer();

            #submit job to Gearman, wait for results
            $data['testResults'] = json_decode($gmc->doNormal("testCollectionSystemTransfer", json_encode($gmData)), true);

            #additional data needed for view
            $data['row'][0]->name = $_POST['name'];
            $data['row'][0]->longName = $_POST['longName'];
            $data['row'][0]->transferType = $_POST['transferType'];
            $data['row'][0]->sourceDir = $_POST['sourceDir'];
            $data['row'][0]->destDir = $_POST['destDir'];
            $data['row'][0]->staleness = $_POST['staleness'];
            $data['row'][0]->useStartDate = $_POST['useStartDate'];
            $data['row'][0]->bandwidthLimit = $_POST['bandwidthLimit'];
            $data['row'][0]->rsyncServer = $_POST['rsyncServer'];
            $data['row'][0]->rsyncUser = $_POST['rsyncUser'];
            $data['row'][0]->rsyncPass = $_POST['rsyncPass'];
            $data['row'][0]->smbServer = $_POST['smbServer'];
            $data['row'][0]->smbUser = $_POST['smbUser'];
            $data['row'][0]->smbPass = $_POST['smbPass'];
            $data['row'][0]->smbDomain = $_POST['smbDomain'];
            $data['row'][0]->sshServer = $_POST['sshServer'];
            $data['row'][0]->sshUser = $_POST['sshUser'];
            $data['row'][0]->sshUseKey = $_POST['sshUseKey'];
            $data['row'][0]->sshPass = $_POST['sshPass'];
            $data['row'][0]->nfsServer = $_POST['nfsServer'];
            //$data['row'][0]->nfsUser = $_POST['nfsUser'];
            //$data['row'][0]->nfsPass = $_POST['nfsPass'];
            $data['row'][0]->includeFilter = $_POST['includeFilter'];
            $data['row'][0]->excludeFilter = $_POST['excludeFilter'];
            $data['row'][0]->ignoreFilter = $_POST['ignoreFilter'];
            
            $data['testCollectionSystemTransferName'] = $gmData['collectionSystemTransfer']->name;      
        }
        
        $data['transferTypeOptions'] = $this->_buildTransferTypesOptions();
        $data['stalenessOptions'] = $this->_buildStalenessOptions();
        $data['useStartDateOptions'] = $this->_buildUseStartDateOptions();
        $data['useSSHKeyOptions'] = $this->_buildUseSSHKeyOptions();

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