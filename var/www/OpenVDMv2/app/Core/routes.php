<?php
/**
 * Routes - all standard routes are defined here.
 *
 * @author David Carr - dave@daveismyname.com
 *
 * @version 2.2
 * @date updated Sept 19, 2015
 */

/** Create alias for Router. */
use Core\Router;
use Helpers\Hooks;

/* Define routes. */
// Configuration-related routes
Router::any('config', '\Controllers\Config\Main@index');
Router::any('config/enableSystem', '\Controllers\Config\Main@enableSystem');
Router::any('config/disableSystem', '\Controllers\Config\Main@disableSystem');
Router::any('config/setupNewCruise', '\Controllers\Config\Main@setupNewCruise');
Router::any('config/setupNewLowering', '\Controllers\Config\Main@setupNewLowering');
Router::any('config/finalizeCurrentCruise', '\Controllers\Config\Main@finalizeCurrentCruise');
Router::any('config/finalizeCurrentLowering', '\Controllers\Config\Main@finalizeCurrentLowering');
Router::any('config/exportOVDMConfig', '\Controllers\Config\Main@exportOVDMConfig');
Router::any('config/exportLoweringConfig', '\Controllers\Config\Main@exportLoweringConfig');
Router::any('config/rsyncPublicDataToCruiseData', '\Controllers\Config\Main@rsyncPublicDataToCruiseData');
Router::any('config/rebuildMD5Summary', '\Controllers\Config\Main@rebuildMD5Summary');
Router::any('config/rebuildTransferLogSummary', '\Controllers\Config\Main@rebuildTransferLogSummary');
Router::any('config/rebuildCruiseDirectory', '\Controllers\Config\Main@rebuildCruiseDirectory');
Router::any('config/rebuildLoweringDirectory', '\Controllers\Config\Main@rebuildLoweringDirectory');
Router::any('config/rebuildDataDashboard', '\Controllers\Config\Main@rebuildDataDashboard');
Router::any('config/editCruise', '\Controllers\Config\Main@editCruise');
Router::any('config/editLowering', '\Controllers\Config\Main@editLowering');
Router::any('config/editShipboardDataWarehouse', '\Controllers\Config\Main@editShipboardDataWarehouse');
Router::any('config/login', '\Controllers\Config\Auth@login');
Router::any('config/logout', '\Controllers\Config\Auth@logout');

Router::any('config/system', '\Controllers\Config\System@index');
Router::any('config/system/editShipboardDataWarehouse', '\Controllers\Config\System@editShipboardDataWarehouse');
Router::any('config/system/testShipboardDataWarehouse', '\Controllers\Config\System@testShipboardDataWarehouse');
Router::any('config/system/editShoresideDataWarehouse', '\Controllers\Config\System@editShoresideDataWarehouse');
Router::any('config/system/testShoresideDataWarehouse', '\Controllers\Config\System@testShoresideDataWarehouse');
Router::any('config/system/editExtraDirectories/(:num)', '\Controllers\Config\System@editExtraDirectories');
Router::any('config/system/editShipToShoreTransfers/(:num)', '\Controllers\Config\System@editShipToShoreTransfers');
Router::any('config/system/enableShipToShoreTransfers/(:num)', '\Controllers\Config\System@enableShipToShoreTransfers');
Router::any('config/system/disableShipToShoreTransfers/(:num)', '\Controllers\Config\System@disableShipToShoreTransfers');
Router::any('config/system/enableShipToShoreBWLimit', '\Controllers\Config\System@enableShipToShoreBWLimit');
Router::any('config/system/disableShipToShoreBWLimit', '\Controllers\Config\System@disableShipToShoreBWLimit');
Router::any('config/system/editShipToShoreBWLimit', '\Controllers\Config\System@editShipToShoreBWLimit');
Router::any('config/system/enableMD5FilesizeLimit', '\Controllers\Config\System@enableMD5FilesizeLimit');
Router::any('config/system/disableMD5FilesizeLimit', '\Controllers\Config\System@disableMD5FilesizeLimit');
Router::any('config/system/editMD5FilesizeLimit', '\Controllers\Config\System@editMD5FilesizeLimit');
Router::any('config/system/addLink', '\Controllers\Config\System@addLink');
Router::any('config/system/editLink/(:num)', '\Controllers\Config\System@editLink');
Router::any('config/system/deleteLink/(:num)', '\Controllers\Config\System@deleteLink');
Router::any('config/system/enableLink/(:num)', '\Controllers\Config\System@enableLink');
Router::any('config/system/disableLink/(:num)', '\Controllers\Config\System@disableLink');
Router::any('config/system/privateLink/(:num)', '\Controllers\Config\System@privateLink');
Router::any('config/system/publicLink/(:num)', '\Controllers\Config\System@publicLink');
//Router::any('config/system/delete/(:num)', '\Controllers\Config\System@delete');

Router::any('config/users/edit/(:num)', '\Controllers\Config\Users@edit');

Router::any('config/collectionSystemTransfers', '\Controllers\Config\CollectionSystemTransfers@index');
Router::any('config/collectionSystemTransfers/add', '\Controllers\Config\CollectionSystemTransfers@add');
Router::any('config/collectionSystemTransfers/edit/(:num)', '\Controllers\Config\CollectionSystemTransfers@edit');
Router::any('config/collectionSystemTransfers/delete/(:num)', '\Controllers\Config\CollectionSystemTransfers@delete');
Router::any('config/collectionSystemTransfers/enable/(:num)', '\Controllers\Config\CollectionSystemTransfers@enable');
Router::any('config/collectionSystemTransfers/disable/(:num)', '\Controllers\Config\CollectionSystemTransfers@disable');
Router::any('config/collectionSystemTransfers/test/(:num)', '\Controllers\Config\CollectionSystemTransfers@test');
Router::any('config/collectionSystemTransfers/run/(:num)', '\Controllers\Config\CollectionSystemTransfers@run');
Router::any('config/collectionSystemTransfers/stop/(:num)', '\Controllers\Config\CollectionSystemTransfers@stop');

Router::any('config/cruiseDataTransfers', '\Controllers\Config\CruiseDataTransfers@index');
Router::any('config/cruiseDataTransfers/add', '\Controllers\Config\CruiseDataTransfers@add');
Router::any('config/cruiseDataTransfers/edit/(:num)', '\Controllers\Config\CruiseDataTransfers@edit');
Router::any('config/cruiseDataTransfers/delete/(:num)', '\Controllers\Config\CruiseDataTransfers@delete');
Router::any('config/cruiseDataTransfers/enable/(:num)', '\Controllers\Config\CruiseDataTransfers@enable');
Router::any('config/cruiseDataTransfers/disable/(:num)', '\Controllers\Config\CruiseDataTransfers@disable');
Router::any('config/cruiseDataTransfers/test/(:num)', '\Controllers\Config\CruiseDataTransfers@test');
Router::any('config/cruiseDataTransfers/run/(:num)', '\Controllers\Config\CruiseDataTransfers@run');
Router::any('config/cruiseDataTransfers/stop/(:num)', '\Controllers\Config\CruiseDataTransfers@stop');

Router::any('config/extraDirectories', '\Controllers\Config\ExtraDirectories@index');
Router::any('config/extraDirectories/add', '\Controllers\Config\ExtraDirectories@add');
Router::any('config/extraDirectories/edit/(:num)', '\Controllers\Config\ExtraDirectories@edit');
Router::any('config/extraDirectories/delete/(:num)', '\Controllers\Config\ExtraDirectories@delete');
Router::any('config/extraDirectories/enable/(:num)', '\Controllers\Config\ExtraDirectories@enable');
Router::any('config/extraDirectories/disable/(:num)', '\Controllers\Config\ExtraDirectories@disable');

Router::any('config/shipToShoreTransfers', '\Controllers\Config\ShipToShoreTransfers@index');
Router::any('config/shipToShoreTransfers/add', '\Controllers\Config\ShipToShoreTransfers@add');
Router::any('config/shipToShoreTransfers/edit/(:num)', '\Controllers\Config\ShipToShoreTransfers@edit');
Router::any('config/shipToShoreTransfers/delete/(:num)', '\Controllers\Config\ShipToShoreTransfers@delete');
Router::any('config/shipToShoreTransfers/enable/(:num)', '\Controllers\Config\ShipToShoreTransfers@enable');
Router::any('config/shipToShoreTransfers/disable/(:num)', '\Controllers\Config\ShipToShoreTransfers@disable');
Router::any('config/shipToShoreTransfers/run', '\Controllers\Config\ShipToShoreTransfers@run');
Router::any('config/shipToShoreTransfers/stop', '\Controllers\Config\ShipToShoreTransfers@stop');
Router::any('config/shipToShoreTransfers/enableShipToShoreTransfers', '\Controllers\Config\ShipToShoreTransfers@enableShipToShoreTransfers');
Router::any('config/shipToShoreTransfers/disableShipToShoreTransfers', '\Controllers\Config\ShipToShoreTransfers@disableShipToShoreTransfers');

Router::any('config/messages', '\Controllers\Config\Messages@index');
Router::any('config/messages/delete/(:num)', '\Controllers\Config\Messages@delete');
Router::any('config/messages/viewedMessage/(:num)', '\Controllers\Config\Messages@viewedMessage');
Router::any('config/messages/viewAllMessages', 'Controllers\Config\Messages@viewAllMessages');
Router::any('config/messages/deleteMessage/(:num)', '\Controllers\Config\Messages@deleteMessage');
Router::any('config/messages/deleteAllMessages', 'Controllers\Config\Messages@deleteAllMessages');

//DataDashboard-related routes
Router::any('dataDashboard', '\Controllers\DataDashboard\DataDashboard@index');
Router::any('dataDashboard/customTab/(:any)', '\Controllers\DataDashboard\DataDashboard@customTab');
Router::any('dataDashboard/dataQuality', '\Controllers\DataDashboard\DataDashboard@dataQuality');
Router::any('dataDashboard/dataQualityShowFileStats/(:all)', '\Controllers\DataDashboard\DataDashboard@dataQualityShowFileStats');
Router::any('dataDashboard/dataQualityShowDataTypeStats/(:any)', '\Controllers\DataDashboard\DataDashboard@dataQualityShowDataTypeStats');

//API-related routes
Router::any('api/warehouse/getCruiseConfig', 'Controllers\Api\Warehouse@getCruiseConfig');
Router::any('api/warehouse/getCruiseID', 'Controllers\Api\Warehouse@getCruiseID');
Router::any('api/warehouse/getCruiseSize', 'Controllers\Api\Warehouse@getCruiseSize');
Router::any('api/warehouse/getCruiseStartDate', 'Controllers\Api\Warehouse@getCruiseStartDate');
Router::any('api/warehouse/getCruiseEndDate', 'Controllers\Api\Warehouse@getCruiseEndDate');
Router::any('api/warehouse/getCruiseFinalizedDate', 'Controllers\Api\Warehouse@getCruiseFinalizedDate');
Router::any('api/warehouse/getLoweringConfig', 'Controllers\Api\Warehouse@getLoweringConfig');
Router::any('api/warehouse/getLoweringID', 'Controllers\Api\Warehouse@getLoweringID');
Router::any('api/warehouse/getLoweringSize', 'Controllers\Api\Warehouse@getLoweringSize');
Router::any('api/warehouse/getLoweringStartDate', 'Controllers\Api\Warehouse@getLoweringStartDate');
Router::any('api/warehouse/getLoweringEndDate', 'Controllers\Api\Warehouse@getLoweringEndDate');
Router::any('api/warehouse/getLoweringFinalizedDate', 'Controllers\Api\Warehouse@getLoweringFinalizedDate');
Router::any('api/warehouse/getFreeSpace', 'Controllers\Api\Warehouse@getFreeSpace');
Router::any('api/warehouse/getMD5FilesizeLimit', 'Controllers\Api\Warehouse@getMD5FilesizeLimit');
Router::any('api/warehouse/getMD5FilesizeLimitStatus', 'Controllers\Api\Warehouse@getMD5FilesizeLimitStatus');
Router::any('api/warehouse/getShipboardDataWarehouseConfig', 'Controllers\Api\Warehouse@getShipboardDataWarehouseConfig');
Router::any('api/warehouse/getShipboardDataWarehouseStatus', 'Controllers\Api\Warehouse@getShipboardDataWarehouseStatus');
Router::any('api/warehouse/getShipToShoreBWLimitStatus', 'Controllers\Api\Warehouse@getShipToShoreBWLimitStatus');
Router::any('api/warehouse/getSystemStatus', 'Controllers\Api\Warehouse@getSystemStatus');
Router::any('api/warehouse/getShowLoweringComponents', 'Controllers\Api\Warehouse@getShowLoweringComponents');
Router::post('api/warehouse/setCruiseSize', 'Controllers\Api\Warehouse@setCruiseSize');
Router::post('api/warehouse/setLoweringSize', 'Controllers\Api\Warehouse@setLoweringSize');

Router::any('api/collectionSystemTransfers/getCollectionSystemTransfers', 'Controllers\Api\CollectionSystemTransfers@getCollectionSystemTransfers');
Router::any('api/collectionSystemTransfers/getActiveCollectionSystemTransfers', 'Controllers\Api\CollectionSystemTransfers@getActiveCollectionSystemTransfers');
Router::any('api/collectionSystemTransfers/getCruiseOnlyCollectionSystemTransfers', 'Controllers\Api\CollectionSystemTransfers@getCruiseOnlyCollectionSystemTransfers');
Router::any('api/collectionSystemTransfers/getLoweringOnlyCollectionSystemTransfers', 'Controllers\Api\CollectionSystemTransfers@getLoweringOnlyCollectionSystemTransfers');
Router::any('api/collectionSystemTransfers/getCollectionSystemTransfer/(:num)', 'Controllers\Api\CollectionSystemTransfers@getCollectionSystemTransfer');
Router::any('api/collectionSystemTransfers/getCollectionSystemTransfersStatuses', 'Controllers\Api\CollectionSystemTransfers@getCollectionSystemTransfersStatuses');
Router::any('api/collectionSystemTransfers/setErrorCollectionSystemTransfer/(:num)', 'Controllers\Api\CollectionSystemTransfers@setErrorCollectionSystemTransfer');
Router::any('api/collectionSystemTransfers/setRunningCollectionSystemTransfer/(:num)', 'Controllers\Api\CollectionSystemTransfers@setRunningCollectionSystemTransfer');
Router::any('api/collectionSystemTransfers/setIdleCollectionSystemTransfer/(:num)', 'Controllers\Api\CollectionSystemTransfers@setIdleCollectionSystemTransfer');

Router::any('api/cruiseDataTransfers/getCruiseDataTransfers', 'Controllers\Api\CruiseDataTransfers@getCruiseDataTransfers');
Router::any('api/cruiseDataTransfers/getCruiseDataTransfer/(:num)', 'Controllers\Api\CruiseDataTransfers@getCruiseDataTransfer');
Router::any('api/cruiseDataTransfers/getRequiredCruiseDataTransfers', 'Controllers\Api\CruiseDataTransfers@getRequiredCruiseDataTransfers');
Router::any('api/cruiseDataTransfers/getRequiredCruiseDataTransfer/(:num)', 'Controllers\Api\CruiseDataTransfers@getRequiredCruiseDataTransfer');
Router::any('api/cruiseDataTransfers/getCruiseDataTransfersStatuses', 'Controllers\Api\CruiseDataTransfers@getCruiseDataTransfersStatuses');
Router::any('api/cruiseDataTransfers/getRequiredCruiseDataTransfersStatuses', 'Controllers\Api\CruiseDataTransfers@getRequiredCruiseDataTransfersStatuses');
Router::any('api/cruiseDataTransfers/setErrorCruiseDataTransfer/(:num)', 'Controllers\Api\CruiseDataTransfers@setErrorCruiseDataTransfer');
Router::any('api/cruiseDataTransfers/setRunningCruiseDataTransfer/(:num)', 'Controllers\Api\CruiseDataTransfers@setRunningCruiseDataTransfer');
Router::any('api/cruiseDataTransfers/setIdleCruiseDataTransfer/(:num)', 'Controllers\Api\CruiseDataTransfers@setIdleCruiseDataTransfer');

Router::any('api/dashboardData/getDashboardDataTypes/(:any)', 'Controllers\Api\DashboardData@getDashboardDataTypes');
Router::any('api/dashboardData/getLatestDataObjectByType/(:any)/(:any)', 'Controllers\Api\DashboardData@getLatestDataObjectByType');
Router::any('api/dashboardData/getLatestVisualizerDataByType/(:any)/(:any)', 'Controllers\Api\DashboardData@getLatestVisualizerDataByType');
Router::any('api/dashboardData/getLatestStatsByType/(:any)/(:any)', 'Controllers\Api\DashboardData@getLatestStatsByType');
Router::any('api/dashboardData/getLatestQualityTestsByType/(:any)/(:any)', 'Controllers\Api\DashboardData@getLatestQualityTestsByType');
Router::any('api/dashboardData/getDashboardObjectVisualizerDataByJsonName/(:any)/(:all)', 'Controllers\Api\DashboardData@getDashboardObjectVisualizerDataByJsonName');
Router::any('api/dashboardData/getDashboardObjectVisualizerDataByRawName/(:any)/(:all)', 'Controllers\Api\DashboardData@getDashboardObjectVisualizerDataByRawName');
Router::any('api/dashboardData/getDashboardObjectStatsByJsonName/(:any)/(:all)', 'Controllers\Api\DashboardData@getDashboardObjectStatsByJsonName');
Router::any('api/dashboardData/getDashboardObjectStatsByRawName/(:any)/(:all)', 'Controllers\Api\DashboardData@getDashboardObjectStatsByRawName');
Router::any('api/dashboardData/getDashboardObjectQualityTestsByJsonName/(:any)/(:all)', 'Controllers\Api\DashboardData@getDashboardObjectQualityTestsByJsonName');
Router::any('api/dashboardData/getDashboardObjectQualityTestsByRawName/(:any)/(:all)', 'Controllers\Api\DashboardData@getDashboardObjectQualityTestsByRawName');

Router::any('api/extraDirectories/getExtraDirectories', 'Controllers\Api\ExtraDirectories@getExtraDirectories');
Router::any('api/extraDirectories/getExtraDirectory/(:num)', 'Controllers\Api\ExtraDirectories@getExtraDirectory');
Router::any('api/extraDirectories/getRequiredExtraDirectories', 'Controllers\Api\ExtraDirectories@getRequiredExtraDirectories');

Router::any('api/tasks/getTasks', 'Controllers\Api\Tasks@getTasks');
Router::any('api/tasks/getActiveTasks', 'Controllers\Api\Tasks@getActiveTasks');
Router::any('api/tasks/getCruiseOnlyTasks', 'Controllers\Api\Tasks@getCruiseOnlyTasks');
Router::any('api/tasks/getLoweringOnlyTasks', 'Controllers\Api\Tasks@getLoweringOnlyTasks');
Router::any('api/tasks/getTask/(:num)', 'Controllers\Api\Tasks@getTask');
Router::any('api/tasks/getTaskStatuses', 'Controllers\Api\Tasks@getTaskStatuses');
Router::any('api/tasks/setErrorTask/(:num)', 'Controllers\Api\Tasks@setErrorTask');
Router::any('api/tasks/setRunningTask/(:num)', 'Controllers\Api\Tasks@setRunningTask');
Router::any('api/tasks/setIdleTask/(:num)', 'Controllers\Api\Tasks@setIdleTask');

Router::any('api/transferLogs/getExcludeLogsSummary', 'Controllers\Api\TransferLogs@getExcludeLogsSummary');
Router::any('api/transferLogs/getShipboardLogsSummary/(:num)', 'Controllers\Api\TransferLogs@getShipboardLogsSummary');
Router::any('api/transferLogs/getShipToShoreLogsSummary/(:num)', 'Controllers\Api\TransferLogs@getShipToShoreLogsSummary');

Router::any('api/shipToShoreTransfers/getShipToShoreTransfers', 'Controllers\Api\ShipToShoreTransfers@getShipToShoreTransfers');
Router::any('api/shipToShoreTransfers/getRequiredShipToShoreTransfers', 'Controllers\Api\ShipToShoreTransfers@getRequiredShipToShoreTransfers');

Router::any('api/messages/viewedMessage/(:num)', 'Controllers\Api\Messages@viewedMessage');
Router::any('api/messages/getRecentMessages', 'Controllers\Api\Messages@getRecentMessages');
Router::any('api/messages/getNewMessagesTotal', 'Controllers\Api\Messages@getNewMessagesTotal');
Router::any('api/messages/newMessage',    'Controllers\Api\Messages@newMessage');

Router::any('api/gearman/newJob/(:any)', 'Controllers\Api\Gearman@newJob');
Router::any('api/gearman/getJobs', 'Controllers\Api\Gearman@getJobs');
Router::any('api/gearman/getJob/(:num)', 'Controllers\Api\Gearman@getJob');
Router::any('api/gearman/clearAllJobsFromDB', 'Controllers\Api\Gearman@clearAllJobsFromDB');

Router::any('', 'Controllers\Welcome@index');
/* Module routes. */
$hooks = Hooks::get();
$hooks->run('routes');

/* If no route found. */
Router::error('Core\Error@index');

/* Turn on old style routing. */
Router::$fallback = false;

/* Execute matched routes. */
Router::dispatch();
