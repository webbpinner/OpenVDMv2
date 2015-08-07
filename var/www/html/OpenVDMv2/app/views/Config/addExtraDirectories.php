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
                    <li class="active"><a id="extraDirectories" href="#extraDirectories" data-toggle="tab">Extra Directories</a></li>
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
                <div class="panel-heading">Add new Extra Directory</div>
                <div class="panel-body">
                    <?php echo Form::open( array('role'=>'form', 'method'=>'post')); ?>
                        <div class="row">
                            <div class="col-lg-12">
                                <div class="form-group"><label>Name</label><?php echo Form::input(array('class'=>'form-control', 'name'=>'name', 'value'=>$_POST['name'])); ?></div>
                                <div class="form-group"><label>Long Name</label><?php echo Form::input(array('class'=>'form-control', 'name'=>'longName', 'value'=>$_POST['longName'])); ?></div>
                                <div class="form-group"><label>Destination Directory</label><?php echo Form::input(array('class'=>'form-control', 'name'=>'destDir', 'value'=>$_POST['destDir'])); ?></div>
                            </div>
                        </div>
                        <div class="row">    
                            <div class="col-lg-12">
                                <?php echo Form::submit(array('name'=>'submit', 'class'=>'btn btn-primary', 'value'=>'Add')); ?>
                                <a href="<?php echo DIR; ?>config/extraDirectories" class="btn btn-danger">Cancel</a>
                            </div>
                        </div>    
                    <?php echo Form::close(); ?>
                </div>
            </div>
        </div>
        <div class="col-lg-6">
            <h3>Page Guide</h3>
            <p>This page is for editing an extra directory in the cruise data directory.  Extra directories are for holding files that can not be automatically transferred into the cruise data directory via Collection System Transfers.</p>
            <p>The <strong>Name</strong> field is a short name for the Collection System Transfer (i.e. Products).  These names should NOT have spaces in them.</p>
            <p>The <strong>Long Name</strong> field is a longer name for the Collection System Transfer (i.e. Cruise Products ).  These names can have spaces in them.</p>
            <p>The <strong>Destination Directory</strong> is where the data will be stored within the cruise data directory.  This can be a parent directory (i.e. Products) or a sub-directory (i.e. EM302/Products).  If a sub-directory is desired use the UNIX-style directory notation '/'.</p>
            <p>Click the <strong>Add</strong> button to submit the extra directory to OpenVDM.  Click the <strong>Cancel</strong> button to exit this form.</p>
        </div>
    </div>
