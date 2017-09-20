<?php

use Core\Error;
use Helpers\Form;

?>

    <div class="row">
        <div class="col-lg-12">
            <?php echo Error::display($error); ?>
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
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">Create New Lowering</div>
                <div class="panel-body">
                    <?php echo Form::open(array('role'=>'form', 'method'=>'post')); ?>
                        <div class="row">
                            <div class="col-lg-12">
                                <div class="form-group">
                                    <label>Lowering ID</label><?php echo Form::input(array('class'=>'form-control', 'type'=>'text', 'name'=>'loweringID', 'value'=>$data['loweringID'])); ?>
                                </div>
                                <label>Lowering Start Date/Time</label>
                                <div class="form-group">
                                    <div class="input-group date datetimepickerToday">
                                        <?php echo Form::input(array('class'=>'form-control', 'type'=>'text', 'name'=>'loweringStartDate', 'value'=>$data['loweringStartDate'])); ?>
                                        <span class="input-group-addon"><i class="fa fa-calendar"></i></span>
                                    </div>
                                </div>
                                <label>Lowering End Date/Time</label>
                                <div class="form-group">
                                    <div class="input-group date datetimepicker">
                                        <?php echo Form::input(array('class'=>'form-control', 'type'=>'text', 'name'=>'loweringEndDate', 'value'=>$data['loweringEndDate'])); ?>
                                        <span class="input-group-addon"><i class="fa fa-calendar"></i></span>
                                    </div>
                                </div>
                                <label>Collection Systems</label>
                                <table class='table table-striped table-hover table-bordered responsive'>
                                    <tr>
                                        <th>Name</th>
                                        <th style='width:20px;'>Enabled</th>
                                    </tr>
<?php
    if($data['collectionSystemTransfers']){
        foreach($data['collectionSystemTransfers'] as $row){
?>
                                    <tr>
                                        <td><?php echo $row->longName; echo ($row->status === "3"? '<span class="pull-right"><i class="fa fa-warning text-danger"></i></span>': ''); ?></td>
                                        <td style='text-align:center'>
<?php
            if($row->enable === "0"){
                echo '                                            ' . Form::submit(array('name'=>'enableCS' . $row->collectionSystemTransferID, 'class'=>'btn btn-xs btn-primary btn-danger', 'value'=>'Off'));
            } else {
                echo '                                            ' . Form::submit(array('name'=>'disableCS' . $row->collectionSystemTransferID, 'class'=>'btn btn-xs btn-primary btn-success', 'value'=>'On'));
            }
?>
                                        </td>
                                    </tr>
<?php
        }
    }
?>
                                </table>                                
                                <?php echo Form::submit(array('name'=>'submit', 'class'=>'btn btn-primary', 'value'=>'Create')); ?>
                                <a href="<?php echo DIR; ?>config" class="btn btn-danger">Cancel</a>
                            </div>
                        </div>    
                    <?php echo Form::close(); ?>
                </div>
            </div>
        </div>
        <div class="col-lg-6">
            <h3>Page Guide</h3>
            <p>This page is for creating a new loweringID and associated lowering data directory.  This page is NOT for configuring OpenVDM to use a previously created loweringID.  If you are trying to configure OpenVDM to use a previously created loweringID click <a href="<?php echo DIR; ?>config/editLowering">here</a>.</p>
            <p>The <strong>Lowering ID</strong> is the unique indentifier for the lowering (i.e. CS-001)</p>
            <p>The <strong>Lowering Start Date/Time </strong> is the designated start date/time of the lowering. This date/time is exported as part of the lowering finialization process and optionally used for identifying old data files that should be skipped during file transfers.  The required format of this date is mm/dd/yyyy hh:mm (i.e. 05/12/2015 00:00).</p>
            <p>The <strong>Collection Systems</strong> table is for specifying what collection system will be used during the lowering.  These can always be changed later from the Collection System Transfers tab.</p>
            <p>Click the <strong>Create</strong> button to save the change and exit back to the main configuration page.  If you enter a loweringID for a lowering that already exists you will be asked to enter a different loweringID.</p>
            <p>Click the <strong>Cancel</strong> button to exit back to the main configuration page without creating a new lowering.</p>
        </div>
    </div>