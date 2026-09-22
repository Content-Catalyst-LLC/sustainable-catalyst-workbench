<?php
/** Workbench v6.4.0 — Platform Core Connectivity Foundation status bridge. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V640_Platform_Core_Connectivity {
    const VERSION = '6.4.0';

    public static function boot() {
        add_action('rest_api_init', array(__CLASS__, 'register_routes'));
        add_shortcode('sc_workbench_core_connectivity_status', array(__CLASS__, 'shortcode'));
    }

    public static function register_routes() {
        register_rest_route('sc-workbench/v1', '/platform-core-connectivity/status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'status'),
            'permission_callback' => '__return_true',
        ));
    }

    private static function backend_url() {
        if (class_exists('SCWB_V531_Settings_Backend_Repair')) {
            $url = SCWB_V531_Settings_Backend_Repair::backend_url();
            if ($url) { return rtrim((string) $url, '/'); }
        }
        if (defined('SCWB_WORKBENCH_BACKEND_URL')) {
            return rtrim((string) SCWB_WORKBENCH_BACKEND_URL, '/');
        }
        return 'https://workbench-api.sustainablecatalyst.com';
    }

    public static function status() {
        $request_fn = function_exists('wp_safe_remote_get') ? 'wp_safe_remote_get' : 'wp_remote_get';
        $response = call_user_func($request_fn, self::backend_url() . '/health', array(
            'timeout' => 8,
            'redirection' => 2,
            'sslverify' => true,
            'headers' => array('Accept' => 'application/json'),
        ));
        if (is_wp_error($response)) {
            return new WP_REST_Response(array(
                'ok' => false,
                'schema' => 'sc-workbench-wordpress-core-connectivity/1.0',
                'version' => self::VERSION,
                'backend' => 'unavailable',
                'detail' => $response->get_error_message(),
            ), 502);
        }
        $code = (int) wp_remote_retrieve_response_code($response);
        $body = json_decode((string) wp_remote_retrieve_body($response), true);
        if ($code < 200 || $code >= 300 || !is_array($body)) {
            return new WP_REST_Response(array(
                'ok' => false,
                'schema' => 'sc-workbench-wordpress-core-connectivity/1.0',
                'version' => self::VERSION,
                'backend' => 'invalid-response',
                'httpStatus' => $code,
            ), 502);
        }
        return new WP_REST_Response(array(
            'ok' => !empty($body['ok']),
            'schema' => 'sc-workbench-wordpress-core-connectivity/1.0',
            'version' => self::VERSION,
            'backend' => 'connected',
            'runtime' => $body,
            'coreGatewayReady' => !empty($body['coreCompatible']),
        ), 200);
    }

    public static function shortcode() {
        return '<div class="scwb-core-connectivity-status" data-workbench-version="' . esc_attr(self::VERSION) . '">Platform Core Connectivity Foundation · Workbench v' . esc_html(self::VERSION) . '</div>';
    }
}

SCWB_V640_Platform_Core_Connectivity::boot();
