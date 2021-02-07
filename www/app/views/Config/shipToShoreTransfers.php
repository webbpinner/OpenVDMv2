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
                    <li class=""><a id="main" href="<?php echo DIR; ?>config">Main</a></li>
                    <li class=""><a id="collectionSystemTransfers" href="<?php echo DIR; ?>config/collectionSystemTransfers">Collection System Transfers</a></li>
                    <li class=""><a id="extraDirectories" href="<?php echo DIR; ?>config/extraDirectories">Extra Directories</a></li>
                    <li class=""><a id="cruiseDataTransfers" href="<?php echo DIR; ?>config/cruiseDataTransfers">Cruise Data Transfers</a></li>
                    <li class="active"><a id="shipToShoreTransfers" href="<?php echo DIR; ?>config/shipToShoreTransfers">Ship-to-Shore Transfers</a></li>
                    <li class=""><a id="system" href="<?php echo DIR; ?>config/system">System</a></li>
                </ul>
            </div>
        </div>
    </div>
    <div class="row">
        <div class="col-lg-7 col-md-12">
            <?php
    if(strcmp($data['ssdwEnable'],"1") === 0) {
?>
            <a href="<?php echo DIR; ?>config/shipToShoreTransfers/disableShipToShoreTransfers" class="btn-lg btn btn-danger btn-block">Disable Ship-to-Shore Transfers</a>
<?php
    } else {
?>
            <a href="<?php echo DIR; ?>config/shipToShoreTransfers/enableShipToShoreTransfers" class="btn-lg btn btn-success btn-block">Enable Ship-to-Shore Transfers</a>
<?php
    }
?>
            <br><br>
            <table class='table table-striped table-hover table-bordered responsive'>
                <tr>
                    <th>Transfer Name</th>
                    <th>Action</th>
                    <th style='width:20px;'>Enabled</th>
                </tr>
<?php
    if($data['shipToShoreTransfers']){
        foreach($data['shipToShoreTransfers'] as $row){
?>
                <tr>
                    <td><?php echo $row->longName; ?></td>
                    <td>
                        <a href='<?php echo DIR; ?>config/shipToShoreTransfers/edit/<?php echo $row->shipToShoreTransferID; ?>'>Edit</a> / 
                        <a href='#confirmDeleteModal' data-toggle="modal" data-item-name="Ship-to-Shore Transfer" data-delete-url="<?php echo DIR; ?>config/shipToShoreTransfers/delete/<?php echo $row->shipToShoreTransferID; ?>">Delete</a>
                    </td>
                    <td style='text-align:center'>
<?php
            if($row->enable == "0"){
?>
                        <a class="btn btn-xs btn-danger" href='<?php echo DIR; ?>config/shipToShoreTransfers/enable/<?php echo $row->shipToShoreTransferID; ?>'>Off</a>
<?php
            } else {
?>
                        <a class="btn btn-xs btn-success" href='<?php echo DIR; ?>config/shipToShoreTransfers/disable/<?php echo $row->shipToShoreTransferID; ?>'>On</a>
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
            <a class="btn btn-sm btn-primary" href="<?php echo DIR; ?>config/shipToShoreTransfers/add">Add New Ship-to-Shore Transfer</a>
            <span class="pull-right">
<?php
    if(strcmp($data['ssdwStatus'], "1") === 0) {
?>
            <a id="runStop" class="btn btn-sm btn-danger" href="<?php echo DIR; ?>config/shipToShoreTransfers/stop">Stop Ship-to-Shore Transfer</a>
<?php
    } else {
?>   
            <a id="runStop" class="btn btn-sm btn-success" href="<?php echo DIR; ?>config/shipToShoreTransfers/run">Run Ship-to-Shore Transfer</a>
<?php        
    }
?>
            </span>
        </div>
        <div class="col-lg-5 col-md-12">
            <h3>Page Guide</h3>
            <p>This page is for managing ship-to-shore transfers between the Shipboard Data Warehouse and the Shoreside Data Warehouse. A Ship-to-Shore Transfers specifies subsets of the cruise data directory that should be queued for transfer.</p>
            <p>Clicking an <strong class="text-primary">Edit</strong> link will redirect you to the corresponding "Edit Ship-to-Shore Transfer Form" where you can modify the Ship-to-Shore Transfer.</p>
            <p>Clicking a <strong class="text-primary">Delete</strong> link will permanently delete the corresponding Ship-to-Shore Transfer. There is a confirmation window so don't worry about accidental clicks.</p>
            <p>The button in the <strong>Enabled</strong> Column shows whether a Ship-to-Shore Transfer will be performed.  Click the button in the enable column to toggle the enable status of the cooresponding Ship-to-Shore Transfer.</p>
            <p>Click the <strong>Add New Ship-to-Shore Transfer</strong> button to add a new Ship-to-Shore Transfer.</p>
            <p>Click the <strong>Run Ship-to-Shore Transfer</strong> button to manually trigger the Ship-to-Shore Transfer.  If a Ship-to-Shore transfer is already in-progress this button will not be present.</p>
            <p>Click the <strong>Stop Ship-to-Shore Transfer</strong> button to manually stop a Ship-to-Shore Transfer that is already in-progress.  If a Ship-to-Shore transfer is not already in-progress this button will not be present.</p>
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