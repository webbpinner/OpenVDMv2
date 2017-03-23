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
                    <li class="active"><a id="collectionSystemTransfers" href="<?php echo DIR; ?>config/collectionSystemTransfers">Collection System Transfers</a></li>
                    <li class=""><a id="extraDirectories" href="<?php echo DIR; ?>config/extraDirectories">Extra Directories</a></li>
                    <li class=""><a id="cruiseDataTransfers" href="<?php echo DIR; ?>config/cruiseDataTransfers">Cruise Data Transfers</a></li>
                    <li class=""><a id="shipToShoreTransfers" href="<?php echo DIR; ?>config/shipToShoreTransfers">Ship-to-Shore Transfers</a></li>
                    <li class=""><a id="system" href="<?php echo DIR; ?>config/system">System</a></li>
                </ul>
            </div>
        </div>
    </div>

    <div class="row">
        <div class="col-lg-6 col-md-7">
            <div class="panel panel-default">
                <div class="panel-heading">Add new Collection System Transfer</div>
                <div class="panel-body">
                    <?php echo Form::open( array('role'=>'form', 'method'=>'post', 'files')); ?>
                        <div class="row">
                            <div class="col-lg-12">
                                <div class="form-group"><label>Name</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'name', 'value'=> $_POST['name']));?></div>
                                <div class="form-group"><label>Long Name</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'longName', 'value'=> $_POST['longName'])); ?></div>
                                <div class="form-group"><label>Destination Directory</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'destDir', 'value'=> $_POST['destDir'])); ?></div>
                                <div class="form-group"><label>Include Filter</label><?php echo Form::textbox( array('class'=>'form-control', 'rows'=>'3', 'name'=>'includeFilter', 'value'=> $_POST['includeFilter'])); ?></div>
                                <div class="form-group"><label>Exclude Filter</label><?php echo Form::textbox( array('class'=>'form-control', 'rows'=>'3', 'name'=>'excludeFilter', 'value'=> $_POST['excludeFilter'])); ?></div>
                                <div class="form-group"><label>Ignore Filter</label><?php echo Form::textbox( array('class'=>'form-control', 'rows'=>'3', 'name'=>'ignoreFilter', 'value'=> $_POST['ignoreFilter'])); ?></div>
                                <div class="form-group">
                                    <label>Skip files being actively written to?</label><?php echo FormCustom::radioInline($data['stalenessOptions'], $_POST['staleness']); ?>
                                </div>
                                <div class="form-group">
                                    <label>Skip files create/modified outside of cruise start/stop times?</label><?php echo FormCustom::radioInline($data['useStartDateOptions'], $_POST['useStartDate']); ?>
                                </div>
                                <div class="form-group">
                                    <label>Transfer Type</label><?php echo FormCustom::radioInline($data['transferTypeOptions'], $_POST['transferType']); ?>
                                </div>
                                <div class="form-group"><label>Source Directory</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'sourceDir', 'value'=> $_POST['sourceDir'])); ?></div>
                                <div class="form-group rsyncServer"><label>Rsync Server</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'rsyncServer', 'value'=> $_POST['rsyncServer'])); ?></div>
                                <div class="form-group rsyncServer"><label>Rsync Username</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'rsyncUser', 'value'=> $_POST['rsyncUser'])); ?></div>
                                <div class="form-group rsyncServer"><label>Rsync Password</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'rsyncPass', 'value'=> $_POST['rsyncPass'], 'type'=>'password')); ?></div>
                                <div class="form-group smbShare"><label>SMB Server/Share</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'smbServer', 'value'=> $_POST['smbServer'])); ?></div>
                                <div class="form-group smbShare"><label>SMB Domain</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'smbDomain', 'value'=> $_POST['smbDomain'])); ?></div>
                                <div class="form-group smbShare"><label>SMB Username</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'smbUser', 'value'=> $_POST['smbUser'])); ?></div>
                                <div class="form-group smbShare"><label>SMB Password</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'smbPass', 'value'=> $_POST['smbPass'], 'type'=>'password')); ?></div>
                                <div class="form-group sshServer"><label>SSH Server</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'sshServer', 'value'=> $_POST['sshServer'])); ?></div>
                                <div class="form-group sshServer"><label>SSH Username</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'sshUser', 'value'=> $_POST['sshUser'])); ?></div>
                                <div class="form-group sshServer">
                                    <label>Use SSH Public/Private key?</label><?php echo FormCustom::radioInline($data['useSSHKeyOptions'], $_POST['sshUseKey']); ?>
                                </div>
                                <div class="form-group sshServer"><label>SSH Password</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'sshPass', 'value'=> $_POST['sshPass'], 'type'=>'password')); ?></div>
                                <div class="form-group nfsShare"><label>NFS Server/Path</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'nfsServer', 'value'=> $_POST['nfsServer'])); ?></div>
<?php
//                                <div class="form-group nfsShare"><label>NFS Username</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'nfsUser', 'value'=> $_POST['nfsUser'])); /?/></div>
//                                <div class="form-group nfsShare"><label>NFS Password</label><?php echo Form::input( array('class'=>'form-control', 'name'=>'nfsPass', 'value'=> $_POST['nfsPass'], 'type'=>'password')); /?/></div>
?>
                            </div>
                        </div>
                        <div class="row">    
                            <div class="col-lg-12">
                                <?php echo Form::submit( array('name'=>'submit', 'class'=>'btn btn-primary', 'value'=>'Add')); ?>
                                <a href="<?php echo DIR; ?>config/collectionSystemTransfers" class="btn btn-danger">Cancel</a>
                                <?php echo Form::submit( array( 'name'=>'inlineTest', 'class'=>'btn btn-primary pull-right', 'value'=>'Test Setup')); ?>
                            </div>
                        </div>    
                    <?php echo Form::close();?>
                </div>
            </div>
        </div>
        <div class="col-lg-6 col-md-5">
            <h3>Page Guide</h3>
            <p>This form is for adding a new Collection System Transfer to OpenVDM. A Collection System Transfer is an OpenVDM-managed file transfer from a data acqusition system to the Shipboard Data Warehouse.</p>
            <p>The <strong>Name</strong> field is a short name for the Collection System Transfer (i.e. WH300).  These names should NOT have spaces in them.</p>
            <p>The <strong>Long Name</strong> field is a longer name for the Collection System Transfer (i.e. RDI Workhorse 300kHz ADCP ).  These names can have spaces in them.</p>
            <p>The <strong>Destination Directory</strong> is where the data will be stored within the cruise data directory.  This can be a parent directory (i.e. WH300) or a sub-directory (i.e. ADCP/WH300).  If a sub-directory is desired use the UNIX-style directory notation '/'.</p>
            <p>The <strong>Include Filter</strong>, <strong>Exclude Filter</strong> and <strong>Ignore Filter</strong> are used to specify which files to/not to transfer.  These filters use the standard regex structure language (i.e. *.Raw).  Use a single comma (,) to deliminate between filters when multiple filters of a specific type are required (i.e. *.Raw,*.txt). The <strong>Include Filter</strong> defines what files should be transferred.  If nothing is placed here OpenVDM assumes all files in the <strong>Source Directory</strong> should be transferred.  The <strong>Exclude Filter</strong> is used to specify files that match the patters defined in the <strong>Include Filter</strong> but that should NOT be transferred. The <strong>Ignore Filter</strong> defines files in the <strong>Source Directory</strong> that should NOT be transferred and should be ignored entirely by OpenVDM.</p>
            <p>The <strong>Skip files being actively written to?</strong> option instructs OpenVDM on whether to copy all files in the source directory or to skip any files OpenVDM determines may be actively written to by the data acquisition system (DAS) on the collection system workstation.  This option should be selected for DAS software that does not close the active data file between writes (a.k.a. SBE Seasave).</p>
            <p>The <strong>Skip files last modified before cruise start date?</strong> option instructs OpenVDM to NOT copy any files in the source directory with a modification date that preceeds the cruise start date.</p>
            <p>The <strong>Transfer Type</strong> defines how OpenVDM will transfer the data from the Collection System to the Data Warehouse.  <strong>Local Directory</strong> is a transfer of data that is located on the Data Warehouse but is outside of the Cruise Data Directory.  <strong>Rsync Server</strong> is a transfer of data from a Collection System running Rsync and SSH servers. <strong>SMB Share</strong> is a transfer of data from a Collection System with a SMB (Windows) Share.  <strong>SSH Server</strong> is a transfer of cruise data to a destination system via Secure Shell (SSH).  <strong>NFS Share</strong> is a transfer of cruise data to a destination system with a Network Filesystem (NFS) Share.</p>
            <p>The <strong>Source Directory</strong> is the location of the data files on the collection system.</p>
            <p class="rsyncServer">The <strong>Rsync Server</strong> is the IP address of the Collection System (i.e. "192.168.4.151").</p>
            <p class="rsyncServer">The <strong>Rsync Username</strong> is the rsync username with permission to access the data on the Collection System (i.e. "shipTech").  If the rsync server allows anonymous access set this field to "anonymous" and no password will be required.</p>
            <p class="rsyncServer">The <strong>Rsync Password</strong> is the rsync password for the Rsync Username. Not required if Rsync Username is set to "anonymous".</p>
            <p class="smbShare">The <strong>SMB Server/Share</strong> is the SMB Server/Share of the Collection System (i.e. "//192.168.4.151/data").</p>
            <p class="smbShare">The <strong>SMB Domain</strong> is the SMB Server/Share Domain of the Collection System (i.e. "WORKGROUP").  If no value is defined this field will default to "WORKGROUP".</p>
            <p class="smbShare">The <strong>SMB Username</strong> is the SMB username with permission to access the data on the Collection System (i.e. "shipTech").  If the smb server allows guest access set this field to "guest" and no password will be required.</p>
            <p class="smbShare">The <strong>SMB Password</strong> is the SMB password for the SMB Username. Not required if SMB Username is set to "guest".</p>
            <p class="sshServer">The <strong>SSH Server</strong> is the IP address of the Collection System (i.e. "192.168.4.151").</p>
            <p class="sshServer">The <strong>SSH Username</strong> is the SSH username with permission to access the data on the Collection System (i.e. "shipTech").</p>
            <p class="sshServer">The <strong>SSH Password</strong> is the SSH password for the Rsync Username.</p>
            <p class="nfsShare">The <strong>NFS Server/Path</strong> is the IP address of the Collection System NFS Server and the remote path (i.e. "192.168.4.151:/mnt/data/ctd").</p>
<?php 
//            <p class="nfsShare">The <strong>NFS Username</strong> is the nfs username with permission to access the data on the Collection System (i.e. "shipTech").  If the nfs server allows anonymous access set this field to "anonymous" and no password will be required.</p>
//            <p class="nfsShare">The <strong>NFS Password</strong> is the nfs password for the nfs Username. Not required if the nfs Username is set to "anonymous".</p>
?>
            <p>Click the <strong>Add</strong> button to add the new collection system transfer to OpenVDM.  Click the <strong>Cancel</strong> button to exit this form.</p>
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
                <h4 class="modal-title" id="myModalLabel">Test Results for <?php echo $data['testCollectionSystemTransferName'] ?></h4>
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
<!--
**** NOTES ****
 - role attribute in opening form tag not appearing.  Possibly need to edit simpleMVC "form" helper to recognize role attribute.
0=>array('id'=>'1', 'name'=>'rd[]', 'value'=>'x', 'label'=>'label_text' )
-->
