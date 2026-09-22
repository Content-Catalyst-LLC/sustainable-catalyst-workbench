<?php
if (!defined('ABSPATH')) { exit; }

function scwb_v710_execution_object_status() {
    $base = rtrim((string) get_option('scwb_backend_url', 'https://workbench-api.sustainablecatalyst.com'), '/');
    $response = wp_remote_get($base . '/v710/status', array('timeout' => 8));
    if (is_wp_error($response)) {
        return array('ok' => false, 'version' => SCWB_VERSION, 'error' => $response->get_error_message());
    }
    $body = json_decode(wp_remote_retrieve_body($response), true);
    return is_array($body) ? $body : array('ok' => false, 'version' => SCWB_VERSION, 'error' => 'invalid-json');
}

function scwb_v710_execution_object_shortcode() {
    $status = scwb_v710_execution_object_status();
    $ok = !empty($status['ok']);
    $version = isset($status['version']) ? esc_html($status['version']) : esc_html(SCWB_VERSION);
    $html = '<div class="scwb-runtime-status scwb-v710">';
    $html .= '<strong>' . esc_html($ok ? 'Unified Execution Object Model Online' : 'Unified Execution Object Model Unavailable') . '</strong>';
    $html .= '<br><span>Workbench ' . $version . '</span>';
    if ($ok) {
        $html .= '<ul>';
        $html .= '<li>Single execution objects: ' . esc_html(!empty($status['singleExecutionObjects']) ? 'Active' : 'Unavailable') . '</li>';
        $html .= '<li>Workflow execution objects: ' . esc_html(!empty($status['workflowExecutionObjects']) ? 'Active' : 'Unavailable') . '</li>';
        $html .= '<li>Content-addressed integrity: ' . esc_html(!empty($status['contentAddressedIntegrity']) ? 'Active' : 'Unavailable') . '</li>';
        $html .= '<li>Explicit object revisions: ' . esc_html(!empty($status['explicitObjectRevisions']) ? 'Active' : 'Unavailable') . '</li>';
        $html .= '<li>Core binding planning: ' . esc_html(!empty($status['coreBindingPlanning']) ? 'Active' : 'Unavailable') . '</li>';
        $html .= '</ul>';
        $html .= '<small>Execution objects are reference-first and content-addressed; no automatic persistence, replay, scientific-validity certification, or truth determination.</small>';
    }
    $html .= '</div>';
    return $html;
}
add_shortcode('sc_workbench_execution_object_status', 'scwb_v710_execution_object_shortcode');

function scwb_v710_register_rest_routes() {
    register_rest_route('sc-workbench/v1', '/execution-object/status', array(
        'methods' => 'GET',
        'callback' => 'scwb_v710_execution_object_status',
        'permission_callback' => '__return_true',
    ));
}
add_action('rest_api_init', 'scwb_v710_register_rest_routes');
