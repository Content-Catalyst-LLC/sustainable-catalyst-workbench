<?php
/** Workbench v4.0.1 — Connected Environment Activation and Integration Reliability. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V401_Connected_Reliability {
    const VERSION = '4.0.1';
    const EXPECTED_STUDIOS = 22;

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 45);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
        add_action('admin_notices', array(__CLASS__, 'admin_notice'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V401_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v401.css';
        $js = $base . '/assets/js/sc-workbench-v401.js';
        wp_register_style('scwb-v401', plugins_url('assets/css/sc-workbench-v401.css', SCWB_V401_PLUGIN_FILE), array('scwb-v400'), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v401', plugins_url('assets/js/sc-workbench-v401.js', SCWB_V401_PLUGIN_FILE), array('scwb-v400'), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_connected_reliability' => 'overview',
            'sc_workbench_activation_audit' => 'activation',
            'sc_workbench_schema_compatibility' => 'schemas',
            'sc_workbench_project_propagation' => 'projects',
            'sc_workbench_handoff_roundtrip' => 'handoffs',
            'sc_workbench_asset_cache_audit' => 'assets',
            'sc_workbench_fallback_recovery' => 'fallback',
            'sc_workbench_integration_fixture' => 'fixture',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, function($atts) use ($panel) {
                    $atts = shortcode_atts(array('project' => 'default', 'display' => 'full', 'title' => 'Connected Environment Reliability'), $atts);
                    return SCWB_V401_Connected_Reliability::render($atts, $panel);
                });
            }
        }
    }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/connected-reliability-status', array('methods' => 'GET', 'callback' => array(__CLASS__, 'status'), 'permission_callback' => '__return_true'));
        register_rest_route('scwb/v1', '/connected-reliability-audit', array('methods' => 'GET', 'callback' => array(__CLASS__, 'activation_audit'), 'permission_callback' => '__return_true'));
        register_rest_route('scwb/v1', '/connected-schema-compatibility', array('methods' => 'GET', 'callback' => array(__CLASS__, 'schema_compatibility'), 'permission_callback' => '__return_true'));
        register_rest_route('scwb/v1', '/connected-repair-plan', array('methods' => 'GET', 'callback' => array(__CLASS__, 'repair_plan'), 'permission_callback' => '__return_true'));
    }

    public static function availability() {
        return class_exists('SCWB_V301_Production_Reliability') ? SCWB_V301_Production_Reliability::availability() : array();
    }

    public static function audit_data() {
        $availability = self::availability();
        $missing = array_values(array_filter($availability, static function($item) { return empty($item['available']); }));
        $registered = count($availability) - count($missing);
        return array(
            'schema' => 'sc-workbench-connected-reliability-audit/1.0',
            'version' => self::VERSION,
            'primaryShortcodeRegistered' => shortcode_exists('sc_workbench'),
            'expectedStudioCount' => self::EXPECTED_STUDIOS,
            'observedStudioCount' => count($availability),
            'registeredStudioCount' => $registered,
            'missingStudios' => $missing,
            'ready' => shortcode_exists('sc_workbench') && empty($missing) && count($availability) >= self::EXPECTED_STUDIOS,
            'automaticRepairAuthorized' => false,
        );
    }

    public static function status() {
        $audit = self::audit_data();
        return rest_ensure_response(array(
            'ok' => $audit['ready'],
            'schema' => 'sc-workbench-connected-reliability-status/1.0',
            'version' => self::VERSION,
            'milestone' => 'Connected Environment Activation and Integration Reliability',
            'expectedStudioCount' => self::EXPECTED_STUDIOS,
            'registeredStudioCount' => $audit['registeredStudioCount'],
            'offlineSupported' => true,
            'browserLocalFallback' => true,
            'renderRequired' => false,
            'automaticRepairAuthorized' => false,
            'automaticPublicationAuthorized' => false,
        ));
    }

    public static function activation_audit() {
        return rest_ensure_response(array('ok' => self::audit_data()['ready'], 'audit' => self::audit_data()));
    }

    public static function schema_compatibility() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-connected-reliability-schema-compatibility/1.0',
            'version' => self::VERSION,
            'supported' => array(
                'sc-workbench-connected-environment-project/1.0',
                'sc-workbench-persistent-project/1.0',
                'sc-workbench-platform-handoff/1.0',
                'sc-workbench-domain-laboratory-contract/1.0',
                'sc-workbench-offline-sync-bundle/1.0',
            ),
            'migrationPreviewRequired' => true,
            'destructiveMigrationAuthorized' => false,
        ));
    }

    public static function repair_plan() {
        $audit = self::audit_data();
        $actions = array();
        if (!$audit['primaryShortcodeRegistered']) { $actions[] = 're-register-shortcodes'; }
        if (!empty($audit['missingStudios'])) { $actions[] = 'rebuild-studio-registry'; }
        if (!$actions) { $actions[] = 're-run-integration-probe'; }
        return rest_ensure_response(array(
            'ok' => $audit['ready'],
            'schema' => 'sc-workbench-connected-reliability-repair-plan/1.0',
            'version' => self::VERSION,
            'actions' => $actions,
            'automaticExecutionAuthorized' => false,
            'automaticDeletionAuthorized' => false,
        ));
    }

    public static function admin_notice() {
        if (!current_user_can('manage_options')) { return; }
        $audit = self::audit_data();
        if ($audit['ready']) { return; }
        echo '<div class="notice notice-warning"><p><strong>Workbench v4.0.1 connected reliability:</strong> The connected environment requires review. Use <code>[sc_workbench_connected_reliability]</code> to inspect activation, schema, handoff, asset, and fallback checks. No automatic repair is performed.</p></div>';
    }

    private static function card($title, $text, $action, $button) {
        ?>
        <article class="scwb-v401__card">
            <h4><?php echo esc_html($title); ?></h4>
            <p><?php echo esc_html($text); ?></p>
            <button type="button" data-scwb-v401-action="<?php echo esc_attr($action); ?>"><?php echo esc_html($button); ?></button>
        </article>
        <?php
    }

    public static function render($atts, $panel = 'overview') {
        self::register_assets();
        wp_enqueue_style('scwb-v400');
        wp_enqueue_style('scwb-v401');
        wp_enqueue_script('scwb-v400');
        wp_enqueue_script('scwb-v401');
        wp_localize_script('scwb-v401', 'SCWBV401Config', array(
            'version' => self::VERSION,
            'restUrl' => esc_url_raw(rest_url('scwb/v1')),
            'backendUrl' => '',
            'nonce' => wp_create_nonce('wp_rest'),
            'expectedStudios' => self::EXPECTED_STUDIOS,
        ));
        $project = sanitize_key($atts['project']) ?: 'default';
        $display = sanitize_key($atts['display']) ?: 'full';
        $audit = self::audit_data();
        ob_start();
        ?>
        <section class="scwb-v401 scwb-v401--<?php echo esc_attr($display); ?>" data-scwb-v401 data-panel="<?php echo esc_attr($panel); ?>" data-project="<?php echo esc_attr($project); ?>" data-version="4.0.1">
            <header class="scwb-v401__header">
                <div><p class="scwb-v401__eyebrow">Workbench v4.0.1 reliability patch</p><h3><?php echo esc_html($atts['title']); ?></h3><p>Validate the live connected environment without changing project data or authorizing destructive repair.</p></div>
                <span class="scwb-v401__status <?php echo $audit['ready'] ? 'is-ready' : 'is-review'; ?>" data-scwb-v401-status><?php echo esc_html($audit['registeredStudioCount'] . '/' . max($audit['observedStudioCount'], self::EXPECTED_STUDIOS) . ' studios registered'); ?></span>
            </header>
            <div class="scwb-v401__summary">
                <div><strong>Primary shortcode</strong><span><?php echo $audit['primaryShortcodeRegistered'] ? 'Registered' : 'Missing'; ?></span></div>
                <div><strong>Connected project</strong><span><?php echo esc_html($project); ?></span></div>
                <div><strong>Fallback</strong><span>Browser-local and offline</span></div>
                <div><strong>Repair policy</strong><span>Human-controlled</span></div>
            </div>
            <div class="scwb-v401__grid">
                <?php self::card('Activation audit', 'Check the canonical shortcode, all 22 studios, rendered panels, and literal shortcode leakage.', 'activation', 'Run activation audit'); ?>
                <?php self::card('Schema compatibility', 'Check connected projects, persistent records, handoffs, Lab contracts, and offline bundles before migration.', 'schemas', 'Inspect schemas'); ?>
                <?php self::card('Project propagation', 'Verify that one active project identifier reaches every mounted studio.', 'projects', 'Test project routing'); ?>
                <?php self::card('Handoff round trip', 'Validate packet fields, content hashes, target receipts, and return paths.', 'handoffs', 'Validate handoffs'); ?>
                <?php self::card('Asset and cache audit', 'Find stale asset versions, duplicate handles, missing files, and exposed shortcodes.', 'assets', 'Audit assets'); ?>
                <?php self::card('Fallback and recovery', 'Confirm browser-local and offline fallback, backup requirements, and safe repair actions.', 'fallback', 'Build recovery plan'); ?>
            </div>
            <pre class="scwb-v401__output" data-scwb-v401-output aria-live="polite">Select a reliability check. No project records will be changed.</pre>
        </section>
        <?php
        return ob_get_clean();
    }
}

SCWB_V401_Connected_Reliability::boot();
