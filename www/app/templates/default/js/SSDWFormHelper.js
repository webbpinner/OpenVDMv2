$(function () {
    'use strict';
    
    function setSSHUseKeyField(sshUseKey) {
        if(sshUseKey == "1"){
            $('input[name=sshPass]').val(""); 
            $('input[name=sshPass]').prop('disabled', true);
        } else {
            $('input[name=sshPass]').prop('disabled', false);
        }
    }
    
    setSSHUseKeyField($('input[name=sshUseKey]:checked').val())

    $('input[name=sshUseKey]').change(function () {
        setSSHUseKeyField($(this).val());
    });
    
});
