$(function () {
    'use strict';

    var OVDM_DIR = '/OpenVDMv2';
    var MAPPROXY_DIR = '/mapproxy';
    var CruiseData_Dir = '/CruiseData';
    
    Highcharts.setOptions({
        colors: ['#337ab7', '#5cb85c', '#d9534f', '#f0ad4e', '#606060']
    });
    
    var map = null;
    var recentPosition = null;

    var geoJsonLayers = [];
    var tileLayers = [];
    var mapBounds = [];
    
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
                buildGGADataObjectList(latestCruise, 'gga', true);

                buildMBGeoTiffDataObjectList(latestCruise, 'geotiff');            
                
                buildHDTDataObjectList(latestCruise, 'hdt');

            }
        });
    }
    
    function buildGGADataObjectList(latestCruise, dataType, useForRecentPosition) {
        var getGGADataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/' + dataType;
        $.getJSON(getGGADataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
                if (data.length > 0) {
                    var f = document.createElement("form");
                    f.setAttribute("id", dataType + '_objectList');
                    
                    if (useForRecentPosition) {
                        var rpd = document.createElement("div");
                        rpd.setAttribute("class","checkbox");
                        var rpl = document.createElement("label");
                        var rpcb = document.createElement("input");
                        rpcb.setAttribute("type", "checkbox");
                        rpcb.setAttribute("id", "checkbox_rp");
                        rpcb.setAttribute("value", data[data.length-1].dataDashboardObjectID);
                        rpl.appendChild(rpcb);
                        rpl.innerHTML = rpl.innerHTML + 'Recent Position';
                        rpd.appendChild(rpl);
                        f.appendChild(rpd);
                    }
                    
                    var fl = document.createElement("label");
                    fl.innerHTML = dataType + " files";
                    f.appendChild(fl);

                    var r = document.createElement("div");
                    r.setAttribute("class", "row");

                    var cols = [document.createElement("div"), document.createElement("div"), document.createElement("div"), document.createElement("div")];
                    cols[0].setAttribute("class", "col-lg-3 col-md-4 col-sm-6");
                    cols[1].setAttribute("class", "col-lg-3 col-md-4 col-sm-6");
                    cols[2].setAttribute("class", "col-lg-3 col-md-4 col-sm-6");
                    cols[3].setAttribute("class", "col-lg-3 col-md-4 col-sm-6");
                    
                    for (var i = data.length-1, row = 0; i >= 0; i--, row++) {
                        var d = document.createElement("div");
                        d.setAttribute("class","checkbox")
                        var l = document.createElement("label");
                        var cb = document.createElement("input");
                        cb.setAttribute("type", "checkbox");
                        cb.setAttribute("id", "checkbox_" + data[i].dataDashboardObjectID);
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

                    f.appendChild(r);
                    
                    $('#' + dataType + "_objectList").replaceWith(f);
                    
                    $('#' + dataType + "_objectList" + ' input[type=checkbox]').click(function(){
                        if($(this).attr('id') == 'checkbox_rp') {
                            updateRecentPosition($(this).attr('value'), this.checked);
                        } else {
                            updateGGAMap($(this).attr('value'), this.checked);
                        }
                    });
                    
                    // Check latest position and most recent dataset
                    if (useForRecentPosition) {
                        $('#checkbox_rp').trigger('click');
                    }
                    
                    $('#checkbox_' + data[data.length-1].dataDashboardObjectID).trigger('click');
                    
                } else {
                    $('#' + dataType + "_objectList").html('<strong>No gga Data Found</strong>');
                }
            }
        });
    }
    
    function buildMBGeoTiffDataObjectList(latestCruise, dataType) {
        var getMBGeoTifDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/' + dataType;
        $.getJSON(getMBGeoTifDataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
                if (data.length > 0) {
                    var f = document.createElement("form");
                    f.setAttribute("id", dataType + "_objectList");
                    
                    var fl = document.createElement("label");
                    fl.innerHTML = dataType + " files";
                    f.appendChild(fl);

                    var r = document.createElement("div");
                    r.setAttribute("class", "row");

                    var cols = [document.createElement("div"), document.createElement("div"), document.createElement("div"), document.createElement("div")];
                    cols[0].setAttribute("class", "col-lg-3 col-md-4 col-sm-6");
                    cols[1].setAttribute("class", "col-lg-3 col-md-4 col-sm-6");
                    cols[2].setAttribute("class", "col-lg-3 col-md-4 col-sm-6");
                    cols[3].setAttribute("class", "col-lg-3 col-md-4 col-sm-6");
                    
                    for (var i = data.length-1, row = 0; i >= 0; i--, row++) {
                        var d = document.createElement("div");
                        d.setAttribute("class","checkbox")
                        var l = document.createElement("label");
                        var cb = document.createElement("input");
                        cb.setAttribute("type", "checkbox");
                        cb.setAttribute("id", "checkbox_" + data[i].dataDashboardObjectID);
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

                    f.appendChild(r);
                    
                    $('#' + dataType + "_objectList").replaceWith(f);
                    
                    $('#' + dataType + "_objectList" + ' input[type=checkbox]').click(function(){
                        updateGeotiffMap($(this).attr('value'), this.checked);
                    });
                    
                    // Check most recent dataset
                    $('#checkbox_' + data[data.length-1].dataDashboardObjectID).trigger('click');
                    
                } else {
                    $('#' + dataType + "_objectList").html('<strong>No geotiff Data Found</strong>');
                }
            }
        });
    }

    function updateRecentPosition(ggaObjectID, checkStatus) {
        
        if(checkStatus) {
            var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + ggaObjectID;
            $.getJSON(getDataObjectFileURL, function (data, status) {
                if (status === 'success' && data !== null) {
                    if ('error' in data){
                        $('#map_placeholder').html('<strong>Error: ' + data[0].error + '</strong>');
                    } else {
                        //Get the last coordinate from the latest trackline
                        var lastCoordinate = data.visualizerData[0].features[0].geometry.coordinates[data.visualizerData[0].features[0].geometry.coordinates.length - 1];
                        var latLng = L.latLng(lastCoordinate[1], lastCoordinate[0]);
                        
                        // Add a marker to the last coordinate
                        recentPosition = L.marker(latLng);

                        // Center the map based on the bounds
                        recentPosition.addTo(map);
                        map.setView(latLng);

                    }
                }
            });
        } else {
            //remove the marker
            map.removeLayer(recentPosition);
        }
    }
    
    function updateGGAMap(ggaObjectID, checkStatus) {
        
        if(checkStatus) {
            var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + ggaObjectID;
            $.getJSON(getDataObjectFileURL, function (data, status) {
                if (status === 'success' && data !== null) {
                    if ('error' in data){
                        $('#map_placeholder').html('<strong>Error: ' + data.error + '</strong>');
                    } else {
                        
                        // Build the layer
                        geoJsonLayers[ggaObjectID] = L.geoJson(data.visualizerData[0], { style: { weight: 3 }});
                        
                        // Calculate the bounds of the layer
                        mapBounds[ggaObjectID] = geoJsonLayers[ggaObjectID].getBounds();
                        
                        // Add the layer to the map
                        geoJsonLayers[ggaObjectID].addTo(map);

                        // Center the map based on the bounds
                        map.fitBounds(mapBounds);

                    }
                }
            });
        } else {
            //remove the layer
            map.removeLayer(geoJsonLayers[ggaObjectID]);
            delete geoJsonLayers[ggaObjectID];
            
            //remove the bounds and re-center/re-zoom the map
            delete mapBounds[ggaObjectID];
            map.fitBounds(mapBounds);
        }
    }
    
    function updateGeotiffMap(geotiffObjectID, checkStatus) {
        
        if(checkStatus) {
            var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + geotiffObjectID;
            $.getJSON(getDataObjectFileURL, function (data, status) {
                if (status === 'success' && data !== null) {
                    if ('error' in data){
                        $('#map_placeholder').html('<strong>Error: ' + data.error + '</strong>');
                    } else {
                        
                        // Calculate the bounds of the layer
                        var coords = data.visualizerData[0]['mapBounds'].split(','),
                            southwest = L.latLng(parseFloat(coords[1]), parseFloat(coords[0])),
                            northeast = L.latLng(parseFloat(coords[3]), parseFloat(coords[2]));
                        
                        mapBounds[geotiffObjectID] = L.latLngBounds(southwest, northeast);
                        
                        
                        //L.tileLayer('http://' + '192.168.1.6' + CruiseData_Dir + '/CS1505/OpenVDM/DashboardData/EM302/proc/' + data[0]['label'] + '/{z}/{x}/{y}.png', {tms:true}).addTo(map);
                        // Build the layer
                        tileLayers[geotiffObjectID] = L.tileLayer(location.protocol + '//' + location.host + CruiseData_Dir + '/' + data.visualizerData[0]['tileDirectory'] + '/{z}/{x}/{y}.png', {
                                tms:true,
                                bounds:mapBounds,
                            }
                        );
                        
                        // Add the layer to the map
                        tileLayers[geotiffObjectID].addTo(map);
                        
                        // Center the map based on the bounds
                        map.fitBounds(mapBounds);

                    }
                }
            });
        } else {
            //remove the layer
            map.removeLayer(tileLayers[geotiffObjectID]);
            delete tileLayers[geotiffObjectID];
            
            //remove the bounds and re-center/re-zoom the map
            delete mapBounds[geotiffObjectID];
            map.fitBounds(mapBounds);
        }
    }
    
    function buildGGAMap(divBlockID) {
        //Build Leaflet latLng object
        var latLng = L.latLng(0, 0);
        recentPosition = null

        //Build the map
        map = L.map(divBlockID, {
            maxZoom: 13,
            fullscreenControl: true,
            attributionControl: false
        }).setView(latLng, 2);

        //Add basemap layer, use ESRI Oceans Base Layer        
        var worldOceanBase = L.tileLayer(window.location.origin + MAPPROXY_DIR +'/tms/1.0.0/WorldOceanBase/esri_online/{z}/{x}/{y}.png', { tms:true, zoomOffset:-1, minZoom:1 } ),
            worldOceanReference = L.tileLayer(window.location.origin + MAPPROXY_DIR +'/tms/1.0.0/WorldOceanReference/esri_online/{z}/{x}/{y}.png', { tms:true, zoomOffset:-1, minZoom:1 } );
        
        L.control.attribution().addAttribution('<a href="http://www.esri.com" target="_blank" style="border: none;">esri</a>').addTo(map);
        
        worldOceanBase.addTo(map);
        worldOceanBase.bringToBack();
        
        var baseLayers = {
        //    "World Ocean Base" : worldOceanBase
        };

        var overlays = {
            "World Ocean Reference" : worldOceanReference
        };
        
        L.control.layers(baseLayers, overlays).addTo(map);

    }
    
    function buildHDTDataObjectList(latestCruise, dataType) {
        var getHDTDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/' + dataType;
        $.getJSON(getHDTDataObjectListURL, function (data, status) {
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
                            updateHDTChart($(this).val(), dataType);
                    });
                    
                    // Check latest position and most recent dataset
                    $('#' + dataType + 'Radio_' + data[data.length-1].dataDashboardObjectID).trigger('click');
                    
                    //buildGGAMap(data[data.length - 1]);
                } else {
                    $('#' + dataType + '_objectList').html('<strong>No ' + dataType + ' Data Found</strong>');
                    $('#' + dataType + '_placeholder').html('<strong>No Data Found</strong>');
                }
            }
        });
    }
    
    function updateHDTChart(dataDashboardObjectID, dataType) {
        var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + dataDashboardObjectID;
        $.getJSON(getDataObjectFileURL, function (data, status) {
            if (status === 'success' && data !== null) {

                if ('error' in data){
                    $('#' + dataDashboardObjectID).html('<strong>Error: ' + data.visualizerData[0].error + '</strong>');
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

                        //if (data.visualizerData[i].label === "Humidity (%)") {
                        //    yAxes[i].min = 0;
                        //    yAxes[i].max = 100;
                        //}

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
    
    function buildGNSSDataObjectList(latestCruise, dataType) {
        var getGNSSDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/' + dataType;
        $.getJSON(getGNSSDataObjectListURL, function (data, status) {
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
                            updateGNSSChart($(this).val(), dataType);
                    });
                    
                    // Check latest position and most recent dataset
                    $('#' + dataType + 'Radio_' + data[data.length-1].dataDashboardObjectID).trigger('click');
                    
                    //buildGGAMap(data[data.length - 1]);
                } else {
                    $('#' + dataType + '_objectList').html('<strong>No ' + dataType + ' Data Found</strong>');
                    $('#' + dataType + '_placeholder').html('<strong>No Data Found</strong>');
                }
            }
        });
    }
    
    function updateGNSSChart(dataDashboardObjectID, dataType) {
        var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + dataDashboardObjectID;
        $.getJSON(getDataObjectFileURL, function (data, status) {
            if (status === 'success' && data !== null) {

                if ('error' in data){
                    $('#' + dataDashboardObjectID).html('<strong>Error: ' + data.visualizerData[0].error + '</strong>');
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

                        //if (data.visualizerData[i].label === "Humidity (%)") {
                        //    yAxes[i].min = 0;
                        //    yAxes[i].max = 100;
                        //}

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

    // Build Blank Map
    buildGGAMap('map_placeholder')
    
    // Build Object Lists, update Map
    getCurrentCruise();
    
});
    
