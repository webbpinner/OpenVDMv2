<?php
/*
 * api/warehouse - RESTful api interface to shipboard data warehouse
 * configuration data.
 *
 * @license   http://opensource.org/licenses/GPL-3.0
 * @author Webb Pinner - oceandatarat@gmail.com - http://www.oceandatarat.org
 * @version 2.5
 * @date 2021-01-10
 */

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
            $nowDateStr = gmdate('Y/m/d H:i');
            $cruiseDates = $this->_warehouseModel->getCruiseDates();

            if($cruiseDates['cruiseStartDate'] > $nowDateStr) {
                $response['warning'] = "Cruise has not started";
            } elseif ($cruiseDates['cruiseEndDate'] != "" && $cruiseDates['cruiseEndDate'] < $nowDateStr) {
                $response['warning'] = "Cruise has Ended";
            }

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
    
    // getShipboardDataWarehouseConfig - return the shipboard data warehouse configuration.
	public function getShipboardDataWarehouseConfig() {

        echo json_encode($this->_warehouseModel->getShipboardDataWarehouseConfig());
    }
    
    // getFreeSpace - return the free space on the server.
	public function getFreeSpace() {

        $data['freeSpace'] = $this->_warehouseModel->getFreeSpace()['freeSpace'];
        $data['totalSpace'] = $this->_warehouseModel->getTotalSpace()['totalSpace'];

        echo json_encode($data);
    }

    // getShowLoweringComponents - return whether or not to show lowering components.
    public function getShowLoweringComponents() {

        echo json_encode($this->_warehouseModel->getShowLoweringComponents());
    }

	// getCruiseSize - return the size of the cruise directory.
	public function getCruiseSize() {

        if(strcmp($this->_warehouseModel->getCruiseID(), '') === 0){
            $data['cruiseSize'] = '';
            $data['cruiseSizeUpdated'] = '1970/01/01 00:00:00';
            echo json_encode($data);

        } else {

            echo json_encode($this->_warehouseModel->getCruiseSize());

        }
    }
    
    // getCruiseID - return the current cruise ID.
	public function getCruiseID() {

        $response['cruiseID'] = $this->_warehouseModel->getCruiseID();
        echo json_encode($response);
    }
    
    // getCruiseDates - return the current cruise start/end dates.
    public function getCruiseDates() {

        $response['cruiseStartDate'] = $this->_warehouseModel->getCruiseStartDate();
        $response['cruiseEndDate'] = $this->_warehouseModel->getCruiseEndDate();
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

    public function getCruiseFinalizedDate() {

        $response = $this->_warehouseModel->getCruiseFinalizedDate();
        echo json_encode($response);
    }

    public function getCruises() {

        $response = $this->_warehouseModel->getCruises();
        echo json_encode($response);
    }

    // getLoweringSize - return the size of the lowering directory.
    public function getLoweringSize() {

        if(strcmp($this->_warehouseModel->getLoweringID(), '') === 0){
            $data['loweringSize'] = 'Undefined';
            $data['loweringSizeUpdated'] = '1970/01/01 00:00:00';
            echo json_encode($data);

        } else {

            echo json_encode($this->_warehouseModel->getLoweringSize());

        }

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

    public function getLoweringFinalizedDate() {

        $response = $this->_warehouseModel->getLoweringFinalizedDate();
        echo json_encode($response);
    }


    public function getLowerings() {

        $response = $this->_warehouseModel->getLowerings();
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
            if(strcmp($row->name, "Transfer_Logs") === 0) {
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

        if($this->_warehouseModel->getShowLoweringComponents()) {
            $response['loweringDataBaseDir'] = $this->_warehouseModel->getLoweringDataBaseDir();
        }

        foreach ($response['collectionSystemTransfersConfig'] as $key => $collectionSystemTransfersConfig) {
            $collectionSystemTransfersConfig->sourceDir = $this->translateOVDMVariables($collectionSystemTransfersConfig->sourceDir);
            $collectionSystemTransfersConfig->destDir = $this->translateOVDMVariables($collectionSystemTransfersConfig->destDir);
        }

        echo json_encode($response);
    
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

        echo json_encode($response);
    
    }

    public function setCruiseSize() {

        $this->_warehouseModel->setCruiseSize(array('value' => $_POST['bytes']));
    }
    
    public function setLoweringSize() {
    
        $this->_warehouseModel->setLoweringSize(array('value' => $_POST['bytes']));
    }
}
