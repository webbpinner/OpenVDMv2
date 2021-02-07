<?php
/*
 * api/shipToShoreTransfers - RESTful api interface to ship-to-shore
 * transfers.
 *
 * @license   http://opensource.org/licenses/GPL-3.0
 * @author Webb Pinner - oceandatarat@gmail.com - http://www.oceandatarat.org
 * @version 2.5
 * @date 2021-01-10
 */

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