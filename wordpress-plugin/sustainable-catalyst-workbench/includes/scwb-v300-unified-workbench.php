<?php
/** Workbench v3.0.0 — Unified Prototyping Workbench. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V300_Unified_Workbench {
    const VERSION = '3.0.0';

    public static function boot() {
        add_action('wp_enqueue_scripts', array(__CLASS__, 'register_assets'));
        add_action('init', array(__CLASS__, 'register_shortcodes'));
    }

    public static function register_assets() {
        $base = defined('SCWB_V300_PLUGIN_FILE') ? SCWB_V300_PLUGIN_FILE : __FILE__;
        wp_register_style('scwb-v300', plugins_url('assets/css/sc-workbench-v300.css', $base), array(), self::VERSION);
        wp_register_script('scwb-v300', plugins_url('assets/js/sc-workbench-v300.js', $base), array(), self::VERSION, true);
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_unified' => 'hub',
            'sc_workbench_project_hub' => 'hub',
            'sc_workbench_studio_registry' => 'registry',
            'sc_workbench_handoff_center' => 'handoff',
            'sc_workbench_workspace_health' => 'health',
            'sc_workbench_project_export' => 'package',
            'sc_workbench_reset_center' => 'reset',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, function($atts = array()) use ($panel) { return SCWB_V300_Unified_Workbench::render($panel, $atts); });
            }
        }
    }

    private static function enqueue_assets() {
        wp_enqueue_style('scwb-v300');
        wp_enqueue_script('scwb-v300');
    }

    public static function render($panel, $atts = array()) {
        self::enqueue_assets();
        $atts = shortcode_atts(array(
            'project' => 'default',
            'title' => 'Unified Prototyping Workbench',
            'display' => 'full',
        ), $atts, 'sc_workbench_unified');
        $project = sanitize_key($atts['project']) ?: 'default';
        $display = sanitize_key($atts['display']);
        if (!in_array($display, array('compact', 'full', 'inline', 'drawer'), true)) { $display = 'full'; }
        $instance = 'scwb-v300-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v300 scwb-v300--<?php echo esc_attr($display); ?>" data-scwb-v300 data-scwb-v300-panel="<?php echo esc_attr($panel); ?>" data-scwb-v300-project="<?php echo esc_attr($project); ?>">
            <header class="scwb-v300__header">
                <div>
                    <p class="scwb-v300__eyebrow">Sustainable Catalyst Workbench · v3.0.0</p>
                    <h2><?php echo esc_html($atts['title']); ?></h2>
                    <p>One project environment for research, calculations, code, devices, simulations, experiments, visualization, evidence, and technical documentation.</p>
                </div>
                <span class="scwb-v300__status" data-scwb-v300-status>Unified project record</span>
            </header>
            <?php self::render_panel($panel); ?>
            <p class="scwb-v300__boundary"><strong>Review boundary:</strong> project health, migration, handoff, package, and reset records are planning and evidence-management aids. They do not establish technical correctness, regulatory compliance, safety, certification, or professional approval. Export a backup before destructive actions and revalidate imported records in every destination system.</p>
        </section>
        <?php return ob_get_clean();
    }

    private static function field($label, $name, $type = 'text', $value = '', $wide = false) { ?>
        <label class="scwb-v300__field<?php echo $wide ? ' scwb-v300__field--wide' : ''; ?>">
            <span><?php echo esc_html($label); ?></span>
            <?php if ('textarea' === $type) : ?>
                <textarea data-scwb-v300-field="<?php echo esc_attr($name); ?>"><?php echo esc_textarea($value); ?></textarea>
            <?php else : ?>
                <input type="<?php echo esc_attr($type); ?>" data-scwb-v300-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>">
            <?php endif; ?>
        </label>
    <?php }

    private static function actions($label, $connect = false) { ?>
        <div class="scwb-v300__actions">
            <button type="button" class="scwb-v300__button scwb-v300__button--primary" data-scwb-v300-action="analyze"><?php echo esc_html($label); ?></button>
            <?php if ($connect) : ?><button type="button" class="scwb-v300__button" data-scwb-v300-action="connect">Connect local runner</button><?php endif; ?>
            <button type="button" class="scwb-v300__button" data-scwb-v300-action="save">Save locally</button>
            <button type="button" class="scwb-v300__button" data-scwb-v300-action="export">Export JSON</button>
        </div>
        <div class="scwb-v300__workspace">
            <div class="scwb-v300__summary" data-scwb-v300-summary aria-live="polite"></div>
            <pre class="scwb-v300__result" data-scwb-v300-result>{}</pre>
        </div>
    <?php }

    private static function render_panel($panel) {
        echo '<div class="scwb-v300__body"><div class="scwb-v300__form">';
        if ('hub' === $panel) {
            echo '<div class="scwb-v300__hero-grid">';
            echo '<div><strong>Project Hub</strong><span>Audit the unified project manifest, studio state, evidence, artifacts, dependencies, and readiness.</span></div>';
            echo '<div><strong>Platform handoffs</strong><span>Package selected records for Site Intelligence, Decision Studio, Research Librarian, or another Workbench project.</span></div>';
            echo '<div><strong>Recovery safeguards</strong><span>Export versioned packages and require explicit confirmation before clearing saved workspace data.</span></div>';
            echo '</div>';
            self::field('Project manifest (JSON)', 'manifest', 'textarea', '{"project_id":"default","title":"Unified Workbench project","revision":"3.0.0","owner":"","studios":[{"id":"research","label":"Research Lab","version":"3.0.0","status":"active","record_count":4,"evidence_ids":["EV-1"],"warnings":[]},{"id":"simulation","label":"Simulation","version":"3.0.0","status":"complete","record_count":3,"evidence_ids":["EV-2"],"warnings":[]}],"artifacts":[{"path":"docs/report.md","kind":"documentation","content_hash":"abc123","size_bytes":1024,"studio_id":"research"}],"evidence_ids":["EV-1","EV-2"],"assumptions":[],"limitations":[],"metadata":{}}', true);
            self::field('Dependencies (JSON)', 'dependencies', 'textarea', '[{"source":"research","target":"simulation","kind":"data"}]', true);
            self::actions('Audit unified project', true);
        } elseif ('registry' === $panel) {
            self::field('Studio records (JSON)', 'studios', 'textarea', '[{"id":"research","label":"Research Lab","version":"3.0.0","status":"active","record_count":4,"evidence_ids":["EV-1"],"warnings":[]},{"id":"embedded","label":"Embedded Devices","version":"3.0.0","status":"not-started","record_count":0,"evidence_ids":[],"warnings":[]},{"id":"documentation","label":"Documentation","version":"3.0.0","status":"complete","record_count":2,"evidence_ids":["EV-2"],"warnings":[]}]', true);
            self::field('Dependencies (JSON)', 'dependencies', 'textarea', '[{"source":"research","target":"documentation","kind":"evidence"}]', true);
            self::actions('Evaluate studio registry');
        } elseif ('handoff' === $panel) {
            self::field('Target application', 'target', 'text', 'decision-studio');
            self::field('Project revision', 'revision', 'text', '3.0.0');
            self::field('Record IDs, one per line', 'record_ids', 'textarea', "CALC-1\nMODEL-1\nREPORT-1", true);
            self::field('Evidence IDs, one per line', 'evidence_ids', 'textarea', "EV-1\nEV-2", true);
            self::field('Handoff summary', 'summary', 'textarea', 'Review this validated project record and use it to compare alternatives and document the decision.', true);
            self::field('Assumptions, one per line', 'assumptions', 'textarea', 'Nominal operating conditions', true);
            self::field('Limitations, one per line', 'limitations', 'textarea', 'Prototype evidence only', true);
            self::actions('Build platform handoff');
        } elseif ('health' === $panel) {
            self::field('Workspace records (JSON)', 'records', 'textarea', '[{"key":"scwb-v300:default:project","category":"project","size_bytes":2048,"revision":"3.0.0","content_hash":"abc123","protected":true,"updated_at":"2026-07-13T00:00:00Z"},{"key":"scwb-v300:default:calculation:1","category":"calculation","size_bytes":1024,"revision":"3.0.0","content_hash":"def456","protected":false,"updated_at":"2026-07-13T00:00:00Z"}]', true);
            self::field('Expected categories, one per line', 'expected_categories', 'textarea', "project\ncalculation\ndocumentation", true);
            self::actions('Evaluate workspace health');
        } elseif ('package' === $panel) {
            self::field('Project manifest (JSON)', 'manifest', 'textarea', '{"project_id":"default","title":"Unified Workbench project","revision":"3.0.0","owner":"","studios":[],"artifacts":[],"evidence_ids":[],"assumptions":[],"limitations":[],"metadata":{}}', true);
            self::field('Package files (JSON)', 'files', 'textarea', '[{"path":"docs/report.md","kind":"documentation","content_hash":"abc123","size_bytes":1024,"studio_id":"documentation"},{"path":"data/results.json","kind":"dataset","content_hash":"def456","size_bytes":2048,"studio_id":"simulation"}]', true);
            self::field('Previous package hash', 'previous_package_hash', 'text', '');
            self::actions('Build project package', true);
        } else {
            self::field('Workspace records (JSON)', 'records', 'textarea', '[{"key":"scwb-v300:default:project","category":"project","size_bytes":2048,"revision":"3.0.0","content_hash":"abc123","protected":true,"updated_at":"2026-07-13T00:00:00Z"},{"key":"scwb-v300:default:calculation:1","category":"calculation","size_bytes":1024,"revision":"3.0.0","content_hash":"def456","protected":false,"updated_at":"2026-07-13T00:00:00Z"}]', true);
            self::field('Scope: selected, category, or all', 'scope', 'text', 'selected');
            self::field('Selected keys, one per line', 'selected_keys', 'textarea', 'scwb-v300:default:calculation:1', true);
            self::field('Categories, one per line', 'categories', 'textarea', 'calculation', true);
            self::field('Backup confirmed: true or false', 'backup_confirmed', 'text', 'false');
            self::field('Confirmation text', 'confirmation_text', 'text', '');
            self::actions('Create reset plan');
        }
        echo '</div></div>';
    }
}
SCWB_V300_Unified_Workbench::boot();
