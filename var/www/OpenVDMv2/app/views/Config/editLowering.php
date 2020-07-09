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
                <div class="panel-heading">Edit Current <?php echo LOWERING_NAME ?></div>
                <div class="panel-body">
                    <?php echo Form::open(array('role'=>'form', 'method'=>'post')); ?>
                        <div class="row">
                            <div class="col-lg-12">
                                <div class="form-group">
                                    <label><?php echo LOWERING_NAME ?> ID</label>
<?php
    if(is_array($data['lowerings']) && sizeof($data['lowerings']) > 0) {
?>
                                    <select name="loweringID" class="form-control">
<?php
        for($i=0;$i<sizeof($data['lowerings']); $i++){
?>
                                        <option value="<?php echo $data['lowerings'][$i]; ?>"<?php echo ' ' . ($data['loweringID'] == $data['lowerings'][$i] ? 'selected':'');?>><?php echo $data['lowerings'][$i]; ?></option>
<?php
        }
    } else {
?>
                                    <select name="loweringID" class="form-control disabled">
                                        <option>No <?php echo LOWERING_NAME ?>s Available</option>
<?php
    }
?>
                                    </select>
                                </div>
                                <label><?php echo LOWERING_NAME ?> Start Date/Time</label>
                                <div class="form-group">
                                    <div id="loweringStartDate", class="input-group date datetimepicker">
                                        <?php echo Form::input(array('class'=>'form-control', 'type'=>'text', 'name'=>'loweringStartDate', 'value'=>$data['loweringStartDate'])); ?>
                                        <span class="input-group-addon"><i class="fa fa-calendar"></i></span>
                                    </div>
                                </div>
                                <label><?php echo LOWERING_NAME ?> End Date/Time</label>
                                <div class="form-group">
                                    <div  id="loweringEndDate", class="input-group date datetimepicker">
                                        <?php echo Form::input(array('class'=>'form-control', 'type'=>'text', 'name'=>'loweringEndDate', 'value'=>$data['loweringEndDate'])); ?>
                                        <span class="input-group-addon"><i class="fa fa-calendar"></i></span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-lg-12">
                                <?php echo Form::submit(array('name'=>'submit', 'class'=>'btn btn-primary', 'value'=>'Update')); ?>
                                <a href="<?php echo DIR; ?>config" class="btn btn-danger">Cancel</a>
                            </div>
                        </div>    
                    <?php echo Form::close(); ?>
                </div>
            </div>
        </div>
        <div class="col-lg-6">
            <h3>Page Guide</h3>
            <p>This page is for configuring OpenVDM to use a previously created <?php echo LOWERING_NAME ?>ID.  This page is NOT for creating a new <?php echo LOWERING_NAME ?>ID (and associated <?php echo LOWERING_NAME ?> data directory).  If you are trying to create a new <?php echo LOWERING_NAME ?>ID (and <?php echo LOWERING_NAME ?> data directory) click <a href="<?php echo DIR; ?>config/setupNewLowering">here</a>.</p>
            <p>The <strong><?php echo LOWERING_NAME ?> ID</strong> is the unique indentifier for the <?php echo LOWERING_NAME ?> (i.e. CS1501)</p>
            <p>The <strong><?php echo LOWERING_NAME ?> Start Date </strong> is the designated start date of the <?php echo LOWERING_NAME ?>. This date is exported as part of the <?php echo LOWERING_NAME ?> finialization process and optionally used for identifying old data files that should be skipped during file transfers.  The required format of this date is yyyy/mm/dd HH:MM (i.e. 2018/01/01 00:00).</p>
            <p>Click the <strong>Update</strong> button to save the change and exit back to the main configuration page.  If you enter a <?php echo LOWERING_NAME ?>ID for a <?php echo LOWERING_NAME ?> that does not exist you will be asked to enter a different <?php echo LOWERING_NAME ?>ID.</p>
            <p>Click the <strong>Cancel</strong> button to revert back to the previous <?php echo LOWERING_NAME ?>ID and exit back to the main configuration page.</p>
        </div>
    </div>
