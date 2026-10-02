<?php
/**
 * Workbench v11.3.0 — Equation & Solver Laboratory.
 *
 * WordPress remains an optional presentation/proxy adapter.
 * Standalone backend contract: wordpressRequired = false.
 * Authoritative computation remains in FastAPI.
 */
if (!defined('ABSPATH')) { exit; }

function scwb_v1130_backend_request($path, $method='GET', $body=null) {
    if (function_exists('scwb_v1100_backend_request')) {
        return scwb_v1100_backend_request($path, $method, $body);
    }
    return array('ok'=>false,'error'=>'Workbench backend adapter unavailable','_httpStatus'=>503);
}

function scwb_v1130_proxy_response($path, $method='GET', $body=null) {
    $data = scwb_v1130_backend_request($path, $method, $body);
    $status = intval($data['_httpStatus'] ?? 200);
    unset($data['_httpStatus']);
    return new WP_REST_Response($data, $status);
}

function scwb_v1130_status_shortcode() {
    $data = scwb_v1130_backend_request('/v1130/status');
    if (empty($data['ok'])) {
        return '<div class="scwb-v1130-status">Equation & Solver Laboratory unavailable.</div>';
    }
    return sprintf(
        '<div class="scwb-v1130-status"><strong>Workbench v%s</strong> · Equation & Solver Laboratory ready · WordPress optional</div>',
        esc_html($data['version'] ?? '11.3.0')
    );
}
add_shortcode('sc_workbench_solver_status', 'scwb_v1130_status_shortcode');

add_action('rest_api_init', function () {
    $permission = function () { return current_user_can('edit_posts'); };

    register_rest_route('sc-workbench/v1/v1130', '/status', array(
        'methods' => 'GET',
        'permission_callback' => $permission,
        'callback' => function () {
            return scwb_v1130_proxy_response('/v1130/status');
        },
    ));

    register_rest_route('sc-workbench/v1/v1130', '/solver', array(
        'methods' => 'POST',
        'permission_callback' => $permission,
        'callback' => function ($request) {
            return scwb_v1130_proxy_response(
                '/calculation-engine/v1/solver',
                'POST',
                $request->get_json_params()
            );
        },
    ));

    register_rest_route('sc-workbench/v1/v1130', '/calculation-object', array(
        'methods' => 'POST',
        'permission_callback' => $permission,
        'callback' => function ($request) {
            return scwb_v1130_proxy_response(
                '/calculation-engine/v1/solver/calculation-object',
                'POST',
                $request->get_json_params()
            );
        },
    ));
});
