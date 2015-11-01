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
        
        $transferLogDir ='';
        foreach($requiredExtraDirectories as $row) {
            if(strcmp($row->name, "Transfer Logs") === 0){
                $transferLogDir = $row->destDir;
                break;
            }
        }
        
        $filename = $warehouseBaseDir . '/' . $data['cruiseID'] . '/' . $transferLogDir . '/' . 'TransferLogSummary.json';
        if (file_exists($filename) && is_readable($filename)) {
            $transferLogSummary = json_decode(file_get_contents($filename));
            #var_dump($transferLogSummary);

            $data['filenameErrors'] = $transferLogSummary->filenameErrors;
            $data['shipboardTransfers'] = $transferLogSummary->shipboardTransfers;
            $data['shipToShoreTransfers'] = $transferLogSummary->shipToShoreTransfers;
        }
       
        $data['javascript'] = array('welcome');
        
        View::rendertemplate('header',$data);
        View::render('Welcome/index',$data);
        View::rendertemplate('footer',$data);
    }
}
