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
                    <li class=""><a id="collectionSystemTransfers" href="#collectionSystemTransfers" data-toggle="tab">Collection System Transfers</a></li>
                    <li class=""><a id="extraDirectories" href="#extraDirectories" data-toggle="tab">Extra Directories</a></li>
                    <li class="active"><a id="cruiseDataTransfers" href="#cruiseDataTransfers" data-toggle="tab">Cruise Data Transfers</a></li>
                    <li class=""><a id="shipToShoreTransfers" href="#shipToShoreTransfers" data-toggle="tab">Ship-to-Shore Transfers</a></li>
                    <li class=""><a id="system" href="#system" data-toggle="tab">System</a></li>
                </ul>
            </div>
        </div>
    </div>


    <div class="row">
        <div class="col-lg-7 col-md-12">
            <table class='table table-striped table-hover table-bordered responsive'>
                <tr>
                    <th>Name</th>
                    <th>Action</th>
                    <th style='width:20px;'>Enabled</th>
                </tr>
<?php
    if($data['cruiseDataTransfers']){
        foreach($data['cruiseDataTransfers'] as $row){
?>
                <tr>
                    <td><?php echo $row->longName; ?></td>
                    <td>
                        <a href='<?php echo DIR; ?>config/cruiseDataTransfers/edit/<?php echo $row->cruiseDataTransferID; ?>'>Edit</a> / 
                        <a href='#confirmDeleteModal' data-toggle="modal" data-item-name="Cruise Data Transfer" data-delete-url="<?php echo DIR; ?>config/cruiseDataTransfers/delete/<?php echo $row->cruiseDataTransferID; ?>">Delete</a> / 
                        <a href='<?php echo DIR; ?>config/cruiseDataTransfers/test/<?php echo $row->cruiseDataTransferID; ?>'>Test</a> / 
<?php
            if($row->status === "1"){
?>
                        <a id="runStop<?php echo $row->cruiseDataTransferID ?>" href='<?php echo DIR; ?>config/cruiseDataTransfers/stop/<?php echo $row->cruiseDataTransferID; ?>'>Stop</a>
 <?php
            } else {
?>
                        <a id="runStop<?php echo $row->cruiseDataTransferID ?>" href='<?php echo DIR; ?>config/cruiseDataTransfers/run/<?php echo $row->cruiseDataTransferID; ?>'>Run</a>
                        <span id="testFail<?php echo $row->cruiseDataTransferID ?>" class="pull-right">
<?php
            }
            if($row->status === "3") {
?>
                            <i class="fa fa-warning text-danger"></i>
<?php
            }
?>
                        </span>
                    </td>
                    <td style='text-align:center'>
<?php
            if($row->enable == "0"){
?>
                        <a class="btn btn-xs btn-danger" href='<?php echo DIR; ?>config/cruiseDataTransfers/enable/<?php echo $row->cruiseDataTransferID; ?>'>Off</a>
<?php
            } else {
?>
                        <a class="btn btn-xs btn-success" href='<?php echo DIR; ?>config/cruiseDataTransfers/disable/<?php echo $row->cruiseDataTransferID; ?>'>On</a>
<?php
            }
?>
                    </td>
                </tr>
<?php

        }
    }
?>
            </table>
            <a class="btn btn-sm btn-primary" href="<?php echo DIR; ?>config/cruiseDataTransfers/add">Add New Cruise Data Transfer</a>
        </div>
        <div class="col-lg-5 col-md-12">
            <h3>Page Guide</h3>
            <p>This page is for managing Cruise Data Transfers.  A Cruise Data Transfer is an OpenVDM-managed copy of all collected data from the current cruise data directory on the Shipboard Data Warehouse to a remote server, NAS box or external HDD connected to the Shipboard Data Warehouse.</p>
            <p>Clicking an <strong class="text-primary">Edit</strong> link will redirect you to the corresponding "Edit Cruise Data Transfer Form" where you can modify the Cruise Data Transfer settings.</p>
            <p>Clicking a <strong class="text-primary">Delete</strong> link will permanently delete the corresponding Collection System Transfer. There is a confirmation window so don't worry about accidental clicks.</p>
            <p>Clicking a <strong class="text-primary">Test</strong> link will verify the corresponding Cruise Data Transfer configuration is valid. A window will appear displaying the test results.  If there is a <i class="fa fa-warning text-danger"></i> in a row, the corresponding Cruise Data Transfer has encountered and error.  Click <strong class="text-primary">Test</strong> to diagnose the problem.</p>
            <p>Clicking a <strong class="text-primary">Run</strong> link will manually trigger the corresponding Cruise Data Transfer to start.  If the Cruise Data Transfer is currently running, this link is not present</p>
            <p>Clicking a <strong class="text-primary">Stop</strong> link will manually trigger the corresponding Cruise Data Transfer to stop immediately.  If the Cruise Data Transfer is not currently running, this link is not present</p>
            <p>The button in the <strong>Enabled</strong> Column shows whether the transfer is enabled.  Click the button in the enable column to toggle the enable status of the cooresponding Cruise Data Transfer.</p>
            <p>Click the <strong>Add New Cruise Data Transfer</strong> button to add a new Cruise Data Transfer.</p>
        </div>
    </div>

<div class="modal fade" id="confirmDeleteModal" tabindex="-1" role="dialog" aria-labelledby="Delete Confirmation" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                <h4 class="modal-title" id="myModalLabel">Delete Confirmation</h4>
            </div>
            <div class="modal-body">Are you sure you want to delete this <span id="modelDeleteItemName"></span>?  This cannot be undone!</div>
            <div class="modal-footer">
                <a href='' class="btn btn-danger" data-dismiss="modal">Cancel</a>
                <a href='doesnotexist' class="btn btn-primary" id="modalDeleteLink">Yup!</a>
            </div>
        </div> <!-- /.modal-content -->
    </div> <!-- /.modal-dialog -->
</div> <!-- /.modal -->
<?php
    if($data['testResults']) {
?>
<div class="modal fade" id="testResultsModal" tabindex="-1" role="dialog" aria-labelledby="Test Results" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                <h4 class="modal-title" id="myModalLabel">Test Results for <?php echo $data['testCruiseDataTransferName'] ?></h4>
            </div>
            <div class="modal-body">
                <ui class="list-unstyled">
<?php
    for($i=0; $i<(sizeof($data['testResults']))-1; $i++){
?>
                    <li><i class="fa fa-<?php echo (strcmp($data['testResults'][$i]->result, "Pass") ? "times text-danger" : "check text-success"); ?>"></i> <?php echo $data['testResults'][$i]->testName; ?></li>
<?php
    }
?>
                    <li><strong><i class="fa fa-<?php echo (strcmp($data['testResults'][sizeof($data['testResults'])-1]->result, "Pass") ? "times text-danger" : "check text-success"); ?>"></i> <?php echo $data['testResults'][sizeof($data['testResults'])-1]->testName; ?></strong></li>
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