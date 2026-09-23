<?php
/** Workbench v8.3.0 — Research Asset & Artifact Registry status bridge. */
if (!defined('ABSPATH')) { exit; }

function scwb_v830_backend_base() {
    $base = get_option('scwb_backend_url', 'https://workbench-api.sustainablecatalyst.com');
    return rtrim((string)$base, '/');
}

function scwb_v830_get_json($path) {
    $url = scwb_v830_backend_base() . $path;
    $response = wp_remote_get($url, array('timeout' => 8));
    if (is_wp_error($response)) { return array('ok'=>false,'error'=>$response->get_error_message()); }
    $body = json_decode(wp_remote_retrieve_body($response), true);
    return is_array($body) ? $body : array('ok'=>false,'error'=>'Invalid backend response');
}

function scwb_v830_status_shortcode() {
    $status = scwb_v830_get_json('/v830/status');
    $manifest = scwb_v830_get_json('/research-assets/manifest');
    $ok = !empty($status['ok']) && !empty($manifest['ok']);
    $version = isset($status['version']) ? esc_html($status['version']) : 'unknown';
    $state = $ok ? 'Online' : 'Unavailable';
    return '<div class="scwb-v830-status"><strong>Research Asset Registry ' . esc_html($state) . '</strong><br><span>Workbench ' . $version . '</span></div>';
}
add_shortcode('sc_workbench_research_asset_registry_status', 'scwb_v830_status_shortcode');

add_action('rest_api_init', function () {
    register_rest_route('sc-workbench/v1', '/research-asset-registry/status', array(
        'methods' => 'GET',
        'permission_callback' => '__return_true',
        'callback' => function () { return rest_ensure_response(scwb_v830_get_json('/v830/status')); },
    ));
});
