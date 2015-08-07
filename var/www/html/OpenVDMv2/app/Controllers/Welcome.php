<?php

namespace Controllers;
use Core\Controller;
use Core\View;

class Welcome extends Controller {

    private $_warehouseModel;
    private $_collectionSystemTransfersModel;
    private $_cruiseDataTransfersModel;
    private $_extraDirectoriesModel;
    
    public function __construct(){
        $this->_warehouseModel = new \Models\Warehouse();
        $this->_collectionSystemTransfersModel = new \Models\Config\CollectionSystemTransfers();
        $this->_cruiseDataTransfersModel = new \Models\Config\CruiseDataTransfers();
        $this->_extraDirectoriesModel = new \Models\Config\ExtraDirectories();
    }

    //private function formatFilesize($bytes) {
    //    $s = array('bytes', 'kb', 'MB', 'GB', 'TB', 'PB');
    //    $e = floor(log($bytes)/log(1024));
    //    return round(($bytes/pow(1024, floor($e))),2) . " " . $s[$e];
//        return '0';
    //}

    public function index(){
        $data['title'] = 'Dashboard';

        if($this->_warehouseModel->getSystemStatus()) {
            $data['systemStatus'] = "On";
        } else {
            $data['systemStatus'] = "Off";            
        }

        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['collectionSystemTransfers'] = $this->_collectionSystemTransfersModel->getCollectionSystemTransfers();
        $data['requiredCruiseDataTransfers'] = $this->_cruiseDataTransfersModel->getRequiredCruiseDataTransfers();
        $data['cruiseDataTransfers'] = $this->_cruiseDataTransfersModel->getCruiseDataTransfers();

        $warehouseBaseDir = $this->_warehouseModel->getShipboardDataWarehouseBaseDir();
        
        $requiredExtraDirectories = $this->_extraDirectoriesModel->getRequiredExtraDirectories();
        $dashboardDataDir ='';
        foreach($requiredExtraDirectories as $row) {
            if(strcmp($row->name, "Dashboard Data") === 0){
                $dashboardDataDir = $row->destDir;
                break;
            }
        }
        
        $filename = $warehouseBaseDir . '/' . $data['cruiseID'] . '/' . $dashboardDataDir . '/' . 'TransferLogSummary.json';
        if (file_exists($filename) && is_readable($filename)) {
            $transferLogSummary = json_decode(file_get_contents($filename));
            $data['filenameErrors'] = $transferLogSummary->filenameErrors;
            $data['shipboardTransfers'] = $transferLogSummary->shipboardTransfers;
            $data['shipToShoreTransfers'] = $transferLogSummary->shipToShoreTransfers;
        }
        
#        $cruiseSize = $this->_warehouseModel->getCruiseSize();
#        if(isset($cruiseSize['error'])){
#            $data['cruiseSize'] = "Error";
#        } else {
#            $data['cruiseSize'] = $this->formatFilesize($cruiseSize['cruiseSize']);
            //$data['cruiseSize'] = $cruiseSize['cruiseSize'];
#        }

#        $freeSpace = $this->_warehouseModel->getFreeSpace();
#        if(isset($freeSpace['error'])){
#            $data['freeSpace'] = "Error";
#        } else {
#            $data['freeSpace'] = $this->formatFilesize($freeSpace['freeSpace']);
            //$data['freeSpace'] = $freeSpace['freeSpace'];
#        }
        
        //$data['cruiseSize'] = $this->_model->getCruiseSize();
        //$data['freeSpace'] = $this->_model->getFreeSpace();        
        $data['javascript'] = array('welcome');
        
        View::rendertemplate('header',$data);
        View::render('Welcome/index',$data);
        View::rendertemplate('footer',$data);
    }
}
