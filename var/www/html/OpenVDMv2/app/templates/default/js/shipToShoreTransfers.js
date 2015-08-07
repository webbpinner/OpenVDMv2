$(function () {
    'use strict';
    
    function updateShipToShoreTransferStatus() {
        var getRequiredCruiseDataTransferStatusURL = siteRoot + 'api/cruiseDataTransfers/getRequiredCruiseDataTransfersStatuses';
        $.getJSON(getRequiredCruiseDataTransferStatusURL, function (data, status) {
            if (status === 'success' && data !== null) {

                var output = '';
                var classes = '';
                var href = '';
                var i;
                
                for (i = 0; i < data.length; i++) {
                    if (data[i].name === "SSDW") {
                    
                        if (data[i].status === "1") {
                            output = 'Stop Ship-to-Shore Transfer';
                            classes = 'btn btn-sm btn-danger';
                            href = siteRoot + 'config/shipToShoreTransfers/stop';
                        } else if (data[i].status === "3") {
                            output = 'Run Ship-to-Shore Transfer';
                            classes = 'btn btn-sm btn-default disabled';
                            href = siteRoot + 'config/shipToShoreTransfers/run';
                        } else {
                            output = 'Run Ship-to-Shore Transfer';
                            classes = 'btn btn-sm btn-success';
                            href = siteRoot + 'config/shipToShoreTransfers/run';
                        }
                    
                        $('#runStop').attr("href", href);
                        $('#runStop').attr("class", classes);
                        $('#runStop').html(output);

                        break;
                    }
                }
            }
        });
    }
    
    setInterval(function () {
        updateShipToShoreTransferStatus();
    }, 5000);
        
});
