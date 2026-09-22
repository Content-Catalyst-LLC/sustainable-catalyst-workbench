<?php
if (!defined('ABSPATH')) { exit; }

function scwb_v700_unified_execution_status() {
    $base = rtrim((string) get_option('scwb_backend_url', 'https://workbench-api.sustainablecatalyst.com'), '/');
    $response = wp_remote_get($base . '/v700/status', array('timeout' => 8));
    if (is_wp_error($response)) {
        return array('ok' => false, 'version' => SCWB_VERSION, 'error' => $response->get_error_message());
    }
    $body = json_decode(wp_remote_retrieve_body($response), true);
    return is_array($body) ? $body : array('ok' => false, 'version' => SCWB_VERSION, 'error' => 'invalid-json');
}

function scwb_v700_unified_execution_shortcode() {
    $status = scwb_v700_unified_execution_status();
    $ok = !empty($status['ok']);
    $version = isset($status['version']) ? esc_html($status['version']) : esc_html(SCWB_VERSION);
    $html = '<div class="scwb-runtime-status scwb-v700">';
    $html .= '<strong>' . esc_html($ok ? 'Unified Scientific & Engineering Runtime Online' : 'Unified Scientific & Engineering Runtime Unavailable') . '</strong>';
    $html .= '<br><span>Workbench ' . $version . '</span>';
    if ($ok) {
        $html .= '<ul>';
        $html .= '<li>Allow-listed specialist operations: ' . esc_html((string) ($status['operationCount'] ?? 0)) . '</li>';
        $html .= '<li>Scientific / engineering categories: ' . esc_html((string) ($status['categoryCount'] ?? 0)) . '</li>';
        $html .= '<li>Canonical execution envelope: ' . esc_html(!empty($status['canonicalExecutionEnvelope']) ? 'Active' : 'Unavailable') . '</li>';
        $html .= '<li>Workflow execution: ' . esc_html(!empty($status['workflowExecution']) ? 'Active' : 'Unavailable') . '</li>';
        $html .= '<li>Core lineage planning: ' . esc_html(!empty($status['coreLineagePlanning']) ? 'Active' : 'Unavailable') . '</li>';
        $html .= '</ul>';
        $html .= '<small>Execution remains bounded and explicit; no arbitrary code, automatic Core persistence, scientific-validity certification, or truth determination.</small>';
    }
    $html .= '</div>';
    return $html;
}
add_shortcode('sc_workbench_unified_execution_status', 'scwb_v700_unified_execution_shortcode');

function scwb_v700_register_rest_routes() {
    register_rest_route('sc-workbench/v1', '/unified-execution/status', array(
        'methods' => 'GET',
        'callback' => 'scwb_v700_unified_execution_status',
        'permission_callback' => '__return_true',
    ));
}
add_action('rest_api_init', 'scwb_v700_register_rest_routes');
