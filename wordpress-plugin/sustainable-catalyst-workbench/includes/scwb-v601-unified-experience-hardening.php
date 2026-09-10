<?php
/** Workbench v6.0.1 — Unified Experience, Runtime Identity & Interface Hardening. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V601_Unified_Experience_Hardening {
    const VERSION = '6.0.1';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 12);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 3000);
        add_action('wp_loaded', array(__CLASS__, 'register_shortcodes'), 3000);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V601_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v601.css';
        $js = $base . '/assets/js/sc-workbench-v601.js';
        wp_register_style('scwb-v601', plugins_url('assets/css/sc-workbench-v601.css', SCWB_V601_PLUGIN_FILE), array('scwb-primary-repair'), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v601', plugins_url('assets/js/sc-workbench-v601.js', SCWB_V601_PLUGIN_FILE), array('scwb-primary-repair'), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    private static function enqueue_assets() {
        self::register_assets();
        wp_enqueue_style('scwb-v601');
        wp_enqueue_script('scwb-v601');
        $backend = class_exists('SCWB_V531_Settings_Backend_Repair') ? SCWB_V531_Settings_Backend_Repair::backend_url('') : '';
        wp_localize_script('scwb-v601', 'SCWBV601Config', array(
            'version' => self::VERSION,
            'backendUrl' => $backend,
            'statusRoute' => '/v601/status',
        ));
    }

    public static function register_shortcodes() {
        foreach (array('sc_workbench_experience','sc_workbench_experience_page','sc_workbench_v601_experience') as $tag) {
            if (shortcode_exists($tag)) { remove_shortcode($tag); }
            add_shortcode($tag, array(__CLASS__, 'render_experience'));
        }
    }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/v601-interface-status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'status'),
            'permission_callback' => '__return_true',
        ));
    }

    public static function status() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-v601-interface-status/1.0',
            'version' => self::VERSION,
            'pluginVersion' => defined('SCWB_VERSION') ? SCWB_VERSION : self::VERSION,
            'primaryShortcodeRegistered' => shortcode_exists('sc_workbench'),
            'computationalProjectRegistered' => shortcode_exists('sc_workbench_computational_project'),
            'graphMathematicsRegistered' => shortcode_exists('sc_workbench_graph_mathematics'),
            'homepageInstrumentIncludedInExperience' => false,
            'graphResizeObserverEnabled' => true,
            'groupedStudioNavigation' => true,
        ));
    }

    public static function render_experience($atts = array()) {
        self::enqueue_assets();
        $atts = shortcode_atts(array('project' => 'default'), $atts, 'sc_workbench_experience');
        $project = sanitize_key($atts['project']) ?: 'default';
        $instance = 'scwb-v601-exp-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v601-experience" data-scwb-v601-experience data-version="6.0.1">
            <header class="scwb-v601-experience__hero">
                <div>
                    <p class="scwb-v601-experience__kicker">Sustainable Catalyst Platform · Workbench v6.0.1</p>
                    <h1>Workbench</h1>
                    <p class="scwb-v601-experience__lede">A unified computational workspace for mathematics, graphing, scientific modeling, engineering analysis, simulation, code, electronics, digital logic, and reproducible technical work.</p>
                    <p class="scwb-v601-experience__sublede">Start with an equation, dataset, model, technical problem, experiment, or engineering system. Keep computation, visualization, assumptions, evidence, provenance, and the resulting technical record connected.</p>
                    <div class="scwb-v601-experience__actions"><a href="#scwb-v601-live">Open full Workbench →</a><a href="#scwb-v601-project">Unified project →</a><a href="#scwb-v601-graph">Graph studio →</a></div>
                </div>
                <div class="scwb-v601-experience__identity" aria-label="Workbench runtime identity">
                    <span>RELEASE <b>6.0.1</b></span><span>STUDIOS <b>39</b></span><span>BACKEND <b data-scwb-v601-backend>CHECKING</b></span><span>GRAPH <b data-scwb-v601-graph-state>RESIZE-SAFE</b></span>
                </div>
            </header>

            <nav class="scwb-v601-experience__rail" aria-label="Workbench sections">
                <a href="#scwb-v601-live">All studios</a><a href="#scwb-v601-project">Unified project</a><a href="#scwb-v601-graph">Graph mathematics</a><a href="#scwb-v601-capabilities">Capabilities</a><a href="#scwb-v601-workflow">Workflow</a><a href="#scwb-v601-boundary">Boundary</a>
            </nav>

            <main>
                <section id="scwb-v601-live" class="scwb-v601-experience__section scwb-v601-experience__live">
                    <div class="scwb-v601-experience__section-head"><div><p>Live workspace · all capabilities</p><h2>Full Workbench</h2></div><p>Search, filter, favorite, and move between all specialist studios without letting the 39-studio registry turn the page into a long sidebar.</p></div>
                    <div class="scwb-v601-experience__mount">
                        <?php echo do_shortcode('[sc_workbench project="' . esc_attr($project) . '" studio="blackboard" title="Sustainable Catalyst Workbench" display="full" diagnostics="false"]'); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
                    </div>
                </section>

                <section id="scwb-v601-project" class="scwb-v601-experience__section">
                    <div class="scwb-v601-experience__section-head"><div><p>Workbench v6</p><h2>Unified computational project</h2></div><p>Shared variables, linked objects, dependency graphs, provenance, append-only history, exports, and explicit platform handoffs.</p></div>
                    <div class="scwb-v601-experience__mount scwb-v601-experience__mount--dark">
                        <?php echo do_shortcode('[sc_workbench_computational_project project="' . esc_attr($project) . '"]'); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
                    </div>
                </section>

                <section id="scwb-v601-graph" class="scwb-v601-experience__section">
                    <div class="scwb-v601-experience__section-head"><div><p>Interactive mathematics</p><h2>Advanced graph mathematics</h2></div><p>The graph remains in normal document flow and redraws on container resize, studio activation, fullscreen changes, and viewport changes.</p></div>
                    <div class="scwb-v601-experience__mount scwb-v601-experience__graph-mount">
                        <?php echo do_shortcode('[sc_workbench_graph_mathematics]'); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
                    </div>
                </section>

                <section id="scwb-v601-capabilities" class="scwb-v601-experience__section">
                    <div class="scwb-v601-experience__section-head"><div><p>Beyond the calculator</p><h2>One technical environment</h2></div><p>The interface is denser, but the capability surface remains complete.</p></div>
                    <div class="scwb-v601-experience__cap-grid">
                        <article><b>MATHEMATICS</b><h3>Symbolic, graphical & geometry</h3><p>CAS, calculus, equations, graph families, advanced graph analysis, dynamic geometry, parameters, roots, extrema, intersections, vector fields, and 3D surfaces.</p></article>
                        <article><b>NUMERICAL</b><h3>Scientific computing</h3><p>Root finding, integration, differentiation, interpolation, ODE solvers, linear algebra, least squares, optimization, diagnostics, and reusable numerical objects.</p></article>
                        <article><b>SYSTEMS</b><h3>Signals & controls</h3><p>FFT, filters, convolution, transfer functions, Bode response, root locus, state-space analysis, controllability, observability, and PID simulation.</p></article>
                        <article><b>ENGINEERING</b><h3>Electronics & embedded</h3><p>Circuits, impedance, ADC/DAC, PWM, sampling, buses, sensor models, GPIO planning, instrumentation, Raspberry Pi, Arduino, and ESP32 scaffolds.</p></article>
                        <article><b>DIGITAL</b><h3>FPGA, PYNQ & logic</h3><p>Boolean logic, truth tables, K-maps, minimization, FSMs, timing, resource estimates, Verilog/VHDL testbenches, and PYNQ planning.</p></article>
                        <article><b>MODELING</b><h3>Simulation & digital twins</h3><p>Dynamic models, scenarios, Monte Carlo studies, state-space systems, calibration, residuals, validation, robotics, and computational intelligence.</p></article>
                        <article><b>DATA</b><h3>Pipelines & visualization</h3><p>Reproducible datasets, transformations, validation, freshness, snapshots, scientific plots, dashboards, uncertainty, spectra, and state views.</p></article>
                        <article><b>EXPERIMENTS</b><h3>Repeatable workflows</h3><p>Protocols, dependencies, checkpoints, schedules, run comparison, deviations, evidence, evaluation, reproducibility, and human review gates.</p></article>
                        <article><b>RECORD</b><h3>Documentation & handoffs</h3><p>Technical dossiers, provenance, history, packages, collaboration, sign-off, offline operation, and explicit handoffs to the Sustainable Catalyst platform.</p></article>
                    </div>
                </section>

                <section id="scwb-v601-workflow" class="scwb-v601-experience__section scwb-v601-experience__workflow">
                    <div class="scwb-v601-experience__section-head"><div><p>Connected workflow</p><h2>From question to reusable technical record</h2></div></div>
                    <ol><li><b>01</b><strong>Define</strong><span>Equation, dataset, model, requirement</span></li><li><b>02</b><strong>Compute</strong><span>Exact, numerical, or simulated analysis</span></li><li><b>03</b><strong>Explore</strong><span>Graphs, geometry, parameters, scenarios</span></li><li><b>04</b><strong>Model</strong><span>System behavior or implementation</span></li><li><b>05</b><strong>Validate</strong><span>Assumptions, diagnostics, evidence</span></li><li><b>06</b><strong>Export</strong><span>Record or platform handoff</span></li></ol>
                </section>

                <section id="scwb-v601-boundary" class="scwb-v601-experience__boundary">
                    <div><p>Execution boundary</p><h2>Power without hidden autonomy</h2></div><p>Workbench supports research, learning, modeling, prototyping, experimentation, technical analysis, and validation planning. Generated engineering artifacts remain human-controlled where physical execution is involved. Results still depend on inputs, assumptions, data quality, model limitations, operating conditions, and appropriate review.</p>
                </section>
            </main>
        </section>
        <?php return ob_get_clean();
    }
}
SCWB_V601_Unified_Experience_Hardening::boot();
