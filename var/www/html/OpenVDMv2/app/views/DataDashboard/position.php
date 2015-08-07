<?php

use Core\Error;
use Helpers\Session;

//var_dump($data['dataObjectTypes']);
?>

    <div class="row">
        <div class="col-lg-12">
            <?php echo Error::display(Session::pull('message'), 'alert alert-success'); ?>
        </div>
    </div>

    <div class="row">
        <div class="col-lg-12">
            <div class="tabbable" style="margin-bottom: 18px;">
                <ul class="nav nav-tabs">
                    <li class=""><a id="main" href="#main" data-toggle="tab">Main</a></li>
                    <li class="active"><a id="position" href="#position" data-toggle="tab">Position</a></li>
                    <li class=""><a id="weather" href="#weather" data-toggle="tab">Weather</a></li>
                    <li class=""><a id="soundVelocity" href="#soundVelocity" data-toggle="tab">Sound Velocity</a></li>
                    <li class=""><a id="qualityControl" href="#qualityControl" data-toggle="tab">QA/QC</a></li> 
                </ul>
            </div>
        </div>
    </div>
    <div class="row">
        <div class="col-lg-12">
            <div class="panel panel-default">
                <div class="panel-heading">Position</div>
                <div class="panel-body">
                    <div id="gga_placeholder" style="min-height:494px;">Loading...</div>
                </div>
                <div class="panel-footer">
                    <div id="gga_objectList">Loading...</div>
                    <div id="geotiff_objectList">Loading...</div>
                </div>
            </div>
        </div>
    </div>
