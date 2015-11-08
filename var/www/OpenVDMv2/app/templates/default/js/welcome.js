$(function () {
    'use strict';
    
    var transferLogNum = 5;
    
    function formatTime(dateStr) {
        return dateStr.substr(0, 4) + '-' + dateStr.substr(4, 2) + '-' + dateStr.substr(6, 2) + ' ' + dateStr.substr(9, 2) + ':' + dateStr.substr(11, 2) + ':' + dateStr.substr(13, 2) + ' UTC';
    }
    
    function updateCollectionSystemTransferStatusList(collectionSystemTransferStatusList) {
        var collectionSystemTransferStatusURL = siteRoot + 'api/collectionSystemTransfers/getCollectionSystemTransfersStatuses';
        $.getJSON(collectionSystemTransferStatusURL, function (data, status) {
            if (status === 'success' && data !== null) {
                var output = '';
                var i = 0;
                for (i = 0; i < data.length; i++) {
                    if (data[i].enable === "1") {
                        output += '<div class="list-group-item ';
                        if (data[i].status === "1") {
                            output += 'list-group-item-success">';
                            output += data[i].longName;
                            output += '<span class="pull-right"><i class="fa fa-download"></i> Running</span></div>';
                        } else if (data[i].status === "2") {
                            output += 'list-group-item-warning">';
                            output += data[i].longName;
                            output += '<span class="pull-right"><i class="fa fa-moon-o"></i> Idle</span></div>';
                        } else if (data[i].status === "3") {
                            output += 'list-group-item-danger">';
                            output += data[i].longName;
                            output += '<span class="pull-right"><i class="fa fa-warning"></i> Error</span></div>';
                        } else if (data[i].status === "4") {
                            output += 'disabled">';
                            output += data[i].longName;
                            output += '<span class="pull-right"><i class="fa fa-times"></i> Disabled</span></div>\n';
                        }
                    }
                }
                
                $(collectionSystemTransferStatusList).html(output);
                
            }
            setTimeout(function () {
                updateCollectionSystemTransferStatusList(collectionSystemTransferStatusList);
            }, 5000);
        });
    }

    
    function updateOptionalCruiseDataTransferStatusList(optionalCruiseDataTransferStatusList) {
        var optionalCruiseDataTransferStatusURL = siteRoot + 'api/cruiseDataTransfers/getCruiseDataTransfersStatuses';
        $.getJSON(optionalCruiseDataTransferStatusURL, function (data, status) {
            if (status === 'success' && data !== null) {
                var output = '';
                var i = 0;
                for (i = 0; i < data.length; i++) {
                    if (data[i].enable === "1") {
                        output += '<div class="list-group-item ';
                        if (data[i].status === "1") {
                            output += 'list-group-item-success">';
                            output += data[i].longName;
                            output += '<span class="pull-right"><i class="fa fa-download"></i> Running</span></div>';
                        } else if (data[i].status === "2") {
                            output += 'list-group-item-warning">';
                            output += data[i].longName;
                            output += '<span class="pull-right"><i class="fa fa-moon-o"></i> Idle</span></div>';
                        } else if (data[i].status === "3") {
                            output += 'list-group-item-danger">';
                            output += data[i].longName;
                            output += '<span class="pull-right"><i class="fa fa-warning"></i> Error</span></div>';
                        } else if (data[i].status === "4") {
                            output += 'disabled">';
                            output += data[i].longName;
                            output += '<span class="pull-right"><i class="fa fa-times"></i> Disabled</span></div>\n';
                        }
                    }
                }
                
                $(optionalCruiseDataTransferStatusList).html(output);
                
            }
            setTimeout(function () {
                updateOptionalCruiseDataTransferStatusList(optionalCruiseDataTransferStatusList);
            }, 5000);
        });
    }
    
    function updateRequiredCruiseDataTransferStatusList(requiredCruiseDataTransferStatusList) {
        var requiredCruiseDataTransferStatusURL = siteRoot + 'api/cruiseDataTransfers/getRequiredCruiseDataTransfersStatuses';
        $.getJSON(requiredCruiseDataTransferStatusURL, function (data, status) {
            if (status === 'success' && data !== null) {
                var output = '';
                var i = 0;
                for (i = 0; i < data.length; i++) {
                    output += '<div class="list-group-item ';
                    if (data[i].status === "1") {
                        output += 'list-group-item-success">';
                        output += data[i].longName;
                        output += '<span class="pull-right"><i class="fa fa-download"></i> Running</span></div>';
                    } else if (data[i].status === "2") {
                        output += 'list-group-item-warning">';
                        output += data[i].longName;
                        output += '<span class="pull-right"><i class="fa fa-moon-o"></i> Idle</span></div>';
                    } else if (data[i].status === "3") {
                        output += 'list-group-item-danger">';
                        output += data[i].longName;
                        output += '<span class="pull-right"><i class="fa fa-warning"></i> Error</span></div>';
                    } else if (data[i].status === "4") {
                        output += 'disabled">';
                        output += data[i].longName;
                        output += '<span class="pull-right"><i class="fa fa-times"></i> Disabled</span></div>\n';
                    }
                }
                
                $(requiredCruiseDataTransferStatusList).html(output);
                
            }
            setTimeout(function () {
                updateRequiredCruiseDataTransferStatusList(requiredCruiseDataTransferStatusList);
            }, 5000);
        });
    }

    function updateErrorLogSummary(errorFilesPanel) {
        var updateTransferLogSummaryURL = siteRoot + 'api/transferLogs/getExcludeLogsSummary';
        var options = {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        };
        $.getJSON(updateTransferLogSummaryURL, function (data, status) {
            if (status === 'success' && data !== null) {

                var errorFilesOutput = '';
                if (data.length > 0) {
                    
                    var i = 0;
                    for (i = 0; i < data.length; i++) {
                        if(data[i].errorFiles.length > 0) {
                            errorFilesOutput += '                   <h5>' + data[i].collectionSystemName + '</h5>';
                            errorFilesOutput += '                   <ul>';
                            var j = 0;
                            for (j = 0; j < data[i].errorFiles.length; j++) {
                                errorFilesOutput += '                       <li><small>' + data[i].errorFiles[j] + '</small></li>';
                            }
                            errorFilesOutput += '                   </ul>';
                        }
                    }
                    
                } else {
                    errorFilesOutput = '                   <h5>No Filename Errors Found</h5>';
                }

                $(errorFilesPanel).html(errorFilesOutput);
            } setTimeout(function () {
                updateErrorLogSummary(errorFilesPanel);
            }, 5000);
        });
    }
                  

    function updateShipboardLogSummary(shipboardFilesPanel) {
        var updateTransferLogSummaryURL = siteRoot + 'api/transferLogs/getShipboardLogsSummary/' + transferLogNum;
        var options = {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        };
        $.getJSON(updateTransferLogSummaryURL, function (data, status) {
            if (status === 'success' && data !== null) {

                var shipboardTransfersOutput = '';
                if ( data.length > 0) {
                    
                    var index = 0;
                    var i = 0;
                    for (i = 0; i < data.length; i++) {
                        index++;
                        if (index > transferLogNum) {
                            break;
                        }
                        shipboardTransfersOutput += '                   <h5>' + data[i].collectionSystemName + ' - ' + formatTime(data[i].date) + '</h5>';
                        shipboardTransfersOutput += '                   <ul>';
                        var j = 0;
                        for (j = 0; j < data[i].newFiles.length; j++) {
                            shipboardTransfersOutput += '                       <li><small>' + data[i].newFiles[j] + '</small></li>';
                        }
                        if (data[i].updatedFiles.length > 0) {
                            shipboardTransfersOutput += '                       <li><small>' + data[i].updatedFiles.length + ' File(s) Updated</small></li>';
                        }
                        shipboardTransfersOutput += '                   </ul>';
                    }
                    

                } else {
                    shipboardTransfersOutput = '                   <h5>No Recent Shipboard Transfers Have Occured</h5>';
                }
                
                $(shipboardFilesPanel).html(shipboardTransfersOutput);
            } setTimeout(function () {
                updateShipboardLogSummary(shipboardFilesPanel);
            }, 5000);
        });
    }

    function updateShipToShoreLogSummary(shipToShoreFilesPanel) {
        var updateTransferLogSummaryURL = siteRoot + 'api/transferLogs/getShipToShoreLogsSummary/' + transferLogNum;
        var options = {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        };
        
         $.getJSON(updateTransferLogSummaryURL, function (data, status) {
            if (status === 'success' && data !== null) {

                var shipToShoreTransfersOutput = '';
                if (data.length > 0) {

                    var index = 0;
                    var i = 0;
                    for (i = 0; i < data.length; i++) {
                        index++;
                        if (index > transferLogNum) {
                            break;
                        }
                        shipToShoreTransfersOutput += '                   <h5>' + data[i].shipToShoreTransferName + ' - ' + formatTime(data[i].date) + '</h5>';
                        shipToShoreTransfersOutput += '                   <ul>';
                        var j = 0;
                        for (j = 0; j < data[i].newFiles.length; j++) {
                            shipToShoreTransfersOutput += '                       <li><small>' + data[i].newFiles[j] + '</small></li>';
                        }
                        if (data[i].updatedFiles.length > 0) {
                            shipToShoreTransfersOutput += '                       <li><small>' + data[i].updatedFiles.length + ' File(s) Updated</small></li>';
                        }
                        shipToShoreTransfersOutput += '                   </ul>';
                    }
                } else {
                    shipToShoreTransfersOutput = '                   <h5>No Recent Ship-to-Shore Transfers Have Occured</h5>';
                }

                $(shipToShoreFilesPanel).html(shipToShoreTransfersOutput);
            } setTimeout(function () {
                updateShipToShoreLogSummary(shipToShoreFilesPanel);
            }, 5000);
        });
    }
    
    updateErrorLogSummary('#filenameErrors');
    updateShipboardLogSummary('#shipboardTransfers');
    updateShipToShoreLogSummary('#shipToShoreTransfers');
    updateCollectionSystemTransferStatusList('#collectionSystemTransferStatusList');
    updateOptionalCruiseDataTransferStatusList('#optionalCruiseDataTransfers');
    updateRequiredCruiseDataTransferStatusList('#requiredCruiseDataTransfers');

});
