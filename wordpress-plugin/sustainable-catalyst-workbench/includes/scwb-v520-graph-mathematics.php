<?php
/** Workbench v5.2.0 — Interactive Graph Mathematics. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V520_Graph_Mathematics {
    const VERSION = '5.2.0';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 61);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V520_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v520.css';
        $js = $base . '/assets/js/sc-workbench-v520.js';
        wp_register_style('scwb-v520', plugins_url('assets/css/sc-workbench-v520.css', SCWB_V520_PLUGIN_FILE), array(), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v520', plugins_url('assets/js/sc-workbench-v520.js', SCWB_V520_PLUGIN_FILE), array(), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_graph_mathematics' => 'graph',
            'sc_workbench_graph_studio' => 'graph',
            'sc_workbench_vector_field' => 'vector',
            'sc_workbench_surface_graph' => 'surface',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, function($atts) use ($panel) {
                    $atts = shortcode_atts(array(
                        'project' => 'default',
                        'display' => 'full',
                        'title' => 'Interactive Graph Mathematics',
                        'backend' => '',
                    ), $atts);
                    return SCWB_V520_Graph_Mathematics::render($atts, $panel);
                });
            }
        }
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

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/graph-mathematics-status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'status'),
            'permission_callback' => '__return_true',
        ));
    }

    public static function status() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-graph-mathematics-interface-status/1.0',
            'version' => self::VERSION,
            'backendConfigured' => '' !== self::backend_url(),
            'capabilities' => array('cartesian','parametric','polar','implicit','contours','live parameters','roots','extrema','intersections','derivative overlays','integral overlays','vector fields','3D surfaces','canonical graph objects'),
            'arbitraryCodeExecutionAuthorized' => false,
            'pythonEvalAuthorized' => false,
            'remoteShellAuthorized' => false,
        ));
    }

    private static function enqueue_assets($backend = '') {
        self::register_assets();
        wp_enqueue_style('scwb-v520');
        wp_enqueue_script('scwb-v520');
        wp_localize_script('scwb-v520', 'SCWBV520Config', array(
            'version' => self::VERSION,
            'backendUrl' => self::backend_url($backend),
        ));
    }

    private static function field($label, $name, $value = '', $type = 'text', $extra = '') {
        ?><label class="scwb-v520__field"><span><?php echo esc_html($label); ?></span><input type="<?php echo esc_attr($type); ?>" data-scwb-v520-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>" <?php echo $extra; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>></label><?php
    }

    public static function render($atts, $panel = 'graph') {
        self::enqueue_assets(isset($atts['backend']) ? $atts['backend'] : '');
        $project = sanitize_key($atts['project']) ?: 'default';
        $instance = 'scwb-v520-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v520" data-scwb-v520 data-panel="<?php echo esc_attr($panel); ?>" data-project="<?php echo esc_attr($project); ?>" data-version="5.2.0">
            <header class="scwb-v520__header">
                <div><p class="scwb-v520__eyebrow">Sustainable Catalyst Workbench · Graph Mathematics v5.2.0</p><h2><?php echo esc_html($atts['title']); ?></h2><p>Linked equations, parameters, analysis, and scientific graph objects on the governed v5.1 symbolic mathematics engine.</p></div>
                <span class="scwb-v520__status" data-scwb-v520-status>Checking graph backend…</span>
            </header>
            <nav class="scwb-v520__tabs" role="tablist" aria-label="Graph mathematics tools">
                <button type="button" role="tab" data-scwb-v520-tab="graph" class="<?php echo 'graph'===$panel?'is-active':''; ?>" aria-selected="<?php echo 'graph'===$panel?'true':'false'; ?>">2D Graph</button>
                <button type="button" role="tab" data-scwb-v520-tab="analysis" aria-selected="false">Analysis</button>
                <button type="button" role="tab" data-scwb-v520-tab="vector" class="<?php echo 'vector'===$panel?'is-active':''; ?>" aria-selected="<?php echo 'vector'===$panel?'true':'false'; ?>">Vector Field</button>
                <button type="button" role="tab" data-scwb-v520-tab="surface" class="<?php echo 'surface'===$panel?'is-active':''; ?>" aria-selected="<?php echo 'surface'===$panel?'true':'false'; ?>">3D Surface</button>
            </nav>
            <div class="scwb-v520__processes" aria-label="Advanced graph process presets">
                <span>ADVANCED PROCESSES</span>
                <button type="button" data-scwb-v520-preset="oscillator">Damped oscillator</button>
                <button type="button" data-scwb-v520-preset="lissajous">Parametric orbit</button>
                <button type="button" data-scwb-v520-preset="rose">Polar symmetry</button>
                <button type="button" data-scwb-v520-preset="implicit">Implicit field</button>
                <button type="button" data-scwb-v520-preset="vortex">Vector vortex</button>
                <button type="button" data-scwb-v520-preset="surface">3D wave surface</button>
            </div>
            <div class="scwb-v520__layout">
                <aside class="scwb-v520__controls">
                    <section data-scwb-v520-view="graph" <?php echo 'graph'===$panel?'':'hidden'; ?>>
                        <label class="scwb-v520__field"><span>Graph mode</span><select data-scwb-v520-field="mode"><option value="cartesian">Cartesian y=f(x)</option><option value="parametric">Parametric x(t), y(t)</option><option value="polar">Polar r(θ)</option><option value="implicit">Implicit / contour</option></select></label>
                        <?php self::field('Expression','expression','a*sin(b*x)'); ?>
                        <div data-scwb-v520-parametric hidden><?php self::field('Y expression','expression_y','a*cos(t)'); ?></div>
                        <div class="scwb-v520__range-grid"><?php self::field('x min','x_min','-10','number','step="any"'); self::field('x max','x_max','10','number','step="any"'); self::field('y min','y_min','-10','number','step="any"'); self::field('y max','y_max','10','number','step="any"'); ?></div>
                        <div class="scwb-v520__parameter"><div><strong>Parameter a</strong><output data-scwb-v520-param-output="a">a = 1</output></div><input type="range" min="-5" max="5" step="0.1" value="1" data-scwb-v520-parameter="a"></div><div class="scwb-v520__parameter"><div><strong>Parameter b</strong><output data-scwb-v520-param-output="b">b = 1</output></div><input type="range" min="0.2" max="5" step="0.1" value="1" data-scwb-v520-parameter="b"></div>
                        <label class="scwb-v520__check"><input type="checkbox" data-scwb-v520-field="derivative"> <span>Derivative overlay</span></label>
                        <div class="scwb-v520__range-grid"><?php self::field('Integral from','integral_lower','','number','step="any"'); self::field('Integral to','integral_upper','','number','step="any"'); ?></div>
                        <button type="button" class="scwb-v520__primary" data-scwb-v520-action="graph">Update graph</button>
                    </section>
                    <section data-scwb-v520-view="analysis" hidden>
                        <h3>Graph analysis</h3><?php self::field('f(x)','analysis_expression','x^3-3*x'); self::field('Compare with g(x)','comparison_expression','0'); ?>
                        <div class="scwb-v520__actions"><button type="button" data-scwb-v520-action="roots">Roots</button><button type="button" data-scwb-v520-action="extrema">Extrema</button><button type="button" data-scwb-v520-action="intersections">Intersections</button></div>
                    </section>
                    <section data-scwb-v520-view="vector" <?php echo 'vector'===$panel?'':'hidden'; ?>>
                        <h3>Vector field</h3><?php self::field('u(x,y)','u_expression','-y'); self::field('v(x,y)','v_expression','x'); ?><button type="button" class="scwb-v520__primary" data-scwb-v520-action="vector">Plot vector field</button>
                    </section>
                    <section data-scwb-v520-view="surface" <?php echo 'surface'===$panel?'':'hidden'; ?>>
                        <h3>3D surface</h3><?php self::field('z=f(x,y)','surface_expression','sin(sqrt(x^2+y^2))'); ?><button type="button" class="scwb-v520__primary" data-scwb-v520-action="surface">Render surface</button>
                    </section>
                    <div class="scwb-v520__readout"><strong>Linked graph object</strong><span data-scwb-v520-message aria-live="polite">Ready.</span><code data-scwb-v520-hash>—</code></div>
                </aside>
                <div class="scwb-v520__stage">
                    <div class="scwb-v520__canvas-wrap"><canvas width="900" height="560" data-scwb-v520-canvas aria-label="Interactive mathematics graph"></canvas></div>
                    <div class="scwb-v520__legend" data-scwb-v520-legend><span>Function</span></div>
                    <div class="scwb-v520__analysis" data-scwb-v520-analysis hidden></div>
                </div>
            </div>
            <footer class="scwb-v520__boundary"><strong>Governed computation</strong><span>Graph expressions use the restricted v5.1 AST/SymPy parser. Arbitrary Python, shell access, automatic publication, and remote command execution remain disabled.</span></footer>
        </section>
        <?php return ob_get_clean();
    }
}
SCWB_V520_Graph_Mathematics::boot();
