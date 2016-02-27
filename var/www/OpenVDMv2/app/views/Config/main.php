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
                    <li class="active"><a id="main" href="<?php echo DIR; ?>config">Main</a></li>
                    <li class=""><a id="collectionSystemTransfers" href="<?php echo DIR; ?>config/collectionSystemTransfers">Collection System Transfers</a></li>
                    <li class=""><a id="extraDirectories" href="<?php echo DIR; ?>config/extraDirectories">Extra Directories</a></li>
                    <li class=""><a id="cruiseDataTransfers" href="<?php echo DIR; ?>config/cruiseDataTransfers">Cruise Data Transfers</a></li>
                    <li class=""><a id="shipToShoreTransfers" href="<?php echo DIR; ?>config/shipToShoreTransfers">Ship-to-Shore Transfers</a></li>
                    <li class=""><a id="system" href="<?php echo DIR; ?>config/system">System</a></li>
                </ul>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col-lg-6 col-md-6">
            <div class="panel panel-default">
                <div class="panel-heading">Cruise Control</div>
                <div class="panel-body">
                    <a href="<?php echo DIR ?>config/setupNewCruise" class="btn-lg btn btn-primary btn-block">Setup New Cruise</a>
                    <a id="finalizeCurrentCruise" href="<?php echo DIR ?>config/finalizeCurrentCruise" class="btn-lg btn btn-primary btn-block">Run End-of-Cruise Tasks</a>
                    <a href="<?php echo DIR ?>config/editCruiseID" class="btn-lg btn btn-primary btn-block">Edit Current CruiseID/Start Date</a>
                </div>
            </div>
            <div class="panel panel-default">
                <div class="panel-heading">Maintenance Tasks</div>
                <div class="panel-body">
                    <div class="list-group" id="taskStatusList">
<?php
    if($data['tasks']){
        foreach($data['tasks'] as $row){
            if((strcmp($row->name, "setupNewCruise") != 0) && (strcmp($row->name, "finalizeCurrentCruise") != 0)) {
                switch($row->status) {
                    case 1:
?>
                        <div class="list-group-item"><?php echo $row->longName; ?><span class="pull-right btn btn-xs btn-primary btn-outline disabled">Wait</span></div>
 <?php
                        break;
                    case 2:
?>
                        <div class="list-group-item"><?php echo $row->longName; ?><a href="<?php echo DIR . 'config/' . $row->name; ?>" class="pull-right btn btn-xs btn-primary btn-outline">Run</a></div>
 <?php
                        break;
                    case 3:
?>
                        <div class="list-group-item"><?php echo $row->longName; ?><span class="pull-right"><i class="fa fa-warning text-danger"></i>&nbsp;&nbsp;<a href="<?php echo DIR . 'config/' . $row->name; ?>" class="btn btn-xs btn-primary btn-outline">Run</a></span></div>
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
        <div class="col-lg-6 col-md-6">
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
                    <div class="list-group-item list-group-item-success"><i class="fa fa-download"></i> <?php echo $row->longName; ?><span class="pull-right">Running</span></div>
 <?php
                        break;
                    case 2:
?>
                    <div class="list-group-item list-group-item-warning"><i class="fa fa-moon-o"></i> <?php echo $row->longName; ?><span class="pull-right">Idle</span></div>
 <?php
                        break;
                    case 3:
?>
                    <div class="list-group-item list-group-item-danger"><i class="fa fa-warning"></i> <?php echo $row->longName; ?><span class="pull-right">Error</span></div>
 <?php
                        break;
                    case 4:
?>
                    <div class="list-group-item disabled"><i class="fa fa-times"></i> <?php echo $row->longName; ?><span class="pull-right">Disabled</span></div>
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
             switch($row->status) {
                 case 1:
?>
                            <div class="list-group-item list-group-item-success"><i class="fa fa-upload"></i> <?php echo $row->longName; ?><span class="pull-right">Running</span></div>
 <?php
                    break;
                 case 2:
?>
                            <div class="list-group-item list-group-item-warning"><i class="fa fa-moon-o"></i> <?php echo $row->longName; ?><span class="pull-right">Idle</span></div>
 <?php
                    break;
                 case 3:
?>
                            <div class="list-group-item list-group-item-danger"><i class="fa fa-warning"></i> <?php echo $row->longName; ?><span class="pull-right">Error</span></div>
 <?php
                    break;
                 case 4:
?>
                            <div class="list-group-item disabled"><i class="fa fa-times"></i> <?php echo $row->longName; ?><span class="pull-right">Disabled</span></div>
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
                switch($row->status) {
                    case 1:
?>
                            <div class="list-group-item list-group-item-success"><i class="fa fa-upload"></i> <?php echo $row->longName; ?><span class="pull-right">Running</span></div>
 <?php
                        break;
                    case 2:
?>
                            <div class="list-group-item list-group-item-warning"><i class="fa fa-moon-o"></i> <?php echo $row->longName; ?><span class="pull-right">Idle</span></div>
 <?php
                        break;
                    case 3:
?>
                            <div class="list-group-item list-group-item-danger"><i class="fa fa-warning"></i> <?php echo $row->longName; ?><span class="pull-right">Error</span></div>
 <?php
                        break;
                    case 4:
?>
                            <div class="list-group-item disabled"><i class="fa fa-times"></i> <?php echo $row->longName; ?><span class="pull-right">Disabled</span></div>
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
<?php
    if($data['jobResults']) {
?>
<div class="modal fade" id="jobResultsModal" tabindex="-1" role="dialog">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                <h4 class="modal-title" id="myModalLabel">Job Results for <?php echo $data['jobName'] ?></h4>
            </div>
            <div class="modal-body">
                <ui class="list-unstyled">
<?php
    for($i=0; $i<(sizeof($data['jobResults']->parts)); $i++){
?>
                    <li><i class="fa fa-<?php echo (strcmp($data['jobResults']->parts[$i]->result, "Pass") ? "times text-danger" : "check text-success"); ?>"></i> <?php echo $data['jobResults']->parts[$i]->partName; ?></li>
<?php
    }
?>
                </ui>
            </div>
            <div class="modal-footer">
                <a href='' class="btn btn-primary" data-dismiss="modal">Close</a>
            </div>
        </div> <!-- /.modal-content -->
    </div> <!-- /.modal-dialog -->
</div> <!-- /.modal -->
<?php
    }
?>