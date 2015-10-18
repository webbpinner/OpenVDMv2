$(function () {
    'use strict';
    
    function updateCollectionSystemTransferStatus() {
        var getJobsURL = siteRoot + 'api/collectionSystemTransfers/getCollectionSystemTransfersStatuses';
        $.getJSON(getJobsURL, function (data, status) {
            if (status === 'success' && data !== null) {

                var output = '';
                var href = '';
                var i;
                
                for (i = 0; i < data.length; i++) {
                    if (data[i].status === "1") {
                        output = 'Stop';
                        href = siteRoot + 'config/collectionSystemTransfers/stop/' + data[i].collectionSystemTransferID;
                    } else {
                        output = 'Run';
                        href = siteRoot + 'config/collectionSystemTransfers/run/' + data[i].collectionSystemTransferID;
                    }
                    
                    $('#runStop' + data[i].collectionSystemTransferID).attr("href", href);
                    $('#runStop' + data[i].collectionSystemTransferID).html(output);

                }
            }
        });
    }
    
    setInterval(function () {
        updateCollectionSystemTransferStatus();
    }, 5000);

    $('#testResultsModal').on('hidden.bs.modal', function () {
        window.location.replace(siteRoot + 'config/collectionSystemTransfers');
    });

});
