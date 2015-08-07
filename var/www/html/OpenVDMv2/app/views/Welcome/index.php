<?php

use Core\Error;
use Helpers\Session;

$transferLogNum = 5;

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
    if($data['filenameErrors']) {
?>
<?php
        foreach($data['filenameErrors'] as $row) {
?>
                    <h5><?php echo $row->collectionSystemName; ?> Filename Errors:</h5>
                    <ul>
<?php
            foreach($row->errorFiles as $file) {
?>
                        <li><small><?php echo $file; ?></small></li>
<?php
            }
?>
                    </ul>
<?php
        }
    } else {
?>
                    <h5>No Filename Errors Found</h5>               
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
    
        for($i = count($data['shipboardTransfers'])-1; $i >= 0; $i-- ) {
            if($itemNum >= $transferLogNum) {
                break;
            }
?>
                    <h5><?php echo $data['shipboardTransfers'][$i]->collectionSystemName; ?> - <?php $timestamp = DateTime::createFromFormat('Ymd\THis\Z', $data['shipboardTransfers'][$i]->date, new DateTimeZone('UTC')); echo $timestamp->format('Y-m-d H:i:s T'); ?></h5>
                    <ul>
<?php
            foreach($data['shipboardTransfers'][$i]->newFiles as $file) {
?>
                        <li><small><?php echo $file; ?></small></li>
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
        
        for($i = count($data['shipToShoreTransfers'])-1; $i >= 0; $i-- ) {
            if($itemNum >= $transferLogNum) {
                break;
            }
?>
                    <h5><?php echo $data['shipToShoreTransfers'][$i]->shipToShoreTransferName; ?> - <?php $timestamp = DateTime::createFromFormat('Ymd\THis\Z', $data['shipToShoreTransfers'][$i]->date, new DateTimeZone('UTC')); echo $timestamp->format('Y-m-d H:i:s T'); ?></h5>
                    <ul>
<?php
            foreach($data['shipToShoreTransfers'][$i]->newFiles as $file) {
?>
                        <li><small><?php echo $file; ?></small></li>
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
