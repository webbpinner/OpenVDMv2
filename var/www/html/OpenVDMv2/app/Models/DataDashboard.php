<?php

namespace Models;
use Core\Model;

class DataDashboard extends Model {

    public function getCruises(){

        return $this->db->select("SELECT DISTINCT dataDashboardObjectCruise FROM ".PREFIX."DataDashboardObjects ORDER BY dataDashboardObjectCruise DESC");
    }

    public function getDataTypes($cruise){

        $dataTypes = $this->db->select("SELECT DISTINCT dataDashboardObjectType FROM ".PREFIX."DataDashboardObjects WHERE dataDashboardObjectCruise = :cruise ORDER BY dataDashboardObjectType",array(':cruise' => $cruise));
        return $dataTypes;
    }

    public function getDataObjects($cruise){

        return $this->db->select("SELECT * FROM ".PREFIX."DataDashboardObjects WHERE dataDashboardObjectCruise = :cruise ORDER BY dataDashboardObjectType, dataDashboardObjectFile",array(':cruise' => $cruise));
    }

    public function getDataObjectsByType($cruise, $dataType){

        return $this->db->select("SELECT * FROM ".PREFIX."DataDashboardObjects WHERE dataDashboardObjectType = :dataType AND dataDashboardObjectCruise = :cruise ORDER BY dataDashboardObjectFile",array(':dataType' => $dataType, ':cruise' => $cruise));
    }

    public function getDataObject($dataObjectID){

        return $this->db->select("SELECT * FROM ".PREFIX."DataDashboardObjects WHERE dataDashboardObjectID = :dataObjectID",array(':dataObjectID' => $dataObjectID));
    }
    
    public function getDataObjectFile($dataObjectID){

        $return = array((object)array());
        
        $dataObject = $this->getDataObject($dataObjectID);
        
        $warehouseModel = new \Models\Warehouse();
        $baseDir = $warehouseModel->getShipboardDataWarehouseBaseDir();

        if(count($dataObject) === 0) {
            $return[0]->error = "Data object not found.";
        } else {
            $filename = $baseDir . '/' . $dataObject[0]->dataDashboardObjectFile;
            if (file_exists($filename) && is_readable($filename)) {
                $return[0] = file_get_contents($filename);
            } else {
                //echo $filename;
                $return[0]->error = "Data file " . $filename . " not found or not reable.";
            }
        }
        return $return;
    }
    
    public function getDataObjectFileVisualizerData($dataObjectID){

        $return = array((object)array());
        
        $dataFileContents = $this->getDataObjectFile($dataObjectID);
        
        if($dataFileContents[0]->error) {
            $return[0]->error = $dataFileContents[0]->error;
        } else {
            $dataFileContentsObj = json_decode($dataFileContents[0]);
            $return[0] = $dataFileContentsObj->visualizerData;
        }
        return $return;
    }
    
    public function getDataObjectFileQualityTests($dataObjectID){

        $return = array((object)array());
        
        $dataFileContents = $this->getDataObjectFile($dataObjectID);
        
        if($dataFileContents[0]->error) {
            $return[0]->error = $dataFileContents[0]->error;
        } else {
            $dataFileContentsObj = json_decode($dataFileContents[0]);
            $return[0] = $dataFileContentsObj->qualityTests;
        }
        return $return;
    }
    
    public function getDataObjectFileStats($dataObjectID){

        $return = array((object)array());
        
        $dataFileContents = $this->getDataObjectFile($dataObjectID);
        
        if($dataFileContents[0]->error) {
            $return[0]->error = $dataFileContents[0]->error;
        } else {
            $dataFileContentsObj = json_decode($dataFileContents[0]);
            $return[0] = $dataFileContentsObj->stats;
        }
        return $return;
    }
    
    public function getDataTypeStats($cruise, $datatype){

        $return = array((object)array());
        
        $dataObjects = $this->getDataObjectsByType($cruise, $datatype);
        
        if(sizeof($dataObjects) === 0){
            $return[0]->error = 'No objects found of type ' . $datatype;
            return $return;
        }
        
        $dataTypeStatsObj = array((object)array());
        
        $init = false;
        for ($i=0; $i < sizeof($dataObjects); $i++) {
            $dataFileStatsObj = $this->getDataObjectFileStats($dataObjects[$i]->dataDashboardObjectID)[0];
            
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
                                echo "timeBounds";
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
                                echo "geoBounds";
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
                                echo "bounds";
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
                                echo "valueValidity";
                                #Sum values
                                $dataTypeStatsObj[$j]->statData[0] += $dataFileStatsObj[$j]->statData[0];

                                $dataTypeStatsObj[$j]->statData[1] += $dataFileStatsObj[$j]->statData[1];
                                
                                break;
                            case "rowValidity":
                                echo "rowValidity";
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

    public function updateDataObject($data, $where){

        $this->db->update(PREFIX."DataDashboardObjects",$data, $where);
    }

    public function getRecentData(){

        return $this->db->select("SELECT * FROM ".PREFIX."RecentData");
    }

    public function getRecentDataTypes(){

        return $this->db->select("SELECT DISTINCT recentDataType FROM ".PREFIX."RecentData");
    }

    public function getRecentDataByType($dataType){

        return $this->db->select("SELECT * FROM ".PREFIX."RecentData WHERE recentDataType = :dataType", array(':dataType' => $dataType));
    }

    public function insertDataObject($data) {

        $this->db->insert(PREFIX."DataDashboardObjects",$data);
    }

    public function deleteDataObject($where) {

        $this->db->delete(PREFIX."DataDashboardObjects",$where);
    }

    public function insertRecentData($data) {

        $this->db->insert(PREFIX."RecentData",$data);
    }

    public function deleteRecentData($where) {

        $this->db->delete(PREFIX."RecentData",$where);
    }

    public function updateRecentData($data, $where) {

        $this->db->update(PREFIX."RecentData",$data, $where);
    }

}
