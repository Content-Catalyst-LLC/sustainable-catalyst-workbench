<?php
/** Workbench v3.7.0 — Domain Laboratory Integration. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V370_Domain_Laboratory_Integration {
    const VERSION = '3.7.0';
    const LINK_POST_TYPE = 'scwb_lab_link';
    const RUN_POST_TYPE = 'scwb_lab_run';
    const LINK_META = '_scwb_lab_link_record';
    const RUN_META = '_scwb_lab_run_record';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_records'), 7);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 40);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V370_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v370.css';
        $js = $base . '/assets/js/sc-workbench-v370.js';
        wp_register_style('scwb-v370', plugins_url('assets/css/sc-workbench-v370.css', SCWB_V370_PLUGIN_FILE), array(), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v370', plugins_url('assets/js/sc-workbench-v370.js', SCWB_V370_PLUGIN_FILE), array(), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_records() {
        $common = array('public' => false, 'show_ui' => true, 'show_in_rest' => false, 'exclude_from_search' => true, 'supports' => array('title', 'author'), 'map_meta_cap' => true, 'capability_type' => 'post');
        register_post_type(self::LINK_POST_TYPE, array_merge($common, array('labels' => array('name' => __('Workbench Lab Links', 'scwb'), 'singular_name' => __('Workbench Lab Link', 'scwb')))));
        register_post_type(self::RUN_POST_TYPE, array_merge($common, array('labels' => array('name' => __('Workbench Lab Runs', 'scwb'), 'singular_name' => __('Workbench Lab Run', 'scwb')))));
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_domain_laboratory' => 'workspace',
            'sc_workbench_lab_domain_registry' => 'domains',
            'sc_workbench_lab_calculation_adapter' => 'calculations',
            'sc_workbench_lab_experiment_bridge' => 'experiments',
            'sc_workbench_lab_validation_contract' => 'validation',
            'sc_workbench_lab_notebook_sync' => 'notebook',
            'sc_workbench_lab_report_template' => 'reports',
            'sc_workbench_lab_project_sync' => 'sync',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, function($atts) use ($panel) {
                    $atts = shortcode_atts(array('project' => 'default', 'domain' => 'physics', 'display' => 'full', 'title' => 'Domain Laboratory Integration'), $atts);
                    return SCWB_V370_Domain_Laboratory_Integration::render($atts, $panel);
                });
            }
        }
    }

    public static function can_write() { return is_user_logged_in() && current_user_can('edit_posts'); }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/domain-laboratory-status', array('methods' => 'GET', 'callback' => array(__CLASS__, 'status'), 'permission_callback' => '__return_true'));
        register_rest_route('scwb/v1', '/lab-links', array('methods' => array('GET', 'POST'), 'callback' => array(__CLASS__, 'links'), 'permission_callback' => array(__CLASS__, 'can_write')));
        register_rest_route('scwb/v1', '/lab-runs', array('methods' => array('GET', 'POST'), 'callback' => array(__CLASS__, 'runs'), 'permission_callback' => array(__CLASS__, 'can_write')));
        register_rest_route('scwb/v1', '/lab-notebooks', array('methods' => 'POST', 'callback' => array(__CLASS__, 'save_notebook'), 'permission_callback' => array(__CLASS__, 'can_write')));
        register_rest_route('scwb/v1', '/lab-reports', array('methods' => 'POST', 'callback' => array(__CLASS__, 'save_report'), 'permission_callback' => array(__CLASS__, 'can_write')));
        register_rest_route('scwb/v1', '/lab-sync-plans', array('methods' => 'POST', 'callback' => array(__CLASS__, 'save_sync'), 'permission_callback' => array(__CLASS__, 'can_write')));
    }

    public static function status() {
        return rest_ensure_response(array('ok' => true, 'schema' => 'sc-workbench-domain-laboratory-status/1.0', 'version' => self::VERSION, 'privateStorageAvailable' => self::can_write(), 'physicalExecution' => false, 'clinicalDiagnosis' => false, 'licensedCertification' => false));
    }

    private static function request_record($request) {
        $record = method_exists($request, 'get_json_params') ? $request->get_json_params() : array();
        return is_array($record) ? $record : array();
    }

    private static function list_records($type, $meta) {
        $posts = get_posts(array('post_type' => $type, 'post_status' => 'private', 'author' => get_current_user_id(), 'numberposts' => 100, 'orderby' => 'modified', 'order' => 'DESC'));
        $records = array();
        foreach ($posts as $post) { $records[] = array('wordpressId' => $post->ID, 'title' => $post->post_title, 'record' => get_post_meta($post->ID, $meta, true)); }
        return rest_ensure_response(array('ok' => true, 'records' => $records));
    }

    private static function save_record($request, $type, $meta, $fallback) {
        if ('GET' === $request->get_method()) { return self::list_records($type, $meta); }
        $record = self::request_record($request);
        $title = sanitize_text_field(isset($record['title']) ? $record['title'] : (isset($record['domainLabel']) ? $record['domainLabel'] : $fallback));
        $post_id = wp_insert_post(array('post_type' => $type, 'post_status' => 'private', 'post_title' => $title, 'post_author' => get_current_user_id()), true);
        if (is_wp_error($post_id)) { return $post_id; }
        update_post_meta($post_id, $meta, $record);
        return rest_ensure_response(array('ok' => true, 'wordpressId' => $post_id, 'record' => $record));
    }

    public static function links($request) { return self::save_record($request, self::LINK_POST_TYPE, self::LINK_META, 'Workbench Lab link'); }
    public static function runs($request) { return self::save_record($request, self::RUN_POST_TYPE, self::RUN_META, 'Workbench Lab run'); }
    public static function save_notebook($request) { return self::save_record($request, self::RUN_POST_TYPE, self::RUN_META, 'Lab notebook entry'); }
    public static function save_report($request) { return self::save_record($request, self::RUN_POST_TYPE, self::RUN_META, 'Lab report'); }
    public static function save_sync($request) { return self::save_record($request, self::LINK_POST_TYPE, self::LINK_META, 'Lab sync plan'); }

    private static function domains() {
        return array(
            'physics' => 'Physics', 'chemistry' => 'Chemistry', 'biology' => 'Biology', 'astronomy' => 'Astronomy',
            'energy-engineering' => 'Energy & Engineering', 'electrical-embedded' => 'Electrical & Embedded',
            'mechanical-thermal' => 'Mechanical & Thermal', 'civil-infrastructure' => 'Civil & Infrastructure',
            'architecture-building' => 'Architecture & Building', 'urban-spatial' => 'Urban & Spatial',
            'sustainable-cities' => 'Sustainable Cities', 'circular-economy' => 'Circular Economy',
            'economics-development' => 'Economics & Development', 'aerospace' => 'Aerospace',
            'rocket-propulsion' => 'Rocket Propulsion', 'microbiology' => 'Microbiology',
            'biochemistry' => 'Biochemistry', 'biotechnology' => 'Biotechnology', 'biomedical' => 'Biomedical Engineering',
            'health-human-services' => 'Health & Human Services',
        );
    }

    private static function field($label, $name, $type = 'text', $value = '', $wide = false) { ?>
        <label class="scwb-v370__field<?php echo $wide ? ' scwb-v370__field--wide' : ''; ?>"><span><?php echo esc_html($label); ?></span>
            <?php if ('textarea' === $type) : ?><textarea data-scwb-v370-field="<?php echo esc_attr($name); ?>"><?php echo esc_textarea($value); ?></textarea>
            <?php else : ?><input type="<?php echo esc_attr($type); ?>" data-scwb-v370-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>"><?php endif; ?>
        </label><?php
    }

    public static function render($atts, $panel = 'workspace') {
        self::register_assets(); wp_enqueue_style('scwb-v370'); wp_enqueue_script('scwb-v370');
        wp_localize_script('scwb-v370', 'SCWBV370Config', array('version' => self::VERSION, 'restUrl' => esc_url_raw(rest_url('scwb/v1')), 'nonce' => wp_create_nonce('wp_rest'), 'authenticated' => self::can_write()));
        $project = sanitize_key($atts['project']) ?: 'default'; $display = sanitize_key($atts['display']) ?: 'full';
        $domain = sanitize_key($atts['domain']); if (!isset(self::domains()[$domain])) { $domain = 'physics'; }
        $tabs = array('workspace' => 'Overview', 'domains' => 'Domains', 'calculations' => 'Calculations', 'experiments' => 'Experiments', 'validation' => 'Validation', 'notebook' => 'Notebook', 'reports' => 'Reports', 'sync' => 'Synchronization');
        $instance = 'scwb-v370-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v370 scwb-v370--<?php echo esc_attr($display); ?>" data-scwb-v370 data-scwb-v370-panel="<?php echo esc_attr($panel); ?>" data-scwb-v370-project="<?php echo esc_attr($project); ?>" data-scwb-v370-domain="<?php echo esc_attr($domain); ?>" data-scwb-v370-version="3.7.0">
            <header class="scwb-v370__header"><div><p class="scwb-v370__eyebrow">Sustainable Catalyst Workbench · v3.7.0</p><h2><?php echo esc_html($atts['title']); ?></h2><p>Connect Workbench calculations, experiments, validation, notebooks, reports, and reproducibility records to Sustainable Catalyst Lab domain workspaces through explicit, auditable contracts.</p></div><span class="scwb-v370__status" data-scwb-v370-status><?php echo self::can_write() ? 'Private Lab records available' : 'Browser-local integration mode'; ?></span></header>
            <nav class="scwb-v370__tabs" role="tablist" aria-label="Domain laboratory integration tools"><?php foreach ($tabs as $key => $label) : ?><button type="button" role="tab" data-scwb-v370-tab="<?php echo esc_attr($key); ?>" class="<?php echo $key === $panel ? 'is-active' : ''; ?>" aria-selected="<?php echo $key === $panel ? 'true' : 'false'; ?>"><?php echo esc_html($label); ?></button><?php endforeach; ?></nav>
            <div class="scwb-v370__toolbar"><label><span>Laboratory domain</span><select data-scwb-v370-field="domain"><?php foreach (self::domains() as $key => $label) : ?><option value="<?php echo esc_attr($key); ?>" <?php selected($domain, $key); ?>><?php echo esc_html($label); ?></option><?php endforeach; ?></select></label><span>Project: <strong><?php echo esc_html($project); ?></strong></span></div>
            <div class="scwb-v370__views">
                <section data-scwb-v370-view="workspace" class="scwb-v370__view<?php echo 'workspace' === $panel ? ' is-active' : ''; ?>" <?php echo 'workspace' === $panel ? '' : 'hidden'; ?>><h3>Shared domain workflow</h3><div class="scwb-v370__cards"><article><strong>Calculate</strong><p>Carry equations, inputs, units, assumptions, evidence, and equivalent implementations into a Lab domain.</p></article><article><strong>Experiment</strong><p>Translate research questions into protocols, controls, instruments, replicates, safety boundaries, and reproducibility records.</p></article><article><strong>Validate</strong><p>Apply domain-specific checks without claiming automatic certification, clinical diagnosis, or licensed approval.</p></article><article><strong>Publish</strong><p>Synchronize notebook entries and draft reports while retaining provenance, review state, and immutable hashes.</p></article></div><p class="scwb-v370__boundary">Workbench prepares and validates auditable records. It does not independently authorize physical experiments, diagnose patients, or replace licensed scientific and engineering review.</p></section>
                <section data-scwb-v370-view="domains" class="scwb-v370__view<?php echo 'domains' === $panel ? ' is-active' : ''; ?>" <?php echo 'domains' === $panel ? '' : 'hidden'; ?>><h3>Domain registry</h3><p>Review active and planned Lab domains, their tool capabilities, units, and validation requirements.</p><button type="button" data-scwb-v370-action="domain-profile">Build domain profile</button></section>
                <section data-scwb-v370-view="calculations" class="scwb-v370__view<?php echo 'calculations' === $panel ? ' is-active' : ''; ?>" <?php echo 'calculations' === $panel ? '' : 'hidden'; ?>><h3>Calculation adapter</h3><div class="scwb-v370__grid"><?php self::field('Title', 'title', 'text', 'Domain calculation'); self::field('Equation', 'equation', 'text', 'y = f(x)'); self::field('Inputs as JSON', 'inputs', 'textarea', '{"x": 1}', true); self::field('Units as JSON', 'units', 'textarea', '{"x": "SI"}', true); self::field('Expected outputs', 'outputs', 'text', 'y'); self::field('Language', 'language', 'text', 'python'); self::field('Assumptions', 'assumptions', 'textarea', '', true); ?></div><button type="button" data-scwb-v370-action="calculation">Build calculation contract</button></section>
                <section data-scwb-v370-view="experiments" class="scwb-v370__view<?php echo 'experiments' === $panel ? ' is-active' : ''; ?>" <?php echo 'experiments' === $panel ? '' : 'hidden'; ?>><h3>Experiment bridge</h3><div class="scwb-v370__grid"><?php self::field('Experiment title', 'experiment_title', 'text', 'Laboratory experiment'); self::field('Hypothesis', 'hypothesis', 'textarea', '', true); self::field('Independent variables', 'independent', 'text', 'input'); self::field('Dependent variables', 'dependent', 'text', 'response'); self::field('Controls', 'controls', 'text', 'baseline'); self::field('Instruments', 'instruments', 'text', 'simulated instrument'); self::field('Protocol steps', 'steps', 'textarea', "Prepare\nMeasure\nRecord", true); self::field('Replicates', 'replicates', 'number', '3'); ?></div><button type="button" data-scwb-v370-action="experiment">Build experiment contract</button></section>
                <section data-scwb-v370-view="validation" class="scwb-v370__view<?php echo 'validation' === $panel ? ' is-active' : ''; ?>" <?php echo 'validation' === $panel ? '' : 'hidden'; ?>><h3>Domain validation contract</h3><div class="scwb-v370__grid"><?php self::field('Artifact type', 'artifact_type', 'text', 'calculation'); self::field('Completed checks', 'checks', 'textarea', '', true); self::field('Reviewer', 'reviewer', 'text', ''); self::field('Evidence IDs', 'evidence', 'text', ''); ?></div><button type="button" data-scwb-v370-action="validation">Build validation contract</button></section>
                <section data-scwb-v370-view="notebook" class="scwb-v370__view<?php echo 'notebook' === $panel ? ' is-active' : ''; ?>" <?php echo 'notebook' === $panel ? '' : 'hidden'; ?>><h3>Notebook synchronization</h3><div class="scwb-v370__grid"><?php self::field('Entry title', 'notebook_title', 'text', 'Laboratory notebook entry'); self::field('Observations', 'observations', 'textarea', '', true); self::field('Author', 'author', 'text', ''); self::field('Related record IDs', 'related_ids', 'text', ''); ?></div><button type="button" data-scwb-v370-action="notebook">Build notebook entry</button><button type="button" data-scwb-v370-save="lab-notebooks">Save privately</button></section>
                <section data-scwb-v370-view="reports" class="scwb-v370__view<?php echo 'reports' === $panel ? ' is-active' : ''; ?>" <?php echo 'reports' === $panel ? '' : 'hidden'; ?>><h3>Domain report template</h3><div class="scwb-v370__grid"><?php self::field('Report title', 'report_title', 'text', 'Domain laboratory report'); self::field('Record IDs', 'report_records', 'text', ''); ?></div><button type="button" data-scwb-v370-action="report">Build report template</button><button type="button" data-scwb-v370-save="lab-reports">Save privately</button></section>
                <section data-scwb-v370-view="sync" class="scwb-v370__view<?php echo 'sync' === $panel ? ' is-active' : ''; ?>" <?php echo 'sync' === $panel ? '' : 'hidden'; ?>><h3>Workbench ↔ Lab synchronization</h3><div class="scwb-v370__grid"><?php self::field('Workbench hash', 'workbench_hash', 'text', ''); self::field('Lab hash', 'lab_hash', 'text', ''); self::field('Conflict strategy', 'conflict_strategy', 'text', 'manual'); self::field('Direction', 'direction', 'text', 'bidirectional'); ?></div><button type="button" data-scwb-v370-action="sync">Build synchronization plan</button><button type="button" data-scwb-v370-save="lab-sync-plans">Save privately</button><button type="button" data-scwb-v370-action="bundle">Build portable bundle</button></section>
            </div>
            <div class="scwb-v370__result"><p data-scwb-v370-message aria-live="polite">Choose a domain tool to build an auditable integration record.</p><pre data-scwb-v370-output>{}</pre><div><button type="button" data-scwb-v370-action="download">Download record</button></div></div>
        </section>
        <?php return ob_get_clean();
    }
}

SCWB_V370_Domain_Laboratory_Integration::boot();
