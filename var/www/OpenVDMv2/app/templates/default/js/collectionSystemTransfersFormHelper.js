$(function () {
    'use strict';
    
    var transferTypeOptions = [
        {"value" : "1", "text" : "Local Directory"},
        {"value" : "2", "text" : "Rsync Server"},
        {"value" : "3", "text" : "SMB Share"},
        {"value" : "4", "text" : "Remote Push"}
    ];
    
    function setTransferTypeFields(transferType) {

        if (transferType === '') { transferType = '1'; }
        var transferTypeText = transferTypeOptions[parseInt(transferType, 10) - 1].text;
        
        switch (transferTypeText) {
        case "Local Directory":
            $(".rsyncServer").hide();
            $(".smbShare").hide();
        //    $(".remotePush").hide();
            break;
        case "Rsync Server":
            $(".rsyncServer").show();
            $(".smbShare").hide();
        //    $(".remotePush").hide();
            break;
        case "SMB Share":
            $(".rsyncServer").hide();
            $(".smbShare").show();
        //    $(".remotePush").hide();
            break;
        case "Remote Push":
            $(".rsyncServer").hide();
            $(".smbShare").hide();
        //    $(".remotePush").show();
            break;
        default:
        }
    }
    
    setTransferTypeFields($('input[name=transferType]:checked').val());
    
    $('input[name=transferType]').change(function () {
        setTransferTypeFields($(this).val());
    });
    
});
