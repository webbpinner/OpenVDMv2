<?php

namespace Controllers\Api;
use Core\Controller;

class ShipToShoreTransfers extends Controller {

    private $_model;

    public function __construct(){
        $this->_model = new \Models\Config\ShipToShoreTransfers();
    }

    public function getShipToShoreTransfers(){

        echo json_encode($this->_model->getShipToShoreTransfers());
    }
    
    public function getRequiredShipToShoreTransfers(){

        echo json_encode($this->_model->getRequiredShipToShoreTransfers());
    }
}