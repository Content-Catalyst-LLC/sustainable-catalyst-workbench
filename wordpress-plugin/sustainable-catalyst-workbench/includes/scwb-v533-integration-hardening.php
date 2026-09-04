<?php
/**
 * Workbench v5.3.3 — Homepage & Workbench Experience Integration Hardening.
 */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V533_Integration_Hardening {
    const VERSION = '5.3.3';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 7);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 100);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V533_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v533.css';
        wp_register_style(
            'scwb-v533',
            plugins_url('assets/css/sc-workbench-v533.css', SCWB_V533_PLUGIN_FILE),
            array('scwb-v532'),
            file_exists($css) ? (string) filemtime($css) : self::VERSION
        );
    }

    private static function enqueue_assets() {
        if (class_exists('SCWB_V530_Blackboard_Creative_Prototyping')) {
            SCWB_V530_Blackboard_Creative_Prototyping::register_assets();
        }
        if (class_exists('SCWB_V532_Compact_Showcase_Experience')) {
            SCWB_V532_Compact_Showcase_Experience::register_assets();
        }
        self::register_assets();

        wp_enqueue_style('scwb-v530');
        wp_enqueue_script('scwb-v530');
        wp_enqueue_style('scwb-v532');
        wp_enqueue_script('scwb-v532');
        wp_enqueue_style('scwb-v533');

        $backend = class_exists('SCWB_V531_Settings_Backend_Repair')
            ? SCWB_V531_Settings_Backend_Repair::backend_url()
            : '';

        // The v5.3.2 renderer is retained, but the active interface identity is v5.3.3.
        // Relocalizing here ensures the browser status rail follows the plugin release.
        wp_localize_script('scwb-v532', 'SCWBV532Config', array(
            'version' => self::VERSION,
            'backendUrl' => $backend,
            'workbenchUrl' => home_url('/workbench/'),
            'viewportScrollGuard' => true,
        ));
    }

    public static function register_shortcodes() {
        // v5.3.3 is authoritative for the homepage and public Workbench experience.
        if (shortcode_exists('sc_workbench_homepage_instrument')) {
            remove_shortcode('sc_workbench_homepage_instrument');
        }
        add_shortcode('sc_workbench_homepage_instrument', array(__CLASS__, 'render_homepage'));

        if (shortcode_exists('sc_workbench_experience')) {
            remove_shortcode('sc_workbench_experience');
        }
        add_shortcode('sc_workbench_experience', array(__CLASS__, 'render_experience'));

        if (shortcode_exists('sc_workbench_experience_page')) {
            remove_shortcode('sc_workbench_experience_page');
        }
        add_shortcode('sc_workbench_experience_page', array(__CLASS__, 'render_experience'));

        // Guard an older homepage implementation from accidentally restoring the tall v5.3.0
        // showcase. It remains available away from the front page for compatibility.
        if (shortcode_exists('sc_workbench_v530_showcase')) {
            remove_shortcode('sc_workbench_v530_showcase');
        }
        add_shortcode('sc_workbench_v530_showcase', array(__CLASS__, 'render_legacy_showcase_guard'));
    }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/v533-interface-status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'status'),
            'permission_callback' => '__return_true',
        ));
    }

    public static function status() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-v533-interface-status/1.0',
            'version' => self::VERSION,
            'homepageShowcase' => 'compact-rotating',
            'viewportScrollGuard' => true,
            'horizontalRailScrollOnly' => true,
            'legacyHomepageShowcaseGuard' => true,
            'workbenchExperience' => true,
            'backendVersionRequired' => '5.3.0',
            'backendRedeployRequired' => false,
        ));
    }

    private static function promote_markup($html, $surface_class) {
        $html = str_replace('data-version="5.3.2"', 'data-version="5.3.3"', $html);
        $html = str_replace('v5.3.2 ·', 'v5.3.3 ·', $html);
        $html = str_replace('SUSTAINABLE CATALYST WORKBENCH · v5.3.2', 'SUSTAINABLE CATALYST WORKBENCH · v5.3.3', $html);
        if ('homepage' === $surface_class) {
            $html = str_replace('class="scwb-v532-home"', 'class="scwb-v532-home scwb-v533-home"', $html);
        } else {
            $html = str_replace('class="scwb-v532-experience"', 'class="scwb-v532-experience scwb-v533-experience"', $html);
        }
        return $html;
    }

    public static function render_homepage($atts = array()) {
        if (!class_exists('SCWB_V532_Compact_Showcase_Experience')) {
            return '<div class="scwb-v533-missing" role="alert"><strong>Workbench homepage showcase is unavailable.</strong><span>Install the complete Workbench v5.3.3 plugin.</span></div>';
        }
        $html = SCWB_V532_Compact_Showcase_Experience::render_homepage($atts);
        self::enqueue_assets();
        return self::promote_markup($html, 'homepage');
    }

    public static function render_experience($atts = array()) {
        if (!class_exists('SCWB_V532_Compact_Showcase_Experience')) {
            return '<div class="scwb-v533-missing" role="alert"><strong>Workbench experience is unavailable.</strong><span>Install the complete Workbench v5.3.3 plugin.</span></div>';
        }
        $html = SCWB_V532_Compact_Showcase_Experience::render_experience($atts);
        self::enqueue_assets();
        return self::promote_markup($html, 'experience');
    }

    public static function render_legacy_showcase_guard($atts = array()) {
        if (function_exists('is_front_page') && is_front_page()) {
            return self::render_homepage($atts);
        }
        if (class_exists('SCWB_V530_Blackboard_Creative_Prototyping')) {
            return SCWB_V530_Blackboard_Creative_Prototyping::render($atts, 'showcase');
        }
        return self::render_homepage($atts);
    }
}
SCWB_V533_Integration_Hardening::boot();
