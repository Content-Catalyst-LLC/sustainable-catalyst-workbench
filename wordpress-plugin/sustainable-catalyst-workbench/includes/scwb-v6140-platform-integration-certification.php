<?php
if (!defined('ABSPATH')) { exit; }

function scwb_v6140_certification_status() {
    $base = rtrim((string) get_option('scwb_backend_url', 'https://workbench-api.sustainablecatalyst.com'), '/');
    $response = wp_remote_get($base . '/v6140/status', array('timeout' => 8));
    if (is_wp_error($response)) {
        return array('ok' => false, 'version' => SCWB_VERSION, 'error' => $response->get_error_message());
    }
    $body = json_decode(wp_remote_retrieve_body($response), true);
    return is_array($body) ? $body : array('ok' => false, 'version' => SCWB_VERSION, 'error' => 'invalid-json');
}

function scwb_v6140_certification_shortcode() {
    $status = scwb_v6140_certification_status();
    $ok = !empty($status['ok']);
    $version = isset($status['version']) ? esc_html($status['version']) : esc_html(SCWB_VERSION);
    $items = array(
        'Local conformance report' => !empty($status['localConformanceReport']),
        'Declared conformance' => !empty($status['declaredConformance']),
        'Suite / product / case / run planning' => !empty($status['productCaseRunPlanning']),
        'Exchange / trace / reproduction checks' => !empty($status['exchangeTraceReproductionChecks']),
        'Immutable certification snapshot planning' => !empty($status['immutableCertificationSnapshotPlanning']),
    );
    $html = '<div class="scwb-runtime-status scwb-v6140">';
    $html .= '<strong>' . esc_html($ok ? 'Platform Integration Certification Online' : 'Platform Integration Certification Unavailable') . '</strong>';
    $html .= '<br><span>Workbench ' . $version . '</span>';
    if ($ok) {
        $html .= '<ul>';
        foreach ($items as $label => $enabled) {
            $html .= '<li>' . esc_html($label) . ': ' . esc_html($enabled ? 'Active' : 'Unavailable') . '</li>';
        }
        $html .= '</ul>';
        $html .= '<small>Scope: runtime-contract conformance only; not scientific-validity or product-quality certification.</small>';
    }
    $html .= '</div>';
    return $html;
}
add_shortcode('sc_workbench_platform_certification_status', 'scwb_v6140_certification_shortcode');

function scwb_v6140_register_rest_routes() {
    register_rest_route('sc-workbench/v1', '/platform-certification/status', array(
        'methods' => 'GET',
        'callback' => 'scwb_v6140_certification_status',
        'permission_callback' => '__return_true',
    ));
}
add_action('rest_api_init', 'scwb_v6140_register_rest_routes');
