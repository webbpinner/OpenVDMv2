<?php

namespace Controllers\Config;
use Core\Controller;
use Core\View;
use Helpers\Session;
use Helpers\Password;
use Helpers\Url;

class Auth extends Controller {
    
    private $_model;
    
    public function __construct() {
        $this->_model = new \Models\Config\Auth();
    }
    
    public function login() {
        
        if(Session::get('loggedin')){
            Url::redirect('config');
        }
        
        if(isset($_POST['submit'])){
            
            $username = $_POST['username'];
            $password = $_POST['password'];
            $referrer = $_POST['referrer'];
            
            //validation
            if(Password::verify($password, $this->_model->getHash($username)) == false) {
                $error[] = 'Wrong username or password';
            }
            
            //if validation has passed, carry on
            if(!$error) {
                Session::set('loggedin',true);
                Session::set('userID', $this->_model->getUserID($username));

                $data = array('lastLogin' => date('Y-m-d G:i:s'));
                $where = array('userID' => $this->_model->getUserID($username));
                $this->_model->updateUser($data,$where);
                
                //Url::redirect($referrer, true);
                Url::redirect('config');
            }
        }
        
        $data['title'] = 'Login';
        $data['referrer'] = $_SERVER['HTTP_REFERER'];
        View::rendertemplate('loginheader', $data);
        View::render('Config/login', $data,$error);
        View::rendertemplate('footer', $data);
    }
    
    public function logout() {
        Session::destroy();
        Url::redirect('');
    }

}
