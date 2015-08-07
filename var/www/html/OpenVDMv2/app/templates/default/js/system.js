$(function () {
    'use strict';
    
    function updateRequiredCruiseDataTransferStatus() {
        var getRequiredCruiseDataTransferStatusURL = siteRoot + 'api/cruiseDataTransfers/getRequiredCruiseDataTransfersStatuses';
        $.getJSON(getRequiredCruiseDataTransferStatusURL, function (data, status) {
            if (status === 'success' && data !== null) {

                var i;
                for (i = 0; i < data.length; i++) {
                    if (data[i].name === "SSDW") {
                        if (data[i].status === "3") {
                            $('#testFailSSDW').html('<i class="fa fa-warning text-danger"></i>');
                        } else {
                            $('#testFailSSDW').html('');
                        }
                    }
                }
            }
        });
    }
    
    function updateSBDWTestFail() {
        var updateSBDWTestFailURL = siteRoot + 'api/warehouse/getShipboardDataWarehouseStatus';
        $.getJSON(updateSBDWTestFailURL, function (data, status) {
            if (status === 'success' && data !== null) {
                if (data.shipboardDataWarehouseStatus === "3") {
                    $('#testFailSBDW').html('<i class="fa fa-warning text-danger"></i>');
                } else {
                    $('#testFailSBDW').html('');
                }
            }
        });
    }
    
    setInterval(function () {
        updateSBDWTestFail();
    }, 5000);
    
    setInterval(function () {
        updateRequiredCruiseDataTransferStatus();
    }, 5000);
    
    $('#testResultsModal').on('hidden.bs.modal', function () {
        window.location.replace(siteRoot + 'config/system');
    });

});

