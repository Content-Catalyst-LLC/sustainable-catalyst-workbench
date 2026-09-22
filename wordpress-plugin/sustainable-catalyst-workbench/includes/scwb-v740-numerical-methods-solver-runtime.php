<?php
if (!defined('ABSPATH')) { exit; }

function scwb_v740_backend_url($path) {
    $base = rtrim((string) get_option('scwb_backend_url', 'https://workbench-api.sustainablecatalyst.com'), '/');
    return $base . $path;
}

function scwb_v740_status_payload() {
    $response = wp_remote_get(scwb_v740_backend_url('/v740/status'), array('timeout' => 8));
    if (is_wp_error($response)) {
        return array('ok' => false, 'version' => SCWB_VERSION, 'error' => $response->get_error_message());
    }
    $body = json_decode(wp_remote_retrieve_body($response), true);
    return is_array($body) ? $body : array('ok' => false, 'version' => SCWB_VERSION, 'error' => 'Invalid backend response');
}

add_shortcode('sc_workbench_numerical_solver_status', function () {
    $data = scwb_v740_status_payload();
    $ok = !empty($data['ok']);
    $label = $ok ? 'Numerical Solver Runtime Online' : 'Numerical Solver Runtime Unavailable';
    $count = isset($data['solverCount']) ? ' · ' . intval($data['solverCount']) . ' solvers' : '';
    return '<div class="scwb-numerical-solver-status"><strong>' . esc_html($label) . '</strong><br><span>Workbench ' . esc_html($data['version'] ?? SCWB_VERSION) . esc_html($count) . '</span></div>';
});

add_action('rest_api_init', function () {
    register_rest_route('sc-workbench/v1', '/numerical-solver/status', array(
        'methods' => 'GET',
        'callback' => function () { return rest_ensure_response(scwb_v740_status_payload()); },
        'permission_callback' => '__return_true',
    ));
});
