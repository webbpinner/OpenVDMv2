<?php

namespace Controllers\Config;
use Core\Controller;
use Core\View;
use Helpers\Password;
use Helpers\Session;
use Helpers\Url;

class Users extends Controller {

    private $_model;

    public function __construct(){
        if(!Session::get('loggedin')){
            Url::redirect('config/login');
        }

        $this->_model = new \Models\Config\Users();
    }
        
    public function index(){
        $data['title'] = 'Configuration';
        $data['users'] = $this->_model->getUsers();
        //$data['javascript'] = array('');
        View::rendertemplate('header',$data);
        View::render('Config/users',$data);
        View::rendertemplate('footer',$data);
    }

    public function add(){
        $data['title'] = 'Add User';

        if(isset($_POST['submit'])){
            $username = $_POST['username'];
            $password = $_POST['password'];

            if($username == ''){
                $error[] = 'Username is required';
            }

            if($password == ''){
                $error[] = 'Password is required';
            } 
                
            if(strcmp($password, $_POST['password2']) !== 0) {
                $error[] = 'Passwords must match';
            }

            if(!$error){
                $postdata = array(
                    'username' => $username,
                    'password' => Password::make($password)//,
                );

                $this->_model->insertUser($postdata);
                Session::set('message','User Added');
                Url::redirect('config/users');
            }
        }

        View::rendertemplate('header',$data);
        View::render('config/addUser',$data,$error);
        View::rendertemplate('footer',$data);
    }
        
    public function edit($id){
        $data['title'] = 'Edit User';
        $data['row'] = $this->_model->getUser($id);

        if(isset($_POST['submit'])){
            $username = $_POST['username'];
            $password = $_POST['password'];

            if($username == ''){
                $error[] = 'Username is required';
            }

            if($password == ''){
                $error[] = 'Password is required';
            }        

            if(strcmp($password, $_POST['password2']) !== 0) {
                $error[] = 'Passwords must match';
            }
            

                
            if(!$error){
                $postdata = array(
                    'username' => $username,
                    'password' => Password::make($password)
                );
            
                $where = array('userID' => $id);
                $this->_model->updateUser($postdata,$where);
                Session::set('message','User Updated');
                Url::redirect('config');
            }
        }

        View::rendertemplate('header',$data);
        View::render('Config/editUser',$data,$error);
        View::rendertemplate('footer',$data);
    }
    
    public function delete($id){
        $where = array('userID' => $id);
        $this->_model->deleteUser($where);
        Session::set('message','User Deleted');
        Url::redirect('config/users');
    }
}