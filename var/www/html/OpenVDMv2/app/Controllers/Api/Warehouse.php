<?php

namespace Controllers\Api;
use Core\Controller;

class Warehouse extends Controller {

    private $_warehouseModel;
 
    public function __construct(){
        $this->_warehouseModel = new \Models\Warehouse();
    }

    public function getSystemStatus(){

        if($this->_warehouseModel->getSystemStatus()) {
            $response['systemStatus'] = "On";
        } else {
            $response['systemStatus'] = "Off";            
        }

        echo json_encode($response);
    }
    
    public function getShipToShoreTransfersStatus(){

        if($this->_warehouseModel->getShipToShoreTransfersStatus()) {
            $response['shipToShoreTransfersStatus'] = "On";
        } else {
            $response['shipToShoreTransfersStatus'] = "Off";            
        }

        echo json_encode($response);
    }
    
    // getFreeSpace - return the free space on the server.
	public function getShipboardDataWarehouseConfig() {

        echo json_encode($this->_warehouseModel->getShipboardDataWarehouseConfig());
    }
    
    // getFreeSpace - return the free space on the server.
	public function getFreeSpace() {

        echo json_encode($this->_warehouseModel->getFreeSpace());
    }

	// getCruiseSize - return the size of the cruise directory.
	public function getCruiseSize() {

        echo json_encode($this->_warehouseModel->getCruiseSize());
    }
    
    // getCruiseID - return the current cruise ID.
	public function getCruiseID() {

        $response['cruiseID'] = $this->_warehouseModel->getCruiseID();
        echo json_encode($response);
    }
    
    // getShipboardDataWarehouseStatus - return the status of the data warehouse.
	public function getShipboardDataWarehouseStatus() {

        $response['shipboardDataWarehouseStatus'] = $this->_warehouseModel->getShipboardDataWarehouseStatus();
        echo json_encode($response);
    }
    
    public function getTransferLogSummary() {
        
        $warehouseBaseDir = $this->_warehouseModel->getShipboardDataWarehouseBaseDir();
        $cruiseID = $this->_warehouseModel->getCruiseID();
        $extraDirectoriesModel = new \Models\Config\ExtraDirectories();
        $requiredExtraDirectories = $extraDirectoriesModel->getRequiredExtraDirectories();
        $dashboardDataDir ='';
        foreach($requiredExtraDirectories as $row) {
            if(strcmp($row->name, "Dashboard Data") === 0) {
                $dashboardDataDir = $row->destDir;
                break;
            }
        }
        
        $filename = $warehouseBaseDir . '/' . $cruiseID . '/' . $dashboardDataDir . '/' . 'TransferLogSummary.json';
        if (file_exists($filename) && is_readable($filename)) {
            echo file_get_contents($filename);
        } else {
            echo "{}";
        }
    }
    
    // getShipToShoreBWLimit - return the ship-to-shore bandwidth limit
	public function getShipToShoreBWLimit() {

        $response['shipToShoreBWLimit'] = $this->_warehouseModel->getShipToShoreBWLimit();
        echo json_encode($response);
    }
    
    // getShipToShoreBWLimitStatus - return the ship-to-shore bandwidth limit status
	public function getShipToShoreBWLimitStatus() {

        $response['shipToShoreBWLimitStatus'] = $this->_warehouseModel->getShipToShoreBWLimitStatus();
        echo json_encode($response);
    }
    
    // getMD5FilesizeLimit - return the md5 filesize limit
	public function getMD5FilesizeLimit() {

        $response['md5FilesizeLimit'] = $this->_warehouseModel->getMd5FilesizeLimit();
        echo json_encode($response);
    }
    
    // getMd5FilesizeLimitStatus - return md5 filesize limit status
	public function getMD5FilesizeLimitStatus() {

        $response['md5FilesizeLimitStatus'] = $this->_warehouseModel->getMd5FilesizeLimitStatus();
        echo json_encode($response);
    }
    
    // getMd5FilesizeLimitStatus - return md5 filesize limit status
	public function getCruiseConfig() {
        
        $collectionSystemsTransfersModel = new \Models\Config\CollectionSystemTransfers();
        $extraDirectoriesModel = new \Models\Config\ExtraDirectories();
        $cruiseDataTransfersModel = new \Models\Config\CruiseDataTransfers();
        $shipToShoreTransfersModel = new \Models\Config\ShipToShoreTransfers();
        
        $response['warehouseConfig'] = $this->_warehouseModel->getShipboardDataWarehouseConfig();
        $response['collectionSystemTransfersConfig'] = $collectionSystemsTransfersModel->getCollectionSystemTransfersConfig();
        $response['extraDirectoriesConfig'] = $extraDirectoriesModel->getExtraDirectoriesConfig();
        $response['cruiseDataTransfersConfig'] = $cruiseDataTransfersModel->getCruiseDataTransfersConfig();
        $response['shipToShoreTransfersConfig'] = $shipToShoreTransfersModel->getShipToShoreTransfersConfig();
        echo json_encode($response, JSON_PRETTY_PRINT);
    
    }
    
}