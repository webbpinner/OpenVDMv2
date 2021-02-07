    <div class="row">
        <div class="col-lg-12">
            <div class="panel">
                <div class="panel-body">
                    <div class="row">
<?php
    for ($i = 0; $i < sizeof($data['dataTypes']); $i++) {
?>
                        <div class="col-lg-12">
                            <div class="panel panel-default">
                                <a id="<?php echo $data['dataTypes'][$i];?>"></a>
                                <div class="panel-heading"><?php echo $data['dataTypes'][$i];?></div>
                                <div class="panel-body">
                                    <table class='table table-striped table-bordered responsive'>
                                        <tr>
                                            <th>Filename</th>
<?php
        for ($k = 0; $k < sizeof($data['dataObjectsQualityTests'][$i][0]); $k++) {
?>
                                            <th width=20px><?php echo $data['dataObjectsQualityTests'][$i][0][$k]->testName;?></th>
<?php
        }
?>
                                            <th class="text-center" width=20px>Stats</th>
                                        </tr>
<?php
        for ($j = 0; $j < sizeof($data['dataObjectsQualityTests'][$i]); $j++) {
?>
                                        <tr>
                                            <td><?php echo $data['dataObjects'][$i][$j]['raw_data']; ?> <a href="<?php echo $data['dataWarehouseApacheDir'] . '/' . $data['dataObjects'][$i][$j]['raw_data']; ?>" download target="_blank"><i class="fa fa-download"></i></a></td>
<?php
            for ($k = 0; $k < sizeof($data['dataObjectsQualityTests'][$i][$j]); $k++) {
?>
                                            <td>
<?php
                if ($data['dataObjectsQualityTests'][$i][$j][$k]->results === "Passed"){
?>                                
                                                <div class="text-center"><i class="fa fa-check text-success"></i></div>
<?php
                } elseif ($data['dataObjectsQualityTests'][$i][$j][$k]->results === "Warning"){
?>
                                                <div class="text-center"><i class="fa fa-warning text-warning"></i></div>
<?php
                } elseif ($data['dataObjectsQualityTests'][$i][$j][$k]->results === "Failed"){
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
                if($data['dataObjectsStats'][$i][$j]){
?>
                                                <a href='<?php echo DIR; ?>dataDashboard/dataQualityShowFileStats/<?php echo $data['dataObjects'][$i][$j]['raw_data']; ?>' class='btn btn-xs btn-default'>Show</a>
<?php
            } else {
?>
                                                <a href='<?php echo DIR; ?>dataDashboard/dataQualityShowFileStats/<?php echo $data['dataObjects'][$i][$j]['raw_data']; ?>' class='btn btn-xs btn-default disabled'>Show</a>
<?php
            }
?>
                                            </td>
                                        </tr>
<?php
        }
                                                                           
?>
                                        <tr>
                                            <td class="text-right" colspan=<?php echo sizeof($data['dataObjectsQualityTests'][$i][0])+2;?>>
<?php
        $statsAvailable = false;
        for ($k = 0; $k < sizeof($data['dataObjectsStats'][$i]); $k++) {
            if($data['dataObjectsStats'][$i][$k]){
                $statsAvailable = true;
                break;
            }
        }
        if($statsAvailable) {
?>
                                                <a href='<?php echo DIR; ?>dataDashboard/dataQualityShowDataTypeStats/<?php echo $data['dataTypes'][$i]; ?>' class='btn btn-xs btn-default'>Show Totals</a>
<?php
        } else {
?>
                                                <a href='<?php echo DIR; ?>dataDashboard/dataQualityShowDataTypeStats/<?php echo $data['dataTypes'][$i]; ?>' class='btn btn-xs btn-default disabled'>Show Totals</a>
<?php
        }
?>
                                            </td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                        </div>
<?php
    }
?>
                    </div>
                </div>
            </div>
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
            echo 'Min: ' . round(floatval($data['stats'][$i]->statValue[0]),2) . ' ' . $data['stats'][$i]->statUnit . ', Max: ' . round(floatval($data['stats'][$i]->statValue[1]),2) . ' ' . $data['stats'][$i]->statUnit;
        } elseif(strcmp($data['stats'][$i]->statType, 'timeBounds') === 0){
            echo 'Start: ' . $data['stats'][$i]->statValue[0] . '</br>';
            echo 'End: ' . $data['stats'][$i]->statValue[1];
        } elseif (strcmp($data['stats'][$i]->statType, 'geoBounds') === 0){
            echo 'North: ' . round(floatval($data['stats'][$i]->statValue[0]),6) . ' ' . $data['stats'][$i]->statUnit . ', East: ' . round(floatval($data['stats'][$i]->statValue[1]),6) . ' ' . $data['stats'][$i]->statUnit . '</br>';
            echo 'South: ' . round(floatval($data['stats'][$i]->statValue[2]),6) . ' ' . $data['stats'][$i]->statUnit . ', West: ' . round(floatval($data['stats'][$i]->statValue[3]),6) . ' ' . $data['stats'][$i]->statUnit;
        } elseif (strcmp($data['stats'][$i]->statType, 'totalValue') === 0){
            echo round(floatval($data['stats'][$i]->statValue[0]),2) . ' ' . $data['stats'][$i]->statUnit;
        } elseif (strcmp($data['stats'][$i]->statType, 'valueValidity') === 0){
            echo 'Valid data values: ' . round(floatval($data['stats'][$i]->statValue[0])/(floatval($data['stats'][$i]->statValue[0]) + floatval($data['stats'][$i]->statValue[1])) * 100,4) . '%';
        } elseif (strcmp($data['stats'][$i]->statType, 'rowValidity') === 0){
            echo 'Valid rows: ' . round(floatval($data['stats'][$i]->statValue[0])/(floatval($data['stats'][$i]->statValue[0]) + floatval($data['stats'][$i]->statValue[1])) * 100,4) . '%';
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
                <a id="modal-close-btn" href="#<?php echo $data['statsDataType']; ?>" class="btn btn-primary" data-dismiss="modal">Close</a>
            </div>
        </div> <!-- /.modal-content -->
    </div> <!-- /.modal-dialog -->
</div> <!-- /.modal -->
<?php
    }
?>
