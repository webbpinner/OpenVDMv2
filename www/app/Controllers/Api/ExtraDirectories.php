<?php
/*
 * api/extraDirectories - RESTful api interface to extra directories.
 *
 * @license   http://opensource.org/licenses/GPL-3.0
 * @author Webb Pinner - oceandatarat@gmail.com - http://www.oceandatarat.org
 * @version 2.5
 * @date 2021-01-10
 */

namespace Controllers\Api;
use Core\Controller;

class ExtraDirectories extends Controller {

    private $_model;

    public function __construct(){
        $this->_model = new \Models\Config\ExtraDirectories();
    }

    public function getExtraDirectories(){

        echo json_encode($this->_model->getExtraDirectories());
    }
    
    public function getExtraDirectory($id){

        echo json_encode($this->_model->getExtraDirectory($id));
    }

    public function getRequiredExtraDirectories(){

        echo json_encode($this->_model->getRequiredExtraDirectories());
    }

}