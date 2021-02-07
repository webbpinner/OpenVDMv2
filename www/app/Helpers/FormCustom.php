<?php
namespace Helpers;
/*
 * Form Helper - create form elements quickly
 *
 * @author David Carr - dave@simplemvcframework.com
 * @version 1.0
 * @date June 27, 2014
 * @date May 18 2015
 */
class FormCustom
{

    /**
     * radioInLine
     * This method returns radio elements in order given in an array
     * For selection pass checked
     * Each radio should look like array(0=>array('id'=>'1', 'name'=>'rd[]', 'value'=>'x', 'label'=>'label_text' ))
     * @param   array(array(id, name, value, class, checked, disabled, label))
     * @return  string
     */
    public function radioInline($params = array(), $value = '')
    {
        $o = '<br />';
        if (!empty($params)) {
            if(strcmp($value, '') === 0) { $value = $params[0]['value']; }
            $x = 0;
            foreach ($params as $k => $v) {
                $v['id'] = (isset($v['id']))                ? $v['id']                          : "rd_id_{$x}_".rand(1000,9999);               
                $o .= "<label class='radio-inline'>";
                $o .= "<input type='radio'";
                $o .= (isset($v['id']))                     ? " id='{$v['name']}{$v['id']}'"    : '';
                $o .= (isset($v['name']))                   ? " name='{$v['name']}'"            : '';
                $o .= (isset($v['value']))                  ? " value='{$v['value']}'"          : '';
                $o .= (isset($v['class']))                  ? " class='{$v['class']}'"          : '';
                $o .= (strcmp($v['value'], $value) === 0)   ? " checked='checked'"              : '';
                $o .= (isset($v['disabled']))               ? " disabled='{$v['disabled']}'"    : '';
                $o .= (isset($params['style']))             ? " style='{$params['style']}'"     : '';
                $o .= " />";
                $o .= (isset($v['label']))                  ? "{$v['label']}"                   : '';
                $o .= "</label>\n";
                $x++;
            }
        }
        return $o;
    }
}