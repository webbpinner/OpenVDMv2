<?php

use Core\Language;
use Core\Error;
use Helpers\Session;
use Helpers\Url;

$loadingImage = '<img height="50" src="' . Url::templatePath() . 'images/loading.gif"/>';

?>

    <div class="row">
        <div class="col-lg-12">
            <?php echo Error::display(Session::pull('message'), 'alert alert-success'); ?>
        </div>
    </div>

    <div class="row">
        <div class="col-lg-12">
            <div class="tabbable" style="margin-bottom: 18px;">
                <ul class="nav nav-tabs">
                    <li class=""><a id="main" href="#main" data-toggle="tab">Main</a></li>
                    <li class="<?php echo ($data['page']==='position'? 'active': ''); ?>"><a id="position" href="#position" data-toggle="tab">Position</a></li>
                    <li class="<?php echo ($data['page']==='weather'? 'active': ''); ?>"><a id="weather" href="#weather" data-toggle="tab">Weather</a></li>
                    <li class="<?php echo ($data['page']==='soundVelocity'? 'active': ''); ?>"><a id="soundVelocity" href="#soundVelocity" data-toggle="tab">Sound Velocity</a></li>
                    <li class=""><a id="dataQuality" href="#dataQuality" data-toggle="tab">Data Quality</a></li> 
                </ul>
            </div>
        </div>
    </div>
    <div class="row">
		<div class="col-md-12">

			<h1>No Data Found!</h1>

			...but it might be on the way.

			<hr />

			<h3>You are seeing this page because no dashboard data related to this page could not be found</h3>
            <p>The fact that you reached this page doesn't means that there is a problem.</p>
            <p>You may be at this page because of one of the following reasons:</p>
            <ul>
                <li>The data simply hasn't arrived yet (very possible if the cruise just started)</li>
                <li>The name of the data dashboard directory has changed in the configuration but the directory has not been renamed (or vice-versa).</li>
                <li>The data was removed (Grab a pitchfork and rally the lynch mob!)</li>
            </ul>
		</div>
    </div>