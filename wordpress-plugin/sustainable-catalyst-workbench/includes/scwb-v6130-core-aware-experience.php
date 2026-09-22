<?php
if (!defined('ABSPATH')) { exit; }

function scwb_v6130_core_aware_status() {
    $base = rtrim((string) get_option('scwb_backend_url', 'https://workbench-api.sustainablecatalyst.com'), '/');
    $response = wp_remote_get($base . '/v6130/status', array('timeout' => 8));
    if (is_wp_error($response)) {
        return array('ok' => false, 'version' => SCWB_VERSION, 'error' => $response->get_error_message());
    }
    $body = json_decode(wp_remote_retrieve_body($response), true);
    return is_array($body) ? $body : array('ok' => false, 'version' => SCWB_VERSION, 'error' => 'invalid-json');
}

function scwb_v6130_core_aware_shortcode() {
    $status = scwb_v6130_core_aware_status();
    $ok = !empty($status['ok']);
    $version = isset($status['version']) ? esc_html($status['version']) : esc_html(SCWB_VERSION);
    $items = array(
        'Core-aware context' => !empty($status['coreAwareContext']),
        'Compatibility evaluation' => !empty($status['compatibilityEvaluation']),
        'Next-action planning' => !empty($status['nextActionPlanning']),
        'Research-state awareness' => !empty($status['researchStateAwareness']),
        'Predictive / forensic / visual awareness' => !empty($status['predictiveForensicVisualAwareness']),
    );
    $html = '<div class="scwb-runtime-status scwb-v6130">';
    $html .= '<strong>' . esc_html($ok ? 'Core-Aware Workbench Experience Online' : 'Core-Aware Workbench Experience Unavailable') . '</strong>';
    $html .= '<br><span>Workbench ' . $version . '</span>';
    if ($ok) {
        $html .= '<ul>';
        foreach ($items as $label => $enabled) {
            $html .= '<li>' . esc_html($label) . ': ' . esc_html($enabled ? 'Active' : 'Unavailable') . '</li>';
        }
        $html .= '</ul>';
    }
    $html .= '</div>';
    return $html;
}
add_shortcode('sc_workbench_core_aware_status', 'scwb_v6130_core_aware_shortcode');

function scwb_v6130_register_rest_routes() {
    register_rest_route('sc-workbench/v1', '/core-aware/status', array(
        'methods' => 'GET',
        'callback' => 'scwb_v6130_core_aware_status',
        'permission_callback' => '__return_true',
    ));
}
add_action('rest_api_init', 'scwb_v6130_register_rest_routes');
