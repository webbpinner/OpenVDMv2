<?php

use Helpers\Assets;
use Helpers\Session;
use Helpers\Url;
use Helpers\Hooks;

    //initialise hooks
    $hooks = Hooks::get();

    $_warehouseModel = new \Models\Warehouse();
    $_messagesModel = new \Models\Config\Messages();
    $_gearmanModel = new \Models\Api\Gearman();
    $_dataDashboardModel = new \Models\DataDashboard();
    $_linksModel = new \Models\Config\Links();


    $messageLimit = "LIMIT 10";
    $jobLimit = "LIMIT 10";


    function formatFilesize($bytes) {
        $s = array('bytes', 'kb', 'MB', 'GB', 'TB', 'PB');
        $e = floor(log($bytes)/log(1024));
        return round(($bytes/pow(1024, floor($e))),2) . " " . $s[$e];
    }

    function time_elapsed_string($mysqlTime)
    {
        $ptime = strtotime($mysqlTime);
        $etime = time() - $ptime;

        if ($etime < 1)
        {
            return '0 seconds';
        }

        $a = array( 365 * 24 * 60 * 60  =>  'year',
                   30 * 24 * 60 * 60  =>  'month',
                   24 * 60 * 60  =>  'day',
                   60 * 60  =>  'hour',
                   60  =>  'minute',
                   1  =>  'second'
                  );
        $a_plural = array( 'year'   => 'years',
                          'month'  => 'months',
                          'day'    => 'days',
                          'hour'   => 'hours',
                          'minute' => 'minutes',
                          'second' => 'seconds'
                         );

        foreach ($a as $secs => $str)
        {
            $d = $etime / $secs;
            if ($d >= 1)
            {
                $r = round($d);
                return $r . ' ' . ($r > 1 ? $a_plural[$str] : $str) . ' ago';
            }
        }
    }

    if($_warehouseModel->getSystemStatus()) {
            $data['systemStatus'] = "On";
    } else {
            $data['systemStatus'] = "Off";
    }

    $data['cruiseID'] = $_warehouseModel->getCruiseID();

    $cruiseSize = $_warehouseModel->getCruiseSize();
    if(isset($cruiseSize['error'])){
        $data['cruiseSize'] = "Error";
    } else {
        $data['cruiseSize'] = formatFilesize($cruiseSize['cruiseSize']);
    }

    $freeSpace = $_warehouseModel->getFreeSpace();
    if(isset($freeSpace['error'])){
        $data['freeSpace'] = "Error";
    } else {
        $data['freeSpace'] = formatFilesize($freeSpace['freeSpace']);
    }

    $data['messagesNavbar'] = $_messagesModel->getNewMessages($messageLimit);
    $data['messagesBadgeNavbar'] = $_messagesModel->getNewMessagesTotal();

// Shows no jobs but also doesn't call job update
//    $data['jobsNavbar'] = array();
//    $data['jobsBadgeNavbar'] = sizeof($data['jobsNavbar']);

    $data['jobsNavbar'] = $_gearmanModel->getJobs();
    $data['jobsBadgeNavbar'] = sizeof($data['jobsNavbar']);

    $data['dataDashboardTabs'] = $_dataDashboardModel->getDataDashboardTabs();

?>

<!DOCTYPE html>
<html lang="<?php echo LANGUAGE_CODE; ?>">
<head>

	<!-- Site meta -->
	<meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Open Vessel Data Management v2.2 (OpenVDMv2)">
    <meta name="author" content="OceanDataRat.org">
	<title><?php echo $data['title'].' - '.SITETITLE; ?></title>

	<!-- CSS -->
<?php

    $cssFileArray = array(
        DIR . 'bower_components/bootstrap/dist/css/bootstrap.min.css',
        DIR . 'bower_components/metisMenu/dist/metisMenu.min.css',
        DIR . 'bower_components/font-awesome/css/font-awesome.min.css',
        Url::templatePath() . 'css/sb-admin-2.css',
        Url::templatePath() . 'css/timeline.css',
        Url::templatePath() . 'css/style.css',
    );

    if (isset($data['css'])){
        foreach ($data['css'] as &$cssFile) {
            if ($cssFile === 'leaflet') {
                array_push($cssFileArray, DIR . 'bower_components/leaflet/dist/leaflet.css');
                array_push($cssFileArray, DIR . 'bower_components/leaflet-fullscreen-bower/leaflet.fullscreen.css');
            } else if ($cssFile === 'leaflet-timedimension') {
                array_push($cssFileArray, DIR . 'bower_components/leaflet-timedimension/dist/leaflet.timedimension.control.css');
            } else if ($cssFile === 'datetimepicker') {
                array_push($cssFileArray, DIR . 'bower_components/eonasdan-bootstrap-datetimepicker/build/css/bootstrap-datetimepicker.min.css');
            } else {
                array_push($cssFileArray, Url::templatePath() . "css/" . $cssFile . ".css");
            }
        }
    }

	Assets::css($cssFileArray);

    //hook for plugging in css
	$hooks->run('css');
?>

</head>
<body>


<?php
    //hook for running code after body tag
    $hooks->run('afterBody');
?>

<div id="wrapper">
    <nav class="navbar navbar-default navbar-static-top" role="navigation" style="margin-bottom: 0">
        <!-- Brand and toggle get grouped for better mobile display -->
        <div class="navbar-header">
            <button type="button" class="navbar-toggle" data-toggle="collapse" data-target=".navbar-collapse">
                <span class="sr-only">Toggle navigation</span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
            </button>
            <a class="navbar-brand" href="<?php echo DIR;?>"><?php echo SITETITLE;?></a>
        </div> <!-- navbar-header -->
        <ul class="nav navbar-top-links navbar-right">
            <li class="dropdown">
                <a class="dropdown-toggle" data-toggle="dropdown" href="#">
                    <span class="badge" id='OVDM_jobCount'><?php echo $data['jobsBadgeNavbar']; ?></span> <i class="fa fa-tasks fa-fw"></i>  <i class="fa fa-caret-down"></i>
                </a>
<?php
 //   if(strcmp($data['jobsBadgeNavbar'],'0') === '0') {
?>
                <ul class="dropdown-menu dropdown-tasks" id='OVDM_jobs'>
<?php
        if($data['jobsNavbar']){
            foreach($data['jobsNavbar'] as $row){
                $progress = intVal(($row->jobNumerator / $row->jobDenominator) * 100);
?>
                    <li>
                        <a class="OVDM_job" jobID="<?php echo $row->jobID; ?>" href="#">
                            <div>
                                <p>
                                    <strong><?php echo $row->jobName; ?></strong>
                                    <span class="pull-right text-muted small"><?php echo $progress; ?>% Complete</span>
                                </p>
                                <div class="progress progress-striped active">
                                    <div class="progress-bar progress-bar-success" role="progressbar" aria-valuenow="<?php echo $row->jobNumerator; ?>" aria-valuemin="0" aria-valuemax="<?php echo $row->jobDenominator; ?>" style="width: <?php echo $progress; ?>%">
                                        <span class="sr-only"><?php echo $progress; ?>% Complete (success)</span>
                                    </div>
                                </div>
                            </div>
                        </a>
                    </li>
<?php
            }
        } else {
?>
                    <li><a class="text-center" href="#"><strong>No tasks are running</strong></a></li>
<?php
        }
?>
                </ul> <!-- dropdown-user -->
<?php
  //  }
?>
            </li> <!-- dropdown -->
            <li class="dropdown">
                <a class="dropdown-toggle" data-toggle="dropdown" href="#">
                    <span class="badge" id='OVDM_messageCount'><?php echo $data['messagesBadgeNavbar']; ?></span> <i class="fa fa-bell fa-fw"></i>  <i class="fa fa-caret-down"></i>
                </a>
                <ul class="dropdown-menu dropdown-alerts" id='OVDM_messages'>
<?php
    if($data['messagesNavbar']){
        foreach($data['messagesNavbar'] as $row){
?>
                    <li>
                            <a class="OVDM_message" messageID="<?php echo $row->messageID; ?>" href="#">
                                <strong><?php echo $row->messageTitle; ?><span class="pull-right text-muted small"><?php echo time_elapsed_string($row->messageTS); ?></span></strong>
                            </a>
                    </li>
                    <li class="divider"></li>

<?php
        }
   }
?>
                    <li><a class="text-center" href="<?php echo DIR; ?>config/messages"><strong>Read All Messages <i class="fa fa-angle-right"></i></strong></a></li>
                </ul> <!-- dropdown-user -->
            </li> <!-- dropdown -->
            <li class="dropdown">
                <a class="dropdown-toggle" data-toggle="dropdown" href="#">
                    <i class="fa fa-user fa-fw"></i> <i class="fa fa-caret-down"></i>
                </a>
                <ul class="dropdown-menu dropdown-user">
<?php
    if(Session::get('loggedin')){
?>
                    <li><a href="<?php echo DIR; ?>config/users/edit/<?php echo Session::get('userID') ?>"><i class="fa fa-user fa-fw"></i>User Settings</a></li>
                    <li><a href="<?php echo DIR; ?>config/logout"><i class="fa fa-sign-out fa-fw"></i>Logout</a></li>
<?php
    } else {
?>
                    <li><a href="<?php echo DIR; ?>config/login"><i class="fa fa-sign-in fa-fw"></i>Login</a></li>
<?php
    }
?>
                </ul> <!-- dropdown-user -->
            </li> <!-- dropdown -->
        </ul>
        <div class="navbar-default sidebar" role="navigation">
            <div class="sidebar-nav navbar-collapse">
                <ul class="nav" id="side-menu">
                    <li><a href="<?php echo DIR; ?>"><i class="fa fa-home fa-fw"></i> Home</a></li>
                    <li><a href="#"><i class="fa fa-dashboard fa-fw"></i> Data Dashboard<span class="fa arrow"></span></a>
                        <ul class="nav nav-second-level">
                            <li><a href="<?php echo DIR; ?>dataDashboard">Main</a></li>
<?php
    foreach($data['dataDashboardTabs'] as $row){
?>
                            <li><a href="<?php echo DIR; ?>dataDashboard/customTab/<?php echo $row['page'];?>"><?php echo $row['title'];?></a></li>
<?php
    }
?>
                            <li><a href="<?php echo DIR; ?>dataDashboard/dataQuality">Data Quality</a></li>
                        </ul> <!-- /.nav-second-level -->
                    </li>
                    <li><a href="#"><i class="fa fa-wrench fa-fw"></i> Configuration<span class="fa arrow"></span></a>
                        <ul class="nav nav-second-level">
                            <li><a href="<?php echo DIR; ?>config">Main</a></li>
                            <li><a href="<?php echo DIR; ?>config/collectionSystemTransfers">Collection System Transfers</a></li>
                            <li><a href="<?php echo DIR; ?>config/extraDirectories">Extra Directories</a></li>
                            <li><a href="<?php echo DIR; ?>config/cruiseDataTransfers">Cruise Data Transfers</a></li>
                            <li><a href="<?php echo DIR; ?>config/shipToShoreTransfers">Ship-to-Shore Transfers</a></li>
                            <li><a href="<?php echo DIR; ?>config/system">System</a></li>
                        </ul> <!-- /.nav-second-level -->
                    </li>
                    <li><a href="#"><i class="fa fa-external-link fa-fw"></i> Links<span class="fa arrow"></span></a>
                        <ul class="nav nav-second-level">
<?php
    $links = $_linksModel->getLinks();
    $_linksModel->processLinkURL($links);
    foreach ($links as $row) {
        if (strcmp($row->enable, '1') == 0) {
            if (strcmp($row->private, '0') == 0) {
?>
                            <li><a href="<?php echo $row->url; ?>" target="_blank"><?php echo $row->name; ?></a></li>
<?php
            } else if((strcmp($row->private, '1') == 0) && Session::get('loggedin')){
?>
                            <li><a href="<?php echo $row->url; ?>" target="_blank"><?php echo $row->name; ?></a></li>
<?php
            }
        }
    }
?>
                        </ul> <!-- /.nav-second-level -->
                    </li>
                </ul>
            </div> <!-- /.sidebar-collapse -->
        </div> <!-- /.navbar-static-side -->
    </nav>

    <!-- Page Content -->
    <div id="page-wrapper">

        <div class="row">
            <div class="col-lg-12">
            </br>
<!--                <h1 class="page-header"><?php echo $data['title']; ?></h1> -->               
            </div>
        </div>

        <div class="row">
            <div class="col-lg-3 col-md-6 col-xs-6">
<?php
    if(Session::get('loggedin')){
?>
                    <a href="<?php echo DIR; echo $data['systemStatus'] === 'On'? "config/disableSystem" : "config/enableSystem";?>">
<?php
    }
?>
                <div id="systemStatusPanel" class="panel <?php echo $data['systemStatus'] === 'On'? "panel-green" : "panel-red"; ?>">
                    <div class="panel-heading">
                        <div id="systemStatus" class="huge"><?php echo $data['systemStatus']; ?></div>
                        <div class="text-right">System Status</div>
                    </div><!-- .panel-heading -->
                </div> <!-- #systemStatusPanel .panel .panel-primary -->
<?php
    if(Session::get('loggedin')){
?>
                    </a>
<?php
    }
?>
            </div> <!-- .col-lg-3 .col-md-6 -->
            <div class="col-lg-3 col-md-6  col-xs-6">
                <div id="cruiseIDPanel" class="panel panel-primary">
                    <div class="panel-heading">
                        <div id="cruiseID" class="huge"><?php echo $data['cruiseID']; ?></div>
                        <div class="text-right">Cruise ID</div>
                    </div> <!-- .panel-heading -->
                </div> <!-- .panel .panel-primary -->
            </div> <!-- .col-lg-3 .col-md-6 -->
            <div class="col-lg-3 col-md-6  col-xs-6">
                <div id="cruiseSizePanel" class="panel panel-primary">
                    <div class="panel-heading">
                        <div id="cruiseSize" class="huge"><?php echo $data['cruiseSize']; ?></div>
                        <div class="text-right">Cruise Size</div>
                    </div> <!-- .panel-heading -->
                </div> <!-- .panel .panel-primary -->
            </div> <!-- .col-lg-3 .col-md-6 -->
            <div class="col-lg-3 col-md-6  col-xs-6">
                <div id="freeSpacePanel" class="panel panel-primary">
                    <div class="panel-heading">
                        <div id="freeSpace" class="huge"><?php echo $data['freeSpace']; ?></div>
                        <div class="text-right">Free Space</div>
                    </div> <!-- .panel-heading -->
                </div> <!-- .panel .panel-primary -->
            </div> <!-- .col-lg-3 .col-md-6 -->
        </div> <!-- .row -->
