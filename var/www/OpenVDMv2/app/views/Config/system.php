<?php

use Core\Error;
use Helpers\Session;

$testFailSSDW = '';
foreach($data['requiredCruiseDataTransfers'] as $row){
    if (strcmp($row->name, "SSDW") === 0) {
        if (strcmp($row->status, "3") === 0) {
            $testFailSSDW = '<i class="fa fa-warning text-danger"></i>';
        }
        break;
    }
}

$testFailSBDW = '';
if (strcmp($data['shipboardDataWarehouseStatus'], "3") === 0) {
    $testFailSBDW = '<i class="fa fa-warning text-danger"></i>';
}


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
                    <li class=""><a id="main" href="<?php echo DIR; ?>config">Main</a></li>
                    <li class=""><a id="collectionSystemTransfers" href="<?php echo DIR; ?>config/collectionSystemTransfers">Collection System Transfers</a></li>
                    <li class=""><a id="extraDirectories" href="<?php echo DIR; ?>config/extraDirectories">Extra Directories</a></li>
                    <li class=""><a id="cruiseDataTransfers" href="<?php echo DIR; ?>config/cruiseDataTransfers">Cruise Data Transfers</a></li>
                    <li class=""><a id="shipToShoreTransfers" href="<?php echo DIR; ?>config/shipToShoreTransfers">Ship-to-Shore Transfers</a></li>
                    <li class="active"><a id="system" href="<?php echo DIR; ?>config/system">System</a></li>
                </ul>
            </div>
        </div>
    </div>
    <div class="row">
        <div class="col-lg-7 col-md-12">
            <table class='table table-striped table-hover table-bordered responsive'>
                <tr>
                    <th>System Behaviors</th>
                    <th>Action</th>
                    <th style='width:20px;'>Enabled</th>
                </tr>
                
                <tr>
                    <td>Ship-to-Shore Transfer Bandwidth Limit: <strong><?php echo (strcmp($data['shipToShoreBWLimit'], '0') === 0 ? 'Unlimited' : $data['shipToShoreBWLimit'] . ' Kbps'); ?></strong></td>
                    <td><a href='<?php echo DIR; ?>config/system/editShipToShoreBWLimit'>Edit</a></td>
                    <td style='text-align:center'>
<?php
            if(strcmp($data['shipToShoreBWLimitStatus'], 'On') === 0){
?>
                        <a class="btn btn-xs btn-success" href='<?php echo DIR; ?>config/system/disableShipToShoreBWLimit'>On</a>
<?php
            } else {
?>
                        <a class="btn btn-xs btn-danger" href='<?php echo DIR; ?>config/system/enableShipToShoreBWLimit'>Off</a>
<?php
            }
?>
                    </td>
                </tr>

                <tr>
                    <td>Data Filesize Limit for MD5 Checksum: <strong><?php echo (strcmp($data['md5FilesizeLimit'], '0') === 0 ? 'Unlimited' : $data['md5FilesizeLimit'] . ' MB'); ?></strong></td>
                    <td><a href='<?php echo DIR; ?>config/system/editMD5FilesizeLimit'>Edit</a></td>
                    <td style='text-align:center'>
<?php
            if(strcmp($data['md5FilesizeLimitStatus'], 'On') === 0){
?>
                        <a class="btn btn-xs btn-success" href='<?php echo DIR; ?>config/system/disableMD5FilesizeLimit'>On</a>
<?php
            } else {
?>
                        <a class="btn btn-xs btn-danger" href='<?php echo DIR; ?>config/system/enableMD5FilesizeLimit'>Off</a>
<?php
            }
?>
                    </td>
                </tr>

            </table>
            <table class='table table-striped table-hover table-bordered responsive'>
                <tr>
                    <th>Sidebar Links<a class="pull-right btn btn-xs btn-primary" href="<?php echo DIR; ?>config/system/addLink">Add New Link</a></th>
                    <th style='width:200px;'>Action</th>
                    <th style='width:20px;'>Private</th>
                    <th style='width:20px;'>Enabled</th>
                </tr>                

<?php
    if($data['links']){
        foreach($data['links'] as $row){
?>
                <tr>
                    <td><?php echo $row->name; ?></td>
                    <td>
                        <a href='<?php echo $row->url; ?>' target='_blank'>Open</a> /
                        <a href='<?php echo DIR; ?>config/system/editLink/<?php echo $row->linkID; ?>'>Edit</a> /
                        <a href='#confirmDeleteModal' data-toggle='modal' data-item-name='Link' data-delete-url='<?php echo DIR; ?>config/system/deleteLink/<?php echo $row->linkID; ?>'>Delete</a>
                    </td>
                    <td style='text-align:center'>
<?php
            if($row->private == "0"){
?>
                        <a class="btn btn-xs btn-danger" href='<?php echo DIR; ?>config/system/privateLink/<?php echo $row->linkID; ?>'>No</a>
<?php
            } else {
?>
                        <a class="btn btn-xs btn-success" href='<?php echo DIR; ?>config/system/publicLink/<?php echo $row->linkID; ?>'>Yes</a>
<?php
            }
?>
                    </td>
                    <td style='text-align:center'>
<?php
            if($row->enable == "0"){
?>
                        <a class="btn btn-xs btn-danger" href='<?php echo DIR; ?>config/system/enableLink/<?php echo $row->linkID; ?>'>Off</a>
<?php
            } else {
?>
                        <a class="btn btn-xs btn-success" href='<?php echo DIR; ?>config/system/disableLink/<?php echo $row->linkID; ?>'>On</a>
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
            <table class='table table-striped table-hover table-bordered responsive'>
                <tr>
                    <th>OpenVDM Specific Ship-to-Shore Transfers</th>
                    <th>Action</th>
                    <th style='width:20px;'>Enabled</th>
                </tr>           

<?php
    if($data['requiredShipToShoreTransfers']){
        foreach($data['requiredShipToShoreTransfers'] as $row){
?>
                <tr>
                    <td><?php echo $row->longName; ?></td>
                    <td>
                        <a href='<?php echo DIR; ?>config/system/editShipToShoreTransfers/<?php echo $row->shipToShoreTransferID; ?>'>Edit</a>
                    </td>
                    <td style='text-align:center'>
<?php
            if($row->enable == "0"){
?>
                        <a class="btn btn-xs btn-danger" href='<?php echo DIR; ?>config/system/enableShipToShoreTransfers/<?php echo $row->shipToShoreTransferID; ?>'>Off</a>
<?php
            } else {
?>
                        <a class="btn btn-xs btn-success" href='<?php echo DIR; ?>config/system/disableShipToShoreTransfers/<?php echo $row->shipToShoreTransferID; ?>'>On</a>
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
            <table class='table table-striped table-hover table-bordered responsive'>
                <tr>
                    <th>OpenVDM Required Directories</th>
                    <th>Action</th>
                </tr>
<?php
    if($data['requiredExtraDirectories']){
        foreach($data['requiredExtraDirectories'] as $row){
?>
                <tr>
                    <td><?php echo $row->longName; ?></td>
                    <td>
                        <a href='<?php echo DIR; ?>config/system/editExtraDirectories/<?php echo $row->extraDirectoryID; ?>'>Edit</a>
                    </td>
                </tr>
<?php
        }
    }
?>
            </table>
            <table class='table table-striped table-hover table-bordered responsive'>
                <tr>
                    <th>Data Warehouses</th>
                    <th>Action</th>
                </tr>
                <tr>
                    <td>Shipboard Data Warehouse (SBDW)</td>
                    <td>
                        <a href="<?php echo DIR ?>config/system/editShipboardDataWarehouse">Edit</a> / 
                        <a href="<?php echo DIR ?>config/system/testShipboardDataWarehouse">Test</a>
                        <span class="pull-right" id="testFailSBDW"><?php echo $testFailSBDW; ?></span>
                    </td>
                </tr>
                <tr>
                    <td>Shoreside Data Warehouse (SSDW)</td>
                    <td>
                        <a href="<?php echo DIR ?>config/system/editShoresideDataWarehouse">Edit</a> / 
                        <a href="<?php echo DIR ?>config/system/testShoresideDataWarehouse">Test</a>
                        <span class="pull-right" id="testFailSSDW"><?php echo $testFailSSDW; ?></span>
                    </td>
                </tr>
            </table>
        </div>
        <div class="col-lg-5 col-md-12">
            <h3>Page Guide</h3>
            <p>This page is for managing OpenVDM specific items.  These items cannot be deleted.</p>
            <p>The <strong>System Behaviors</strong> table is for setting variables used in vairous OpenVDM programs.  Click the cooresponding <strong class="text-primary">Edit</strong> link to modify the value.  For all of these variables there is a default value.  Click the cooresponding <strong>Enable</strong> button to either use of the set value or ignore the set value and use the system default.</p>
            <p>The <strong>Sidebar Links</strong> table is for managing the links listed in the Links section of the sidebar navigation. Click the cooresponding <strong class="text-primary">Open</strong> link to open the link in a new tab (same as clicking the link in the sidebar).
            Click the cooresponding <strong class="text-primary">Edit</strong> link to edit the name and/or URL of the link.
            Click the cooresponding <strong class="text-primary">Delete</strong> link to permanently delete the link.
            Use the button in the <strong>Private</strong> column to make the link appear for only authenticated visitors ("Yes") or all visitors ("No").        
            Use the button in the <strong>Enable</strong> column to enable/disable which will show/hide the cooresponding link.
            <p>The <strong>OpenVDM Specific Ship-to-Shore Transfers</strong> table is for managing Ship-to-Shore Transfers of data generated by OpenVDM such as the Dashboard Data and RSS Feeds. Click the cooresponding <strong class="text-primary">Edit</strong> link to change the behaviors of these transfers.  Use the button in the <strong>Enable</strong> column to enable/disable the cooresponding transfer.</p>
            <p>The <strong>OpenVDM Requried Directories</strong> table is for managing locations of directories within the cruise data directory that are required by OpenVDM. Click the cooresponding <strong class="text-primary">Edit</strong> link to change these locations.</p>
            <p>The <strong>Data Warehouses</strong> table is for managing the Shipboard Data Warehouse and the Shoreside Data Warehouse.  Click <strong class="text-primary">Edit</strong> to view/modify the warehouse's settings.  Click <strong class="text-primary">Test</strong> to verify the corresponding Data Warehouse configuration is valid. A window will appear displaying the test results.  If there is a <i class="fa fa-warning text-danger"></i> in a row, there is an error with the corresponding Data Warehouse configuration.  Click <strong class="text-primary">Test</strong> to diagnose the problem.</p>
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
                <h4 class="modal-title" id="myModalLabel">Test Results for <?php echo $data['testWarehouseName'] ?></h4>
            </div>
            <div class="modal-body">
                <ui class="list-unstyled">
<?php
    for($i=0; $i<(sizeof($data['testResults']['parts']))-1; $i++){
?>
                    <li><i class="fa fa-<?php echo (strcmp($data['testResults']['parts'][$i]['result'], "Pass") ? "times text-danger" : "check text-success"); ?>"></i> <?php echo $data['testResults']['parts'][$i]['testName']; ?></li>
<?php
    }
?>
                    <li><strong><i class="fa fa-<?php echo (strcmp($data['testResults']['parts'][sizeof($data['testResults']['parts'])-1]['result'], "Pass") ? "times text-danger" : "check text-success"); ?>"></i> <?php echo $data['testResults']['parts'][sizeof($data['testResults']['parts'])-1]['testName']; ?></strong></li>
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