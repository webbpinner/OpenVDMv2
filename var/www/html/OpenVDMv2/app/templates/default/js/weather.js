$(function () {
    'use strict';

    var OVDM_DIR = '/OpenVDMv2';
    
    Highcharts.setOptions({
        colors: ['#337ab7', '#5cb85c', '#d9534f', '#f0ad4e', '#606060']
    });
    
    var sensorNames = [{dataType: 'gga',   sensorName: 'GPS-Based Position'},
                       {dataType: 'met',   sensorName: 'Weather Sensor'},
                       {dataType: 'twind', sensorName: 'Young Wind Sensor'},
                       {dataType: 'tsg',   sensorName: 'Thermosalinograph'},
                       {dataType: 'svp',   sensorName: 'Sound Velocity Probe'}];
    
    function getCurrentCruise() {
        var getLastestCruiseURL = window.location.origin + OVDM_DIR + '/api/warehouse/getCruiseID';
        $.getJSON(getLastestCruiseURL, function (data, status) {
            if (status === 'success' && data !== null) {
                var latestCruise = data.cruiseID;
                buildMETDataObjectList(latestCruise, 'met');
                buildTWINDDataObjectList(latestCruise, 'twind');

            }
        });
    }

    
    function buildMETDataObjectList(latestCruise, dataType) {
        var getMETDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/' + dataType;
        $.getJSON(getMETDataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
                if (data.length > 0) {
                    var f = document.createElement("form");
                    f.setAttribute("id", dataType + '_objectList');
                    
                    var fg = document.createElement("div");
                    fg.setAttribute("class", "form-group");

                    var r = document.createElement("div");
                    r.setAttribute("class", "row");

                    var cols = [document.createElement("div"), document.createElement("div"), document.createElement("div"), document.createElement("div")];
                    cols[0].setAttribute("class", "col-lg-3 col-sm-6");
                    cols[1].setAttribute("class", "col-lg-3 col-sm-6");
                    cols[2].setAttribute("class", "col-lg-3 col-sm-6");
                    cols[3].setAttribute("class", "col-lg-3 col-sm-6");
                    
                    for (var i = data.length-1, row = 0; i >= 0; i--, row++) {
                        var d = document.createElement("div");
                        d.setAttribute("class","radio")
                        var l = document.createElement("label");
                        var cb = document.createElement("input");
                        cb.setAttribute("type", "radio");
                        cb.setAttribute("name", dataType + "RadioOptions");
                        cb.setAttribute("id", dataType + "Radio_" + data[i].dataDashboardObjectID);
                        cb.setAttribute("value", data[i].dataDashboardObjectID);
                        l.appendChild(cb);
                        l.innerHTML = l.innerHTML + '<small>' + data[i].dataDashboardRawFile.split(/[\\/]/).pop() + '</small>';
                        d.appendChild(l)
                        cols[row].appendChild(d);
                        
                        if(row == 3) {
                            row = -1;
                        }
                    }
                    
                    r.appendChild(cols[0]);
                    r.appendChild(cols[1]);
                    r.appendChild(cols[2]);
                    r.appendChild(cols[3]);

                    fg.appendChild(r);
                    f.appendChild(fg);
                    
                    $('#' + dataType + '_objectList').replaceWith(f);
                    
                    $('#' + dataType + '_objectList' + ' input[type=radio]').click(function(){
                            updateMETChart($(this).val(), dataType);
                    });
                    
                    // Check latest position and most recent dataset
                    $('#' + dataType + 'Radio_' + data[data.length-1].dataDashboardObjectID).trigger('click');
                    
                } else {
                    $('#' + dataType + '_objectList').html('<strong>No met Data Found</strong>');
                    $('#' + dataType + '_placeholder').html('<strong>No Data Found</strong>');
                }
            }
        });
    }
    
    function updateMETChart(dataDashboardObjectID, dataType) {
        var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + dataDashboardObjectID;
        $.getJSON(getDataObjectFileURL, function (data, status) {
            if (status === 'success' && data !== null) {

                if ('error' in data){
                    $('#' + dataDashboardObjectID).html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    var seriesData = [];
                    var yAxes = [];
                    var xAxes = [];

                    var i = 0;
                    for (i = 0; i < data.visualizerData.length; i++) {
                        yAxes[i] = {
                            labels: {
                                format: '{value}',
                                style: {
                                    color: Highcharts.getOptions().colors[i]
                                }
                            },
                            title: {
                                text: '',
                                style: {
                                    color: Highcharts.getOptions().colors[i]
                                }
                            }
                        };
                        if (i >= data.visualizerData.length / 2) {
                            yAxes[i].opposite = true;
                        }

                        if (data.visualizerData[i].label === "Humidity (%)") {
                            yAxes[i].min = 0;
                            yAxes[i].max = 100;
                        }

                        seriesData[i] = {
                            name: data.visualizerData[i].label,
                            yAxis: i,
                            data: data.visualizerData[i].data,
                            animation: false
                        };
                    }

                    var chartOptions = {
                        chart: {type: 'line' },
                        title: {text: ''},
                        tooltip: {shared: true, crosshairs: true},
                        legend: {enabled: true},
                        xAxis: {type: 'datetime',
                                title: {text: ''},
                                dateTimeLabelFormats: {millisecond: '%H', second: '%H:%M:%S', minute: '%H:%M', hour: '%H:%M', day: '%e. %b', week: '%e. %b', month: '%b \'%y', year: '%Y'}
                               },
                        yAxis: yAxes,
                        series: seriesData
                    };

                    $('#' + dataType + '_placeholder').highcharts(chartOptions);
                }
            }
        });
    }
    
    function buildTWINDDataObjectList(latestCruise, dataType) {
        var getTWINDDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/' + dataType;
        $.getJSON(getTWINDDataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
                if (data.length > 0) {
                    var f = document.createElement("form");
                    f.setAttribute("id", dataType + "_objectList");
                    
                    var fg = document.createElement("div");
                    fg.setAttribute("class", "form-group");

                    var r = document.createElement("div");
                    r.setAttribute("class", "row");

                    var cols = [document.createElement("div"), document.createElement("div"), document.createElement("div"), document.createElement("div")];
                    cols[0].setAttribute("class", "col-lg-3 col-sm-6");
                    cols[1].setAttribute("class", "col-lg-3 col-sm-6");
                    cols[2].setAttribute("class", "col-lg-3 col-sm-6");
                    cols[3].setAttribute("class", "col-lg-3 col-sm-6");
                    
                    for (var i = data.length-1, row = 0; i >= 0; i--, row++) {
                        var d = document.createElement("div");
                        d.setAttribute("class","radio")
                        var l = document.createElement("label");
                        var cb = document.createElement("input");
                        cb.setAttribute("type", "radio");
                        cb.setAttribute("name", dataType + "RadioOptions");
                        cb.setAttribute("id", dataType + "Radio_" + data[i].dataDashboardObjectID);
                        cb.setAttribute("value", data[i].dataDashboardObjectID);
                        l.appendChild(cb);
                        l.innerHTML = l.innerHTML + '<small>' + data[i].dataDashboardRawFile.split(/[\\/]/).pop() + '</small>';
                        d.appendChild(l)
                        cols[row].appendChild(d);
                        
                        if(row == 3) {
                            row = -1;
                        }
                    }
                    
                    r.appendChild(cols[0]);
                    r.appendChild(cols[1]);
                    r.appendChild(cols[2]);
                    r.appendChild(cols[3]);

                    fg.appendChild(r);
                    f.appendChild(fg);
                    
                    $('#' + dataType + '_objectList').replaceWith(f);
                    
                    $('#' + dataType + '_objectList' + ' input[type=radio]').click(function(){
                            updateTWINDChart($(this).val(), dataType);
                    });
                    
                    // Check latest position and most recent dataset
                    $('#' + dataType + 'Radio_' + data[data.length-1].dataDashboardObjectID).trigger('click');
                    
                } else {
                    $('#' + dataType + '_objectList').html('<strong>No twind Data Found</strong>');
                    $('#' + dataType + '_placeholder').html('<strong>No Data Found</strong>');
                }
            }
        });
    }
    
    function updateTWINDChart(dataDashboardObjectID, dataType) {
        var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + dataDashboardObjectID;
        $.getJSON(getDataObjectFileURL, function (data, status) {
            if (status === 'success' && data !== null) {

                if ('error' in data){
                    $('#' + dataDashboardObjectID).html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    var seriesData = [];
                    var yAxes = [];
                    var xAxes = [];

                    var i = 0;
                    for (i = 0; i < data.visualizerData.length; i++) {
                        yAxes[i] = {
                            labels: {
                                format: '{value}',
                                style: {
                                    color: Highcharts.getOptions().colors[i]
                                }
                            },
                            title: {
                                text: '',
                                style: {
                                    color: Highcharts.getOptions().colors[i]
                                }
                            }
                        };
                        if (i >= data.visualizerData.length / 2) {
                            yAxes[i].opposite = true;
                        }

                        seriesData[i] = {
                            name: data.visualizerData[i].label,
                            yAxis: i,
                            data: data.visualizerData[i].data,
                            animation: false
                        };
                    }

                    var chartOptions = {
                        chart: {type: 'line' },
                        title: {text: ''},
                        tooltip: {shared: true, crosshairs: true},
                        legend: {enabled: true},
                        xAxis: {type: 'datetime',
                                title: {text: ''},
                                dateTimeLabelFormats: {millisecond: '%H', second: '%H:%M:%S', minute: '%H:%M', hour: '%H:%M', day: '%e. %b', week: '%e. %b', month: '%b \'%y', year: '%Y'}
                               },
                        yAxis: yAxes,
                        series: seriesData
                    };

                    $('#' + dataType + '_placeholder').highcharts(chartOptions);
                }
            }
        });
    }
    
    getCurrentCruise();

});
    
