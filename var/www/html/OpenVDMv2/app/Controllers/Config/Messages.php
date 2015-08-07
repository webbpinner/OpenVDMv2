<?php
namespace controllers\config;
use Core\Controller;
use Core\View;
use Helpers\Url;
use Helpers\Session;
use Helpers\Paginator;

class Messages extends Controller {

    private $_messagesModel;

    public function __construct(){
        if(!Session::get('loggedin')){
            Url::redirect('config/login');
        }

        $this->_messagesModel = new \Models\Config\Messages();
    }
        
    public function index(){
        $data['title'] = 'Messages';
        
        $pages = new Paginator('15','page');

        $pages->setTotal($this->_messagesModel->getMessagesTotal());
        $data['messages'] = $this->_messagesModel->getMessages($pages->getLimit());
        $data['page_links'] = $pages->pageLinks();
        
        
//        $data['javascript'] = array('');
        View::rendertemplate('header',$data);
        View::render('Config/messages',$data);
        View::rendertemplate('footer',$data);
    }
    
    public function deleteMessage($id){
        $where = array('messageID' => $id);
        $this->_messagesModel->deleteMessage($where);
        Session::set('message','Message Deleted');
        Url::redirect('config/messages');
    }
    
    public function viewedMessage($id){
        $this->_messagesModel->viewedMessage($id);
        Url::redirect('config/messages');
    }
    
    public function viewAllMessages(){
        $this->_messagesModel->viewAllMessages();
        Url::redirect('config/messages');
    }
    
    public function deleteAllMessages(){
        $this->_messagesModel->deleteAllMessages();
        Session::set('message','Messages Deleted');
        Url::redirect('config/messages');
    }

}