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
                <div class="panel-heading">Create New Cruise</div>
                <div class="panel-body">
                    <?php echo Form::open(array('role'=>'form', 'method'=>'post')); ?>
                        <div class="row">
                            <div class="col-lg-12">
                                <div class="form-group">
                                    <label>Cruise ID</label><?php echo Form::input(array('class'=>'form-control', 'type'=>'text', 'name'=>'cruiseID', 'value'=>$data['cruiseID'])); ?>
                                </div>
                                <label>Cruise Start Date/Time</label>
                                <div class="form-group">
                                    <div class="input-group date datetimepickerToday">
                                        <?php echo Form::input(array('class'=>'form-control', 'type'=>'text', 'name'=>'cruiseStartDate', 'value'=>$data['cruiseStartDate'])); ?>
                                        <span class="input-group-addon"><i class="fa fa-calendar"></i></span>
                                    </div>
                                </div>
                                <label>Cruise End Date/Time</label>
                                <div class="form-group">
                                    <div class="input-group date datetimepicker">
                                        <?php echo Form::input(array('class'=>'form-control', 'type'=>'text', 'name'=>'cruiseEndDate', 'value'=>$data['cruiseEndDate'])); ?>
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
                                <label>Other Options</label>
                                <table class='table table-striped table-hover table-bordered responsive'>
                                    <tr>
                                        <th>Name</th>
                                        <th style='width:20px;'>Enabled</th>
                                    </tr>
                                    <tr>
                                        <td>Show Lowering Components</td><td style='width:20px; text-align:center'><?php echo $data['showLoweringComponents'] === True ? Form::submit(array('name'=>'hideLoweringComponents', 'class'=>'btn btn-xs btn-success', 'value'=>'On')): Form::submit(array('name'=>'showLoweringComponents', 'class'=>'btn btn-xs btn-danger', 'value'=>'Off')); ?></td>
                                    </tr>
                                    <tr>
                                        <td>Ship-to-Shore Transfers</td><td style='width:20px; text-align:center'><?php echo $data['shipToShoreTransfersEnable'] === '1' ? Form::submit(array('name'=>'disableSSDW', 'class'=>'btn btn-xs btn-success', 'value'=>'On')): Form::submit(array('name'=>'enableSSDW', 'class'=>'btn btn-xs btn-danger', 'value'=>'Off')); ?></td>
                                    </tr>
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
            <p>This page is for creating a new cruiseID and associated cruise data directory.  This page is NOT for configuring OpenVDM to use a previously created cruiseID.  If you are trying to configure OpenVDM to use a previously created cruiseID click <a href="<?php echo DIR; ?>config/editCruise">here</a>.</p>
            <p>The <strong>Cruise ID</strong> is the unique indentifier for the cruise (i.e. CS1501)</p>
            <p>The <strong>Cruise Start Date/Time </strong> is the designated start date/time of the cruise. This date/time is exported as part of the cruise finialization process and optionally used for identifying old data files that should be skipped during file transfers.  The required format of this date is mm/dd/yyyy hh:mm (i.e. 05/12/2015 00:00).</p>
            <p>The <strong>Collection Systems</strong> table is for specifying what collection system will be used during the cruise.  These can always be changed later from the Collection System Transfers tab.</p>
            <p>Click the <strong>Create</strong> button to save the change and exit back to the main configuration page.  If you enter a cruiseID for a cruise that already exists you will be asked to enter a different cruiseID.</p>
            <p>Click the <strong>Cancel</strong> button to exit back to the main configuration page without creating a new cruise.</p>
        </div>
    </div>