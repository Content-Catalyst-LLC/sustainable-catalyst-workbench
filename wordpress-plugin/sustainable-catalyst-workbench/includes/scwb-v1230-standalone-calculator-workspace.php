<?php
/**
 * Workbench v12.3.0 — Standalone Calculator Workspace.
 * WordPress remains optional; wordpressRequired = false.
 * WordPress does not own calculator execution or CalculationObject persistence.
 * The standalone application calls FastAPI directly.
 */
if (!defined('ABSPATH')) { exit; }

function scwb_v1230_backend_request($path,$method='GET',$body=null) {
    if (function_exists('scwb_v1100_backend_request')) {
        return scwb_v1100_backend_request($path,$method,$body);
    }
    return array('ok'=>false,'error'=>'Workbench backend adapter unavailable','_httpStatus'=>503);
}

function scwb_v1230_proxy_response($path,$method='GET',$body=null) {
    $data=scwb_v1230_backend_request($path,$method,$body);
    $status=intval($data['_httpStatus'] ?? 200);
    unset($data['_httpStatus']);
    return new WP_REST_Response($data,$status);
}

add_action('rest_api_init',function(){
    $permission=function(){return current_user_can('edit_posts');};

    register_rest_route('sc-workbench/v1/v1230','/status',array(
      'methods'=>'GET','permission_callback'=>$permission,
      'callback'=>function(){return scwb_v1230_proxy_response('/v1230/status');}));

    register_rest_route('sc-workbench/v1/v1230','/calculator-config',array(
      'methods'=>'GET','permission_callback'=>$permission,
      'callback'=>function(){return scwb_v1230_proxy_response('/standalone/v1/calculator/config');}));
});
