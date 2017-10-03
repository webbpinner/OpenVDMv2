<?php

use Core\Error;
use Helpers\Form;
use Helpers\FormCustom;

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
                    <li class="active"><a id="cruiseDataTransfers" href="<?php echo DIR; ?>config/cruiseDataTransfers">Cruise Data Transfers</a></li>
                    <li class=""><a id="shipToShoreTransfers" href="<?php echo DIR; ?>config/shipToShoreTransfers">Ship-to-Shore Transfers</a></li>
                    <li class=""><a id="system" href="<?php echo DIR; ?>config/system">System</a></li>
                </ul>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col-lg-6 col-md-7">
            <div class="panel panel-default">
                <div class="panel-heading">Edit Cruise Data Transfer</div>
                <div class="panel-body">
                    <?php echo Form::open( array('role'=>'form', 'method'=>'post')); ?>
                        <div class="row">
                            <div class="col-lg-12">
                                <div class="form-group"><label>Name</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'name', 'value'=> $data['row'][0]->name)); ?></div>
                                <div class="form-group"><label>Long Name</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'longName', 'value'=> $data['row'][0]->longName)); ?></div>
                                <div class="form-group"><label>Include OpenVDM generated files?</label><?php echo FormCustom::radioInline($data['includeOVDMFilesOptions'], $data['row'][0]->includeOVDMFiles); ?></div>
                                <div class="form-group"><label>Transfer bandwidth limit (in kB/s): <?php echo Form::input( array('name'=>'bandwidthLimit', 'value'=> $data['row'][0]->bandwidthLimit, 'size'=>'7', 'length'=>'8')); ?></label></div>
                                <div class="form-group"><label>Transfer Type</label><?php echo FormCustom::radioInline($data['transferTypeOptions'], $data['row'][0]->transferType); ?></div>
                                <div class="form-group"><label>Destination Directory</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'destDir', 'value'=> $data['row'][0]->destDir)); ?></div>
                                <div class="form-group localDir"><label>Destination Directory is mountpoint?</label><?php echo FormCustom::radioInline($data['useLocalMountPointOptions'], $data['row'][0]->localDirIsMountPoint); ?></div>
                                <div class="form-group rsyncServer"><label>Rsync Server</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'rsyncServer', 'value'=> $data['row'][0]->rsyncServer)); ?></div>
                                <div class="form-group rsyncServer"><label>Rsync username</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'rsyncUser', 'value'=> $data['row'][0]->rsyncUser)); ?></div>
                                <div class="form-group rsyncServer"><label>Rsync password</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'rsyncPass', 'type'=>'password', 'value'=> $data['row'][0]->rsyncPass)); ?></div>
                                <div class="form-group smbShare"><label>SMB Server/Share</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'smbServer', 'value'=> $data['row'][0]->smbServer)); ?></div>
                                <div class="form-group smbShare"><label>SMB Domain</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'smbDomain', 'value'=> $data['row'][0]->smbDomain)); ?></div>
                                <div class="form-group smbShare"><label>SMB Username</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'smbUser', 'value'=> $data['row'][0]->smbUser)); ?></div>
                                <div class="form-group smbShare"><label>SMB Password</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'smbPass', 'type'=>'password', 'value'=> $data['row'][0]->smbPass)); ?></div>
                                <div class="form-group sshServer"><label>SSH Server</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'sshServer', 'value'=> $data['row'][0]->sshServer)); ?></div>
                                <div class="form-group sshServer"><label>SSH Username</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'sshUser', 'value'=> $data['row'][0]->sshUser)); ?></div>
                                <div class="form-group sshServer"><label>Use SSH Public/Private key?</label><?php echo FormCustom::radioInline($data['useSSHKeyOptions'], $data['row'][0]->sshUseKey); ?></div>
                                <div class="form-group sshServer"><label>SSH Password</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'sshPass', 'type'=>'password', 'value'=> $data['row'][0]->sshPass)); ?></div>
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
        <div class="col-lg-6 col-md-5">
            <h3>Page Guide</h3>
            <p>This form is for editing an existing Cruise Data Transfer to OpenVDM. A Cruise Data Transfer is an OpenVDM-managed copy of all collected data from the current cruise data directory on the Shipboard Data Warehouse to a remote server, NAS box or external HDD connected to the Shipboard Data Warehouse.</p>
            <p>The <strong>Name</strong> field is a short name for the Cruise Data Transfer (i.e. "ChiefSciHDD").  These names should NOT have spaces in them.</p>
            <p>The <strong>Long Name</strong> field is a longer name for the Cruise Data Transfer (i.e. "Chief Scientist USB HDD" ).  These names can have spaces in them.</p>
            <p>The <strong>Include OVDM Files</strong> option is to specifiy wether the transfer should include files generated by OpenVDM such as the transfer logs, data dashboard datasets and the cruise configuration file.</p>
            <p>The <strong>Transfer bandwidth limit</strong> option will limit the amount of network bandwidth use for the cruise data transfer.  Setting this option to 0 or leaving it empty will removing any bandwidth restrictions</p>
            <p>The <strong>Transfer Type</strong> defines how OpenVDM will transfer the data from the cruise data directory on the Data Warehouse to the desired destination.  <strong>Local Directory</strong> is a transfer of the cruise data to another location on the Data Warehouse but outside of the Cruise Data Directory (i.e USB hard drive).  <strong>Rsync Server</strong> is a transfer of cruise data to a destination system running Rsync and SSH servers. <strong>SMB Share</strong> is a transfer of cruise data to a destination system with a SMB (Windows) Share (i.e. a NAS box).  <strong>SSH Server</strong> is a transfer of cruise data to a destination system via Secure Shell (SSH).</p>
            <p>The <strong>Destination Directory</strong> is the directory within the destination location where the cruise data will be copied to.</p>
            <p class="localDir">The <strong>Destination Directory is mountpoint</strong> specifies whether OpenVDM should confirm a device (external HDD) is connected at that location.</p>
            <p class="rsyncServer">The <strong>Rsync Server</strong> is the IP address of the Destination System (i.e. "192.168.4.151").</p>
            <p class="rsyncServer">The <strong>Rsync Username</strong> is the rsync username with permission to access the data on the Destination System (i.e. "shipTech").  If the rsync server allows anonymous access set this field to "anonymous" and no password will be required.</p>
            <p class="rsyncServer">The <strong>Rsync Password</strong> is the rsync password for the Rsync Username. Not required if Rsync Username is set to "anonymous".</p>
            <p class="smbShare">The <strong>SMB Server/Share</strong> is the SMB Server/Share of the Destination System (i.e. "//192.168.4.151/data").</p>
            <p class="smbShare">The <strong>SMB Domain</strong> is the SMB Server/Share Domain of the Destination System (i.e. "WORKGROUP").  If no value is defined this field will default to "WORKGROUP".</p>
            <p class="smbShare">The <strong>SMB Username</strong> is the SMB username with permission to access the data on the Destination System (i.e. "shipTech").  If the smb server allows guest access set this field to "guest" and no password will be required.</p>
            <p class="smbShare">The <strong>SMB Password</strong> is the SMB password for the SMB Username. Not required if SMB Username is set to "guest".</p>
            <p class="sshServer">The <strong>SSH Server</strong> is the IP address of the Destination SSH Server (i.e. "192.168.4.151").</p>
            <p class="sshServer">The <strong>SSH Username</strong> is the SSH username with permission to access the data on the Destination SSH Server (i.e. "shipTech").</p>
            <p class="sshServer">The <strong>Use SSH Public/Private key?</strong> instructs OpenVDM to authenticate this connection using SSH public/private keys instead of a password</p>
            <p class="sshServer">The <strong>SSH Password</strong> is the SSH password for the Rsync Username.</p>
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
    for($i=0; $i<(sizeof($data['testResults']['parts']))-1; $i++){
?>
                    <li><i class="fa fa-<?php echo (strcmp($data['testResults']['parts'][$i]['result'], "Pass") ? "times text-danger" : "check text-success"); ?>"></i> <?php echo $data['testResults']['parts'][$i]['testName']; ?></li>
<?php
    }
?>
                    <li><strong><i class="fa fa-<?php echo (strcmp($data['testResults']['parts'][sizeof($data['testResults']['parts'])-1]['result'], "Pass") ? "times text-danger" : "check text-success"); ?>"></i> <?php echo $data['testResults']['parts'][sizeof($data['testResults']['parts'])-1]['testName']; ?></strong></li>
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
