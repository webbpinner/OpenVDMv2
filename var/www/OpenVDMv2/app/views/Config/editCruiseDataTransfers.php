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
                    <li class="active"><a id="cruiseDataTransfers" href="#cruiseDataTransfers" data-toggle="tab">Cruise Data Transfers</a></li>
                    <li class=""><a id="shipToShoreTransfers" href="#shipToShoreTransfers" data-toggle="tab">Ship-to-Shore Transfers</a></li>
                    <li class=""><a id="system" href="#system" data-toggle="tab">System</a></li>
                </ul>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">Edit Cruise Data Transfer</div>
                <div class="panel-body">
                    <?php echo Form::open( array('role'=>'form', 'method'=>'post')); ?>
                        <div class="row">
                            <div class="col-lg-12">
                                <div class="form-group"><label>Name</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'name', 'value'=> $data['row'][0]->name)); ?></div>
                                <div class="form-group"><label>Long Name</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'longName', 'value'=> $data['row'][0]->longName)); ?></div>
                                <div class="form-group">
                                    <label>Transfer Type</label><?php echo Form::radioInline($data['transferTypeOptions'], $data['row'][0]->transferType); ?>
                                </div>
                                <div class="form-group"><label>Destination Directory</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'destDir', 'value'=> $data['row'][0]->destDir)); ?></div>
                                <div class="form-group rsyncServer"><label>Rsync Server</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'rsyncServer', 'value'=> $data['row'][0]->rsyncServer)); ?></div>
                                <div class="form-group rsyncServer"><label>Rsync username</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'rsyncUser', 'value'=> $data['row'][0]->rsyncUser)); ?></div>
                                <div class="form-group rsyncServer"><label>Rsync password</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'rsyncPass', 'type'=>'password', 'value'=> $data['row'][0]->rsyncPass)); ?></div>
                                <div class="form-group smbShare"><label>SMB Server/Share</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'smbServer', 'value'=> $data['row'][0]->smbServer)); ?></div>
                                <div class="form-group smbShare"><label>SMB Domain</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'smbDomain', 'value'=> $data['row'][0]->smbDomain)); ?></div>
                                <div class="form-group smbShare"><label>SMB Username</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'smbUser', 'value'=> $data['row'][0]->smbUser)); ?></div>
                                <div class="form-group smbShare"><label>SMB Password</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'smbPass', 'type'=>'password', 'value'=> $data['row'][0]->smbPass)); ?></div>
                                <div class="form-group sshServer"><label>SSH Server</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'sshServer', 'value'=> $data['row'][0]->sshServer)); ?></div>
                                <div class="form-group sshServer"><label>SSH Username</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'sshUser', 'value'=> $data['row'][0]->sshUser)); ?></div>
                                <div class="form-group sshServer"><label>SSH Password</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'sshPass', 'type'=>'password', 'value'=> $data['row'][0]->sshPass)); ?></div>
                                <div class="form-group nfsShare"><label>NFS Server/Share</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'nfsServer', 'value'=> $data['row'][0]->nfsServer)); ?></div>
                                <div class="form-group nfsShare"><label>NFS Username</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'nfsUser', 'value'=> $data['row'][0]->nfsUser)); ?></div>
                                <div class="form-group nfsShare"><label>NFS Password</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'nfsPass', 'type'=>'password', 'value'=> $data['row'][0]->nfsPass)); ?></div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-lg-12">
                                <?php echo Form::submit( array('name'=>'submit', 'class'=>'btn btn-primary', 'value'=>'Update')); ?>
                                <a href="<?php echo DIR; ?>config/cruiseDataTransfers" class="btn btn-danger">Cancel</a>
                                <?php echo Form::submit( array( 'name'=>'inlineTest', 'class'=>'btn btn-primary pull-right', 'value'=>'Test Setup')); ?>
                            </div>
                        </div>
                    <?php echo Form::close(); ?>
                </div>
            </div>
        </div>
        <div class="col-lg-6">
            <h3>Page Guide</h3>
            <p>This form is for editing an existing Cruise Data Transfer to OpenVDM. A Cruise Data Transfer is an OpenVDM-managed copy of all collected data from the current cruise data directory on the Shipboard Data Warehouse to a remote server, NAS box or external HDD connected to the Shipboard Data Warehouse.</p>
            <p>The <strong>Name</strong> field is a short name for the Cruise Data Transfer (i.e. "ChiefSciHDD").  These names should NOT have spaces in them.</p>
            <p>The <strong>Long Name</strong> field is a longer name for the Cruise Data Transfer (i.e. "Chief Scientist USB HDD" ).  These names can have spaces in them.</p>
            <p>The <strong>Transfer Type</strong> defines how OpenVDM will transfer the data from the cruise data directory on the Data Warehouse to the desired destination.  <strong>Local Directory</strong> is a transfer of the cruise data to another location on the Data Warehouse but outside of the Cruise Data Directory (i.e USB hard drive).  <strong>Rsync Server</strong> is a transfer of cruise data to a destination system running Rsync and SSH servers. <strong>SMB Share</strong> is a transfer of cruise data to a destination system with a SMB (Windows) Share (i.e. a NAS box).</p>
            <p>The <strong>Destination Directory</strong> is the directory within the destination location where the cruise data will be copied to.</p>
            <p class="rsyncServer">The <strong>Rsync Server</strong> is the IP address of the Destination System (i.e. "192.168.4.151").</p>
            <p class="rsyncServer">The <strong>Rsync Username</strong> is the SSH username with permission to access the data on the Destination System (i.e. "shipTech").</p>
            <p class="rsyncServer">The <strong>Rsync Password</strong> is the SSH password for the Rsync Username.</p>
            <p class="smbShare">The <strong>SMB Server/Share</strong> is the SMB Server/Share of the Destination System (i.e. "//192.168.4.151/data").</p>
            <p class="smbShare">The <strong>SMB Domain</strong> is the SMB Server/Share Domain of the Destination System (i.e. "WORKGROUP").  If no value is defined this field will default to "WORKGROUP".</p>
            <p class="smbShare">The <strong>SMB Username</strong> is the SMB username with permission to access the data on the Destination System (i.e. "shipTech").</p>
            <p class="smbShare">The <strong>SMB Password</strong> is the SMB password for the SMB Username.</p>
            <p class="sshServer">The <strong>SSH Server</strong> is the IP address of the Destination SSH Server (i.e. "192.168.4.151").</p>
            <p class="sshServer">The <strong>SSH Username</strong> is the SSH username with permission to access the data on the Destination SSH Server (i.e. "shipTech").</p>
            <p class="sshServer">The <strong>SSH Password</strong> is the SSH password for the Rsync Username.</p>
            <p class="nfsShare">The <strong>NFS Server/Share</strong> is the IP address of the Destination NFS Server (i.e. "192.168.4.151").</p>
            <p class="nfsShare">The <strong>NFS Username</strong> is the NFS username with permission to access the data on the Destination NFS Server (i.e. "shipTech").</p>
            <p class="nfsShare">The <strong>NFS Password</strong> is the NFS password for the NFS Username.</p>
            <p>Click the <strong>Update</strong> button to submit the changes to OpenVDM.  Click the <strong>Cancel</strong> button to exit this form.  Click the <strong>Test Setup</strong> button to test the configuration currently in the form.  This DOES NOT save the configuration.  You will need to click the <strong>Update</strong> button to commit the changes.</p>
        </div>
    </div>
<?php
    if($data['testResults']) {
?>
<div class="modal fade" id="testResultsModal" tabindex="-1" role="dialog" aria-labelledby="Test Results" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                <h4 class="modal-title" id="myModalLabel">Test Results for <?php echo $data['testCruiseDataTransferName'] ?></h4>
            </div>
            <div class="modal-body">
                <ui class="list-unstyled">
<?php
    for($i=0; $i<(sizeof($data['testResults']))-1; $i++){
?>
                    <li><i class="fa fa-<?php echo (strcmp($data['testResults'][$i]->result, "Pass") ? "times text-danger" : "check text-success"); ?>"></i> <?php echo $data['testResults'][$i]->testName; ?></li>
<?php
    }
?>
                    <li><strong><i class="fa fa-<?php echo (strcmp($data['testResults'][sizeof($data['testResults'])-1]->result, "Pass") ? "times text-danger" : "check text-success"); ?>"></i> <?php echo $data['testResults'][sizeof($data['testResults'])-1]->testName; ?></strong></li>
                </ui>
            </div>
            <div class="modal-footer">
                <a href='' class="btn btn-primary" data-dismiss="modal">Close</a>
            </div>
        </div> <!-- /.modal-content -->
    </div> <!-- /.modal-dialog -->
</div> <!-- /.modal -->
<?php
    }
?>
