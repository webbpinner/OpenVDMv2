<?php
/*
 * api/collectionSystemTransfers - RESTful api interface to collection system
 * transfers.
 *
 * @license   http://opensource.org/licenses/GPL-3.0
 * @author Webb Pinner - webb@oceandatarat.org - http://www.oceandatarat.org
 * @version 2.0
 * @date May 31, 2015
 */

namespace Controllers\Api;
use Core\Controller;

class CollectionSystemTransfers extends Controller {


    /**
    * The collectionSystemTransferModel object.
    * @var model
    */
    private $_collectionSystemTransfersModel;

    /**
    * Sets the username for the given user instance. If the username
    * is already set, it will be overwritten. Throws an invalid
    * argument exception if the provided username is of an invalid
    * format.
    *
    * @param string $sUsername The username string to set
    *
    * @return  User
    * @throws  InvalidArgumentException
    * @todo    Check to make sure the username isn't already taken
    *
    * @since   2012-07-07
    * @author  Bruno Skvorc <bruno@skvorc.me>
    *
    * @edit    2012-07-08<br />
    *          John Doe <john@doe.com><br />
    *          Changed some essential
    *          functionality for the better<br/>
    *          #edit3392
    */
    public function __construct(){
        $this->_collectionSystemTransfersModel = new \Models\Config\CollectionSystemTransfers();
    }

    public function getCollectionSystemTransfers(){
        echo json_encode($this->_collectionSystemTransfersModel->getCollectionSystemTransfers());
    }
    
    public function getActiveCollectionSystemTransfers(){
        echo json_encode($this->_collectionSystemTransfersModel->getActiveCollectionSystemTransfers());
    }

    public function getCruiseOnlyCollectionSystemTransfers(){
        echo json_encode($this->_collectionSystemTransfersModel->getCruiseOnlyCollectionSystemTransfers());
    }

    public function getLoweringOnlyCollectionSystemTransfers(){
        echo json_encode($this->_collectionSystemTransfersModel->getLoweringOnlyCollectionSystemTransfers());
    }

    public function getCollectionSystemTransfer($id){
        echo json_encode($this->_collectionSystemTransfersModel->getCollectionSystemTransfer($id));
    }
    
    // getCollectionSystemTransfersStatuses - return the names and statuses of the collection system transfers.
	public function getCollectionSystemTransfersStatuses() {
        echo json_encode($this->_collectionSystemTransfersModel->getCollectionSystemTransfersStatuses());
    }
    
    // setErrorCollectionSystemTransfersStatuses
	public function setErrorCollectionSystemTransfer($id) {
        $this->_collectionSystemTransfersModel->setErrorCollectionSystemTransfer($id);
    }
    
    // setRunningCollectionSystemTransfersStatuses
	public function setRunningCollectionSystemTransfer($id) {
        $return = array();
        if(isset($_POST['jobPid'])){
            $this->_collectionSystemTransfersModel->setRunningCollectionSystemTransfer($id, $_POST['jobPid']);
            $return['status'] = 'success';
        } else {
            $return['status'] = 'error';
            $return['message'] = 'missing POST data';
        }
        echo json_encode($return);
    }

    
    // setIdleCollectionSystemTransfersStatuses
	public function setIdleCollectionSystemTransfer($id) {
        $this->_collectionSystemTransfersModel->setIdleCollectionSystemTransfer($id);
    }

}