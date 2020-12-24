    <div class="row">
<?php
    for($i = 0; $i < sizeof($data['dataTypes']); $i++){
?>
        <div class="col-lg-4 col-md-6">
            <div class="panel panel-default">
                <div class="panel-body">
                    <div id="<?php echo $data['dataTypes'][$i]; ?>-placeholder" style="min-height:200px;">Loading...</div>
                </div>
                <div class="panel-footer"><?php echo $data['dataTypes'][$i]; ?></div>
            </div>
        </div>
<?php
    }
?>
    </div>
