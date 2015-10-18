$(function () {
    'use strict';
   
    $(window).load(function(){
        if($('#statsModal')) {
            $('#statsModal').modal('show');
        }
    });
    
    $('#statsModal').on('hidden.bs.modal', function () {
        window.location.replace(siteRoot + 'dataDashboard/qualityControl');
    });
});