<?php
/**
 * Workbench v12.0.0 — Standalone Workbench Application Shell.
 * WordPress remains optional; wordpressRequired = false.
 * Authoritative application shell is standalone.
 * Authoritative computation remains in FastAPI.
 */
if (!defined('ABSPATH')) { exit; }

function scwb_v1200_backend_request($path,$method='GET',$body=null) {
    if (function_exists('scwb_v1100_backend_request')) {
        return scwb_v1100_backend_request($path,$method,$body);
    }
    return array('ok'=>false,'error'=>'Workbench backend adapter unavailable','_httpStatus'=>503);
}

function scwb_v1200_proxy_response($path,$method='GET',$body=null) {
    $data=scwb_v1200_backend_request($path,$method,$body);
    $status=intval($data['_httpStatus'] ?? 200);
    unset($data['_httpStatus']);
    return new WP_REST_Response($data,$status);
}

add_action('rest_api_init',function(){
    $permission=function(){return current_user_can('edit_posts');};

    register_rest_route('sc-workbench/v1/v1200','/status',array(
      'methods'=>'GET','permission_callback'=>$permission,
      'callback'=>function(){return scwb_v1200_proxy_response('/v1200/status');}));

    register_rest_route('sc-workbench/v1/v1200','/app-manifest',array(
      'methods'=>'GET','permission_callback'=>$permission,
      'callback'=>function(){return scwb_v1200_proxy_response('/standalone/v1/app-manifest');}));

    register_rest_route('sc-workbench/v1/v1200','/app-routes',array(
      'methods'=>'GET','permission_callback'=>$permission,
      'callback'=>function(){return scwb_v1200_proxy_response('/standalone/v1/app-routes');}));

    register_rest_route('sc-workbench/v1/v1200','/app-shell',array(
      'methods'=>'GET','permission_callback'=>$permission,
      'callback'=>function(){return scwb_v1200_proxy_response('/standalone/v1/app-shell');}));
});
