$(function () {
    'use strict';
    
    $('#main').on("click", function () {
        window.location.href = siteRoot + 'config';
    });
    
    $('#collectionSystemTransfers').on("click", function () {
        window.location.href = siteRoot + 'config/collectionSystemTransfers';
    });
    
    $('#extraDirectories').on("click", function () {
        window.location.href = siteRoot + 'config/extraDirectories';
    });
    
    $('#cruiseDataTransfers').on("click", function () {
        window.location.href = siteRoot + 'config/cruiseDataTransfers';
    });
    
    $('#shipToShoreTransfers').on("click", function () {
        window.location.href = siteRoot + 'config/shipToShoreTransfers';
    });
    
    $('#system').on("click", function () {
        window.location.href = siteRoot + 'config/system';
    });
});