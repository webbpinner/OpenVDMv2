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
        for($j=0; $j < sizeof($data['placeholders'][$i]['dataFiles']); $j++){
?>
                                <a id="<?php echo $data['placeholders'][$i]['dataFiles'][$j][0]['type']; ?>"></a>
<?php
            $filecount += sizeof($data['placeholders'][$i]['dataFiles'][$j]);
        }
?>
                                    <div class="panel-heading"><?php echo $data['placeholders'][$i]['heading'];?><?php echo ($data['placeholders'][$i]['plotType'] == 'chart'? '<i id="' . $data['placeholders'][$i]['id'] . '_expand-btn" class="expand-btn pull-right btn btn-sm btn-default fa fa-expand"></i>': ''); ?></div>                  
                                    <div class="panel-body">
                                        <div class="<?php echo $data['placeholders'][$i]['plotType']; ?>" id="<?php echo $data['placeholders'][$i]['id'];?>_placeholder" style="min-height:<?php echo (strcmp($data['placeholders'][$i][plotType], 'map') === 0? '493': '200'); ?>px;"><?php echo ($filecount > 0? $loadingImage: 'No Data Found.'); ?></div>
                                    </div>
                                    <div class="panel-footer">
                                        <div class="objectList" id="<?php echo $data['placeholders'][$i]['id'];?>_objectList-placeholder">
                                            <form>                                            
<?php
        for($j = 0; $j < sizeof($data['placeholders'][$i]['dataArray']); $j++){
?>                                     
                                                <div class="row">
                                                    <div class="col-lg-12"><strong><?php echo $data['placeholders'][$i]['dataFiles'][$j][0]['type']; ?></strong><?php echo (strcmp($data['placeholders'][$i][plotType], 'map') === 0? '<div class="pull-right"><div class="btn btn-xs btn-default selectAll" >Select All</div> <div class="btn btn-xs btn-default clearAll" >Clear All</div></div>': ''); ?></div>
<?php
            if(is_array($data['placeholders'][$i]['dataFiles'][$j]) && sizeof($data['placeholders'][$i]['dataFiles'][$j]) > 0){
                if(strcmp($data['placeholders'][$i]['dataArray'][$j]['visType'], 'geoJSON')===0) {
?>
                                                    <div class='col-lg-12'>
                                                        <input class='lp-checkbox' type="checkbox" value="<?php echo $data['placeholders'][$i]['dataFiles'][$j][0]['type'];?>" checked> Latest Position
                                                    </div></br>
<?php
                    for($k = sizeof($data['placeholders'][$i]['dataFiles'][$j])-1; $k >= 0; $k--){
?>                              
                                                    <div class='col-lg-4 col-sm-6'>
                                                        <input class='<?php echo $data['placeholders'][$i]['dataArray'][$j]['visType']; ?>-checkbox' type="checkbox" value="<?php echo $data['placeholders'][$i]['dataFiles'][$j][$k]['dd_json'];?>" checked> <?php echo end(explode('/',$data['placeholders'][$i]['dataFiles'][$j][$k]['raw_data']));?>
                                                        <a href="<?php echo $data['dataWarehouseApacheDir'] . '/' . $data['placeholders'][$i]['dataFiles'][$j][$k]['raw_data']; ?>" download target="_blank"><i class="fa fa-download"></i></a>
                                                    </div>
<?php
                    }
                } else if(strcmp($data['placeholders'][$i]['dataArray'][$j]['visType'], 'tms')===0) {
                    for($k = sizeof($data['placeholders'][$i]['dataFiles'][$j])-1; $k >= 0; $k--){
?>                              
                                                    <div class='col-lg-4 col-sm-6'>
                                                        <input class='<?php echo $data['placeholders'][$i]['dataArray'][$j]['visType']; ?>-checkbox' type="checkbox" value="<?php echo $data['placeholders'][$i]['dataFiles'][$j][$k]['dd_json'];?>" checked> <?php echo end(explode('/',$data['placeholders'][$i]['dataFiles'][$j][$k]['raw_data']));?>
                                                        <a href="<?php echo $data['dataWarehouseApacheDir'] . '/' . $data['placeholders'][$i]['dataFiles'][$j][$k]['raw_data']; ?>" download target="_blank"><i class="fa fa-download"></i></a>
                                                    </div>
<?php
                    }
                } else if(strcmp($data['placeholders'][$i]['dataArray'][$j]['visType'], 'json')===0) {
?>
                                                    <div class="form-group">
<?php
                    for($k = sizeof($data['placeholders'][$i]['dataFiles'][$j])-1; $k >= 0; $k--){
?>                              
                                                        <div class='col-lg-4 col-sm-6'>
                                                            <input class='<?php echo $data['placeholders'][$i]['dataArray'][$j]['visType']; ?>-radio' name="<?php echo $data['placeholders'][$i]['dataFiles'][$j][$k]['type'];?>" type="radio" value="<?php echo $data['placeholders'][$i]['dataFiles'][$j][$k]['dd_json'];?>"  <?php echo ($k === sizeof($data['placeholders'][$i]['dataFiles'][$j])-1? 'checked' : '');   ?>> <?php echo end(explode('/',$data['placeholders'][$i]['dataFiles'][$j][$k]['raw_data']));?>
                                                            <a href="<?php echo $data['dataWarehouseApacheDir'] . '/' . $data['placeholders'][$i]['dataFiles'][$j][$k]['raw_data']; ?>" download target="_blank"><i class="fa fa-download"></i></a>
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
                    for($k = sizeof($data['placeholders'][$i]['dataFiles'][$j])-1; $k >= 0; $k--){
?>                              
                                                        <div class='col-lg-4 col-sm-6'>
                                                            <input class='<?php echo $data['placeholders'][$i]['dataArray'][$j]['visType']; ?>-radio' name="<?php echo $data['placeholders'][$i]['dataFiles'][$j][$k]['type'];?>" type="radio" value="<?php echo $data['placeholders'][$i]['dataFiles'][$j][$k]['dd_json'];?>"  <?php echo ($k === sizeof($data['placeholders'][$i]['dataFiles'][$j])-1? 'checked' : '');   ?>> <?php echo end(explode('/',$data['placeholders'][$i]['dataFiles'][$j][$k]['raw_data']));?>
                                                            <a href="<?php echo $data['dataWarehouseApacheDir'] . '/' . $data['placeholders'][$i]['dataFiles'][$j][$k]['raw_data']; ?>" download target="_blank"><i class="fa fa-download"></i></a>
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
