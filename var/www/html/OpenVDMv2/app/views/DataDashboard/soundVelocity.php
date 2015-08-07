<?php

use Core\Error;
use Helpers\Session;

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
                    <li class=""><a id="position" href="#position" data-toggle="tab">Position</a></li>
                    <li class=""><a id="weather" href="#weather" data-toggle="tab">Weather</a></li>
                    <li class="active"><a id="soundVelocity" href="#soundVelocity" data-toggle="tab">Sound Velocity</a></li>
                    <li class=""><a id="qualityControl" href="#qualityControl" data-toggle="tab">QA/QC</a></li> 
                </ul>
            </div>
        </div>
    </div>
    <div class="row">
        <div class="col-lg-12">
            <div class="panel panel-default">
                <div class="panel-heading">tsg</div>
                <div class="panel-body">
                    <div id="tsg_placeholder"  style="min-height:200px;">Loading...</div>
                </div>
                <div class="panel-footer">
                    <div id="tsg_objectList">Loading...</div>
                </div>
            </div>
        </div>
    </div>
    <div class="row">
        <div class="col-lg-12">
            <div class="panel panel-default">
                <div class="panel-heading">svp</div>
                <div class="panel-body">
                    <div id="svp_placeholder"  style="min-height:200px;">Loading...</div>
                </div>
                <div class="panel-footer">
                    <div id="svp_objectList">Loading...</div>
                </div>
            </div>
        </div>
    </div>
