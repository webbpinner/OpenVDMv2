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
                    <li class=""><a id="shipToShoreTransfers" href="<?php echo DIR; ?>config/shipToShoreTransfers">Ship-to-Shore Transfers</a></li>
                    <li class="active"><a id="system" href="<?php echo DIR; ?>config/system">System</a></li>
                </ul>
            </div>
        </div>
    </div>
    <div class="row">
        <div class="col-md-6">
            <table class='table table-striped table-hover table-bordered responsive'>
                <tr>
                    <th>Name</th>
                    <th>Action</th>
                </tr>
<?php
    if($data['users']){
        foreach($data['users'] as $row){
?>
                <tr>
                    <td><?php echo $row->username; ?></td>
                    <td>
                        <a href='<?php echo DIR; ?>config/users/edit/<?php echo $row->userID; ?>'>Edit</a>
<?php
            if (strcmp(Session::get('userID'), $row->userID) !== 0 ) {
?>
                        / 
                        <a href='#confirmDeleteModal' data-toggle="modal" data-item-name="User" data-delete-url="<?php echo DIR; ?>config/users/delete/<?php echo $row->userID; ?>">Delete</a>
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
            <a class="btn btn-sm btn-primary" href="<?php echo DIR; ?>config/users/add">Add New User</a>
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