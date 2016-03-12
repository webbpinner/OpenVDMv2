$(function () {
    'use strict';
    
    var MAPPROXY_DIR = '/mapproxy';

    var max_values = 5;
    
    Highcharts.setOptions({
        colors: ['#337ab7', '#5cb85c', '#d9534f', '#f0ad4e', '#606060']
    });
    
    function displayLatestJSON(dataType) {
        var getVisualizerDataURL = siteRoot + 'api/dashboardData/getLatestVisualizerDataByType/' + cruiseID + '/' + dataType;
        $.getJSON(getVisualizerDataURL, function (data, status) {
            if (status === 'success' && data !== null) {
                
                var placeholder = '#' + dataType + '-placeholder';
                if (data.indexOf('error') > 0) {
                    $(placeholder).html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    var seriesData = [],
                        yAxes = [],
                        xAxes = [],
                        i = 0;
                    
                    for (i = 0; i < data.length; i++) {
                        yAxes[i] = {
                            labels: {
                                enabled: false
                            },
                            title: {
                                enabled: false
                            }
                        };
                    
                        //if (data[i].label === "Humidity (%)") {
                        //    yAxes[i].min = 0;
                        //    yAxes[i].max = 100;
                        //}
                    
                        seriesData[i] = {
                            name: data[i].label,
                            yAxis: i,
                            data: data[i].data,
                            animation: false
                        };
                    }
                
                    var chartOptions = {
                        chart: {
                            type: 'line',
                            events: {
                                click: function (e) {
                                    window.location.href = siteRoot + 'dataDashboard/customTab/' + subPages[dataType] + '#' + dataType;
                                }
                            }
                        },
                        plotOptions: {
                            series: {
                                events: {
                                    legendItemClick: function () {
                                        return false;
                                    }
                                },
                                states: {
                                    hover: {
                                        enabled: false
                                    }
                                }
                            }
                        },
                        title: {text: ''},
                        tooltip: false,
                        legend: {
                            enabled: true
                        },
                        xAxis: {
                            type: 'datetime',
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
    
        
    function displayLatestGeoJSON(dataType) {
        var getVisualizerDataURL = siteRoot + 'api/dashboardData/getLatestVisualizerDataByType/' + cruiseID + '/' + dataType;
        $.getJSON(getVisualizerDataURL, function (data, status) {
            if (status === 'success' && data !== null) {

                var placeholder = '#' + dataType + '-placeholder';
                if ('error' in data) {
                    $(placeholder).html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    //Get the last coordinate from the latest trackline
                    var lastCoordinate = data[0].features[0].geometry.coordinates[data[0].features[0].geometry.coordinates.length - 1],
                        latLng = L.latLng(lastCoordinate[1], lastCoordinate[0]);
                    
                    if (lastCoordinate[0] < 0) {
                        latLng = latLng.wrap(360, 0);
                    } else {
                        latLng = latLng.wrap();
                    }
                    
                    // Add latest trackline (GeoJSON)
                    var ggaData = L.geoJson(data[0], {
                        style: { weight: 3 },
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
                    }),
                        mapBounds = ggaData.getBounds();
                    
                    mapBounds.extend(latLng);

                    //Build the map
                    var mapdb = L.map(placeholder.split('#')[1], {
                        maxZoom: 13,
                        zoomControl: false,
                        dragging: false,
                        doubleClickZoom: false,
                        touchZoom: false,
                        scrollWheelZoom: false
                    }).fitBounds(mapBounds).zoomOut(1);
                    
                    mapdb.on('click', function(e) {
                        window.location.href = siteRoot + 'dataDashboard/customTab/' + subPages[dataType] + '#' + dataType;
                    });

                    //Add basemap layer, use ESRI Oceans Base Layer
                    //L.esri.basemapLayer("Oceans").addTo(mapdb);
                    L.tileLayer(window.location.origin + MAPPROXY_DIR +'/tms/1.0.0/WorldOceanBase/esri_online/{z}/{x}/{y}.png', { tms:true, zoomOffset:-1, minZoom:1 } ).addTo(mapdb);
                    L.control.attribution().addAttribution('<a href="http://www.esri.com" target="_blank" style="border: none;">esri</a>').addTo(mapdb);

                    // Add latest trackline (GeoJSON)
                    ggaData.addTo(mapdb);
                    
                    // Add marker at the last coordinate
                    var marker = L.marker(latLng).addTo(mapdb);
                    
                }
            }
        });
    }
    
    function displayLatestTMS(dataType) {
        var getVisualizerDataURL = siteRoot + 'api/dashboardData/getLatestVisualizerDataByType/' + cruiseID + '/' + dataType;
        $.getJSON(getVisualizerDataURL, function (data, status) {
            if (status === 'success' && data !== null) {
                
                var placeholder = '#' + dataType + '-placeholder';
                if ('error' in data) {
                    $(placeholder).html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    
                    var coords = data[0]['mapBounds'].split(','),
                            southwest = L.latLng(parseFloat(coords[1]), parseFloat(coords[0])),
                            northeast = L.latLng(parseFloat(coords[3]), parseFloat(coords[2]));
                        
                    //Build Leaflet latLng object
                    var mapBounds = L.latLngBounds(southwest, northeast);
                    var latLng = mapBounds.getCenter();

                    //Build the map
                    var mapdb = L.map(placeholder.split('#')[1], {
                        maxZoom: 9,
                        zoomControl: false,
                        dragging: false,
                        doubleClickZoom: false,
                        touchZoom: false,
                        scrollWheelZoom: false
                    });
                    
                    mapdb.on('click', function(e) {
                        window.location.href = siteRoot + 'dataDashboard/customTab/' + subPages[dataType] + '#' + dataType;
                    });

                    //Add basemap layer, use ESRI Oceans Base Layer
                    //L.esri.basemapLayer("Oceans").addTo(mapdb);
                    L.tileLayer(window.location.origin + MAPPROXY_DIR +'/tms/1.0.0/WorldOceanBase/esri_online/{z}/{x}/{y}.png', { tms:true, zoomOffset:-1, minZoom:1 } ).addTo(mapdb);
                    L.control.attribution().addAttribution('<a href="http://www.esri.com" target="_blank" style="border: none;">esri</a>').addTo(mapdb);

                    // Add latest trackline (GeoJSON)
                    L.tileLayer(location.protocol + '//' + location.host + cruiseDataDir + '/' + data[0]['tileDirectory'] + '/{z}/{x}/{y}.png', {
                        tms: true,
                        bounds:mapBounds
                    }).addTo(mapdb);
                    mapdb.fitBounds(mapBounds);
                }
            }
        });
    }

    function displayLatestData() {
        
        var i = 0;
        for (i = 0; i < geoJSONTypes.length; i++) {
            if ($('#' + geoJSONTypes[i] + '-placeholder').length) {
                displayLatestGeoJSON(geoJSONTypes[i]);
            }
        }

        for (i = 0; i < tmsTypes.length; i++) {
            if ($('#' + tmsTypes[i] + '-placeholder').length) {
                displayLatestTMS(tmsTypes[i]);
            }
        }

        for (i = 0; i < jsonTypes.length; i++) {
            if ($('#' + jsonTypes[i] + '-placeholder').length) {
                displayLatestJSON(jsonTypes[i]);
            }
        }
    }
    
    displayLatestData();
});