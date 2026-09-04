<?php
/** Workbench v5.6.0 — Numerical Methods & Scientific Computing. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V560_Numerical_Scientific_Computing {
    const VERSION = '5.6.0';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 8);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 150);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V560_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v560.css';
        $js = $base . '/assets/js/sc-workbench-v560.js';
        wp_register_style(
            'scwb-v560',
            plugins_url('assets/css/sc-workbench-v560.css', SCWB_V560_PLUGIN_FILE),
            array(),
            file_exists($css) ? (string) filemtime($css) : self::VERSION
        );
        wp_register_script(
            'scwb-v560',
            plugins_url('assets/js/sc-workbench-v560.js', SCWB_V560_PLUGIN_FILE),
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
        wp_enqueue_style('scwb-v560');
        wp_enqueue_script('scwb-v560');
        wp_localize_script('scwb-v560', 'SCWBV560Config', array(
            'version' => self::VERSION,
            'backendUrl' => self::backend_url($backend),
            'routes' => array(
                'status' => '/v560/status',
                'root' => '/v560/root',
                'integrate' => '/v560/integrate',
                'differentiate' => '/v560/differentiate',
                'interpolate' => '/v560/interpolate',
                'ode' => '/v560/ode',
                'linearAlgebra' => '/v560/linear-algebra',
                'optimize' => '/v560/optimize',
            ),
        ));
    }

    public static function register_shortcodes() {
        foreach (array('sc_workbench_numerical_methods', 'sc_workbench_scientific_computing', 'sc_workbench_numerical_studio', 'sc_workbench_numerical') as $tag) {
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
        register_rest_route('scwb/v1', '/v560-interface-status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'status'),
            'permission_callback' => '__return_true',
        ));
    }

    public static function status() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-numerical-methods-interface-status/1.0',
            'version' => self::VERSION,
            'backendConfigured' => '' !== self::backend_url(),
            'backendVersionRequired' => '5.6.0',
            'rootFinding' => true,
            'numericalIntegration' => true,
            'finiteDifferenceDerivatives' => true,
            'interpolation' => true,
            'odeSolvers' => true,
            'linearAlgebra' => true,
            'boundedOptimization' => true,
            'reproducibleNumericalObjects' => true,
        ));
    }

    private static function promote_public_markup($html, $surface) {
        $html = str_replace('data-version="5.5.0"', 'data-version="5.6.0"', $html);
        $html = str_replace('SUSTAINABLE CATALYST WORKBENCH · v5.5.0', 'SUSTAINABLE CATALYST WORKBENCH · v5.6.0', $html);
        $html = str_replace('v5.5.0 ·', 'v5.6.0 ·', $html);
        if ('homepage' === $surface) {
            $html = str_replace('scwb-v550-home', 'scwb-v550-home scwb-v560-home', $html);
        } else {
            $html = str_replace('scwb-v550-experience', 'scwb-v550-experience scwb-v560-experience', $html);
            $html = str_replace('<span><i></i> GEOMETRY</span>', '<span><i></i> GEOMETRY</span><span><i></i> NUMERICAL</span>', $html);
            $html = str_replace('<a href="?studio=visualization"><b>Data &amp; Visualization</b>', '<a href="?studio=numerical"><b>Numerical Computing</b><span>roots · integration · ODEs · linear algebra · optimization</span></a><a href="?studio=visualization"><b>Data &amp; Visualization</b>', $html);
        }
        return $html;
    }

    public static function render_homepage($atts = array()) {
        if (!class_exists('SCWB_V550_Dynamic_Geometry')) {
            return '<div role="alert">Workbench homepage showcase requires the complete v5.6.0 plugin.</div>';
        }
        return self::promote_public_markup(SCWB_V550_Dynamic_Geometry::render_homepage($atts), 'homepage');
    }

    public static function render_experience($atts = array()) {
        if (!class_exists('SCWB_V550_Dynamic_Geometry')) {
            return '<div role="alert">Workbench experience requires the complete v5.6.0 plugin.</div>';
        }
        return self::promote_public_markup(SCWB_V550_Dynamic_Geometry::render_experience($atts), 'experience');
    }

    public static function shortcode($atts = array()) {
        $atts = shortcode_atts(array(
            'project' => 'default',
            'display' => 'full',
            'title' => 'Numerical Methods & Scientific Computing',
            'backend' => '',
        ), $atts);
        return self::render($atts);
    }

    public static function render($atts = array()) {
        self::enqueue_assets(isset($atts['backend']) ? $atts['backend'] : '');
        $project = sanitize_key(isset($atts['project']) ? $atts['project'] : 'default') ?: 'default';
        $instance = 'scwb-v560-' . wp_generate_uuid4();
        ob_start();
        ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v560" data-scwb-v560 data-project="<?php echo esc_attr($project); ?>" data-version="5.6.0">
            <header class="scwb-v560__header">
                <div>
                    <p class="scwb-v560__eyebrow">Sustainable Catalyst Workbench · Numerical Methods &amp; Scientific Computing · v5.6.0</p>
                    <h2><?php echo esc_html(isset($atts['title']) ? $atts['title'] : 'Numerical Methods & Scientific Computing'); ?></h2>
                    <p>Move from symbolic mathematics into bounded numerical experiments with inspectable methods, tolerances, diagnostics, and reproducible result objects.</p>
                </div>
                <span class="scwb-v560__status" data-scwb-v560-status>Checking numerical backend…</span>
            </header>

            <div class="scwb-v560__tabs" role="tablist" aria-label="Numerical computing methods">
                <button type="button" class="is-active" data-scwb-v560-mode="root">ROOTS</button>
                <button type="button" data-scwb-v560-mode="integrate">INTEGRATE</button>
                <button type="button" data-scwb-v560-mode="differentiate">DERIVATIVE</button>
                <button type="button" data-scwb-v560-mode="interpolate">INTERPOLATE</button>
                <button type="button" data-scwb-v560-mode="ode">ODE</button>
                <button type="button" data-scwb-v560-mode="linear">LINEAR ALGEBRA</button>
                <button type="button" data-scwb-v560-mode="optimize">OPTIMIZE</button>
            </div>

            <div class="scwb-v560__layout">
                <aside class="scwb-v560__controls">
                    <section class="scwb-v560__mode-panel is-active" data-scwb-v560-panel="root">
                        <label><span>Expression</span><input data-scwb-v560-root-expression value="x^3 - x - 2"></label>
                        <div class="scwb-v560__row"><label><span>Min</span><input type="number" step="any" data-scwb-v560-root-min value="1"></label><label><span>Max</span><input type="number" step="any" data-scwb-v560-root-max value="2"></label></div>
                        <label><span>Method</span><select data-scwb-v560-root-method><option value="brentq">Brent</option><option value="bisection">Bisection</option><option value="newton">Newton</option><option value="secant">Secant</option></select></label>
                        <button type="button" class="scwb-v560__run" data-scwb-v560-run="root">Find root</button>
                    </section>

                    <section class="scwb-v560__mode-panel" data-scwb-v560-panel="integrate">
                        <label><span>Expression</span><input data-scwb-v560-integrate-expression value="sin(x)"></label>
                        <div class="scwb-v560__row"><label><span>Lower</span><input type="number" step="any" data-scwb-v560-integrate-lower value="0"></label><label><span>Upper</span><input type="number" step="any" data-scwb-v560-integrate-upper value="3.141592653589793"></label></div>
                        <label><span>Method</span><select data-scwb-v560-integrate-method><option value="adaptive">Adaptive quadrature</option><option value="simpson">Simpson</option><option value="trapezoid">Trapezoid</option></select></label>
                        <button type="button" class="scwb-v560__run" data-scwb-v560-run="integrate">Integrate</button>
                    </section>

                    <section class="scwb-v560__mode-panel" data-scwb-v560-panel="differentiate">
                        <label><span>Expression</span><input data-scwb-v560-differentiate-expression value="sin(x) * exp(-x/4)"></label>
                        <div class="scwb-v560__row"><label><span>x</span><input type="number" step="any" data-scwb-v560-differentiate-x value="1"></label><label><span>Order</span><select data-scwb-v560-differentiate-order><option value="1">First</option><option value="2">Second</option></select></label></div>
                        <button type="button" class="scwb-v560__run" data-scwb-v560-run="differentiate">Differentiate</button>
                    </section>

                    <section class="scwb-v560__mode-panel" data-scwb-v560-panel="interpolate">
                        <label><span>x values</span><input data-scwb-v560-interpolate-x value="0,1,2,3,4"></label>
                        <label><span>y values</span><input data-scwb-v560-interpolate-y value="0,1,0,1,0"></label>
                        <label><span>Method</span><select data-scwb-v560-interpolate-method><option value="pchip">PCHIP</option><option value="cubic-spline">Cubic spline</option><option value="linear">Linear</option></select></label>
                        <button type="button" class="scwb-v560__run" data-scwb-v560-run="interpolate">Interpolate</button>
                    </section>

                    <section class="scwb-v560__mode-panel" data-scwb-v560-panel="ode">
                        <label><span>dy/dt</span><input data-scwb-v560-ode-expression value="-0.35*y"></label>
                        <div class="scwb-v560__row"><label><span>y(0)</span><input type="number" step="any" data-scwb-v560-ode-y0 value="1"></label><label><span>t max</span><input type="number" step="any" data-scwb-v560-ode-tmax value="12"></label></div>
                        <label><span>Method</span><select data-scwb-v560-ode-method><option>RK45</option><option>DOP853</option><option>Radau</option><option>BDF</option></select></label>
                        <button type="button" class="scwb-v560__run" data-scwb-v560-run="ode">Solve ODE</button>
                    </section>

                    <section class="scwb-v560__mode-panel" data-scwb-v560-panel="linear">
                        <label><span>Matrix A</span><textarea rows="4" data-scwb-v560-linear-matrix>3,2\n1,2</textarea></label>
                        <label><span>Vector b</span><input data-scwb-v560-linear-vector value="5,5"></label>
                        <label><span>Operation</span><select data-scwb-v560-linear-operation><option value="solve">Solve Ax=b</option><option value="eigen">Eigen analysis</option><option value="svd">SVD</option><option value="least-squares">Least squares</option><option value="inverse">Inverse</option></select></label>
                        <button type="button" class="scwb-v560__run" data-scwb-v560-run="linear">Compute</button>
                    </section>

                    <section class="scwb-v560__mode-panel" data-scwb-v560-panel="optimize">
                        <label><span>Objective</span><input data-scwb-v560-optimize-expression value="(x-2)^2 + (y+1)^2"></label>
                        <label><span>Variables</span><input data-scwb-v560-optimize-variables value="x,y"></label>
                        <label><span>Initial</span><input data-scwb-v560-optimize-initial value="0,0"></label>
                        <label><span>Bounds</span><input data-scwb-v560-optimize-bounds value="-5:5,-5:5"></label>
                        <label><span>Goal</span><select data-scwb-v560-optimize-goal><option value="minimize">Minimize</option><option value="maximize">Maximize</option></select></label>
                        <button type="button" class="scwb-v560__run" data-scwb-v560-run="optimize">Optimize</button>
                    </section>
                </aside>

                <main class="scwb-v560__workspace">
                    <div class="scwb-v560__workspace-head"><span>SCIENTIFIC COMPUTING OUTPUT</span><b data-scwb-v560-result-kind>ready</b></div>
                    <div class="scwb-v560__visual"><canvas width="1000" height="460" data-scwb-v560-canvas aria-label="Numerical result visualization"></canvas></div>
                    <div class="scwb-v560__metrics" data-scwb-v560-metrics><div><span>METHOD</span><b>—</b></div><div><span>RESULT</span><b>—</b></div><div><span>DIAGNOSTIC</span><b>—</b></div></div>
                    <pre class="scwb-v560__json" data-scwb-v560-json aria-live="polite">Select a method and run a bounded numerical calculation.</pre>
                </main>
            </div>

            <footer class="scwb-v560__boundary">
                <strong>Governed numerical computation.</strong>
                <span>Expressions use the restricted mathematics parser. Methods expose tolerances and diagnostics. No arbitrary Python, shell, uploaded callable, or unattended device execution is authorized.</span>
            </footer>
        </section>
        <?php
        return ob_get_clean();
    }
}

SCWB_V560_Numerical_Scientific_Computing::boot();
