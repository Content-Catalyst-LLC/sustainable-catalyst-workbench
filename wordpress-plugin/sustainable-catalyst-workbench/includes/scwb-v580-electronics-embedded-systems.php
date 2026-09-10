<?php
/** Workbench v5.8.0 — Electronics & Embedded Systems Studio. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V580_Electronics_Embedded_Systems {
    const VERSION = '5.8.0';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 8);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 170);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V580_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v580.css';
        $js = $base . '/assets/js/sc-workbench-v580.js';
        wp_register_style('scwb-v580', plugins_url('assets/css/sc-workbench-v580.css', SCWB_V580_PLUGIN_FILE), array(), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v580', plugins_url('assets/js/sc-workbench-v580.js', SCWB_V580_PLUGIN_FILE), array(), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
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
        wp_enqueue_style('scwb-v580');
        wp_enqueue_script('scwb-v580');
        wp_localize_script('scwb-v580', 'SCWBV580Config', array(
            'version' => self::VERSION,
            'backendUrl' => self::backend_url($backend),
            'routes' => array(
                'status' => '/v580/status',
                'resistorNetwork' => '/v580/resistor-network',
                'rlc' => '/v580/rlc',
                'adcDac' => '/v580/adc-dac',
                'pwmTimer' => '/v580/pwm-timer',
                'sampling' => '/v580/sampling',
                'busPlan' => '/v580/bus-plan',
                'sensorModel' => '/v580/sensor-model',
                'gpioPlan' => '/v580/gpio-plan',
                'prototypeScaffold' => '/v580/prototype-scaffold',
            ),
        ));
    }

    public static function register_shortcodes() {
        foreach (array(
            'sc_workbench_electronics_embedded',
            'sc_workbench_electronics_studio',
            'sc_workbench_embedded_systems',
            'sc_workbench_embedded_studio',
            'sc_workbench_electronics'
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
        register_rest_route('scwb/v1', '/v580-interface-status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'status'),
            'permission_callback' => '__return_true',
        ));
    }

    public static function status() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-electronics-embedded-interface-status/1.0',
            'version' => self::VERSION,
            'backendConfigured' => '' !== self::backend_url(),
            'backendVersionRequired' => '5.8.0',
            'circuitAnalysis' => true,
            'adcDacPlanning' => true,
            'pwmTimerPlanning' => true,
            'samplingAnalysis' => true,
            'digitalBusPlanning' => true,
            'sensorModels' => true,
            'gpioPlanning' => true,
            'exportOnlyPrototypeScaffolds' => true,
        ));
    }

    private static function promote_public_markup($html, $surface) {
        $html = str_replace('data-version="5.7.0"', 'data-version="5.8.0"', $html);
        $html = str_replace('SUSTAINABLE CATALYST WORKBENCH · v5.7.0', 'SUSTAINABLE CATALYST WORKBENCH · v5.8.0', $html);
        $html = str_replace('v5.7.0 ·', 'v5.8.0 ·', $html);
        if ('homepage' === $surface) {
            $html = str_replace('scwb-v570-home', 'scwb-v570-home scwb-v580-home', $html);
        } else {
            $html = str_replace('scwb-v570-experience', 'scwb-v570-experience scwb-v580-experience', $html);
            $html = str_replace('<span><i></i> SIGNALS + CONTROL</span>', '<span><i></i> SIGNALS + CONTROL</span><span><i></i> ELECTRONICS + EMBEDDED</span>', $html);
            $needle = '<a href="?studio=signals"><b>Signals &amp; Control</b><span>spectra · filters · transfer functions · state space · PID</span></a>';
            $insert = $needle . '<a href="?studio=electronics"><b>Electronics &amp; Embedded</b><span>circuits · ADC/DAC · PWM · buses · sensors · prototype planning</span></a>';
            $html = str_replace($needle, $insert, $html);
        }
        return $html;
    }

    public static function render_homepage($atts = array()) {
        if (!class_exists('SCWB_V570_Signals_Systems_Control_Mathematics')) {
            return '<div role="alert">Workbench homepage showcase requires the complete v5.8.0 plugin.</div>';
        }
        return self::promote_public_markup(SCWB_V570_Signals_Systems_Control_Mathematics::render_homepage($atts), 'homepage');
    }

    public static function render_experience($atts = array()) {
        if (!class_exists('SCWB_V570_Signals_Systems_Control_Mathematics')) {
            return '<div role="alert">Workbench experience requires the complete v5.8.0 plugin.</div>';
        }
        return self::promote_public_markup(SCWB_V570_Signals_Systems_Control_Mathematics::render_experience($atts), 'experience');
    }

    public static function shortcode($atts = array()) {
        $atts = shortcode_atts(array(
            'project' => 'default',
            'display' => 'full',
            'title' => 'Electronics & Embedded Systems Studio',
            'backend' => '',
        ), $atts);
        return self::render($atts);
    }

    public static function render($atts = array()) {
        self::enqueue_assets(isset($atts['backend']) ? $atts['backend'] : '');
        $project = sanitize_key(isset($atts['project']) ? $atts['project'] : 'default') ?: 'default';
        $instance = 'scwb-v580-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v580" data-scwb-v580 data-project="<?php echo esc_attr($project); ?>" data-version="5.8.0">
            <header class="scwb-v580__header">
                <div>
                    <p class="scwb-v580__eyebrow">Sustainable Catalyst Workbench · Electronics &amp; Embedded Systems · v5.8.0</p>
                    <h2><?php echo esc_html(isset($atts['title']) ? $atts['title'] : 'Electronics & Embedded Systems Studio'); ?></h2>
                    <p>Move from circuit mathematics to ADC/DAC, timing, sampling, digital buses, sensor models, GPIO plans, and export-only embedded scaffolds with explicit electrical assumptions.</p>
                </div>
                <span class="scwb-v580__status" data-scwb-v580-status>Checking electronics backend…</span>
            </header>

            <div class="scwb-v580__tabs" role="tablist" aria-label="Electronics and embedded methods">
                <button type="button" class="is-active" data-scwb-v580-mode="circuit">CIRCUIT</button>
                <button type="button" data-scwb-v580-mode="rlc">RLC</button>
                <button type="button" data-scwb-v580-mode="adc">ADC/DAC</button>
                <button type="button" data-scwb-v580-mode="pwm">PWM/TIMER</button>
                <button type="button" data-scwb-v580-mode="sampling">SAMPLING</button>
                <button type="button" data-scwb-v580-mode="bus">BUS</button>
                <button type="button" data-scwb-v580-mode="sensor">SENSOR</button>
                <button type="button" data-scwb-v580-mode="gpio">GPIO</button>
                <button type="button" data-scwb-v580-mode="prototype">PROTOTYPE</button>
            </div>

            <div class="scwb-v580__layout">
                <aside class="scwb-v580__controls">
                    <section class="scwb-v580__panel is-active" data-scwb-v580-panel="circuit">
                        <label><span>Topology</span><select data-scwb-v580-circuit-topology><option value="series">Series</option><option value="parallel">Parallel</option></select></label>
                        <label><span>Resistors Ω</span><input value="100,220,330" data-scwb-v580-circuit-r></label>
                        <label><span>Source voltage V</span><input type="number" step="any" value="5" data-scwb-v580-circuit-v></label>
                        <button type="button" class="scwb-v580__run" data-scwb-v580-run="circuit">Analyze resistor network</button>
                    </section>

                    <section class="scwb-v580__panel" data-scwb-v580-panel="rlc">
                        <label><span>Topology</span><select data-scwb-v580-rlc-topology><option value="series">Series</option><option value="parallel">Parallel</option></select></label>
                        <div class="scwb-v580__triple"><label><span>R Ω</span><input type="number" step="any" value="100" data-scwb-v580-rlc-r></label><label><span>L H</span><input type="number" step="any" value="0.01" data-scwb-v580-rlc-l></label><label><span>C F</span><input type="number" step="any" value="0.000001" data-scwb-v580-rlc-c></label></div>
                        <div class="scwb-v580__row"><label><span>Frequency Hz</span><input type="number" step="any" value="1000" data-scwb-v580-rlc-f></label><label><span>Source V</span><input type="number" step="any" value="1" data-scwb-v580-rlc-v></label></div>
                        <button type="button" class="scwb-v580__run" data-scwb-v580-run="rlc">Analyze impedance</button>
                    </section>

                    <section class="scwb-v580__panel" data-scwb-v580-panel="adc">
                        <div class="scwb-v580__row"><label><span>Bits</span><input type="number" min="1" max="32" value="12" data-scwb-v580-adc-bits></label><label><span>Reference V</span><input type="number" step="any" value="3.3" data-scwb-v580-adc-ref></label></div>
                        <div class="scwb-v580__row"><label><span>Input V</span><input type="number" step="any" value="1.65" data-scwb-v580-adc-input></label><label><span>DAC code (optional)</span><input type="number" min="0" placeholder="use ADC code" data-scwb-v580-adc-code></label></div>
                        <button type="button" class="scwb-v580__run" data-scwb-v580-run="adc">Quantize ADC / DAC</button>
                    </section>

                    <section class="scwb-v580__panel" data-scwb-v580-panel="pwm">
                        <div class="scwb-v580__row"><label><span>Clock Hz</span><input type="number" step="any" value="16000000" data-scwb-v580-pwm-clock></label><label><span>Target Hz</span><input type="number" step="any" value="1000" data-scwb-v580-pwm-frequency></label></div>
                        <div class="scwb-v580__row"><label><span>Duty %</span><input type="number" step="any" value="50" data-scwb-v580-pwm-duty></label><label><span>Counter bits</span><input type="number" min="4" max="64" value="16" data-scwb-v580-pwm-bits></label></div>
                        <label><span>Prescalers</span><input value="1,8,64,256,1024" data-scwb-v580-pwm-prescalers></label>
                        <label><span>Alignment</span><select data-scwb-v580-pwm-alignment><option value="edge">Edge aligned</option><option value="center">Center aligned</option></select></label>
                        <button type="button" class="scwb-v580__run" data-scwb-v580-run="pwm">Plan PWM timer</button>
                    </section>

                    <section class="scwb-v580__panel" data-scwb-v580-panel="sampling">
                        <div class="scwb-v580__row"><label><span>Sample rate Hz</span><input type="number" step="any" value="10000" data-scwb-v580-sampling-rate></label><label><span>Signal bandwidth Hz</span><input type="number" step="any" value="1000" data-scwb-v580-sampling-bandwidth></label></div>
                        <div class="scwb-v580__row"><label><span>ADC bits</span><input type="number" value="12" data-scwb-v580-sampling-bits></label><label><span>Duration s</span><input type="number" step="any" value="1" data-scwb-v580-sampling-duration></label></div>
                        <button type="button" class="scwb-v580__run" data-scwb-v580-run="sampling">Analyze sampling plan</button>
                    </section>

                    <section class="scwb-v580__panel" data-scwb-v580-panel="bus">
                        <label><span>Protocol</span><select data-scwb-v580-bus-protocol><option value="i2c">I²C</option><option value="spi">SPI</option><option value="uart">UART</option></select></label>
                        <div class="scwb-v580__row"><label><span>Clock / baud Hz</span><input type="number" step="any" value="400000" data-scwb-v580-bus-rate></label><label><span>Payload bytes</span><input type="number" value="32" data-scwb-v580-bus-bytes></label></div>
                        <label><span>Transactions</span><input type="number" value="1" data-scwb-v580-bus-count></label>
                        <button type="button" class="scwb-v580__run" data-scwb-v580-run="bus">Estimate bus transfer</button>
                    </section>

                    <section class="scwb-v580__panel" data-scwb-v580-panel="sensor">
                        <label><span>Model</span><select data-scwb-v580-sensor-model><option value="linear">Linear voltage sensor</option><option value="voltage-divider">Voltage divider</option><option value="ntc-beta">NTC beta</option></select></label>
                        <div class="scwb-v580__row"><label><span>Input / measured V</span><input type="number" step="any" value="1" data-scwb-v580-sensor-input></label><label><span>Gain per V</span><input type="number" step="any" value="100" data-scwb-v580-sensor-gain></label></div>
                        <div class="scwb-v580__row"><label><span>Offset</span><input type="number" step="any" value="0" data-scwb-v580-sensor-offset></label><label><span>Supply V</span><input type="number" step="any" value="3.3" data-scwb-v580-sensor-supply></label></div>
                        <div class="scwb-v580__row"><label><span>Known / nominal Ω</span><input type="number" step="any" value="10000" data-scwb-v580-sensor-known></label><label><span>Measured Ω</span><input type="number" step="any" value="10000" data-scwb-v580-sensor-resistance></label></div>
                        <button type="button" class="scwb-v580__run" data-scwb-v580-run="sensor">Evaluate sensor model</button>
                    </section>

                    <section class="scwb-v580__panel" data-scwb-v580-panel="gpio">
                        <label><span>Target family</span><select data-scwb-v580-gpio-target><option value="generic">Generic</option><option value="arduino">Arduino</option><option value="esp32">ESP32</option><option value="raspberry-pi">Raspberry Pi</option><option value="pynq">PYNQ</option></select></label>
                        <label><span>Assignments: signal,pin,direction,voltage,interface</span><textarea rows="5" data-scwb-v580-gpio-assignments>sensor,A0,input,3.3,adc
pwm_out,D9,output,3.3,pwm
sda,SDA,bidirectional,3.3,i2c
scl,SCL,bidirectional,3.3,i2c</textarea></label>
                        <button type="button" class="scwb-v580__run" data-scwb-v580-run="gpio">Validate GPIO plan</button>
                    </section>

                    <section class="scwb-v580__panel" data-scwb-v580-panel="prototype">
                        <label><span>Target</span><select data-scwb-v580-proto-target><option value="arduino">Arduino</option><option value="esp32">ESP32</option><option value="raspberry-pi">Raspberry Pi</option><option value="pynq">PYNQ</option><option value="verilog">Verilog</option><option value="vhdl">VHDL</option></select></label>
                        <label><span>Project name</span><input value="catalyst_prototype" data-scwb-v580-proto-name></label>
                        <div class="scwb-v580__row"><label><span>Interface</span><select data-scwb-v580-proto-interface><option value="gpio">GPIO</option><option value="adc">ADC</option><option value="pwm">PWM</option><option value="i2c">I²C</option><option value="spi">SPI</option><option value="uart">UART</option></select></label><label><span>Nominal sample rate Hz</span><input type="number" step="any" value="1000" data-scwb-v580-proto-rate></label></div>
                        <button type="button" class="scwb-v580__run" data-scwb-v580-run="prototype">Create export scaffold</button>
                    </section>
                </aside>

                <div class="scwb-v580__workspace">
                    <div class="scwb-v580__workspace-head"><span>ELECTRONICS / EMBEDDED OUTPUT</span><b data-scwb-v580-result-kind>READY</b></div>
                    <div class="scwb-v580__visual"><canvas width="1100" height="500" data-scwb-v580-canvas aria-label="Electronics and embedded visualization"></canvas></div>
                    <div class="scwb-v580__metrics" data-scwb-v580-metrics><div><span>METHOD</span><b>—</b></div><div><span>PRIMARY RESULT</span><b>—</b></div><div><span>DIAGNOSTIC</span><b>—</b></div></div>
                    <pre class="scwb-v580__json" data-scwb-v580-json>{
  "status": "Ready for bounded electronics or embedded-system analysis"
}</pre>
                </div>
            </div>

            <footer class="scwb-v580__boundary"><strong>Governed electronics and embedded planning.</strong><span>Results are analytical and export-only. Verify component ratings, board pinout, voltage domains, timing, grounding, isolation, and applicable safety requirements before physical wiring or programming. Workbench does not access GPIO, serial/JTAG programmers, or automatically program devices.</span></footer>
        </section>
        <?php return ob_get_clean();
    }
}
SCWB_V580_Electronics_Embedded_Systems::boot();
