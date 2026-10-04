<?php
/**
 * Workbench v12.8.0 — WordPress State Dependency Elimination.
 *
 * wordpressRequired = false.
 * WordPress compatibility adapter only.
 *
 * This adapter MUST NOT store canonical v12 Workbench application state in
 * WordPress options, user meta, post meta, transients, or nonce-backed sessions.
 * It may expose status and compatibility links to the standalone application.
 */
if (!defined('ABSPATH')) { exit; }

function scwb_v1280_backend_request($path,$method='GET',$body=null){
    if(function_exists('scwb_v1100_backend_request')){
        return scwb_v1100_backend_request($path,$method,$body);
    }
    return array(
        'ok'=>false,
        'error'=>'Workbench backend adapter unavailable',
        '_httpStatus'=>503
    );
}

function scwb_v1280_status_shortcode(){
    $data=scwb_v1280_backend_request('/v1280/status');
    if(empty($data['ok'])){
        return '<div class="scwb-v1280-status">Standalone state certification unavailable.</div>';
    }
    return sprintf(
        '<div class="scwb-v1280-status"><strong>Workbench v%s</strong> · Standalone state authority certified · WordPress compatibility only</div>',
        esc_html($data['version'] ?? '12.8.0')
    );
}
add_shortcode('sc_workbench_state_authority','scwb_v1280_status_shortcode');

add_action('rest_api_init',function(){
    $permission=function(){return current_user_can('edit_posts');};

    register_rest_route('sc-workbench/v1/v1280','/status',array(
      'methods'=>'GET',
      'permission_callback'=>$permission,
      'callback'=>function(){
          return new WP_REST_Response(scwb_v1280_backend_request('/v1280/status'),200);
      }));

    register_rest_route('sc-workbench/v1/v1280','/state-authority',array(
      'methods'=>'GET',
      'permission_callback'=>$permission,
      'callback'=>function(){
          return new WP_REST_Response(scwb_v1280_backend_request('/standalone/v1/state-authority'),200);
      }));

    register_rest_route('sc-workbench/v1/v1280','/certification',array(
      'methods'=>'GET',
      'permission_callback'=>$permission,
      'callback'=>function(){
          return new WP_REST_Response(scwb_v1280_backend_request('/standalone/v1/state-dependency/certification'),200);
      }));
});
