<?php
/**
 * Workbench v12.5.0 — Notebook & Calculation History.
 * WordPress remains optional; wordpressRequired = false.
 * WordPress does not own notebook or history persistence.
 * Persistent notebook/history state remains in FastAPI/SQLite.
 */
if (!defined('ABSPATH')) { exit; }
function scwb_v1250_backend_request($path,$method='GET',$body=null){
    if(function_exists('scwb_v1100_backend_request')) return scwb_v1100_backend_request($path,$method,$body);
    return array('ok'=>false,'error'=>'Workbench backend adapter unavailable','_httpStatus'=>503);
}
add_action('rest_api_init',function(){
    $permission=function(){return current_user_can('edit_posts');};
    register_rest_route('sc-workbench/v1/v1250','/status',array(
      'methods'=>'GET','permission_callback'=>$permission,
      'callback'=>function(){return new WP_REST_Response(scwb_v1250_backend_request('/v1250/status'),200);}));
});
