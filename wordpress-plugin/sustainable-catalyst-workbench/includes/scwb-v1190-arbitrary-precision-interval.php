<?php
/**
 * Workbench v11.9.0 — Arbitrary Precision & Interval Arithmetic.
 * WordPress remains optional; wordpressRequired = false.
 * Authoritative computation remains in FastAPI.
 */
if (!defined('ABSPATH')) { exit; }
function scwb_v1190_backend_request($path,$method='GET',$body=null){
    if(function_exists('scwb_v1100_backend_request')) return scwb_v1100_backend_request($path,$method,$body);
    return array('ok'=>false,'error'=>'Workbench backend adapter unavailable','_httpStatus'=>503);
}
function scwb_v1190_proxy_response($path,$method='GET',$body=null){
    $data=scwb_v1190_backend_request($path,$method,$body);
    $status=intval($data['_httpStatus'] ?? 200); unset($data['_httpStatus']);
    return new WP_REST_Response($data,$status);
}
add_action('rest_api_init',function(){
    $p=function(){return current_user_can('edit_posts');};
    register_rest_route('sc-workbench/v1/v1190','/status',array(
      'methods'=>'GET','permission_callback'=>$p,
      'callback'=>fn()=>scwb_v1190_proxy_response('/v1190/status')));
    register_rest_route('sc-workbench/v1/v1190','/precision',array(
      'methods'=>'POST','permission_callback'=>$p,
      'callback'=>fn($r)=>scwb_v1190_proxy_response('/calculation-engine/v1/precision','POST',$r->get_json_params())));
    register_rest_route('sc-workbench/v1/v1190','/calculation-object',array(
      'methods'=>'POST','permission_callback'=>$p,
      'callback'=>fn($r)=>scwb_v1190_proxy_response('/calculation-engine/v1/precision/calculation-object','POST',$r->get_json_params())));
});
