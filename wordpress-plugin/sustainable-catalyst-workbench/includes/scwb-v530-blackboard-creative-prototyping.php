<?php
/** Workbench v5.3.0 — Computational Blackboard, Creative Mathematics & Physical Prototyping. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V530_Blackboard_Creative_Prototyping {
    const VERSION = '5.3.0';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 62);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V530_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v530.css';
        $js = $base . '/assets/js/sc-workbench-v530.js';
        wp_register_style('scwb-v530', plugins_url('assets/css/sc-workbench-v530.css', SCWB_V530_PLUGIN_FILE), array(), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v530', plugins_url('assets/js/sc-workbench-v530.js', SCWB_V530_PLUGIN_FILE), array(), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
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
        wp_enqueue_style('scwb-v530');
        wp_enqueue_script('scwb-v530');
        wp_localize_script('scwb-v530', 'SCWBV530Config', array(
            'version' => self::VERSION,
            'interfaceVersion' => defined('SCWB_VERSION') ? SCWB_VERSION : self::VERSION,
            'backendUrl' => self::backend_url($backend),
        ));
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_blackboard' => 'blackboard',
            'sc_workbench_computational_blackboard' => 'blackboard',
            'sc_workbench_music_mathematics' => 'music',
            'sc_workbench_creative_mathematics' => 'creative',
            'sc_workbench_prototype_bench' => 'prototype',
            'sc_workbench_homepage_instrument' => 'homepage',
            'sc_workbench_v530_showcase' => 'showcase',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, function($atts) use ($panel) {
                    $atts = shortcode_atts(array(
                        'project' => 'default',
                        'display' => 'full',
                        'title' => '',
                        'backend' => '',
                    ), $atts);
                    return SCWB_V530_Blackboard_Creative_Prototyping::render($atts, $panel);
                });
            }
        }
    }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/v530-interface-status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'status'),
            'permission_callback' => '__return_true',
        ));
    }

    public static function status() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-v530-interface-status/1.0',
            'version' => self::VERSION,
            'backendConfigured' => '' !== self::backend_url(),
            'capabilities' => array(
                'computational blackboard', 'deterministic symbolic translation', 'music mathematics',
                'creative mathematics', 'Arduino prototypes', 'ESP32 prototypes', 'Raspberry Pi prototypes',
                'PYNQ scaffolds', 'Verilog', 'VHDL', 'homepage computational instrument'
            ),
            'arbitraryCodeExecutionAuthorized' => false,
            'remoteShellAuthorized' => false,
            'deviceExecutionAuthorized' => false,
        ));
    }

    private static function field($label, $name, $value = '', $type = 'text', $extra = '') {
        ?><label class="scwb-v530__field"><span><?php echo esc_html($label); ?></span><input type="<?php echo esc_attr($type); ?>" data-scwb-v530-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>" <?php echo $extra; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>></label><?php
    }

    private static function render_blackboard($compact = false) { ?>
        <section class="scwb-v530__blackboard <?php echo $compact ? 'is-compact' : ''; ?>" data-scwb-v530-blackboard>
            <div class="scwb-v530__blackboard-bar">
                <div><span class="scwb-v530__lamp is-live"></span><strong>Computational Blackboard</strong></div>
                <span>restricted symbolic translation · CAS 5.1</span>
            </div>
            <div class="scwb-v530__blackboard-grid">
                <div class="scwb-v530__blackboard-input">
                    <label><span>Write mathematics naturally or symbolically</span><textarea rows="3" data-scwb-v530-blackboard-input spellcheck="false">integrate x^2 from 0 to 3</textarea></label>
                    <div class="scwb-v530__chips" aria-label="Blackboard examples">
                        <button type="button" data-scwb-v530-example="integrate x^2 from 0 to 3">∫ integral</button>
                        <button type="button" data-scwb-v530-example="d/dx sin(x)*exp(x)">d/dx derivative</button>
                        <button type="button" data-scwb-v530-example="solve x^2+4*x-12=0 for x">solve equation</button>
                        <button type="button" data-scwb-v530-example="factor x^4-1">factor</button>
                    </div>
                </div>
                <div class="scwb-v530__translation">
                    <span class="scwb-v530__micro-label">SYMBOLIC TRANSLATION</span>
                    <pre data-scwb-v530-translation>∫ x² dx</pre>
                    <div class="scwb-v530__answer-row"><div><span>EXACT</span><strong data-scwb-v530-exact>9</strong></div><div><span>DECIMAL</span><strong data-scwb-v530-decimal>9.00000000000000</strong></div></div>
                    <div class="scwb-v530__object-line"><span>OBJECT</span><code data-scwb-v530-object>mathematics · waiting</code></div>
                </div>
            </div>
            <?php if (!$compact) : ?>
            <div class="scwb-v530__blackboard-actions">
                <button type="button" class="scwb-v530__primary" data-scwb-v530-action="translate">Translate / compute</button>
                <button type="button" data-scwb-v530-action="graph-blackboard">Graph expression</button>
                <span data-scwb-v530-blackboard-status aria-live="polite">Automatic translation ready.</span>
            </div>
            <div class="scwb-v530__blackboard-graph"><canvas width="900" height="300" data-scwb-v530-blackboard-canvas aria-label="Graph linked to blackboard mathematics"></canvas><div data-scwb-v530-blackboard-graph-note>Graph link ready.</div></div>
            <?php endif; ?>
        </section>
    <?php }

    private static function render_music() { ?>
        <section class="scwb-v530__instrument" data-scwb-v530-music>
            <header><div><p>Sound &amp; Mathematics</p><h3>Hear the structure of a number</h3></div><span data-scwb-v530-music-status>Acoustics engine</span></header>
            <div class="scwb-v530__instrument-grid">
                <div class="scwb-v530__controls">
                    <label class="scwb-v530__field"><span>Mode</span><select data-scwb-v530-field="music_mode"><option value="note">Note → frequency</option><option value="frequency">Frequency → note</option><option value="interval">Interval / cents</option><option value="harmonics">Harmonic series</option><option value="waveform">Waveform</option></select></label>
                    <?php self::field('Note','music_note','A4'); self::field('Frequency (Hz)','music_frequency','440','number','step="any" min="0.001"'); self::field('Second frequency (Hz)','music_second_frequency','660','number','step="any" min="0.001"'); ?>
                    <label class="scwb-v530__field"><span>Waveform</span><select data-scwb-v530-field="music_waveform"><option value="sine">Sine</option><option value="square">Square</option><option value="triangle">Triangle</option><option value="sawtooth">Sawtooth</option></select></label>
                    <div class="scwb-v530__button-row"><button type="button" class="scwb-v530__primary" data-scwb-v530-action="music">Calculate</button><button type="button" data-scwb-v530-action="play-tone">Play tone</button></div>
                </div>
                <div class="scwb-v530__music-stage">
                    <div class="scwb-v530__music-readout"><div><span>NOTE</span><strong data-scwb-v530-music-note>A4</strong></div><div><span>FREQUENCY</span><strong data-scwb-v530-music-frequency>440 Hz</strong></div><div><span>WAVELENGTH</span><strong data-scwb-v530-music-wavelength>0.7795 m</strong></div></div>
                    <canvas width="780" height="260" data-scwb-v530-music-canvas aria-label="Musical waveform"></canvas>
                    <div class="scwb-v530__harmonics" data-scwb-v530-harmonics></div>
                </div>
            </div>
        </section>
    <?php }

    private static function render_creative() { ?>
        <section class="scwb-v530__instrument" data-scwb-v530-creative>
            <header><div><p>Mathematics &amp; Form</p><h3>Turn relationships into geometry</h3></div><span>parametric form engine</span></header>
            <div class="scwb-v530__instrument-grid">
                <div class="scwb-v530__controls">
                    <label class="scwb-v530__field"><span>Form family</span><select data-scwb-v530-field="form_family"><option value="lissajous">Lissajous</option><option value="rose">Polar rose</option><option value="spiral">Harmonic spiral</option><option value="harmonic-orbit">Harmonic orbit</option></select></label>
                    <?php self::field('a','form_a','3','number','step="0.1"'); self::field('b','form_b','2','number','step="0.1"'); self::field('phase','form_phase','0.5','number','step="0.1"'); ?>
                    <button type="button" class="scwb-v530__primary" data-scwb-v530-action="form">Generate form</button>
                    <p class="scwb-v530__hint">Explore symmetry, resonance, phase, ratio, and periodic form as mathematics rather than decoration.</p>
                </div>
                <div class="scwb-v530__creative-stage"><canvas width="780" height="520" data-scwb-v530-form-canvas aria-label="Creative mathematical form"></canvas><div class="scwb-v530__formula" data-scwb-v530-formula>x = sin(3t + φ) · y = sin(2t)</div></div>
            </div>
        </section>
    <?php }

    private static function render_prototype() { ?>
        <section class="scwb-v530__instrument" data-scwb-v530-prototype>
            <header><div><p>Physical Prototyping</p><h3>Move from mathematics to hardware scaffolds</h3></div><span>export-only · human controlled</span></header>
            <div class="scwb-v530__prototype-tabs" role="tablist" aria-label="Prototype targets">
                <?php foreach (array('arduino'=>'Arduino','esp32'=>'ESP32','raspberry-pi'=>'Raspberry Pi','pynq'=>'PYNQ','verilog'=>'Verilog','vhdl'=>'VHDL') as $key=>$label) : ?><button type="button" data-scwb-v530-target="<?php echo esc_attr($key); ?>" class="<?php echo 'arduino'===$key?'is-active':''; ?>"><?php echo esc_html($label); ?></button><?php endforeach; ?>
            </div>
            <div class="scwb-v530__prototype-grid">
                <div class="scwb-v530__controls">
                    <?php self::field('Project','prototype_name','signal_prototype'); self::field('Signal frequency (Hz)','prototype_frequency','440','number','step="any"'); self::field('Sample rate (Hz)','prototype_sample_rate','8000','number','step="any"'); self::field('Clock (MHz)','prototype_clock','100','number','step="any"'); ?>
                    <button type="button" class="scwb-v530__primary" data-scwb-v530-action="prototype">Generate scaffold</button>
                    <div class="scwb-v530__prototype-flow"><span>MATHEMATICS</span><i>→</i><span>SIGNAL</span><i>→</i><span>LOGIC</span><i>→</i><span>DEVICE</span></div>
                </div>
                <div class="scwb-v530__code-panel"><div class="scwb-v530__code-bar"><strong data-scwb-v530-prototype-file>arduino.ino</strong><span data-scwb-v530-prototype-target>Arduino</span></div><pre data-scwb-v530-prototype-code>// Generate an allowlisted prototype scaffold.</pre><p data-scwb-v530-prototype-requirements>Public Workbench does not flash or program hardware automatically.</p></div>
            </div>
        </section>
    <?php }

    private static function render_homepage() { ?>
        <section class="scwb-v530-home scwb-v531-home" data-scwb-v530-home>
            <div class="scwb-v530-home__top scwb-v531-home__top">
                <div><p>WORKBENCH / COMPUTATIONAL INSTRUMENT</p><h3>Mathematics into form, sound, and systems.</h3></div>
                <span data-scwb-v530-home-status><i></i> v5.3.1 · checking backend</span>
            </div>
            <div class="scwb-v531-home__body">
                <div class="scwb-v530-home__blackboard scwb-v531-home__equation">
                    <span>LIVE TRANSFORMATION</span>
                    <code data-scwb-v530-home-input>sin(2*pi*440*t)</code>
                    <strong data-scwb-v530-home-output>→ A4 · waveform · harmonics</strong>
                    <div class="scwb-v531-home__chain"><b>ƒ(x)</b><i>→</i><b>GRAPH</b><i>→</i><b>Hz</b><i>→</i><b>FORM</b><i>→</i><b>DEVICE</b></div>
                </div>
                <div class="scwb-v530-home__visual scwb-v531-home__visual">
                    <div class="scwb-v531-home__mode" data-scwb-v530-home-label>MATHEMATICS → SOUND</div>
                    <canvas width="760" height="300" data-scwb-v530-home-canvas aria-label="Workbench capability visualization"></canvas>
                </div>
            </div>
            <div class="scwb-v531-home__capabilities" aria-label="Workbench capabilities">
                <span><b>CAS</b> symbolic</span><span><b>GRAPH</b> 2D · 3D</span><span><b>SOUND</b> harmonics</span><span><b>FORM</b> parametric</span><span><b>PROTOTYPE</b> MCU · FPGA</span>
            </div>
            <div class="scwb-v530-home__footer scwb-v531-home__footer"><p>Equation → graph → sound → form → physical system</p><a href="/workbench/">Open Workbench →</a></div>
        </section>
    <?php }

    public static function render($atts, $panel = 'showcase') {
        self::enqueue_assets(isset($atts['backend']) ? $atts['backend'] : '');
        $project = sanitize_key($atts['project']) ?: 'default';
        $instance = 'scwb-v530-' . wp_generate_uuid4();
        if ('homepage' === $panel) { ob_start(); self::render_homepage(); return ob_get_clean(); }
        ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v530" data-scwb-v530 data-panel="<?php echo esc_attr($panel); ?>" data-project="<?php echo esc_attr($project); ?>" data-version="5.3.0">
            <?php if ('showcase' === $panel) : ?>
                <header class="scwb-v530__hero"><div><p>Sustainable Catalyst Workbench · v5.3.0</p><h2>Mathematics becomes visible, audible, computational, and physical.</h2><span>Computational Blackboard · Creative Mathematics · Music &amp; Acoustics · Physical Prototyping</span></div><div class="scwb-v530__equation-chain"><b>ƒ(x)</b><i>→</i><b>GRAPH</b><i>→</i><b>Hz</b><i>→</i><b>FORM</b><i>→</i><b>FPGA</b></div></header>
                <?php self::render_blackboard(false); ?>
                <div class="scwb-v530__dual"><?php self::render_music(); self::render_creative(); ?></div>
                <?php self::render_prototype(); ?>
            <?php elseif ('blackboard' === $panel) : self::render_blackboard(false); ?>
            <?php elseif ('music' === $panel) : self::render_music(); ?>
            <?php elseif ('creative' === $panel) : self::render_creative(); ?>
            <?php elseif ('prototype' === $panel) : self::render_prototype(); ?>
            <?php endif; ?>
            <footer class="scwb-v530__boundary"><strong>Governed computation</strong><span>Symbolic translation uses the restricted CAS. Prototype outputs are export-only templates. No arbitrary Python, remote shell, automatic device programming, or unattended hardware execution is authorized.</span></footer>
        </section>
        <?php return ob_get_clean();
    }
}
SCWB_V530_Blackboard_Creative_Prototyping::boot();
