<?php
/**
 * Workbench v11.0.0 — Unified Calculation Engine & Calculation Object Foundation.
 *
 * WordPress remains an optional presentation/proxy adapter.
 * Standalone backend contract: wordpressRequired = false.
 * Authoritative computation remains in FastAPI.
 */
if (!defined('ABSPATH')) { exit; }

function scwb_v1100_backend_request($path, $method='GET', $body=null) {
    if (function_exists('scwb_v10110_backend_request')) {
        return scwb_v10110_backend_request($path, $method, $body);
    }
    if (function_exists('scwb_v10103_backend_request')) {
        return scwb_v10103_backend_request($path, $method, $body);
    }
    return array('ok'=>false,'error'=>'Workbench backend adapter unavailable','_httpStatus'=>503);
}

function scwb_v1100_proxy_response($path, $method='GET', $body=null) {
    $data = scwb_v1100_backend_request($path, $method, $body);
    $status = intval($data['_httpStatus'] ?? 200);
    unset($data['_httpStatus']);
    return new WP_REST_Response($data, $status);
}

function scwb_v1100_status_shortcode() {
    $data = scwb_v1100_backend_request('/v1100/status');
    if (empty($data['ok'])) {
        return '<div class="scwb-v1100-status">Unified Calculation Engine unavailable.</div>';
    }
    return sprintf(
        '<div class="scwb-v1100-status"><strong>Workbench v%s</strong> · Unified Calculation Engine ready · Calculation Object v1 · WordPress optional</div>',
        esc_html($data['version'] ?? '11.0.0')
    );
}
add_shortcode('sc_workbench_unified_calculation_status', 'scwb_v1100_status_shortcode');

add_action('rest_api_init', function () {
    $permission = function () { return current_user_can('edit_posts'); };

    register_rest_route('sc-workbench/v1/v1100', '/status', array(
        'methods' => 'GET',
        'permission_callback' => $permission,
        'callback' => function () {
            return scwb_v1100_proxy_response('/v1100/status');
        },
    ));

    register_rest_route('sc-workbench/v1/v1100', '/schema', array(
        'methods' => 'GET',
        'permission_callback' => $permission,
        'callback' => function () {
            return scwb_v1100_proxy_response('/calculation-engine/v1/schema');
        },
    ));

    foreach (array('normalize', 'plan', 'compute') as $action) {
        register_rest_route('sc-workbench/v1/v1100', '/' . $action, array(
            'methods' => 'POST',
            'permission_callback' => $permission,
            'callback' => function ($request) use ($action) {
                return scwb_v1100_proxy_response(
                    '/calculation-engine/v1/' . $action,
                    'POST',
                    $request->get_json_params()
                );
            },
        ));
    }
});
