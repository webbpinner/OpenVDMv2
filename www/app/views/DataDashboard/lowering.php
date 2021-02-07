<?php
$loweringID  = (($_GET['loweringID'] && in_array($_GET['loweringID'], $data['loweringIDs'])) ? $_GET['loweringID'] : $data['loweringID']);    // returns whether the input integer is odd
rsort($data['loweringIDs']);
?>

<?php # echo '<pre>'; print_r($data['placeholders'][0]['dataFiles']); echo '</pre>';?>
        <div class="row">
            <div class="col-lg-12">
                <div class="pull-right">
                    <form  class="form-inline">                            
                        <div class="form-group">
                            <label for="lowering_sel">Lowering:</label>
                            <select class="form-control inline" id="lowering_sel" onchange="window.location.href = window.location.href.split('?')[0] + '?loweringID=' + this[selectedIndex].value">
<?php
    for($i = 0; $i < sizeof($data['loweringIDs']); $i++){
?>
                                <option value="<?php echo $data['loweringIDs'][$i]; ?>" <?php echo ($loweringID == $data['loweringIDs'][$i] ? "selected" : "")?>><?php echo $data['loweringIDs'][$i]; ?></option>
<?php
    }
?>
                            </select>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-lg-12">
                <div class="panel">
                    <div class="panel-body">
                        <div class="row">
                            <div class="col-lg-12">
<?php
    for($i = 0; $i < sizeof($data['placeholders']); $i++){
?>
                                <div class="panel panel-default">
<?php
        //$dataFiles = array_filter($data['placeholders'][$i]['dataFiles'], "loweringFiles");
        //var_dump($dataFiles);
        for($j=0; $j < sizeof($data['placeholders'][$i]['dataFiles']); $j++){

          $dataFiles = array_filter($data['placeholders'][$i]['dataFiles'][$j], function($dataFile) use($loweringID) {
            return preg_match("/$loweringID/", $dataFile['dd_json']);
          });
          $dataFiles = array_values($dataFiles);
          // echo '<pre>'; print_r($dataFiles); echo '</pre>';
?>
                                <a id="<?php echo $dataFiles[0]['type']; ?>"></a>
<?php
            $filecount += sizeof($dataFiles);
        }
?>
                                    <div class="panel-heading"><?php echo $data['placeholders'][$i]['heading'];?><?php echo ($data['placeholders'][$i]['plotType'] == 'chart'? '<i id="' . $data['placeholders'][$i]['id'] . '_expand-btn" class="expand-btn pull-right btn btn-sm btn-default fa fa-expand"></i>': ''); ?>
                                    </div>                  
                                    <div class="panel-body">
                                        <div class="<?php echo $data['placeholders'][$i]['plotType']; ?>" id="<?php echo $data['placeholders'][$i]['id'];?>_placeholder" style="min-height:<?php echo (strcmp($data['placeholders'][$i]['plotType'], 'map') === 0? '493': '200'); ?>px;"><?php echo ($filecount > 0? $loadingImage: 'No Data Found.'); ?></div>
                                    </div>
                                    <div class="panel-footer">
                                        <div class="objectList" id="<?php echo $data['placeholders'][$i]['id'];?>_objectList-placeholder">
                                            <form>                                            
<?php
        for($j = 0; $j < sizeof($data['placeholders'][$i]['dataArray']); $j++){
            // echo '<pre>'; print_r($data['placeholders'][$i]['dataArray'][$j]); echo '</pre>';
            $dataFiles = array_filter($data['placeholders'][$i]['dataFiles'][$j], function($dataFile) use($loweringID) {
              return preg_match("/$loweringID/", $dataFile['dd_json']);
            });

            $dataFiles = array_values($dataFiles);
            // echo '<pre>'; print_r($dataFiles); echo '</pre>';
?>                                     
                                                <div class="row">
                                                    <div class="col-lg-12"><strong><?php echo $dataFiles[0]['type']; ?></strong><?php echo (strcmp($data['placeholders'][$i]['plotType'], 'map') === 0 && sizeof($dataFiles) > 0? '<div class="pull-right"><div class="btn btn-xs btn-default selectAll" >Select All</div> <div class="btn btn-xs btn-default clearAll" >Clear All</div></div>': ''); ?></div>
<?php
            if(sizeof($dataFiles) > 0){
                if(strcmp($data['placeholders'][$i]['dataArray'][$j]['visType'], 'geoJSON')===0) {
?>
                                                    <div class='col-lg-12'>
                                                        <input class='se-checkbox' type="checkbox" value="<?php echo $dataFiles[0]['type'];?>" checked> Start/End Positions
                                                    </div></br>
<?php
                    for($k = sizeof($dataFiles)-1; $k >= 0; $k--){
?>                              
                                                    <div class='col-lg-4 col-sm-6'>
                                                        <input class='<?php echo $data['placeholders'][$i]['dataArray'][$j]['visType']; ?>-checkbox' type="checkbox" value="<?php echo $dataFiles[$k]['dd_json'];?>" checked> <?php echo end(explode('/',$dataFiles[$k]['raw_data']));?>
                                                        <a href="<?php echo $data['dataWarehouseApacheDir'] . '/' . $dataFiles[$k]['raw_data']; ?>" download target="_blank"><i class="fa fa-download"></i></a>
                                                    </div>
<?php
                    }
                } else if(strcmp($data['placeholders'][$i]['dataArray'][$j]['visType'], 'tms')===0) {
                    for($k = sizeof($datafiles)-1; $k >= 0; $k--){
?>                              
                                                    <div class='col-lg-4 col-sm-6'>
                                                        <input class='<?php echo $data['placeholders'][$i]['dataArray'][$j]['visType']; ?>-checkbox' type="checkbox" value="<?php echo $dataFiles[$k]['dd_json'];?>" checked> <?php echo end(explode('/',$dataFiles[$k]['raw_data']));?>
                                                        <a href="<?php echo $data['dataWarehouseApacheDir'] . '/' . $dataFiles[$k]['raw_data']; ?>" download target="_blank"><i class="fa fa-download"></i></a>
                                                    </div>
<?php
                    }
                } else if(strcmp($data['placeholders'][$i]['dataArray'][$j]['visType'], 'json')===0) {
?>
                                                    <div class="form-group">
<?php
                    for($k = sizeof($dataFiles)-1; $k >= 0; $k--){
?>                              
                                                        <div class='col-lg-4 col-sm-6'>
                                                            <input class='<?php echo $data['placeholders'][$i]['dataArray'][$j]['visType']; ?>-radio' name="<?php echo $dataFiles[$k]['type'];?>" type="radio" value="<?php echo $dataFiles[$k]['dd_json'];?>"  <?php echo ($k === sizeof($dataFiles)-1? 'checked' : '');   ?>> <?php echo end(explode('/',$dataFiles[$k]['raw_data']));?>
                                                            <a href="<?php echo $data['dataWarehouseApacheDir'] . '/' . $dataFiles[$k]['raw_data']; ?>" download target="_blank"><i class="fa fa-download"></i></a>
                                                        </div>
<?php
                    }
?>
                                                    </div>
<?php
                } else if(strcmp($data['placeholders'][$i]['dataArray'][$j]['visType'], 'json-reversed-y')===0) {
?>
                                                    <div class="form-group">
<?php
                    for($k = sizeof($dataFiles)-1; $k >= 0; $k--){
?>                              
                                                        <div class='col-lg-4 col-sm-6'>
                                                            <input class='<?php echo $data['placeholders'][$i]['dataArray'][$j]['visType']; ?>-radio' name="<?php echo $dataFiles[$k]['type'];?>" type="radio" value="<?php echo $dataFiles[$k]['dd_json'];?>"  <?php echo ($k === sizeof($dataFiles)-1? 'checked' : '');   ?>> <?php echo end(explode('/',$dataFiles[$k]['raw_data']));?>
                                                            <a href="<?php echo $data['dataWarehouseApacheDir'] . '/' . $dataFiles[$k]['raw_data']; ?>" download target="_blank"><i class="fa fa-download"></i></a>
                                                        </div>
<?php
                    }
?>
                                                    </div>
<?php
                } else {
?>
                                                    <div class='col-lg-12'>No data found
							<?php var_dump($data['placeholders'][$i]['dataArray'][$j]); ?>
						    </div>
<?php
                }
            }
?>
                                                </div>
<?php
        }
?>
                                            </form>
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
        </div>
