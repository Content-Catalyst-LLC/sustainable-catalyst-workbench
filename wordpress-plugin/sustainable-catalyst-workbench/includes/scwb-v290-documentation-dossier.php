<?php
/**
 * Sustainable Catalyst Prototyping Workbench v2.9.0.
 * Technical Documentation and Product Dossier Studio.
 */
if (!defined('ABSPATH')) { exit; }

if (!class_exists('SCWB_V290_Documentation_Dossier')) {
final class SCWB_V290_Documentation_Dossier {
    const VERSION = '2.9.0';
    const HANDLE = 'scwb-v290';
    private static $assets_loaded = false;

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_shortcodes'));
        add_filter('do_shortcode_tag', array(__CLASS__, 'append_suite'), 20, 4);
    }

    public static function register_shortcodes() {
        $shortcodes = array(
            'sc_workbench_documentation_dossier' => 'documentation',
            'sc_workbench_product_dossier' => 'product',
            'sc_workbench_requirements_traceability' => 'traceability',
            'sc_workbench_revision_change_control' => 'revision',
            'sc_workbench_verification_evidence' => 'evidence',
            'sc_workbench_release_readiness' => 'readiness',
        );
        foreach ($shortcodes as $tag => $panel) {
            add_shortcode($tag, function ($atts = array()) use ($panel) {
                return SCWB_V290_Documentation_Dossier::render_panel($panel, $atts);
            });
        }
    }

    public static function append_suite($output, $tag, $attr, $match) {
        $parents = array('sc_workbench_experiment_automation', 'sc_workbench_hardware_validation', 'sc_workbench_multilanguage_runtime');
        if (!in_array($tag, $parents, true) || false !== strpos($output, 'data-scwb-v290-suite')) { return $output; }
        $project = isset($attr['project']) ? $attr['project'] : 'default';
        return $output . self::render_suite_launcher($project);
    }

    private static function enqueue_assets() {
        if (self::$assets_loaded) { return; }
        self::$assets_loaded = true;
        $plugin_file = defined('SCWB_V290_PLUGIN_FILE') ? SCWB_V290_PLUGIN_FILE : dirname(__DIR__) . '/sustainable-catalyst-workbench.php';
        $base_url = plugin_dir_url($plugin_file);
        wp_enqueue_style(self::HANDLE, $base_url . 'assets/css/sc-workbench-v290.css', array(), self::VERSION);
        wp_enqueue_script(self::HANDLE, $base_url . 'assets/js/sc-workbench-v290.js', array(), self::VERSION, true);
        wp_localize_script(self::HANDLE, 'SCWBV290', array(
            'version' => self::VERSION,
            'runnerDefaultUrl' => 'http://127.0.0.1:8787',
            'storagePrefix' => 'scwb-v290:',
        ));
    }

    private static function titles() {
        return array(
            'documentation' => __('Technical Documentation Studio', 'sustainable-catalyst-workbench'),
            'product' => __('Product Dossier Studio', 'sustainable-catalyst-workbench'),
            'traceability' => __('Requirements-to-Test Traceability Studio', 'sustainable-catalyst-workbench'),
            'revision' => __('Revision and Engineering Change Control Studio', 'sustainable-catalyst-workbench'),
            'evidence' => __('Verification Evidence Registry', 'sustainable-catalyst-workbench'),
            'readiness' => __('Manufacturing and Release Readiness Studio', 'sustainable-catalyst-workbench'),
        );
    }

    public static function render_panel($panel, $atts = array()) {
        self::enqueue_assets();
        $titles = self::titles();
        $atts = shortcode_atts(array(
            'title' => isset($titles[$panel]) ? $titles[$panel] : __('Technical Documentation Studio', 'sustainable-catalyst-workbench'),
            'project' => 'default',
            'display' => 'full',
        ), $atts);
        $project = sanitize_key($atts['project']) ?: 'default';
        $id = wp_unique_id('scwb-v290-');
        ob_start(); ?>
        <section id="<?php echo esc_attr($id); ?>" class="scwb-v290 scwb-v290--<?php echo esc_attr($panel); ?>" data-scwb-v290-panel="<?php echo esc_attr($panel); ?>" data-scwb-v290-project="<?php echo esc_attr($project); ?>">
            <header class="scwb-v290__header">
                <div>
                    <p class="scwb-v290__eyebrow"><?php esc_html_e('Sustainable Catalyst Prototyping Workbench · v2.9.0', 'sustainable-catalyst-workbench'); ?></p>
                    <h2><?php echo esc_html($atts['title']); ?></h2>
                </div>
                <span class="scwb-v290__status" data-scwb-v290-status><?php esc_html_e('Versioned browser-local record', 'sustainable-catalyst-workbench'); ?></span>
            </header>
            <?php self::render_body($panel); ?>
            <p class="scwb-v290__boundary"><?php esc_html_e('Documentation, readiness, compliance, manufacturing, certification, and verification records are planning and evidence-management aids. They do not establish regulatory approval, product safety, conformity, fitness for use, or professional sign-off. Validate every record against applicable standards, controlled source files, actual hardware and software revisions, qualified review, and organizational quality procedures.', 'sustainable-catalyst-workbench'); ?></p>
        </section>
        <?php return ob_get_clean();
    }

    private static function field($label, $name, $type = 'text', $value = '', $placeholder = '', $wide = false) { ?>
        <label class="scwb-v290__field<?php echo $wide ? ' scwb-v290__field--wide' : ''; ?>">
            <span><?php echo esc_html($label); ?></span>
            <?php if ('textarea' === $type) : ?>
                <textarea data-scwb-v290-field="<?php echo esc_attr($name); ?>" placeholder="<?php echo esc_attr($placeholder); ?>"><?php echo esc_textarea($value); ?></textarea>
            <?php else : ?>
                <input type="<?php echo esc_attr($type); ?>" data-scwb-v290-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>" placeholder="<?php echo esc_attr($placeholder); ?>">
            <?php endif; ?>
        </label>
    <?php }

    private static function actions($primary = 'Build documentation record', $connect = false) { ?>
        <div class="scwb-v290__actions">
            <button type="button" class="scwb-v290__button scwb-v290__button--primary" data-scwb-v290-action="analyze"><?php echo esc_html($primary); ?></button>
            <?php if ($connect) : ?><button type="button" class="scwb-v290__button" data-scwb-v290-action="connect"><?php esc_html_e('Connect local runner', 'sustainable-catalyst-workbench'); ?></button><?php endif; ?>
            <button type="button" class="scwb-v290__button" data-scwb-v290-action="save"><?php esc_html_e('Save locally', 'sustainable-catalyst-workbench'); ?></button>
            <button type="button" class="scwb-v290__button" data-scwb-v290-action="export-json"><?php esc_html_e('Export JSON', 'sustainable-catalyst-workbench'); ?></button>
            <button type="button" class="scwb-v290__button" data-scwb-v290-action="export-markdown"><?php esc_html_e('Export Markdown', 'sustainable-catalyst-workbench'); ?></button>
            <button type="button" class="scwb-v290__button" data-scwb-v290-action="export-html"><?php esc_html_e('Export HTML', 'sustainable-catalyst-workbench'); ?></button>
        </div>
        <div class="scwb-v290__workspace">
            <div class="scwb-v290__summary" data-scwb-v290-summary aria-live="polite"></div>
            <pre class="scwb-v290__result" data-scwb-v290-result>{}</pre>
        </div>
    <?php }

    private static function render_body($panel) {
        echo '<div class="scwb-v290__body"><div class="scwb-v290__form">';
        if ('documentation' === $panel) {
            self::field('Document title', 'title', 'text', 'Engineering technical report');
            self::field('Project revision', 'revision', 'text', '0.1.0');
            self::field('Owner or reviewer', 'owner', 'text', '');
            self::field('Sections (JSON)', 'sections', 'textarea', '[{"id":"summary","title":"Executive summary","content":"Purpose, scope, and current state.","status":"review","source_records":["REQ-1"]},{"id":"architecture","title":"System architecture","content":"Components, interfaces, data flow, and boundaries.","status":"draft","source_records":["ARCH-1"]},{"id":"verification","title":"Verification and validation","content":"Test results, simulations, measurements, and deviations.","status":"draft","source_records":["TEST-1","EV-1"]}]', '', true);
            self::field('Assumptions, one per line', 'assumptions', 'textarea', "Nominal operating conditions\nControlled source data", '', true);
            self::field('Limitations, one per line', 'limitations', 'textarea', "Prototype maturity\nPending independent review", '', true);
            self::field('Risks, one per line', 'risks', 'textarea', "Revision mismatch\nIncomplete verification coverage", '', true);
            self::actions('Build technical document', true);
        } elseif ('product' === $panel) {
            self::field('Product or system name', 'product_name', 'text', 'Sustainable sensing platform');
            self::field('Dossier title', 'title', 'text', 'Product technical dossier');
            self::field('Revision', 'revision', 'text', '1.0.0');
            self::field('Dossier sections (JSON)', 'sections', 'textarea', '[{"id":"requirements","title":"Requirements","content":"Approved product and system requirements.","status":"approved"},{"id":"design","title":"Design definition","content":"Architecture, schematics, code, BOM, and interfaces.","status":"review"},{"id":"validation","title":"Verification evidence","content":"Traceability, test reports, calibration, and model validation.","status":"review"},{"id":"release","title":"Release and manufacturing","content":"Revision baseline, build instructions, quality controls, and known limitations.","status":"draft"}]', '', true);
            self::field('Runner URL', 'runner_url', 'url', 'http://127.0.0.1:8787');
            self::field('Pairing code', 'pairing_code', 'text', '', 'Six-digit code');
            self::actions('Build product dossier', true);
        } elseif ('traceability' === $panel) {
            self::field('Requirements (JSON)', 'requirements', 'textarea', '[{"id":"REQ-1","title":"Measure temperature within ±0.5 °C","source":"Product requirements","priority":"critical","status":"approved","verification_method":"test"},{"id":"REQ-2","title":"Export a versioned measurement record","source":"Data requirements","priority":"high","status":"implemented","verification_method":"demonstration"}]', '', true);
            self::field('Verification records (JSON)', 'verifications', 'textarea', '[{"id":"TEST-1","title":"Temperature accuracy test","requirement_ids":["REQ-1"],"evidence_ids":["EV-1"],"status":"pass","revision":"1.0.0"},{"id":"DEMO-1","title":"Record export demonstration","requirement_ids":["REQ-2"],"evidence_ids":["EV-2"],"status":"pass","revision":"1.0.0"}]', '', true);
            self::actions('Evaluate traceability');
        } elseif ('revision' === $panel) {
            self::field('Revision history (JSON)', 'revisions', 'textarea', '[{"revision":"0.1.0","date":"2026-07-13","author":"Project team","summary":"Initial prototype baseline","artifact_hash":"abc123","approved":true},{"revision":"1.0.0","date":"2026-07-13","author":"Project team","summary":"Validated release baseline","artifact_hash":"def456","approved":true}]', '', true);
            self::field('Engineering changes (JSON)', 'changes', 'textarea', '[{"id":"CR-1","title":"Improve enclosure sealing","reason":"Field ingress risk","affected_items":["MECH-ENCLOSURE","TEST-IP"],"status":"approved","target_revision":"1.1.0"}]', '', true);
            self::actions('Audit revisions and changes');
        } elseif ('evidence' === $panel) {
            self::field('Evidence records (JSON)', 'records', 'textarea', '[{"id":"EV-1","title":"Temperature accuracy test report","kind":"test","source_uri":"reports/temperature-accuracy.pdf","revision":"1.0.0","content_hash":"abc123","generated_at":"2026-07-13T00:00:00Z","approved":true},{"id":"EV-2","title":"Export demonstration record","kind":"report","source_uri":"reports/export-demo.json","revision":"1.0.0","content_hash":"def456","generated_at":"2026-07-13T00:00:00Z","approved":true}]', '', true);
            self::actions('Build evidence register');
        } else {
            self::field('Readiness items (JSON)', 'items', 'textarea', '[{"id":"RD-REQ","category":"requirements","title":"Requirements approved","status":"complete","critical":true,"evidence_ids":["EV-REQ"]},{"id":"RD-DES","category":"design","title":"Design baseline released","status":"complete","critical":true,"evidence_ids":["EV-DES"]},{"id":"RD-VER","category":"verification","title":"Critical verification complete","status":"in-progress","critical":true,"evidence_ids":["EV-VER"]},{"id":"RD-MFG","category":"manufacturing","title":"Build and inspection instructions reviewed","status":"in-progress","critical":false,"evidence_ids":[]},{"id":"RD-DOC","category":"documentation","title":"Technical dossier approved","status":"in-progress","critical":true,"evidence_ids":[]}]', '', true);
            self::actions('Evaluate release readiness');
        }
        echo '</div></div>';
    }

    private static function render_suite_launcher($project) {
        self::enqueue_assets();
        return '<aside class="scwb-v290__suite" data-scwb-v290-suite><div><strong>' . esc_html__('Documentation and Product Dossier Studio', 'sustainable-catalyst-workbench') . '</strong><span>' . esc_html__('Convert project records into traceable documentation, evidence registers, revision histories, and release-readiness dossiers.', 'sustainable-catalyst-workbench') . '</span></div>' . do_shortcode('[sc_workbench_documentation_dossier project="' . esc_attr(sanitize_key($project) ?: 'default') . '" display="compact"]') . '</aside>';
    }
}
SCWB_V290_Documentation_Dossier::boot();
}
