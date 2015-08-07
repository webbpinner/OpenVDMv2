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
                buildMETDataObjectList(latestCruise, 'met_objectList');
                buildTWINDDataObjectList(latestCruise, 'twind_objectList');
            }
        });
    }

    
    function buildMETDataObjectList(latestCruise, dataObjectListDivBlockID) {
        var getMETDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/met';
        $.getJSON(getMETDataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
                if (data.length > 0) {
                    var f = document.createElement("form");
                    f.setAttribute("id", dataObjectListDivBlockID);
                    
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
                        cb.setAttribute("name", "metRadioOptions");
                        cb.setAttribute("id", "metRadio_" + data[i].dataDashboardObjectID);
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
                    
                    $('#' + dataObjectListDivBlockID).replaceWith(f);
                    
                    $('#' + dataObjectListDivBlockID + ' input[type=radio]').click(function(){
                            updateMETChart($(this).val());
                    });
                    
                    // Check latest position and most recent dataset
                    $('#metRadio_' + data[data.length-1].dataDashboardObjectID).trigger('click');
                    
                    //buildGGAMap(data[data.length - 1]);
                } else {
                    $('#' + dataObjectListDivBlockID).html('<strong>No met Data Found</strong>');
                    $('#met_placeholder').html('<strong>No Data Found</strong>');
                }
            }
        });
    }
    
    function updateMETChart(dataDashboardObjectID) {
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

                    $('#met_placeholder').highcharts(chartOptions);
                }
            }
        });
    }
    
    function buildTWINDDataObjectList(latestCruise, dataObjectListDivBlockID) {
        var getTWINDDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/twind';
        $.getJSON(getTWINDDataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
                if (data.length > 0) {
                    var f = document.createElement("form");
                    f.setAttribute("id", dataObjectListDivBlockID);
                    
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
                        cb.setAttribute("name", "twindRadioOptions");
                        cb.setAttribute("id", "twindRadio_" + data[i].dataDashboardObjectID);
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
                    
                    $('#' + dataObjectListDivBlockID).replaceWith(f);
                    
                    $('#' + dataObjectListDivBlockID + ' input[type=radio]').click(function(){
                            updateTWINDChart($(this).val());
                    });
                    
                    // Check latest position and most recent dataset
                    $('#twindRadio_' + data[data.length-1].dataDashboardObjectID).trigger('click');
                    
                } else {
                    $('#' + dataObjectListDivBlockID).html('<strong>No twind Data Found</strong>');
                    $('#twind_placeholder').html('<strong>No Data Found</strong>');
                }
            }
        });
    }
    
    function updateTWINDChart(dataDashboardObjectID) {
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

                    $('#twind_placeholder').highcharts(chartOptions);
                }
            }
        });
    }
    
    getCurrentCruise();

});
    
