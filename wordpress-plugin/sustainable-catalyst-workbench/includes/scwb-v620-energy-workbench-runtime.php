<?php
/**
 * Workbench v6.2.0 — Energy Workbench Runtime bridge.
 *
 * Exposes read-only WordPress REST status for the explicit-input Energy Systems
 * execution runtime. Calculation execution stays on the Workbench backend.
 */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V620_Energy_Workbench_Runtime {
    const VERSION = '6.2.0';
    const ENERGY_SYSTEMS_VERSION = '1.3.0';

    public static function boot() {
        add_action('rest_api_init', array(__CLASS__, 'register_routes'));
        add_shortcode('sc_workbench_energy_runtime_status', array(__CLASS__, 'shortcode'));
    }

    public static function register_routes() {
        register_rest_route('sc-workbench/v1', '/energy-runtime/status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'status'),
            'permission_callback' => '__return_true',
        ));
    }

    private static function backend_url() {
        if (class_exists('SCWB_V531_Settings_Backend_Repair')) {
            return rtrim((string) SCWB_V531_Settings_Backend_Repair::backend_url(), '/');
        }
        if (defined('SCWB_WORKBENCH_BACKEND_URL')) {
            return rtrim((string) SCWB_WORKBENCH_BACKEND_URL, '/');
        }
        return 'https://workbench-api.sustainablecatalyst.com';
    }

    public static function status() {
        $url = self::backend_url() . '/v1/energy-runtime/execution-framework';
        $response = wp_remote_get($url, array('timeout' => 8, 'redirection' => 2));
        if (is_wp_error($response)) {
            return new WP_REST_Response(array(
                'ok' => false,
                'version' => self::VERSION,
                'energySystemsVersion' => self::ENERGY_SYSTEMS_VERSION,
                'backend' => 'unavailable',
                'detail' => $response->get_error_message(),
            ), 502);
        }
        $code = (int) wp_remote_retrieve_response_code($response);
        $body = json_decode((string) wp_remote_retrieve_body($response), true);
        if ($code < 200 || $code >= 300 || !is_array($body)) {
            return new WP_REST_Response(array(
                'ok' => false,
                'version' => self::VERSION,
                'energySystemsVersion' => self::ENERGY_SYSTEMS_VERSION,
                'backend' => 'invalid-response',
                'httpStatus' => $code,
            ), 502);
        }
        return new WP_REST_Response(array(
            'ok' => !empty($body['ok']),
            'version' => self::VERSION,
            'energySystemsVersion' => self::ENERGY_SYSTEMS_VERSION,
            'backend' => 'connected',
            'runtime' => $body,
        ), 200);
    }

    public static function shortcode() {
        return '<div class="scwb-energy-runtime-status" data-workbench-version="' . esc_attr(self::VERSION) . '" data-energy-systems-version="' . esc_attr(self::ENERGY_SYSTEMS_VERSION) . '">Energy Workbench Runtime v' . esc_html(self::VERSION) . ' · Energy Systems v' . esc_html(self::ENERGY_SYSTEMS_VERSION) . '</div>';
    }
}

SCWB_V620_Energy_Workbench_Runtime::boot();
