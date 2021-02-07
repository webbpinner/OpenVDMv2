<?php

use Core\Language;
use Core\Error;
use Helpers\Session;
use Helpers\Url;

$loadingImage = '<img height="50" src="' . Url::templatePath() . 'images/loading.gif"/>';

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
                    <li class="<?php echo ($data['page']==='position'? 'active': ''); ?>"><a id="position" href="#position" data-toggle="tab">Position</a></li>
                    <li class="<?php echo ($data['page']==='weather'? 'active': ''); ?>"><a id="weather" href="#weather" data-toggle="tab">Weather</a></li>
                    <li class="<?php echo ($data['page']==='soundVelocity'? 'active': ''); ?>"><a id="soundVelocity" href="#soundVelocity" data-toggle="tab">Sound Velocity</a></li>
                    <li class=""><a id="dataQuality" href="#dataQuality" data-toggle="tab">Data Quality</a></li> 
                </ul>
            </div>
        </div>
    </div>
    <div class="row">
        <div class="col-lg-12">
            <div class="panel">
                <div class="panel-body">
                    <div class="row">
                        <div class="col-lg-12">
<?php
    for($i = 0; $i < sizeof($data['placeholders']); $i++){
?>
                            <div class="panel panel-default">
<?php
        for($j=0; $j < sizeof($data['placeholders'][$i]->dataFiles); $j++){
?>
                            <a id="<?php echo $data['placeholders'][$i]->dataFiles[$j][0]['type']; ?>"></a>
<?php
            $filecount += sizeof($data['placeholders'][$i]->dataFiles[$j]);
        }
?>
                                <div class="panel-heading"><?php echo $data['placeholders'][$i]->heading;?><?php echo ($data['placeholders'][$i]->plotType == 'chart'? '<i id="' . $data['placeholders'][$i]->id . '_expand-btn" class="expand-btn pull-right btn btn-sm btn-default fa fa-expand"></i>': ''); ?></div>                  
                                <div class="panel-body">
                                    <div class="<?php echo $data['placeholders'][$i]->plotType; ?>" id="<?php echo $data['placeholders'][$i]->id;?>_placeholder" style="min-height:<?php echo (strcmp($data['placeholders'][$i]->plotType, 'map') === 0? '493': '200'); ?>px;"><?php echo ($filecount > 0? $loadingImage: 'No Data Found.'); ?></div>
                                </div>
                                <div class="panel-footer">
                                    <div class="objectList" id="<?php echo $data['placeholders'][$i]->id;?>_objectList-placeholder">
                                        <form>                                            
<?php
        for($j = 0; $j < sizeof($data['placeholders'][$i]->dataTypes); $j++){
?>                                     
                                            <div class="row">
                                                <div class="col-lg-12"><strong><?php echo $data['placeholders'][$i]->dataFiles[$j][0]['type']; ?></strong></div>
<?php
            if(is_array($data['placeholders'][$i]->dataFiles[$j]) && sizeof($data['placeholders'][$i]->dataFiles[$j]) > 0){
                if(strcmp($data['placeholders'][$i]->dataTypes[$j], 'geoJSON')===0) {
?>
                                                <div class='col-lg-12'>
                                                    <input class='lp-checkbox' type="checkbox" value="<?php echo $data['placeholders'][$i]->dataFiles[$j][0]['type'];?>" checked> Latest Position
                                                </div></br>
<?php
                    for($k = sizeof($data['placeholders'][$i]->dataFiles[$j])-1; $k >= 0; $k--){
?>                              
                                                <div class='col-lg-4 col-sm-6'>
                                                    <input class='<?php echo $data['placeholders'][$i]->dataTypes[$j]; ?>-checkbox' type="checkbox" value="<?php echo $data['placeholders'][$i]->dataFiles[$j][$k]['dd_json'];?>" checked> <?php echo end(explode('/',$data['placeholders'][$i]->dataFiles[$j][$k]['raw_data']));?>
                                                    <a href="<?php echo $data['dataWarehouseApacheDir'] . '/' . $data['placeholders'][$i]->dataFiles[$j][$k]['raw_data']; ?>" download target="_blank"><i class="fa fa-download"></i></a>
                                                </div>
<?php
                    }
                } else if(strcmp($data['placeholders'][$i]->dataTypes[$j], 'tms')===0) {
                    for($k = sizeof($data['placeholders'][$i]->dataFiles[$j])-1; $k >= 0; $k--){
?>                              
                                                <div class='col-lg-4 col-sm-6'>
                                                    <input class='<?php echo $data['placeholders'][$i]->dataTypes[$j]; ?>-checkbox' type="checkbox" value="<?php echo $data['placeholders'][$i]->dataFiles[$j][$k]['dd_json'];?>" checked> <?php echo end(explode('/',$data['placeholders'][$i]->dataFiles[$j][$k]['raw_data']));?>
                                                    <a href="<?php echo $data['dataWarehouseApacheDir'] . '/' . $data['placeholders'][$i]->dataFiles[$j][$k]['raw_data']; ?>" download target="_blank"><i class="fa fa-download"></i></a>
                                                </div>
<?php
                    }
                } else if(strcmp($data['placeholders'][$i]->dataTypes[$j], 'json')===0) {
?>
                                                <div class="form-group">
<?php
                    for($k = sizeof($data['placeholders'][$i]->dataFiles[$j])-1; $k >= 0; $k--){
?>                              
                                                    <div class='col-lg-4 col-sm-6'>
                                                        <input class='<?php echo $data['placeholders'][$i]->dataTypes[$j]; ?>-radio' name="<?php echo $data['placeholders'][$i]->dataFiles[$j][$k]['type'];?>" type="radio" value="<?php echo $data['placeholders'][$i]->dataFiles[$j][$k]['dd_json'];?>"  <?php echo ($k === sizeof($data['placeholders'][$i]->dataFiles[$j])-1? 'checked' : '');   ?>> <?php echo end(explode('/',$data['placeholders'][$i]->dataFiles[$j][$k]['raw_data']));?>
                                                        <a href="<?php echo $data['dataWarehouseApacheDir'] . '/' . $data['placeholders'][$i]->dataFiles[$j][$k]['raw_data']; ?>" download target="_blank"><i class="fa fa-download"></i></a>
                                                    </div>
<?php
                    }
?>
                                                </div>
<?php
                    }
            } else {
?>
                                                <div class='col-lg-12'>No data found</div>
<?php
            }
?>
                                            </div>
<?php
        }
?>
                                        </form>
                                    </div>
                                </div>
                            </div>
<?php
    }
?>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>