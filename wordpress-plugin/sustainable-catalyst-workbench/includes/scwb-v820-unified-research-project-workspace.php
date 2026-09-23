<?php
if (!defined('ABSPATH')) { exit; }

function scwb_v820_api_base() {
    $base = defined('SCWB_API_BASE') ? SCWB_API_BASE : get_option('scwb_api_base', 'https://workbench-api.sustainablecatalyst.com');
    return rtrim((string)$base, '/');
}

function scwb_v820_status_payload() {
    $response = wp_remote_get(scwb_v820_api_base() . '/v820/status', array('timeout' => 8));
    if (is_wp_error($response)) return array('ok'=>false,'version'=>'8.2.0','error'=>$response->get_error_message());
    $body = json_decode(wp_remote_retrieve_body($response), true);
    return is_array($body) ? $body : array('ok'=>false,'version'=>'8.2.0','error'=>'Invalid backend response');
}

add_shortcode('sc_workbench_research_project_status', function() {
    $s = scwb_v820_status_payload();
    $ok = !empty($s['ok']);
    $label = $ok ? 'Research Project Workspace Online' : 'Research Project Workspace Unavailable';
    return '<div class="scwb-status scwb-v820"><strong>'.esc_html($label).'</strong><br><span>Workbench '.esc_html($s['version'] ?? '8.2.0').'</span></div>';
});

add_action('rest_api_init', function() {
    register_rest_route('sc-workbench/v1', '/research-project/status', array(
        'methods' => 'GET', 'callback' => function() { return rest_ensure_response(scwb_v820_status_payload()); },
        'permission_callback' => '__return_true'
    ));
});
