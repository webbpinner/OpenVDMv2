$(function () {
    'use strict';
    
    function updateCruiseDataTransferStatus() {
        var getCruiseDataTransferStatusURL = siteRoot + 'api/cruiseDataTransfers/getCruiseDataTransfersStatuses';
        $.getJSON(getCruiseDataTransferStatusURL, function (data, status) {
            if (status === 'success' && data !== null) {

                var output = '';
                var href = '';
                var i;
                
                for (i = 0; i < data.length; i++) {
                    if (data[i].status === "1") {
                        output = 'Stop';
                        href = siteRoot + 'config/cruiseDataTransfers/stop/' + data[i].cruiseDataTransferID;
                    } else {
                        output = 'Run';
                        href = siteRoot + 'config/cruiseDataTransfers/run/' + data[i].cruiseDataTransferID;
                    }
                    
                    $('#runStop' + data[i].cruiseDataTransferID).attr("href", href);
                    $('#runStop' + data[i].cruiseDataTransferID).html(output);

                    if (data[i].status === "3") {
                        $('#testFail' + data[i].cruiseDataTransferID).html('<i class="fa fa-warning text-danger"></i>');
                    } else {
                        $('#testFail' + data[i].cruiseDataTransferID).html('');
                    }
                }
            }
        });
    }
    
    setInterval(function () {
        updateCruiseDataTransferStatus();
    }, 5000);

    $('#testResultsModal').on('hidden.bs.modal', function () {
        window.location.replace(siteRoot + 'config/cruiseDataTransfers');
    });
        
});
