<?php

namespace Models;
use Core\Model;


class TransferLogs extends Model {

    private $_warehouseModel;
    private $_cruiseDataDir;
    private $_cruiseID;
    private $_extraDirectoryModel;
    private $_transferLogDir;

    public function __construct(){
        $this->_warehouseModel = new \Models\Warehouse();
        $this->_cruiseDataDir = $this->_warehouseModel->getShipboardDataWarehouseBaseDir();
        $this->_cruiseID = $this->_warehouseModel->getCruiseID();
        $this->_extraDirectoryModel = new \Models\Config\ExtraDirectories();
        $this->_transferLogsDir = $this->_extraDirectoryModel->getExtraDirectoryByName('Transfer Logs')[0]->destDir;
    }

    private function outputLogFilenames($files) {
        $returnArray = array();
        for($i = sizeof($files)-1; $i >= 0; $i--) {
            array_push($returnArray, $files[$i]);
        }
        return $returnArray;
    }
    
    private function outputLogFileSummary($files) {
        $returnArray = array();
        
        for($i = sizeof($files)-1; $i >= 0; $i--) {
            if (file_exists($files[$i]) && is_readable($files[$i])) {
                $transferLogSummary = json_decode(file_get_contents($files[$i]));
                list($collectionSystem, $date) = explode("_", basename($files[$i]), 2);
                $date = explode(".", $date, 2)[0];

                if (strcmp($date, "Exclude") === 0) {
                    $obj = (object) array('collectionSystemName' => $collectionSystem, 'errorFiles' => $transferLogSummary->exclude);
                    array_push($returnArray, $obj);
                } else {
                    $obj = (object) array('collectionSystemName' => $collectionSystem, 'date' => $date, 'newFiles' => $transferLogSummary->new, 'updatedFiles' => $transferLogSummary->updated);
                    array_push($returnArray, $obj);                
                }
            }
        }
        
        if(strcmp($date, "Exclude") != 0) {
            if(sizeof($returnArray) > 0) {
                $sortArray = array();

                foreach($returnArray as $dataObject){
                    foreach($dataObject as $key=>$value){
                        if(!isset($sortArray[$key])){
                            $sortArray[$key] = array();
                        }
                        $sortArray[$key][] = $value;
                    }
                }

                $orderby = "date"; //change this to whatever key you want from the array

                array_multisort($sortArray[$orderby],SORT_DESC,$returnArray); 
            }            
        }
        
        //return $dataObjects;  
        return $returnArray;
    }
    
    public function getExcludeLogFilenames() {
        $files = glob($this->_cruiseDataDir . '/' . $this->_cruiseID . '/' . $this->_transferLogsDir ."/*_Exclude.log");
        return $this->outputLogFilenames($files);
    }
    
    public function getExcludeLogsSummary() {
        $files = glob($this->_cruiseDataDir . '/' . $this->_cruiseID . '/' . $this->_transferLogsDir ."/*_Exclude.log");
        return $this->outputLogFileSummary($files);
    }
    
    public function getShipboardLogFilenames($count = 0) {
        $files = preg_grep('#SSDW#', glob($this->_cruiseDataDir . '/' . $this->_cruiseID . '/' . $this->_transferLogsDir ."/*Z.log"), PREG_GREP_INVERT);
        if ($count > 0) {
            array_splice($files, 0, sizeof($files)-$count);
        }
        return $this->outputLogFilenames($files);
    }
    
    public function getShipboardLogsSummary($count = 0) {
        
        //preg_grep('#\.zip$#', glob('/dir/somewhere/*'), PREG_GREP_INVERT)
        array_multisort(array_map('filemtime', ($files = preg_grep('#SSDW#', glob($this->_cruiseDataDir . '/' . $this->_cruiseID . '/' . $this->_transferLogsDir ."/*Z.log"), PREG_GREP_INVERT))), SORT_ASC, $files);
        if ($count > 0) {
            array_splice($files, 0, sizeof($files)-$count);
        }
        return $this->outputLogFileSummary($files);
    }
    
    public function getShipToShoreLogFilenames($count = 0) {
        $files = glob($this->_cruiseDataDir . '/' . $this->_cruiseID . '/' . $this->_transferLogsDir ."/SSDW*.log");
        if ($count > 0) {
            array_splice($files, 0, sizeof($files)-$count);
        }
        return $this->outputLogFilenames($files);
    }
    
    public function getShipToShoreLogsSummary($count = 0) {
        $files = glob($this->_cruiseDataDir . '/' . $this->_cruiseID . '/' . $this->_transferLogsDir ."/SSDW*.log");
        if ($count > 0) {
            array_splice($files, 0, sizeof($files)-$count);
        }
        return $this->outputLogFileSummary($files);
    }
    
    public function getExcludeLogFilenameByName($name) {
        $files = glob($this->_cruiseDataDir . '/' . $this->_cruiseID . '/' . $this->_transferLogsDir ."/" . $name . "_Exclude.log");        
        return $this->outputLogFilenames($files);
    }
    
    public function getExcludeLogSummaryByName($name) {
        $files = glob($this->_cruiseDataDir . '/' . $this->_cruiseID . '/' . $this->_transferLogsDir ."/" . $name . "_Exclude.log");        
        return $this->outputLogFileSummary($files);
    }
    
    public function getShipboardLogFilenamesByName($name, $count = 0) {
        $files = glob($this->_cruiseDataDir . '/' . $this->_cruiseID . '/' . $this->_transferLogsDir ."/" . $name . "_*Z.log");
        if ($count > 0) {
            array_splice($files, 0, sizeof($files)-$count);
        }
        return $this->outputLogFilenames($files);
    }
    
    public function getShipboardLogsSummaryByName($name, $count = 0) {
        $files = glob($this->_cruiseDataDir . '/' . $this->_cruiseID . '/' . $this->_transferLogsDir ."/" . $name . "_*Z.log");
        if ($count > 0) {
            array_splice($files, 0, sizeof($files)-$count);
        }
        return $this->outputLogFileSummary($files);
    }
}
