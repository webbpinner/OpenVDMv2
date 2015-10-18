<?php

namespace Controllers\Api;
use Core\Controller;

class Messages extends Controller {

    private $_messageModel;
    private $_messageLimit = "LIMIT 10";

    public function __construct(){
        $this->_messageModel = new \Models\Config\Messages();
    }

    public function newMessage(){

        var_dump($_POST);
        
        if(isset($_POST['message'])) {
            $this->_messageModel->insertMessage(array('message'=>$_POST['message']));
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