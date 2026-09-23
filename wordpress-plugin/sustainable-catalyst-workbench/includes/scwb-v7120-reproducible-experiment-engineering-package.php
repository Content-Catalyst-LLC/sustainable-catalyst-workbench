<?php
if (!defined('ABSPATH')) { exit; }
function scwb_v7120_backend_url($path) {
    $base = defined('SCWB_BACKEND_URL') ? SCWB_BACKEND_URL : 'https://workbench-api.sustainablecatalyst.com';
    return rtrim($base, '/') . $path;
}
function scwb_v7120_status_payload() {
    $response = wp_remote_get(scwb_v7120_backend_url('/v7120/status'), array('timeout' => 8));
    if (is_wp_error($response)) { return array('ok'=>false,'error'=>$response->get_error_message()); }
    $body = json_decode(wp_remote_retrieve_body($response), true);
    return is_array($body) ? $body : array('ok'=>false,'error'=>'Invalid Workbench response');
}
add_shortcode('sc_workbench_reproducible_package_status', function () {
    $data = scwb_v7120_status_payload(); $ok = !empty($data['ok']);
    return '<div class="scwb-runtime-status"><strong>Reproducible Experiment &amp; Engineering Package:</strong> ' . esc_html($ok ? 'Online' : 'Unavailable') . '</div>';
});
add_action('rest_api_init', function () {
    register_rest_route('sc-workbench/v1', '/reproducible-package/status', array(
        'methods' => 'GET', 'callback' => function () { return rest_ensure_response(scwb_v7120_status_payload()); }, 'permission_callback' => '__return_true',
    ));
});
