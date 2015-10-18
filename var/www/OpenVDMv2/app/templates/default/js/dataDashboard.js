$(function () {
    'use strict';

    var max_values = 5;
    
    var OVDM_DIR = '/OpenVDMv2';
    var MAPPROXY_DIR = '/mapproxy';
    var CruiseData_Dir = '/CruiseData';
    
    //var mapdb;
    //var latLng = null;
    
    Highcharts.setOptions({
        colors: ['#337ab7', '#5cb85c', '#d9534f', '#f0ad4e', '#606060']
    });
    
    var sensorNames = [];
    sensorNames['gga']   = 'GPS-Based Position';
    sensorNames['hdt']   = 'Heading';
    
    sensorNames['geotiff']   = 'bathymetry';

    sensorNames['met']   = 'Weather Sensor';
    
    sensorNames['tsg']   = 'Thermosalinograph';
    
    sensorNames['twind'] = 'Young Wind Sensor';

    sensorNames['svp']   = 'Sound Velocity Probe';

    var subPages = [];
    subPages['gga']   = 'position';
    
    subPages['geotiff']   = 'position';

    subPages['hdt']   = 'position';

    subPages['met']   = 'weather';
    
    subPages['twind'] = 'weather';
    
    subPages['tsg']   = 'soundVelocity';
    
    subPages['svp']   = 'soundVelocity';

    function getCurrentCruiseDB() {
        var getLastestCruiseURL = window.location.origin + OVDM_DIR + '/api/warehouse/getCruiseID';
        $.getJSON(getLastestCruiseURL, function (data, status) {
            if (status === 'success' && data !== null) {
                var latestCruise = data.cruiseID;
                
                buildGGADataObjectListDB(latestCruise, 'gga');           
                
                buildGeotiffDataObjectListDB(latestCruise, 'geotiff');

                buildHDTDataObjectListDB(latestCruise, 'hdt');           

                buildMETDataObjectListDB(latestCruise, 'met');
                
                buildTSGDataObjectListDB(latestCruise, 'tsg');
                
                buildTWINDDataObjectListDB(latestCruise, 'twind');
                
                buildSVPDataObjectListDB(latestCruise, 'svp');
            }
        });
    }

    
    function buildMETDataObjectListDB(latestCruise, dataType) {
        var getMETDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/' + dataType;
        $.getJSON(getMETDataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
//                $('#wddb-placeholder').css({ 'height': "190px" });
                if (data.length > 0) {
                    buildMETChartDB(data[data.length - 1], dataType);
                } else {
                    $('#'+ dataType + '_placeholder').html('<h3>No Data Found</h3>');
                }
            }
        });
    }
    
    function buildMETChartDB(latestDataObject, dataType) {
        var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + latestDataObject.dataDashboardObjectID;
        $.getJSON(getDataObjectFileURL, function (data, status) {
            if (status === 'success' && data !== null) {
                
                if ('error' in data) {
                    $('#' + dataType + '_placeholder').html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    var seriesData = [];
                    var yAxes = [];
                    var xAxes = [];
                
                    var i = 0;
                    for (i = 0; i < data.visualizerData.length; i++) {
                        yAxes[i] = {
                            labels: {
                                enabled: false
                            },
                            title: {
                                enabled: false
                            }
                        };
                    
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
                        chart: {
                            type: 'line',
                            events: {
                                click: function (e) {
                                    window.location.href = window.location.origin + OVDM_DIR + '/dataDashboard/' + subPages[dataType];
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
                    $('#' + dataType + '_placeholder').highcharts(chartOptions);
                }
            }
        });
    }
    
    function buildTSGDataObjectListDB(latestCruise, dataType) {
        var getTSGDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/' + dataType;
        $.getJSON(getTSGDataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
 //               $('#sddb-placeholder').css({ 'height': "190px" });
                if (data.length > 0) {
                    buildTSGChartDB(data[data.length - 1], dataType);
                } else {
                    $('#'+ dataType + '_placeholder').html('<h3>No Data Found</h3>');
                }
            }
        });
    }
    
    function buildTSGChartDB(latestDataObject, dataType) {
        var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + latestDataObject.dataDashboardObjectID;
        $.getJSON(getDataObjectFileURL, function (data, status) {
            if (status === 'success' && data !== null) {

                if ('error' in data) {
                    $('#' + dataType + '_placeholder').html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    var seriesData = [];
                    var yAxes = [];
                    var xAxes = [];

                    var i = 0;
                    for (i = 0; i < data.visualizerData.length; i++) {
                        yAxes[i] = {
                            labels: {
                                enabled: false
                            },
                            title: {
                                enabled: false
                            }
                        };

                        seriesData[i] = {
                            name: data.visualizerData[i].label,
                            yAxis: i,
                            data: data.visualizerData[i].data,
                            animation: false
                        };
                    }

                    var chartOptions = {
                        chart: {
                            type: 'line',
                            events: {
                                click: function (e) {
                                    window.location.href = window.location.origin + OVDM_DIR + '/dataDashboard/' + subPages[dataType];
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
                        tooltip: {
                            enabled: false
                        },
                        legend: {
                            enabled: true
                        },
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
    
    function buildTWINDDataObjectListDB(latestCruise, dataType) {
        var getTWINDDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/' + dataType;
        $.getJSON(getTWINDDataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
 //               $('#sddb-placeholder').css({ 'height': "190px" });
                if (data.length > 0) {
                    buildTWINDChartDB(data[data.length - 1], dataType);
                } else {
                    $('#' + dataType + '_placeholder').html('<h3>No Data Found</h3>');
                }
            }
        });
    }
    
    function buildTWINDChartDB(latestDataObject, dataType) {
        var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + latestDataObject.dataDashboardObjectID;
        $.getJSON(getDataObjectFileURL, function (data, status) {
            if (status === 'success' && data !== null) {

                if ('error' in data) {
                    $('#' + dataType + '_placeholder').html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    var seriesData = [];
                    var yAxes = [];
                    var xAxes = [];

                    var i = 0;
                    for (i = 0; i < data.visualizerData.length; i++) {
                        yAxes[i] = {
                            labels: {
                                enabled: false
                            },
                            title: {
                                enabled: false
                            }
                        };

                        seriesData[i] = {
                            name: data.visualizerData[i].label,
                            yAxis: i,
                            data: data.visualizerData[i].data,
                            animation: false
                        };
                    }

                    var chartOptions = {
                        chart: {
                            type: 'line',
                            events: {
                                click: function (e) {
                                    window.location.href = window.location.origin + OVDM_DIR + '/dataDashboard/' + subPages[dataType];
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
                        tooltip: {
                            enabled: false
                        },
                        legend: {
                            enabled: true
                        },
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
    
    function buildHDTDataObjectListDB(latestCruise, dataType) {
        var getTWINDDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/' + dataType;
        $.getJSON(getTWINDDataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
 //               $('#sddb-placeholder').css({ 'height': "190px" });
                if (data.length > 0) {
                    buildTWINDChartDB(data[data.length - 1], dataType);
                } else {
                    $('#' + dataType + '_placeholder').html('<h3>No Data Found</h3>');
                }
            }
        });
    }
    
    function buildHDTChartDB(latestDataObject, dataType) {
        var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + latestDataObject.dataDashboardObjectID;
        $.getJSON(getDataObjectFileURL, function (data, status) {
            if (status === 'success' && data !== null) {

                if ('error' in data) {
                    $('#' + dataType + '_placeholder').html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    var seriesData = [];
                    var yAxes = [];
                    var xAxes = [];

                    var i = 0;
                    for (i = 0; i < data.visualizerData.length; i++) {
                        yAxes[i] = {
                            labels: {
                                enabled: false
                            },
                            title: {
                                enabled: false
                            }
                        };

                        seriesData[i] = {
                            name: data.visualizerData[i].label,
                            yAxis: i,
                            data: data.visualizerData[i].data,
                            animation: false
                        };
                    }

                    var chartOptions = {
                        chart: {
                            type: 'line',
                            events: {
                                click: function (e) {
                                    window.location.href = window.location.origin + OVDM_DIR + '/dataDashboard/' + subPages[dataType];
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
                        tooltip: {
                            enabled: false
                        },
                        legend: {
                            enabled: true
                        },
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
    
    function buildGNSSDataObjectListDB(latestCruise, dataType) {
        var getGNSSDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/' + dataType;
        $.getJSON(getGNSSDataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
 //               $('#sddb-placeholder').css({ 'height': "190px" });
                if (data.length > 0) {
                    buildGNSSChartDB(data[data.length - 1], dataType);
                } else {
                    $('#' + dataType + '_placeholder').html('<h3>No Data Found</h3>');
                }
            }
        });
    }
    
    function buildGNSSChartDB(latestDataObject, dataType) {
        var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + latestDataObject.dataDashboardObjectID;
        $.getJSON(getDataObjectFileURL, function (data, status) {
            if (status === 'success' && data !== null) {

                if ('error' in data) {
                    $('#' + dataType + '_placeholder').html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    var seriesData = [];
                    var yAxes = [];
                    var xAxes = [];

                    var i = 0;
                    for (i = 0; i < data.visualizerData.length; i++) {
                        yAxes[i] = {
                            labels: {
                                enabled: false
                            },
                            title: {
                                enabled: false
                            }
                        };

                        seriesData[i] = {
                            name: data.visualizerData[i].label,
                            yAxis: i,
                            data: data.visualizerData[i].data,
                            animation: false
                        };
                    }

                    var chartOptions = {
                        chart: {
                            type: 'line',
                            events: {
                                click: function (e) {
                                    window.location.href = window.location.origin + OVDM_DIR + '/dataDashboard/' + subPages[dataType];
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
                        tooltip: {
                            enabled: false
                        },
                        legend: {
                            enabled: true
                        },
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
    
    function buildSVPDataObjectListDB(latestCruise, dataObjectListDivBlock) {
        var getSVPDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/svp';
        $.getJSON(getSVPDataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
 //               $('#sddb-placeholder').css({ 'height': "190px" });
                if (data.length > 0) {
                    buildSVPChartDB(data[data.length - 1]);
                } else {
                    $('#svp_placeholder').html('<h3>No Data Found</h3>');
                }
            }
        });
    }
    
    function buildSVPChartDB(latestDataObject) {
        var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + latestDataObject.dataDashboardObjectID;
        $.getJSON(getDataObjectFileURL, function (data, status) {
            if (status === 'success' && data !== null) {

                if ('error' in data) {
                    $('#svp_placeholder').html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    var seriesData = [];
                    var yAxes = [];
                    var xAxes = [];

                    var i = 0;
                    for (i = 0; i < data.visualizerData.length; i++) {
                        yAxes[i] = {
                            labels: {
                                enabled: false
                            },
                            title: {
                                enabled: false
                            }
                        };

                        seriesData[i] = {
                            name: data.visualizerData[i].label,
                            yAxis: i,
                            data: data.visualizerData[i].data,
                            animation: false
                        };
                    }

                    var chartOptions = {
                        chart: {
                            type: 'line',
                            events: {
                                click: function (e) {
                                    window.location.href = window.location.origin + OVDM_DIR + '/dataDashboard/' + subPages['svp'];
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
                        tooltip: {
                            enabled: false
                        },
                        legend: {
                            enabled: true
                        },
                        xAxis: {type: 'datetime',
                                title: {text: ''},
                                dateTimeLabelFormats: {millisecond: '%H', second: '%H:%M:%S', minute: '%H:%M', hour: '%H:%M', day: '%e. %b', week: '%e. %b', month: '%b \'%y', year: '%Y'}
                               },
                        yAxis: yAxes,
                        series: seriesData
                    };
                
                    $('#svp_placeholder').highcharts(chartOptions);
                }
            }
        });
    }
    
    function buildGGADataObjectListDB(latestCruise, dataType) {
        var getGGADataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/' + dataType;
        $.getJSON(getGGADataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
 //               $('#navdb-placeholder').css({ 'height': "190px" });
                if (data.length > 0) {
                    buildGGAMapDB(data[data.length - 1], dataType);
                } else {
                    $('#' + dataType + '_placeholder').html('<h3>No Data Found</h3>');
                }
            }
        });
    }
    
    function buildGGAMapDB(latestDataObject, dataType) {
        var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + latestDataObject.dataDashboardObjectID;
        $.getJSON(getDataObjectFileURL, function (data, status) {
            if (status === 'success' && data !== null) {
                
                if ('error' in data) {
                    $('#' + dataType + '_placeholder').html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    //Get the last coordinate from the latest trackline
                    var lastCoordinate = data.visualizerData[0].features[0].geometry.coordinates[data.visualizerData[0].features[0].geometry.coordinates.length - 1];
                    var latLng = L.latLng(lastCoordinate[1], lastCoordinate[0]);
                    
                    // Add latest trackline (GeoJSON)
                    var ggaData = L.geoJson(data.visualizerData[0]);
                    
                    var mapBounds = ggaData.getBounds();
                    mapBounds.extend(latLng);

                    //Build the map
                    var mapdb = L.map(dataType + '_placeholder', {
                        maxZoom: 13,
                        zoomControl: false,
                        dragging: false,
                        doubleClickZoom: false,
                        touchZoom: false,
                        scrollWheelZoom: false,
                        attributionControl: false
                    }).fitBounds(mapBounds).zoomOut(1);
                    
                    mapdb.on('click', function(e) {
                        window.location.href = window.location.origin + OVDM_DIR + '/dataDashboard/' + subPages[dataType];
                    });

                    //Add basemap layer, use ESRI Oceans Base Layer
                    L.tileLayer(window.location.origin + MAPPROXY_DIR +'/tms/1.0.0/WorldOceanBase/esri_online/{z}/{x}/{y}.png', { tms:true, zoomOffset:-1, minZoom:1 } ).addTo(mapdb);
                    L.control.attribution().addAttribution('<a href="http://www.esri.com" target="_blank" style="border: none;">esri</a>').addTo(mapdb);


                    // Add latest trackline (GeoJSON)
                    L.geoJson(data.visualizerData[0]).addTo(mapdb);
                    
                    // Add marker at the last coordinate
                    var marker = L.marker(latLng).addTo(mapdb);
                    
                }
            }
        });
    }

    function buildGeotiffDataObjectListDB(latestCruise, dataType) {
        var getGeotiffDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/' + dataType;
        $.getJSON(getGeotiffDataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
 //               $('#navdb-placeholder').css({ 'height': "190px" });
                if (data.length > 0) {
                    buildGeotiffMapDB(data[data.length - 1], dataType);
                } else {
                    $('#'+ dataType +'_placeholder').html('<h3>No Data Found</h3>');
                }
            }
        });
    }
    
    function buildGeotiffMapDB(latestDataObject, dataType) {
        var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + latestDataObject.dataDashboardObjectID;
        $.getJSON(getDataObjectFileURL, function (data, status) {
            if (status === 'success' && data !== null) {
                
                if ('error' in data) {
                    $('#'+ dataType +'_placeholder').html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    
                    var coords = data.visualizerData[0]['mapBounds'].split(','),
                            southwest = L.latLng(parseFloat(coords[1]), parseFloat(coords[0])),
                            northeast = L.latLng(parseFloat(coords[3]), parseFloat(coords[2]));
                        
                    //Build Leaflet latLng object
                    var mapBounds = L.latLngBounds(southwest, northeast);
                    var latLng = mapBounds.getCenter();

                    //Build the map
                    var mapdb = L.map(dataType + '_placeholder', {
                        maxZoom: 9,
                        zoomControl: false,
                        dragging: false,
                        doubleClickZoom: false,
                        touchZoom: false,
                        scrollWheelZoom: false,
                        attributionControl: false
                    });
                    
                    mapdb.on('click', function(e) {
                        window.location.href = window.location.origin + OVDM_DIR + '/dataDashboard/' + subPages[dataType];
                    });

                    //Add basemap layer, use ESRI Oceans Base Layer
                    L.tileLayer(window.location.origin + MAPPROXY_DIR +'/tms/1.0.0/WorldOceanBase/esri_online/{z}/{x}/{y}.png', { tms:true, zoomOffset:-1, minZoom:1 } ).addTo(mapdb);
                    L.control.attribution().addAttribution('<a href="http://www.esri.com" target="_blank" style="border: none;">esri</a>').addTo(mapdb);

                    // Add latest trackline (GeoJSON)
                    L.tileLayer(location.protocol + '//' + location.host + CruiseData_Dir + '/' + data.visualizerData[0]['tileDirectory'] + '/{z}/{x}/{y}.png', {
                            tms:true,
                            bounds:mapBounds
                        }
                    ).addTo(mapdb);
                    mapdb.fitBounds(mapBounds);
                }
            }
        });
    }

    getCurrentCruiseDB();
});
    
