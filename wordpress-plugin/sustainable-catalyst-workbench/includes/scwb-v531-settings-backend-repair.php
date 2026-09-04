<?php
/**
 * Workbench v5.3.1 — Settings & Backend Connection Repair.
 */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V531_Settings_Backend_Repair {
    const VERSION = '5.3.1';
    const OPTION_BACKEND_URL = 'scwb_workbench_backend_url';
    const MENU_SLUG = 'scwb-workbench';
    const CANONICAL_BACKEND = 'https://workbench-api.sustainablecatalyst.com';

    public static function boot() {
        add_action('admin_menu', array(__CLASS__, 'register_admin_menu'));
        add_action('admin_init', array(__CLASS__, 'register_settings'));
        add_action('admin_enqueue_scripts', array(__CLASS__, 'enqueue_admin_assets'));
        add_action('wp_ajax_scwb_v531_test_backend', array(__CLASS__, 'ajax_test_backend'));
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
        if (function_exists('plugin_basename')) {
            add_filter('plugin_action_links_' . plugin_basename(SCWB_V531_PLUGIN_FILE), array(__CLASS__, 'plugin_action_links'));
        }
    }

    public static function register_settings() {
        register_setting('scwb_v531_settings', self::OPTION_BACKEND_URL, array(
            'type' => 'string',
            'sanitize_callback' => array(__CLASS__, 'sanitize_backend_url'),
            'default' => '',
        ));
    }

    public static function sanitize_backend_url($value) {
        $value = trim((string) $value);
        if ('' === $value) { return ''; }
        $value = function_exists('esc_url_raw') ? esc_url_raw($value, array('https', 'http')) : filter_var($value, FILTER_SANITIZE_URL);
        if (!$value) { return ''; }
        return rtrim($value, '/');
    }

    public static function saved_backend_url() {
        if (!function_exists('get_option')) { return ''; }
        return self::sanitize_backend_url(get_option(self::OPTION_BACKEND_URL, ''));
    }

    public static function backend_url($override = '') {
        $candidate = self::sanitize_backend_url($override);
        if (!$candidate && defined('SCWB_WORKBENCH_BACKEND_URL')) {
            $candidate = self::sanitize_backend_url((string) SCWB_WORKBENCH_BACKEND_URL);
        }
        if (!$candidate) {
            $candidate = self::saved_backend_url();
        }
        if (function_exists('apply_filters')) {
            $candidate = self::sanitize_backend_url((string) apply_filters('scwb_workbench_backend_url', $candidate));
        }
        return rtrim($candidate, '/');
    }

    public static function configuration_source() {
        if (defined('SCWB_WORKBENCH_BACKEND_URL') && trim((string) SCWB_WORKBENCH_BACKEND_URL)) {
            return 'wp-config.php';
        }
        if (self::saved_backend_url()) { return 'Workbench settings'; }
        return 'Not configured';
    }

    public static function register_admin_menu() {
        add_menu_page(
            'Sustainable Catalyst Workbench',
            'Workbench',
            'manage_options',
            self::MENU_SLUG,
            array(__CLASS__, 'render_settings_page'),
            'dashicons-calculator',
            58
        );
        add_submenu_page(
            self::MENU_SLUG,
            'Workbench Settings',
            'Settings',
            'manage_options',
            self::MENU_SLUG,
            array(__CLASS__, 'render_settings_page')
        );
    }

    public static function enqueue_admin_assets($hook = '') {
        if (false === strpos((string) $hook, self::MENU_SLUG)) { return; }
        $base = dirname(SCWB_V531_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v531-admin.css';
        $js = $base . '/assets/js/sc-workbench-v531-admin.js';
        wp_enqueue_style(
            'scwb-v531-admin',
            plugins_url('assets/css/sc-workbench-v531-admin.css', SCWB_V531_PLUGIN_FILE),
            array(),
            file_exists($css) ? (string) filemtime($css) : self::VERSION
        );
        wp_enqueue_script(
            'scwb-v531-admin',
            plugins_url('assets/js/sc-workbench-v531-admin.js', SCWB_V531_PLUGIN_FILE),
            array(),
            file_exists($js) ? (string) filemtime($js) : self::VERSION,
            true
        );
        wp_localize_script('scwb-v531-admin', 'SCWBV531Admin', array(
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('scwb_v531_test_backend'),
            'canonicalBackend' => self::CANONICAL_BACKEND,
            'version' => self::VERSION,
        ));
    }

    public static function plugin_action_links($links) {
        $url = admin_url('admin.php?page=' . self::MENU_SLUG);
        array_unshift($links, '<a href="' . esc_url($url) . '">Settings</a>');
        return $links;
    }

    private static function endpoint_probe($base, $path) {
        $request_fn = function_exists('wp_safe_remote_get') ? 'wp_safe_remote_get' : 'wp_remote_get';
        $response = call_user_func($request_fn, rtrim($base, '/') . $path, array(
            'timeout' => 8,
            'redirection' => 2,
            'sslverify' => true,
            'headers' => array('Accept' => 'application/json'),
        ));
        if (is_wp_error($response)) {
            return array('ok' => false, 'error' => $response->get_error_message());
        }
        $code = (int) wp_remote_retrieve_response_code($response);
        $body = json_decode((string) wp_remote_retrieve_body($response), true);
        if ($code < 200 || $code >= 300 || !is_array($body)) {
            return array('ok' => false, 'http' => $code, 'error' => 'Unexpected backend response.');
        }
        return array(
            'ok' => !empty($body['ok']),
            'http' => $code,
            'version' => isset($body['version']) ? sanitize_text_field((string) $body['version']) : '',
            'engine' => isset($body['engine']) ? sanitize_text_field((string) $body['engine']) : '',
            'schema' => isset($body['schema']) ? sanitize_text_field((string) $body['schema']) : '',
        );
    }

    public static function ajax_test_backend() {
        check_ajax_referer('scwb_v531_test_backend', 'nonce');
        if (!current_user_can('manage_options')) {
            wp_send_json_error(array('message' => 'Insufficient permissions.'), 403);
        }
        $posted = isset($_POST['backendUrl']) ? wp_unslash($_POST['backendUrl']) : '';
        $base = self::sanitize_backend_url($posted);
        if (!$base) { $base = self::backend_url(); }
        if (!$base) {
            wp_send_json_error(array('message' => 'Enter a backend URL before testing.'), 400);
        }
        $checks = array(
            'cas' => self::endpoint_probe($base, '/v510/status'),
            'graph' => self::endpoint_probe($base, '/v520/status'),
            'creative' => self::endpoint_probe($base, '/v530/status'),
            'advancedGraph' => self::endpoint_probe($base, '/v540/status'),
            'dynamicGeometry' => self::endpoint_probe($base, '/v550/status'),
        );
        $all_ok = true;
        foreach ($checks as $check) { if (empty($check['ok'])) { $all_ok = false; break; } }
        $payload = array(
            'ok' => $all_ok,
            'backendUrl' => $base,
            'source' => self::configuration_source(),
            'checks' => $checks,
            'message' => $all_ok ? 'Workbench backend connected.' : 'Backend reached, but one or more capability checks failed.',
        );
        if ($all_ok) { wp_send_json_success($payload); }
        wp_send_json_error($payload, 502);
    }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/v531-settings-status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'status'),
            'permission_callback' => '__return_true',
        ));
    }

    public static function status() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-settings-status/1.0',
            'version' => self::VERSION,
            'backendConfigured' => '' !== self::backend_url(),
            'configurationSource' => self::configuration_source(),
            'adminConnectionTest' => true,
            'wpConfigOverrideSupported' => true,
        ));
    }

    public static function render_settings_page() {
        if (!current_user_can('manage_options')) { return; }
        $constant_locked = defined('SCWB_WORKBENCH_BACKEND_URL') && trim((string) SCWB_WORKBENCH_BACKEND_URL);
        $saved = self::saved_backend_url();
        $effective = self::backend_url();
        $field_value = $constant_locked ? self::sanitize_backend_url((string) SCWB_WORKBENCH_BACKEND_URL) : ($saved ?: self::CANONICAL_BACKEND);
        ?>
        <div class="wrap scwb-v531-admin">
            <div class="scwb-v531-admin__hero">
                <div>
                    <p>SUSTAINABLE CATALYST WORKBENCH</p>
                    <h1>Settings</h1>
                    <span>Backend connection, execution boundaries, and runtime status in one place.</span>
                </div>
                <div class="scwb-v531-admin__version">PLUGIN v<?php echo esc_html(defined('SCWB_VERSION') ? SCWB_VERSION : self::VERSION); ?></div>
            </div>

            <?php settings_errors(); ?>

            <section class="scwb-v531-admin__card scwb-v531-admin__connection">
                <div class="scwb-v531-admin__card-head">
                    <div><p>WORKBENCH CONNECTION</p><h2>Backend</h2></div>
                    <span class="scwb-v531-admin__source">Source: <?php echo esc_html(self::configuration_source()); ?></span>
                </div>
                <form method="post" action="options.php" data-scwb-v531-settings-form>
                    <?php settings_fields('scwb_v531_settings'); ?>
                    <label class="scwb-v531-admin__field">
                        <span>Backend URL</span>
                        <input type="url" name="<?php echo esc_attr(self::OPTION_BACKEND_URL); ?>" value="<?php echo esc_attr($field_value); ?>" placeholder="<?php echo esc_attr(self::CANONICAL_BACKEND); ?>" <?php echo $constant_locked ? 'readonly' : ''; ?> data-scwb-v531-backend-url>
                    </label>
                    <?php if ($constant_locked) : ?>
                        <p class="description">This value is locked by <code>SCWB_WORKBENCH_BACKEND_URL</code> in <code>wp-config.php</code>. Remove that constant to manage the URL here.</p>
                    <?php else : ?>
                        <p class="description">Canonical production backend: <code><?php echo esc_html(self::CANONICAL_BACKEND); ?></code></p>
                    <?php endif; ?>
                    <div class="scwb-v531-admin__actions">
                        <?php if (!$constant_locked) : submit_button('Save connection', 'primary', 'submit', false); endif; ?>
                        <button type="button" class="button button-secondary" data-scwb-v531-test>Test connection</button>
                        <?php if (!$constant_locked) : ?><button type="button" class="button" data-scwb-v531-use-canonical>Use canonical backend</button><?php endif; ?>
                    </div>
                </form>
                <div class="scwb-v531-admin__test" data-scwb-v531-test-result aria-live="polite">
                    <div class="scwb-v531-admin__test-title"><i></i><strong><?php echo $effective ? 'Ready to test' : 'Not configured'; ?></strong><span><?php echo esc_html($effective ?: 'Enter the Workbench backend URL.'); ?></span></div>
                    <div class="scwb-v531-admin__checks">
                        <div><span>CAS</span><b data-scwb-v531-check="cas">—</b></div>
                        <div><span>GRAPH</span><b data-scwb-v531-check="graph">—</b></div>
                        <div><span>BLACKBOARD + CREATIVE</span><b data-scwb-v531-check="creative">—</b></div>
                        <div><span>ADVANCED GRAPH</span><b data-scwb-v531-check="advancedGraph">—</b></div>
                        <div><span>DYNAMIC GEOMETRY</span><b data-scwb-v531-check="dynamicGeometry">—</b></div>
                    </div>
                </div>
            </section>

            <section class="scwb-v531-admin__card">
                <div class="scwb-v531-admin__card-head"><div><p>EXECUTION</p><h2>Boundaries</h2></div></div>
                <div class="scwb-v531-admin__boundary-grid">
                    <div><span>Browser interaction</span><b class="is-ready">Enabled</b><small>Graphing, controls, visualization, local interface state</small></div>
                    <div><span>Server computation</span><b class="is-ready">Configured by backend</b><small>CAS, advanced graph analysis, dynamic geometry, Blackboard, creative mathematics</small></div>
                    <div><span>Workbench Runner</span><b>Separate pairing</b><small>Approved local runtimes and engineering tools only</small></div>
                    <div><span>Physical device programming</span><b class="is-guarded">Manual approval</b><small>Public Prototype Bench remains export-only</small></div>
                </div>
            </section>

            <details class="scwb-v531-admin__advanced">
                <summary>Advanced configuration</summary>
                <div>
                    <p><strong>wp-config.php override</strong></p>
                    <code>define('SCWB_WORKBENCH_BACKEND_URL', '<?php echo esc_html(self::CANONICAL_BACKEND); ?>');</code>
                    <p>The constant takes priority over the saved setting. The <code>scwb_workbench_backend_url</code> filter remains available for managed deployments.</p>
                </div>
            </details>
        </div>
        <?php
    }
}
SCWB_V531_Settings_Backend_Repair::boot();
