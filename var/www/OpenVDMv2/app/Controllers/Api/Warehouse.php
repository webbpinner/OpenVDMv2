<?php

namespace Controllers\Api;
use Core\Controller;

class Warehouse extends Controller {

    private $_warehouseModel;

    private function translateOVDMVariables($text) {

        $returnText = $text;
        $returnText = str_replace("{cruiseID}", $this->_warehouseModel->getCruiseID(), $returnText);
        $returnText = str_replace("{loweringID}", $this->_warehouseModel->getLoweringID(), $returnText);
        $returnText = str_replace("{loweringDataBaseDir}", $this->_warehouseModel->getLoweringDataBaseDir() , $returnText);

        return $returnText;
    }
 
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

    // getFreeSpace - return the free space on the server.
    public function showLoweringComponents() {

        echo json_encode($this->_warehouseModel->showLoweringComponents());
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
    
    // getCruiseStartDate - return the current cruise start date.
	public function getCruiseStartDate() {

        $response['cruiseStartDate'] = $this->_warehouseModel->getCruiseStartDate();
        echo json_encode($response);
    }
    
    // getCruiseEndDate - return the current cruise end date.
    public function getCruiseEndDate() {

        $response['cruiseEndDate'] = $this->_warehouseModel->getCruiseEndDate();
        echo json_encode($response);
    }

        // getLoweringSize - return the size of the lowering directory.
    public function getLoweringSize() {

        echo json_encode($this->_warehouseModel->getLoweringSize());
    }
    
    // getLoweringID - return the current lowering ID.
    public function getLoweringID() {

        $response['loweringID'] = $this->_warehouseModel->getLoweringID();
        echo json_encode($response);
    }
    
    // getLoweringStartDate - return the current lowering start date.
    public function getLoweringStartDate() {

        $response['loweringStartDate'] = $this->_warehouseModel->getLoweringStartDate();
        echo json_encode($response);
    }
    
    // getLoweringEndDate - return the current lowering end date.
    public function getLoweringEndDate() {

        $response['loweringEndDate'] = $this->_warehouseModel->getLoweringEndDate();
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
        $transferLogDir ='';
        foreach($requiredExtraDirectories as $row) {
            if(strcmp($row->name, "Transfer Logs") === 0) {
                $transferLogDir = $row->destDir;
                break;
            }
        }
        
        $filename = $warehouseBaseDir . '/' . $cruiseID . '/' . $transferLogDir . '/' . 'TransferLogSummary.json';
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
    
    // getCruiseConfig - return OVDM cruise config
	public function getCruiseConfig() {
        
        $collectionSystemsTransfersModel = new \Models\Config\CollectionSystemTransfers();
        $extraDirectoriesModel = new \Models\Config\ExtraDirectories();
        $cruiseDataTransfersModel = new \Models\Config\CruiseDataTransfers();
        $shipToShoreTransfersModel = new \Models\Config\ShipToShoreTransfers();        
        
        $response['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $response['cruiseStartDate'] = $this->_warehouseModel->getCruiseStartDate();
        $response['cruiseEndDate'] = $this->_warehouseModel->getCruiseEndDate();
        $response['warehouseConfig'] = $this->_warehouseModel->getShipboardDataWarehouseConfig();
        $response['collectionSystemTransfersConfig'] = $collectionSystemsTransfersModel->getCruiseOnlyCollectionSystemTransfers();
        $response['extraDirectoriesConfig'] = $extraDirectoriesModel->getExtraDirectoriesConfig();
        $response['cruiseDataTransfersConfig'] = $cruiseDataTransfersModel->getCruiseDataTransfersConfig();
        $response['shipToShoreTransfersConfig'] = $shipToShoreTransfersModel->getShipToShoreTransfersConfig();

        if($this->_warehouseModel->showLoweringComponents()) {
            $response['loweringDataBaseDir'] = $this->_warehouseModel->getLoweringDataBaseDir();
        }

        foreach ($response['collectionSystemTransfersConfig'] as $key => $collectionSystemTransfersConfig) {
            $collectionSystemTransfersConfig->sourceDir = $this->translateOVDMVariables($collectionSystemTransfersConfig->sourceDir);
            $collectionSystemTransfersConfig->destDir = $this->translateOVDMVariables($collectionSystemTransfersConfig->destDir);
        }

        echo json_encode($response, JSON_PRETTY_PRINT);
    
    }

    // getLoweringConfig - return Lowering config
    public function getLoweringConfig() {
        
        $collectionSystemsTransfersModel = new \Models\Config\CollectionSystemTransfers();
        $extraDirectoriesModel = new \Models\Config\ExtraDirectories();
        $cruiseDataTransfersModel = new \Models\Config\CruiseDataTransfers();
        $shipToShoreTransfersModel = new \Models\Config\ShipToShoreTransfers();
                
        $response['loweringID'] = $this->_warehouseModel->getLoweringID();
        $response['loweringStartDate'] = $this->_warehouseModel->getLoweringStartDate();
        $response['loweringEndDate'] = $this->_warehouseModel->getLoweringEndDate();
        $response['collectionSystemTransfersConfig'] = $collectionSystemsTransfersModel->getLoweringOnlyCollectionSystemTransfers();

        foreach ($response['collectionSystemTransfersConfig'] as $key => $collectionSystemTransfersConfig) {
            $collectionSystemTransfersConfig->sourceDir = $this->translateOVDMVariables($collectionSystemTransfersConfig->sourceDir);
            $collectionSystemTransfersConfig->destDir = $this->translateOVDMVariables($collectionSystemTransfersConfig->destDir);
        }

        echo json_encode($response, JSON_PRETTY_PRINT);
    
    }
    
}