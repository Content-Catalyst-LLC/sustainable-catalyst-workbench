<?php
/** Workbench v4.4.0 — Automated Evaluation, Benchmarking, and Comparison Laboratory. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V440_Evaluation_Laboratory {
    const VERSION = '4.4.0';
    const EXPECTED_STUDIOS = 26;

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_records'), 4);
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 50);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_records() {
        $common = array(
            'public' => false,
            'show_ui' => false,
            'show_in_rest' => false,
            'exclude_from_search' => true,
            'supports' => array('title', 'author', 'custom-fields'),
        );
        register_post_type('scwb_benchmark', array_merge($common, array('label' => 'Workbench Benchmarks')));
        register_post_type('scwb_eval_run', array_merge($common, array('label' => 'Workbench Evaluation Runs')));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V440_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v440.css';
        $js = $base . '/assets/js/sc-workbench-v440.js';
        wp_register_style('scwb-v440', plugins_url('assets/css/sc-workbench-v440.css', SCWB_V440_PLUGIN_FILE), array('scwb-v430'), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v440', plugins_url('assets/js/sc-workbench-v440.js', SCWB_V440_PLUGIN_FILE), array('scwb-v430'), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_evaluation_lab' => 'workspace',
            'sc_workbench_benchmark_catalog' => 'benchmarks',
            'sc_workbench_experiment_matrix' => 'matrix',
            'sc_workbench_trial_statistics' => 'statistics',
            'sc_workbench_candidate_comparison' => 'comparison',
            'sc_workbench_regression_detection' => 'regression',
            'sc_workbench_reproducibility_audit' => 'reproducibility',
            'sc_workbench_evaluation_leaderboard' => 'leaderboard',
            'sc_workbench_evaluation_gate' => 'gate',
            'sc_workbench_evaluation_package' => 'package',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, function($atts = array()) use ($panel) {
                    $atts = shortcode_atts(array(
                        'project' => 'default',
                        'benchmark' => 'default',
                        'display' => 'full',
                        'title' => 'Automated Evaluation and Benchmarking Laboratory',
                    ), $atts);
                    return SCWB_V440_Evaluation_Laboratory::render($atts, $panel);
                });
            }
        }
    }

    private static function can_persist() { return is_user_logged_in() && current_user_can('edit_posts'); }
    public static function permission_persist() { return self::can_persist(); }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/evaluation-lab-status', array('methods' => 'GET', 'callback' => array(__CLASS__, 'status'), 'permission_callback' => '__return_true'));
        register_rest_route('scwb/v1', '/benchmarks', array('methods' => array('GET', 'POST'), 'callback' => array(__CLASS__, 'benchmarks'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
        register_rest_route('scwb/v1', '/evaluation-runs', array('methods' => array('GET', 'POST'), 'callback' => array(__CLASS__, 'evaluation_runs'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
        register_rest_route('scwb/v1', '/evaluation-matrices', array('methods' => 'POST', 'callback' => array(__CLASS__, 'matrix_plan'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
        register_rest_route('scwb/v1', '/evaluation-comparisons', array('methods' => 'POST', 'callback' => array(__CLASS__, 'comparison_plan'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
        register_rest_route('scwb/v1', '/evaluation-gates', array('methods' => 'POST', 'callback' => array(__CLASS__, 'gate_plan'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
    }

    public static function status() {
        return array(
            'ok' => true,
            'version' => self::VERSION,
            'expectedStudioCount' => self::EXPECTED_STUDIOS,
            'authenticated' => is_user_logged_in(),
            'canPersistPrivateEvaluationRecords' => self::can_persist(),
            'privateByDefault' => true,
            'browserFallback' => true,
            'offlineEvaluation' => true,
            'paidExternalDatabaseRequired' => false,
            'automaticExperimentExecutionAuthorized' => false,
            'automaticLeaderboardPublicationAuthorized' => false,
            'automaticBaselineReplacementAuthorized' => false,
            'automaticReleaseApprovalAuthorized' => false,
            'automaticCertificationAuthorized' => false,
        );
    }

    private static function list_records($type) {
        if (!function_exists('get_posts')) { return array(); }
        $posts = get_posts(array('post_type' => $type, 'post_status' => array('private', 'draft'), 'numberposts' => 100, 'orderby' => 'modified', 'order' => 'DESC'));
        $records = array();
        foreach ($posts as $post) {
            $records[] = array('id' => (int) $post->ID, 'title' => $post->post_title, 'status' => $post->post_status, 'modified' => $post->post_modified_gmt);
        }
        return $records;
    }

    private static function collection_response($type, $request) {
        $method = is_object($request) && method_exists($request, 'get_method') ? $request->get_method() : 'GET';
        if ('POST' !== strtoupper($method)) {
            return rest_ensure_response(array('ok' => true, 'records' => self::list_records($type)));
        }
        if (!function_exists('wp_insert_post')) {
            return rest_ensure_response(array('ok' => false, 'message' => 'Private WordPress persistence is unavailable.'));
        }
        $params = is_object($request) && method_exists($request, 'get_json_params') ? (array) $request->get_json_params() : array();
        $title = isset($params['title']) ? sanitize_text_field($params['title']) : 'Workbench evaluation record';
        $post_id = wp_insert_post(array('post_type' => $type, 'post_status' => 'private', 'post_title' => $title, 'post_author' => get_current_user_id()), true);
        if (is_wp_error($post_id)) {
            return rest_ensure_response(array('ok' => false, 'message' => $post_id->get_error_message()));
        }
        if (function_exists('update_post_meta')) {
            update_post_meta($post_id, '_scwb_v440_record', wp_json_encode($params));
        }
        return rest_ensure_response(array('ok' => true, 'id' => (int) $post_id, 'private' => true, 'automaticPublicationAuthorized' => false));
    }

    public static function benchmarks($request = null) { return self::collection_response('scwb_benchmark', $request); }
    public static function evaluation_runs($request = null) { return self::collection_response('scwb_eval_run', $request); }
    public static function matrix_plan() { return rest_ensure_response(array('ok' => true, 'requiresExplicitExecution' => true, 'automaticExperimentExecutionAuthorized' => false)); }
    public static function comparison_plan() { return rest_ensure_response(array('ok' => true, 'statisticalClaimAuthorized' => false, 'automaticBaselineReplacementAuthorized' => false)); }
    public static function gate_plan() { return rest_ensure_response(array('ok' => true, 'humanApprovalRequired' => true, 'automaticReleaseApprovalAuthorized' => false)); }

    private static function enqueue_assets() {
        self::register_assets();
        wp_enqueue_style('scwb-v440');
        wp_enqueue_script('scwb-v440');
    }

    private static function field($label, $name, $value = '', $type = 'text', $wide = false) {
        echo '<label class="scwb-v440__field' . ($wide ? ' scwb-v440__field--wide' : '') . '"><span>' . esc_html($label) . '</span>';
        if ('textarea' === $type) {
            echo '<textarea data-scwb-v440-field="' . esc_attr($name) . '">' . esc_textarea($value) . '</textarea>';
        } else {
            echo '<input type="' . esc_attr($type) . '" data-scwb-v440-field="' . esc_attr($name) . '" value="' . esc_attr($value) . '">';
        }
        echo '</label>';
    }

    private static function actions($primary) {
        echo '<div class="scwb-v440__actions"><button type="button" class="scwb-v440__button scwb-v440__button--primary" data-scwb-v440-action="build">' . esc_html($primary) . '</button><button type="button" class="scwb-v440__button" data-scwb-v440-action="save-local">Save browser record</button><button type="button" class="scwb-v440__button" data-scwb-v440-action="export">Export JSON</button></div><div class="scwb-v440__result" aria-live="polite"><p data-scwb-v440-summary>Ready to prepare an auditable evaluation record.</p><pre data-scwb-v440-output>{}</pre></div>';
    }

    private static function render_panel($panel, $benchmark) {
        echo '<div class="scwb-v440__grid">';
        if ('workspace' === $panel) {
            echo '<article class="scwb-v440__card"><strong>Define benchmarks</strong><span>Preserve metrics, directions, datasets, protocols, baselines, units, and review boundaries.</span></article>';
            echo '<article class="scwb-v440__card"><strong>Compare candidates</strong><span>Summarize repeated trials, uncertainty, practical differences, and regressions without overstating causality.</span></article>';
            echo '<article class="scwb-v440__card"><strong>Verify reproducibility</strong><span>Check seeds, runtime, environment, dataset, protocol, and repeated-run consistency.</span></article>';
            echo '<article class="scwb-v440__card"><strong>Gate human decisions</strong><span>Leaderboards, baseline replacement, release approval, and certification remain explicitly human controlled.</span></article>';
            self::field('Benchmark title', 'title', 'Scientific and Engineering Benchmark');
            self::field('Benchmark ID', 'benchmarkId', $benchmark);
            self::field('Metric name', 'metricName', 'score');
            self::field('Metric direction', 'direction', 'maximize');
            self::field('Candidates JSON', 'candidates', '["baseline","candidate-a"]', 'textarea', true);
            self::field('Parameter grid JSON', 'parameterGrid', '{"mode":["standard","robust"]}', 'textarea', true);
            self::field('Seeds JSON', 'seeds', '[42,43,44]', 'textarea', true);
            self::actions('Build evaluation workspace');
        } elseif ('benchmarks' === $panel) {
            self::field('Benchmark title', 'title', 'Scientific benchmark');
            self::field('Benchmark ID', 'benchmarkId', $benchmark);
            self::field('Domain', 'domain', 'general');
            self::field('Task type', 'taskType', 'scientific');
            self::field('Metric name', 'metricName', 'score');
            self::field('Direction', 'direction', 'maximize');
            self::field('Dataset hash', 'datasetHash', '');
            self::field('Protocol hash', 'protocolHash', '');
            self::actions('Normalize benchmark');
        } elseif ('matrix' === $panel) {
            self::field('Benchmark ID', 'benchmarkId', $benchmark);
            self::field('Candidates JSON', 'candidates', '["baseline","candidate-a"]', 'textarea', true);
            self::field('Parameter grid JSON', 'parameterGrid', '{"setting":[1,2]}', 'textarea', true);
            self::field('Seeds JSON', 'seeds', '[42,43]', 'textarea', true);
            self::field('Datasets JSON', 'datasets', '["dataset-a"]', 'textarea', true);
            self::field('Maximum runs', 'maxRuns', '500', 'number');
            self::actions('Build experiment matrix');
        } elseif ('statistics' === $panel) {
            self::field('Benchmark ID', 'benchmarkId', $benchmark);
            self::field('Metric name', 'metricName', 'score');
            self::field('Direction', 'direction', 'maximize');
            self::field('Trials JSON', 'trials', '[{"candidate":"baseline","metricValue":0.8,"seed":42,"success":true},{"candidate":"candidate-a","metricValue":0.84,"seed":42,"success":true}]', 'textarea', true);
            self::actions('Summarize trials');
        } elseif ('comparison' === $panel) {
            self::field('Baseline summary JSON', 'baseline', '{"mean":0.8,"stdev":0.02}', 'textarea', true);
            self::field('Candidate summary JSON', 'candidate', '{"mean":0.84,"stdev":0.02}', 'textarea', true);
            self::field('Direction', 'direction', 'maximize');
            self::field('Practical threshold', 'practicalThreshold', '0.01', 'number');
            self::actions('Compare candidates');
        } elseif ('regression' === $panel) {
            self::field('Metric label', 'label', 'primary metric');
            self::field('Baseline value', 'baselineValue', '0.84', 'number');
            self::field('Current value', 'currentValue', '0.82', 'number');
            self::field('Direction', 'direction', 'maximize');
            self::field('Absolute tolerance', 'absoluteTolerance', '0.005', 'number');
            self::field('Percent tolerance', 'percentTolerance', '0.5', 'number');
            self::actions('Detect regression');
        } elseif ('reproducibility' === $panel) {
            self::field('Trials JSON', 'trials', '[]', 'textarea', true);
            self::field('Metric tolerance', 'metricTolerance', '0.000001', 'number');
            self::actions('Audit reproducibility');
        } elseif ('leaderboard' === $panel) {
            self::field('Benchmark ID', 'benchmarkId', $benchmark);
            self::field('Metric name', 'metricName', 'score');
            self::field('Direction', 'direction', 'maximize');
            self::field('Entries JSON', 'entries', '[{"candidate":"baseline","metricValue":0.8},{"candidate":"candidate-a","metricValue":0.84}]', 'textarea', true);
            self::actions('Build provisional leaderboard');
        } elseif ('gate' === $panel) {
            self::field('Benchmark JSON', 'benchmark', '{"benchmarkId":"' . $benchmark . '"}', 'textarea', true);
            self::field('Regressions JSON', 'regressions', '[]', 'textarea', true);
            self::field('Reproducibility JSON', 'reproducibility', '{"ready":false}', 'textarea', true);
            self::field('Unresolved findings JSON', 'unresolvedFindings', '[]', 'textarea', true);
            self::field('Required artifacts JSON', 'requiredArtifacts', '["benchmark","trial-summary","reproducibility-audit"]', 'textarea', true);
            self::field('Available artifacts JSON', 'availableArtifacts', '[]', 'textarea', true);
            self::field('Approver', 'approver', '');
            self::actions('Evaluate release gate');
        } else {
            self::field('Benchmark JSON', 'benchmark', '{}', 'textarea', true);
            self::field('Experiment matrix JSON', 'matrix', '{}', 'textarea', true);
            self::field('Summaries JSON', 'summaries', '{}', 'textarea', true);
            self::field('Comparisons JSON', 'comparisons', '[]', 'textarea', true);
            self::field('Regressions JSON', 'regressions', '[]', 'textarea', true);
            self::field('Reproducibility JSON', 'reproducibility', '{}', 'textarea', true);
            self::field('Leaderboard JSON', 'leaderboard', '{}', 'textarea', true);
            self::field('Gate JSON', 'gate', '{}', 'textarea', true);
            self::actions('Build evaluation package');
        }
        echo '</div>';
    }

    public static function render($atts, $panel = 'workspace') {
        self::enqueue_assets();
        $project = sanitize_key($atts['project']);
        $benchmark = sanitize_key($atts['benchmark']);
        $display = in_array($atts['display'], array('full', 'compact'), true) ? $atts['display'] : 'full';
        $authenticated = self::can_persist();
        $instance = 'scwb-v440-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v440 scwb-v440--<?php echo esc_attr($display); ?>" data-scwb-v440 data-scwb-v440-panel="<?php echo esc_attr($panel); ?>" data-scwb-project="<?php echo esc_attr($project); ?>" data-scwb-benchmark="<?php echo esc_attr($benchmark); ?>" data-scwb-authenticated="<?php echo $authenticated ? 'true' : 'false'; ?>">
            <header class="scwb-v440__header"><div><p class="scwb-v440__eyebrow">Sustainable Catalyst Workbench · v4.4.0</p><h2><?php echo esc_html($atts['title']); ?></h2><p>Benchmark catalogs, experiment matrices, trial statistics, baseline comparisons, reproducibility audits, regression detection, provisional leaderboards, and human-controlled evaluation gates.</p></div><span class="scwb-v440__status <?php echo $authenticated ? 'is-online' : 'is-local'; ?>"><?php echo $authenticated ? 'Private WordPress storage available' : 'Browser-local evaluation'; ?></span></header>
            <?php self::render_panel($panel, $benchmark); ?>
            <?php if (!$authenticated) : ?><div class="scwb-v440__notice" role="status"><strong>Local-first mode.</strong><span>Sign in with an authorized WordPress account to preserve private benchmark and evaluation-run records on this site.</span></div><?php endif; ?>
            <p class="scwb-v440__boundary"><strong>Evaluation boundary:</strong> plans and reports do not automatically execute experiments, publish leaderboards, replace baselines, approve releases, establish causation, or certify scientific, engineering, safety, regulatory, or professional conclusions.</p>
        </section>
        <?php return ob_get_clean();
    }
}
SCWB_V440_Evaluation_Laboratory::boot();
