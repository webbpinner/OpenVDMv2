<?php
/*
 * api/dashboardData - RESTful api interface to dashboard data objects.
 *
 * @license   http://opensource.org/licenses/GPL-3.0
 * @author Webb Pinner - oceandatarat@gmail.com - http://www.oceandatarat.org
 * @version 2.3
 * @date 2017-10-05
 */

namespace Controllers\Api;
use Core\Controller;

class DashboardData extends Controller {

    private $_model;

    public function __construct(){

        $this->_model = new \Models\DashboardData();
    }
    
    public function getCruises() {
        $cruiseModel = new \Models\Cruises();
        echo json_encode($cruiseModel->getCruises());
    }

    public function getDashboardDataTypes($cruiseID) {
        $this->_model->setCruiseID($cruiseID);
        echo json_encode($this->_model->getDashboardDataTypes($dataType));
    }
        
    public function getDataObjectsByType($cruiseID, $dataType){
        $this->_model->setCruiseID($cruiseID);
        $dataObjectList = $this->_model->getDashboardObjectsByTypes($dataType);
        if(is_array($dataObjectList) && sizeof($dataObjectList) > 0) {
            echo json_encode(array($dataObjectList));
        } else {
            echo json_encode(array());
        }
    }
    
    public function getLatestDataObjectByType($cruiseID, $dataType){
        $this->_model->setCruiseID($cruiseID);
        $dataObjectList = $this->_model->getDashboardObjectsByTypes($dataType);
        if(is_array($dataObjectList) && sizeof($dataObjectList) > 0) {
            echo json_encode(array($dataObjectList[sizeof($dataObjectList)-1]));
        } else {
            echo json_encode(array());
        }
    }
    
    public function getLatestVisualizerDataByType($cruiseID, $dataType){
        $this->_model->setCruiseID($cruiseID);
        $dataObjectList = $this->_model->getDashboardObjectsByTypes($dataType);
        if(is_array($dataObjectList) && sizeof($dataObjectList) > 0) {
            $lastDataObject = $dataObjectList[sizeof($dataObjectList)-1];
            //echo $lastDataObject['dd_json'];
            echo json_encode($this->_model->getDashboardObjectVisualizerDataByJsonName($lastDataObject['dd_json']));
        } else {
            echo json_encode(array());
        }
    }
    
    public function getLatestStatsByType($cruiseID, $dataType){
        $this->_model->setCruiseID($cruiseID);
        $dataObjectList = $this->_model->getDashboardObjectsByTypes($dataType);
        if(is_array($dataObjectList) && sizeof($dataObjectList) > 0) {
            $lastDataObject = $dataObjectList[sizeof($dataObjectList)-1];
            //echo $lastDataObject['dd_json'];
            echo json_encode($this->_model->getDashboardObjectStatsByName($lastDataObject['dd_json']));
        } else {
            echo json_encode(array());
        }
    }
    
    public function getLatestQualityTestsByType($cruiseID, $dataType){
        $this->_model->setCruiseID($cruiseID);
        $dataObjectList = $this->_model->getDashboardObjectsByTypes($dataType);
        if(is_array($dataObjectList) && sizeof($dataObjectList) > 0) {
            $lastDataObject = $dataObjectList[sizeof($dataObjectList)-1];
            //echo $lastDataObject['dd_json'];
            echo json_encode($this->_model->getDashboardObjectQualityTestsByName($lastDataObject['dd_json']));
        } else {
            echo json_encode(array());
        }
    }
    
    public function getDashboardObjectVisualizerDataByJsonName($cruiseID, $dd_json){
        $this->_model->setCruiseID($cruiseID);
        $dataObjectVisualizerData = $this->_model->getDashboardObjectVisualizerDataByJsonName($dd_json);
        if(is_array($dataObjectVisualizerData) && sizeof($dataObjectVisualizerData) > 0) {
            echo json_encode($dataObjectVisualizerData);
        } else {
            echo json_encode(array());
        }
    }
    
    public function getDashboardObjectVisualizerDataByRawName($cruiseID, $raw_data){
        $this->_model->setCruiseID($cruiseID);
        $dataObjectVisualizerData = $this->_model->getDashboardObjectVisualizerDataByRawName($raw_data);
        if(is_array($dataObjectVisualizerData) && sizeof($dataObjectVisualizerData) > 0) {
            echo json_encode($dataObjectVisualizerData);
        } else {
            echo json_encode(array());
        }
    }
    
    public function getDashboardObjectStatsByJsonName($cruiseID, $dd_json){
        $this->_model->setCruiseID($cruiseID);
        $dataObjectStats = $this->_model->getDashboardObjectStatsByJsonName($dd_json);
        if(is_array($dataObjectStats) && sizeof($dataObjectStats) > 0) {
            echo json_encode($dataObjectStats);
        } else {
            echo json_encode(array());
        }
    }
    
    public function getDashboardObjectStatsByRawName($cruiseID, $raw_data){
        $this->_model->setCruiseID($cruiseID);
        $dataObjectStats = $this->_model->getDashboardObjectStatsByRawName($raw_data);
        if(is_array($dataObjectStats) && sizeof($dataObjectStats) > 0) {
            echo json_encode($dataObjectStats);
        } else {
            echo json_encode(array());
        }
    }
    
    public function getDashboardObjectQualityTestsByJsonName($cruiseID, $dd_json){
        $this->_model->setCruiseID($cruiseID);
        $dataObjectQualityTests = $this->_model->getDashboardObjectQualityTestsByJsonName($dd_json);
        if(is_array($dataObjectQualityTests) && sizeof($dataObjectQualityTests) > 0) {
            echo json_encode($dataObjectQualityTests);
        } else {
            echo json_encode(array());
        }
    }
    
    public function getDashboardObjectQualityTestsByRawName($cruiseID, $raw_data){
        $this->_model->setCruiseID($cruiseID);
        $dataObjectQualityTests = $this->_model->getDashboardObjectQualityTestsByRawName($raw_data);
        if(is_array($dataObjectQualityTests) && sizeof($dataObjectQualityTests) > 0) {
            echo json_encode($dataObjectQualityTests);
        } else {
            echo json_encode(array());
        }
    }
}
