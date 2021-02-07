$(function () {
    'use strict';
    
    var transferTypeOptions = [
        {"value" : "1", "text" : "Local Directory"},
        {"value" : "2", "text" : "Rsync Server"},
        {"value" : "3", "text" : "SMB Share"},
        {"value" : "4", "text" : "SSH Server"},
        {"value" : "5", "text" : "NFS Share"},
    ];

    function setSSHUseKeyField(sshUseKey) {
        if(sshUseKey == "1"){
            $('input[name=sshPass]').val(""); 
            $('input[name=sshPass]').prop('disabled', true);
        } else {
            $('input[name=sshPass]').prop('disabled', false);
        }
    }
    
    function setTransferTypeFields(transferType) {

        if (transferType === '') { transferType = '1'; }
        var transferTypeText = transferTypeOptions[parseInt(transferType, 10) - 1].text;
        
        switch (transferTypeText) {
        case "Local Directory":
            $(".localDir").show();
            $(".rsyncServer").hide();
            $(".smbShare").hide();
            $(".sshServer").hide();
            $(".nfsShare").hide();
            break;
        case "Rsync Server":
            $(".localDir").hide();
            $(".rsyncServer").show();
            $(".smbShare").hide();
            $(".sshServer").hide();
            $(".nfsShare").hide();
            break;
        case "SMB Share":
            $(".localDir").hide();
            $(".rsyncServer").hide();
            $(".smbShare").show();
            $(".sshServer").hide();
            $(".nfsShare").hide();
            break;
        case "SSH Server":
            $(".localDir").hide();
            $(".rsyncServer").hide();
            $(".smbShare").hide();
            $(".sshServer").show();
            $(".nfsShare").hide();
            break;
        case "NFS Share":
            $(".localDir").hide();
            $(".rsyncServer").hide();
            $(".smbShare").hide();
            $(".sshServer").hide();
            $(".nfsShare").show();
            break;
        default:
        }
    }
    
    setTransferTypeFields($('input[name=transferType]:checked').val());
    setSSHUseKeyField($('input[name=sshUseKey]:checked').val())
    
    $('input[name=transferType]').change(function () {
        setTransferTypeFields($(this).val());
    });

    $('input[name=sshUseKey]').change(function () {
        setSSHUseKeyField($(this).val());
    });
    
});
