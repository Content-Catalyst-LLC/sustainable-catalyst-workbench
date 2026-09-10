<?php
/** Workbench v5.9.0 — FPGA, PYNQ & Digital Logic Workbench. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V590_FPGA_PYNQ_Digital_Logic {
    const VERSION = '5.9.0';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 8);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 175);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V590_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v590.css';
        $js = $base . '/assets/js/sc-workbench-v590.js';
        wp_register_style('scwb-v590', plugins_url('assets/css/sc-workbench-v590.css', SCWB_V590_PLUGIN_FILE), array(), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v590', plugins_url('assets/js/sc-workbench-v590.js', SCWB_V590_PLUGIN_FILE), array(), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function backend_url($override = '') {
        if (class_exists('SCWB_V531_Settings_Backend_Repair')) {
            return SCWB_V531_Settings_Backend_Repair::backend_url($override);
        }
        $candidate = trim((string) $override);
        if (!$candidate && defined('SCWB_WORKBENCH_BACKEND_URL')) { $candidate = trim((string) SCWB_WORKBENCH_BACKEND_URL); }
        if (function_exists('apply_filters')) { $candidate = (string) apply_filters('scwb_workbench_backend_url', $candidate); }
        return rtrim($candidate, '/');
    }

    private static function enqueue_assets($backend = '') {
        self::register_assets();
        wp_enqueue_style('scwb-v590');
        wp_enqueue_script('scwb-v590');
        wp_localize_script('scwb-v590', 'SCWBV590Config', array(
            'version' => self::VERSION,
            'backendUrl' => self::backend_url($backend),
            'routes' => array(
                'status' => '/v590/status',
                'truthTable' => '/v590/truth-table',
                'minimize' => '/v590/minimize',
                'karnaugh' => '/v590/karnaugh',
                'fsm' => '/v590/fsm',
                'timing' => '/v590/timing',
                'hdlScaffold' => '/v590/hdl-scaffold',
                'resourceEstimate' => '/v590/resource-estimate',
                'pynqOverlay' => '/v590/pynq-overlay',
            ),
        ));
    }

    public static function register_shortcodes() {
        foreach (array(
            'sc_workbench_digital_logic',
            'sc_workbench_fpga_pynq',
            'sc_workbench_digital_logic_studio',
            'sc_workbench_fpga_workbench',
            'sc_workbench_pynq_studio'
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
        register_rest_route('scwb/v1', '/v590-interface-status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'status'),
            'permission_callback' => '__return_true',
        ));
    }

    public static function status() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-digital-logic-interface-status/1.0',
            'version' => self::VERSION,
            'backendConfigured' => '' !== self::backend_url(),
            'backendVersionRequired' => '5.9.0',
            'truthTables' => true,
            'karnaughMaps' => true,
            'booleanMinimization' => true,
            'finiteStateMachines' => true,
            'timingWaveforms' => true,
            'hdlScaffolds' => true,
            'pynqOverlayPlanning' => true,
            'bitstreamProgrammingAuthorized' => false,
        ));
    }

    private static function promote_public_markup($html, $surface) {
        $html = str_replace('data-version="5.8.0"', 'data-version="5.9.0"', $html);
        $html = str_replace('SUSTAINABLE CATALYST WORKBENCH · v5.8.0', 'SUSTAINABLE CATALYST WORKBENCH · v5.9.0', $html);
        $html = str_replace('v5.8.0 ·', 'v5.9.0 ·', $html);
        if ('homepage' === $surface) {
            $html = str_replace('scwb-v580-home', 'scwb-v580-home scwb-v590-home', $html);
        } else {
            $html = str_replace('scwb-v580-experience', 'scwb-v580-experience scwb-v590-experience', $html);
            $html = str_replace('<span><i></i> ELECTRONICS + EMBEDDED</span>', '<span><i></i> ELECTRONICS + EMBEDDED</span><span><i></i> FPGA + DIGITAL LOGIC</span>', $html);
            $needle = '<a href="?studio=electronics"><b>Electronics &amp; Embedded</b><span>circuits · ADC/DAC · PWM · buses · sensors · prototype planning</span></a>';
            $insert = $needle . '<a href="?studio=digital-logic"><b>FPGA, PYNQ &amp; Digital Logic</b><span>truth tables · K-maps · FSMs · timing · HDL · PYNQ</span></a>';
            $html = str_replace($needle, $insert, $html);
        }
        return $html;
    }

    public static function render_homepage($atts = array()) {
        if (!class_exists('SCWB_V580_Electronics_Embedded_Systems')) {
            return '<div role="alert">Workbench homepage showcase requires the complete v5.9.0 plugin.</div>';
        }
        return self::promote_public_markup(SCWB_V580_Electronics_Embedded_Systems::render_homepage($atts), 'homepage');
    }

    public static function render_experience($atts = array()) {
        if (!class_exists('SCWB_V580_Electronics_Embedded_Systems')) {
            return '<div role="alert">Workbench experience requires the complete v5.9.0 plugin.</div>';
        }
        return self::promote_public_markup(SCWB_V580_Electronics_Embedded_Systems::render_experience($atts), 'experience');
    }

    public static function shortcode($atts = array()) {
        $atts = shortcode_atts(array(
            'project' => 'default',
            'display' => 'full',
            'title' => 'FPGA, PYNQ & Digital Logic Workbench',
            'backend' => '',
        ), $atts);
        return self::render($atts);
    }

    public static function render($atts = array()) {
        self::enqueue_assets(isset($atts['backend']) ? $atts['backend'] : '');
        $project = sanitize_key(isset($atts['project']) ? $atts['project'] : 'default') ?: 'default';
        $instance = 'scwb-v590-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v590" data-scwb-v590 data-project="<?php echo esc_attr($project); ?>" data-version="5.9.0">
            <header class="scwb-v590__header">
                <div>
                    <p class="scwb-v590__eyebrow">Sustainable Catalyst Workbench · FPGA, PYNQ &amp; Digital Logic · v5.9.0</p>
                    <h2><?php echo esc_html(isset($atts['title']) ? $atts['title'] : 'FPGA, PYNQ & Digital Logic Workbench'); ?></h2>
                    <p>Design and inspect digital logic from Boolean expressions through truth tables, Karnaugh maps, state machines, timing waveforms, resource estimates, HDL scaffolds, and PYNQ overlay plans.</p>
                </div>
                <span class="scwb-v590__status" data-scwb-v590-status>Checking digital logic backend…</span>
            </header>

            <div class="scwb-v590__tabs" role="tablist" aria-label="Digital logic methods">
                <button type="button" class="is-active" data-scwb-v590-mode="logic">LOGIC</button>
                <button type="button" data-scwb-v590-mode="kmap">K-MAP</button>
                <button type="button" data-scwb-v590-mode="fsm">FSM</button>
                <button type="button" data-scwb-v590-mode="timing">TIMING</button>
                <button type="button" data-scwb-v590-mode="hdl">HDL</button>
                <button type="button" data-scwb-v590-mode="pynq">PYNQ</button>
            </div>

            <div class="scwb-v590__layout">
                <aside class="scwb-v590__controls">
                    <section class="scwb-v590__panel is-active" data-scwb-v590-panel="logic">
                        <label><span>Boolean expression</span><input value="(A & B) | (!A & C)" data-scwb-v590-expression></label>
                        <div class="scwb-v590__actions">
                            <button type="button" class="scwb-v590__run" data-scwb-v590-run="truth">Truth table</button>
                            <button type="button" class="scwb-v590__run" data-scwb-v590-run="minimize">Minimize</button>
                            <button type="button" class="scwb-v590__run" data-scwb-v590-run="resource">Estimate resources</button>
                        </div>
                        <p class="scwb-v590__hint">Allowed syntax: variables, 0/1, ! or ~, &amp;, |, ^, parentheses; AND/OR/NOT/XOR words are also accepted.</p>
                    </section>

                    <section class="scwb-v590__panel" data-scwb-v590-panel="kmap">
                        <label><span>Expression (2–4 variables)</span><input value="(!A & B) | (A & !B)" data-scwb-v590-kmap-expression></label>
                        <button type="button" class="scwb-v590__run" data-scwb-v590-run="kmap">Build Karnaugh map</button>
                    </section>

                    <section class="scwb-v590__panel" data-scwb-v590-panel="fsm">
                        <label><span>States (comma separated)</span><input value="IDLE,RUN,DONE" data-scwb-v590-fsm-states></label>
                        <label><span>Initial state</span><input value="IDLE" data-scwb-v590-fsm-initial></label>
                        <label><span>Encoding</span><select data-scwb-v590-fsm-encoding><option value="binary">Binary</option><option value="gray">Gray</option><option value="one-hot">One-hot</option></select></label>
                        <label><span>Transitions: from,input,to,output</span><textarea rows="7" data-scwb-v590-fsm-transitions>IDLE,start,RUN,0
IDLE,0,IDLE,0
RUN,done,DONE,1
RUN,0,RUN,0
DONE,reset,IDLE,0
DONE,0,DONE,1</textarea></label>
                        <button type="button" class="scwb-v590__run" data-scwb-v590-run="fsm">Validate FSM</button>
                    </section>

                    <section class="scwb-v590__panel" data-scwb-v590-panel="timing">
                        <label><span>Expression</span><input value="A ^ B" data-scwb-v590-timing-expression></label>
                        <label><span>Sample period ns</span><input type="number" step="any" value="10" data-scwb-v590-timing-period></label>
                        <label><span>Signals: NAME:010101</span><textarea rows="5" data-scwb-v590-timing-signals>A:00111100
B:01010101</textarea></label>
                        <button type="button" class="scwb-v590__run" data-scwb-v590-run="timing">Simulate logic waveform</button>
                    </section>

                    <section class="scwb-v590__panel" data-scwb-v590-panel="hdl">
                        <label><span>Language</span><select data-scwb-v590-hdl-language><option value="verilog">Verilog</option><option value="vhdl">VHDL</option></select></label>
                        <label><span>Module name</span><input value="catalyst_logic" data-scwb-v590-hdl-module></label>
                        <label><span>Expression</span><input value="(A & B) | (!A & C)" data-scwb-v590-hdl-expression></label>
                        <label><span>Output</span><input value="Y" data-scwb-v590-hdl-output></label>
                        <button type="button" class="scwb-v590__run" data-scwb-v590-run="hdl">Generate HDL + testbench scaffold</button>
                    </section>

                    <section class="scwb-v590__panel" data-scwb-v590-panel="pynq">
                        <label><span>Board family</span><select data-scwb-v590-pynq-board><option value="generic-pynq">Generic PYNQ</option><option value="pynq-z2">PYNQ-Z2</option><option value="pynq-z1">PYNQ-Z1</option></select></label>
                        <label><span>Project name</span><input value="catalyst_overlay" data-scwb-v590-pynq-project></label>
                        <label><span>Module name</span><input value="catalyst_logic" data-scwb-v590-pynq-module></label>
                        <label><span>Expression</span><input value="A ^ B" data-scwb-v590-pynq-expression></label>
                        <button type="button" class="scwb-v590__run" data-scwb-v590-run="pynq">Create PYNQ overlay scaffold</button>
                    </section>
                </aside>

                <div class="scwb-v590__workspace">
                    <div class="scwb-v590__workspace-head"><span>DIGITAL LOGIC / FPGA OUTPUT</span><b data-scwb-v590-result-kind>READY</b></div>
                    <div class="scwb-v590__visual"><canvas width="1100" height="500" data-scwb-v590-canvas aria-label="Digital logic visualization"></canvas></div>
                    <div class="scwb-v590__metrics" data-scwb-v590-metrics><div><span>METHOD</span><b>—</b></div><div><span>PRIMARY RESULT</span><b>—</b></div><div><span>BOUNDARY</span><b>EXPORT ONLY</b></div></div>
                    <pre class="scwb-v590__json" data-scwb-v590-json>{
  "status": "Ready for deterministic digital-logic analysis"
}</pre>
                </div>
            </div>

            <footer class="scwb-v590__boundary"><strong>Logic analysis, simulation, and export only.</strong><span>Workbench does not run Vivado/Quartus synthesis, resolve physical pins automatically, generate or program bitstreams, access JTAG, or load PYNQ overlays. Verify official board constraints, voltage standards, clocks, timing, resource utilization, and generated HDL in your approved external toolchain before hardware use.</span></footer>
        </section>
        <?php return ob_get_clean();
    }
}
SCWB_V590_FPGA_PYNQ_Digital_Logic::boot();
