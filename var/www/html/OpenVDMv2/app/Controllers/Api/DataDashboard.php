<?php

namespace Controllers\Api;
use Core\Controller;

class DataDashboard extends Controller {

    private $_dataDashboardModel;
    
    private $_validRecentDataTypes = array('tsg','met','gga','svp','twind');
    
    private function getDataDashboardDir() {
        $extraDirectoriesModel = new \Models\Config\ExtraDirectories();
        $extraDirectories = $extraDirectoriesModel->getRequiredExtraDirectories();
        foreach ($extraDirectories as $extraDirectory) {
            if (strcmp($extraDirectory->name, 'Dashboard Data') === 0){
                return $extraDirectory->destDir;
            }
        }
        return '';
    }
    
    private function getWarehouseBaseDir() {
        $warehouseModel = new \Models\Warehouse();
        return $warehouseModel->getShipboardDataWarehouseBaseDir();
    }

    public function __construct(){
        $this->_dataDashboardModel = new \Models\DataDashboard();
    }

    public function getCruises(){
        $cruiseIDs = $this->_dataDashboardModel->getCruises();
        $returnObj = array();
        foreach ($cruiseIDs as $cruiseID) {
            array_push($returnObj, $cruiseID->dataDashboardObjectCruise);
        }
        echo json_encode($returnObj);
    }

    public function getDataObjectTypes($cruise){
        
        $dataTypes = $this->_dataDashboardModel->getDataTypes($cruise);        
        $returnObj = array();
        foreach ($dataTypes as $dataType) {
            array_push($returnObj, $dataType->dataDashboardObjectType);
        }
        echo json_encode($returnObj);
        
    }

    public function getDataObjects($cruise){
        echo json_encode($this->_dataDashboardModel->getDataObjects($cruise));
    }

    public function getDataObjectsByType($cruise,$dataType){
        echo json_encode($this->_dataDashboardModel->getDataObjectsByType($cruise, $dataType));
    }

    public function getDataObject($dataObjectID){

        $return = array((object)array());

        $dataObject = $this->_dataDashboardModel->getDataObject($dataObjectID);

        if(count($dataObject) === 0) {
            $return[0]->error = "Data object not found.";
            echo json_encode($return);
        } else {
            echo json_encode($this->_dataDashboardModel->getDataObject($dataObjectID));
        }
    }

    public function getRecentData(){
        echo json_encode($this->_dataDashboardModel->getRecentData());
    }

    public function getRecentDataByType($dataType){
        echo json_encode($this->_dataDashboardModel->getRecentDataByType($dataType));
    }
    
    public function getDataObjectFile($dataObjectID){

        $baseDir = $this->getWarehouseBaseDir();
        
        $return = array((object)array());

        $dataObject = $this->_dataDashboardModel->getDataObject($dataObjectID);

        if(count($dataObject) === 0) {
            $return[0]->error = "Data object not found.";
        } else {
            $filename = $baseDir . '/' . $dataObject[0]->dataDashboardObjectFile;
            if (file_exists($filename) && is_readable($filename)) {
                echo file_get_contents($filename);
                return;
            } else {
                //echo $filename;
                $return[0]->error = "Data file not found or not reable.";
            }
        }
        echo json_encode($return);
    }

    public function getDataObjectFileVisualizerData($dataObjectID){

        $baseDir = $this->getWarehouseBaseDir();
        
        $return = array((object)array());

        $dataObject = $this->_dataDashboardModel->getDataObject($dataObjectID);

        if(count($dataObject) === 0) {
            $return[0]->error = "Data object not found.";
        } else {
            $filename = $baseDir . '/' . $dataObject[0]->dataDashboardObjectFile;
            if (file_exists($filename) && is_readable($filename)) {
                $fileContents =  json_decode(file_get_contents($filename));
                echo json_encode($fileContents->visualizerData);
                return;
            } else {
                //echo $filename;
                $return[0]->error = "Data file not found or not reable.";
            }
        }
        echo json_encode($return);
    }
    
    public function getDataObjectFileQualityTests($dataObjectID){

        $baseDir = $this->getWarehouseBaseDir();
        
        $return = array((object)array());

        $dataObject = $this->_dataDashboardModel->getDataObject($dataObjectID);

        if(count($dataObject) === 0) {
            $return[0]->error = "Data object not found.";
        } else {
            $filename = $baseDir . '/' . $dataObject[0]->dataDashboardObjectFile;
            if (file_exists($filename) && is_readable($filename)) {
                $fileContents =  json_decode(file_get_contents($filename));
                echo json_encode($fileContents->qualityTests);
                return;
            } else {
                //echo $filename;
                $return[0]->error = "Data file not found or not reable.";
            }
        }
        echo json_encode($return);
    }
    
    public function getDataObjectFileStats($dataObjectID){

        $baseDir = $this->getWarehouseBaseDir();
        
        $return = array((object)array());

        $dataObject = $this->_dataDashboardModel->getDataObject($dataObjectID);

        if(count($dataObject) === 0) {
            $return[0]->error = "Data object not found.";
        } else {
            $filename = $baseDir . '/' . $dataObject[0]->dataDashboardObjectFile;
            if (file_exists($filename) && is_readable($filename)) {
                $fileContents =  json_decode(file_get_contents($filename));
                echo json_encode($fileContents->stats);
                return;
            } else {
                //echo $filename;
                $return[0]->error = "Data file not found or not reable.";
            }
        }
        echo json_encode($return);
    }
    
    public function updateDataDashboardObjectsFromManifest($cruise){

        $baseDir = $this->getWarehouseBaseDir();
        $dataDashboardDir = $this->getDataDashboardDir();
            
        $return = array((object)array());
        $count = 0;
        $new = 0;
        $updated = 0;
        $removed = 0;
        $fileErrors = 0;


        // Get objects for cruise already in database
        $existingDataObjects = $this->_dataDashboardModel->getDataObjects($cruise);
        // open the manifest file
        $filename = $baseDir . '/' . $cruise . '/' . $dataDashboardDir . '/' . 'manifest.json';

        if (file_exists($filename) && is_readable($filename)) {
            $manifestData = json_decode(file_get_contents($filename));
            
            foreach ($existingDataObjects as $existingObject) {

                if(sizeof($manifestData) == 0) {
                    $where = array('dataDashboardObjectID' => $existingObject->dataDashboardObjectID);
                    $this->_dataDashboardModel->deleteDataObject($where);
                    $removed += 1;
                } elseif(isset($manifestData[$count]->dd_json) && isset($manifestData[$count]->type)) {
                    if($count < sizeof($manifestData)) {
                        $where = array('dataDashboardObjectID' => $existingObject->dataDashboardObjectID);
                        $data = array('dataDashboardObjectFile' => $manifestData[$count]->dd_json, 'dataDashboardRawFile' => $manifestData[$count]->raw_data, 'dataDashboardObjectType' => $manifestData[$count]->type, 'dataDashboardObjectCruise'=>$cruise);
                        $this->_dataDashboardModel->updateDataObject($data, $where);
                        $count += 1;
                        $updated += 1;
                    } else {
                        $where = array('dataDashboardObjectID' => $existingObject->dataDashboardObjectID);
                        $this->_dataDashboardModel->deleteDataObject($where);
                        $removed += 1;
                    }
                } else {
                    $fileErrors += 1;
                }
            }

            for( ; $count < sizeof($manifestData); $count++) {
                if(isset($manifestData[$count]->dd_json) && isset($manifestData[$count]->type)) {
                    $data = array('dataDashboardObjectFile' => $manifestData[$count]->dd_json, 'dataDashboardRawFile' => $manifestData[$count]->raw_data, 'dataDashboardObjectType' => $manifestData[$count]->type, 'dataDashboardObjectCruise'=>$cruise);
                    $this->_dataDashboardModel->insertDataObject($data);
                    $new += 1;
                } else {
                    $fileErrors += 1;
                }
            }

            $return[0]->updated = (string)$updated;
            $return[0]->removed = (string)$removed;
            $return[0]->new = (string)$new;
            $return[0]->fileErrors = (string)$fileErrors;
        } else {
            $return[0]->error = "Manifest file: " . $filename . " not found or not reable.";
        }

        echo json_encode($return);
    }

    public function getRecentDataObjectFileByType($cruise,$dataType){

        $dataObjects = $this->_dataDashboardModel->getDataObjectsByType($cruise, $dataType);
        $this->getDataObjectFile($dataObjects[count($dataObjects)-1]->dataDashboardObjectID);
    }

    public function updateRecentData() {
        
        $baseDir = $this->getWarehouseBaseDir();

        $return = array();

        $cruises = $this->_dataDashboardModel->getDruises();
        $lastCruise = $cruises[0]->dataObjectCruise;
        #var_dump($lastCruise);

        $dataTypes = $this->_dataDashboardModel->getDataTypes($lastCruise);
        #var_dump($dataTypes);

        $recentData = $this->_dataDashboardModel->getRecentData();
        foreach($recentData as $rd) {
            $data = array('recentDataValue' => 'NaN');
            $where = array('recentDataID' => $rd->recentDataID);
            $this->_dataDashboardModel->updateRecentData($data, $where);
        }

        foreach($dataTypes as $dataType){

            #var_dump($dataType);

            $dataObjectType = $dataType->dataDashboardObjectType;

            #var_dump($dataObjectType);

            $existingRecentData = $this->_dataDashboardModel->getRecentDataByType($dataObjectType);
            $existingRecentDataSize = count($existingRecentData);

            $dataObjects = $this->_dataDashboardModel->getDataObjectsByType($lastCruise, $dataObjectType);
            #var_dump($dataObjects);

            $lastDataObject = $dataObjects[count($dataObjects)-1];
            #var_dump($lastDataObject);

            $filename = $baseDir . '/' . $lastDataObject->dataDashboardObjectFile;
            #var_dump($filename);

            if (file_exists($filename) && is_readable($filename)) {

                $count = 0;

                $lastDataObjectFileContents = json_decode(file_get_contents($filename));
                #var_dump($lastDataObjectFileContents);
                
                if (strcmp($dataObjectType, "cam") === 0 ){
                    //ignore
                }elseif (strcmp($dataObjectType, "gga") === 0 ){
                    $coordinates = $lastDataObjectFileContents->geodata->coordinates;
                    $lastCoordinate = $coordinates[count($coordinates)-1];
                    $data = array('recentDataName' => 'Longitude',
                                  'recentDataUnit' => 'ddeg',
                                  'recentDataValue' => $lastCoordinate[0],
                                  'recentDataDataobjectid' => $lastDataObject->dataDashboardObjectID,
                                  'recentDataType' => $dataObjectType,
                                  'recentDataDatetime' => "0");

                    if($count < $existingRecentDataSize) {
                        $where = array('recentDataID' => $existingRecentData[$count]->recentDataID);
                        #var_dump($where);
                        $this->_dataDashboardModel->updateRecentData($data, $where);
                    } else {
                        $this->_dataDashboardModel->insertRecentData($data);
                    }
                    $count += 1;

                    $data = array('recentDataName' => 'Latitude',
                                  'recentDataUnit' => 'ddeg',
                                  'recentDataValue' => $lastCoordinate[1],
                                  'recentDataDataObjectID' => $lastDataObject->dataDashboardObjectID,
                                  'recentDataType' => $dataObjectType,
                                  'recentDataDatetime' => "0");

                    if($count < $existingRecentDataSize) {
                        $where = array('recentDataID' => $existingRecentData[$count]->recentDataID);
                        #var_dump($where);
			$this->_dataDashboardModel->update_recentData($data, $where);
                    } else {
                        $this->_dataDashboardModel->insertRecentData($data);
                    }
                    $count += 1;
                } else {
                    $lastDataObjectSize = count($lastDataObjectFileContents);
                    foreach($lastDataObjectFileContents as $sensorType){
                        
                        $recentData = $sensorType->data[count($sensorType->data)-1];
                        $data = array('recentDataName' => $sensorType->label,
                                      'recentDataUnit' => $sensorType->unit,
                                      'recentDataValue' => $recentData[1],
                                      'recentDataDataObjectID' => $lastDataObject->dataDashboardObjectID,
                                      'recentDataType' => $dataObjectType,
                                      'recentDataDatetime' => $recentData[0]);
                        #var_dump($data);

                        if($count < $existingRecentDataSize) {

                            $where = array('recentDataID' => $existingRecentData[$count]->recentDataID);
			    #var_dump($existingRecentData[$count]);
			    #var_dump($where);
                            $this->_dataDashboardModel->updateRecentData($data, $where);
                        } else {

                            $this->_dataDashboardModel->insertRecentData($data);
                        }
                        $count += 1;
                    }

                    for( ; $count < $existingRecentDataSize; $count++) {

                        $where = array('recentDataID' => $existingRecentData[$count]->recentDataID);
			#var_dump($where);
                        $this->_dataDashboardModel->deleteRecentData($where);
                    }
                }
                array_push($return, array('success' => "Data updated from " . $lastDataObject->dataDashboardObjectFile));
            } else {
                array_push($return, array('error' => "Data file: " . $lastDataObject->dataDashboardObjectFile . " not found or not readable."));
            }
        }

        $recentData = $this->_dataDashboardModel->getRecentData();
        foreach($recentData as $rd) {
            if(strcmp($rd->recentDataValue,'NaN') === 0) {
                $where = array('recentDataID' => $rd->recentDataID);
		#var_dump($where);
                $this->_dataDashboardModel->deleteRecentData($where);
            }
        }

        //var_dump($return);
        echo json_encode($return);
    }
}
