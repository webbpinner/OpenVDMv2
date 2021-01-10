<?php
/*
 * api/cruiseDataTransfers - RESTful api interface to cruise data transfers
 *
 * @license   http://opensource.org/licenses/GPL-3.0
 * @author Webb Pinner - oceandatarat@gmail.com - http://www.oceandatarat.org
 * @version 2.5
 * @date 2021-01-10
 */

namespace Controllers\Api;
use Core\Controller;

class CruiseDataTransfers extends Controller {

    private $_cruiseDataTransfersModel;

    public function __construct(){
        $this->_cruiseDataTransfersModel = new \Models\Config\CruiseDataTransfers();
    }

    public function getCruiseDataTransfers(){

        echo json_encode($this->_cruiseDataTransfersModel->getCruiseDataTransfers());
    }
    
    public function getCruiseDataTransfer($id){

        echo json_encode($this->_cruiseDataTransfersModel->getCruiseDataTransfer($id));
    }
    
    public function getRequiredCruiseDataTransfers(){

        echo json_encode($this->_cruiseDataTransfersModel->getRequiredCruiseDataTransfers());
    }

    public function getRequiredCruiseDataTransfer($id){

        echo json_encode($this->_cruiseDataTransfersModel->getRequiredCruiseDataTransfer($id));
    }
    
    // getCruiseDataTransfersStatuses - return the names and statuses of the cruise data transfers.
	public function getCruiseDataTransfersStatuses() {
        echo json_encode($this->_cruiseDataTransfersModel->getCruiseDataTransfersStatuses());
    }

    // getCruiseDataTransfersStatuses - return the names and statuses of the cruise data transfers.
	public function getRequiredCruiseDataTransfersStatuses() {
        echo json_encode($this->_cruiseDataTransfersModel->getRequiredCruiseDataTransfersStatuses());
    }

    // setStoppingCruiseDataTransfer
    public function setStoppingCruiseDataTransfer($id) {
        $this->_cruiseDataTransfersModel->setStoppingCruiseDataTransfer($id);
    }

    // setErrorCruiseDataTransfer
	public function setErrorCruiseDataTransfer($id) {
        $this->_cruiseDataTransfersModel->setErrorCruiseDataTransfer($id);
    }
    
    // setRunningCruiseDataTransfer
	public function setRunningCruiseDataTransfer($id) {
        $return = array();
        if(isset($_POST['jobPid'])){
            $this->_cruiseDataTransfersModel->setRunningCruiseDataTransfer($id, $_POST['jobPid']);
            $return['status'] = 'success';
        } else {
            $return['status'] = 'error';
            $return['message'] = 'missing POST data';
        }
        echo json_encode($return);
    }
    
    // setIdlerCruiseDataTransfer
	public function setIdleCruiseDataTransfer($id) {
        $this->_cruiseDataTransfersModel->setIdleCruiseDataTransfer($id);
    }

}
