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
                    <li class="active"><a id="main" href="#main" data-toggle="tab">Main</a></li>
                    <li class=""><a id="position" href="#position" data-toggle="tab">Position</a></li>
                    <li class=""><a id="weather" href="#weather" data-toggle="tab">Weather</a></li>
                    <li class=""><a id="soundVelocity" href="#soundVelocity" data-toggle="tab">Sound Velocity</a></li>
                    <li class=""><a id="dataQuality" href="#dataQuality" data-toggle="tab">Data Quality</a></li> 
                </ul>
            </div>
        </div>
    </div>
    <div class="row">

<?php
    for($i = 0; $i < sizeof($data['dataTypes']); $i++){
?>
        <div class="col-lg-4 col-md-6">
            <div class="panel panel-default">
                <div class="panel-body">
                    <div id="<?php echo $data['dataTypes'][$i]; ?>-placeholder" style="min-height:200px;">Loading...</div>
                </div>
                <div class="panel-footer"><?php echo $data['dataTypes'][$i]; ?></div>
            </div>
        </div>
<?php
    }
?>
    </div>
