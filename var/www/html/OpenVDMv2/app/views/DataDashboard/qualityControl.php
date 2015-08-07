<?php

use Core\Error;
use Helpers\Session;

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
                    <li class=""><a id="position" href="#position" data-toggle="tab">Position</a></li>
                    <li class=""><a id="weather" href="#weather" data-toggle="tab">Weather</a></li>
                    <li class=""><a id="soundVelocity" href="#soundVelocity" data-toggle="tab">Sound Velocity</a></li>
                    <li class="active"><a id="qualityControl" href="#qualityControl" data-toggle="tab">QA/QC</a></li>                    
                </ul>
            </div>
        </div>
    </div>
    <div class="row">
        <div class="col-lg-12">
<?php
    for ($i = 0; $i < sizeof($data['dataDashboardObjectsByTypes']); $i++) {
?>
            <div class="panel panel-default">
                <div class="panel-heading"><?php echo $data['dataDashboardObjectsByTypes'][$i][0]->dataDashboardObjectType;?></div>
                <div class="panel-body">
                    <table class='table table-striped table-bordered responsive'>
                        <tr>
                            <th>Filename</th>
<?php
        for ($j = 0; $j < sizeof($data['dataDashboardObjectsQualityTestsByTypes'][$i][0]); $j++) {
?>
                            <th width=20px><?php echo $data['dataDashboardObjectsQualityTestsByTypes'][$i][0][$j]->testName;?></th>
<?php
        }
?>
                            <th class="text-center" width=20px>Stats</th>
                        </tr>
<?php
        for ($j = 0; $j < sizeof($data['dataDashboardObjectsByTypes'][$i]); $j++) {
?>
                        <tr>
                            <td><?php echo $data['dataDashboardObjectsByTypes'][$i][$j]->dataDashboardRawFile; ?></td>
<?php
            for ($k = 0; $k < sizeof($data['dataDashboardObjectsQualityTestsByTypes'][$i][$j]); $k++) {
?>
                            <td>
<?php
                if ($data['dataDashboardObjectsQualityTestsByTypes'][$i][$j][$k]->results === "Passed"){
?>                                
                                <div class="text-center"><i class="fa fa-check text-success"></i></div>
<?php
                } elseif ($data['dataDashboardObjectsQualityTestsByTypes'][$i][$j][$k]->results === "Warning"){
?>
                                <div class="text-center"><i class="fa fa-warning text-warning"></i></div>
<?php
                } elseif ($data['dataDashboardObjectsQualityTestsByTypes'][$i][$j][$k]->results === "Failed"){
?>
                                <div class="text-center"><i class="fa fa-times text-danger"></i></div>
<?php
                }
?>                                                                                                         
                            </td>
<?php
            }
?>
                            <td>
<?php
                if($data['dataDashboardObjectsStatsByTypes'][$i][$j]){
?>
                                <a href='<?php echo DIR; ?>dataDashboard/qualityControlShowDataFileStats/<?php echo $data['dataDashboardObjectsByTypes'][$i][$j]->dataDashboardObjectID; ?>' class='btn btn-xs btn-default'>Show</a>
<?php
            } else {
?>
                                <a href='<?php echo DIR; ?>dataDashboard/qualityControlShowDataFileStats/<?php echo $data['dataDashboardObjectsByTypes'][$i][$j]->dataDashboardObjectID; ?>' class='btn btn-xs btn-default disabled'>Show</a>
<?php
            }
?>
                            </td>
                        </tr>
<?php
        }
                                                                           
?>
                        <tr>
                            <td class="text-right" colspan=<?php echo sizeof($data['dataDashboardObjectsQualityTestsByTypes'][$i][0])+2;?>>
<?php
        $statsAvailable = false;
        for ($k = 0; $k < sizeof($data['dataDashboardObjectsStatsByTypes'][$i]); $k++) {
            if($data['dataDashboardObjectsStatsByTypes'][$i][$k]){
                $statsAvailable = true;
                break;
            }
        }
        if($statsAvailable) {
?>
                                <a href='<?php echo DIR; ?>dataDashboard/qualityControlShowDataTypeStats/<?php echo $data['dataDashboardObjectsByTypes'][$i][0]->dataDashboardObjectType; ?>' class='btn btn-xs btn-default'>Show Totals</a>
<?php
        } else {
?>
                                <a href='<?php echo DIR; ?>dataDashboard/qualityControlShowDataTypeStats/<?php echo $data['dataDashboardObjectsByTypes'][$i][0]->dataDashboardObjectType; ?>' class='btn btn-xs btn-default disabled'>Show Totals</a>
<?php
        }
?>
                            </td>
                        </tr>
                    </table>
                </div>
            </div>
<?php
    }
?>
        </div>
    </div>
<?php
    if($data['stats']) {
?>
<div class="modal fade" id="statsModal" tabindex="-1" role="dialog">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                <h4 class="modal-title" id="myModalLabel">Stats for <?php echo $data['statsTitle'] ?></h4>
            </div>
            <div class="modal-body">
                <table class="table">
                    <tbody>
<?php
    for($i=0; $i<(sizeof($data['stats'])); $i++){
?>
                        <tr>
                            <td><?php echo $data['stats'][$i]->statName; ?>:</td>
                            <td>
<?php
        if(strcmp($data['stats'][$i]->statType, 'bounds') === 0){
            echo 'Min: ' . round(floatval($data['stats'][$i]->statData[0]),2) . ' ' . $data['stats'][$i]->statUnit . ', Max: ' . round(floatval($data['stats'][$i]->statData[1]),2) . ' ' . $data['stats'][$i]->statUnit;
        } elseif(strcmp($data['stats'][$i]->statType, 'timeBounds') === 0){
            echo 'Start: ' . gmdate('r', floatval($data['stats'][$i]->statData[0])) . '</br>';
            echo 'End: ' . gmdate('r', floatval($data['stats'][$i]->statData[1]));
        } elseif (strcmp($data['stats'][$i]->statType, 'geoBounds') === 0){
            echo 'North: ' . round(floatval($data['stats'][$i]->statData[0]),6) . ' ' . $data['stats'][$i]->statUnit . ', East: ' . round(floatval($data['stats'][$i]->statData[1]),6) . ' ' . $data['stats'][$i]->statUnit . '</br>';
            echo 'South: ' . round(floatval($data['stats'][$i]->statData[2]),6) . ' ' . $data['stats'][$i]->statUnit . ', West: ' . round(floatval($data['stats'][$i]->statData[3]),6) . ' ' . $data['stats'][$i]->statUnit;
        } elseif (strcmp($data['stats'][$i]->statType, 'totalValue') === 0){
            echo round(floatval($data['stats'][$i]->statData[0]),2) . ' ' . $data['stats'][$i]->statUnit;
        } elseif (strcmp($data['stats'][$i]->statType, 'valueValidity') === 0){
            echo 'Valid data values: ' . round(floatval($data['stats'][$i]->statData[0])/(floatval($data['stats'][$i]->statData[0]) + floatval($data['stats'][$i]->statData[1])) * 100,4) . '%';
        } elseif (strcmp($data['stats'][$i]->statType, 'rowValidity') === 0){
            echo 'Valid rows: ' . round(floatval($data['stats'][$i]->statData[0])/(floatval($data['stats'][$i]->statData[0]) + floatval($data['stats'][$i]->statData[1])) * 100,4) . '%';
        }
            
?>
                            
                            </td>
                        </tr>
<?php
    }
?>
                    <tbody>
                </table>
            </div>
            <div class="modal-footer">
                <a href='' class="btn btn-primary" data-dismiss="modal">Close</a>
            </div>
        </div> <!-- /.modal-content -->
    </div> <!-- /.modal-dialog -->
</div> <!-- /.modal -->
<?php
    }
?>
