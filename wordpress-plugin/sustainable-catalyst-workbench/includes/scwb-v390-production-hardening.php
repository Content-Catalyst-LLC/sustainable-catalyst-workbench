<?php
/** Workbench v3.9.0 — Production Evaluation and Public Release Hardening. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V390_Production_Hardening {
    const VERSION = '3.9.0';
    const EVALUATION_POST_TYPE = 'scwb_evaluation';
    const GATE_POST_TYPE = 'scwb_release_gate';
    const EVALUATION_META = '_scwb_evaluation_record';
    const GATE_META = '_scwb_release_gate_record';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_records'), 7);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 40);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V390_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v390.css';
        $js = $base . '/assets/js/sc-workbench-v390.js';
        wp_register_style('scwb-v390', plugins_url('assets/css/sc-workbench-v390.css', SCWB_V390_PLUGIN_FILE), array(), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v390', plugins_url('assets/js/sc-workbench-v390.js', SCWB_V390_PLUGIN_FILE), array(), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_records() {
        $common = array(
            'public' => false,
            'show_ui' => true,
            'show_in_rest' => false,
            'exclude_from_search' => true,
            'supports' => array('title', 'author'),
            'map_meta_cap' => true,
            'capability_type' => 'post',
        );
        register_post_type(self::EVALUATION_POST_TYPE, array_merge($common, array('labels' => array(
            'name' => __('Workbench Evaluation Reports', 'scwb'),
            'singular_name' => __('Workbench Evaluation Report', 'scwb'),
        ))));
        register_post_type(self::GATE_POST_TYPE, array_merge($common, array('labels' => array(
            'name' => __('Workbench Release Gates', 'scwb'),
            'singular_name' => __('Workbench Release Gate', 'scwb'),
        ))));
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_production_hardening' => 'workspace',
            'sc_workbench_accessibility_audit' => 'accessibility',
            'sc_workbench_performance_evaluation' => 'performance',
            'sc_workbench_security_review' => 'security',
            'sc_workbench_compatibility_matrix' => 'compatibility',
            'sc_workbench_migration_stress' => 'migration',
            'sc_workbench_failure_injection' => 'resilience',
            'sc_workbench_onboarding' => 'onboarding',
            'sc_workbench_extension_contract' => 'contracts',
            'sc_workbench_public_release_gate' => 'release',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, function($atts) use ($panel) {
                    $atts = shortcode_atts(array(
                        'project' => 'default',
                        'display' => 'full',
                        'title' => 'Production Evaluation and Public Release Hardening',
                    ), $atts);
                    return SCWB_V390_Production_Hardening::render($atts, $panel);
                });
            }
        }
    }

    public static function can_write() {
        return is_user_logged_in() && current_user_can('edit_posts');
    }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/production-hardening-status', array(
            'methods' => 'GET', 'callback' => array(__CLASS__, 'status'), 'permission_callback' => '__return_true',
        ));
        register_rest_route('scwb/v1', '/evaluation-reports', array(
            'methods' => array('GET', 'POST'), 'callback' => array(__CLASS__, 'evaluations'), 'permission_callback' => array(__CLASS__, 'can_write'),
        ));
        register_rest_route('scwb/v1', '/release-gates', array(
            'methods' => array('GET', 'POST'), 'callback' => array(__CLASS__, 'gates'), 'permission_callback' => array(__CLASS__, 'can_write'),
        ));
        register_rest_route('scwb/v1', '/public-release-manifests', array(
            'methods' => 'POST', 'callback' => array(__CLASS__, 'save_manifest'), 'permission_callback' => array(__CLASS__, 'can_write'),
        ));
        register_rest_route('scwb/v1', '/extension-contracts', array(
            'methods' => 'POST', 'callback' => array(__CLASS__, 'save_extension_contract'), 'permission_callback' => array(__CLASS__, 'can_write'),
        ));
    }

    public static function status() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-production-hardening-status/1.0',
            'version' => self::VERSION,
            'requiredEvaluations' => array('accessibility', 'performance', 'security', 'compatibility', 'migration-stress', 'failure-recovery', 'onboarding', 'extension-contract'),
            'privateStorageAvailable' => self::can_write(),
            'humanReleaseApprovalRequired' => true,
            'automaticPublicationAuthorized' => false,
            'productionCertificationClaim' => false,
        ));
    }

    private static function request_record($request) {
        $record = method_exists($request, 'get_json_params') ? $request->get_json_params() : array();
        return is_array($record) ? $record : array();
    }

    private static function list_records($type, $meta) {
        $posts = get_posts(array(
            'post_type' => $type, 'post_status' => 'private', 'author' => get_current_user_id(),
            'numberposts' => 100, 'orderby' => 'modified', 'order' => 'DESC',
        ));
        $records = array();
        foreach ($posts as $post) {
            $records[] = array('wordpressId' => $post->ID, 'title' => $post->post_title, 'record' => get_post_meta($post->ID, $meta, true));
        }
        return rest_ensure_response(array('ok' => true, 'records' => $records));
    }

    private static function save_record($type, $meta, $request, $prefix) {
        $record = self::request_record($request);
        if (!$record) { return new WP_Error('scwb_empty_record', 'A record is required.', array('status' => 400)); }
        $title = sanitize_text_field(isset($record['title']) ? $record['title'] : $prefix . ' ' . gmdate('Y-m-d H:i:s'));
        $id = wp_insert_post(array('post_type' => $type, 'post_status' => 'private', 'post_title' => $title, 'post_author' => get_current_user_id()), true);
        if (is_wp_error($id)) { return $id; }
        update_post_meta($id, $meta, $record);
        return rest_ensure_response(array('ok' => true, 'wordpressId' => $id, 'record' => $record));
    }

    public static function evaluations($request) {
        return 'GET' === $request->get_method()
            ? self::list_records(self::EVALUATION_POST_TYPE, self::EVALUATION_META)
            : self::save_record(self::EVALUATION_POST_TYPE, self::EVALUATION_META, $request, 'Evaluation');
    }

    public static function gates($request) {
        return 'GET' === $request->get_method()
            ? self::list_records(self::GATE_POST_TYPE, self::GATE_META)
            : self::save_record(self::GATE_POST_TYPE, self::GATE_META, $request, 'Release gate');
    }

    public static function save_manifest($request) {
        return self::save_record(self::GATE_POST_TYPE, self::GATE_META, $request, 'Public release manifest');
    }

    public static function save_extension_contract($request) {
        return self::save_record(self::EVALUATION_POST_TYPE, self::EVALUATION_META, $request, 'Extension contract');
    }

    private static function field($label, $name, $type = 'text', $value = '', $wide = false) {
        ?><label class="scwb-v390__field<?php echo $wide ? ' scwb-v390__field--wide' : ''; ?>">
            <span><?php echo esc_html($label); ?></span>
            <?php if ('textarea' === $type) : ?>
                <textarea data-scwb-v390-field="<?php echo esc_attr($name); ?>"><?php echo esc_textarea($value); ?></textarea>
            <?php else : ?>
                <input type="<?php echo esc_attr($type); ?>" data-scwb-v390-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>">
            <?php endif; ?>
        </label><?php
    }

    public static function render($atts, $panel = 'workspace') {
        self::register_assets();
        wp_enqueue_style('scwb-v390');
        wp_enqueue_script('scwb-v390');
        wp_localize_script('scwb-v390', 'SCWBV390Config', array(
            'version' => self::VERSION,
            'restUrl' => esc_url_raw(rest_url('scwb/v1')),
            'backendUrl' => '',
            'nonce' => wp_create_nonce('wp_rest'),
            'authenticated' => self::can_write(),
        ));
        $project = sanitize_key($atts['project']) ?: 'default';
        $display = sanitize_key($atts['display']) ?: 'full';
        $tabs = array(
            'workspace' => 'Overview', 'accessibility' => 'Accessibility', 'performance' => 'Performance',
            'security' => 'Security', 'compatibility' => 'Compatibility', 'migration' => 'Migration Stress',
            'resilience' => 'Failure Recovery', 'onboarding' => 'Onboarding', 'contracts' => 'Extension Contracts',
            'release' => 'Release Gate',
        );
        $instance = 'scwb-v390-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v390 scwb-v390--<?php echo esc_attr($display); ?>" data-scwb-v390 data-scwb-v390-panel="<?php echo esc_attr($panel); ?>" data-scwb-v390-project="<?php echo esc_attr($project); ?>" data-scwb-v390-version="3.9.0">
            <header class="scwb-v390__header">
                <div>
                    <p class="scwb-v390__eyebrow">Sustainable Catalyst Workbench · v3.9.0</p>
                    <h2><?php echo esc_html($atts['title']); ?></h2>
                    <p>Evaluate accessibility, performance, security, compatibility, migrations, recovery, onboarding, and extension stability before a human authorizes public release.</p>
                </div>
                <span class="scwb-v390__status">Evidence-gated · human approved</span>
            </header>
            <nav class="scwb-v390__tabs" aria-label="Production hardening tools" role="tablist">
                <?php foreach ($tabs as $key => $label) : ?>
                    <button type="button" class="<?php echo $key === $panel ? 'is-active' : ''; ?>" data-scwb-v390-tab="<?php echo esc_attr($key); ?>"><?php echo esc_html($label); ?></button>
                <?php endforeach; ?>
            </nav>
            <div class="scwb-v390__views">
                <section class="scwb-v390__view" data-scwb-v390-view="workspace" <?php echo 'workspace' === $panel ? '' : 'hidden'; ?>>
                    <h3>Public-release evaluation system</h3>
                    <div class="scwb-v390__cards">
                        <article><strong>Inclusive interface</strong><p>Keyboard, focus, labels, landmarks, screen-reader smoke tests, motion, contrast, and mobile overflow.</p></article>
                        <article><strong>Production budgets</strong><p>Transfer, JavaScript, CSS, interaction, layout stability, API latency, and memory thresholds.</p></article>
                        <article><strong>Operational resilience</strong><p>Migration stress, corrupt data, storage exhaustion, interrupted updates, backend outages, and rollback.</p></article>
                        <article><strong>Stable public contracts</strong><p>Versioned schemas, hooks, routes, deprecations, compatibility floors, onboarding, and human release gates.</p></article>
                    </div>
                    <div class="scwb-v390__boundary"><strong>Boundary:</strong> A ready gate records evidence and human approval. It does not certify regulatory compliance or publish automatically.</div>
                </section>
                <section class="scwb-v390__view" data-scwb-v390-view="accessibility" <?php echo 'accessibility' === $panel ? '' : 'hidden'; ?>>
                    <h3>Accessibility evaluation</h3><div class="scwb-v390__grid">
                    <?php self::field('Pages tested', 'pagesTested', 'number', '12'); self::field('Contrast failures', 'contrastFailures', 'number', '0'); self::field('Heading failures', 'headingFailures', 'number', '0'); self::field('Mobile overflow failures', 'mobileOverflowFailures', 'number', '0'); ?>
                    </div><button type="button" data-scwb-v390-action="accessibility">Build accessibility report</button>
                </section>
                <section class="scwb-v390__view" data-scwb-v390-view="performance" <?php echo 'performance' === $panel ? '' : 'hidden'; ?>>
                    <h3>Performance budgets</h3><div class="scwb-v390__grid">
                    <?php self::field('Transfer (KB)', 'transferKb', 'number', '900'); self::field('JavaScript (KB)', 'javascriptKb', 'number', '450'); self::field('LCP (ms)', 'lcpMs', 'number', '2200'); self::field('INP (ms)', 'inpMs', 'number', '180'); self::field('CLS', 'cls', 'number', '0.08'); self::field('API p95 (ms)', 'apiP95Ms', 'number', '600'); ?>
                    </div><button type="button" data-scwb-v390-action="performance">Evaluate performance</button>
                </section>
                <section class="scwb-v390__view" data-scwb-v390-view="security" <?php echo 'security' === $panel ? '' : 'hidden'; ?>>
                    <h3>Security and privacy posture</h3><div class="scwb-v390__grid">
                    <?php self::field('Public write routes', 'publicWriteRoutes', 'number', '0'); self::field('Potential secrets', 'secretFindings', 'number', '0'); self::field('High dependency findings', 'dependencyFindings', 'number', '0'); self::field('Unsafe HTML findings', 'unsafeHtmlFindings', 'number', '0'); ?>
                    </div><button type="button" data-scwb-v390-action="security">Build security report</button>
                </section>
                <section class="scwb-v390__view" data-scwb-v390-view="compatibility" <?php echo 'compatibility' === $panel ? '' : 'hidden'; ?>>
                    <h3>Cross-environment compatibility matrix</h3><div class="scwb-v390__grid">
                    <?php self::field('Browsers', 'browsers', 'text', 'Chrome,Firefox,Safari,Edge', true); self::field('Editors', 'editors', 'text', 'Gutenberg,Classic Editor,Elementor', true); self::field('Viewports', 'viewports', 'text', '360x800,768x1024,1440x900', true); self::field('Failures (JSON)', 'compatibilityFailures', 'textarea', '[]', true); ?>
                    </div><button type="button" data-scwb-v390-action="compatibility">Build compatibility matrix</button>
                </section>
                <section class="scwb-v390__view" data-scwb-v390-view="migration" <?php echo 'migration' === $panel ? '' : 'hidden'; ?>>
                    <h3>Migration and storage stress test</h3><div class="scwb-v390__grid">
                    <?php self::field('Projects', 'projects', 'number', '100'); self::field('Records', 'records', 'number', '10000'); self::field('Observed duration (ms)', 'observedDurationMs', 'number', '2000'); self::field('Maximum duration (ms)', 'maximumDurationMs', 'number', '5000'); ?>
                    </div><button type="button" data-scwb-v390-action="migration">Build migration stress report</button>
                </section>
                <section class="scwb-v390__view" data-scwb-v390-view="resilience" <?php echo 'resilience' === $panel ? '' : 'hidden'; ?>>
                    <h3>Failure injection and recovery</h3><?php self::field('Scenarios (JSON)', 'scenarios', 'textarea', '[{"id":"backend-offline","severity":"high","recovered":true,"dataLoss":false},{"id":"interrupted-update","severity":"critical","recovered":true,"dataLoss":false}]', true); ?>
                    <button type="button" data-scwb-v390-action="resilience">Build recovery report</button>
                </section>
                <section class="scwb-v390__view" data-scwb-v390-view="onboarding" <?php echo 'onboarding' === $panel ? '' : 'hidden'; ?>>
                    <h3>Public onboarding package</h3><div class="scwb-v390__grid">
                    <?php self::field('Personas', 'personas', 'text', 'researcher,engineer,educator,reviewer', true); self::field('Quickstarts', 'quickstarts', 'text', 'browser-local,wordpress,offline-install', true); self::field('Example projects', 'exampleProjects', 'number', '4'); ?>
                    </div><button type="button" data-scwb-v390-action="onboarding">Build onboarding package</button>
                </section>
                <section class="scwb-v390__view" data-scwb-v390-view="contracts" <?php echo 'contracts' === $panel ? '' : 'hidden'; ?>>
                    <h3>Stable extension contract</h3><div class="scwb-v390__grid">
                    <?php self::field('Contract name', 'contractName', 'text', 'sc-workbench-extension-contract'); self::field('Contract version', 'contractVersion', 'text', '1.0'); self::field('Hooks', 'hooks', 'text', 'scwb:project-changed,scwb:studio-activated', true); self::field('Schemas', 'schemas', 'text', 'sc-workbench-project/3.0,sc-workbench-evidence/1.0,sc-workbench-handoff/1.0', true); ?>
                    </div><button type="button" data-scwb-v390-action="contracts">Build extension contract</button>
                </section>
                <section class="scwb-v390__view" data-scwb-v390-view="release" <?php echo 'release' === $panel ? '' : 'hidden'; ?>>
                    <h3>Human-controlled public release gate</h3>
                    <p>The gate requires all eight evaluation records, verified checksums, verified rollback, complete documentation, no unresolved high/critical findings, and explicit human approval.</p>
                    <label class="scwb-v390__approval"><input type="checkbox" data-scwb-v390-field="humanApproval"> I have reviewed the evidence and approve release.</label>
                    <button type="button" data-scwb-v390-action="release">Evaluate release gate</button>
                    <button type="button" data-scwb-v390-action="download">Download latest record</button>
                </section>
            </div>
            <section class="scwb-v390__result" aria-live="polite"><h3>Evaluation record</h3><p data-scwb-v390-summary>No evaluation has been generated.</p><pre data-scwb-v390-output>{}</pre></section>
        </section>
        <?php return ob_get_clean();
    }
}
SCWB_V390_Production_Hardening::boot();
