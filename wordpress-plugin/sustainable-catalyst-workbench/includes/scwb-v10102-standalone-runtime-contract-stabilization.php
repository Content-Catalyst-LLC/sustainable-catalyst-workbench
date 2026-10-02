<?php
/**
 * Workbench v10.10.2 — Standalone Runtime Health, Bootstrap & API Contract Stabilization.
 *
 * WordPress remains an optional presentation/proxy adapter.
 * Standalone backend contract: wordpressRequired = false.
 * Authoritative computation remains in FastAPI.
 */
if (!defined('ABSPATH')) { exit; }

function scwb_v10102_backend_request($path, $method='GET', $body=null) {
    if (function_exists('scwb_v10101_backend_request')) {
        return scwb_v10101_backend_request($path, $method, $body);
    }
    if (function_exists('scwb_v10100_backend_request')) {
        return scwb_v10100_backend_request($path, $method, $body);
    }

    $base = defined('SCWB_BACKEND_URL')
        ? rtrim(SCWB_BACKEND_URL, '/')
        : rtrim((string)get_option('scwb_backend_url', 'https://workbench-api.sustainablecatalyst.com'), '/');

    $args = array(
        'method' => $method,
        'timeout' => 30,
        'headers' => array('Accept' => 'application/json', 'Content-Type' => 'application/json'),
    );
    if ($body !== null) { $args['body'] = wp_json_encode($body); }

    $response = wp_remote_request($base . $path, $args);
    if (is_wp_error($response)) {
        return array('ok' => false, 'error' => $response->get_error_message(), '_httpStatus' => 502);
    }

    $status = wp_remote_retrieve_response_code($response);
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) { $data = array('ok' => false, 'error' => 'Invalid backend response'); }
    $data['_httpStatus'] = $status;
    return $data;
}

function scwb_v10102_proxy_response($path) {
    $data = scwb_v10102_backend_request($path);
    $status = intval($data['_httpStatus'] ?? 200);
    unset($data['_httpStatus']);
    return new WP_REST_Response($data, $status);
}

function scwb_v10102_standalone_status_shortcode() {
    $data = scwb_v10102_backend_request('/v10102/status');
    if (empty($data['ok'])) {
        return '<div class="scwb-v10102-status">Standalone Workbench runtime unavailable.</div>';
    }
    return sprintf(
        '<div class="scwb-v10102-status"><strong>Workbench v%s</strong> · Standalone runtime ready · API contract v%s · WordPress optional</div>',
        esc_html($data['version'] ?? '10.10.2'),
        esc_html($data['contractVersion'] ?? '1.0')
    );
}
add_shortcode('sc_workbench_standalone_status', 'scwb_v10102_standalone_status_shortcode');

add_action('rest_api_init', function () {
    $permission = function () { return current_user_can('edit_posts'); };

    $routes = array(
        '/status' => '/v10102/status',
        '/health' => '/standalone/v1/health',
        '/bootstrap' => '/standalone/v1/bootstrap',
        '/api-contract' => '/standalone/v1/api-contract',
        '/compatibility' => '/standalone/v1/compatibility',
    );

    foreach ($routes as $wp_path => $backend_path) {
        register_rest_route('sc-workbench/v1/v10102', $wp_path, array(
            'methods' => 'GET',
            'permission_callback' => $permission,
            'callback' => function () use ($backend_path) {
                return scwb_v10102_proxy_response($backend_path);
            },
        ));
    }
});
