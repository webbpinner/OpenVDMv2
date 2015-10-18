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
                    <li class=""><a id="main" href="#main" data-toggle="tab">Main</a></li>
                    <li class=""><a id="collectionSystemTransfers" href="#collectionSystemTransfers" data-toggle="tab">Collection System Transfers</a></li>
                    <li class=""><a id="extraDirectories" href="#extraDirectories" data-toggle="tab">Extra Directories</a></li>
                    <li class=""><a id="cruiseDataTransfers" href="#cruiseDataTransfers" data-toggle="tab">Cruise Data Transfers</a></li>
                    <li class="active"><a id="shipToShoreTransfers" href="#shipToShoreTransfers" data-toggle="tab">Ship-to-Shore Transfers</a></li>
                    <li class=""><a id="system" href="#system" data-toggle="tab">System</a></li>
                </ul>
            </div>
        </div>
    </div>    <div class="row">
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">Edit Ship-to-Shore Transfer</div>
                <div class="panel-body">
                    <?php echo Form::open(array('role'=>'form', 'method'=>'post')); ?>
                        <div class="row">
                            <div class="col-lg-12">
                                <div class="form-group"><label>Name</label><?php echo Form::input(array('class'=>'form-control', 'name'=>'name', 'value'=>$data['row'][0]->name)); ?></div>
                                <div class="form-group"><label>Long Name</label><?php echo Form::input(array('class'=>'form-control', 'name'=>'longName', 'value'=>$data['row'][0]->longName)); ?></div>
                                <div class="form-group">
                                    <label>Priority</label><?php echo Form::radioInline($data['transferPriorityOptions'], $data['row'][0]->priority); ?>
                                </div>
                                <div class="form-group"><label>Collection System</label><?php echo Form::select($data['collectionSystemOptions']); ?></div>
                                <div class="form-group"><label>Extra Directory</label><?php echo Form::select($data['extraDirectoryOptions']); ?></div>
                                <div class="form-group"><label>Include Filter</label><?php echo Form::textbox(array('class'=>'form-control', 'name'=>'includeFilter', 'rows'=>'3', 'value'=>$data['row'][0]->includeFilter)); ?></div>
                                <?php echo Form::submit(array('name'=>'submit', 'class'=>'btn btn-primary', 'value'=>'Update')); ?>
                                <a href="<?php echo DIR; ?>config/shipToShoreTransfers" class="btn btn-danger">Cancel</a>
                            </div>
                        </div>
                    <?php echo Form::close(); ?>
                </div>
            </div>
        </div>
        <div class="col-lg-6">
            <h3>Page Guide</h3>
            <p>This form is for editing an existing Ship-to-Shore Transfer within OpenVDM. A Ship-to-Shore Transfers specifies subsets of the cruise data directory that should be queued for transfer to the Shoreside Data Warehouse (SSDW).</p>
            <p>The <strong>Name</strong> field is a short name for the Ship-to-Shore Transfer (i.e. KML_Tracklines).  These names should NOT have spaces in them.</p>
            <p>The <strong>Long Name</strong> field is a longer name for the Ship-to-Shore Transfer (i.e. Google KML Tracklines ).  These names can have spaces in them.</p>
            <p>The <strong>Priority</strong> defines the order in which files are transferred to the SSDW.  The lower the priority number the greater importance placed on the files for transferring them to the SSDW during a Ship-to-Shore transfer (i.e. the most important files to transfer should have a priority of 1).</p>
            <p>The <strong>Collection System</strong> dropdown defines the collection system directory within the cruise data directory to transfer files from. Similarly the <strong>Extra Directory</strong> dropdown defines the extra directory within the cruise data directory to transfer files from. A Ship-to-Shore Transfer must have a Collection System and/or Extra Directory selected.</p>
            <p>The <strong>Include Filter</strong> is used to specify which files from the selected Collection System and/or Extra Directory to transfer.  If no filter is specified, OpenVDM will attempt to transfer all the files in the selected Collection System and/or Extra Directory.  The filter uses the standard regex structure language (i.e. *.Raw).  Use a single space to deliminate between filters when multiple include filters are required (i.e. *.Raw *.txt).</p>
            <p>Click the <strong>Update</strong> button to submit the changes to OpenVDM.  Click the <strong>Cancel</strong> button to exit this form.</p>
        </div>
    </div>
