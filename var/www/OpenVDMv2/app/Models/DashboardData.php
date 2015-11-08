<?php

namespace Models;
use Core\Model;


class DashboardData extends Model {

    private $_cruiseDataDir;
    private $_cruiseID;
    private $_dashboardDataDir;
    private $_manifestObj;

    public function __construct(){
        $warehouseModel = new \Models\Warehouse();
        $extraDirectoriesModel = new \Models\Config\ExtraDirectories();
        $this->_cruiseDataDir = $warehouseModel->getShipboardDataWarehouseBaseDir();
        $this->_cruiseID = $warehouseModel->getCruiseID();
        $this->_dashboardDataDir = $extraDirectoriesModel->getExtraDirectoryByName('Dashboard Data')[0]->destDir;

        $this->_manifestObj = null;
    }
    
    public function getDashboardManifest() {
        return $this->_manifestObj;
    }
    
    private function buildManifestObj(){

        $results = array();
        
        $manifestFile = $this->_cruiseDataDir . DIRECTORY_SEPARATOR . $this->_cruiseID . DIRECTORY_SEPARATOR . $this->_dashboardDataDir . DIRECTORY_SEPARATOR . "manifest.json";

        if (file_exists($manifestFile) && is_readable($manifestFile)) {
            $manifestContents = file_get_contents($manifestFile);
            $this->_manifestObj = json_decode($manifestContents,true);
        }
    }

    public function getDashboardDataTypes() {

        $dataTypes = array();

        //If the manifest object has not been set, set it.
        if($this->_manifestObj === null) {
            $this->buildManifestObj();

            //If the manifest object is still null, something's wrong, quit.
            if($this->_manifestObj === null) {
                return $dataTypes;
            }
        }


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

        //If the manifest object has not been set, set it.
        if($this->_manifestObj === null) {
            $this->buildManifestObj();
            
            //If the manifest object is still null, something's wrong, quit.
            if($this->_manifestObj === null) {
                return $dataObjects;
            }
        }
        
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
        
        //If the manifest object has not been set, set it.
        if($this->_manifestObj === null) {
            $this->buildManifestObj();
            
            //If the manifest object is still null, something's wrong, quit.
            if($this->_manifestObj === null) {
                return $dataObjects;
            }
        }
        
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
        
        //If the manifest object has not been set, set it.
        if($this->_manifestObj === null) {
            $this->buildManifestObj();
            
            //If the manifest object is still null, something's wrong, quit.
            if($this->_manifestObj === null) {
                return $dataObjects;
            }
        }
        
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
