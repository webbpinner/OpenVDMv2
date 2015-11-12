<?php

use Helpers\Assets;
use Helpers\Url;
use Helpers\Hooks;

//initialise hooks
$hooks = Hooks::get();

?>
    </div> <!-- page-wrapper -->
    <span class="text-muted pull-right" style="padding: 15px"><a href="http://www.oceandatarat.org/?page_id=1123">OpenVDMv2</a> is licensed under the <a href="http://www.gnu.org/licenses/gpl-3.0.html">GPLv3</a> public license</span>
</div> <!-- wrapper -->


<!-- JS -->    
<script type="text/javascript">
    var siteRoot = "<?php echo DIR; ?>";
    var cruiseID = "<?php echo $data['cruiseID']; ?>";
    var cruiseDataDir = "<?php echo $data['dataWarehouseApacheDir']; ?>";
    
</script>

<?php 

$jsFileArray = array(
    Url::templatePath() . 'bower_components/jquery/dist/jquery.min.js',
    Url::templatePath() . 'bower_components/bootstrap/dist/js/bootstrap.min.js',
    Url::templatePath() . 'bower_components/metisMenu/dist/metisMenu.min.js',
    Url::templatePath() . 'bower_components/startbootstrap-sb-admin-2/dist/js/sb-admin-2.js',
    Url::templatePath() . 'js/jquery.cookie.js',
    Url::templatePath() . 'js/header.js',    
    Url::templatePath() . 'js/modals.js',
);
    
if (isset($data['javascript'])){
    foreach ($data['javascript'] as &$jsFile) {
        if ($jsFile === 'leaflet') {
            array_push($jsFileArray, Url::templatePath() . 'bower_components/leaflet/leaflet.js');
            array_push($jsFileArray, Url::templatePath() . 'bower_components/esri-leaflet/esri-leaflet.js');
            array_push($jsFileArray, Url::templatePath() . 'bower_components/leaflet/plugins/leaflet-fullscreen/Leaflet.fullscreen.min.js');
            //array_push($jsFileArray, Url::templatePath() . "js/esriCredit.js");
        } else if ($jsFile === 'highcharts') {
            array_push($jsFileArray, Url::templatePath() . 'bower_components/highcharts/js/highcharts.js');
            array_push($jsFileArray, Url::templatePath() . 'js/highcharts-fa-plugin.js'); 
        } else if ($jsFile === 'bootstrap-datepicker') {
            array_push($jsFileArray, Url::templatePath() . 'bower_components/bootstrap-datepicker/dist/js/bootstrap-datepicker.min.js');   
            array_push($jsFileArray, Url::templatePath() . 'js/datepicker.js');
        } else {
            array_push($jsFileArray, Url::templatePath() . 'js/' . $jsFile . '.js');
        }
    }
}

Assets::js($jsFileArray);

//hook for plugging in javascript
$hooks->run('js');

//hook for plugging in code into the footer
$hooks->run('footer');

?>

</body>
</html>