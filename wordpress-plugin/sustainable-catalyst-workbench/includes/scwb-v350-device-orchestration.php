<?php
/**
 * Workbench v3.5.0 — Advanced Device and Instrument Orchestration.
 */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V350_Device_Orchestration {
    const VERSION = '3.5.0';
    const DEVICE_POST_TYPE = 'scwb_device';
    const RUN_POST_TYPE = 'scwb_device_run';
    const DEVICE_META = '_scwb_v350_device';
    const RUN_META = '_scwb_v350_run';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_records'), 6);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 30);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = plugin_dir_path(SCWB_V350_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v350.css';
        $js = $base . '/assets/js/sc-workbench-v350.js';
        wp_register_style('scwb-v350', plugins_url('assets/css/sc-workbench-v350.css', SCWB_V350_PLUGIN_FILE), array('scwb-primary-repair'), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v350', plugins_url('assets/js/sc-workbench-v350.js', SCWB_V350_PLUGIN_FILE), array('scwb-primary-repair'), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_records() {
        $common = array('public' => false, 'show_ui' => current_user_can('edit_posts'), 'show_in_rest' => false, 'supports' => array('title', 'author'), 'map_meta_cap' => true, 'capability_type' => 'post');
        register_post_type(self::DEVICE_POST_TYPE, array_merge($common, array('labels' => array('name' => __('Workbench Devices', 'scwb'), 'singular_name' => __('Workbench Device', 'scwb')))));
        register_post_type(self::RUN_POST_TYPE, array_merge($common, array('labels' => array('name' => __('Workbench Device Runs', 'scwb'), 'singular_name' => __('Workbench Device Run', 'scwb')))));
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_device_orchestration' => 'workspace',
            'sc_workbench_device_inventory' => 'inventory',
            'sc_workbench_device_consent' => 'consent',
            'sc_workbench_calibration_scheduler' => 'calibration',
            'sc_workbench_instrument_sessions' => 'sessions',
            'sc_workbench_experiment_runs' => 'runs',
            'sc_workbench_device_logs' => 'recovery',
            'sc_workbench_hardware_simulation' => 'simulation',
        );
        foreach ($map as $shortcode => $panel) {
            add_shortcode($shortcode, function($atts = array()) use ($panel, $shortcode) {
                $atts = shortcode_atts(array('project' => 'default', 'display' => 'full', 'title' => 'Advanced Device and Instrument Orchestration'), $atts, $shortcode);
                return SCWB_V350_Device_Orchestration::render($atts, $panel);
            });
        }
    }

    private static function can_write() { return is_user_logged_in() && current_user_can('edit_posts'); }
    private static function permission() { return self::can_write(); }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/device-orchestration-status', array('methods' => 'GET', 'callback' => array(__CLASS__, 'status'), 'permission_callback' => '__return_true'));
        register_rest_route('scwb/v1', '/devices', array(
            array('methods' => 'GET', 'callback' => array(__CLASS__, 'list_devices'), 'permission_callback' => array(__CLASS__, 'permission')),
            array('methods' => 'POST', 'callback' => array(__CLASS__, 'save_device'), 'permission_callback' => array(__CLASS__, 'permission')),
        ));
        register_rest_route('scwb/v1', '/device-runs', array(
            array('methods' => 'GET', 'callback' => array(__CLASS__, 'list_runs'), 'permission_callback' => array(__CLASS__, 'permission')),
            array('methods' => 'POST', 'callback' => array(__CLASS__, 'save_run'), 'permission_callback' => array(__CLASS__, 'permission')),
        ));
        register_rest_route('scwb/v1', '/device-consent', array('methods' => 'POST', 'callback' => array(__CLASS__, 'echo_private_record'), 'permission_callback' => array(__CLASS__, 'permission')));
        register_rest_route('scwb/v1', '/instrument-sessions', array('methods' => 'POST', 'callback' => array(__CLASS__, 'echo_private_record'), 'permission_callback' => array(__CLASS__, 'permission')));
        register_rest_route('scwb/v1', '/calibration-schedules', array('methods' => 'POST', 'callback' => array(__CLASS__, 'echo_private_record'), 'permission_callback' => array(__CLASS__, 'permission')));
    }

    public static function status() { return rest_ensure_response(array('ok' => true, 'version' => self::VERSION, 'localConsentRequired' => true, 'arbitraryCommandExecution' => false, 'privateStorageAvailable' => self::can_write())); }
    public static function echo_private_record($request) { return rest_ensure_response(array('ok' => true, 'record' => $request->get_json_params())); }

    private static function list_records($type, $meta) {
        $posts = get_posts(array('post_type' => $type, 'post_status' => 'private', 'author' => get_current_user_id(), 'numberposts' => 100, 'orderby' => 'modified', 'order' => 'DESC'));
        $rows = array(); foreach ($posts as $post) { $record = get_post_meta($post->ID, $meta, true); if (is_array($record)) { $record['wordpressId'] = $post->ID; $rows[] = $record; } }
        return $rows;
    }
    public static function list_devices() { return rest_ensure_response(array('ok' => true, 'devices' => self::list_records(self::DEVICE_POST_TYPE, self::DEVICE_META))); }
    public static function list_runs() { return rest_ensure_response(array('ok' => true, 'runs' => self::list_records(self::RUN_POST_TYPE, self::RUN_META))); }

    private static function save_record($request, $type, $meta, $title_key) {
        $record = $request->get_json_params(); if (!is_array($record)) { return new WP_Error('invalid_record', 'A JSON record is required.', array('status' => 400)); }
        $title = sanitize_text_field(isset($record[$title_key]) ? $record[$title_key] : ucfirst(str_replace('_', ' ', $type)));
        $post_id = wp_insert_post(array('post_type' => $type, 'post_status' => 'private', 'post_title' => $title, 'post_author' => get_current_user_id()), true);
        if (is_wp_error($post_id)) { return $post_id; }
        update_post_meta($post_id, $meta, $record);
        return rest_ensure_response(array('ok' => true, 'wordpressId' => $post_id, 'record' => $record));
    }
    public static function save_device($request) { return self::save_record($request, self::DEVICE_POST_TYPE, self::DEVICE_META, 'name'); }
    public static function save_run($request) { return self::save_record($request, self::RUN_POST_TYPE, self::RUN_META, 'title'); }

    private static function field($label, $name, $type = 'text', $value = '', $wide = false) { ?>
        <label class="scwb-v350__field<?php echo $wide ? ' scwb-v350__field--wide' : ''; ?>"><span><?php echo esc_html($label); ?></span>
            <?php if ('textarea' === $type) : ?><textarea data-scwb-v350-field="<?php echo esc_attr($name); ?>"><?php echo esc_textarea($value); ?></textarea>
            <?php else : ?><input type="<?php echo esc_attr($type); ?>" data-scwb-v350-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>"><?php endif; ?>
        </label><?php
    }

    public static function render($atts, $panel = 'workspace') {
        self::register_assets(); wp_enqueue_style('scwb-v350'); wp_enqueue_script('scwb-v350');
        wp_localize_script('scwb-v350', 'SCWBV350Config', array('version' => self::VERSION, 'restUrl' => esc_url_raw(rest_url('scwb/v1')), 'nonce' => wp_create_nonce('wp_rest'), 'authenticated' => self::can_write()));
        $project = sanitize_key($atts['project']) ?: 'default'; $display = sanitize_key($atts['display']) ?: 'full';
        $tabs = array('workspace'=>'Overview','inventory'=>'Inventory','consent'=>'Consent','calibration'=>'Calibration','sessions'=>'Sessions','runs'=>'Runs','recovery'=>'Recovery','simulation'=>'Simulation');
        $instance = 'scwb-v350-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v350 scwb-v350--<?php echo esc_attr($display); ?>" data-scwb-v350 data-scwb-v350-panel="<?php echo esc_attr($panel); ?>" data-scwb-v350-project="<?php echo esc_attr($project); ?>" data-scwb-v350-version="3.5.0">
            <header class="scwb-v350__header"><div><p class="scwb-v350__eyebrow">Sustainable Catalyst Workbench · v3.5.0</p><h2><?php echo esc_html($atts['title']); ?></h2><p>Inventory local devices, discover capabilities, authorize explicit operations, plan calibrated sessions and experiment runs, simulate absent hardware, and preserve recovery-aware logs.</p></div><span class="scwb-v350__status" data-scwb-v350-status><?php echo self::can_write() ? 'Private device storage available' : 'Browser-local device mode'; ?></span></header>
            <nav class="scwb-v350__tabs" role="tablist" aria-label="Device orchestration tools"><?php foreach($tabs as $key=>$label): ?><button type="button" role="tab" data-scwb-v350-tab="<?php echo esc_attr($key); ?>" class="<?php echo $key===$panel?'is-active':''; ?>" aria-selected="<?php echo $key===$panel?'true':'false'; ?>"><?php echo esc_html($label); ?></button><?php endforeach; ?></nav>
            <div class="scwb-v350__views">
                <section data-scwb-v350-view="workspace" class="scwb-v350__view<?php echo 'workspace'===$panel?' is-active':''; ?>" <?php echo 'workspace'===$panel?'':'hidden'; ?>><h3>Orchestration overview</h3><p>Build an auditable local-device workflow. No arbitrary shell execution is exposed.</p><div class="scwb-v350__cards"><article><strong>1. Inventory</strong><span>Record device identity, transport, firmware, state, and capabilities.</span></article><article><strong>2. Consent</strong><span>Allowlist devices and operations with expiration and sensitive-action confirmation.</span></article><article><strong>3. Run</strong><span>Plan ordered tasks, rollback steps, stop conditions, and simulation fallbacks.</span></article></div></section>
                <section data-scwb-v350-view="inventory" class="scwb-v350__view<?php echo 'inventory'===$panel?' is-active':''; ?>" <?php echo 'inventory'===$panel?'':'hidden'; ?>><h3>Connected-device inventory</h3><div class="scwb-v350__grid"><?php self::field('Device name','device_name','text','Bench instrument'); self::field('Device ID','device_id','text','bench-instrument'); self::field('Type','device_type','text','instrument'); self::field('Transport','transport','text','usb'); self::field('Vendor','vendor'); self::field('Model','model'); self::field('Firmware','firmware'); self::field('Status','status','text','available'); self::field('Capabilities, comma-separated','capabilities','text','read, acquire, calibrate',true); ?></div><div class="scwb-v350__actions"><button data-scwb-v350-action="add-device">Add device</button><button data-scwb-v350-action="discover">Discover capabilities</button><button data-scwb-v350-action="save-device">Save private device</button></div><div data-scwb-v350-inventory class="scwb-v350__inventory"></div></section>
                <section data-scwb-v350-view="consent" class="scwb-v350__view<?php echo 'consent'===$panel?' is-active':''; ?>" <?php echo 'consent'===$panel?'':'hidden'; ?>><h3>Local consent and allowlist</h3><p>Sensitive operations require the exact phrase <code>AUTHORIZE LOCAL DEVICE CONTROL</code>.</p><div class="scwb-v350__grid"><?php self::field('Actor ID','actor_id','text','local-user'); self::field('Allowed operations','allowed_operations','text','discover, read, acquire, calibrate, simulate, validate',true); self::field('Expires at','expires_at','text',''); self::field('Confirmation phrase','confirmation_phrase','text','',true); ?></div><div class="scwb-v350__actions"><button data-scwb-v350-action="build-consent">Build consent</button><button data-scwb-v350-action="revoke-consent">Revoke local consent</button></div></section>
                <section data-scwb-v350-view="calibration" class="scwb-v350__view<?php echo 'calibration'===$panel?' is-active':''; ?>" <?php echo 'calibration'===$panel?'':'hidden'; ?>><h3>Calibration schedule</h3><div class="scwb-v350__grid"><?php self::field('Default interval, days','interval_days','number','180'); self::field('Warning window, days','warning_days','number','30'); ?></div><div class="scwb-v350__actions"><button data-scwb-v350-action="build-calibration">Build schedule</button></div></section>
                <section data-scwb-v350-view="sessions" class="scwb-v350__view<?php echo 'sessions'===$panel?' is-active':''; ?>" <?php echo 'sessions'===$panel?'':'hidden'; ?>><h3>Instrument sessions</h3><div class="scwb-v350__grid"><?php self::field('Session title','session_title','text','Instrument session'); self::field('Operator ID','operator_id','text','local-user'); self::field('Notes','session_notes','textarea','',true); ?></div><div class="scwb-v350__actions"><button data-scwb-v350-action="build-session">Build session</button></div></section>
                <section data-scwb-v350-view="runs" class="scwb-v350__view<?php echo 'runs'===$panel?' is-active':''; ?>" <?php echo 'runs'===$panel?'':'hidden'; ?>><h3>Experiment-run orchestration</h3><div class="scwb-v350__grid"><?php self::field('Run title','run_title','text','Device experiment run'); self::field('Tasks JSON','tasks_json','textarea','[{"device_id":"bench-instrument","operation":"acquire","capability":"measurement","expected_duration_seconds":30,"rollback":{"operation":"reset"}}]',true); ?></div><label class="scwb-v350__check"><input type="checkbox" data-scwb-v350-field="simulation_mode"> Use clearly labeled hardware-absent simulation mode</label><div class="scwb-v350__actions"><button data-scwb-v350-action="build-run">Build run plan</button><button data-scwb-v350-action="save-run">Save private run</button></div></section>
                <section data-scwb-v350-view="recovery" class="scwb-v350__view<?php echo 'recovery'===$panel?' is-active':''; ?>" <?php echo 'recovery'===$panel?'':'hidden'; ?>><h3>Logs and failure recovery</h3><div class="scwb-v350__grid"><?php self::field('Failed task ID','failed_task_id'); self::field('Failure type','failure_type','text','unknown'); self::field('Log message','log_message','textarea','',true); ?></div><div class="scwb-v350__actions"><button data-scwb-v350-action="append-log">Append chained log</button><button data-scwb-v350-action="build-recovery">Build recovery plan</button><button data-scwb-v350-action="download-bundle">Download run bundle</button></div></section>
                <section data-scwb-v350-view="simulation" class="scwb-v350__view<?php echo 'simulation'===$panel?' is-active':''; ?>" <?php echo 'simulation'===$panel?'':'hidden'; ?>><h3>Hardware-absent simulation</h3><p>Create a deterministic, clearly labeled simulation twin for the selected device.</p><div class="scwb-v350__grid"><?php self::field('Seed','simulation_seed','number','1'); self::field('Noise fraction','noise_fraction','number','0.01'); self::field('Initial state JSON','initial_state','textarea','{"value":0}',true); ?></div><div class="scwb-v350__actions"><button data-scwb-v350-action="build-simulation">Build simulation twin</button></div></section>
            </div>
            <aside class="scwb-v350__output"><header><strong>Device orchestration record</strong><span data-scwb-v350-message aria-live="polite">Ready.</span></header><pre data-scwb-v350-output>{}</pre></aside>
            <footer class="scwb-v350__boundary"><strong>Control boundary:</strong> Workbench creates allowlisted plans and records. It does not expose arbitrary shell execution, bypass device safety controls, or replace laboratory, electrical, machinery, aviation, medical-device, or occupational safety procedures.</footer>
        </section><?php return ob_get_clean();
    }
}
SCWB_V350_Device_Orchestration::boot();
