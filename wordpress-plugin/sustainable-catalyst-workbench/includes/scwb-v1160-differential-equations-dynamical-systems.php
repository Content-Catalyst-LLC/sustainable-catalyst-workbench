<?php
/**
 * Workbench v11.6.0 — Differential Equations & Dynamical Systems.
 * WordPress remains optional; wordpressRequired = false.
 * Authoritative computation remains in FastAPI.
 */
if (!defined('ABSPATH')) { exit; }

function scwb_v1160_backend_request($path,$method='GET',$body=null) {
    if (function_exists('scwb_v1100_backend_request')) {
        return scwb_v1100_backend_request($path,$method,$body);
    }
    return array('ok'=>false,'error'=>'Workbench backend adapter unavailable','_httpStatus'=>503);
}
function scwb_v1160_proxy_response($path,$method='GET',$body=null) {
    $data=scwb_v1160_backend_request($path,$method,$body);
    $status=intval($data['_httpStatus'] ?? 200); unset($data['_httpStatus']);
    return new WP_REST_Response($data,$status);
}
function scwb_v1160_status_shortcode() {
    $data=scwb_v1160_backend_request('/v1160/status');
    if (empty($data['ok'])) return '<div class="scwb-v1160-status">Differential Equations runtime unavailable.</div>';
    return sprintf('<div class="scwb-v1160-status"><strong>Workbench v%s</strong> · Differential Equations & Dynamical Systems ready · WordPress optional</div>',
        esc_html($data['version'] ?? '11.6.0'));
}
add_shortcode('sc_workbench_dynamics_status','scwb_v1160_status_shortcode');

add_action('rest_api_init',function(){
    $permission=function(){ return current_user_can('edit_posts'); };
    register_rest_route('sc-workbench/v1/v1160','/status',array(
        'methods'=>'GET','permission_callback'=>$permission,
        'callback'=>function(){ return scwb_v1160_proxy_response('/v1160/status'); }));
    register_rest_route('sc-workbench/v1/v1160','/dynamics',array(
        'methods'=>'POST','permission_callback'=>$permission,
        'callback'=>function($request){ return scwb_v1160_proxy_response(
            '/calculation-engine/v1/dynamics','POST',$request->get_json_params()); }));
    register_rest_route('sc-workbench/v1/v1160','/calculation-object',array(
        'methods'=>'POST','permission_callback'=>$permission,
        'callback'=>function($request){ return scwb_v1160_proxy_response(
            '/calculation-engine/v1/dynamics/calculation-object','POST',$request->get_json_params()); }));
});
