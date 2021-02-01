<?php

use Core\Error;
use Helpers\Session;

$enableSSDW = false;
foreach($data['requiredCruiseDataTransfers'] as $row){
    if (strcmp($row->name, "SSDW") == 0) {
        if (strcmp($row->enable, "1") == 0) {
            $enableSSDW = true;
        }
        break;
    }
}
?>
    <div class="row">
        <div class="col-lg-12">
            <?php echo Error::display(Session::pull('message'), 'alert alert-success'); ?>
        </div>
    </div>

    <div class="row">
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">Incorrect Filenames Detected</div>
                <div class="panel-body" id="filenameErrors">
<?php 
    $noErrors = True;
    if( is_array($data['filenameErrors']) && sizeof($data['filenameErrors']) > 0) {
?>
<?php
        foreach($data['filenameErrors'] as $row) {
            if(is_array($row->errorFiles) && sizeof($row->errorFiles) > 0) {
?>
                    <h5><?php echo $row->collectionSystemName; ?></h5>
                    <ul>
<?php
               if( is_array($row->errorFiles) && sizeof($row->errorFiles) <= 20) {
                   foreach($row->errorFiles as $file) {
?>
                        <li><small><?php echo $file; ?></small></li>
<?php
                    }
               } else {
                   for($i = 0; $i < 20; $i++) {
?>
                        <li><small><?php echo $row->errorFiles[$i]; ?></small></li>
<?php
                   }
?>
                        <li><small>...and <strong><?php echo sizeof($row->errorFiles)-20; ?></strong> other files</small></li>
<?php
               }
?>
                    </ul>
<?php
                $noErrors = False;
            }
        }
    }

    if($noErrors) {
?>
                    <h5>No Filename Errors Detected</h5>               
<?php
    }
?>
                </div>
            </div>
            <div class="panel panel-default">
                <div class="panel-heading">Recent Shipboard Data Transfers</div>
                <div class="panel-body" id="shipboardTransfers">
<?php
    if($data['shipboardTransfers']) {
        $itemNum = 0;
    
        for($i = 0; $i < count($data['shipboardTransfers']); $i++ ) {
?>
                    <h5><?php echo $data['shipboardTransfers'][$i]->collectionSystemName; ?> - <?php $timestamp = DateTime::createFromFormat('Ymd\THis\Z', $data['shipboardTransfers'][$i]->date, new DateTimeZone('UTC')); echo $timestamp->format('Y-m-d H:i:s T'); ?></h5>
                    <ul>
<?php
            if( is_array($data['shipboardTransfers'][$i]->newFiles) && sizeof($data['shipboardTransfers'][$i]->newFiles) <= 20) {
                foreach($data['shipboardTransfers'][$i]->newFiles as $file) {
?>
                        <li><small><?php echo $file; ?></small></li>
<?php
                }
            } else {
                for($j = 0; $j < 20; $j++) {
?>
                        <li><small><?php echo $data['shipboardTransfers'][$i]->newFiles[$j]; ?></small></li>
<?php
                }
?>
                        <li><small>...and <strong><?php echo sizeof($data['shipboardTransfers'][$i]->newFiles)-20; ?></strong> other files</small></li>
<?php
            }

	    if(count($data['shipboardTransfers'][$i]->updatedFiles) > 0) {
?>
                        <li><small><?php echo count($data['shipboardTransfers'][$i]->updatedFiles); ?> File(s) Updated.</small></li>
<?php
            }
?>
                    </ul>
<?php
            $itemNum++;
        }
    } else {
?>
                    <h5>No Recent Shipboard Transfers Have Occured</h5>               
<?php
    }
?>
                </div>
            </div>
            <div class="panel panel-default">
                <div class="panel-heading">Recent Ship-To-Shore Data Transfers</div>
                <div class="panel-body" id="shipToShoreTransfers">
<?php
    if($data['shipToShoreTransfers']) {
        $itemNum = 0;
        
        for($i = 0; $i < count($data['shipToShoreTransfers']); $i++ ) {
?>
                    <h5><?php echo $data['shipToShoreTransfers'][$i]->shipToShoreTransferName; ?> - <?php $timestamp = DateTime::createFromFormat('Ymd\THis\Z', $data['shipToShoreTransfers'][$i]->date, new DateTimeZone('UTC')); echo $timestamp->format('Y-m-d H:i:s T'); ?></h5>
                    <ul>
<?php
	    if( is_array($data['shipToShoreTransfers'][$i]->newFiles) && sizeof($data['shipToShoreTransfers'][$i]->newFiles) <= 20) {
                foreach($data['shipToShoreTransfers'][$i]->newFiles as $file) {
?>
                        <li><small><?php echo $file; ?></small></li>
<?php
                }
            } else {
                for($j = 0; $j < 20; $j++) {
?>
                        <li><small><?php echo $data['shipToShoreTransfers'][$i]->newFiles[$j]; ?></small></li>
<?php
                }
?>
                        <li><small>...and <strong><?php echo sizeof($data['shipToShoreTransfers'][$i]->newFiles)-20; ?></strong> other files</small></li>
<?php
            }	
		
	    if(count($data['shipToShoreTransfers'][$i]->updatedFiles) > 0) {
?>
                        <li><small><?php echo count($data['shipToShoreTransfers'][$i]->updatedFiles); ?> File(s) Updated.</small></li>
<?php
            }
?>
                    </ul>
<?php
            $itemNum++;
        }
?>
                
<?php
    } else {
?>
                    <h5>No Recent Ship-to-Shore Transfers Have Occured</h5>   
<?php
    }
?>
                </div>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">Collection System Transfer Status</div>
                <div class="panel-body">
                    <div class="list-group" id="collectionSystemTransferStatusList">
<?php
    if($data['collectionSystemTransfers']){
        foreach($data['collectionSystemTransfers'] as $row){
            if($row->enable === "1"){
                switch($row->status) {
                    case 1:
?>
                    <div class="list-group-item list-group-item-success"><?php echo $row->longName; ?><span class="pull-right"><i class="fa fa-download"></i> Running</span></div>
 <?php
                        break;
                    case 2:
?>
                    <div class="list-group-item list-group-item-warning"><?php echo $row->longName; ?><span class="pull-right"><i class="fa fa-moon-o"></i> Idle</span></div>
 <?php
                        break;
                    case 3:
?>
                    <div class="list-group-item list-group-item-danger"><?php echo $row->longName; ?><span class="pull-right"><i class="fa fa-warning"></i> Error</span></div>
 <?php
                        break;
                    case 4:
?>
                    <div class="list-group-item disabled"><?php echo $row->longName; ?><span class="pull-right"><i class="fa fa-times"></i> Disabled</span></div>
 <?php
                        break;
                }
            }
        }
    }
?>
                    </div>
                </div>
            </div>
            <div class="panel panel-default">
                <div class="panel-heading">Cruise Data Transfer Status</div>
                <div class="panel-body">
                    <div class="list-group" id="requiredCruiseDataTransfers">
<?php
    if($data['requiredCruiseDataTransfers']){
        foreach($data['requiredCruiseDataTransfers'] as $row){
            switch($row->status){
                case 1:
?>
                            <div class="list-group-item list-group-item-success"><?php echo $row->longName; ?><span class="pull-right"><i class="fa fa-upload"></i> Running</span></div>
 <?php
                    break;
                case 2:
?>
                            <div class="list-group-item list-group-item-warning"><?php echo $row->longName; ?><span class="pull-right"><i class="fa fa-moon-o"></i> Idle</span></div>
 <?php
                    break;
                case 3:
?>
                            <div class="list-group-item list-group-item-danger"><?php echo $row->longName; ?><span class="pull-right"><i class="fa fa-warning"></i> Error</span></div>
 <?php
                    break;
                case 4:
?>
                            <div class="list-group-item disabled"><?php echo $row->longName; ?><span class="pull-right"><i class="fa fa-times"></i> Disabled</span></div>
 <?php
                    break;
            }
        }
    }
?>
                    </div>
                    <div class="list-group" id="optionalCruiseDataTransfers">
<?php
    if($data['cruiseDataTransfers']){
        foreach($data['cruiseDataTransfers'] as $row){
             if($row->enable === "1"){
                switch($row->status){
                    case 1:
?>
                            <div class="list-group-item list-group-item-success"><?php echo $row->longName; ?><span class="pull-right"><i class="fa fa-upload"></i> Running</span></div>
 <?php
                    break;
                    case 2:
?>
                            <div class="list-group-item list-group-item-warning"><?php echo $row->longName; ?><span class="pull-right"><i class="fa fa-moon-o"></i> Idle</span></div>
 <?php
                    break;
                    case 3:
?>
                            <div class="list-group-item list-group-item-danger"><?php echo $row->longName; ?><span class="pull-right"><i class="fa fa-warning"></i> Error</span></div>
 <?php
                    break;
                    case 4:
?>
                            <div class="list-group-item disabled"><?php echo $row->longName; ?><span class="pull-right"><i class="fa fa-times"></i> Disabled</span></div>
 <?php
                    break;
                }
             }
        }
    }
?>

                    </div>
                </div>
            </div>
        </div>
    </div>
