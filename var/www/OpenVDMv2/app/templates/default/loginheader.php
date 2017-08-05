<?php

    use Helpers\Assets;
    use Helpers\Url;   

?>

    
    <!DOCTYPE html>
<html lang="<?php echo LANGUAGE_CODE; ?>">
<head>

    <!-- Site meta -->
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Open Vessel Data Management v2.3 (OpenVDMv2)">
    <meta name="author" content="Capable Solutions">
    <title><?php echo $data['title'].' - '.SITETITLE; //SITETITLE defined in app/core/config.php ?></title>

    <!-- CSS -->
	<?php
		Assets::css(array(
			DIR . 'bower_components/bootstrap/dist/css/bootstrap.min.css',
			DIR . 'bower_components/metisMenu/dist/metisMenu.min.css',
            DIR . 'bower_components/font-awesome/css/font-awesome.min.css',
			Url::templatePath() . 'css/sb-admin-2.css',
			Url::templatePath() . 'css/timeline.css',
            Url::templatePath() . 'css/style.css',
		))
	?>

</head>
<body>
    <div class="wrapper">
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
        <div class="navbar-default sidebar" role="navigation">
            <div class="sidebar-nav navbar-collapse">
                <ul class="nav" id="side-menu">
                    <li><a href="<?php echo DIR; ?>"><i class="fa fa-home fa-fw"></i> Home</a></li>
                    <li><a href="#"><i class="fa fa-dashboard fa-fw"></i> Data Dashboard<span class="fa arrow"></span></a>
                        <ul class="nav nav-second-level">
                            <li><a href="<?php echo DIR; ?>dataDashboard">Main</a></li>
                            <li><a href="<?php echo DIR; ?>dataDashboard/position">Position</a></li>
                            <li><a href="<?php echo DIR; ?>dataDashboard/weather">Weather</a></li>
                            <li><a href="<?php echo DIR; ?>dataDashboard/soundVelocity">Sound Velocity</a></li>
                        </ul> <!-- /.nav-second-level -->
                    </li>
                    <li><a href="#"><i class="fa fa-wrench fa-fw"></i> Configuration<span class="fa arrow"></span></a>
                        <ul class="nav nav-second-level">
                            <li><a href="<?php echo DIR; ?>config">Main</a></li>
                            <li><a href="<?php echo DIR; ?>config/collectionSystemTransfers">Collection System Transfers</a></li>
                            <li><a href="<?php echo DIR; ?>config/extraDirectories">Extra Directories</a></li>
                            <li><a href="<?php echo DIR; ?>config/cruiseDataTransfers">Cruise Data Transfers</a></li>
                            <li><a href="<?php echo DIR; ?>config/shipToShoreTransfers">Ship-to-Shore Transfers</a></li>
                            <li><a href="<?php echo DIR; ?>config/users">Users</a></li>
                        </ul> <!-- /.nav-second-level -->
                    </li>
                </ul>
            </div> <!-- /.sidebar-collapse -->
        </div> <!-- /.navbar-static-side -->
    </nav>
    
    <!-- Page Content -->
    <div id="page-wrapper">
