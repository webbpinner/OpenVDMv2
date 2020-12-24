<?php

namespace controllers\config;
use Core\Controller;
use Core\View;
use Helpers\Url;
use Helpers\Session;

class ExtraDirectories extends Controller {

    private $_model;
    
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

        $this->_model = new \Models\Config\ExtraDirectories();
    }
        
    public function index(){
        $data['title'] = 'Configuration';
        $data['javascript'] = array();
        $data['extraDirectories'] = $this->_model->getExtraDirectories();
        View::rendertemplate('header',$data);
        View::render('Config/extraDirectories',$data);
        View::rendertemplate('footer',$data);
    }

    public function add(){
        $data['title'] = 'Add Extra Directory';
        $data['javascript'] = array('extraDirectoriesFormHelper');

        if(isset($_POST['submit'])){
            $name = $_POST['name'];
            $longName = $_POST['longName'];
            $destDir = $_POST['destDir'];
            $enable = 0;

            if($name == ''){
                $error[] = 'Name is required';
            }

            if($longName == ''){
                $error[] = 'Long name is required';
            }

            if($destDir == ''){
                $error[] = 'Destination directory is required';
            } 
            
            if(!$error){
                $postdata = array(
                    'name' => $name,
                    'longName' => $longName,
                    'destDir' => $destDir,
                    'enable' => $enable
                );

                $this->_model->insertExtraDirectory($postdata);

                Session::set('message','Extra Directory Added');
                Url::redirect('config/extraDirectories');
            }
        }

        View::rendertemplate('header',$data);
        View::render('Config/addExtraDirectories',$data,$error);
        View::rendertemplate('footer',$data);
    }
        
    public function edit($id){
        $data['title'] = 'Edit Extra Directory';
        $data['javascript'] = array('extraDirectoriesFormHelper');
        $data['row'] = $this->_model->getExtraDirectory($id);

        if(isset($_POST['submit'])){
            $name = $_POST['name'];
            $longName = $_POST['longName'];
            $destDir = $_POST['destDir'];

            if($name == ''){
                $error[] = 'Name is required';
            } 

            if($longName == ''){
                $error[] = 'Long name is required';
            } 

            if($destDir == ''){
                $error[] = 'Destination directory is required';
            } 
                
            if(!$error){
                $postdata = array(
                    'name' => $name,
                    'longName' => $longName,
                    'destDir' => $destDir,
                );
            
                
                $where = array('extraDirectoryID' => $id);
                $this->_model->updateExtraDirectory($postdata,$where);

                if($data['row'][0]->destDir != $destDir){
                    $this->updateCruiseDirectory();
                }
                
                Session::set('message','Extra Directory Updated');
                Url::redirect('config/extraDirectories');
            } else {
                
                $data['row'][0]->name = $name;
                $data['row'][0]->longName = $longName;
                $data['row'][0]->destDir = $destDir;
            }
        }

        View::rendertemplate('header',$data);
        View::render('Config/editExtraDirectories',$data,$error);
        View::rendertemplate('footer',$data);
    }
    
    public function delete($id){
        
        $where = array('extraDirectoryID' => $id);
        $this->_model->deleteExtraDirectory($where);
        Session::set('message','Extra Directory Deleted');
        Url::redirect('config/extraDirectories');
    }
    
    public function enable($id) {
        $this->_model->enableExtraDirectory($id);
        
        $this->updateCruiseDirectory();
        
        Url::redirect('config/extraDirectories');
    }
    
    public function disable($id) {
        $this->_model->disableExtraDirectory($id);
        Url::redirect('config/extraDirectories');
    }

}
