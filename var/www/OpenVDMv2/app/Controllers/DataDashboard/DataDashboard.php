<?php

namespace Controllers\DataDashboard;
use Core\Controller;
use Core\View;
use Helpers\Session;
use Helpers\Url;

class DataDashboard extends Controller {
    
    private $_warehouseModel;
    private $_dataDashboardModel;

    public function __construct(){
        
        $this->_warehouseModel = new \Models\Warehouse();
        $this->_dataDashboardModel = new \Models\DataDashboard();
    }

    public function index(){
            
        $data['title'] = 'Data Dashboard';
        $data['css'] = array('leaflet');
        $data['javascript'] = array('main_dataDashboard', 'tabs_dataDashboard', 'dataDashboard', 'leaflet');
        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['systemStatus'] = $this->_warehouseModel->getSystemStatus();
        $data['dataObjectTypes'] = $this->_dataDashboardModel->getDataTypes($data['cruiseID']);
        if (sizeof($data['dataObjectTypes']) > 0) {
            array_push($data['javascript'], 'highcharts');
            array_push($data['javascript'], 'leaflet');
        }
        
        View::rendertemplate('header',$data);
        View::render('DataDashboard/main',$data);
        View::rendertemplate('footer',$data);
    }
    
    public function position(){
            
        $data['title'] = 'Position';
        $data['css'] = array('leaflet');
        $data['javascript'] = array('tabs_dataDashboard', 'position', 'leaflet', 'highcharts');
        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['systemStatus'] = $this->_warehouseModel->getSystemStatus();
        
        View::rendertemplate('header',$data);
        View::render('DataDashboard/position',$data);
        View::rendertemplate('footer',$data);
    }
    
    public function soundVelocity(){
            
        $data['title'] = 'Sound Velocity';
        $data['javascript'] = array('tabs_dataDashboard', 'soundVelocity', 'highcharts');
        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['systemStatus'] = $this->_warehouseModel->getSystemStatus();
        
        View::rendertemplate('header',$data);
        View::render('DataDashboard/soundVelocity',$data);
        View::rendertemplate('footer',$data);
    }

    public function weather(){
            
        $data['title'] = 'Weather';
        $data['javascript'] = array('tabs_dataDashboard','weather', 'highcharts');
        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['systemStatus'] = $this->_warehouseModel->getSystemStatus();
        
        View::rendertemplate('header',$data);
        View::render('DataDashboard/weather',$data);
        View::rendertemplate('footer',$data);
    }
    
    public function qualityControl(){
        
        $data['title'] = 'QA/QC';
        $data['javascript'] = array('tabs_dataDashboard','qualityControl');
        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['systemStatus'] = $this->_warehouseModel->getSystemStatus();
        $data['dataObjectTypes'] = $this->_dataDashboardModel->getDataTypes($data['cruiseID']);
        #var_dump($data['dataObjectTypes']);
        
        $dataTypeNum = sizeof($data['dataObjectTypes']);
        $data['dataDashboardObjectsByTypes'] = array($dataTypeNum);
        $data['dataDashboardObjectsQualityTestsByTypes'] = array($dataTypeNum);
        $data['dataDashboardObjectsStatsByTypes'] = array($dataTypeNum);
        
        for($i = 0; $i < $dataTypeNum; $i++)
        {
            $data['dataDashboardObjectsByTypes'][$i] = $this->_dataDashboardModel->getDataObjectsByType($data['cruiseID'], $data['dataObjectTypes'][$i]->dataDashboardObjectType);
            $fileNum = sizeof($data['dataDashboardObjectsByTypes'][$i]);
            $data['dataDashboardObjectsQualityTestsByTypes'][$i] = array($fileNum);
            $data['dataDashboardObjectsStatsByTypes'][$i] = array($fileNum);
            for($j = 0; $j < $fileNum; $j++) {
                $data['dataDashboardObjectsQualityTestsByTypes'][$i][$j] = $this->_dataDashboardModel->getDataObjectFileQualityTests($data['dataDashboardObjectsByTypes'][$i][$j]->dataDashboardObjectID)[0];
                if(sizeof($this->_dataDashboardModel->getDataObjectFileStats($data['dataDashboardObjectsByTypes'][$i][$j]->dataDashboardObjectID)[0])>0 ){
                    $data['dataDashboardObjectsStatsByTypes'][$i][$j] = true;
                } else {
                    $data['dataDashboardObjectsStatsByTypes'][$i][$j] = false;
                }
            }
        }
        
        View::rendertemplate('header',$data);
        View::render('DataDashboard/qualityControl',$data);
        View::rendertemplate('footer',$data);
    }
    
    public function qualityControlShowDataFileStats($id){
        
        $data['title'] = 'QA/QC';
        $data['javascript'] = array('tabs_dataDashboard','qualityControl');
        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['systemStatus'] = $this->_warehouseModel->getSystemStatus();
        $data['dataObjectTypes'] = $this->_dataDashboardModel->getDataTypes($data['cruiseID']);
        #var_dump($data['dataObjectTypes']);
        
        $dataTypeNum = sizeof($data['dataObjectTypes']);
        $data['dataDashboardObjectsByTypes'] = array($dataTypeNum);
        $data['dataDashboardObjectsQualityTestsByTypes'] = array($dataTypeNum);
        
        for($i = 0; $i < $dataTypeNum; $i++)
        {
            $data['dataDashboardObjectsByTypes'][$i] = $this->_dataDashboardModel->getDataObjectsByType($data['cruiseID'], $data['dataObjectTypes'][$i]->dataDashboardObjectType);
            $fileNum = sizeof($data['dataDashboardObjectsByTypes'][$i]);
            $data['dataDashboardObjectsQualityTestsByTypes'][$i] = array($fileNum);
            for($j = 0; $j < $fileNum; $j++) {
                $data['dataDashboardObjectsQualityTestsByTypes'][$i][$j] = $this->_dataDashboardModel->getDataObjectFileQualityTests($data['dataDashboardObjectsByTypes'][$i][$j]->dataDashboardObjectID)[0];
                if(sizeof($this->_dataDashboardModel->getDataObjectFileStats($data['dataDashboardObjectsByTypes'][$i][$j]->dataDashboardObjectID)[0])>0 ){
                    $data['dataDashboardObjectsStatsByTypes'][$i][$j] = true;
                } else {
                    $data['dataDashboardObjectsStatsByTypes'][$i][$j] = false;
                }
            }
        }
        
        $data['statsTitle'] = array_pop(explode("/", $this->_dataDashboardModel->getDataObject($id)[0]->dataDashboardRawFile));
        $data['stats'] = $this->_dataDashboardModel->getDataObjectFileStats($id)[0];
        
        View::rendertemplate('header',$data);
        View::render('DataDashboard/qualityControl',$data);
        View::rendertemplate('footer',$data);
    }
    
    public function qualityControlShowDataTypeStats($datatype){
        
        $data['title'] = 'QA/QC';
        $data['javascript'] = array('tabs_dataDashboard','qualityControl');
        $data['cruiseID'] = $this->_warehouseModel->getCruiseID();
        $data['systemStatus'] = $this->_warehouseModel->getSystemStatus();
        $data['dataObjectTypes'] = $this->_dataDashboardModel->getDataTypes($data['cruiseID']);
        #var_dump($data['dataObjectTypes']);
        
        $dataTypeNum = sizeof($data['dataObjectTypes']);
        $data['dataDashboardObjectsByTypes'] = array($dataTypeNum);
        $data['dataDashboardObjectsQualityTestsByTypes'] = array($dataTypeNum);
        
        for($i = 0; $i < $dataTypeNum; $i++)
        {
            $data['dataDashboardObjectsByTypes'][$i] = $this->_dataDashboardModel->getDataObjectsByType($data['cruiseID'], $data['dataObjectTypes'][$i]->dataDashboardObjectType);
            $fileNum = sizeof($data['dataDashboardObjectsByTypes'][$i]);
            $data['dataDashboardObjectsQualityTestsByTypes'][$i] = array($fileNum);
            for($j = 0; $j < $fileNum; $j++) {
                $data['dataDashboardObjectsQualityTestsByTypes'][$i][$j] = $this->_dataDashboardModel->getDataObjectFileQualityTests($data['dataDashboardObjectsByTypes'][$i][$j]->dataDashboardObjectID)[0];
                if(sizeof($this->_dataDashboardModel->getDataObjectFileStats($data['dataDashboardObjectsByTypes'][$i][$j]->dataDashboardObjectID)[0])>0 ){
                    $data['dataDashboardObjectsStatsByTypes'][$i][$j] = true;
                } else {
                    $data['dataDashboardObjectsStatsByTypes'][$i][$j] = false;
                }
            }
        }
        
        $data['statsTitle'] = $datatype;
        $data['stats'] = $this->_dataDashboardModel->getDataTypeStats($this->_warehouseModel->getCruiseID(), $datatype);
        
        View::rendertemplate('header',$data);
        View::render('DataDashboard/qualityControl',$data);
        View::rendertemplate('footer',$data);
    }

}
