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
                    <li class="active"><a id="extraDirectories" href="<?php echo DIR; ?>config/extraDirectories">Extra Directories</a></li>
                    <li class=""><a id="cruiseDataTransfers" href="<?php echo DIR; ?>config/cruiseDataTransfers">Cruise Data Transfers</a></li>
                    <li class=""><a id="shipToShoreTransfers" href="<?php echo DIR; ?>config/shipToShoreTransfers">Ship-to-Shore Transfers</a></li>
                    <li class=""><a id="system" href="<?php echo DIR; ?>config/system">System</a></li>
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
    if($data['extraDirectories']){
        foreach($data['extraDirectories'] as $row){
?>
                <tr>
                    <td><?php echo $row->longName; ?></td>
                    <td>
                        <a href='<?php echo DIR; ?>config/extraDirectories/edit/<?php echo $row->extraDirectoryID; ?>'>Edit</a>
                        /
                        <a href='#confirmDeleteModal' data-toggle="modal" data-item-name="Extra Directory" data-delete-url="<?php echo DIR; ?>config/extraDirectories/delete/<?php echo $row->extraDirectoryID; ?>">Delete</a>
                    </td>
                    <td style='text-align:center'>
<?php
            if($row->enable == "0"){
?>
                        <a class="btn btn-xs btn-danger" href='<?php echo DIR; ?>config/extraDirectories/enable/<?php echo $row->extraDirectoryID; ?>'>Off</a>
<?php
            } else {
?>
                        <a class="btn btn-xs btn-success" href='<?php echo DIR; ?>config/extraDirectories/disable/<?php echo $row->extraDirectoryID; ?>'>On</a>
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
            <a class="btn btn-sm btn-primary" href="<?php echo DIR; ?>config/extraDirectories/add">Add New Extra Directory</a>
        </div>
        <div class="col-lg-5 col-md-12">
            <h3>Page Guide</h3>
            <p>This page is for managing extra directories in the cruise data directory.  Extra directories are for holding files that can not be automatically transferred into the cruise data directory via Collection System Transfers.</p>
            <p>Examples for having Extra Directories include storing data from collection systems that cannot be connected to via SMB or SSH/Rsync, or storing manually-created data products such as maps, and storing manually-created reports/summaries.</p>
            <p>Clicking an <strong class="text-primary">Edit</strong> link will redirect you to the corresponding "Edit Extra Directory Form" where you can modify the Extra Directory name and location.</p>
            <p>Clicking a <strong class="text-primary">Delete</strong> link will permanently delete the corresponding Extra Directory. There is a confirmation window so don't worry about accidental clicks.</p>
            <p>The button in the <strong>Enabled</strong> column shows whether the directory will be created within the cruise data directory for the current cruise.  Click the button to toggle the enable/disable the cooresponding Extra Directory.  In accordance with OpenVDM data integrity policies, disabling an extra directory will not delete an existing directory.  The directly will simply not be created with in the cruise data directoy when a new cruise is initialized.</p>
            <p>Click the <strong>Add New Extra Directory</strong> button to add a new Extra Directory.</p>
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