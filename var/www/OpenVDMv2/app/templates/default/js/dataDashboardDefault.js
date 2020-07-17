$(function () {
    'use strict';
    
    var MAPPROXY_DIR = '/mapproxy';
    
    Highcharts.setOptions({
        colors: ['#337ab7', '#5cb85c', '#d9534f', '#f0ad4e', '#606060']
    });
    
    var chartHeight = 200;

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
            //maxZoom: 13,
            fullscreenControl: true,
            //timeDimension: true,
//            timeDimensionControl: true,
        }).setView(L.latLng(0, 0), 2);

        //Add basemap layer, use ESRI Oceans Base Layer
        //var worldOceanBase = L.esri.basemapLayer('Oceans'),
        //    worldOceanReference = L.esri.basemapLayer('OceansLabels'),
        //    gmrtBase = L.tileLayer.wms('http://gmrt.marine-geo.org/cgi-bin/mapserv?map=/public/mgg/web/gmrt.marine-geo.org/htdocs/services/map/wms_merc.map', {
        //        layers: 'topo',
        //        transparent: true,
        //        //format: 'image/png',
        //        version: '1.1.1',
        //        crs: L.CRS.EPSG4326,
        //        attribution: '<a href="http://www.marine-geo.org/portals/gmrt/" target="_blank">GMRT</a>'
        //    });
        
        var worldOceanBase = L.tileLayer(window.location.origin + MAPPROXY_DIR +'/tms/1.0.0/WorldOceanBase/EPSG900913/{z}/{x}/{y}.png', {
                tms:true,
                zoomOffset:-1,
                minZoom:1,
                maxNativeZoom:9,
                attribution: '<a href="http://www.esri.com" target="_blank" style="border: none;">esri</a>'
            }),
            worldOceanReference = L.tileLayer(window.location.origin + MAPPROXY_DIR +'/tms/1.0.0/WorldOceanReference/EPSG900913/{z}/{x}/{y}.png', {
                tms:true,
                zoomOffset:-1,
                minZoom:1,
                maxNativeZoom:9,
                attribution: '<a href="http://www.esri.com" target="_blank" style="border: none;">esri</a>'
            }),
	        gmrtBase = L.tileLayer(window.location.origin + MAPPROXY_DIR +'/tms/1.0.0/GMRTBase/EPSG900913/{z}/{x}/{y}.png', {
                tms:true,
                zoomOffset:-1,
                minZoom:1,
                attribution: '<a href="http://www.marine-geo.org/portals/gmrt/" target="_blank">GMRT</a>'
            });
        
        worldOceanBase.addTo(mapObject['map']);
        worldOceanBase.bringToBack();
        worldOceanReference.addTo(mapObject['map']);
        
        var baseLayers = {
            "World Ocean Base" : worldOceanBase,
            "GMRT Base" : gmrtBase
        };

        var overlays = {
            "World Ocean Reference" : worldOceanReference
        };
        
        L.control.layers(baseLayers, overlays).addTo(mapObject['map']);

	// start of TimeDimension manual instantiation
	//var timeDimension = new L.TimeDimension({
	//        period: "PT1M",
	//    });
	// helper to share the timeDimension object between all layers
	//mapObject['map'].timeDimension = timeDimension;

	// otherwise you have to set the 'timeDimension' option on all layers.
        //var timeDimensionControlOptions = {
            //player:        player,
            //timeDimension: timeDimension,
            //position:      'bottomleft',
            //autoPlay:      true,
            //minSpeed:      1,
            //speedStep:     0.5,
            //maxSpeed:      15,
            //timeSliderDragUpdate: true
            //'backwardButton': false,
            //'playButton': false,
            //'forwardButton': false,
            //'speedSlider': false
        //};

        //var timeDimensionControl = new L.Control.TimeDimension(timeDimensionControlOptions);
        //mapObject['map'].addControl(timeDimensionControl);
        
        
        return mapObject;
    }
    
    function initChartObject(placeholderID, objectListID, dataType) {
        
        var chartObject = [];
        
        //Build chartObject object
        chartObject['placeholderID'] = placeholderID;
        chartObject['objectListID'] = objectListID;
        var tempArray = chartObject['placeholderID'].split("_");
        tempArray.pop();
        chartObject['dataType'] = tempArray.join('_');
        chartObject['expanded'] = false; //chartHeight;
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
            if ($(this).hasClass( "json-reversed-y-radio" )) {
                updateChart(chartObjects[i], $(this).val(), true);
            } else {
                updateChart(chartObjects[i], $(this).val());
            }
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
                    var lastCoordinate = data[0].features[data[0].features.length - 1].geometry.coordinates[data[0].features[data[0].features.length - 1].geometry.coordinates.length - 1];
                    var latestPosition = L.latLng(lastCoordinate[1], lastCoordinate[0]);
                    
                    if (lastCoordinate[0] < 0) {
                        latestPosition = latestPosition.wrap(360, 0);
                    } else {
                        latestPosition = latestPosition.wrap();
                    }
                    
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
                    //mapObject['geoJSONLayers'][dataObjectJsonName] = L.timeDimension.layer.geoJson(data[0], {
                    mapObject['geoJSONLayers'][dataObjectJsonName] = L.geoJson(data[0], {
                        style: { weight: 3 },
                        //udpateTimeDimension: true,
                        addLastPoint: true,
                        waitForReady: true,
                        coordsToLatLng: function (coords) {
                            var longitude = coords[0],
                                latitude = coords[1];

                            var latlng = L.latLng(latitude, longitude);

                            if (longitude < 0) {
                                return latlng.wrap(360, 0);
                            } else {
                                return latlng.wrap();
                            }
                        }                                                                    
                    });
                        
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

                    // Build the layer
                    mapObject['tmsLayers'][tmsObjectJsonName] = L.tileLayer(location.protocol + '//' + location.host + cruiseDataDir + '/' + data[0]['tileDirectory'] + '/{z}/{x}/{y}.png', {
                        tms:true,
                        bounds:L.latLngBounds(southwest, northeast),
                        zIndex: 10
                    });
                    
                    if (parseFloat(coords[0]) < 0) {
                        southwest = southwest.wrap(360, 0);
                    } else {
                        southwest = southwest.wrap();
                    }
                    
                    if (parseFloat(coords[2]) < 0) {
                        northeast = northeast.wrap(360, 0);
                    } else {
                        northeast = northeast.wrap();
                    }
                    
                    mapObject['mapBounds'][tmsObjectJsonName] = L.latLngBounds(southwest, northeast);
                    //console.log(mapObject['mapBounds'][tmsObjectJsonName]);
                        
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
    
    function updateChart(chartObject, dataObjectJsonName, reversedY) {
        var reversedY = reversedY || false;
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

                        if (reversedY) {
                            yAxes[i].reversed = true;
                        }

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
                                var toolTipStr = '<span style="font-size: 10px">Time: ' + Highcharts.dateFormat('%b %e %Y - %H:%M:%S', this.x) + '</span>';
                                $.each(this.points, function (i) {
                                    toolTipStr += '<br/>' + '<span style="font-size: 10px; color:' + this.series.color + '">\u25CF</span><span style="font-size: 10px"> ' + this.series.name + ': ' + this.y +  ' </span>';
                                });
                                return toolTipStr;
                            }
                        },
                        legend: {enabled: true},
                        xAxis: {type: 'datetime',
                                title: {text: ''},
                                dateTimeLabelFormats: {millisecond: '%H', second: '%H:%M:%S', minute: '%H:%M', hour: '%H:%M', day: '%b %e', week: '%b %e', month: '%b \'%y', year: '%Y'}
                               },
                        yAxis: yAxes,
                        series: seriesData,
                        //exporting: {
                        //    buttons: {
                        //            customButton: {
                        //            text: 'Test',
                        //            symbol: 'text:\uf065',
                        //            symbolFill: '666',
                        //            symbolStroke: 'none',
                        //            symbolX: '14',
                        //            symbolY: '9',
                        //            onclick: function () {
                        //                alert('You pressed the button!');
                        //            }
                        //        }
                        //    }
                        //}
                    };

//                    console.log('chartOptions:', chartOptions)
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
        
        $( '#' + mapObjects[i]['objectListID']).find('.clearAll').click(function() {
            var row = $(this).closest("div.row")
            $.each(row.find(':checkbox'), function () {
                if ($(this).prop('checked')) {
                    $(this).prop('checked', false); // Unchecks it
                    $(this).trigger('change');
                }
            });
        });

        $( '#' + mapObjects[i]['objectListID']).find('.selectAll').click(function() {
            var row = $(this).closest("div.row")
            $.each(row.find(':checkbox'), function () {
                if (!$(this).prop('checked')) {
                    $(this).prop('checked', true); // Unchecks it
                    $(this).trigger('change');
                }
            });
        });

    });
    
    //Check for updates
    $.each(chartObjects, function(i) {
        $( '#' + chartObjects[i]['objectListID']).find(':radio').change(function() {
	    if ($(this).hasClass( "json-reversed-y-radio" )) {
                updateChart(chartObjects[i], $(this).val(), true);
            } else {
                updateChart(chartObjects[i], $(this).val());
            }
        });
        
        $( '#' + chartObjects[i]['dataType'] + '_expand-btn').click(function() {
            var chart = $('#' + chartObjects[i]['placeholderID']).highcharts();
            
            $('#' + chartObjects[i]['placeholderID']).height(chartObjects[i]['expanded'] ? 200 : 500);
            $('#' + chartObjects[i]['placeholderID']).highcharts().reflow();
            $(this).removeClass(chartObjects[i]['expanded'] ? 'fa-compress' : 'fa-expand');
            $(this).addClass(chartObjects[i]['expanded'] ? 'fa-expand' : 'fa-compress');
            chartObjects[i]['expanded'] = !chartObjects[i]['expanded'];
        });
    });
    
    

});
