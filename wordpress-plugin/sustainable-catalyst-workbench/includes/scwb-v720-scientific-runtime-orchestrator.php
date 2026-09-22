<?php
if (!defined('ABSPATH')) { exit; }

function scwb_v720_runtime_orchestrator_status() {
    $base = rtrim((string) get_option('scwb_backend_url', 'https://workbench-api.sustainablecatalyst.com'), '/');
    $response = wp_remote_get($base . '/v720/status', array('timeout' => 8));
    if (is_wp_error($response)) {
        return array('ok' => false, 'version' => SCWB_VERSION, 'error' => $response->get_error_message());
    }
    $body = json_decode(wp_remote_retrieve_body($response), true);
    return is_array($body) ? $body : array('ok' => false, 'version' => SCWB_VERSION, 'error' => 'invalid-json');
}

function scwb_v720_runtime_orchestrator_shortcode() {
    $status = scwb_v720_runtime_orchestrator_status();
    $ok = !empty($status['ok']);
    $version = isset($status['version']) ? esc_html($status['version']) : esc_html(SCWB_VERSION);
    $html = '<div class="scwb-runtime-status scwb-v720">';
    $html .= '<strong>' . esc_html($ok ? 'Scientific Runtime Orchestrator Online' : 'Scientific Runtime Orchestrator Unavailable') . '</strong>';
    $html .= '<br><span>Workbench ' . $version . '</span>';
    if ($ok) {
        $html .= '<ul>';
        $html .= '<li>Runtime adapters: ' . esc_html((string) ($status['adapterCount'] ?? 0)) . '</li>';
        $html .= '<li>Local bounded adapters: ' . esc_html((string) ($status['localAdapterCount'] ?? 0)) . '</li>';
        $html .= '<li>Deterministic routing: ' . esc_html(!empty($status['deterministicRouting']) ? 'Active' : 'Unavailable') . '</li>';
        $html .= '<li>Workflow orchestration: ' . esc_html(!empty($status['workflowOrchestration']) ? 'Active' : 'Unavailable') . '</li>';
        $html .= '<li>Core workflow planning: ' . esc_html(!empty($status['coreResearchWorkflowPlanning']) ? 'Active' : 'Unavailable') . '</li>';
        $html .= '</ul>';
        $html .= '<small>Orchestration is allow-listed and explicit. External R/Julia/ML adapters remain plan-only; no arbitrary code or automatic Core/external dispatch is authorized.</small>';
    }
    $html .= '</div>';
    return $html;
}
add_shortcode('sc_workbench_runtime_orchestrator_status', 'scwb_v720_runtime_orchestrator_shortcode');

function scwb_v720_register_rest_routes() {
    register_rest_route('sc-workbench/v1', '/runtime-orchestrator/status', array(
        'methods' => 'GET',
        'callback' => 'scwb_v720_runtime_orchestrator_status',
        'permission_callback' => '__return_true',
    ));
}
add_action('rest_api_init', 'scwb_v720_register_rest_routes');
