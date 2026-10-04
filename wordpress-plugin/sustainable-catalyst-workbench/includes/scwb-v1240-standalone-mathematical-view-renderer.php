<?php
/**
 * Workbench v12.4.0 — Standalone Mathematical View Renderer.
 * WordPress remains optional; wordpressRequired = false.
 * WordPress does not own mathematical rendering.
 * Renderer-neutral view specs remain authoritative in FastAPI.
 */
if (!defined('ABSPATH')) { exit; }
function scwb_v1240_backend_request($path,$method='GET',$body=null){
    if(function_exists('scwb_v1100_backend_request')) return scwb_v1100_backend_request($path,$method,$body);
    return array('ok'=>false,'error'=>'Workbench backend adapter unavailable','_httpStatus'=>503);
}
add_action('rest_api_init',function(){
    $permission=function(){return current_user_can('edit_posts');};
    register_rest_route('sc-workbench/v1/v1240','/status',array(
      'methods'=>'GET','permission_callback'=>$permission,
      'callback'=>function(){return new WP_REST_Response(scwb_v1240_backend_request('/v1240/status'),200);}));
});
