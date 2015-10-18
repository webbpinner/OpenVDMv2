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
                    <li class="active"><a id="main" href="#main" data-toggle="tab">Main</a></li>
                    <li class=""><a id="collectionSystemTransfers" href="#collectionSystemTransfers" data-toggle="tab">Collection System Transfers</a></li>
                    <li class=""><a id="extraDirectories" href="#extraDirectories" data-toggle="tab">Extra Directories</a></li>
                    <li class=""><a id="cruiseDataTransfers" href="#cruiseDataTransfers" data-toggle="tab">Cruise Data Transfers</a></li>
                    <li class=""><a id="shipToShoreTransfers" href="#shipToShoreTransfers" data-toggle="tab">Ship-to-Shore Transfers</a></li>
                    <li class=""><a id="system" href="#system" data-toggle="tab">System</a></li>
                </ul>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">Edit CruiseID</div>
                <div class="panel-body">
                    <?php echo Form::open(array('role'=>'form', 'method'=>'post')); ?>
                        <div class="row">
                            <div class="col-lg-12">
                                <div class="form-group">
                                    <label>Cruise ID</label><?php echo Form::input(array('class'=>'form-control', 'type'=>'text', 'name'=>'cruiseID', 'value'=>$data['cruiseID'])); ?>
                                </div>
                                <label>Cruise Start Date</label>
                                <div class="form-group input-group">
                                    <?php echo Form::input(array('class'=>'form-control datepicker', 'type'=>'text', 'name'=>'cruiseStartDate', 'value'=>$data['cruiseStartDate'])); ?><span class="input-group-addon"><i class="fa fa-calendar"></i></span>
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
            <p>This page is for configuring OpenVDM to use a previously created cruiseID.  This page is NOT for creating a new cruiseID (and associated cruise data directory).  If you are trying to create a new cruiseID (and cruise data directory) click <a href="<?php echo DIR; ?>config/setupNewCruise">here</a>.</p>
            <p>The <strong>Cruise ID</strong> is the unique indentifier for the cruise (i.e. CS1501)</p>
            <p>The <strong>Cruise Start Date </strong> is the designated start date of the cruise. This date is exported as part of the cruise finialization process and optionally used for identifying old data files that should be skipped during file transfers.  The required format of this date is mm/dd/yyyy (i.e. 05/12/2015).</p>
            <p>Click the <strong>Update</strong> button to save the change and exit back to the main configuration page.  If you enter a cruiseID for a cruise that does not exist you will be asked to enter a different cruiseID.</p>
            <p>Click the <strong>Cancel</strong> button to revert back to the previous cruiseID and exit back to the main configuration page.</p>
        </div>
    </div>