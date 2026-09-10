<?php
/** Workbench v6.0.1 patch identity — Unified Computational Workbench. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V600_Unified_Computational_Workbench {
    const VERSION = '6.0.1';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 8);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 190);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V600_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v600.css';
        $js = $base . '/assets/js/sc-workbench-v600.js';
        wp_register_style('scwb-v600', plugins_url('assets/css/sc-workbench-v600.css', SCWB_V600_PLUGIN_FILE), array(), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v600', plugins_url('assets/js/sc-workbench-v600.js', SCWB_V600_PLUGIN_FILE), array(), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function backend_url($override = '') {
        if (class_exists('SCWB_V531_Settings_Backend_Repair')) {
            return SCWB_V531_Settings_Backend_Repair::backend_url($override);
        }
        return rtrim(trim((string) $override), '/');
    }

    private static function enqueue_assets($backend = '') {
        self::register_assets();
        wp_enqueue_style('scwb-v600');
        wp_enqueue_script('scwb-v600');
        wp_localize_script('scwb-v600', 'SCWBV600Config', array(
            'version' => self::VERSION,
            'backendUrl' => self::backend_url($backend),
            'routes' => array(
                'status' => '/v601/status',
                'projectBuild' => '/v600/project/build',
                'variablesResolve' => '/v600/variables/resolve',
                'linksValidate' => '/v600/links/validate',
                'provenanceBuild' => '/v600/provenance/build',
                'historyBuild' => '/v600/history/build',
                'exportBuild' => '/v600/export/build',
                'handoffBuild' => '/v600/handoff/build',
            ),
        ));
    }

    public static function register_shortcodes() {
        foreach (array(
            'sc_workbench_computational_project',
            'sc_workbench_unified_computational',
            'sc_workbench_computational_workbench',
            'sc_workbench_v600'
        ) as $tag) {
            if (shortcode_exists($tag)) { remove_shortcode($tag); }
            add_shortcode($tag, array(__CLASS__, 'shortcode'));
        }

        foreach (array('sc_workbench_homepage_instrument', 'sc_workbench_experience', 'sc_workbench_experience_page') as $tag) {
            if (shortcode_exists($tag)) { remove_shortcode($tag); }
        }
        add_shortcode('sc_workbench_homepage_instrument', array(__CLASS__, 'render_homepage'));
        add_shortcode('sc_workbench_experience', array(__CLASS__, 'render_experience'));
        add_shortcode('sc_workbench_experience_page', array(__CLASS__, 'render_experience'));
    }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/v600-interface-status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'status'),
            'permission_callback' => '__return_true',
        ));
    }

    public static function status() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-unified-computational-interface-status/1.0',
            'version' => self::VERSION,
            'backendConfigured' => '' !== self::backend_url(),
            'backendVersionRequired' => '6.0.1',
            'canonicalComputationalProjects' => true,
            'sharedVariables' => true,
            'linkedObjects' => true,
            'provenance' => true,
            'projectHistory' => true,
            'portableExports' => true,
            'crossPlatformHandoffs' => true,
            'automaticExecutionAuthorized' => false,
        ));
    }

    private static function promote_public_markup($html, $surface) {
        $html = str_replace('data-version="5.9.0"', 'data-version="6.0.1"', $html);
        $html = str_replace('SUSTAINABLE CATALYST WORKBENCH · v5.9.0', 'SUSTAINABLE CATALYST WORKBENCH · v6.0.1', $html);
        $html = str_replace('v5.9.0 ·', 'v6.0.1 ·', $html);
        if ('homepage' === $surface) {
            $html = str_replace('scwb-v590-home', 'scwb-v590-home scwb-v600-home', $html);
        } else {
            $html = str_replace('scwb-v590-experience', 'scwb-v590-experience scwb-v600-experience', $html);
            $html = str_replace('<span><i></i> FPGA + DIGITAL LOGIC</span>', '<span><i></i> FPGA + DIGITAL LOGIC</span><span><i></i> UNIFIED COMPUTATIONAL PROJECTS</span>', $html);
            $needle = '<a href="?studio=digital-logic"><b>FPGA, PYNQ &amp; Digital Logic</b><span>truth tables · K-maps · FSMs · timing · HDL · PYNQ</span></a>';
            $insert = '<a href="?studio=computational-project"><b>Unified Computational Project</b><span>shared variables · linked objects · provenance · history · exports · handoffs</span></a>' . $needle;
            $html = str_replace($needle, $insert, $html);
        }
        return $html;
    }

    public static function render_homepage($atts = array()) {
        if (!class_exists('SCWB_V590_FPGA_PYNQ_Digital_Logic')) {
            return '<div role="alert">Workbench homepage showcase requires the complete v6.0.0 plugin.</div>';
        }
        return self::promote_public_markup(SCWB_V590_FPGA_PYNQ_Digital_Logic::render_homepage($atts), 'homepage');
    }

    public static function render_experience($atts = array()) {
        if (!class_exists('SCWB_V590_FPGA_PYNQ_Digital_Logic')) {
            return '<div role="alert">Workbench experience requires the complete v6.0.0 plugin.</div>';
        }
        return self::promote_public_markup(SCWB_V590_FPGA_PYNQ_Digital_Logic::render_experience($atts), 'experience');
    }

    public static function shortcode($atts = array()) {
        $atts = shortcode_atts(array(
            'project' => 'default',
            'display' => 'full',
            'title' => 'Unified Computational Workbench',
            'backend' => '',
        ), $atts);
        return self::render($atts);
    }

    public static function render($atts = array()) {
        self::enqueue_assets(isset($atts['backend']) ? $atts['backend'] : '');
        $project = sanitize_key(isset($atts['project']) ? $atts['project'] : 'default') ?: 'default';
        $instance = 'scwb-v600-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v600" data-scwb-v600 data-project="<?php echo esc_attr($project); ?>" data-version="6.0.1">
            <header class="scwb-v600__header">
                <div>
                    <p class="scwb-v600__eyebrow">Sustainable Catalyst Workbench · Unified Computational Projects · v6.0.1</p>
                    <h2><?php echo esc_html(isset($atts['title']) ? $atts['title'] : 'Unified Computational Workbench'); ?></h2>
                    <p>Keep mathematics, graphs, geometry, numerical results, control models, electronics plans, and digital-logic artifacts in one linked computational project with shared variables and auditable provenance.</p>
                </div>
                <span class="scwb-v600__status" data-scwb-v600-status>Checking unified backend…</span>
            </header>

            <div class="scwb-v600__ribbon" aria-label="Unified project pipeline">
                <span>PROJECT</span><i>→</i><span>VARIABLES</span><i>→</i><span>OBJECTS</span><i>→</i><span>LINKS</span><i>→</i><span>PROVENANCE</span><i>→</i><span>EXPORT / HANDOFF</span>
            </div>

            <div class="scwb-v600__layout">
                <aside class="scwb-v600__controls">
                    <div class="scwb-v600__section-title"><span>COMPUTATIONAL PROJECT</span><b>LOCAL-FIRST</b></div>
                    <label><span>Project ID</span><input value="<?php echo esc_attr($project); ?>" data-scwb-v600-project-id></label>
                    <label><span>Title</span><input value="Integrated computational study" data-scwb-v600-title></label>
                    <label><span>Description</span><textarea rows="3" data-scwb-v600-description>Linked mathematical and engineering objects in one reproducible Workbench project.</textarea></label>

                    <details open>
                        <summary>Shared variables</summary>
                        <textarea rows="8" data-scwb-v600-variables>[
  {"name":"a","value":2,"valueType":"number","units":""},
  {"name":"frequency_hz","value":1000,"valueType":"number","units":"Hz"}
]</textarea>
                    </details>

                    <details open>
                        <summary>Computational objects</summary>
                        <textarea rows="12" data-scwb-v600-objects>[
  {"objectId":"math-model","kind":"symbolic-expression","studio":"mathematics","title":"Base model","payload":{"expression":"a*x^2"},"variableInputs":["a"],"variableOutputs":[]},
  {"objectId":"graph-view","kind":"graph","studio":"graph-mathematics","title":"Linked graph","payload":{"expression":"a*x^2"},"variableInputs":["a"],"variableOutputs":[],"dependencyObjectIds":["math-model"]}
]</textarea>
                    </details>

                    <details>
                        <summary>Object links</summary>
                        <textarea rows="7" data-scwb-v600-links>[
  {"fromObjectId":"math-model","toObjectId":"graph-view","relation":"feeds","variableNames":["a"]}
]</textarea>
                    </details>

                    <div class="scwb-v600__actions">
                        <button type="button" data-scwb-v600-action="build">Build project</button>
                        <button type="button" data-scwb-v600-action="variables">Resolve variables</button>
                        <button type="button" data-scwb-v600-action="links">Validate links</button>
                        <button type="button" data-scwb-v600-action="save">Save locally</button>
                    </div>
                </aside>

                <div class="scwb-v600__workspace">
                    <div class="scwb-v600__workspace-head"><span>PROJECT GRAPH / TECHNICAL RECORD</span><b data-scwb-v600-kind>READY</b></div>
                    <div class="scwb-v600__graph"><canvas width="1200" height="480" data-scwb-v600-canvas aria-label="Computational project dependency graph"></canvas></div>
                    <div class="scwb-v600__metrics" data-scwb-v600-metrics>
                        <div><span>PROJECT</span><b>—</b></div><div><span>VARIABLES</span><b>—</b></div><div><span>OBJECTS</span><b>—</b></div><div><span>INTEGRITY</span><b>—</b></div>
                    </div>
                    <div class="scwb-v600__handoff">
                        <label><span>Handoff target</span><select data-scwb-v600-target><option value="lab">Lab</option><option value="decision-studio">Decision Studio</option><option value="knowledge-library">Knowledge Library</option><option value="research-librarian">Research Librarian</option><option value="site-intelligence">Site Intelligence</option><option value="workspace">Workspace</option><option value="offline">Offline package</option></select></label>
                        <button type="button" data-scwb-v600-action="history">Build history</button>
                        <button type="button" data-scwb-v600-action="export">Build export</button>
                        <button type="button" data-scwb-v600-action="handoff">Build handoff</button>
                    </div>
                    <pre class="scwb-v600__json" data-scwb-v600-json>{
  "status": "Ready to assemble a unified computational project"
}</pre>
                </div>
            </div>

            <footer class="scwb-v600__boundary"><strong>Unified project orchestration, not autonomous execution.</strong><span>v6.0.1 links inspectable Workbench objects and prepares portable records. It does not automatically execute generated code, publish results, program hardware, certify models, or perform destructive synchronization.</span></footer>
        </section>
        <?php return ob_get_clean();
    }
}
SCWB_V600_Unified_Computational_Workbench::boot();
