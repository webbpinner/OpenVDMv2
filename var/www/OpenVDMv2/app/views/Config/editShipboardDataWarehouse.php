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
                <div class="panel-heading">Edit Shipboard Data Warehouse</div>
                <div class="panel-body">
                    <?php echo Form::open(array('role'=>'form', 'method'=>'post')); ?>
                        <div class="row">
                            <div class="col-lg-12">
                                <div class="form-group">
                                    <label>Server IP</label><?php echo Form::input(array('class'=>'form-control', 'type'=>'text', 'name'=>'shipboardDataWarehouseIP', 'value'=>$data['shipboardDataWarehouseConfig']['shipboardDataWarehouseIP'])); ?>
                                </div>
                                <div class="form-group">
                                    <label>Cruise Data Directory</label><?php echo Form::input(array('class'=>'form-control', 'type'=>'text', 'name'=>'shipboardDataWarehouseBaseDir', 'value'=>$data['shipboardDataWarehouseConfig']['shipboardDataWarehouseBaseDir'])); ?>
                                </div>
                                <div class="form-group">
                                    <label>Server Username</label><?php echo Form::input(array('class'=>'form-control', 'type'=>'text', 'name'=>'shipboardDataWarehouseUsername', 'value'=>$data['shipboardDataWarehouseConfig']['shipboardDataWarehouseUsername'])); ?>
                                </div>
                                <div class="form-group">
                                    <label>Public Data Directory</label><?php echo Form::input(array('class'=>'form-control', 'type'=>'text', 'name'=>'shipboardDataWarehousePublicDataDir', 'value'=>$data['shipboardDataWarehouseConfig']['shipboardDataWarehousePublicDataDir'])); ?>
                                </div>

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
            <p>This form is for editing settings related to the Shipboard Data Warehouse (SBDW). The Shipboard Data Warehouse hosts the OpenVDM data management tools, the OpenVDM (this) web-interface and stores the cruise data.</p>
            <p>The <strong>Server IP</strong> is the IP address of the Shipboard Data Warehouse (i.e. "192.168.4.151").</p>
            <p>The <strong>Cruise Data Directory</strong> is the location of the parent directory to the Cruise Data Directories on the SBDW (i.e. "/mnt/vault/FTPRoot/CruiseData").</p>
            <p>The <strong>Server Username</strong> is the username on the SBDW with read/write permission to the files/folders in the Cruise Data Directories (i.e. "shipTech").</p>
            <p>The <strong>Public Data Directory</strong> is the location of the PublicData directory on the SBDW. (i.e. "/mnt/vault/FTPRoot/PublicData").</p>
            <p>Click the <strong>Update</strong> button to submit the changes to OpenVDM.  Click the <strong>Cancel</strong> button to exit this form.</p>
        </div>
    </div>