<?php
/** Workbench v3.6.0 — Computational Intelligence and Predictive Analytics. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V360_Computational_Intelligence {
    const VERSION = '3.6.0';
    const MODEL_POST_TYPE = 'scwb_model';
    const RUN_POST_TYPE = 'scwb_ml_run';
    const MODEL_META = '_scwb_model_record';
    const RUN_META = '_scwb_ml_run_record';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_records'), 7);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 40);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V360_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v360.css';
        $js = $base . '/assets/js/sc-workbench-v360.js';
        wp_register_style('scwb-v360', plugins_url('assets/css/sc-workbench-v360.css', SCWB_V360_PLUGIN_FILE), array(), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v360', plugins_url('assets/js/sc-workbench-v360.js', SCWB_V360_PLUGIN_FILE), array(), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_records() {
        $common = array('public' => false, 'show_ui' => true, 'show_in_rest' => false, 'exclude_from_search' => true, 'supports' => array('title', 'author'), 'map_meta_cap' => true, 'capability_type' => 'post');
        register_post_type(self::MODEL_POST_TYPE, array_merge($common, array('labels' => array('name' => __('Workbench Models', 'scwb'), 'singular_name' => __('Workbench Model', 'scwb')))));
        register_post_type(self::RUN_POST_TYPE, array_merge($common, array('labels' => array('name' => __('Workbench ML Runs', 'scwb'), 'singular_name' => __('Workbench ML Run', 'scwb')))));
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_computational_intelligence' => 'workspace',
            'sc_workbench_dataset_profiler' => 'data',
            'sc_workbench_predictive_modeling' => 'modeling',
            'sc_workbench_model_validation' => 'validation',
            'sc_workbench_forecasting' => 'forecasting',
            'sc_workbench_drift_leakage' => 'responsible',
            'sc_workbench_model_card' => 'cards',
            'sc_workbench_ml_reproducibility' => 'reproduce',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, function($atts) use ($panel) {
                    $atts = shortcode_atts(array('project' => 'default', 'display' => 'full', 'title' => 'Computational Intelligence and Predictive Analytics'), $atts);
                    return SCWB_V360_Computational_Intelligence::render($atts, $panel);
                });
            }
        }
    }

    public static function can_write() {
        return is_user_logged_in() && current_user_can('edit_posts');
    }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/computational-intelligence-status', array('methods' => 'GET', 'callback' => array(__CLASS__, 'status'), 'permission_callback' => '__return_true'));
        register_rest_route('scwb/v1', '/model-records', array('methods' => array('GET', 'POST'), 'callback' => array(__CLASS__, 'models'), 'permission_callback' => array(__CLASS__, 'can_write')));
        register_rest_route('scwb/v1', '/ml-runs', array('methods' => array('GET', 'POST'), 'callback' => array(__CLASS__, 'runs'), 'permission_callback' => array(__CLASS__, 'can_write')));
        register_rest_route('scwb/v1', '/model-cards', array('methods' => 'POST', 'callback' => array(__CLASS__, 'save_model_card'), 'permission_callback' => array(__CLASS__, 'can_write')));
        register_rest_route('scwb/v1', '/validation-reports', array('methods' => 'POST', 'callback' => array(__CLASS__, 'save_validation'), 'permission_callback' => array(__CLASS__, 'can_write')));
    }

    public static function status() {
        return rest_ensure_response(array('ok' => true, 'schema' => 'sc-workbench-computational-intelligence-status/1.0', 'version' => self::VERSION, 'privateStorageAvailable' => self::can_write(), 'trainingExecution' => false, 'highStakesAutomation' => false));
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
        $title = sanitize_text_field(isset($record['title']) ? $record['title'] : (isset($record['modelName']) ? $record['modelName'] : $fallback));
        $post_id = wp_insert_post(array('post_type' => $type, 'post_status' => 'private', 'post_title' => $title, 'post_author' => get_current_user_id()), true);
        if (is_wp_error($post_id)) { return $post_id; }
        update_post_meta($post_id, $meta, $record);
        return rest_ensure_response(array('ok' => true, 'wordpressId' => $post_id, 'record' => $record));
    }

    public static function models($request) { return self::save_record($request, self::MODEL_POST_TYPE, self::MODEL_META, 'Workbench model'); }
    public static function runs($request) { return self::save_record($request, self::RUN_POST_TYPE, self::RUN_META, 'Workbench ML run'); }
    public static function save_model_card($request) { return self::save_record($request, self::MODEL_POST_TYPE, self::MODEL_META, 'Model card'); }
    public static function save_validation($request) { return self::save_record($request, self::RUN_POST_TYPE, self::RUN_META, 'Validation report'); }

    private static function field($label, $name, $type = 'text', $value = '', $wide = false) { ?>
        <label class="scwb-v360__field<?php echo $wide ? ' scwb-v360__field--wide' : ''; ?>"><span><?php echo esc_html($label); ?></span>
            <?php if ('textarea' === $type) : ?><textarea data-scwb-v360-field="<?php echo esc_attr($name); ?>"><?php echo esc_textarea($value); ?></textarea>
            <?php else : ?><input type="<?php echo esc_attr($type); ?>" data-scwb-v360-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>"><?php endif; ?>
        </label><?php
    }

    public static function render($atts, $panel = 'workspace') {
        self::register_assets(); wp_enqueue_style('scwb-v360'); wp_enqueue_script('scwb-v360');
        wp_localize_script('scwb-v360', 'SCWBV360Config', array('version' => self::VERSION, 'restUrl' => esc_url_raw(rest_url('scwb/v1')), 'nonce' => wp_create_nonce('wp_rest'), 'authenticated' => self::can_write()));
        $project = sanitize_key($atts['project']) ?: 'default'; $display = sanitize_key($atts['display']) ?: 'full';
        $tabs = array('workspace' => 'Overview', 'data' => 'Data', 'modeling' => 'Modeling', 'validation' => 'Validation', 'forecasting' => 'Forecasting', 'responsible' => 'Drift & Fairness', 'cards' => 'Model Cards', 'reproduce' => 'Reproducibility');
        $instance = 'scwb-v360-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v360 scwb-v360--<?php echo esc_attr($display); ?>" data-scwb-v360 data-scwb-v360-panel="<?php echo esc_attr($panel); ?>" data-scwb-v360-project="<?php echo esc_attr($project); ?>" data-scwb-v360-version="3.6.0">
            <header class="scwb-v360__header"><div><p class="scwb-v360__eyebrow">Sustainable Catalyst Workbench · v3.6.0</p><h2><?php echo esc_html($atts['title']); ?></h2><p>Profile data, plan leakage-safe experiments, evaluate predictive models, inspect uncertainty and drift, compare subgroup performance, and preserve auditable model cards and reproducibility records.</p></div><span class="scwb-v360__status" data-scwb-v360-status><?php echo self::can_write() ? 'Private model storage available' : 'Browser-local analytics mode'; ?></span></header>
            <nav class="scwb-v360__tabs" role="tablist" aria-label="Computational intelligence tools"><?php foreach ($tabs as $key => $label) : ?><button type="button" role="tab" data-scwb-v360-tab="<?php echo esc_attr($key); ?>" class="<?php echo $key === $panel ? 'is-active' : ''; ?>" aria-selected="<?php echo $key === $panel ? 'true' : 'false'; ?>"><?php echo esc_html($label); ?></button><?php endforeach; ?></nav>
            <div class="scwb-v360__views">
                <section data-scwb-v360-view="workspace" class="scwb-v360__view<?php echo 'workspace' === $panel ? ' is-active' : ''; ?>" <?php echo 'workspace' === $panel ? '' : 'hidden'; ?>><h3>Auditable predictive workflow</h3><p>Workbench separates data profiling, split design, feature decisions, model evaluation, responsible-use audits, documentation, and human review.</p><div class="scwb-v360__cards"><article><strong>1. Frame</strong><span>Define task, target, intended use, exclusions, and review requirements.</span></article><article><strong>2. Validate</strong><span>Use held-out data, baselines, cross-validation, uncertainty, leakage, drift, and subgroup checks.</span></article><article><strong>3. Document</strong><span>Export content-hashed model cards, experiment records, and cross-language fixtures.</span></article></div></section>
                <section data-scwb-v360-view="data" class="scwb-v360__view<?php echo 'data' === $panel ? ' is-active' : ''; ?>" <?php echo 'data' === $panel ? '' : 'hidden'; ?>><h3>Dataset profile and split plan</h3><div class="scwb-v360__grid"><?php self::field('Dataset ID', 'dataset_id', 'text', 'sample-dataset'); self::field('Target column', 'target', 'text', 'outcome'); self::field('Rows JSON', 'rows_json', 'textarea', '[{"feature":1,"group":"A","outcome":2},{"feature":2,"group":"B","outcome":4},{"feature":3,"group":"A","outcome":6}]', true); self::field('Split strategy', 'split_strategy', 'text', 'random'); ?></div><div class="scwb-v360__actions"><button data-scwb-v360-action="profile">Profile dataset</button><button data-scwb-v360-action="split">Build split plan</button><button data-scwb-v360-action="features">Build feature plan</button></div></section>
                <section data-scwb-v360-view="modeling" class="scwb-v360__view<?php echo 'modeling' === $panel ? ' is-active' : ''; ?>" <?php echo 'modeling' === $panel ? '' : 'hidden'; ?>><h3>Predictive modeling scaffold</h3><div class="scwb-v360__grid"><?php self::field('Experiment name', 'experiment_name', 'text', 'Predictive analytics experiment'); self::field('Task', 'task', 'text', 'regression'); self::field('Features, comma-separated', 'features', 'text', 'feature', true); self::field('Validation strategy', 'validation_strategy', 'text', 'k-fold'); ?></div><label class="scwb-v360__check"><input type="checkbox" data-scwb-v360-field="high_stakes_context"> High-stakes context requiring independent qualified review</label><div class="scwb-v360__actions"><button data-scwb-v360-action="scaffold">Build experiment scaffold</button></div></section>
                <section data-scwb-v360-view="validation" class="scwb-v360__view<?php echo 'validation' === $panel ? ' is-active' : ''; ?>" <?php echo 'validation' === $panel ? '' : 'hidden'; ?>><h3>Model validation</h3><div class="scwb-v360__grid"><?php self::field('Actual values JSON', 'y_true', 'textarea', '[2,4,6,8]', true); self::field('Predicted values JSON', 'y_pred', 'textarea', '[2.1,3.8,6.2,7.9]', true); self::field('Positive label', 'positive_label', 'text', '1'); self::field('Fold metrics JSON', 'folds_json', 'textarea', '[{"rmse":0.3},{"rmse":0.4},{"rmse":0.35}]', true); ?></div><div class="scwb-v360__actions"><button data-scwb-v360-action="regression">Regression metrics</button><button data-scwb-v360-action="classification">Classification metrics</button><button data-scwb-v360-action="cross-validation">Summarize folds</button><button data-scwb-v360-action="save-validation">Save private validation</button></div></section>
                <section data-scwb-v360-view="forecasting" class="scwb-v360__view<?php echo 'forecasting' === $panel ? ' is-active' : ''; ?>" <?php echo 'forecasting' === $panel ? '' : 'hidden'; ?>><h3>Time-series forecasting</h3><div class="scwb-v360__grid"><?php self::field('Series JSON', 'series_json', 'textarea', '[10,12,13,15,18,20]', true); self::field('Forecast horizon', 'horizon', 'number', '5'); ?></div><div class="scwb-v360__actions"><button data-scwb-v360-action="forecast">Linear-trend forecast</button></div></section>
                <section data-scwb-v360-view="responsible" class="scwb-v360__view<?php echo 'responsible' === $panel ? ' is-active' : ''; ?>" <?php echo 'responsible' === $panel ? '' : 'hidden'; ?>><h3>Leakage, drift, and subgroup performance</h3><div class="scwb-v360__grid"><?php self::field('Reference values JSON', 'reference_json', 'textarea', '[1,2,3,4,5]', true); self::field('Current values JSON', 'current_json', 'textarea', '[2,3,4,5,6]', true); self::field('Known post-outcome fields', 'post_outcome_fields', 'text', 'final_outcome, approved_after_review', true); self::field('Group metrics JSON', 'groups_json', 'textarea', '[{"group":"A","count":100,"positive_rate":0.55,"true_positive_rate":0.8},{"group":"B","count":90,"positive_rate":0.45,"true_positive_rate":0.7}]', true); ?></div><div class="scwb-v360__actions"><button data-scwb-v360-action="drift">Audit drift</button><button data-scwb-v360-action="leakage">Audit leakage</button><button data-scwb-v360-action="fairness">Audit subgroup gaps</button></div></section>
                <section data-scwb-v360-view="cards" class="scwb-v360__view<?php echo 'cards' === $panel ? ' is-active' : ''; ?>" <?php echo 'cards' === $panel ? '' : 'hidden'; ?>><h3>Model card and review boundary</h3><div class="scwb-v360__grid"><?php self::field('Model name', 'model_name', 'text', 'Transparent baseline model'); self::field('Algorithm', 'algorithm', 'text', 'linear regression'); self::field('Intended uses', 'intended_uses', 'textarea', 'Exploratory forecasting and decision support', true); self::field('Limitations', 'limitations', 'textarea', 'Not validated beyond the documented dataset and time period', true); self::field('Reviewer', 'reviewer'); ?></div><div class="scwb-v360__actions"><button data-scwb-v360-action="model-card">Build model card</button><button data-scwb-v360-action="save-model">Save private model</button><button data-scwb-v360-action="download">Download analytics bundle</button></div></section>
                <section data-scwb-v360-view="reproduce" class="scwb-v360__view<?php echo 'reproduce' === $panel ? ' is-active' : ''; ?>" <?php echo 'reproduce' === $panel ? '' : 'hidden'; ?>><h3>Cross-language reproducibility</h3><div class="scwb-v360__grid"><?php self::field('Languages', 'languages', 'text', 'python,r,javascript,rust', true); self::field('Coefficients JSON', 'coefficients_json', 'textarea', '[1.5,-0.25]', true); self::field('Intercept', 'intercept', 'number', '0.5'); self::field('Absolute tolerance', 'tolerance', 'number', '0.000000001'); ?></div><div class="scwb-v360__actions"><button data-scwb-v360-action="reproducibility">Build reproducibility plan</button></div></section>
            </div>
            <aside class="scwb-v360__output"><header><strong>Computational intelligence record</strong><span data-scwb-v360-message aria-live="polite">Ready.</span></header><pre data-scwb-v360-output>{}</pre></aside>
            <footer class="scwb-v360__boundary"><strong>Responsible-use boundary:</strong> Workbench supports transparent analysis and review. It does not train arbitrary remote models, establish causation, certify legal or regulatory compliance, diagnose patients, or make autonomous employment, credit, education, insurance, benefits, safety, or other high-stakes decisions.</footer>
        </section><?php return ob_get_clean();
    }
}
SCWB_V360_Computational_Intelligence::boot();
