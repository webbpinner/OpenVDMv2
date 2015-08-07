$(function () {
    'use strict';

    var max_values = 5;
    
    var OVDM_DIR = '/OpenVDMv2';
    var CruiseData_Dir = '/CruiseData';
    
    //var mapdb;
    //var latLng = null;
    
    Highcharts.setOptions({
        colors: ['#337ab7', '#5cb85c', '#d9534f', '#f0ad4e', '#606060']
    });
    
    var sensorNames = [];
    sensorNames['gga']   = 'GPS-Based Position';
    sensorNames['geotiff']   = 'bathymetry';
    sensorNames['met']   = 'Weather Sensor';
    sensorNames['twind'] = 'Young Wind Sensor';
    sensorNames['tsg']   = 'Thermosalinograph';
    sensorNames['svp']   = 'Sound Velocity Probe';

    var subPages = [];
    subPages['gga']   = 'position';
    subPages['geotiff']   = 'position';
    subPages['met']   = 'weather';
    subPages['twind'] = 'weather';
    subPages['tsg']   = 'soundVelocity';
    subPages['svp']   = 'soundVelocity';

    
    function getCurrentCruiseDB() {
        var getLastestCruiseURL = window.location.origin + OVDM_DIR + '/api/warehouse/getCruiseID';
        $.getJSON(getLastestCruiseURL, function (data, status) {
            if (status === 'success' && data !== null) {
                var latestCruise = data.cruiseID;
                buildMETDataObjectListDB(latestCruise, '#objectList');
                buildTSGDataObjectListDB(latestCruise, '#objectList');
                buildTWINDDataObjectListDB(latestCruise, '#objectList');
                buildSVPDataObjectListDB(latestCruise, '#objectList');
                buildGGADataObjectListDB(latestCruise, '#objectList');           
                buildGeotiffDataObjectListDB(latestCruise, '#objectList');           
            }
        });
    }

    
    function buildMETDataObjectListDB(latestCruise, dataObjectListDivBlock) {
        var getMETDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/met';
        $.getJSON(getMETDataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
//                $('#wddb-placeholder').css({ 'height': "190px" });
                if (data.length > 0) {
                    buildMETChartDB(data[data.length - 1]);
                } else {
                    $('#met_placeholder').html('<h3>No Data Found</h3>');
                }
            }
        });
    }
    
    function buildMETChartDB(latestDataObject) {
        var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + latestDataObject.dataDashboardObjectID;
        $.getJSON(getDataObjectFileURL, function (data, status) {
            if (status === 'success' && data !== null) {
                
                if ('error' in data) {
                    $('#met_placeholder').html('<strong>Error: ' + data.error + '</strong>');
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
                                    window.location.href = window.location.origin + OVDM_DIR + '/dataDashboard/' + subPages['met'];
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
                    $('#met_placeholder').highcharts(chartOptions);
                }
            }
        });
    }
    
    function buildTSGDataObjectListDB(latestCruise, dataObjectListDivBlock) {
        var getTSGDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/tsg';
        $.getJSON(getTSGDataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
 //               $('#sddb-placeholder').css({ 'height': "190px" });
                if (data.length > 0) {
                    buildTSGChartDB(data[data.length - 1]);
                } else {
                    $('#tsg_placeholder').html('<h3>No Data Found</h3>');
                }
            }
        });
    }
    
    function buildTSGChartDB(latestDataObject) {
        var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + latestDataObject.dataDashboardObjectID;
        $.getJSON(getDataObjectFileURL, function (data, status) {
            if (status === 'success' && data !== null) {

                if ('error' in data) {
                    $('#tsg_placeholder').html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    //Drop int. temp to simplify chart
                    data.visualizerData.shift();

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
                                    window.location.href = window.location.origin + OVDM_DIR + '/dataDashboard/' + subPages['tsg'];
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

                    $('#tsg_placeholder').highcharts(chartOptions);
                }
            }
        });
    }
    
    function buildTWINDDataObjectListDB(latestCruise, dataObjectListDivBlock) {
        var getTWINDDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/twind';
        $.getJSON(getTWINDDataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
 //               $('#sddb-placeholder').css({ 'height': "190px" });
                if (data.length > 0) {
                    buildTWINDChartDB(data[data.length - 1]);
                } else {
                    $('#twind_placeholder').html('<h3>No Data Found</h3>');
                }
            }
        });
    }
    
    function buildTWINDChartDB(latestDataObject) {
        var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + latestDataObject.dataDashboardObjectID;
        $.getJSON(getDataObjectFileURL, function (data, status) {
            if (status === 'success' && data !== null) {

                if ('error' in data) {
                    $('#twind_placeholder').html('<strong>Error: ' + data.error + '</strong>');
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
                                    window.location.href = window.location.origin + OVDM_DIR + '/dataDashboard/' + subPages['twind'];
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

                    $('#twind_placeholder').highcharts(chartOptions);
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
    
    function buildGGADataObjectListDB(latestCruise, dataObjectListDivBlock) {
        var getGGADataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/gga';
        $.getJSON(getGGADataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
 //               $('#navdb-placeholder').css({ 'height': "190px" });
                if (data.length > 0) {
                    buildGGAMapDB(data[data.length - 1]);
                } else {
                    $('#gga_placeholder').html('<h3>No Data Found</h3>');
                }
            }
        });
    }
    
    function buildGGAMapDB(latestDataObject) {
        var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + latestDataObject.dataDashboardObjectID;
        $.getJSON(getDataObjectFileURL, function (data, status) {
            if (status === 'success' && data !== null) {
                
                if ('error' in data) {
                    $('#gga_placeholder').html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    //Get the last coordinate from the latest trackline
                    var lastCoordinate = data.visualizerData[0].features[0].geometry.coordinates[data.visualizerData[0].features[0].geometry.coordinates.length - 1];
                    var latLng = L.latLng(lastCoordinate[1], lastCoordinate[0]);
                    
                    // Add latest trackline (GeoJSON)
                    var ggaData = L.geoJson(data.visualizerData[0]);
                    
                    var mapBounds = ggaData.getBounds();
                    mapBounds.extend(latLng);

                    //Build the map
                    var mapdb = L.map('gga_placeholder', {
                        maxZoom: 13,
                        zoomControl: false,
                        dragging: false,
                        doubleClickZoom: false,
                        touchZoom: false,
                        scrollWheelZoom: false
                    }).fitBounds(mapBounds).zoomOut(1);
                    
                    mapdb.on('click', function(e) {
                        window.location.href = window.location.origin + OVDM_DIR + '/dataDashboard/' + subPages['gga'];
                    });

                    //Add basemap layer, use ESRI Oceans Base Layer
                    L.esri.basemapLayer("Oceans").addTo(mapdb);

                    // Add latest trackline (GeoJSON)
                    L.geoJson(data.visualizerData[0]).addTo(mapdb);
                    
                    // Add marker at the last coordinate
                    var marker = L.marker(latLng).addTo(mapdb);
                    
                }
            }
        });
    }

    function buildGeotiffDataObjectListDB(latestCruise, dataObjectListDivBlock) {
        var getGeotiffDataObjectListURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectsByType/' + latestCruise + '/geotiff';
        $.getJSON(getGeotiffDataObjectListURL, function (data, status) {
            if (status === 'success' && data !== null) {
 //               $('#navdb-placeholder').css({ 'height': "190px" });
                if (data.length > 0) {
                    buildGeotiffMapDB(data[data.length - 1]);
                } else {
                    $('#geotiff_placeholder').html('<h3>No Data Found</h3>');
                }
            }
        });
    }
    
    function buildGeotiffMapDB(latestDataObject) {
        var getDataObjectFileURL = window.location.origin + OVDM_DIR + '/api/dataDashboard/getDataObjectFile/' + latestDataObject.dataDashboardObjectID;
        $.getJSON(getDataObjectFileURL, function (data, status) {
            if (status === 'success' && data !== null) {
                
                if ('error' in data) {
                    $('#geotiff_placeholder').html('<strong>Error: ' + data.error + '</strong>');
                } else {
                    
                    var coords = data.visualizerData[0]['mapBounds'].split(','),
                            southwest = L.latLng(parseFloat(coords[1]), parseFloat(coords[0])),
                            northeast = L.latLng(parseFloat(coords[3]), parseFloat(coords[2]));
                        
                    //Build Leaflet latLng object
                    var mapBounds = L.latLngBounds(southwest, northeast);
                    var latLng = mapBounds.getCenter();

                    //Build the map
                    var mapdb = L.map('geotiff_placeholder', {
                        maxZoom: 9,
                        zoomControl: false,
                        dragging: false,
                        doubleClickZoom: false,
                        touchZoom: false,
                        scrollWheelZoom: false
                    });
                    
                    mapdb.on('click', function(e) {
                        window.location.href = window.location.origin + OVDM_DIR + '/dataDashboard/' + subPages['geotiff'];
                    });

                    //Add basemap layer, use ESRI Oceans Base Layer
                    L.esri.basemapLayer("Oceans").addTo(mapdb);

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
    
