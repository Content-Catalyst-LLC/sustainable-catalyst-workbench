<?php
/** Workbench v5.5.0 — Dynamic Geometry & Interactive Mathematics. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V550_Dynamic_Geometry {
    const VERSION = '5.5.0';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 8);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 145);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V550_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v550.css';
        $js = $base . '/assets/js/sc-workbench-v550.js';
        wp_register_style(
            'scwb-v550',
            plugins_url('assets/css/sc-workbench-v550.css', SCWB_V550_PLUGIN_FILE),
            array(),
            file_exists($css) ? (string) filemtime($css) : self::VERSION
        );
        wp_register_script(
            'scwb-v550',
            plugins_url('assets/js/sc-workbench-v550.js', SCWB_V550_PLUGIN_FILE),
            array(),
            file_exists($js) ? (string) filemtime($js) : self::VERSION,
            true
        );
    }

    public static function backend_url($override = '') {
        if (class_exists('SCWB_V531_Settings_Backend_Repair')) {
            return SCWB_V531_Settings_Backend_Repair::backend_url($override);
        }
        $candidate = trim((string) $override);
        if (!$candidate && defined('SCWB_WORKBENCH_BACKEND_URL')) {
            $candidate = trim((string) SCWB_WORKBENCH_BACKEND_URL);
        }
        if (function_exists('apply_filters')) {
            $candidate = (string) apply_filters('scwb_workbench_backend_url', $candidate);
        }
        return rtrim($candidate, '/');
    }

    private static function enqueue_assets($backend = '') {
        self::register_assets();
        wp_enqueue_style('scwb-v550');
        wp_enqueue_script('scwb-v550');
        wp_localize_script('scwb-v550', 'SCWBV550Config', array(
            'version' => self::VERSION,
            'backendUrl' => self::backend_url($backend),
            'maxPoints' => 64,
            'maxObjects' => 96,
            'maxConstraints' => 96,
        ));
    }

    public static function register_shortcodes() {
        foreach (array('sc_workbench_dynamic_geometry', 'sc_workbench_geometry', 'sc_workbench_geometry_studio') as $tag) {
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
        register_rest_route('scwb/v1', '/v550-interface-status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'status'),
            'permission_callback' => '__return_true',
        ));
    }

    public static function status() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-dynamic-geometry-interface-status/1.0',
            'version' => self::VERSION,
            'backendConfigured' => '' !== self::backend_url(),
            'backendVersionRequired' => '5.5.0',
            'draggablePoints' => true,
            'constraints' => true,
            'measurements' => true,
            'affineTransforms' => true,
            'expressionLinkedLoci' => true,
            'algebraGeometryLinkage' => true,
            'reproducibleGeometryObjects' => true,
        ));
    }

    private static function promote_public_markup($html, $surface) {
        $html = str_replace('data-version="5.4.0"', 'data-version="5.5.0"', $html);
        $html = str_replace('SUSTAINABLE CATALYST WORKBENCH · v5.4.0', 'SUSTAINABLE CATALYST WORKBENCH · v5.5.0', $html);
        $html = str_replace('v5.4.0 ·', 'v5.5.0 ·', $html);
        if ('homepage' === $surface) {
            $html = str_replace('scwb-v540-home', 'scwb-v540-home scwb-v550-home', $html);
        } else {
            $html = str_replace('scwb-v540-experience', 'scwb-v540-experience scwb-v550-experience', $html);
            $html = str_replace('<span><i></i> PROTOTYPING</span>', '<span><i></i> PROTOTYPING</span><span><i></i> GEOMETRY</span>', $html);
            $html = str_replace('<b>ƒ(x)</b><i>→</i><b>GRAPH</b><i>→</i><b>Hz</b>', '<b>ƒ(x)</b><i>→</i><b>GRAPH</b><i>→</i><b>GEOMETRY</b><i>→</i><b>Hz</b>', $html);
            $html = str_replace('<a href="?studio=visualization"><b>Data &amp; Visualization</b>', '<a href="?studio=geometry"><b>Dynamic Geometry</b><span>points · constraints · transformations · loci</span></a><a href="?studio=visualization"><b>Data &amp; Visualization</b>', $html);
        }
        return $html;
    }

    public static function render_homepage($atts = array()) {
        if (!class_exists('SCWB_V540_Advanced_Graph_Mathematics')) {
            return '<div role="alert">Workbench homepage showcase requires the complete v5.5.0 plugin.</div>';
        }
        return self::promote_public_markup(SCWB_V540_Advanced_Graph_Mathematics::render_homepage($atts), 'homepage');
    }

    public static function render_experience($atts = array()) {
        if (!class_exists('SCWB_V540_Advanced_Graph_Mathematics')) {
            return '<div role="alert">Workbench experience requires the complete v5.5.0 plugin.</div>';
        }
        return self::promote_public_markup(SCWB_V540_Advanced_Graph_Mathematics::render_experience($atts), 'experience');
    }

    public static function shortcode($atts = array()) {
        $atts = shortcode_atts(array(
            'project' => 'default',
            'display' => 'full',
            'title' => 'Dynamic Geometry & Interactive Mathematics',
            'backend' => '',
        ), $atts);
        return self::render($atts);
    }

    public static function render($atts = array()) {
        self::enqueue_assets(isset($atts['backend']) ? $atts['backend'] : '');
        $project = sanitize_key(isset($atts['project']) ? $atts['project'] : 'default') ?: 'default';
        $instance = 'scwb-v550-' . wp_generate_uuid4();
        ob_start();
        ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v550" data-scwb-v550 data-project="<?php echo esc_attr($project); ?>" data-version="5.5.0">
            <header class="scwb-v550__header">
                <div>
                    <p class="scwb-v550__eyebrow">Sustainable Catalyst Workbench · Dynamic Geometry & Interactive Mathematics · v5.5.0</p>
                    <h2><?php echo esc_html(isset($atts['title']) ? $atts['title'] : 'Dynamic Geometry & Interactive Mathematics'); ?></h2>
                    <p>Move mathematical objects directly. Geometry, equations, measurements, constraints, transformations, and loci remain linked as the construction changes.</p>
                </div>
                <span class="scwb-v550__status" data-scwb-v550-status>Checking geometry backend…</span>
            </header>

            <div class="scwb-v550__presets" aria-label="Dynamic geometry examples">
                <span>EXAMPLES</span>
                <button type="button" data-scwb-v550-preset="triangle">Dynamic triangle</button>
                <button type="button" data-scwb-v550-preset="circle">Circle + constraint</button>
                <button type="button" data-scwb-v550-preset="transform">Matrix transform</button>
                <button type="button" data-scwb-v550-preset="conic">Conic geometry</button>
                <button type="button" data-scwb-v550-preset="locus">Expression locus</button>
            </div>

            <div class="scwb-v550__toolbar" aria-label="Geometry construction tools">
                <button type="button" class="is-active" data-scwb-v550-tool="move"><b>↖</b><span>Move</span></button>
                <button type="button" data-scwb-v550-tool="point"><b>•</b><span>Point</span></button>
                <button type="button" data-scwb-v550-tool="segment"><b>╱</b><span>Segment</span></button>
                <button type="button" data-scwb-v550-tool="circle"><b>○</b><span>Circle</span></button>
                <button type="button" data-scwb-v550-tool="polygon"><b>△</b><span>Polygon</span></button>
                <button type="button" data-scwb-v550-action="undo"><b>↶</b><span>Undo</span></button>
                <button type="button" data-scwb-v550-action="reset"><b>↺</b><span>Reset</span></button>
                <button type="button" data-scwb-v550-action="fullscreen"><b>⛶</b><span>Fullscreen</span></button>
            </div>

            <div class="scwb-v550__layout">
                <aside class="scwb-v550__left">
                    <section class="scwb-v550__panel">
                        <div class="scwb-v550__panel-head"><span>CONSTRUCTION</span><b data-scwb-v550-counts>0 points · 0 objects</b></div>
                        <div class="scwb-v550__object-list" data-scwb-v550-object-list></div>
                    </section>

                    <section class="scwb-v550__panel">
                        <div class="scwb-v550__panel-head"><span>CONSTRAINTS</span><b>bounded solver</b></div>
                        <label class="scwb-v550__field"><span>Constraint</span>
                            <select data-scwb-v550-constraint-type>
                                <option value="horizontal">Horizontal</option>
                                <option value="vertical">Vertical</option>
                                <option value="distance">Fixed distance</option>
                                <option value="midpoint">Midpoint</option>
                                <option value="coincident">Coincident</option>
                                <option value="point-on-circle">Point on circle</option>
                            </select>
                        </label>
                        <label class="scwb-v550__field"><span>Point IDs</span><input type="text" value="A,B" placeholder="A,B or M,A,B" data-scwb-v550-constraint-points></label>
                        <label class="scwb-v550__field"><span>Value</span><input type="number" step="any" value="4" data-scwb-v550-constraint-value></label>
                        <button type="button" class="scwb-v550__secondary" data-scwb-v550-add-constraint>Add constraint</button>
                        <div class="scwb-v550__constraint-list" data-scwb-v550-constraint-list></div>
                    </section>

                    <section class="scwb-v550__panel">
                        <div class="scwb-v550__panel-head"><span>TRANSFORM</span><b>affine matrix</b></div>
                        <div class="scwb-v550__transform-grid">
                            <button type="button" data-scwb-v550-transform="rotate30">Rotate +30°</button>
                            <button type="button" data-scwb-v550-transform="reflectX">Reflect x</button>
                            <button type="button" data-scwb-v550-transform="reflectY">Reflect y</button>
                            <button type="button" data-scwb-v550-transform="scale125">Scale 1.25×</button>
                        </div>
                    </section>
                </aside>

                <main class="scwb-v550__stage">
                    <div class="scwb-v550__stage-head">
                        <div><span>DYNAMIC PLANE</span><b data-scwb-v550-stage-readout>x −10…10 · y −7…7</b></div>
                        <div class="scwb-v550__mode" data-scwb-v550-mode>MOVE · drag points</div>
                    </div>
                    <div class="scwb-v550__canvas-wrap" data-scwb-v550-canvas-wrap>
                        <canvas width="1280" height="820" data-scwb-v550-canvas aria-label="Interactive dynamic geometry plane"></canvas>
                        <div class="scwb-v550__cursor" data-scwb-v550-cursor hidden></div>
                    </div>
                    <div class="scwb-v550__message" data-scwb-v550-message>Ready.</div>
                    <div class="scwb-v550__object-hash"><span>GEOMETRY OBJECT</span><code data-scwb-v550-hash>—</code></div>
                </main>

                <aside class="scwb-v550__right">
                    <section class="scwb-v550__panel">
                        <div class="scwb-v550__panel-head"><span>ALGEBRA ↔ GEOMETRY</span><b>live</b></div>
                        <div class="scwb-v550__algebra" data-scwb-v550-algebra><p>Select or move an object to inspect its equation.</p></div>
                    </section>

                    <section class="scwb-v550__panel">
                        <div class="scwb-v550__panel-head"><span>MEASUREMENTS</span><b>live</b></div>
                        <div class="scwb-v550__measurements" data-scwb-v550-measurements></div>
                    </section>

                    <section class="scwb-v550__panel scwb-v550__locus-panel">
                        <div class="scwb-v550__panel-head"><span>EXPRESSION LOCUS</span><b>restricted CAS</b></div>
                        <label class="scwb-v550__field"><span>x(t)</span><input type="text" value="3*cos(t)" data-scwb-v550-locus-x></label>
                        <label class="scwb-v550__field"><span>y(t)</span><input type="text" value="2*sin(t)" data-scwb-v550-locus-y></label>
                        <button type="button" class="scwb-v550__secondary" data-scwb-v550-locus-generate>Generate locus</button>
                    </section>

                    <section class="scwb-v550__panel">
                        <div class="scwb-v550__panel-head"><span>CONSTRUCTION HISTORY</span><b data-scwb-v550-history-count>0 steps</b></div>
                        <ol class="scwb-v550__history" data-scwb-v550-history></ol>
                        <button type="button" class="scwb-v550__secondary" data-scwb-v550-copy>Copy geometry JSON</button>
                    </section>
                </aside>
            </div>

            <footer class="scwb-v550__boundary">
                <strong>Governed interactive mathematics</strong>
                <span>Geometry is solved through bounded deterministic construction rules. Expression-linked loci continue to use the restricted v5.1 AST → SymPy parser. No Python eval/exec, remote shell, or arbitrary code execution is authorized.</span>
            </footer>
        </section>
        <?php
        return ob_get_clean();
    }
}
SCWB_V550_Dynamic_Geometry::boot();
