$(function () {
    'use strict';

    var OVDM_DIR = '/OpenVDMv2';
    var CruiseData_Dir = '/CruiseData';
    
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
                buildGGADataObjectList(latestCruise, 'gga_objectList');
                buildMBGeoTiffDataObjectList(latestCruise, 'geotiff_objectList');            

            }
        });
    }
    
    function buildGGADataObjectList(latestCruise, dataObjectListDivBlockID) {
        var getGGADataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/gga';
        $.getJSON(getGGADataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
                if (data.length > 0) {
                    var f = document.createElement("form");
                    f.setAttribute("id", dataObjectListDivBlockID);
                    
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
                    
                    var fl = document.createElement("label");
                    fl.innerHTML = "gga files";
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
                    
                    $('#' + dataObjectListDivBlockID).replaceWith(f);
                    
                    $('#' + dataObjectListDivBlockID + ' input[type=checkbox]').click(function(){
                        if($(this).attr('id') == 'checkbox_rp') {
                            updateRecentPosition($(this).attr('value'), this.checked);
                        } else {
                            updateGGAMap($(this).attr('value'), this.checked);
                        }
                    });
                    
                    // Check latest position and most recent dataset
                    $('#checkbox_rp').trigger('click');
                    $('#checkbox_' + data[data.length-1].dataDashboardObjectID).trigger('click');
                    
                } else {
                    $('#' + dataObjectListDivBlockID).html('<strong>No gga Data Found</strong>');
                }
            }
        });
    }
    
    function buildMBGeoTiffDataObjectList(latestCruise, dataObjectListDivBlockID) {
        var getMBGeoTifDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/geotiff';
        $.getJSON(getMBGeoTifDataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
                if (data.length > 0) {
                    var f = document.createElement("form");
                    f.setAttribute("id", dataObjectListDivBlockID);
                    
                    var fl = document.createElement("label");
                    fl.innerHTML = "geotiff files";
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
                    
                    $('#' + dataObjectListDivBlockID).replaceWith(f);
                    
                    $('#' + dataObjectListDivBlockID + ' input[type=checkbox]').click(function(){
                        updateGeotiffMap($(this).attr('value'), this.checked);
                    });
                    
                    // Check most recent dataset
                    $('#checkbox_' + data[data.length-1].dataDashboardObjectID).trigger('click');
                    
                } else {
                    $('#' + dataObjectListDivBlockID).html('<strong>No geotiff Data Found</strong>');
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
                        $('#gga_placeholder').html('<strong>Error: ' + data[0].error + '</strong>');
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
                        $('#gga_placeholder').html('<strong>Error: ' + data.error + '</strong>');
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
                        $('#gga_placeholder').html('<strong>Error: ' + data.error + '</strong>');
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
        }).setView(latLng, 2);

        //Add basemap layer, use ESRI Oceans Base Layer
        L.esri.basemapLayer("Oceans").addTo(map);
    }

    // Build Blank Map
    buildGGAMap('gga_placeholder')
    
    // Build Object Lists, update Map
    getCurrentCruise();
    
});
    
