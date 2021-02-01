<?php

namespace Controllers;
use Core\Controller;
use Core\View;

class Welcome extends Controller {

    private $_warehouseModel;
    private $_collectionSystemTransfersModel;
    private $_cruiseDataTransfersModel;
    private $_transferLogsModel;
    private $_extraDirectoriesModel;
    
    public function __construct(){
        $this->_warehouseModel = new \Models\Warehouse();
        $this->_collectionSystemTransfersModel = new \Models\Config\CollectionSystemTransfers();
        $this->_cruiseDataTransfersModel = new \Models\Config\CruiseDataTransfers();
        $this->_transferLogsModel = new \Models\TransferLogs();
        $this->_extraDirectoriesModel = new \Models\Config\ExtraDirectories();
    }

    public function index(){
        $data['title'] = 'Dashboard';

        if($this->_warehouseModel->getSystemStatus()) {
            $data['systemStatus'] = "On";
        } else {
            $data['systemStatus'] = "Off";            
        }

        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['collectionSystemTransfers'] = $this->_collectionSystemTransfersModel->getActiveCollectionSystemTransfers();
        $data['requiredCruiseDataTransfers'] = $this->_cruiseDataTransfersModel->getRequiredCruiseDataTransfers();
        $data['cruiseDataTransfers'] = $this->_cruiseDataTransfersModel->getCruiseDataTransfers();
        
        $data['filenameErrors'] = $this->_transferLogsModel->getExcludeLogsSummary();
        $data['shipboardTransfers'] = $this->_transferLogsModel->getShipboardLogsSummary(5);
        $data['shipToShoreTransfers'] = $this->_transferLogsModel->getShipToShoreLogsSummary(5);
        $data['javascript'] = array('welcome');
        
        View::rendertemplate('header',$data);
        View::render('Welcome/index',$data);
        View::rendertemplate('footer',$data);
    }
}
