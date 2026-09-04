<?php
/**
 * Workbench v5.3.2 — Compact Computational Showcase, Advanced Graph Presentation & Workbench Experience Redesign.
 */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V532_Compact_Showcase_Experience {
    const VERSION = '5.3.2';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 6);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 90);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V532_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v532.css';
        $js = $base . '/assets/js/sc-workbench-v532.js';
        wp_register_style('scwb-v532', plugins_url('assets/css/sc-workbench-v532.css', SCWB_V532_PLUGIN_FILE), array('scwb-v530'), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v532', plugins_url('assets/js/sc-workbench-v532.js', SCWB_V532_PLUGIN_FILE), array('scwb-v530'), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    private static function enqueue_assets() {
        if (class_exists('SCWB_V530_Blackboard_Creative_Prototyping')) {
            SCWB_V530_Blackboard_Creative_Prototyping::register_assets();
            wp_enqueue_style('scwb-v530');
            wp_enqueue_script('scwb-v530');
        }
        self::register_assets();
        wp_enqueue_style('scwb-v532');
        wp_enqueue_script('scwb-v532');
        $backend = class_exists('SCWB_V531_Settings_Backend_Repair') ? SCWB_V531_Settings_Backend_Repair::backend_url() : '';
        wp_localize_script('scwb-v532', 'SCWBV532Config', array(
            'version' => self::VERSION,
            'backendUrl' => $backend,
            'workbenchUrl' => home_url('/workbench/'),
        ));
    }

    public static function register_shortcodes() {
        if (shortcode_exists('sc_workbench_homepage_instrument')) {
            remove_shortcode('sc_workbench_homepage_instrument');
        }
        add_shortcode('sc_workbench_homepage_instrument', array(__CLASS__, 'render_homepage'));
        if (!shortcode_exists('sc_workbench_experience')) {
            add_shortcode('sc_workbench_experience', array(__CLASS__, 'render_experience'));
        }
        if (!shortcode_exists('sc_workbench_experience_page')) {
            add_shortcode('sc_workbench_experience_page', array(__CLASS__, 'render_experience'));
        }
    }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/v532-interface-status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'status'),
            'permission_callback' => '__return_true',
        ));
    }

    public static function status() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-v532-interface-status/1.0',
            'version' => self::VERSION,
            'homepageShowcase' => 'compact-rotating',
            'advancedGraphPresentation' => true,
            'workbenchExperience' => true,
            'backendVersionRequired' => '5.3.0',
            'backendRedeployRequired' => false,
        ));
    }

    private static function component($shortcode, $fallback) {
        if (!shortcode_exists($shortcode)) {
            return '<div class="scwb-v532__missing"><strong>' . esc_html($fallback) . '</strong><span>Install the complete Workbench v5.3.2 plugin.</span></div>';
        }
        return do_shortcode('[' . $shortcode . ']');
    }

    public static function render_homepage($atts = array()) {
        self::enqueue_assets();
        ob_start(); ?>
        <section class="scwb-v532-home" data-scwb-v532-home data-version="5.3.2" aria-label="Sustainable Catalyst Workbench computational showcase">
            <header class="scwb-v532-home__header">
                <a class="scwb-v532-home__brand" href="<?php echo esc_url(home_url('/workbench/')); ?>">
                    <span>WORKBENCH</span>
                    <strong>Computational Instrument</strong>
                </a>
                <span class="scwb-v532-home__status" data-scwb-v532-status><i></i> v5.3.2 · checking</span>
            </header>

            <div class="scwb-v532-home__stage">
                <div class="scwb-v532-home__readout">
                    <span class="scwb-v532-home__mode" data-scwb-v532-label>GRAPH MATHEMATICS</span>
                    <code data-scwb-v532-input>f(x) = x³ − 3x</code>
                    <strong data-scwb-v532-output>roots · extrema · derivative</strong>
                    <small data-scwb-v532-meta>CAS → analysis → visualization</small>
                </div>
                <div class="scwb-v532-home__visual">
                    <canvas width="1100" height="380" data-scwb-v532-canvas aria-label="Rotating Workbench mathematics visualization"></canvas>
                    <span>LIVE COMPUTATIONAL VIEW</span>
                </div>
            </div>

            <div class="scwb-v532-home__rail" role="tablist" aria-label="Workbench showcase features">
                <button type="button" class="is-active" data-scwb-v532-mode="0"><b>GRAPH</b><span>analysis</span></button>
                <button type="button" data-scwb-v532-mode="1"><b>CAS</b><span>calculus</span></button>
                <button type="button" data-scwb-v532-mode="2"><b>SOUND</b><span>harmonics</span></button>
                <button type="button" data-scwb-v532-mode="3"><b>FORM</b><span>parametric</span></button>
                <button type="button" data-scwb-v532-mode="4"><b>PROTOTYPE</b><span>MCU · FPGA</span></button>
            </div>

            <footer class="scwb-v532-home__footer">
                <div><b>ƒ(x)</b><i>→</i><b>GRAPH</b><i>→</i><b>Hz</b><i>→</i><b>FORM</b><i>→</i><b>DEVICE</b></div>
                <a class="scwb-v532-home__open" href="<?php echo esc_url(home_url('/workbench/')); ?>">Open Workbench →</a>
            </footer>
        </section>
        <?php return ob_get_clean();
    }

    public static function render_experience($atts = array()) {
        self::enqueue_assets();
        ob_start(); ?>
        <section class="scwb-v532-experience" data-scwb-v532-experience data-version="5.3.2">
            <header class="scwb-v532-experience__hero">
                <div>
                    <p>SUSTAINABLE CATALYST WORKBENCH · v5.3.2</p>
                    <h1>Turn mathematics into analysis, sound, form, and physical systems.</h1>
                    <span>Start with a mathematical idea. Carry the same object through symbolic computation, visualization, creative structure, simulation, and prototyping.</span>
                    <div class="scwb-v532-experience__actions">
                        <a href="#scwb-v532-core">Start computing →</a>
                        <a href="#scwb-v532-pathways">Explore capabilities →</a>
                    </div>
                </div>
                <div class="scwb-v532-experience__signal" aria-label="Workbench capability path">
                    <b>ƒ(x)</b><i>→</i><b>GRAPH</b><i>→</i><b>Hz</b><i>→</i><b>FORM</b><i>→</i><b>DEVICE</b>
                    <small>one object · multiple representations</small>
                </div>
            </header>

            <div class="scwb-v532-experience__status">
                <span><i></i> CAS</span><span><i></i> GRAPH</span><span><i></i> BLACKBOARD</span><span><i></i> CREATIVE MATH</span><span><i></i> PROTOTYPING</span>
            </div>

            <section id="scwb-v532-core" class="scwb-v532-experience__section">
                <div class="scwb-v532-experience__section-head"><p>COMPUTATIONAL CORE</p><h2>Write the mathematics. See what it means.</h2><span>Symbolic translation and graph mathematics stay connected rather than becoming separate calculator steps.</span></div>
                <div class="scwb-v532-experience__core">
                    <div class="scwb-v532-experience__mount is-blackboard"><?php echo self::component('sc_workbench_blackboard', 'Computational Blackboard'); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></div>
                    <div class="scwb-v532-experience__mount is-graph"><?php echo self::component('sc_workbench_graph_mathematics', 'Graph Mathematics'); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></div>
                </div>
            </section>

            <section id="scwb-v532-pathways" class="scwb-v532-experience__section scwb-v532-experience__pathways">
                <div class="scwb-v532-experience__section-head"><p>MATHEMATICS AS A LANGUAGE</p><h2>Move the same relationships across domains.</h2><span>Explore mathematical structure as sound, geometry, signals, and physical computation.</span></div>
                <nav class="scwb-v532-experience__tabs" role="tablist" aria-label="Creative and physical Workbench pathways">
                    <button type="button" class="is-active" data-scwb-v532-lens="sound">Sound &amp; Mathematics</button>
                    <button type="button" data-scwb-v532-lens="form">Mathematics &amp; Form</button>
                    <button type="button" data-scwb-v532-lens="prototype">Prototype Bench</button>
                </nav>
                <div class="scwb-v532-experience__lens is-active" data-scwb-v532-lens-panel="sound"><?php echo self::component('sc_workbench_music_mathematics', 'Sound & Mathematics'); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></div>
                <div class="scwb-v532-experience__lens" data-scwb-v532-lens-panel="form" hidden><?php echo self::component('sc_workbench_creative_mathematics', 'Mathematics & Form'); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></div>
                <div class="scwb-v532-experience__lens" data-scwb-v532-lens-panel="prototype" hidden><?php echo self::component('sc_workbench_prototype_bench', 'Prototype Bench'); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></div>
            </section>

            <section class="scwb-v532-experience__section">
                <div class="scwb-v532-experience__section-head"><p>ADVANCED WORKBENCH</p><h2>Continue from mathematics into full technical work.</h2></div>
                <div class="scwb-v532-experience__navigator">
                    <a href="#scwb-v532-core"><b>Mathematics</b><span>CAS · calculus · graph analysis</span></a>
                    <a href="?studio=visualization"><b>Data &amp; Visualization</b><span>plots · dashboards · spatial views</span></a>
                    <a href="?studio=simulation"><b>Simulation</b><span>systems · scenarios · digital twins</span></a>
                    <a href="?studio=instrumentation"><b>Signals</b><span>frequency · acquisition · uncertainty</span></a>
                    <a href="?studio=runtime"><b>Programming</b><span>multi-language technical projects</span></a>
                    <a href="#scwb-v532-pathways"><b>Physical Computing</b><span>Arduino · ESP32 · PYNQ · FPGA · HDL</span></a>
                </div>
            </section>

            <footer class="scwb-v532-experience__boundary"><strong>Inspectable computation</strong><span>Restricted symbolic parsing, explicit execution boundaries, export-only public hardware scaffolds, and reviewable technical records remain part of the Workbench design.</span></footer>
        </section>
        <?php return ob_get_clean();
    }
}
SCWB_V532_Compact_Showcase_Experience::boot();
