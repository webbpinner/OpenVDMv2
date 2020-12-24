<?php

use Core\Error;
use Helpers\Form;
?>
    
    <div class="container">
        <div class="row">
            <div class="col-md-4 col-md-offset-3">
                <div class="login-panel panel panel-default">
                    <div class="panel-heading">
                        <h3 class="panel-title">Please Sign In</h3>
                    </div>
                    <div class="panel-body">
                        <?php echo Error::display($error); ?>
                        <?php echo Form::open(array('method' => 'post'));?>
                            <fieldset>
                                <?php echo Form::input(array('name' => 'referrer', 'type' => 'hidden', 'value' => $data['referrer']));?>                                
                                <div class="form-group"><?php echo Form::input(array('name' => 'username', 'class' => 'form-control', 'placeholder' => 'Username', 'autofocus' => '' ));?></div>
                                <div class="form-group"><?php echo Form::input(array('name' => 'password', 'class' => 'form-control', 'placeholder' => 'Password', 'type' => 'password'));?></div>
                                <div class="form-group"><?php echo Form::submit(array('name' => 'submit', 'class' => 'btn btn-lg btn-primary btn-block', 'value' => 'Login'));?></div>
                            </fieldset>
                        <?php echo Form::close();?>
                    </div>
                </div>
            </div>
        </div>
    </div>
