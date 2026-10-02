<?php
/**
 * Workbench v10.10.1 — WordPress Dependency Inventory & Routing Isolation.
 *
 * WordPress is an optional adapter, never the canonical Workbench runtime.
 * Standalone backend contract: wordpressRequired = false.
 * Authoritative computation remains in FastAPI.
 */
if (!defined('ABSPATH')) { exit; }

function scwb_v10101_backend_request($path, $method='GET', $body=null) {
    if (function_exists('scwb_v10100_backend_request')) {
        return scwb_v10100_backend_request($path, $method, $body);
    }
    $base = defined('SCWB_BACKEND_URL')
        ? rtrim(SCWB_BACKEND_URL, '/')
        : rtrim((string)get_option('scwb_backend_url', 'https://workbench-api.sustainablecatalyst.com'), '/');
    $args = array('method'=>$method, 'timeout'=>30, 'headers'=>array('Accept'=>'application/json','Content-Type'=>'application/json'));
    if ($body !== null) { $args['body'] = wp_json_encode($body); }
    $response = wp_remote_request($base . $path, $args);
    if (is_wp_error($response)) {
        return array('ok'=>false,'error'=>$response->get_error_message(),'_httpStatus'=>502);
    }
    $status = wp_remote_retrieve_response_code($response);
    $data = json_decode(wp_remote_retrieve_body($response), true);
    if (!is_array($data)) { $data = array('ok'=>false,'error'=>'Invalid backend response'); }
    $data['_httpStatus'] = $status;
    return $data;
}

function scwb_v10101_proxy_response($path) {
    $data = scwb_v10101_backend_request($path);
    $status = intval($data['_httpStatus'] ?? 200);
    unset($data['_httpStatus']);
    return new WP_REST_Response($data, $status);
}

function scwb_v10101_decoupling_status_shortcode() {
    $data = scwb_v10101_backend_request('/v10101/status');
    if (empty($data['ok'])) {
        return '<div class="scwb-v10101-status">Workbench decoupling status unavailable.</div>';
    }
    return sprintf(
        '<div class="scwb-v10101-status"><strong>Workbench v%s</strong> · Backend authoritative · WordPress optional · Routing isolation ready</div>',
        esc_html($data['version'] ?? '10.10.1')
    );
}
add_shortcode('sc_workbench_decoupling_status', 'scwb_v10101_decoupling_status_shortcode');

add_action('rest_api_init', function () {
    $permission = function () { return current_user_can('edit_posts'); };
    register_rest_route('sc-workbench/v1/v10101', '/status', array(
        'methods'=>'GET','permission_callback'=>$permission,
        'callback'=>function(){ return scwb_v10101_proxy_response('/v10101/status'); },
    ));
    register_rest_route('sc-workbench/v1/v10101', '/dependencies', array(
        'methods'=>'GET','permission_callback'=>$permission,
        'callback'=>function(){ return scwb_v10101_proxy_response('/decoupling/dependencies'); },
    ));
    register_rest_route('sc-workbench/v1/v10101', '/routes', array(
        'methods'=>'GET','permission_callback'=>$permission,
        'callback'=>function(){ return scwb_v10101_proxy_response('/decoupling/routes'); },
    ));
    register_rest_route('sc-workbench/v1/v10101', '/adapter', array(
        'methods'=>'GET','permission_callback'=>$permission,
        'callback'=>function(){ return scwb_v10101_proxy_response('/decoupling/adapters/wordpress'); },
    ));
});
