<?php
if (!defined('ABSPATH')) { exit; }

function scwb_v690_visual_reasoning_status() {
    $base = rtrim((string) get_option('scwb_backend_url', 'https://workbench-api.sustainablecatalyst.com'), '/');
    $response = wp_remote_get($base . '/v690/status', array('timeout' => 8));
    if (is_wp_error($response)) {
        return array('ok' => false, 'version' => SCWB_VERSION, 'error' => $response->get_error_message());
    }
    $body = json_decode(wp_remote_retrieve_body($response), true);
    return is_array($body) ? $body : array('ok' => false, 'version' => SCWB_VERSION, 'error' => 'invalid-json');
}

function scwb_v690_visual_reasoning_shortcode() {
    $status = scwb_v690_visual_reasoning_status();
    $ok = !empty($status['ok']);
    $label = $ok ? 'Visual Reasoning Runtime Adapter Online' : 'Visual Reasoning Runtime Adapter Unavailable';
    $version = isset($status['version']) ? esc_html($status['version']) : esc_html(SCWB_VERSION);
    return '<div class="scwb-runtime-status scwb-v690"><strong>' . esc_html($label) . '</strong><br><span>Workbench ' . $version . '</span></div>';
}
add_shortcode('sc_workbench_visual_reasoning_status', 'scwb_v690_visual_reasoning_shortcode');
