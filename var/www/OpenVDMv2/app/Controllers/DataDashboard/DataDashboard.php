<?php

namespace Controllers\DataDashboard;
use Core\Controller;
use Core\View;
use Helpers\Session;
use Helpers\Url;

class Placeholder
{
    public $plotType;
    public $dataType;
    public $id;
    public $heading;
    public $dataTypes;
    public $dataFiles;
}

class DataDashboard extends Controller {
    
    private $_warehouseModel;
    private $_dashboardDataModel;

    public function __construct(){
        
        $this->_warehouseModel = new \Models\Warehouse();
        $this->_dashboardDataModel = new \Models\DashboardData();
    }

    public function index(){
            
        $data['title'] = 'Data Dashboard';
        $data['page'] = 'main';
        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['systemStatus'] = $this->_warehouseModel->getSystemStatus();
        $data['dataWarehouseApacheDir'] = $this->_warehouseModel->getDataWarehouseApacheDir();
        $data['css'] = array('leaflet');
        $data['javascript'] = array('dataDashboard', 'tabs_dataDashboard', 'leaflet', 'highcharts');
        $data['dataTypes'] = $this->_dashboardDataModel->getDashboardDataTypes();
        
        View::renderTemplate('header', $data);
        if( sizeof($data['dataTypes'])>0){
            View::render('DataDashboard/main', $data);
        } else {
            View::render('DataDashboard/noData', $data);
        }
        View::renderTemplate('footer', $data);
    }
    
    public function position(){
            
        $data['title'] = 'Position';
        $data['page'] = 'position';
        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['systemStatus'] = $this->_warehouseModel->getSystemStatus();
        $data['dataWarehouseApacheDir'] = $this->_warehouseModel->getDataWarehouseApacheDir();
        $data['css'] = array('leaflet');
        $data['javascript'] = array('tabs_dataDashboard', 'dataTabs', 'leaflet', 'highcharts');
        
        $position = new Placeholder();
        $position->plotType = 'map';
        $position->id = 'map';
        $position->heading = 'Position';
        $position->dataTypes = array('geoJSON', 'tms');
        $position->dataFiles = array(
            $this->_dashboardDataModel->getDashboardObjectsByTypes('gga'),
            $this->_dashboardDataModel->getDashboardObjectsByTypes('geotiff'),
        );

        $data['placeholders'] = array($position);
        
        $noDataFiles = true;
        for($i = 0; $i < sizeof($data['placeholders']); $i++) {
            for($j = 0; $j < sizeof($data['placeholders'][$i]->dataFiles); $j++) {
                if(sizeof($data['placeholders'][$i]->dataFiles[$j]) > 0) {
                    $noDataFiles = false;
                    break;
                }
            }
            
            if(!$noDataFiles) {
                break;
            }
        }
        
        View::renderTemplate('header', $data);
        if ($noDataFiles) {
            View::render('DataDashboard/noData', $data);
        } else {
            View::render('DataDashboard/dataDashboard', $data);
        }
        View::renderTemplate('footer', $data);
    }
    
    public function soundVelocity(){
            
        $data['title'] = 'Sound Velocity';
        $data['page'] = 'soundVelocity';
        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['systemStatus'] = $this->_warehouseModel->getSystemStatus();
        $data['dataWarehouseApacheDir'] = $this->_warehouseModel->getDataWarehouseApacheDir();
        $data['javascript'] = array('tabs_dataDashboard', 'dataTabs', 'highcharts');
        
        $tsg = new Placeholder();
        $tsg->plotType = 'chart';
        $tsg->id = 'tsg';
        $tsg->heading = 'Thermosalinograph Sensor';
        $tsg->dataTypes = array('json');
        $tsg->dataFiles = array(
            $this->_dashboardDataModel->getDashboardObjectsByTypes('tsg')
        );
        
        $svp = new Placeholder();
        $svp->plotType = 'chart';
        $svp->id = 'svp';
        $svp->heading = 'Sound Velocity Probe';
        $svp->dataTypes = array('json');
        $svp->dataFiles = array(
            $this->_dashboardDataModel->getDashboardObjectsByTypes('svp')
        );
        
        $data['placeholders'] = array($tsg, $svp);
        
        $noDataFiles = true;
        for($i = 0; $i < sizeof($data['placeholders']); $i++) {
            for($j = 0; $j < sizeof($data['placeholders'][$i]->dataFiles); $j++) {
                if(sizeof($data['placeholders'][$i]->dataFiles[$j]) > 0) {
                    $noDataFiles = false;
                    break;
                }
            }
            
            if(!$noDataFiles) {
                break;
            }
        }
        
        View::renderTemplate('header', $data);
        if ($noDataFiles) {
            View::render('DataDashboard/noData', $data);
        } else {
            View::render('DataDashboard/dataDashboard', $data);
        }
        View::renderTemplate('footer', $data);
    }

    public function weather(){
            
        $data['title'] = 'Weather';
        $data['page'] = 'weather';
        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['systemStatus'] = $this->_warehouseModel->getSystemStatus();
        $data['dataWarehouseApacheDir'] = $this->_warehouseModel->getDataWarehouseApacheDir();
        $data['javascript'] = array('tabs_dataDashboard','dataTabs', 'highcharts');
        
        $met = new Placeholder();
        $met->plotType = 'chart';
        $met->id = 'met';
        $met->heading = 'Meterological Sensor';
        $met->dataTypes = array('json');
        $met->dataFiles = array(
            $this->_dashboardDataModel->getDashboardObjectsByTypes('met')
        );
        
        $twind = new Placeholder();
        $twind->plotType = 'chart';
        $twind->id = 'twind';
        $twind->heading = 'Wind Sensor';
        $twind->dataTypes = array('json');
        $twind->dataFiles = array(
            $this->_dashboardDataModel->getDashboardObjectsByTypes('twind')
        );
        
        $data['placeholders'] = array($met, $twind);
        
        $noDataFiles = true;
        for($i = 0; $i < sizeof($data['placeholders']); $i++) {
            for($j = 0; $j < sizeof($data['placeholders'][$i]->dataFiles); $j++) {
                if(sizeof($data['placeholders'][$i]->dataFiles[$j]) > 0) {
                    $noDataFiles = false;
                    break;
                }
            }
            
            if(!$noDataFiles) {
                break;
            }
        }
        
        View::renderTemplate('header', $data);
        if ($noDataFiles) {
            View::render('DataDashboard/noData', $data);
        } else {
            View::render('DataDashboard/dataDashboard', $data);
        }
        View::renderTemplate('footer', $data);
    }
    
    public function dataQuality(){
        
        $data['title'] = 'Data Quality';
        $data['page'] = 'dataQuality';
        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['systemStatus'] = $this->_warehouseModel->getSystemStatus();
        $data['dataWarehouseApacheDir'] = $this->_warehouseModel->getDataWarehouseApacheDir();
        $data['javascript'] = array('tabs_dataDashboard','dataQuality');
        $data['dataTypes'] = $this->_dashboardDataModel->getDashboardDataTypes();
        $data['dataObjects'] = array();
        $data['dataObjectsQualityTests'] = array();
        $data['dataObjectsStats'] = array();
        
        for($i = 0; $i < sizeof($data['dataTypes']); $i++) {
            array_push($data['dataObjects'], $this->_dashboardDataModel->getDashboardObjectsByTypes($data['dataTypes'][$i]));
            array_push($data['dataObjectsQualityTests'], array());
            array_push($data['dataObjectsStats'], array());
            for($j = 0; $j < sizeof($data['dataObjects'][$i]); $j++) {
                //var_dump($dashboardDataModel->getDashboardObjectQualityTestsByJsonName($data['dataObjects'][$i][$j]['dd_json']));
                array_push($data['dataObjectsQualityTests'][$i], $this->_dashboardDataModel->getDashboardObjectQualityTestsByJsonName($data['dataObjects'][$i][$j]['dd_json']));
                array_push($data['dataObjectsStats'][$i], $this->_dashboardDataModel->getDashboardObjectStatsByJsonName($data['dataObjects'][$i][$j]['dd_json']));
            }
        }
        
        View::renderTemplate('header', $data);
        if( sizeof($data['dataTypes'])>0){
            View::render('DataDashboard/dataQuality', $data);
        } else {
            View::render('DataDashboard/noData', $data);
        }
        View::renderTemplate('footer', $data);
    }
    
    public function dataQualityShowFileStats($raw_data){
        
        $data['title'] = 'Data Quality';
        $data['page'] = 'dataQuality';
        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['systemStatus'] = $this->_warehouseModel->getSystemStatus();
        $data['javascript'] = array('tabs_dataDashboard', 'dataQuality');
        $data['dataTypes'] = $this->_dashboardDataModel->getDashboardDataTypes();
        $data['dataObjects'] = array();
        $data['dataObjectsQualityTests'] = array();
        $data['dataObjectsStats'] = array();
        
        for($i = 0; $i < sizeof($data['dataTypes']); $i++) {
            array_push($data['dataObjects'], $this->_dashboardDataModel->getDashboardObjectsByTypes($data['dataTypes'][$i]));
            array_push($data['dataObjectsQualityTests'], array());
            array_push($data['dataObjectsStats'], array());
            for($j = 0; $j < sizeof($data['dataObjects'][$i]); $j++) {
                //var_dump($dashboardDataModel->getDashboardObjectQualityTestsByJsonName($data['dataObjects'][$i][$j]['dd_json']));
                array_push($data['dataObjectsQualityTests'][$i], $this->_dashboardDataModel->getDashboardObjectQualityTestsByJsonName($data['dataObjects'][$i][$j]['dd_json']));
                array_push($data['dataObjectsStats'][$i], $this->_dashboardDataModel->getDashboardObjectStatsByJsonName($data['dataObjects'][$i][$j]['dd_json']));
            }
        }
        
        $data['statsTitle'] = array_pop(explode("/", $raw_data));
        $data['stats'] = $this->_dashboardDataModel->getDashboardObjectStatsByRawName($raw_data);
        
        View::renderTemplate('header', $data);
        View::render('DataDashboard/dataQuality', $data);
        View::renderTemplate('footer', $data);
    }
    
    public function dataQualityShowDataTypeStats($dataType){
        
        $data['title'] = 'Data Quality';
        $data['page'] = 'dataQuality';
        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['systemStatus'] = $this->_warehouseModel->getSystemStatus();
        $data['javascript'] = array('tabs_dataDashboard', 'dataQuality');
        $data['dataTypes'] = $this->_dashboardDataModel->getDashboardDataTypes();
        $data['dataObjects'] = array();
        $data['dataObjectsQualityTests'] = array();
        $data['dataObjectsStats'] = array();
        
        for($i = 0; $i < sizeof($data['dataTypes']); $i++) {
            array_push($data['dataObjects'], $this->_dashboardDataModel->getDashboardObjectsByTypes($data['dataTypes'][$i]));
            array_push($data['dataObjectsQualityTests'], array());
            array_push($data['dataObjectsStats'], array());
            for($j = 0; $j < sizeof($data['dataObjects'][$i]); $j++) {
                //var_dump($dashboardDataModel->getDashboardObjectQualityTestsByJsonName($data['dataObjects'][$i][$j]['dd_json']));
                array_push($data['dataObjectsQualityTests'][$i], $this->_dashboardDataModel->getDashboardObjectQualityTestsByJsonName($data['dataObjects'][$i][$j]['dd_json']));
                array_push($data['dataObjectsStats'][$i], $this->_dashboardDataModel->getDashboardObjectStatsByJsonName($data['dataObjects'][$i][$j]['dd_json']));
            }
        }
        
        $data['statsTitle'] = $dataType;
        $data['stats'] = $this->_dashboardDataModel->getDataTypeStats($dataType);
        
        View::renderTemplate('header', $data);
        View::render('DataDashboard/dataQuality', $data);
        View::renderTemplate('footer', $data);
    }

}
