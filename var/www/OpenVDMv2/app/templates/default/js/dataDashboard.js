$(function () {
    'use strict';
    
    var MAPPROXY_DIR = '/mapproxy';
    
    Highcharts.setOptions({
        colors: ['#337ab7', '#5cb85c', '#d9534f', '#f0ad4e', '#606060']
    });

    var mapObjects = [],
        chartObjects = [];
    
    function updateBounds(mapObject) {
        if (mapObject['map']) {
            // Center the map based on the bounds
            var mapBoundsArray = [];
            for (var item in mapObject['mapBounds'] ){
                mapBoundsArray.push( mapObject['mapBounds'][ item ] );
            }
            
            if (mapBoundsArray.length > 0) {
                mapObject['map'].fitBounds(mapBoundsArray);
            }
        }
    }

    function initMapObject(placeholderID, objectListID) {
        
        var mapObject = [];
        
        //Build mapObject object
        mapObject['placeholderID'] = placeholderID;
        mapObject['objectListID'] = objectListID;
        mapObject['markers'] = [];
        mapObject['geoJSONLayers'] = [];
        mapObject['tmsLayers'] = [];
        mapObject['mapBounds'] = [];

        //Build the map
        mapObject['map'] = L.map(mapObject['placeholderID'], {
            maxZoom: 13,
            fullscreenControl: true,
        }).setView(L.latLng(0, 0), 2);

        //Add basemap layer, use ESRI Oceans Base Layer
        //L.esri.basemapLayer("Oceans").addTo(mapObject['map']);
        //L.esri.basemapLayer("OceansLabels").addTo(mapObject['map']);
        var worldOceanBase = L.tileLayer(window.location.origin + MAPPROXY_DIR +'/tms/1.0.0/WorldOceanBase/esri_online/{z}/{x}/{y}.png', { tms:true, zoomOffset:-1, minZoom:1 } ),
            worldOceanReference = L.tileLayer(window.location.origin + MAPPROXY_DIR +'/tms/1.0.0/WorldOceanReference/esri_online/{z}/{x}/{y}.png', { tms:true, zoomOffset:-1, minZoom:1 } );
        
        L.control.attribution().addAttribution('<a href="http://www.esri.com" target="_blank" style="border: none;">esri</a>').addTo(mapObject['map']);
        
        worldOceanBase.addTo(mapObject['map']);
        worldOceanBase.bringToBack();
        
        var baseLayers = {
        //    "World Ocean Base" : worldOceanBase
        };

        var overlays = {
            "World Ocean Reference" : worldOceanReference
        };
        
        L.control.layers(baseLayers, overlays).addTo(mapObject['map']);
        
        
        return mapObject;
    }
    
    function initChartObject(placeholderID, objectListID, dataType) {
        
        var chartObject = [];
        
        //Build mapObject object
        chartObject['placeholderID'] = placeholderID;
        chartObject['objectListID'] = objectListID;
        chartObject['dataType'] = dataType;
        return chartObject;
    }

    function mapChecked(mapObject) {
        $( '#' + mapObject['objectListID']).find(':checkbox:checked').each(function() {
            if ($(this).hasClass("lp-checkbox")) {
                addLatestPositionToMap(mapObject, $(this).val());
            } else if ($(this).hasClass("geoJSON-checkbox")) {
                //alert($(this).val());
                addGeoJSONToMap(mapObject, $(this).val());
            } else if ($(this).hasClass("tms-checkbox")) {
                //alert($(this).val());
                addTMSToMap(mapObject, $(this).val());
            }
        });        
    }
    
    function chartChecked(chartObject) {
        //alert('#' + chartObject['objectListID']);        
        //alert($( '#' + chartObject['objectListID']).length);
        //alert($( '#' + chartObject['objectListID']).find(':radio:checked').length);
        $( '#' + chartObject['objectListID']).find(':radio:checked').each(function() {
            updateChart(chartObject, $(this).val());
        }); 
    }
    
    function addLatestPositionToMap(mapObject, dataType) {
        var getVisualizerDataURL = siteRoot + 'api/dashboardData/getLatestVisualizerDataByType/' + cruiseID + '/' + dataType;
        $.getJSON(getVisualizerDataURL, function (data, status) {
            if (status === 'success' && data !== null) {
                
                if ('error' in data) {
                    $('#' + mapObject['placeholderID']).html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    //Get the last coordinate from the latest trackline
                    var lastCoordinate = data[0].features[0].geometry.coordinates[data[0].features[0].geometry.coordinates.length - 1];
                    var latestPosition = L.latLng(lastCoordinate[1], lastCoordinate[0]);
                    var bounds = new L.LatLngBounds([latestPosition]);
                    mapObject['mapBounds']['LatestPosition-' + dataType] = bounds;
                        
                    // Add marker at the last coordinate
                    mapObject['markers']['LatestPosition-' + dataType] = L.marker(latestPosition);
                    mapObject['markers']['LatestPosition-' + dataType].addTo(mapObject['map']);
                    
                    updateBounds(mapObject);
                }
            }
        });
    }

    function removeLatestPositionFromMap(mapObject, dataType) {
        mapObject['map'].removeLayer(mapObject['markers']['LatestPosition-' + dataType]);
            
        //remove the bounds and re-center/re-zoom the map
        delete mapObject['markers']['LatestPosition-' + dataType];
        
        updateBounds(mapObject);
    }

    function addGeoJSONToMap(mapObject, dataObjectJsonName) {
        var getVisualizerDataURL = siteRoot + 'api/dashboardData/getDashboardObjectVisualizerDataByJsonName/' + cruiseID + '/' + dataObjectJsonName;
        $.getJSON(getVisualizerDataURL, function (data, status) {
            if (status === 'success' && data !== null) {
                
                var placeholder = '#' + mapObject['placeholderID'];
                if ('error' in data) {
                    $(placeholder).html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    // Build the layer
                    mapObject['geoJSONLayers'][dataObjectJsonName] = L.geoJson(data[0], { style: { weight: 3 }});
                        
                    // Calculate the bounds of the layer
                    mapObject['mapBounds'][dataObjectJsonName] = mapObject['geoJSONLayers'][dataObjectJsonName].getBounds();
                        
                    // Add the layer to the map
                    mapObject['geoJSONLayers'][dataObjectJsonName].addTo(mapObject['map']);
                    
                    updateBounds(mapObject);
                }
            }
        });
    }
    
    function removeGeoJSONFromMap(mapObject, dataObjectJsonName) {
        mapObject['map'].removeLayer(mapObject['geoJSONLayers'][dataObjectJsonName]);
        delete mapObject['geoJSONLayers'][dataObjectJsonName];
            
        //remove the bounds and re-center/re-zoom the map
        delete mapObject['mapBounds'][dataObjectJsonName];
        
        updateBounds(mapObject);
    }
    
    function addTMSToMap(mapObject, tmsObjectJsonName) {
        var getDataObjectFileURL = siteRoot + 'api/dashboardData/getDashboardObjectVisualizerDataByJsonName/' + cruiseID + '/' + tmsObjectJsonName;
        $.getJSON(getDataObjectFileURL, function (data, status) {
            if (status === 'success' && data !== null) {
                
                var placeholder = '#' + mapObject['placeholderID'];
                if ('error' in data){
                    $(placeholder).html('<strong>Error: ' + data.error + '</strong>');
                } else {
                        
                    // Calculate the bounds of the layer
                    var coords = data[0]['mapBounds'].split(','),
                        southwest = L.latLng(parseFloat(coords[1]), parseFloat(coords[0])),
                        northeast = L.latLng(parseFloat(coords[3]), parseFloat(coords[2]));
                        
                    mapObject['mapBounds'][tmsObjectJsonName] = L.latLngBounds(southwest, northeast);

                    // Build the layer
                    mapObject['tmsLayers'][tmsObjectJsonName] = L.tileLayer(location.protocol + '//' + location.host + cruiseDataDir + '/' + data[0]['tileDirectory'] + '/{z}/{x}/{y}.png', {
                        tms:true,
                        bounds:L.latLngBounds(southwest, northeast),
                    });
                        
                    // Add the layer to the map
                    mapObject['tmsLayers'][tmsObjectJsonName].addTo(mapObject['map']);

                    updateBounds(mapObject);
                }
            }
        });
    }
    
    function removeTMSFromMap(mapObject, tmsObjectJsonName) {
        //remove the layer
        mapObject['map'].removeLayer(mapObject['tmsLayers'][tmsObjectJsonName]);
        delete mapObject['tmsLayers'][tmsObjectJsonName];
            
        //remove the bounds and re-center/re-zoom the map
        delete mapObject['mapBounds'][tmsObjectJsonName];
        
        updateBounds(mapObject);
    }
    
    function updateChart(chartObject, dataObjectJsonName) {
        var getVisualizerDataURL = siteRoot + 'api/dashboardData/getDashboardObjectVisualizerDataByJsonName/' + cruiseID + '/' + dataObjectJsonName;
        $.getJSON(getVisualizerDataURL, function (data, status) {
            if (status === 'success' && data !== null) {

                var placeholder = '#' + chartObject['placeholderID'];
                if ('error' in data){
                    $(placeholder).html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    var seriesData = [];
                    var yAxes = [];
                    var xAxes = [];

                    var i = 0;
                    for (i = 0; i < data.length; i++) {
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
                        if (i >= data.length / 2) {
                            yAxes[i].opposite = true;
                        }

                        //if (data[i].label === "Humidity (%)") {
                        //    yAxes[i].min = 0;
                        //    yAxes[i].max = 100;
                        //}

                        seriesData[i] = {
                            name: data[i].label +  ' (' + data[i].unit + ')',
                            yAxis: i,
                            data: data[i].data,
                            animation: false
                        };
                    }

                    var chartOptions = {
                        chart: {type: 'line' },
                        title: {text: ''},
                        tooltip: {
                            shared: true,
                            crosshairs: true,
                            xDateFormat: '%Y-%m-%d',
                            formatter: function() {
                                var toolTipStr = '<span style="font-size: 10px">Time: ' + Highcharts.dateFormat('%H:%M:%S', new Date(this.x)) + '</span>';
                                $.each(this.points, function (i) {
                                    toolTipStr += '<br/>' + '<span style="font-size: 10px; color:' + this.series.color + '">\u25CF</span><span style="font-size: 10px"> ' + data[i].label + ': ' + this.y +  ' ' + data[i].unit + '</span>';
                                });
                                return toolTipStr;
                            }
                        },
                        legend: {enabled: true},
                        xAxis: {type: 'datetime',
                                title: {text: ''},
                                dateTimeLabelFormats: {millisecond: '%H', second: '%H:%M:%S', minute: '%H:%M', hour: '%H:%M', day: '%e. %b', week: '%e. %b', month: '%b \'%y', year: '%Y'}
                               },
                        yAxis: yAxes,
                        series: seriesData
                    };

                    $(placeholder).highcharts(chartOptions);
                }
            }
        });
    }
    
    //Initialize the mapObjects
    $( '.map' ).each(function( index ) {
        var mapPlaceholderID = $( this ).attr('id');
        var tempArray = mapPlaceholderID.split("_");
        tempArray.pop();
        var objectListPlaceholderID =  tempArray.join('_') + '_objectList-placeholder';
        //alert(objectListPlaceholderID);
        mapObjects.push(initMapObject(mapPlaceholderID, objectListPlaceholderID));
    });
    
    //Initialize the chartObjects
    $( '.chart' ).each(function( index ) {
        var chartPlaceholderID = $( this ).attr('id');
        var tempArray = chartPlaceholderID.split("_");
        tempArray.pop();
        var objectListPlaceholderID =  tempArray.join('_') + '_objectList-placeholder';
        //alert(objectListPlaceholderID);
        chartObjects.push(initChartObject(chartPlaceholderID, objectListPlaceholderID));
    });
    
    //build the maps
    for(var i = 0; i < mapObjects.length; i++) {
        mapChecked(mapObjects[i]);
        setTimeout(updateBounds(mapObjects[i]), 5000);
    }
    
    //build the charts
    for(var i = 0; i < chartObjects.length; i++) {
        chartChecked(chartObjects[i]);
    }
    
    //Check for updates
    $.each(mapObjects, function(i) {
        $( '#' + mapObjects[i]['objectListID']).find(':checkbox:checked').change(function() {
            if ($(this).is(":checked")) {
                if ($(this).hasClass("lp-checkbox")) {
                    //alert($(this).val());
                    addLatestPositionToMap(mapObjects[i], $(this).val());
                } else if ($(this).hasClass("geoJSON-checkbox")) {
                    //alert($(this).val());
                    addGeoJSONToMap(mapObjects[i], $(this).val());
                } else if ($(this).hasClass("tms-checkbox")) {
                    //alert($(this).val());
                    addTMSToMap(mapObjects[i], $(this).val());
                }
            } else {
                if ($(this).hasClass("lp-checkbox")) {
                    //alert($(this).val());
                    removeLatestPositionFromMap(mapObjects[i], $(this).val());
                } else if ($(this).hasClass("geoJSON-checkbox")) {
                    //alert($(this).val());
                    removeGeoJSONFromMap(mapObjects[i], $(this).val());
                } else if ($(this).hasClass("tms-checkbox")) {
                    //alert($(this).val());
                    removeTMSFromMap(mapObjects[i], $(this).val());
                }
            }
        });
    });
    
    //Check for updates
    $.each(chartObjects, function(i) {
        $( '#' + chartObjects[i]['objectListID']).find(':radio').change(function() {
            updateChart(chartObjects[i], $(this).val());
        });
    });
});
