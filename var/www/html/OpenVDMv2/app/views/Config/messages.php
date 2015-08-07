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
        <div class="col-lg-8">
            <div class="panel panel-default">
                <div class="panel-heading">Manage Messages</div>
                <div class="panel-body">
<?php
    if($data['messages']){
?>
                    <table class='table table-striped table-hover table-bordered responsive'>
                        <tr>
                            <th style='width:40px'>Delete</th>
                            <th>Message</th>
                            <th>Timestamp (UTC)</th>
                        </tr>
<?php
        foreach($data['messages'] as $row){
?>
                        <tr>
                            <td style='text-align:center'>
                                <a href="<?php echo DIR; ?>config/messages/deleteMessage/<?php echo $row->messageID; ?>"><i class="fa fa-times text-danger"></i></a>
                            </td>
                            <td>
<?php
            if($row->messageViewed == 0) {
?>
                                <a href="<?php echo DIR; ?>config/messages/viewedMessage/<?php echo $row->messageID; ?>"><strong><?php echo $row->message; ?></strong></a>
<?php
            } else {
?>
                        <?php echo $row->message; ?>
<?php
            }
?>
                            </td>
                            <td>
<?php
            if($row->messageViewed == 0) {
?>
                                <a href="<?php echo DIR; ?>config/messages/viewedMessage/<?php echo $row->messageID; ?>"><strong><?php echo $row->messageTS; ?></strong></a>
<?php
            } else {
?>
                        <?php echo $row->messageTS; ?>
<?php
            }
?>
                            </td>
                        </tr>
<?php
        }
?>
                    </table>
                    <?php echo $data['page_links']; ?>
                    <span class="pull-right">
                        <a class="btn btn-danger", href='#confirmDeleteModal' data-toggle="modal" data-item-name="ALL the Messages" data-delete-url="<?php echo DIR; ?>config/messages/deleteAllMessages">Delete all messages</a>
                        <a class="btn btn-primary", href="<?php echo DIR; ?>config/messages/viewAllMessages">Mark all messages as read</a>
                    </span>
<?php
    } else {
?>
                    <span>No Messages found.</span>
<?php
    }
?>
                </div>
            </div>
        </div>
    </div>

<div class="modal fade" id="confirmDeleteModal" tabindex="-1" role="dialog">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                <h4 class="modal-title" id="myModalLabel">Delete Confirmation</h4>
            </div>
            <div class="modal-body">Are you sure you want to delete <span id="modelDeleteItemName"></span>?  This cannot be undone!</div>
            <div class="modal-footer">
                <a href='' class="btn btn-danger" data-dismiss="modal">Cancel</a>
                <a href='doesnotexist' class="btn btn-primary" id="modalDeleteLink">Yup!</a>
            </div>
        </div> <!-- /.modal-content -->
    </div> <!-- /.modal-dialog -->
</div> <!-- /.modal -->