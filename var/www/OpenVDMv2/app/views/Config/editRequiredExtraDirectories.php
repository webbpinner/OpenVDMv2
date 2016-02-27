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
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">Edit Extra Directory</div>
                <div class="panel-body">
                    <?php echo Form::open( array('role'=>'form', 'method'=>'post')); ?>
                        <div class="row">
                            <div class="col-lg-12">
                                <div class="form-group"><label>Name</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'name', 'value'=>$data['row'][0]->name, 'disabled'=>'disabled')); ?></div>
                                <div class="form-group"><label>Long Name</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'longName', 'value'=>$data['row'][0]->longName)); ?></div>
                                <div class="form-group"><label>Destination Directory</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'destDir', 'value'=>$data['row'][0]->destDir)); ?></div>
                            </div>
                        </div>
                        <div class="row">    
                            <div class="col-lg-12">
                                <?php echo Form::submit(array('name'=>'submit', 'class'=>'btn btn-primary', 'value'=>'Update')); ?>
                                <a href="<?php echo DIR; ?>config/system" class="btn btn-danger">Cancel</a>
                            </div>
                        </div>    
                    <?php echo Form::close(); ?>
                </div>
            </div>
        </div>
        <div class="col-lg-6">
            <h3>Page Guide</h3>
            <p>This form is for editing an OpenVDM-Specific Extra Directory. This extra directory within the cruise data directory is used by OpenVDM for storing OpenVDM-specific files.</p>
            <p>The <strong>Name</strong> field is a short name for the Extra Directory (i.e. KML_Tracklines).  This name cannot be changed because it is leveraged by the various parts of OpenVDM.</p>
            <p>The <strong>Long Name</strong> field is a longer name for the Directory (i.e. Google KML Tracklines ).  These names can have spaces in them.</p>
            <p>The <strong>Destination Directory</strong> is used to specify the extra directory name/location within the cruise data directory. This can be a parent directory (i.e. Products) or a sub-directory (i.e. EM302/Products).  If a sub-directory is desired use the UNIX-style directory notation '/'.</p>
            <p>Click the <strong>Update</strong> button to submit the changes to OpenVDM.  Click the <strong>Cancel</strong> button to exit this form.</p>
        </div>
    </div>
