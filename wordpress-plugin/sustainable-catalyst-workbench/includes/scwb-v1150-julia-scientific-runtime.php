<?php
/**
 * Workbench v11.5.0 — Julia Scientific Runtime Foundation.
 * WordPress remains optional; wordpressRequired = false.
 * Authoritative computation remains in FastAPI.
 */
if (!defined('ABSPATH')) { exit; }

function scwb_v1150_backend_request($path,$method='GET',$body=null) {
    if (function_exists('scwb_v1100_backend_request')) {
        return scwb_v1100_backend_request($path,$method,$body);
    }
    return array('ok'=>false,'error'=>'Workbench backend adapter unavailable','_httpStatus'=>503);
}
function scwb_v1150_proxy_response($path,$method='GET',$body=null) {
    $data=scwb_v1150_backend_request($path,$method,$body);
    $status=intval($data['_httpStatus'] ?? 200); unset($data['_httpStatus']);
    return new WP_REST_Response($data,$status);
}
function scwb_v1150_status_shortcode() {
    $data=scwb_v1150_backend_request('/v1150/status');
    if (empty($data['ok'])) return '<div class="scwb-v1150-status">Julia Scientific Runtime unavailable.</div>';
    $state=!empty($data['julia']['installed']) ? 'online' : 'fallback available';
    return sprintf('<div class="scwb-v1150-status"><strong>Workbench v%s</strong> · Julia runtime %s · WordPress optional</div>',
        esc_html($data['version'] ?? '11.5.0'),esc_html($state));
}
add_shortcode('sc_workbench_julia_runtime_status','scwb_v1150_status_shortcode');

add_action('rest_api_init',function(){
    $permission=function(){ return current_user_can('edit_posts'); };
    $routes=array('/status'=>'/v1150/status','/runtime'=>'/calculation-engine/v1/runtimes/julia',
                  '/contract'=>'/calculation-engine/v1/runtimes/julia/contract');
    foreach($routes as $wp_path=>$backend_path){
        register_rest_route('sc-workbench/v1/v1150',$wp_path,array(
            'methods'=>'GET','permission_callback'=>$permission,
            'callback'=>function() use ($backend_path){ return scwb_v1150_proxy_response($backend_path); }));
    }
    register_rest_route('sc-workbench/v1/v1150','/execute',array(
        'methods'=>'POST','permission_callback'=>$permission,
        'callback'=>function($request){ return scwb_v1150_proxy_response(
            '/calculation-engine/v1/runtimes/julia/execute','POST',$request->get_json_params()); }));
    register_rest_route('sc-workbench/v1/v1150','/calculation-object',array(
        'methods'=>'POST','permission_callback'=>$permission,
        'callback'=>function($request){ return scwb_v1150_proxy_response(
            '/calculation-engine/v1/runtimes/julia/calculation-object','POST',$request->get_json_params()); }));
});
