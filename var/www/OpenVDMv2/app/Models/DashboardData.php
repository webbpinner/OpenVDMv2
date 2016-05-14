<?php

namespace Models;
use Core\Model;


class DashboardData extends Model {

    const CONFIG_FN = 'ovdmConfig.json';
    const MANIFEST_FN = 'manifest.json';
    
    private $_cruiseDataDir;
    private $_manifestObj;
    private $_cruiseID;
    private $_warehouseModel;

    public function __construct($cruiseID = null) {
        $this->_warehouseModel = new \Models\Warehouse();
        $this->_cruiseDataDir = $this->_warehouseModel->getShipboardDataWarehouseBaseDir();
        $this->_manifestObj = null;
        if ($cruiseID == null){
            $this->setCruiseID($this->_warehouseModel->getCruiseID());
        } else {
            $this->setCruiseID($cruiseID);
        }
    }
    
    public function getDashboardManifest() {
        return $this->_manifestObj;
    }
    
    private function buildManifestObj(){

        $results = array();

        if($this->_manifestObj === null && $this->_cruiseID != null) {

            //Get the list of directories
            if (is_dir($this->_cruiseDataDir . DIRECTORY_SEPARATOR . $this->_cruiseID))
            {
                //Check each Directory for ovdmConfig.json
                $cruiseList = scandir($this->_cruiseDataDir . DIRECTORY_SEPARATOR . $this->_cruiseID);
                foreach ($cruiseList as $cruiseKey => $cruiseValue){
                    if (in_array($cruiseValue,array(self::CONFIG_FN))){
                        $ovdmConfigContents = file_get_contents($this->_cruiseDataDir . DIRECTORY_SEPARATOR . $this->_cruiseID . DIRECTORY_SEPARATOR . self::CONFIG_FN);
                        $ovdmConfigJSON = json_decode($ovdmConfigContents,true);
                        //Get the the directory that holds the DashboardData
                        for($i = 0; $i < sizeof($ovdmConfigJSON['extraDirectoriesConfig']); $i++){
                            if(strcmp($ovdmConfigJSON['extraDirectoriesConfig'][$i]['name'], 'Dashboard Data') === 0){
                                $dataDashboardList = scandir($this->_cruiseDataDir . DIRECTORY_SEPARATOR . $this->_cruiseID . DIRECTORY_SEPARATOR . $ovdmConfigJSON['extraDirectoriesConfig'][$i]['destDir']);
                                foreach ($dataDashboardList as $dataDashboardKey => $dataDashboardValue){
                                    //If a manifest file is found, add CruiseID to output
                                    if (in_array($dataDashboardValue,array(self::MANIFEST_FN))){
                                        $manifestContents = file_get_contents($this->_cruiseDataDir . DIRECTORY_SEPARATOR . $this->_cruiseID . DIRECTORY_SEPARATOR . $ovdmConfigJSON['extraDirectoriesConfig'][$i]['destDir'] . DIRECTORY_SEPARATOR . self::MANIFEST_FN);
					$this->_manifestObj = json_decode($manifestContents,true);
                                        break;
                                    }
                                }
                                break;
                            }
                        }
                        break;
                    }
                }
            }
        }
    }

    public function getDashboardDataTypes() {

        $dataTypes = array();

        foreach ($this->_manifestObj as $manifestItem){
            foreach ($manifestItem as $manifestItemKey => $manifestItemValue){
                if (strcmp($manifestItemKey, 'type') === 0){
                    if(!in_array($manifestItemValue,$dataTypes)){
                        $dataTypes[] = $manifestItemValue;
                        continue;
                    }
                }
            }
        }
        sort($dataTypes);
        return $dataTypes;
    }

    public function getDashboardObjectsByTypes($dataType) {

        $dataObjects = array();

        foreach ($this->_manifestObj as $manifestItem) {
            foreach ($manifestItem as $manifestItemKey => $manifestItemValue){
                if (strcmp($manifestItemKey, 'type') === 0){
                    if(strcmp($manifestItemValue, $dataType) === 0) {
                        $dataObjects[] = $manifestItem;
                        continue;
                    }
                }
            }
        }
        

        if(sizeof($dataObjects) > 0) {
            $sortArray = array();

            foreach($dataObjects as $dataObject){
                foreach($dataObject as $key=>$value){
                    if(!isset($sortArray[$key])){
                        $sortArray[$key] = array();
                    }
                    $sortArray[$key][] = $value;
                }
            }

            $orderby = "dd_json"; //change this to whatever key you want from the array

            array_multisort($sortArray[$orderby],SORT_ASC,$dataObjects); 
        }
        return $dataObjects;   
    }
    
    public function getDashboardObjectContentsByJsonName($dd_json){
        $dataObjectContents = '';
        
        $foundIt = false;
        foreach ($this->_manifestObj as $manifestItem) {
            foreach ($manifestItem as $manifestItemKey => $manifestItemValue){
                if (strcmp($manifestItemKey, 'dd_json') === 0){
                    if(strcmp($manifestItemValue, $dd_json) === 0) {
                        $dataObjectContents = file_get_contents($this->_cruiseDataDir . DIRECTORY_SEPARATOR . $dd_json);
                        $foundIt = true;
                        break;
                    }
                }
            }
            if($foundIt) {
                break;
            }
        }
        return $dataObjectContents;
    }
    
    public function getDashboardObjectContentsByRawName($raw_data){
        $dataObjectContents = '';
        
        $foundIt = false;
        foreach ($this->_manifestObj as $manifestItem) {
            foreach ($manifestItem as $manifestItemKey => $manifestItemValue){
                if (strcmp($manifestItemKey, 'raw_data') === 0){
                    if(strcmp($manifestItemValue, $raw_data) === 0) {
                        $dataObjectContents = file_get_contents($this->_cruiseDataDir . DIRECTORY_SEPARATOR . $manifestItem['dd_json']);
                        $foundIt = true;
                        break;
                    }
                }
            }
            if($foundIt) {
                break;
            }
        }
        return $dataObjectContents;
    }
    
    public function getDashboardObjectDataTypeByJsonName($dd_json){
        $dataType = '';
        
        foreach ($this->_manifestObj as $manifestItem) {
            if (strcmp($manifestItem['dd_json'], $dd_json) === 0) {
                $dataType = $manifestItem['type'];
                break;
            }
        }
        return $dataType;
    }

    public function getDashboardObjectDataTypeByRawName($raw_data){
        $dataType = '';
        
        foreach ($this->_manifestObj as $manifestItem) {
            if (strcmp($manifestItem['raw_data'], $raw_data) === 0) {
                $dataType = $manifestItem['type'];
                break;
            }
        }
        return $dataType;
    }
        
    public function getDashboardObjectVisualizerDataByJsonName($dd_json){
        $dataObjectContentsOBJ = json_decode($this->getDashboardObjectContentsByJsonName($dd_json));
        return $dataObjectContentsOBJ->visualizerData;
    }

    public function getDashboardObjectVisualizerDataByRawName($raw_data){
        $dataObjectContentsOBJ = json_decode($this->getDashboardObjectContentsByRawName($raw_data));
        return $dataObjectContentsOBJ->visualizerData;
    }

    public function getDashboardObjectStatsByJsonName($dd_json){
        $dataObjectContentsOBJ = json_decode($this->getDashboardObjectContentsByJsonName($dd_json));
        return $dataObjectContentsOBJ->stats;
    }
    
    public function getDashboardObjectStatsByRawName($raw_data){
        $dataObjectContentsOBJ = json_decode($this->getDashboardObjectContentsByRawName($raw_data));
        return $dataObjectContentsOBJ->stats;
    }
    
    public function getDashboardObjectQualityTestsByJsonName($dd_json){
        $dataObjectContentsOBJ = json_decode($this->getDashboardObjectContentsByJsonName($dd_json));
        return $dataObjectContentsOBJ->qualityTests;
    }
    
    public function getDashboardObjectQualityTestsByRawName($raw_data){
        $dataObjectContentsOBJ = json_decode($this->getDashboardObjectContentsByRawName($raw_data));
        return $dataObjectContentsOBJ->qualityTests;
    }
    
    public function getCruiseID(){
        return $this->_cruiseID;
    }
    
    public function setCruiseID($cruiseID) {
        $this->_cruiseID = $cruiseID;
        $this->buildManifestObj();
    }
    
    public function getDataTypeStats($dataType) {

        $return = array((object)array());
        
        $dataObjects = $this->getDashboardObjectsByTypes($dataType);
        
        if(sizeof($dataObjects) === 0){
            $return[0]->error = 'No objects found of type ' . $dataType;
            return $return;
        }
        
        $dataTypeStatsObj = array((object)array());
        
        $init = false;
        for ($i=0; $i < sizeof($dataObjects); $i++) {
            $dataFileStatsObj = $this->getDashboardObjectStatsByJsonName($dataObjects[$i]['dd_json']);
            
            if($dataFileStatsObj[0]->error) {
                $return[0]->error = $dataFileStatsObj[0]->error;
                return $return;
            } else {
                if(!$init){
                    $dataTypeStatsObj = $dataFileStatsObj;
                    $init = true;
                } else {
                    for ($j=0; $j < sizeof($dataFileStatsObj); $j++) {
                        switch ($dataFileStatsObj[$j]->statType){
                            case "timeBounds":
                                #Start Time
                                if($dataFileStatsObj[$j]->statData[0] < $dataTypeStatsObj[$j]->statData[0]){
                                    $dataTypeStatsObj[$j]->statData[0] = $dataFileStatsObj[$j]->statData[0];
                                }
                                
                                #End Time
                                if($dataFileStatsObj[$j]->statData[1] > $dataTypeStatsObj[$j]->statData[1]){
                                    $dataTypeStatsObj[$j]->statData[1] = $dataFileStatsObj[$j]->statData[1];
                                }
                                
                                break;
                                
                            case "geoBounds":
                                #North
                                if($dataFileStatsObj[$j]->statData[0] > $dataTypeStatsObj[$j]->statData[0]){
                                    $dataTypeStatsObj[$j]->statData[0] = $dataFileStatsObj[$j]->statData[0];
                                }
                                
                                #East
                                if($dataFileStatsObj[$j]->statData[1] < $dataTypeStatsObj[$j]->statData[1]){
                                    $dataTypeStatsObj[$j]->statData[1] = $dataFileStatsObj[$j]->statData[1];
                                }

                                #South
                                if($dataFileStatsObj[$j]->statData[2] < $dataTypeStatsObj[$j]->statData[2]){
                                    $dataTypeStatsObj[$j]->statData[2] = $dataFileStatsObj[$j]->statData[2];
                                }

                                #West
                                if($dataFileStatsObj[$j]->statData[3] < $dataTypeStatsObj[$j]->statData[3]){
                                    $dataTypeStatsObj[$j]->statData[3] = $dataFileStatsObj[$j]->statData[3];
                                }

                                break;
                                
                            case "bounds":
                                #Min
                                if($dataFileStatsObj[$j]->statData[0] < $dataTypeStatsObj[$j]->statData[0]){
                                    $dataTypeStatsObj[$j]->statData[0] = $dataFileStatsObj[$j]->statData[0];
                                }
                                
                                #Max
                                if($dataFileStatsObj[$j]->statData[1] > $dataTypeStatsObj[$j]->statData[1]){
                                    $dataTypeStatsObj[$j]->statData[1] = $dataFileStatsObj[$j]->statData[1];
                                }
                                
                                break;
                            
                            case "totalValue":
                                #Sum values
                                $dataTypeStatsObj[$j]->statData[0] += $dataFileStatsObj[$j]->statData[0];
                            
                                break;
                            
                            case "valueValidity":
                                #Sum values
                                $dataTypeStatsObj[$j]->statData[0] += $dataFileStatsObj[$j]->statData[0];

                                $dataTypeStatsObj[$j]->statData[1] += $dataFileStatsObj[$j]->statData[1];
                                
                                break;
                            case "rowValidity":
                                #Sum values
                                $dataTypeStatsObj[$j]->statData[0] += $dataFileStatsObj[$j]->statData[0];

                                $dataTypeStatsObj[$j]->statData[1] += $dataFileStatsObj[$j]->statData[1];
                                
                                break;
                                
                        }
                    }
                }   
            }
        }
        
        $fileCountStat = new \stdClass();
        $fileCountStat->statType = "totalValue";
        $fileCountStat->statName = "File Count";
        $fileCountStat->statData = array();
        $fileCountStat->statData[0] = sizeof($dataObjects);
        
        array_unshift($dataTypeStatsObj, $fileCountStat);
        
        $return = $dataTypeStatsObj;
        return $return;
    }
}
