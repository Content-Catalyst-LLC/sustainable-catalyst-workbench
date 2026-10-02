<?php
/**
 * Workbench v10.10.4 — Dual-Mode WordPress + Standalone Certification.
 *
 * WordPress remains an optional presentation/proxy adapter.
 * Standalone backend contract: wordpressRequired = false.
 * Authoritative computation remains in FastAPI.
 */
if (!defined('ABSPATH')) { exit; }

function scwb_v10104_backend_request($path, $method='GET', $body=null) {
    if (function_exists('scwb_v10103_backend_request')) {
        return scwb_v10103_backend_request($path, $method, $body);
    }
    if (function_exists('scwb_v10102_backend_request')) {
        return scwb_v10102_backend_request($path, $method, $body);
    }

    return array(
        'ok' => false,
        'error' => 'Workbench backend adapter unavailable',
        '_httpStatus' => 503,
    );
}

function scwb_v10104_proxy_response($path) {
    $data = scwb_v10104_backend_request($path);
    $status = intval($data['_httpStatus'] ?? 200);
    unset($data['_httpStatus']);
    return new WP_REST_Response($data, $status);
}

function scwb_v10104_certification_shortcode() {
    $data = scwb_v10104_backend_request('/v10104/status');
    if (empty($data['ok'])) {
        return '<div class="scwb-v10104-status">Dual-mode certification unavailable.</div>';
    }

    return sprintf(
        '<div class="scwb-v10104-status"><strong>Workbench v%s</strong> · Dual-mode certification %s · Standalone certified · WordPress adapter certified</div>',
        esc_html($data['version'] ?? '10.10.4'),
        esc_html($data['certification'] ?? 'unknown')
    );
}
add_shortcode('sc_workbench_dual_mode_certification', 'scwb_v10104_certification_shortcode');

add_action('rest_api_init', function () {
    $permission = function () { return current_user_can('edit_posts'); };

    $routes = array(
        '/status' => '/v10104/status',
        '/report' => '/certification/dual-mode',
        '/routes' => '/certification/dual-mode/routes',
        '/probe' => '/certification/dual-mode/probe',
    );

    foreach ($routes as $wp_path => $backend_path) {
        register_rest_route('sc-workbench/v1/v10104', $wp_path, array(
            'methods' => 'GET',
            'permission_callback' => $permission,
            'callback' => function () use ($backend_path) {
                return scwb_v10104_proxy_response($backend_path);
            },
        ));
    }
});
