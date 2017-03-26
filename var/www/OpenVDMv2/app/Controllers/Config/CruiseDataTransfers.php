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
            array_push($output, $option);
        }
        
        return $output;
    }

    private function _buildUseSSHKeyOptions() {
        
        $trueFalse = array(array('id'=>'useSSHKey0', 'name'=>'sshUseKey', 'value'=>'0', 'label'=>'No'), array('id'=>'useSSHKey1', 'name'=>'sshUseKey', 'value'=>'1', 'label'=>'Yes'));
        return $trueFalse;
    }

    private function _buildUseLocalMountPointOptions() {
        
        $trueFalse = array(array('id'=>'localDirIsMountPoint0', 'name'=>'localDirIsMountPoint', 'value'=>'0', 'label'=>'No'), array('id'=>'localDirIsMountPoint1', 'name'=>'localDirIsMountPoint', 'value'=>'1', 'label'=>'Yes'));
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
        $data['cruiseDataTransfers'] = $this->_cruiseDataTransfersModel->getCruiseDataTransfers();
        $data['javascript'] = array('cruiseDataTransfers');
        View::rendertemplate('header',$data);
        View::render('Config/cruiseDataTransfers',$data);
        View::rendertemplate('footer',$data);
    }

    public function add(){
        $data['title'] = 'Add Cruise Data Transfer';
        $data['javascript'] = array('cruiseDataTransfersFormHelper');
        $data['transferTypeOptions'] = $this->_buildTransferTypesOptions($_POST['transferType']);
        $data['useSSHKeyOptions'] = $this->_buildUseSSHKeyOptions();
        $data['useLocalMountPointOptions'] = $this->_buildUseLocalMountPointOptions();

        if(isset($_POST['submit'])){
            $name = $_POST['name'];
            $longName = $_POST['longName'];
            $transferType = $_POST['transferType'];
            $destDir = $_POST['destDir'];
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
            $nfsServer = $_POST['nfsServer'];
            //$nfsUser = $_POST['nfsUser'];
            //$nfsPass = $_POST['nfsPass'];
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
                    $localDirIsMountPoint = '0';
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

                if($smbUser != 'guest' && $smbPass == ''){
                    $error[] = 'SMB Password is required';
                    $smbDataCheck = false;
                } 
            
                if($smbDomain == ''){
                    $smbDomain = 'WORKGROUP';
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

                if(($sshPass == '') && ($sshUseKey == 0)){
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
                    $nfsServer = '';
                    //$nfsUser = '';
                    //$nfsPass = '';
                }

            } elseif ($transferType == 5) { // NFS Server
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
                    $localDirIsMountPoint = '0';
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
                    'destDir' => $destDir,
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
                    'nfsServer' => $nfsServer,
                    //'nfsUser' => $nfsUser,
                    //'nfsPass' => $nfsPass,
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
            $nfsServer = $_POST['nfsServer'];
            //$nfsUser = $_POST['nfsUser'];
            //$nfsPass = $_POST['nfsPass'];
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
                    $localDirIsMountPoint = '0';
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

                if($smbUser != 'guest' && $smbPass == ''){
                    $error[] = 'SMB Password is required';
                    $smbDataCheck = false;
                } 
            
                if($smbDomain == ''){
                    $smbDomain = 'WORKGROUP';
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
                    $localDirIsMountPoint = '0';
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
                
            } elseif ($transferType == 5) { // NFS Server
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
                    $localDirIsMountPoint = '0';
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
                $gmData['cruiseDataTransfer'] = (object)array(
                    'name' => $name,
                    'longName' => $longName,
                    'transferType' => $transferType,
                    'destDir' => $destDir,
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
                    'nfsServer' => $nfsServer,
                    //'nfsUser' => $nfsUser,
                    //'nfsPass' => $nfsPass,
                    'status' => '4',
                    'enable' => '0'
                    );
            
                # create the gearman client
                $gmc= new \GearmanClient();

                # add the default server (localhost)
                $gmc->addServer();

                #submit job to Gearman, wait for results
                $data['testResults'] = json_decode($gmc->doNormal("testCruiseDataTransfer", json_encode($gmData)), true);
            
                $data['testCruiseDataTransferName'] = $gmData['cruiseDataTransfer']->name;     
            }
        }

        View::rendertemplate('header',$data);
        View::render('Config/addCruiseDataTransfers',$data,$error);
        View::rendertemplate('footer',$data);
    }
        
    public function edit($id){
        $data['title'] = 'Edit Cruise Data Transfer';
        $data['javascript'] = array('cruiseDataTransfersFormHelper');
        $data['transferTypeOptions'] = $this->_buildTransferTypesOptions($data['row'][0]->transferType);
        $data['useSSHKeyOptions'] = $this->_buildUseSSHKeyOptions();
        $data['useLocalMountPointOptions'] = $this->_buildUseLocalMountPointOptions();
        $data['row'] = $this->_cruiseDataTransfersModel->getCruiseDataTransfer($id);

        if(isset($_POST['submit'])){
            $name = $_POST['name'];
            $longName = $_POST['longName'];
            $transferType = $_POST['transferType'];
            $destDir = $_POST['destDir'];
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
            $nfsServer = $_POST['nfsServer'];
            //$nfsUser = $_POST['nfsUser'];
            //$nfsPass = $_POST['nfsPass'];

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
                    $localDirIsMountPoint = '0';
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
                    $localDirIsMountPoint = '0';
                    $rsyncServer = '';
                    $rsyncUser = '';
                    $rsyncPass = '';
                    $sshServer = '';
                    $sshUser = '';
                    $sshPass = '';
                    $nfsServer = '';
                    //$nfsUser = '';
                    //$nfsPass = '';
                }
            } elseif ($transferType == 4) { //ssh
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
                    $localDirIsMountPoint = '0';
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
                    'destDir' => $destDir,
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
                    'nfsServer' => $nfsServer,
                    //'nfsUser' => $nfsUser,
                    //'nfsPass' => $nfsPass,

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
                $data['row'][0]->nfsServer = $nfsServer;
                //$data['row'][0]->nfsUser = $nfsUser;
                //$data['row'][0]->nfsPass = $nfsPass;
            }
        } else if(isset($_POST['inlineTest'])){
            $_warehouseModel = new \Models\Warehouse();
            $gmData['cruiseDataTransfer'] = $this->_cruiseDataTransfersModel->getCruiseDataTransfer($id)[0];
            
            $gmData['cruiseDataTransfer']->name = $_POST['name'];
            $gmData['cruiseDataTransfer']->longName = $_POST['longName'];
            $gmData['cruiseDataTransfer']->transferType = $_POST['transferType'];
            $gmData['cruiseDataTransfer']->destDir = $_POST['destDir'];
            $gmData['cruiseDataTransfer']->localDirIsMountPoint = $_POST['localDirIsMountPoint'];
            $gmData['cruiseDataTransfer']->rsyncServer = $_POST['rsyncServer'];
            $gmData['cruiseDataTransfer']->rsyncUser = $_POST['rsyncUser'];
            $gmData['cruiseDataTransfer']->rsyncPass = $_POST['rsyncPass'];
            $gmData['cruiseDataTransfer']->smbServer = $_POST['smbServer'];
            $gmData['cruiseDataTransfer']->smbUser = $_POST['smbUser'];
            $gmData['cruiseDataTransfer']->smbPass = $_POST['smbPass'];
            $gmData['cruiseDataTransfer']->smbDomain = $_POST['smbDomain'];
            $gmData['cruiseDataTransfer']->sshServer = $_POST['sshServer'];
            $gmData['cruiseDataTransfer']->sshUser = $_POST['sshUser'];
            $gmData['cruiseDataTransfer']->sshUseKey = $_POST['sshUseKey'];
            $gmData['cruiseDataTransfer']->sshPass = $_POST['sshPass'];
            $gmData['cruiseDataTransfer']->nfsServer = $_POST['nfsServer'];
            //$gmData['cruiseDataTransfer']->nfsUser = $_POST['nfsUser'];
            //$gmData['cruiseDataTransfer']->nfsPass = $_POST['nfsPass'];
            
            # create the gearman client
            $gmc= new \GearmanClient();

            # add the default server (localhost)
            $gmc->addServer();

            #submit job to Gearman, wait for results
            $data['testResults'] = json_decode($gmc->doNormal("testCruiseDataTransfer", json_encode($gmData)), true);

            #additional data needed for view
            $data['row'][0]->name = $_POST['name'];
            $data['row'][0]->longName = $_POST['longName'];
            $data['row'][0]->transferType = $_POST['transferType'];
            $data['row'][0]->destDir = $_POST['destDir'];
            $data['row'][0]->localDirIsMountPoint = $_POST['localDirIsMountPoint'];
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
            
            $data['testCruiseDataTransferName'] = $gmData['cruiseDataTransfer']->name;      
        }
        
        $data['transferTypeOptions'] = $this->_buildTransferTypesOptions();
        $data['useSSHKeyOptions'] = $this->_buildUseSSHKeyOptions();
        $data['localDirIsMountPoint'] = $this->_buildUseLocalMountPointOptions();

        View::rendertemplate('header',$data);
        View::render('Config/editCruiseDataTransfers',$data,$error);
        View::rendertemplate('footer',$data);
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
    
    public function test($id) {
        
        $cruiseDataTransfer = $this->_cruiseDataTransfersModel->getCruiseDataTransfer($id)[0];
        $gmData = array(
            'cruiseDataTransfer' => array(
                'cruiseDataTransferID' => $cruiseDataTransfer->cruiseDataTransferID
            )
        );
                
        # create the gearman client
        $gmc= new \GearmanClient();

        # add the default server (localhost)
        $gmc->addServer();

        #submit job to Gearman, wait for results
        $data['testResults'] = json_decode($gmc->doNormal("testCruiseDataTransfer", json_encode($gmData)), true);

        $data['title'] = 'Configuration';
        $data['cruiseDataTransfers'] = $this->_cruiseDataTransfersModel->getCruiseDataTransfers();
        $data['javascript'] = array('cruiseDataTransfers');

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
    
        sleep(1);
        
        Url::redirect('config/cruiseDataTransfers');
    }
        
    public function stop($id) {
        
        $gmData = array(
            'pid' => $this->_cruiseDataTransfersModel->getCruiseDataTransfer($id)[0]->pid
        );
        
        # create the gearman client
        $gmc= new \GearmanClient();

        # add the default server (localhost)
        $gmc->addServer();

        #submit job to Gearman
        $job_handle = $gmc->doBackground("stopJob", json_encode($gmData));
    
        sleep(1);
    
        Url::redirect('config/cruiseDataTransfers');
    }
}