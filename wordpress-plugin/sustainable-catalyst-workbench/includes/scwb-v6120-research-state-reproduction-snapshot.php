<?php
if (!defined('ABSPATH')) { exit; }

function scwb_v6120_research_state_status() {
    $base = rtrim((string) get_option('scwb_backend_url', 'https://workbench-api.sustainablecatalyst.com'), '/');
    $response = wp_remote_get($base . '/v6120/status', array('timeout' => 8));
    if (is_wp_error($response)) {
        return array('ok' => false, 'version' => SCWB_VERSION, 'error' => $response->get_error_message());
    }
    $body = json_decode(wp_remote_retrieve_body($response), true);
    return is_array($body) ? $body : array('ok' => false, 'version' => SCWB_VERSION, 'error' => 'invalid-json');
}

function scwb_v6120_research_state_shortcode() {
    $status = scwb_v6120_research_state_status();
    $ok = !empty($status['ok']);
    $label = $ok ? 'Research State & Reproduction Runtime Online' : 'Research State & Reproduction Runtime Unavailable';
    $version = isset($status['version']) ? esc_html($status['version']) : esc_html(SCWB_VERSION);
    return '<div class="scwb-runtime-status scwb-v6120"><strong>' . esc_html($label) . '</strong><br><span>Workbench ' . $version . '</span></div>';
}
add_shortcode('sc_workbench_research_state_status', 'scwb_v6120_research_state_shortcode');

function scwb_v6120_register_rest_routes() {
    register_rest_route('sc-workbench/v1', '/research-state/status', array(
        'methods' => 'GET',
        'callback' => 'scwb_v6120_research_state_status',
        'permission_callback' => '__return_true',
    ));
}
add_action('rest_api_init', 'scwb_v6120_register_rest_routes');
