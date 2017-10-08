<?php
/*
 * api/transferLogs - RESTful api interface to collection system and ship-
 * to-shore transfers logs.
 *
 * @license   http://opensource.org/licenses/GPL-3.0
 * @author Webb Pinner - oceandatarat@gmail.com - http://www.oceandatarat.org
 * @version 2.3
 * @date 2017-10-05
 */

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