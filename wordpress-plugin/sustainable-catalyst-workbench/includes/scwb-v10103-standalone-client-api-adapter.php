<?php
/**
 * Workbench v10.10.3 — Standalone Client/API Adapter Foundation.
 *
 * WordPress remains an optional presentation/proxy adapter.
 * Standalone backend contract: wordpressRequired = false.
 * Authoritative computation remains in FastAPI.
 */
if (!defined('ABSPATH')) { exit; }

function scwb_v10103_backend_request($path, $method='GET', $body=null) {
    if (function_exists('scwb_v10102_backend_request')) {
        return scwb_v10102_backend_request($path, $method, $body);
    }
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

function scwb_v10103_proxy_response($path, $method='GET', $body=null) {
    $data = scwb_v10103_backend_request($path, $method, $body);
    $status = intval($data['_httpStatus'] ?? 200);
    unset($data['_httpStatus']);
    return new WP_REST_Response($data, $status);
}

function scwb_v10103_client_status_shortcode() {
    $data = scwb_v10103_backend_request('/v10103/status');
    if (empty($data['ok'])) {
        return '<div class="scwb-v10103-status">Standalone client adapter unavailable.</div>';
    }
    return sprintf(
        '<div class="scwb-v10103-status"><strong>Workbench v%s</strong> · Standalone client adapter ready · WordPress optional</div>',
        esc_html($data['version'] ?? '10.10.3')
    );
}
add_shortcode('sc_workbench_standalone_client_status', 'scwb_v10103_client_status_shortcode');

add_action('rest_api_init', function () {
    $permission = function () { return current_user_can('edit_posts'); };

    $get_routes = array(
        '/status' => '/v10103/status',
        '/config' => '/standalone/v1/client/config',
        '/adapter' => '/standalone/v1/client/adapter',
        '/capabilities' => '/standalone/v1/client/capabilities',
    );

    foreach ($get_routes as $wp_path => $backend_path) {
        register_rest_route('sc-workbench/v1/v10103', $wp_path, array(
            'methods' => 'GET',
            'permission_callback' => $permission,
            'callback' => function () use ($backend_path) {
                return scwb_v10103_proxy_response($backend_path);
            },
        ));
    }

    register_rest_route('sc-workbench/v1/v10103', '/plan', array(
        'methods' => 'POST',
        'permission_callback' => $permission,
        'callback' => function ($request) {
            return scwb_v10103_proxy_response(
                '/standalone/v1/client/plan',
                'POST',
                $request->get_json_params()
            );
        },
    ));

    register_rest_route('sc-workbench/v1/v10103', '/compute', array(
        'methods' => 'POST',
        'permission_callback' => $permission,
        'callback' => function ($request) {
            return scwb_v10103_proxy_response(
                '/standalone/v1/client/compute',
                'POST',
                $request->get_json_params()
            );
        },
    ));
});
