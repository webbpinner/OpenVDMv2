$(function () {
    'use strict';
    
    function updateCollectionSystemTransferStatusList(collectionSystemTransferStatusList) {

        var collectionSystemTransferStatusURL = siteRoot + 'api/collectionSystemTransfers/getActiveCollectionSystemTransfers';
        $.getJSON(collectionSystemTransferStatusURL, function (data, status) {
            if (status === 'success' && data !== null) {
                var output = '';
                var i = 0;
                for (i = 0; i < data.length; i++) {
                    if (data[i].enable === "1") {
                        output += '<div class="list-group-item ';
                        if (data[i].status === "1") {
                            output += 'list-group-item-success"><i class="fa fa-download"></i> ';
                            output += data[i].longName;
                            output += '<span class="pull-right">Running</span></div>';
                        } else if (data[i].status === "2") {
                            output += 'list-group-item-warning"><i class="fa fa-moon-o"></i> ';
                            output += data[i].longName;
                            output += '<span class="pull-right">Idle</span></div>';
                        } else if (data[i].status === "3") {
                            output += 'list-group-item-danger"><i class="fa fa-warning"></i> ';
                            output += data[i].longName;
                            output += '<span class="pull-right">Error</span></div>';
                        } else if (data[i].status === "4") {
                            output += 'disabled"><i class="fa fa-times"></i> ';
                            output += data[i].longName;
                            output += '<span class="pull-right">Disabled</span></div>\n';
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

    function updateFinalizedCruiseButton(status) {
        if (status === "3") {
            $('#finalizeCurrentCruise').html('<i class="fa fa-warning"></i> Run End-of-Cruise Tasks');
        } else {
            var finalizedStatusURL = siteRoot + 'api/warehouse/getCruiseFinalizedDate'
            $.getJSON(finalizedStatusURL, function (data, status) {
                if (status === 'success' && data !== null) {
                    if (data.cruiseFinalizedOn) {
                        $('#finalizeCurrentCruise').html('<i class="fa fa-check"></i> Run End-of-Cruise Tasks');
                    } else {
                        $('#finalizeCurrentCruise').html("Run End-of-Cruise Tasks");
                    }
                } else {
                    $('#finalizeCurrentCruise').html("Run End-of-Cruise Tasks");
                }
            });
        }
    }
    
    function updateFinalizedLoweringButton(status) {
        if (status === "3") {
            $('#finalizeCurrentLowering').html('<i class="fa fa-warning"></i> Run End-of-' + lowering_name + ' Tasks');
        } else {
            var finalizedStatusURL = siteRoot + 'api/warehouse/getLoweringFinalizedDate'
            $.getJSON(finalizedStatusURL, function (data, status) {
                if (status === 'success' && data !== null) {
                    if (data.loweringFinalizedOn) {
                        $('#finalizeCurrentLowering').html('<i class="fa fa-check"></i> Run End-of-' + lowering_name + ' Tasks');
                    } else {
                        $('#finalizeCurrentLowering').html('Run End-of-' + lowering_name + ' Tasks');
                    }
                } else {
                    $('#finalizeCurrentLowering').html('Run End-of-' + lowering_name + ' Tasks');
                }
            });
        }
    }

    function updateTaskStatusList(taskList) {
        var taskStatusURL = siteRoot + 'api/tasks/getActiveTasks'
        $.getJSON(taskStatusURL, function (data, status) {
            if (status === 'success' && data !== null) {
                var output = '';
                var i = 0;
                for (i = 0; i < data.length; i++) {
                    if((data[i].name != 'setupNewCruise') && (data[i].name != 'finalizeCurrentCruise') && (data[i].name != 'setupNewLowering') && (data[i].name != 'finalizeCurrentLowering')) {
                        output += '<div class="list-group-item">';
                        output += data[i].longName;
                        if (data[i].status === "1") {
                            output += '<span class="pull-right btn btn-outline btn-default btn-xs disabled">Wait</span></div>';
                        } else if (data[i].status === "2") {
                            output += '<a href="' + siteRoot + 'config/' + data[i].name + '" class="pull-right btn btn-outline btn-primary btn-xs">Run</a>';
                        } else if (data[i].status === "3") {
                            output += '<span class="pull-right"><i class="fa fa-warning text-danger"></i>&nbsp;&nbsp;<a href="' + siteRoot + 'config/' + data[i].name + '" class="btn btn-outline btn-primary btn-xs">Run</a></span>';
                        }
                    } else if (data[i].name === 'finalizeCurrentCruise') {
                        if (data[i].status === "1") {
                            $('#finalizeCurrentCruise').addClass('disabled');
                            $('#finalizeCurrentCruise').html("Running End-of-Cruise Tasks... please standby.")
                        } else {
                            $('#finalizeCurrentCruise').removeClass('disabled');
                            //$('#finalizeCurrentCruise').html("Run End-of-Cruise Tasks")
                            updateFinalizedCruiseButton(data[i].status);
                        }
                    } else if (data[i].name === 'finalizeCurrentLowering') {
                        if (data[i].status === "1") {
                            $('#finalizeCurrentLowering').addClass('disabled');
                            $('#finalizeCurrentLowering').html("Running End-of-" + lowering_name + " Tasks... please standby.")
                        } else {
                            $('#finalizeCurrentLowering').removeClass('disabled');
                            //$('#finalizeCurrentLowering').html("Run End-of-" + lowering_name + " Tasks")
                            updateFinalizedLoweringButton(data[i].status);
                        }
                    }
                    output += '</div>';
                }
                
                $(taskList).html(output);
                
            }
            setTimeout(function () {
                updateTaskStatusList(taskList);
            }, 5000);
        });
    }
    
    function updateOptionalCruiseDataTransferStatusList(optionalCruiseDataTransferStatusList) {
        var optionalCruiseDataTransferStatusURL = siteRoot + 'api/cruiseDataTransfers/getCruiseDataTransfersStatuses';
        $.getJSON(optionalCruiseDataTransferStatusURL, function (data, status) {
            if (status === 'success' && data !== null) {
                var output = '';
                for (var i = 0; i < data.length; i++) {
                    if (data[i].enable === "1") {
                        output += '<div class="list-group-item ';
                        if(data[i].status == "1") {
                            output += 'list-group-item-success"><i class="fa fa-download"></i> '
                            output += data[i].longName
                            output += '<span class="pull-right">Running</span></div>'
                        } else if(data[i].status == "2") {
                            output += 'list-group-item-warning"><i class="fa fa-moon-o"></i> '
                            output += data[i].longName
                            output += '<span class="pull-right">Idle</span></div>'
                        } else if (data[i].status == "3") {
                            output += 'list-group-item-danger"><i class="fa fa-warning"></i> '
                            output += data[i].longName
                            output += '<span class="pull-right">Error</span></div>'
                        } else if (data[i].status == "4") {
                            output += 'disabled"><i class="fa fa-times"></i> '
                            output += data[i].longName
                            output += '<span class="pull-right">Disabled</span></div>\n'
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
                for (var i = 0; i < data.length; i++) {
                    output += '<div class="list-group-item ';
                    if(data[i].status == "1") {
                        output += 'list-group-item-success"><i class="fa fa-download"></i> '
                        output += data[i].longName
                        output += '<span class="pull-right">Running</span></div>'
                    } else if(data[i].status == "2") {
                        output += 'list-group-item-warning"><i class="fa fa-moon-o"></i> '
                        output += data[i].longName
                        output += '<span class="pull-right">Idle</span></div>'
                    } else if (data[i].status == "3") {
                        output += 'list-group-item-danger"><i class="fa fa-warning"></i> '
                        output += data[i].longName
                        output += '<span class="pull-right">Error</span></div>'
                    } else if (data[i].status == "4") {
                        output += 'disabled"><i class="fa fa-times"></i> '
                        output += data[i].longName
                        output += '<span class="pull-right">Disabled</span></div>\n'
                    }
                }
                
                $(requiredCruiseDataTransferStatusList).html(output);
                
            }
            setTimeout(function () {
                updateRequiredCruiseDataTransferStatusList(requiredCruiseDataTransferStatusList);
            }, 5000);
        });
    }

    updateCollectionSystemTransferStatusList('#collectionSystemTransferStatusList');
    updateOptionalCruiseDataTransferStatusList('#optionalCruiseDataTransfers');
    updateRequiredCruiseDataTransferStatusList('#requiredCruiseDataTransfers');
    updateTaskStatusList('#taskStatusList');
    
    $('#jobResultsModal').on('hidden.bs.modal', function () {
        window.location.replace(siteRoot + 'config');
    });
});
