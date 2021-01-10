<?php
/*
 * api/messages - RESTful api interface to OpenVDM messages
 *
 * @license   http://opensource.org/licenses/GPL-3.0
 * @author Webb Pinner - oceandatarat@gmail.com - http://www.oceandatarat.org
 * @version 2.5
 * @date 2021-01-10
 */

namespace Controllers\Api;
use Core\Controller;

class Messages extends Controller {

    private $_messageModel;
    private $_messageLimit = "LIMIT 10";

    public function __construct(){
        $this->_messageModel = new \Models\Config\Messages();
    }

    public function newMessage(){

        //var_dump($_POST);

        if(isset($_POST['messageTitle']) && isset($_POST['messageBody'])) {
            $this->_messageModel->insertMessage(array('messageTitle'=>$_POST['messageTitle'], 'messageBody'=>$_POST['messageBody']));
            $return['status'] = 'success';
        } elseif(isset($_POST['messageTitle'])) {
            $this->_messageModel->insertMessage(array('messageTitle'=>$_POST['messageTitle'], 'messageBody'=>''));
            $return['status'] = 'success';
        } else {
            $return['status'] = 'error';
            $return['error'] = 'missing POST data';
        }
        echo json_encode($return);
    }
    
    public function viewedMessage($id){

        $this->_messageModel->viewedMessage($id);
        
        $return['status'] = 'success';
        
        echo json_encode($return);
    }
    
    public function getRecentMessages(){

        echo json_encode($this->_messageModel->getNewMessages($this->_messageLimit));
    }
    
    public function getNewMessagesTotal(){

        echo json_encode($this->_messageModel->getNewMessagesTotal());
    }


}
