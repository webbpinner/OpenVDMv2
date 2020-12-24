<?php

use Core\Error;
use Helpers\Form;

?>
    <div class="row">
        <div class="col-lg-12">
            <?php echo Error::display($error); ?>
        </div>
    </div>
    <div class="row">
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">Add new User</div>
                <div class="panel-body">
                    <?php echo Form::open(array('role'=>'form', 'method'=>'post')); ?>
                        <div class="row">
                            <div class="col-lg-12">
                                <div class="form-group"><label>Username</label><?php echo Form::input(array('class'=>'form-control', 'name'=>'username', 'value'=>$_POST['username'])); ?></div>
                                <div class="form-group"><label>Password</label><?php echo Form::input(array('class'=>'form-control', 'name'=>'password', 'value'=>'', 'type'=>'password')); ?></div>
                                <div class="form-group"><label>Password (verify)</label><?php echo Form::input(array('class'=>'form-control', 'name'=>'password2', 'value'=>'', 'type'=>'password')); ?></div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-lg-12">
                                <?php echo Form::submit(array('name'=>'submit', 'class'=>'btn btn-primary', 'value'=>'Add')); ?>
                                <a href="<?php echo DIR; ?>config/users" class="btn btn-danger">Cancel</a>
                            </div>
                        </div>    
                    <?php echo Form::close(); ?>
                </div>
            </div>
        </div>
    </div>