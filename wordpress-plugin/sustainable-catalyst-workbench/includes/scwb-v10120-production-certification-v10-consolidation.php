<?php
/**
 * Workbench v10.12.0 — Production Certification & v10 Consolidation.
 *
 * WordPress remains an optional presentation/proxy adapter.
 * Standalone backend contract: wordpressRequired = false.
 * Authoritative computation remains in FastAPI.
 */
if (!defined('ABSPATH')) { exit; }

function scwb_v10120_backend_request($path, $method='GET', $body=null) {
    if (function_exists('scwb_v10110_backend_request')) {
        return scwb_v10110_backend_request($path, $method, $body);
    }
    if (function_exists('scwb_v10103_backend_request')) {
        return scwb_v10103_backend_request($path, $method, $body);
    }
    return array(
        'ok' => false,
        'error' => 'Workbench backend adapter unavailable',
        '_httpStatus' => 503,
    );
}

function scwb_v10120_proxy_response($path) {
    $data = scwb_v10120_backend_request($path);
    $status = intval($data['_httpStatus'] ?? 200);
    unset($data['_httpStatus']);
    return new WP_REST_Response($data, $status);
}

function scwb_v10120_certification_shortcode() {
    $data = scwb_v10120_backend_request('/v10120/status');
    if (empty($data['ok'])) {
        return '<div class="scwb-v10120-status">Workbench v10 production certification unavailable.</div>';
    }

    return sprintf(
        '<div class="scwb-v10120-status"><strong>Workbench v%s</strong> · v10 production certification %s · Standalone ready · WordPress optional</div>',
        esc_html($data['version'] ?? '10.12.0'),
        esc_html($data['certification'] ?? 'unknown')
    );
}
add_shortcode('sc_workbench_v10_production_certification', 'scwb_v10120_certification_shortcode');

add_action('rest_api_init', function () {
    $permission = function () { return current_user_can('edit_posts'); };

    $routes = array(
        '/status' => '/v10120/status',
        '/certification' => '/certification/v10',
        '/releases' => '/certification/v10/releases',
        '/contracts' => '/certification/v10/contracts',
        '/probe' => '/certification/v10/probe',
    );

    foreach ($routes as $wp_path => $backend_path) {
        register_rest_route('sc-workbench/v1/v10120', $wp_path, array(
            'methods' => 'GET',
            'permission_callback' => $permission,
            'callback' => function () use ($backend_path) {
                return scwb_v10120_proxy_response($backend_path);
            },
        ));
    }
});
