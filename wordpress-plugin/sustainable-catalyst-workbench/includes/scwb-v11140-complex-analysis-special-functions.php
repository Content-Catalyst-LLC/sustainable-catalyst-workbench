<?php
/**
 * Workbench v11.14.0 — Complex Analysis & Special Functions.
 * WordPress remains optional; wordpressRequired = false.
 * Authoritative computation remains in FastAPI.
 */
if (!defined('ABSPATH')) { exit; }

function scwb_v11140_backend_request($path,$method='GET',$body=null) {
    if (function_exists('scwb_v1100_backend_request')) {
        return scwb_v1100_backend_request($path,$method,$body);
    }
    return array('ok'=>false,'error'=>'Workbench backend adapter unavailable','_httpStatus'=>503);
}
function scwb_v11140_proxy_response($path,$method='GET',$body=null) {
    $data=scwb_v11140_backend_request($path,$method,$body);
    $status=intval($data['_httpStatus'] ?? 200); unset($data['_httpStatus']);
    return new WP_REST_Response($data,$status);
}
add_action('rest_api_init',function(){
    $permission=function(){return current_user_can('edit_posts');};
    register_rest_route('sc-workbench/v1/v11140','/status',array(
      'methods'=>'GET','permission_callback'=>$permission,
      'callback'=>function(){return scwb_v11140_proxy_response('/v11140/status');}));
    register_rest_route('sc-workbench/v1/v11140','/complex-analysis',array(
      'methods'=>'POST','permission_callback'=>$permission,
      'callback'=>function($r){return scwb_v11140_proxy_response(
        '/calculation-engine/v1/complex-analysis','POST',$r->get_json_params());}));
    register_rest_route('sc-workbench/v1/v11140','/calculation-object',array(
      'methods'=>'POST','permission_callback'=>$permission,
      'callback'=>function($r){return scwb_v11140_proxy_response(
        '/calculation-engine/v1/complex-analysis/calculation-object','POST',$r->get_json_params());}));
});
