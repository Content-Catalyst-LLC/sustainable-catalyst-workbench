<?php
/** Workbench v8.4.0 — Interactive Execution Console status bridge. */
if (!defined('ABSPATH')) { exit; }
function scwb_v840_backend_base() { return rtrim((string)get_option('scwb_backend_url','https://workbench-api.sustainablecatalyst.com'), '/'); }
function scwb_v840_get_json($path) {
    $response=wp_remote_get(scwb_v840_backend_base().$path,array('timeout'=>8));
    if (is_wp_error($response)) { return array('ok'=>false,'error'=>$response->get_error_message()); }
    $body=json_decode(wp_remote_retrieve_body($response),true); return is_array($body)?$body:array('ok'=>false,'error'=>'Invalid backend response');
}
function scwb_v840_status_shortcode() {
    $status=scwb_v840_get_json('/v840/status'); $manifest=scwb_v840_get_json('/execution-console/manifest');
    $ok=!empty($status['ok'])&&!empty($manifest['ok']); $version=isset($status['version'])?esc_html($status['version']):'unknown';
    return '<div class="scwb-v840-status"><strong>Interactive Execution Console '.esc_html($ok?'Online':'Unavailable').'</strong><br><span>Workbench '.$version.'</span></div>';
}
add_shortcode('sc_workbench_execution_console_status','scwb_v840_status_shortcode');
add_action('rest_api_init',function(){ register_rest_route('sc-workbench/v1','/execution-console/status',array('methods'=>'GET','permission_callback'=>'__return_true','callback'=>function(){ return rest_ensure_response(scwb_v840_get_json('/v840/status')); })); });
