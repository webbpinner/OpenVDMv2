<?php

namespace Controllers\Api;
use Core\Controller;

class TransferLogs extends Controller {

    private $_model;

    public function __construct(){

        $this->_model = new \Models\TransferLogs();
    }
    
    public function getExcludeLogsSummary() {
        echo json_encode($this->_model->getExcludeLogsSummary());
    }

    public function getShipboardLogsSummary($count = 0) {
        echo json_encode($this->_model->getShipboardLogsSummary($count));
    }

    public function getShipToShoreLogsSummary($count = 0) {
        echo json_encode($this->_model->getShipToShoreLogsSummary($count));
    }
}