<?php
/**
 * Workbench v12.10.0 — WordPress-Optional Production Workbench.
 *
 * wordpressRequired = false.
 * WordPress optional compatibility adapter only.
 *
 * The canonical production Workbench is:
 * standalone web app -> FastAPI -> persistent v12 state.
 *
 * This adapter publishes status/certification information and may remain
 * installed on sustainablecatalyst.com for public-site compatibility.
 */
if (!defined('ABSPATH')) { exit; }

function scwb_v12100_backend_request($path,$method='GET',$body=null){
    if(function_exists('scwb_v1100_backend_request')){
        return scwb_v1100_backend_request($path,$method,$body);
    }
    return array(
        'ok'=>false,
        'error'=>'Workbench backend adapter unavailable',
        '_httpStatus'=>503
    );
}

function scwb_v12100_production_status_shortcode(){
    $data=scwb_v12100_backend_request('/v12100/status');
    if(empty($data['ok'])){
        return '<div class="scwb-v12100-status">Workbench production certification unavailable.</div>';
    }
    $state=!empty($data['productionReady'])?'Production ready':'Production configuration pending';
    return sprintf(
        '<div class="scwb-v12100-status"><strong>Workbench v%s</strong> · %s · WordPress optional</div>',
        esc_html($data['version'] ?? '12.10.0'),
        esc_html($state)
    );
}
add_shortcode('sc_workbench_production_status','scwb_v12100_production_status_shortcode');

add_action('rest_api_init',function(){
    $permission=function(){return current_user_can('edit_posts');};

    register_rest_route('sc-workbench/v1/v12100','/status',array(
      'methods'=>'GET',
      'permission_callback'=>$permission,
      'callback'=>function(){
          return new WP_REST_Response(scwb_v12100_backend_request('/v12100/status'),200);
      }));

    register_rest_route('sc-workbench/v1/v12100','/readiness',array(
      'methods'=>'GET',
      'permission_callback'=>$permission,
      'callback'=>function(){
          return new WP_REST_Response(scwb_v12100_backend_request('/standalone/v1/production/readiness'),200);
      }));

    register_rest_route('sc-workbench/v1/v12100','/certification',array(
      'methods'=>'GET',
      'permission_callback'=>$permission,
      'callback'=>function(){
          return new WP_REST_Response(scwb_v12100_backend_request('/standalone/v1/production/certification'),200);
      }));
});
