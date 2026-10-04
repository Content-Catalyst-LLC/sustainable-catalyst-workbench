<?php
/**
 * Workbench v12.2.0 — Persistent Calculation & Project Store.
 * WordPress remains optional; wordpressRequired = false.
 * WordPress is not the persistence authority.
 * Persistent state remains in the FastAPI application store.
 */
if (!defined('ABSPATH')) { exit; }

function scwb_v1220_backend_request($path,$method='GET',$body=null) {
    if (function_exists('scwb_v1100_backend_request')) {
        return scwb_v1100_backend_request($path,$method,$body);
    }
    return array('ok'=>false,'error'=>'Workbench backend adapter unavailable','_httpStatus'=>503);
}
function scwb_v1220_proxy_response($path,$method='GET',$body=null) {
    $data=scwb_v1220_backend_request($path,$method,$body);
    $status=intval($data['_httpStatus'] ?? 200); unset($data['_httpStatus']);
    return new WP_REST_Response($data,$status);
}
add_action('rest_api_init',function(){
    $permission=function(){return current_user_can('edit_posts');};
    register_rest_route('sc-workbench/v1/v1220','/status',array(
      'methods'=>'GET','permission_callback'=>$permission,
      'callback'=>function(){return scwb_v1220_proxy_response('/v1220/status');}));
    register_rest_route('sc-workbench/v1/v1220','/store-status',array(
      'methods'=>'GET','permission_callback'=>$permission,
      'callback'=>function(){return scwb_v1220_proxy_response('/standalone/v1/store/status');}));
});
