<?php
/** Workbench v5.4.0 — Advanced Graph Mathematics II. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V540_Advanced_Graph_Mathematics {
    const VERSION = '5.4.0';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 8);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 140);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V540_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v540.css';
        $js = $base . '/assets/js/sc-workbench-v540.js';
        wp_register_style(
            'scwb-v540',
            plugins_url('assets/css/sc-workbench-v540.css', SCWB_V540_PLUGIN_FILE),
            array(),
            file_exists($css) ? (string) filemtime($css) : self::VERSION
        );
        wp_register_script(
            'scwb-v540',
            plugins_url('assets/js/sc-workbench-v540.js', SCWB_V540_PLUGIN_FILE),
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
        wp_enqueue_style('scwb-v540');
        wp_enqueue_script('scwb-v540');
        wp_localize_script('scwb-v540', 'SCWBV540Config', array(
            'version' => self::VERSION,
            'backendUrl' => self::backend_url($backend),
            'maxSeries' => 8,
        ));
    }

    public static function register_shortcodes() {
        foreach (array('sc_workbench_graph_mathematics', 'sc_workbench_graph_studio') as $tag) {
            if (shortcode_exists($tag)) { remove_shortcode($tag); }
            add_shortcode($tag, array(__CLASS__, 'shortcode'));
        }
        if (shortcode_exists('sc_workbench_advanced_graph_mathematics')) {
            remove_shortcode('sc_workbench_advanced_graph_mathematics');
        }
        add_shortcode('sc_workbench_advanced_graph_mathematics', array(__CLASS__, 'shortcode'));

        // Keep the compact homepage and redesigned Workbench experience, but promote
        // their public release identity and mount the v5.4 graph studio through the
        // overridden graph shortcode above.
        foreach (array('sc_workbench_homepage_instrument', 'sc_workbench_experience', 'sc_workbench_experience_page') as $tag) {
            if (shortcode_exists($tag)) { remove_shortcode($tag); }
        }
        add_shortcode('sc_workbench_homepage_instrument', array(__CLASS__, 'render_homepage'));
        add_shortcode('sc_workbench_experience', array(__CLASS__, 'render_experience'));
        add_shortcode('sc_workbench_experience_page', array(__CLASS__, 'render_experience'));
    }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/v540-interface-status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'status'),
            'permission_callback' => '__return_true',
        ));
    }

    public static function status() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-advanced-graph-interface-status/1.0',
            'version' => self::VERSION,
            'backendConfigured' => '' !== self::backend_url(),
            'backendVersionRequired' => '5.4.0',
            'multiExpressionStack' => true,
            'domainRestrictions' => true,
            'piecewiseByDomain' => true,
            'inequalityRegions' => true,
            'tangentNormalConstruction' => true,
            'asymptoteDiscontinuityAnalysis' => true,
            'valueTable' => true,
            'zoomPanTrace' => true,
        ));
    }

    private static function promote_public_assets() {
        $backend = self::backend_url();
        if (function_exists('wp_localize_script')) {
            wp_localize_script('scwb-v532', 'SCWBV532Config', array(
                'version' => self::VERSION,
                'backendUrl' => $backend,
                'workbenchUrl' => function_exists('home_url') ? home_url('/workbench/') : '/workbench/',
                'viewportScrollGuard' => true,
            ));
        }
    }

    private static function promote_markup($html, $surface) {
        $html = str_replace('data-version="5.3.3"', 'data-version="5.4.0"', $html);
        $html = str_replace('data-version="5.3.2"', 'data-version="5.4.0"', $html);
        $html = str_replace('SUSTAINABLE CATALYST WORKBENCH · v5.3.3', 'SUSTAINABLE CATALYST WORKBENCH · v5.4.0', $html);
        $html = str_replace('SUSTAINABLE CATALYST WORKBENCH · v5.3.2', 'SUSTAINABLE CATALYST WORKBENCH · v5.4.0', $html);
        $html = str_replace('v5.3.3 ·', 'v5.4.0 ·', $html);
        if ('homepage' === $surface) {
            $html = str_replace('scwb-v533-home', 'scwb-v533-home scwb-v540-home', $html);
        } else {
            $html = str_replace('scwb-v533-experience', 'scwb-v533-experience scwb-v540-experience', $html);
        }
        return $html;
    }

    public static function render_homepage($atts = array()) {
        if (!class_exists('SCWB_V533_Integration_Hardening')) {
            return '<div role="alert">Workbench homepage showcase requires the complete v5.4.0 plugin.</div>';
        }
        $html = SCWB_V533_Integration_Hardening::render_homepage($atts);
        self::promote_public_assets();
        return self::promote_markup($html, 'homepage');
    }

    public static function render_experience($atts = array()) {
        if (!class_exists('SCWB_V533_Integration_Hardening')) {
            return '<div role="alert">Workbench experience requires the complete v5.4.0 plugin.</div>';
        }
        $html = SCWB_V533_Integration_Hardening::render_experience($atts);
        self::promote_public_assets();
        return self::promote_markup($html, 'experience');
    }

    public static function shortcode($atts = array()) {
        $atts = shortcode_atts(array(
            'project' => 'default',
            'display' => 'full',
            'title' => 'Advanced Graph Mathematics',
            'backend' => '',
        ), $atts);
        return self::render($atts);
    }

    private static function field($label, $name, $value, $type = 'number', $extra = '') {
        ?>
        <label class="scwb-v540__field">
            <span><?php echo esc_html($label); ?></span>
            <input type="<?php echo esc_attr($type); ?>" data-scwb-v540-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>" <?php echo $extra; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>>
        </label>
        <?php
    }

    public static function render($atts = array()) {
        self::enqueue_assets(isset($atts['backend']) ? $atts['backend'] : '');
        $project = sanitize_key(isset($atts['project']) ? $atts['project'] : 'default') ?: 'default';
        $instance = 'scwb-v540-' . wp_generate_uuid4();
        ob_start();
        ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v540" data-scwb-v540 data-project="<?php echo esc_attr($project); ?>" data-version="5.4.0">
            <header class="scwb-v540__header">
                <div>
                    <p class="scwb-v540__eyebrow">Sustainable Catalyst Workbench · Advanced Graph Mathematics II · v5.4.0</p>
                    <h2><?php echo esc_html(isset($atts['title']) ? $atts['title'] : 'Advanced Graph Mathematics'); ?></h2>
                    <p>Stack functions, restrict domains, build piecewise views, inspect roots and intersections, construct tangent and normal lines, expose asymptotes and discontinuities, and move between graph and value-table representations.</p>
                </div>
                <span class="scwb-v540__status" data-scwb-v540-status>Checking advanced graph backend…</span>
            </header>

            <div class="scwb-v540__processes" aria-label="Advanced graph examples">
                <span>EXAMPLES</span>
                <button type="button" data-scwb-v540-preset="calculus">Calculus analysis</button>
                <button type="button" data-scwb-v540-preset="piecewise">Piecewise domains</button>
                <button type="button" data-scwb-v540-preset="rational">Asymptotes</button>
                <button type="button" data-scwb-v540-preset="inequality">Inequality region</button>
                <button type="button" data-scwb-v540-preset="parameter">Live parameter</button>
            </div>

            <div class="scwb-v540__layout">
                <aside class="scwb-v540__controls">
                    <div class="scwb-v540__control-head">
                        <div><span>EXPRESSION STACK</span><strong>Up to 8 linked functions</strong></div>
                        <button type="button" data-scwb-v540-add-series>+ Add</button>
                    </div>

                    <div class="scwb-v540__series-stack" data-scwb-v540-series-stack>
                        <div class="scwb-v540__series-row" data-scwb-v540-series-row>
                            <label class="scwb-v540__series-visible"><input type="checkbox" checked data-scwb-v540-series-visible><i></i></label>
                            <input type="text" value="x^3-3*x" aria-label="Function expression" data-scwb-v540-series-expression>
                            <input type="text" value="f" aria-label="Function label" data-scwb-v540-series-label>
                            <select aria-label="Derivative overlay" data-scwb-v540-series-derivative><option value="0">f</option><option value="1">f′</option><option value="2">f″</option></select>
                            <button type="button" aria-label="Remove expression" data-scwb-v540-remove-series>×</button>
                            <div class="scwb-v540__domain"><span>domain</span><input type="number" step="any" placeholder="min" data-scwb-v540-domain-min><b>≤ x ≤</b><input type="number" step="any" placeholder="max" data-scwb-v540-domain-max></div>
                        </div>
                        <div class="scwb-v540__series-row" data-scwb-v540-series-row>
                            <label class="scwb-v540__series-visible"><input type="checkbox" checked data-scwb-v540-series-visible><i></i></label>
                            <input type="text" value="0.5*x+1" aria-label="Function expression" data-scwb-v540-series-expression>
                            <input type="text" value="g" aria-label="Function label" data-scwb-v540-series-label>
                            <select aria-label="Derivative overlay" data-scwb-v540-series-derivative><option value="0">g</option><option value="1">g′</option><option value="2">g″</option></select>
                            <button type="button" aria-label="Remove expression" data-scwb-v540-remove-series>×</button>
                            <div class="scwb-v540__domain"><span>domain</span><input type="number" step="any" placeholder="min" data-scwb-v540-domain-min><b>≤ x ≤</b><input type="number" step="any" placeholder="max" data-scwb-v540-domain-max></div>
                        </div>
                    </div>
                    <p class="scwb-v540__hint">Piecewise functions can be built by stacking expressions with different domain restrictions.</p>

                    <details open class="scwb-v540__control-group">
                        <summary>Analysis</summary>
                        <div class="scwb-v540__checks">
                            <label><input type="checkbox" checked value="roots" data-scwb-v540-analysis> Roots</label>
                            <label><input type="checkbox" checked value="extrema" data-scwb-v540-analysis> Extrema</label>
                            <label><input type="checkbox" checked value="intersections" data-scwb-v540-analysis> Intersections</label>
                            <label><input type="checkbox" value="asymptotes" data-scwb-v540-analysis> Asymptotes</label>
                            <label><input type="checkbox" value="discontinuities" data-scwb-v540-analysis> Discontinuities</label>
                        </div>
                        <div class="scwb-v540__two">
                            <?php self::field('Tangent at x', 'tangent_at', '', 'number', 'step="any" placeholder="optional"'); ?>
                            <label class="scwb-v540__toggle"><span>Normal line</span><input type="checkbox" data-scwb-v540-normal></label>
                        </div>
                    </details>

                    <details class="scwb-v540__control-group">
                        <summary>Inequality / region</summary>
                        <label class="scwb-v540__field"><span>Expression</span><input type="text" value="" placeholder="e.g. x^2-4" data-scwb-v540-region-expression></label>
                        <div class="scwb-v540__region-row">
                            <select data-scwb-v540-region-comparator aria-label="Inequality comparator"><option value="lte">≤</option><option value="lt">&lt;</option><option value="gte">≥</option><option value="gt">&gt;</option></select>
                            <input type="number" step="any" value="0" data-scwb-v540-region-level aria-label="Inequality level">
                        </div>
                    </details>

                    <details class="scwb-v540__control-group">
                        <summary>Parameters</summary>
                        <div class="scwb-v540__parameter"><div><b>a</b><output data-scwb-v540-param-output="a">1.00</output></div><input type="range" min="-5" max="5" step="0.05" value="1" data-scwb-v540-parameter="a"></div>
                        <div class="scwb-v540__parameter"><div><b>b</b><output data-scwb-v540-param-output="b">1.00</output></div><input type="range" min="-5" max="5" step="0.05" value="1" data-scwb-v540-parameter="b"></div>
                        <div class="scwb-v540__parameter"><div><b>c</b><output data-scwb-v540-param-output="c">0.00</output></div><input type="range" min="-5" max="5" step="0.05" value="0" data-scwb-v540-parameter="c"></div>
                    </details>

                    <details class="scwb-v540__control-group">
                        <summary>Viewport</summary>
                        <div class="scwb-v540__viewport">
                            <?php self::field('x min', 'x_min', '-10', 'number', 'step="any"'); ?>
                            <?php self::field('x max', 'x_max', '10', 'number', 'step="any"'); ?>
                            <?php self::field('y min', 'y_min', '-10', 'number', 'step="any"'); ?>
                            <?php self::field('y max', 'y_max', '10', 'number', 'step="any"'); ?>
                        </div>
                    </details>

                    <button type="button" class="scwb-v540__primary" data-scwb-v540-update>Update advanced graph</button>
                    <div class="scwb-v540__message" data-scwb-v540-message>Ready.</div>
                </aside>

                <div class="scwb-v540__stage">
                    <div class="scwb-v540__stage-tools">
                        <div><span>ADVANCED CARTESIAN · MULTI-SERIES</span><b data-scwb-v540-viewport-readout>x −10…10 · y −10…10</b></div>
                        <nav aria-label="Graph stage controls">
                            <button type="button" data-scwb-v540-stage-action="table">Value table</button>
                            <button type="button" data-scwb-v540-stage-action="reset">Reset view</button>
                            <button type="button" data-scwb-v540-stage-action="fullscreen">Fullscreen</button>
                        </nav>
                    </div>
                    <div class="scwb-v540__canvas-wrap" data-scwb-v540-canvas-wrap>
                        <canvas width="1200" height="720" data-scwb-v540-canvas aria-label="Advanced mathematical graph"></canvas>
                        <div class="scwb-v540__trace" data-scwb-v540-trace hidden></div>
                    </div>
                    <div class="scwb-v540__legend" data-scwb-v540-legend></div>
                    <div class="scwb-v540__analysis" data-scwb-v540-analysis-output></div>
                    <div class="scwb-v540__table" data-scwb-v540-table hidden></div>
                    <div class="scwb-v540__object"><span>GRAPH OBJECT</span><code data-scwb-v540-hash>—</code></div>
                </div>
            </div>

            <footer class="scwb-v540__boundary">
                <strong>Governed mathematics</strong>
                <span>Expressions still pass through the restricted v5.1 AST → SymPy allow-list. v5.4.0 does not authorize Python eval/exec, remote shell access, or arbitrary code execution.</span>
            </footer>
        </section>
        <?php
        return ob_get_clean();
    }
}
SCWB_V540_Advanced_Graph_Mathematics::boot();
