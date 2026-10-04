<?php
/**
 * Workbench v12.9.0 — Standalone Migration Certification.
 *
 * wordpressRequired = false.
 * WordPress compatibility/status adapter only.
 *
 * Migration authority, application state, authentication, computation,
 * persistence, rendering, notebooks, history, reproducibility packages, and
 * launch validation remain outside WordPress.
 */
if (!defined('ABSPATH')) { exit; }

function scwb_v1290_backend_request($path,$method='GET',$body=null){
    if(function_exists('scwb_v1100_backend_request')){
        return scwb_v1100_backend_request($path,$method,$body);
    }
    return array(
        'ok'=>false,
        'error'=>'Workbench backend adapter unavailable',
        '_httpStatus'=>503
    );
}

function scwb_v1290_migration_status_shortcode(){
    $data=scwb_v1290_backend_request('/v1290/status');
    if(empty($data['ok'])){
        return '<div class="scwb-v1290-status">Standalone migration certification unavailable.</div>';
    }
    return sprintf(
        '<div class="scwb-v1290-status"><strong>Workbench v%s</strong> · Standalone migration certified · WordPress optional</div>',
        esc_html($data['version'] ?? '12.9.0')
    );
}
add_shortcode('sc_workbench_migration_certification','scwb_v1290_migration_status_shortcode');

add_action('rest_api_init',function(){
    $permission=function(){return current_user_can('edit_posts');};

    register_rest_route('sc-workbench/v1/v1290','/status',array(
      'methods'=>'GET',
      'permission_callback'=>$permission,
      'callback'=>function(){
          return new WP_REST_Response(scwb_v1290_backend_request('/v1290/status'),200);
      }));

    register_rest_route('sc-workbench/v1/v1290','/certification',array(
      'methods'=>'GET',
      'permission_callback'=>$permission,
      'callback'=>function(){
          return new WP_REST_Response(scwb_v1290_backend_request('/standalone/v1/migration/certification'),200);
      }));

    register_rest_route('sc-workbench/v1/v1290','/runbook',array(
      'methods'=>'GET',
      'permission_callback'=>$permission,
      'callback'=>function(){
          return new WP_REST_Response(scwb_v1290_backend_request('/standalone/v1/migration/runbook'),200);
      }));
});
