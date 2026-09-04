<?php
/** Workbench v5.7.0 — Signals, Systems & Control Mathematics. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V570_Signals_Systems_Control_Mathematics {
    const VERSION = '5.7.0';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 8);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 160);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V570_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v570.css';
        $js = $base . '/assets/js/sc-workbench-v570.js';
        wp_register_style(
            'scwb-v570',
            plugins_url('assets/css/sc-workbench-v570.css', SCWB_V570_PLUGIN_FILE),
            array(),
            file_exists($css) ? (string) filemtime($css) : self::VERSION
        );
        wp_register_script(
            'scwb-v570',
            plugins_url('assets/js/sc-workbench-v570.js', SCWB_V570_PLUGIN_FILE),
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
        wp_enqueue_style('scwb-v570');
        wp_enqueue_script('scwb-v570');
        wp_localize_script('scwb-v570', 'SCWBV570Config', array(
            'version' => self::VERSION,
            'backendUrl' => self::backend_url($backend),
            'routes' => array(
                'status' => '/v570/status',
                'spectrum' => '/v570/spectrum',
                'convolve' => '/v570/convolve',
                'filterDesign' => '/v570/filter-design',
                'transferFunction' => '/v570/transfer-function',
                'stateSpace' => '/v570/state-space',
                'pid' => '/v570/pid',
                'rootLocus' => '/v570/root-locus',
            ),
        ));
    }

    public static function register_shortcodes() {
        foreach (array(
            'sc_workbench_signals_systems_controls',
            'sc_workbench_control_mathematics',
            'sc_workbench_signals_studio',
            'sc_workbench_signals',
            'sc_workbench_systems_control'
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
        register_rest_route('scwb/v1', '/v570-interface-status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'status'),
            'permission_callback' => '__return_true',
        ));
    }

    public static function status() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-signals-systems-control-interface-status/1.0',
            'version' => self::VERSION,
            'backendConfigured' => '' !== self::backend_url(),
            'backendVersionRequired' => '5.7.0',
            'spectrumAnalysis' => true,
            'digitalFilterDesign' => true,
            'transferFunctions' => true,
            'rootLocus' => true,
            'stateSpace' => true,
            'pidClosedLoopSimulation' => true,
            'convolution' => true,
            'reproducibleSignalsControlObjects' => true,
        ));
    }

    private static function promote_public_markup($html, $surface) {
        $html = str_replace('data-version="5.6.0"', 'data-version="5.7.0"', $html);
        $html = str_replace('SUSTAINABLE CATALYST WORKBENCH · v5.6.0', 'SUSTAINABLE CATALYST WORKBENCH · v5.7.0', $html);
        $html = str_replace('v5.6.0 ·', 'v5.7.0 ·', $html);
        if ('homepage' === $surface) {
            $html = str_replace('scwb-v560-home', 'scwb-v560-home scwb-v570-home', $html);
        } else {
            $html = str_replace('scwb-v560-experience', 'scwb-v560-experience scwb-v570-experience', $html);
            $html = str_replace('<span><i></i> NUMERICAL</span>', '<span><i></i> NUMERICAL</span><span><i></i> SIGNALS + CONTROL</span>', $html);
            $needle = '<a href="?studio=numerical"><b>Numerical Computing</b><span>roots · integration · ODEs · linear algebra · optimization</span></a>';
            $insert = $needle . '<a href="?studio=signals"><b>Signals &amp; Control</b><span>spectra · filters · transfer functions · state space · PID</span></a>';
            $html = str_replace($needle, $insert, $html);
        }
        return $html;
    }

    public static function render_homepage($atts = array()) {
        if (!class_exists('SCWB_V560_Numerical_Scientific_Computing')) {
            return '<div role="alert">Workbench homepage showcase requires the complete v5.7.0 plugin.</div>';
        }
        return self::promote_public_markup(SCWB_V560_Numerical_Scientific_Computing::render_homepage($atts), 'homepage');
    }

    public static function render_experience($atts = array()) {
        if (!class_exists('SCWB_V560_Numerical_Scientific_Computing')) {
            return '<div role="alert">Workbench experience requires the complete v5.7.0 plugin.</div>';
        }
        return self::promote_public_markup(SCWB_V560_Numerical_Scientific_Computing::render_experience($atts), 'experience');
    }

    public static function shortcode($atts = array()) {
        $atts = shortcode_atts(array(
            'project' => 'default',
            'display' => 'full',
            'title' => 'Signals, Systems & Control Mathematics',
            'backend' => '',
        ), $atts);
        return self::render($atts);
    }

    public static function render($atts = array()) {
        self::enqueue_assets(isset($atts['backend']) ? $atts['backend'] : '');
        $project = sanitize_key(isset($atts['project']) ? $atts['project'] : 'default') ?: 'default';
        $instance = 'scwb-v570-' . wp_generate_uuid4();
        ob_start();
        ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v570" data-scwb-v570 data-project="<?php echo esc_attr($project); ?>" data-version="5.7.0">
            <header class="scwb-v570__header">
                <div>
                    <p class="scwb-v570__eyebrow">Sustainable Catalyst Workbench · Signals, Systems &amp; Control Mathematics · v5.7.0</p>
                    <h2><?php echo esc_html(isset($atts['title']) ? $atts['title'] : 'Signals, Systems & Control Mathematics'); ?></h2>
                    <p>Inspect spectra, design bounded digital filters, analyze transfer functions and state-space models, trace closed-loop poles, and simulate PID response without leaving the reproducible Workbench environment.</p>
                </div>
                <span class="scwb-v570__status" data-scwb-v570-status>Checking signals backend…</span>
            </header>

            <div class="scwb-v570__tabs" role="tablist" aria-label="Signals and control methods">
                <button type="button" class="is-active" data-scwb-v570-mode="spectrum">SPECTRUM</button>
                <button type="button" data-scwb-v570-mode="filter">FILTER</button>
                <button type="button" data-scwb-v570-mode="transfer">TRANSFER</button>
                <button type="button" data-scwb-v570-mode="root-locus">ROOT LOCUS</button>
                <button type="button" data-scwb-v570-mode="state-space">STATE SPACE</button>
                <button type="button" data-scwb-v570-mode="pid">PID</button>
                <button type="button" data-scwb-v570-mode="convolution">CONVOLUTION</button>
            </div>

            <div class="scwb-v570__layout">
                <aside class="scwb-v570__controls">
                    <section class="scwb-v570__mode-panel is-active" data-scwb-v570-panel="spectrum">
                        <label><span>Sample rate (Hz)</span><input type="number" step="any" value="1000" data-scwb-v570-spectrum-rate></label>
                        <div class="scwb-v570__row">
                            <label><span>Tone (Hz)</span><input type="number" step="any" value="50" data-scwb-v570-spectrum-tone></label>
                            <label><span>Harmonic</span><input type="number" step="any" value="0.2" data-scwb-v570-spectrum-harmonic></label>
                        </div>
                        <label><span>Samples CSV (optional)</span><textarea rows="4" placeholder="Leave blank to synthesize the tone above" data-scwb-v570-spectrum-values></textarea></label>
                        <div class="scwb-v570__row">
                            <label><span>Window</span><select data-scwb-v570-spectrum-window><option value="hann">Hann</option><option value="hamming">Hamming</option><option value="blackman">Blackman</option><option value="rectangular">Rectangular</option></select></label>
                            <label><span>Detrend</span><select data-scwb-v570-spectrum-detrend><option value="constant">Mean</option><option value="linear">Linear</option><option value="none">None</option></select></label>
                        </div>
                        <button type="button" class="scwb-v570__run" data-scwb-v570-run="spectrum">Analyze spectrum</button>
                    </section>

                    <section class="scwb-v570__mode-panel" data-scwb-v570-panel="filter">
                        <div class="scwb-v570__row">
                            <label><span>Family</span><select data-scwb-v570-filter-family><option value="butterworth">Butterworth</option><option value="chebyshev1">Chebyshev I</option></select></label>
                            <label><span>Response</span><select data-scwb-v570-filter-response><option value="lowpass">Low-pass</option><option value="highpass">High-pass</option><option value="bandpass">Band-pass</option><option value="bandstop">Band-stop</option></select></label>
                        </div>
                        <div class="scwb-v570__row">
                            <label><span>Order</span><input type="number" min="1" max="12" value="4" data-scwb-v570-filter-order></label>
                            <label><span>Sample rate</span><input type="number" step="any" value="1000" data-scwb-v570-filter-rate></label>
                        </div>
                        <label><span>Cutoff Hz</span><input value="100" data-scwb-v570-filter-cutoff placeholder="100 or 100,250"></label>
                        <label><span>Ripple dB (Chebyshev)</span><input type="number" step="any" value="1" data-scwb-v570-filter-ripple></label>
                        <button type="button" class="scwb-v570__run" data-scwb-v570-run="filter">Design filter</button>
                    </section>

                    <section class="scwb-v570__mode-panel" data-scwb-v570-panel="transfer">
                        <label><span>Numerator coefficients</span><input value="1" data-scwb-v570-tf-num></label>
                        <label><span>Denominator coefficients</span><input value="1,1" data-scwb-v570-tf-den></label>
                        <div class="scwb-v570__row">
                            <label><span>Min Hz</span><input type="number" step="any" value="0.01" data-scwb-v570-tf-fmin></label>
                            <label><span>Max Hz</span><input type="number" step="any" value="100" data-scwb-v570-tf-fmax></label>
                        </div>
                        <label><span>Step duration (s)</span><input type="number" step="any" value="10" data-scwb-v570-tf-duration></label>
                        <button type="button" class="scwb-v570__run" data-scwb-v570-run="transfer">Analyze transfer function</button>
                    </section>

                    <section class="scwb-v570__mode-panel" data-scwb-v570-panel="root-locus">
                        <label><span>Open-loop numerator</span><input value="1" data-scwb-v570-rl-num></label>
                        <label><span>Open-loop denominator</span><input value="1,3,2,0" data-scwb-v570-rl-den></label>
                        <div class="scwb-v570__row">
                            <label><span>Gain min</span><input type="number" step="any" value="0" data-scwb-v570-rl-min></label>
                            <label><span>Gain max</span><input type="number" step="any" value="100" data-scwb-v570-rl-max></label>
                        </div>
                        <button type="button" class="scwb-v570__run" data-scwb-v570-run="root-locus">Trace root locus</button>
                    </section>

                    <section class="scwb-v570__mode-panel" data-scwb-v570-panel="state-space">
                        <label><span>A matrix (rows separated by new lines)</span><textarea rows="3" data-scwb-v570-ss-a>0,1
-2,-3</textarea></label>
                        <div class="scwb-v570__row">
                            <label><span>B</span><input value="0,1" data-scwb-v570-ss-b></label>
                            <label><span>C</span><input value="1,0" data-scwb-v570-ss-c></label>
                        </div>
                        <div class="scwb-v570__row">
                            <label><span>D</span><input type="number" step="any" value="0" data-scwb-v570-ss-d></label>
                            <label><span>Duration</span><input type="number" step="any" value="10" data-scwb-v570-ss-duration></label>
                        </div>
                        <button type="button" class="scwb-v570__run" data-scwb-v570-run="state-space">Analyze state space</button>
                    </section>

                    <section class="scwb-v570__mode-panel" data-scwb-v570-panel="pid">
                        <label><span>Plant numerator</span><input value="1" data-scwb-v570-pid-num></label>
                        <label><span>Plant denominator</span><input value="1,1" data-scwb-v570-pid-den></label>
                        <div class="scwb-v570__triple">
                            <label><span>Kp</span><input type="number" step="any" value="2" data-scwb-v570-pid-kp></label>
                            <label><span>Ki</span><input type="number" step="any" value="1" data-scwb-v570-pid-ki></label>
                            <label><span>Kd</span><input type="number" step="any" value="0.1" data-scwb-v570-pid-kd></label>
                        </div>
                        <div class="scwb-v570__row">
                            <label><span>Setpoint</span><input type="number" step="any" value="1" data-scwb-v570-pid-setpoint></label>
                            <label><span>Duration</span><input type="number" step="any" value="10" data-scwb-v570-pid-duration></label>
                        </div>
                        <button type="button" class="scwb-v570__run" data-scwb-v570-run="pid">Simulate closed loop</button>
                    </section>

                    <section class="scwb-v570__mode-panel" data-scwb-v570-panel="convolution">
                        <label><span>Signal</span><textarea rows="3" data-scwb-v570-conv-signal>1,2,3,2,1</textarea></label>
                        <label><span>Kernel</span><input value="0.25,0.5,0.25" data-scwb-v570-conv-kernel></label>
                        <div class="scwb-v570__row">
                            <label><span>Mode</span><select data-scwb-v570-conv-mode><option value="same">Same</option><option value="full">Full</option><option value="valid">Valid</option></select></label>
                            <label class="scwb-v570__check"><span>Normalize</span><input type="checkbox" checked data-scwb-v570-conv-normalize></label>
                        </div>
                        <button type="button" class="scwb-v570__run" data-scwb-v570-run="convolution">Convolve signal</button>
                    </section>
                </aside>

                <div class="scwb-v570__workspace">
                    <div class="scwb-v570__workspace-head"><span>SIGNALS / SYSTEMS / CONTROL OUTPUT</span><b data-scwb-v570-result-kind>READY</b></div>
                    <div class="scwb-v570__visual"><canvas width="1100" height="500" data-scwb-v570-canvas aria-label="Signals and control visualization"></canvas></div>
                    <div class="scwb-v570__metrics" data-scwb-v570-metrics>
                        <div><span>METHOD</span><b>—</b></div>
                        <div><span>PRIMARY RESULT</span><b>—</b></div>
                        <div><span>DIAGNOSTIC</span><b>—</b></div>
                    </div>
                    <pre class="scwb-v570__json" data-scwb-v570-json>{
  "status": "Ready for a bounded signals/control computation"
}</pre>
                </div>
            </div>

            <footer class="scwb-v570__boundary"><strong>Governed signals and control computation.</strong><span>Models, filters, spectra, and controller simulations are analytical aids. No arbitrary code execution, shell access, unattended control action, device programming, or physical-system actuation is authorized.</span></footer>
        </section>
        <?php
        return ob_get_clean();
    }
}
SCWB_V570_Signals_Systems_Control_Mathematics::boot();
