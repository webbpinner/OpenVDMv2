$(function () {
    'use strict';
   
    $(window).load(function(){
        if($('#statsModal')) {
            $('#statsModal').modal('show');
        }
    });
    
    $('#statsModal').on('hidden.bs.modal', function () {
        var closeURL = $(this).find('#modal-close-btn').attr("href");
        window.location.replace(closeURL);
    });
});