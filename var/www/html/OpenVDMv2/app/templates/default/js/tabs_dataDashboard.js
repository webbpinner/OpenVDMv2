$(function () {
    'use strict';
    
    $('#jobResultsModal').on('hidden.bs.modal', function () {
        window.location.replace(siteRoot + 'dataDashboard');
    });

    $('#main').on("click", function () {
        window.location.href = siteRoot + 'dataDashboard';
    });
    
    $('#position').on("click", function () {
        window.location.href = siteRoot + 'dataDashboard/position';
    });
    
    $('#soundVelocity').on("click", function () {
        window.location.href = siteRoot + 'dataDashboard/soundVelocity';
    });
    
    $('#weather').on("click", function () {
        window.location.href = siteRoot + 'dataDashboard/weather';
    });
    
    $('#qualityControl').on("click", function () {
        window.location.href = siteRoot + 'dataDashboard/qualityControl';
    });
});