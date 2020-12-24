<?php

namespace Models;
use Core\Model;

class DataDashboard extends Model {

    private $_tabs;
    private $_dashboardDataModel;

    public function __construct(){
        
        $this->_dashboardDataModel = new \Models\DashboardData();
        $this->_tabs = yaml_parse_file(DASHBOARD_CONF);
    }
    
    private function getAllDataTypes() {
        $dataTypes = array();
        foreach($this->_tabs as $tab) {
            foreach($tab['placeholderArray'] as $placeholder) {
                foreach($placeholder['dataArray'] as $data) {
                    array_push($dataTypes, $data['dataType']);
                }
            }
        }
        return array_unique($dataTypes, SORT_REGULAR);
    }
    
    private function getDataTypeByVisType($visType) {
        $dataTypes = array();
        foreach($this->_tabs as $tab) {
            foreach($tab['placeholderArray'] as $placeholder) {
                foreach($placeholder['dataArray'] as $data) {
                    if( strcmp($data['visType'], $visType) === 0 ) {
                        array_push($dataTypes, $data['dataType']);
                    }
                }
            }
        }
        return array_unique($dataTypes, SORT_REGULAR);
    }

    public function getJSONTypes() {
        return $this->getDataTypeByVisType('json');
    }

    public function getJSONReversedYTypes() {
        return $this->getDataTypeByVisType('json-reversed-y');
    }

    
    public function getGeoJSONTypes() {
        return $this->getDataTypeByVisType('geoJSON');
    }
    
    public function getTMSTypes() {
        return $this->getDataTypeByVisType('tms');
    }
        
    public function getSubPages() {
        $dataTypes = $this->getAllDataTypes();
        $subPages = array();
        foreach($dataTypes as $dataType) {
            foreach($this->_tabs as $tab) {
                foreach($tab['placeholderArray'] as $placeholder) {
                    foreach($placeholder['dataArray'] as $data) {
                        if( strcmp($data['dataType'], $dataType) === 0 ) {
                            $subPages[$dataType] = $tab['page'];
                            break;
                        }
                    }
                }
            }
        }
        return $subPages;
    }
    
    public function getDataDashboardTabs() {
        return $this->_tabs;
    }
    
    public function getDataDashboardTab($tabName) {
        foreach($this->_tabs as $tab) {
            
            if($tab['page'] == $tabName) {
                return $tab;
            }
        }
        return;
    }
    
}
?>
