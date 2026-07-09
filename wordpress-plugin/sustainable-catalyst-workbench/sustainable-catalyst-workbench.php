<?php
/**
 * Plugin Name: Sustainable Catalyst Workbench
 * Description: Compact AI-enabled research and analytics workbench with Python/R/Julia/Haskell-ready backend, advanced calculators, serious global-impact tools, SVG visual analytics, and Gemini/DeepSeek/OpenAI provider support, exportable SVG/PNG graph images, and PDF-ready reports with equation CSV export, and equation-derived calculator backlog management, feature-builder queue, article profiles, domain summaries, and 59 equation-derived built calculator tools, plus validation/routing dashboards and page-level calculator embed shortcode recommendations, stable v1.0 shortcode placement modes, validation dashboard, article placement assistant, public tool catalog endpoints, v1.1 Chalkboard Translator symbolic math plus engineering units, v1.2 Graph Studio with parameter sliders, and v1.3 Engineering Mode output templates.
 * Version: 1.3.0
 * Author: Content Catalyst LLC
 * License: MIT
 * Text Domain: sustainable-catalyst-workbench
 */

if (!defined('ABSPATH')) { exit; }

final class SC_Workbench_Plugin {
    const VERSION = '1.3.0';
    const OPTION_BACKEND_URL = 'sc_workbench_backend_url';
    const OPTION_BACKEND_KEY = 'sc_workbench_backend_key';
    const OPTION_AI_PROVIDER = 'sc_workbench_ai_provider';
    const OPTION_PROVIDER_KEY = 'sc_workbench_provider_key_encrypted';
    const OPTION_PROVIDER_KEY_SET = 'sc_workbench_provider_key_set';
    const OPTION_ENABLE_AI = 'sc_workbench_enable_ai';
    const OPTION_ENABLE_SCOPE_GATE = 'sc_workbench_enable_scope_gate';
    const OPTION_DEBUG = 'sc_workbench_debug';
    const OPTION_TIMEOUT = 'sc_workbench_timeout';
    const OPTION_DEFAULT_TOPIC = 'sc_workbench_default_topic';
    const OPTION_THEME = 'sc_workbench_theme';
    const OPTION_VERSION = 'sc_workbench_version';


    public function __construct() {
        add_action('init', [$this, 'register_shortcodes']);
        add_action('wp_enqueue_scripts', [$this, 'enqueue_assets']);
        add_action('admin_enqueue_scripts', [$this, 'enqueue_admin_assets']);
        add_action('rest_api_init', [$this, 'register_rest_routes']);
        add_action('admin_menu', [$this, 'register_admin_menu']);
        add_action('admin_init', [$this, 'handle_settings_save']);
        add_action('plugins_loaded', [$this, 'maybe_install']);
    }

    public static function activate() {
        self::create_equation_table();
        self::create_calculator_backlog_table();
        self::create_feature_builder_table();
        self::create_shortcode_recommendations_table();
        update_option(self::OPTION_VERSION, self::VERSION);
        add_option(self::OPTION_BACKEND_URL, 'http://127.0.0.1:8088');
        add_option(self::OPTION_AI_PROVIDER, 'backend');
        add_option(self::OPTION_ENABLE_AI, '1');
        add_option(self::OPTION_ENABLE_SCOPE_GATE, '1');
        add_option(self::OPTION_DEBUG, '0');
        add_option(self::OPTION_TIMEOUT, '45');
        add_option(self::OPTION_DEFAULT_TOPIC, 'research-library');
        add_option(self::OPTION_THEME, 'institutional');
    }

    public function enqueue_assets() {
        wp_register_style('sc-workbench', plugin_dir_url(__FILE__) . 'assets/sc-workbench.css', [], self::VERSION);
        wp_register_script('sc-workbench', plugin_dir_url(__FILE__) . 'assets/sc-workbench.js', [], self::VERSION, true);
        wp_localize_script('sc-workbench', 'SCWorkbench', [
            'restUrl' => esc_url_raw(rest_url('sc-workbench/v1')),
            'nonce' => wp_create_nonce('wp_rest'),
            'theme' => get_option(self::OPTION_THEME, 'institutional'),
            'localTools' => $this->local_tools(),
            'backendRequiredHelp' => 'Calculators are listed locally. Advanced computation and graph generation require the FastAPI backend to be running and reachable.',
        ]);
    }

    public function enqueue_admin_assets($hook) {
        if (strpos($hook, 'sustainable-catalyst-workbench') !== false) {
            wp_enqueue_style('sc-workbench-admin', plugin_dir_url(__FILE__) . 'assets/sc-workbench-admin.css', [], self::VERSION);
            wp_enqueue_script('sc-workbench-admin', plugin_dir_url(__FILE__) . 'assets/sc-workbench-admin.js', [], self::VERSION, true);
            wp_localize_script('sc-workbench-admin', 'SCWorkbenchAdmin', [
                'restUrl' => esc_url_raw(rest_url('sc-workbench/v1')),
                'nonce' => wp_create_nonce('wp_rest'),
            ]);
        }
    }

    public function register_shortcodes() {
        add_shortcode('sc_workbench', [$this, 'render_workbench']);
        add_shortcode('sc_workbench_compact', [$this, 'render_workbench']);
        add_shortcode('sc_workbench_pathways', [$this, 'render_pathways']);
        add_shortcode('sc_workbench_chalkboard', [$this, 'render_chalkboard']);
        add_shortcode('sc_workbench_graph_studio', [$this, 'render_graph_studio']);
        add_shortcode('sc_workbench_engineering_mode', [$this, 'render_engineering_mode']);
    }

    private function ensure_assets() {
        wp_enqueue_style('sc-workbench');
        wp_enqueue_script('sc-workbench');
    }

    public function render_workbench($atts) {
        $this->ensure_assets();
        $atts = shortcode_atts([
            'topic' => get_option(self::OPTION_DEFAULT_TOPIC, 'research-library'),
            'title' => 'Ask the Sustainable Catalyst Workbench',
            'mode' => 'guided',
            'article' => '',
            'equations' => 'auto',
            'tool' => '',
            'start_tab' => '',
            'display' => 'compact'
        ], $atts, 'sc_workbench');
        $uid = 'scwb-' . wp_generate_uuid4();
        $current_post_id = get_queried_object_id();
        $article_slug = $atts['article'] ? sanitize_title($atts['article']) : ($current_post_id ? get_post_field('post_name', $current_post_id) : '');
        $display_mode = sanitize_key($atts['display']);
        if (!in_array($display_mode, ['inline','compact','full','drawer'], true)) { $display_mode = 'compact'; }
        ob_start(); ?>
        <section id="<?php echo esc_attr($uid); ?>" class="scwb scwb-theme-<?php echo esc_attr(get_option(self::OPTION_THEME, 'institutional')); ?> scwb-display-<?php echo esc_attr($display_mode); ?>" data-scwb data-topic="<?php echo esc_attr(sanitize_key($atts['topic'])); ?>" data-mode="<?php echo esc_attr(sanitize_key($atts['mode'])); ?>" data-display="<?php echo esc_attr($display_mode); ?>" data-post-id="<?php echo esc_attr($current_post_id); ?>" data-article-slug="<?php echo esc_attr($article_slug); ?>" data-equation-display="<?php echo esc_attr(sanitize_key($atts['equations'])); ?>" data-default-tool="<?php echo esc_attr(sanitize_key($atts['tool'])); ?>" data-start-tab="<?php echo esc_attr(sanitize_key($atts['start_tab'])); ?>">
            <div class="scwb-head">
                <p class="scwb-eyebrow">Sustainable Catalyst Workbench</p>
                <h2><?php echo esc_html(sanitize_text_field($atts['title'])); ?></h2>
                <p>A compact research and analytics tool for asking questions, running calculators, generating graphs, and following model-aware pathways across the Sustainable Catalyst knowledge system.</p>
            </div>
            <div class="scwb-mode-row" role="tablist" aria-label="Workbench modes">
                <button type="button" class="is-active" data-scwb-tab="ask">Ask</button>
                <button type="button" data-scwb-tab="chalkboard">Chalkboard</button>
                <button type="button" data-scwb-tab="graph">Graph Studio</button>
                <button type="button" data-scwb-tab="engineering">Engineering Mode</button>
                <button type="button" data-scwb-tab="calculate">Calculate</button>
                <button type="button" data-scwb-tab="models">Models</button>
                <button type="button" data-scwb-tab="equations">Equations</button>
                <button type="button" data-scwb-tab="pathways">Pathways</button>
            </div>

            <div class="scwb-panel is-active" data-scwb-panel="ask">
                <form data-scwb-ask-form class="scwb-form">
                    <label>Ask a question
                        <textarea name="question" rows="4" placeholder="Ask about science, sustainability, engineering, architecture, psychology, economics, energy, governance, mathematical modeling, decision science, or meaning."></textarea>
                    </label>
                    <div class="scwb-inline-controls">
                        <label>Mode <select name="mode"><option value="guided">Guided</option><option value="analyst">Analyst</option><option value="expert">Expert</option></select></label>
                        <button type="submit" class="scwb-button">Ask Workbench</button>
                    </div>
                </form>
                <div class="scwb-output" data-scwb-ask-output hidden></div>
            </div>

            <div class="scwb-panel" data-scwb-panel="chalkboard">
                <?php echo $this->chalkboard_html(); ?>
            </div>

            <div class="scwb-panel" data-scwb-panel="graph">
                <?php echo $this->graph_studio_html(); ?>
            </div>

            <div class="scwb-panel" data-scwb-panel="engineering">
                <?php echo $this->engineering_mode_html(); ?>
            </div>

            <div class="scwb-panel" data-scwb-panel="calculate">
                <div class="scwb-toolbar">
                    <label>Calculator <select data-scwb-tool-select><option value="">Loading calculators…</option></select></label>
                    <label>Mode <select data-scwb-tool-mode><option value="guided">Guided</option><option value="analyst">Analyst</option><option value="expert">Expert</option></select></label>
                    <button type="button" class="scwb-button scwb-button-secondary" data-scwb-open-tool>Open Calculator</button>
                </div>
                <div class="scwb-tool-shell" data-scwb-tool-shell></div>
            </div>

            <div class="scwb-panel" data-scwb-panel="models">
                <div class="scwb-models" data-scwb-models>
                    <p class="scwb-muted">Loading model registry…</p>
                </div>
            </div>

            <div class="scwb-panel" data-scwb-panel="equations">
                <div class="scwb-equations" data-scwb-equations>
                    <p class="scwb-muted">Loading article equations…</p>
                </div>
            </div>

            <div class="scwb-panel" data-scwb-panel="pathways">
                <?php echo $this->pathways_html(); ?>
            </div>
            <p class="scwb-fineprint">Educational and analytical support only. Not a substitute for licensed engineering, architecture, clinical, legal, financial, or safety-critical professional judgment.</p>
        </section>
        <?php return ob_get_clean();
    }

    public function render_chalkboard($atts) {
        $this->ensure_assets();
        $atts = shortcode_atts([
            'title' => 'Chalkboard Translator',
            'display' => 'full'
        ], $atts, 'sc_workbench_chalkboard');
        $uid = 'scwb-chalkboard-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($uid); ?>" class="scwb scwb-chalkboard-only scwb-theme-<?php echo esc_attr(get_option(self::OPTION_THEME, 'institutional')); ?> scwb-display-<?php echo esc_attr(sanitize_key($atts['display'])); ?>" data-scwb-chalkboard-only>
            <div class="scwb-head">
                <p class="scwb-eyebrow">Sustainable Catalyst Workbench</p>
                <h2><?php echo esc_html(sanitize_text_field($atts['title'])); ?></h2>
                <p>Type keyboard math, engineering formulas, or unit-aware expressions and translate them into chalkboard notation, LaTeX, SymPy code, symbolic results, unit notes, and graphs.</p>
            </div>
            <?php echo $this->chalkboard_html(); ?>
            <p class="scwb-fineprint">Educational and analytical support only. Not a substitute for licensed engineering, safety-critical, legal, medical, or financial judgment.</p>
        </section>
        <?php return ob_get_clean();
    }

    public function render_graph_studio($atts) {
        $this->ensure_assets();
        $atts = shortcode_atts([
            'title' => 'Graph Studio',
            'display' => 'full'
        ], $atts, 'sc_workbench_graph_studio');
        $uid = 'scwb-graph-studio-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($uid); ?>" class="scwb scwb-graph-only scwb-theme-<?php echo esc_attr(get_option(self::OPTION_THEME, 'institutional')); ?> scwb-display-<?php echo esc_attr(sanitize_key($atts['display'])); ?>" data-scwb-graph-only>
            <div class="scwb-head">
                <p class="scwb-eyebrow">Sustainable Catalyst Workbench</p>
                <h2><?php echo esc_html(sanitize_text_field($atts['title'])); ?></h2>
                <p>Enter a symbolic function, adjust parameters with sliders, generate exportable graphs, and inspect the equation, assumptions, range, and derivative view.</p>
            </div>
            <?php echo $this->graph_studio_html(); ?>
            <p class="scwb-fineprint">Educational and analytical support only. Not a substitute for licensed engineering, safety-critical, legal, medical, or financial judgment.</p>
        </section>
        <?php return ob_get_clean();
    }

    public function render_engineering_mode($atts) {
        $this->ensure_assets();
        $atts = shortcode_atts([
            'title' => 'Engineering Mode',
            'display' => 'full'
        ], $atts, 'sc_workbench_engineering_mode');
        $uid = 'scwb-engineering-mode-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($uid); ?>" class="scwb scwb-engineering-only scwb-theme-<?php echo esc_attr(get_option(self::OPTION_THEME, 'institutional')); ?> scwb-display-<?php echo esc_attr(sanitize_key($atts['display'])); ?>" data-scwb-engineering-only>
            <div class="scwb-head">
                <p class="scwb-eyebrow">Sustainable Catalyst Workbench</p>
                <h2><?php echo esc_html(sanitize_text_field($atts['title'])); ?></h2>
                <p>Turn formulas, units, and symbolic relationships into an engineering-style calculation note with assumptions, validation checks, warnings, and export-ready review structure.</p>
            </div>
            <?php echo $this->engineering_mode_html(); ?>
            <p class="scwb-fineprint">Educational engineering-aware analysis only. Not a substitute for licensed, code-compliant, safety-critical, or stamped professional engineering judgment.</p>
        </section>
        <?php return ob_get_clean();
    }

    private function chalkboard_html() {
        ob_start(); ?>
        <div class="scwb-chalkboard" data-scwb-chalkboard>
            <div class="scwb-chalkboard-grid">
                <form data-scwb-symbolic-form class="scwb-form scwb-symbolic-form">
                    <label>Keyboard input
                        <textarea name="input" rows="6" data-scwb-symbolic-input placeholder="Examples:
x^2 + 3x - 4
y = sin(x) + 0.3sin(3x)
F = m*a
m = 12 kg
a = 3.5 m/s^2">x^2 + 3x - 4</textarea>
                        <small>Use normal keyboard syntax: <code>^</code> for powers, <code>sqrt(x)</code>, <code>sin(theta)</code>, <code>int</code>-style notation, or engineering lines with units.</small>
                    </label>
                    <div class="scwb-inline-controls scwb-symbolic-controls">
                        <label>Action
                            <select name="action">
                                <option value="translate">Translate</option>
                                <option value="simplify">Simplify</option>
                                <option value="solve">Solve</option>
                                <option value="differentiate">Differentiate</option>
                                <option value="integrate">Integrate</option>
                                <option value="factor">Factor</option>
                                <option value="expand">Expand</option>
                                <option value="graph">Graph</option>
                            </select>
                        </label>
                        <label>Variable <input name="variable" type="text" value="x"></label>
                        <label>x min <input name="x_min" type="number" value="-10" step="any"></label>
                        <label>x max <input name="x_max" type="number" value="10" step="any"></label>
                        <button type="submit" class="scwb-button">Run Symbolic Analysis</button>
                    </div>
                </form>
                <div class="scwb-chalkboard-preview-card">
                    <p class="scwb-card-label">Live chalkboard preview</p>
                    <div class="scwb-chalkboard-display" data-scwb-chalkboard-preview>x² + 3x − 4</div>
                    <p class="scwb-muted">This preview helps users see what their keyboard input means before the backend computes it.</p>
                </div>
            </div>
            <div class="scwb-output" data-scwb-symbolic-output hidden></div>
        </div>
        <?php return ob_get_clean();
    }

    private function graph_studio_html() {
        ob_start(); ?>
        <div class="scwb-graph-studio" data-scwb-graph-studio>
            <form data-scwb-graph-form class="scwb-form scwb-graph-form">
                <label>Graph expression
                    <textarea name="input" rows="4" data-scwb-graph-input placeholder="Examples:
y = a*sin(b*x)
f(x) = A*exp(-k*x)*sin(omega*x)
y = m*x + b">y = a*sin(b*x)</textarea>
                    <small>Use <code>x</code> as the graph axis and symbols such as <code>a</code>, <code>b</code>, <code>k</code>, or <code>omega</code> as adjustable slider parameters.</small>
                </label>
                <div class="scwb-inline-controls scwb-graph-controls-row">
                    <label>Variable <input name="variable" type="text" value="x"></label>
                    <label>x min <input name="x_min" type="number" value="-10" step="any"></label>
                    <label>x max <input name="x_max" type="number" value="10" step="any"></label>
                    <label>Samples <input name="points" type="number" value="700" step="1" min="80" max="2000"></label>
                    <label class="scwb-check-label"><input name="show_derivative" type="checkbox" value="1"> Show derivative</label>
                    <button type="submit" class="scwb-button">Generate Graph</button>
                </div>
            </form>
            <div class="scwb-graph-slider-panel" data-scwb-graph-sliders hidden></div>
            <div class="scwb-output" data-scwb-graph-output hidden></div>
        </div>
        <?php return ob_get_clean();
    }

    private function engineering_mode_html() {
        ob_start(); ?>
        <div class="scwb-engineering-mode" data-scwb-engineering-mode>
            <form data-scwb-engineering-form class="scwb-form scwb-engineering-form">
                <label>Engineering formula, variables, and units
                    <textarea name="input" rows="7" data-scwb-engineering-input placeholder="Examples:
F = m*a
m = 12 kg
a = 3.5 m/s^2

sigma = F/A
F = 1000 N
A = 0.02 m^2">F = m*a
m = 12 kg
a = 3.5 m/s^2</textarea>
                    <small>Use one formula line plus optional unit assignments. Engineering Mode turns the result into a reviewable calculation note.</small>
                </label>
                <div class="scwb-inline-controls scwb-engineering-controls-row">
                    <label>Solve variable <input name="variable" type="text" value=""></label>
                    <label class="scwb-check-label"><input name="include_solve" type="checkbox" value="1"> Try symbolic solve</label>
                    <button type="submit" class="scwb-button">Generate Engineering Note</button>
                </div>
            </form>
            <div class="scwb-engineering-template-card">
                <p class="scwb-card-label">Output template</p>
                <ol>
                    <li>Problem / relationship</li>
                    <li>Inputs and units</li>
                    <li>Formula and symbolic form</li>
                    <li>Computation result</li>
                    <li>Assumptions</li>
                    <li>Validation checks</li>
                    <li>Limitations and next review</li>
                </ol>
            </div>
            <div class="scwb-output" data-scwb-engineering-output hidden></div>
        </div>
        <?php return ob_get_clean();
    }

    public function render_pathways($atts) {
        $this->ensure_assets();
        return '<div class="scwb scwb-pathways-only">' . $this->pathways_html() . '</div>';
    }

    private function pathways_html() {
        return '<div class="scwb-pathways">'
            . '<article><strong>Systems Reasoning</strong><span>Feedback, resilience, thresholds, interdependence, and long-term change.</span></article>'
            . '<article><strong>Scientific and Mathematical Reasoning</strong><span>Symbols, models, calculus, linear algebra, probability, statistics, and interpretation.</span></article>'
            . '<article><strong>Engineering and Built Environment</strong><span>Energy, infrastructure, building performance, materials, architecture, and design constraints.</span></article>'
            . '<article><strong>Psychology and Decision-Making</strong><span>Cognition, behavior, grit, motivation, scales, choices, risk, and judgment.</span></article>'
            . '<article><strong>Economics and Energy Systems</strong><span>Costs, benefits, elasticity, demand, emissions, storage, generation, and scenarios.</span></article>'
            . '<article><strong>Governance and Meaning</strong><span>Institutions, ethics, AI accountability, cultural interpretation, philosophy, and public responsibility.</span></article>'
            . '<article><strong>Pattern, Geometry, Design, Music, and AI</strong><span>Music theory, color systems, vector geometry, embeddings, Fourier analysis, PCA, visual identity, and multimodal patterns.</span></article>'
            . '<article><strong>Earth, Ocean, Climate, and Environmental Monitoring</strong><span>Sensor QA/QC, time series, thresholds, climate indicators, marine systems, earth hazards, and global impact.</span></article>'
            . '<article><strong>Law, Legal Traditions, Health, and Metaphysics</strong><span>International law, comparative legal traditions, public-health analytics, legal/ethical impact, ontology, causation, identity, and meaning.</span></article>'
            . '<article><strong>Advanced Engineering Stack</strong><span>Mechanical, civil, electronics, RF/antenna, aerospace, reliability, safety margins, FMEA, materials, thermal, fluids, and systems engineering.</span></article>'
            . '<article><strong>Lab Science and Advanced Physical Systems</strong><span>Biology, chemistry, physician-facing research metrics, lab QA/QC, nuclear physics, particle physics, neurophysics, and high-resolution graph/report exports.</span></article>'
            . '</div>';
    }

    public function register_rest_routes() {
        register_rest_route('sc-workbench/v1', '/tools', ['methods'=>'GET', 'callback'=>[$this,'rest_tools'], 'permission_callback'=>'__return_true']);
        register_rest_route('sc-workbench/v1', '/tool/(?P<tool_id>[a-z0-9\-]+)', ['methods'=>'GET', 'callback'=>[$this,'rest_tool'], 'permission_callback'=>'__return_true']);
        register_rest_route('sc-workbench/v1', '/run', ['methods'=>'POST', 'callback'=>[$this,'rest_run'], 'permission_callback'=>'__return_true']);
        register_rest_route('sc-workbench/v1', '/ask', ['methods'=>'POST', 'callback'=>[$this,'rest_ask'], 'permission_callback'=>'__return_true']);
        register_rest_route('sc-workbench/v1', '/models', ['methods'=>'GET', 'callback'=>[$this,'rest_models'], 'permission_callback'=>'__return_true']);
        register_rest_route('sc-workbench/v1', '/health', ['methods'=>'GET', 'callback'=>[$this,'rest_health'], 'permission_callback'=>[$this,'admin_permission']]);
        register_rest_route('sc-workbench/v1', '/ai-status', ['methods'=>'GET', 'callback'=>[$this,'rest_ai_status'], 'permission_callback'=>[$this,'admin_permission']]);
        register_rest_route('sc-workbench/v1', '/equations', ['methods'=>'GET', 'callback'=>[$this,'rest_equations'], 'permission_callback'=>'__return_true']);
        register_rest_route('sc-workbench/v1', '/equations/current', ['methods'=>'GET', 'callback'=>[$this,'rest_current_equations'], 'permission_callback'=>'__return_true']);
        register_rest_route('sc-workbench/v1', '/equations/analyze', ['methods'=>'POST', 'callback'=>[$this,'rest_analyze_equation'], 'permission_callback'=>'__return_true']);
        register_rest_route('sc-workbench/v1', '/equations/scan', ['methods'=>'POST', 'callback'=>[$this,'rest_scan_equations'], 'permission_callback'=>[$this,'admin_permission']]);
        register_rest_route('sc-workbench/v1', '/calculator-backlog', ['methods'=>'GET', 'callback'=>[$this,'rest_calculator_backlog'], 'permission_callback'=>[$this,'admin_permission']]);
        register_rest_route('sc-workbench/v1', '/feature-builder', ['methods'=>'GET', 'callback'=>[$this,'rest_feature_builder'], 'permission_callback'=>[$this,'admin_permission']]);
        register_rest_route('sc-workbench/v1', '/shortcode-recommendations', ['methods'=>'GET', 'callback'=>[$this,'rest_shortcode_recommendations'], 'permission_callback'=>[$this,'admin_permission']]);
        register_rest_route('sc-workbench/v1', '/validation-summary', ['methods'=>'GET', 'callback'=>[$this,'rest_validation_summary'], 'permission_callback'=>[$this,'admin_permission']]);
        register_rest_route('sc-workbench/v1', '/tool-catalog', ['methods'=>'GET', 'callback'=>[$this,'rest_tool_catalog'], 'permission_callback'=>'__return_true']);
        register_rest_route('sc-workbench/v1', '/placement-assistant', ['methods'=>'GET', 'callback'=>[$this,'rest_placement_assistant'], 'permission_callback'=>[$this,'admin_permission']]);
        register_rest_route('sc-workbench/v1', '/symbolic', ['methods'=>'POST', 'callback'=>[$this,'rest_symbolic'], 'permission_callback'=>'__return_true']);
        register_rest_route('sc-workbench/v1', '/graph', ['methods'=>'POST', 'callback'=>[$this,'rest_graph'], 'permission_callback'=>'__return_true']);
        register_rest_route('sc-workbench/v1', '/engineering', ['methods'=>'POST', 'callback'=>[$this,'rest_engineering'], 'permission_callback'=>'__return_true']);
    }

    public function admin_permission() { return current_user_can('manage_options'); }

    public function rest_tools(WP_REST_Request $request) {
        $query = [];
        foreach (['domain','topic','limit'] as $key) { if ($request->get_param($key)) { $query[$key] = sanitize_text_field($request->get_param($key)); } }
        $res = $this->backend_get('/tools' . ($query ? '?' . http_build_query($query) : ''));
        if (is_wp_error($res) || !is_array($res) || empty($res['tools'])) {
            return new WP_REST_Response([
                'ok' => true,
                'source' => 'wordpress-local-registry',
                'backend_online' => false,
                'backend_error' => is_wp_error($res) ? $res->get_error_message() : 'Backend returned no tools.',
                'tools' => $this->filter_local_tools($this->local_tools(), $query),
                'notice' => 'Showing built-in calculator registry. Start the FastAPI backend to run Python/R/Julia/Haskell analytics and graphs.'
            ], 200);
        }
        $res['backend_online'] = true;
        return new WP_REST_Response($res, 200);
    }

    public function rest_tool(WP_REST_Request $request) {
        $tool_id = sanitize_key($request['tool_id']);
        $res = $this->backend_get('/tools/' . rawurlencode($tool_id));
        if (is_wp_error($res)) {
            $tool = $this->local_tool($tool_id);
            if ($tool) { return new WP_REST_Response(['ok'=>true, 'source'=>'wordpress-local-registry', 'backend_online'=>false, 'tool'=>$tool], 200); }
            return new WP_REST_Response(['ok'=>false, 'error'=>$res->get_error_message()], 200);
        }
        return new WP_REST_Response($res, 200);
    }

    public function rest_run(WP_REST_Request $request) {
        $payload = $request->get_json_params();
        $payload = is_array($payload) ? $payload : [];
        $res = $this->backend_post('/tools/run', $payload);
        if (is_wp_error($res)) {
            $tool_id = isset($payload['tool_id']) ? sanitize_key($payload['tool_id']) : '';
            $tool = $this->local_tool($tool_id);
            return new WP_REST_Response([
                'ok'=>false,
                'tool'=> $tool ? $tool['title'] : $tool_id,
                'summary'=>'The calculator interface is loaded, but the advanced analytics backend is not reachable from WordPress.',
                'error'=>$res->get_error_message(),
                'values'=>[
                    'backend_status'=>'offline_or_unreachable',
                    'required_action'=>'Start/deploy the FastAPI backend and confirm the Backend URL in SC Workbench settings.'
                ],
                'warnings'=>['This tool requires the Python/FastAPI backend for computation and graph generation.'],
                'disclaimer'=>'Educational support only. Advanced calculators run on the backend, not in browser JavaScript.'
            ], 200);
        }
        return new WP_REST_Response($res, 200);
    }

    public function rest_symbolic(WP_REST_Request $request) {
        $payload = $request->get_json_params();
        $payload = is_array($payload) ? $payload : [];
        $payload['input'] = sanitize_textarea_field($payload['input'] ?? '');
        $payload['action'] = sanitize_key($payload['action'] ?? 'translate');
        $payload['variable'] = sanitize_text_field($payload['variable'] ?? 'x');
        $payload['x_min'] = is_numeric($payload['x_min'] ?? null) ? floatval($payload['x_min']) : -10;
        $payload['x_max'] = is_numeric($payload['x_max'] ?? null) ? floatval($payload['x_max']) : 10;
        $payload['include_graph'] = ($payload['action'] === 'graph');
        $res = $this->backend_post('/symbolic/analyze', $payload);
        if (is_wp_error($res)) {
            return new WP_REST_Response([
                'ok'=>false,
                'tool'=>'Chalkboard Translator + Symbolic Math',
                'summary'=>'The Chalkboard interface is loaded, but the symbolic math backend is not reachable from WordPress.',
                'error'=>$res->get_error_message(),
                'values'=>[
                    'keyboard_input'=>$payload['input'],
                    'backend_status'=>'offline_or_unreachable',
                    'required_action'=>'Deploy or start the FastAPI backend and confirm the Backend URL in SC Workbench settings.'
                ],
                'warnings'=>['Symbolic math, unit-aware analysis, and graph generation require the FastAPI backend.'],
                'disclaimer'=>'Educational support only. Engineering outputs require qualified professional review.'
            ], 200);
        }
        return new WP_REST_Response($res, 200);
    }

    public function rest_graph(WP_REST_Request $request) {
        $payload = $request->get_json_params();
        $payload = is_array($payload) ? $payload : [];
        $payload['input'] = sanitize_textarea_field($payload['input'] ?? '');
        $payload['variable'] = sanitize_text_field($payload['variable'] ?? 'x');
        $payload['x_min'] = is_numeric($payload['x_min'] ?? null) ? floatval($payload['x_min']) : -10;
        $payload['x_max'] = is_numeric($payload['x_max'] ?? null) ? floatval($payload['x_max']) : 10;
        $payload['points'] = is_numeric($payload['points'] ?? null) ? intval($payload['points']) : 700;
        $payload['show_derivative'] = !empty($payload['show_derivative']);
        $params = [];
        if (isset($payload['parameters']) && is_array($payload['parameters'])) {
            foreach ($payload['parameters'] as $key => $value) {
                $safe_key = preg_replace('/[^A-Za-z0-9_]/', '', sanitize_text_field((string)$key));
                if ($safe_key !== '' && is_numeric($value)) { $params[$safe_key] = floatval($value); }
            }
        }
        $payload['parameters'] = $params;
        $res = $this->backend_post('/graph/studio', $payload);
        if (is_wp_error($res)) {
            return new WP_REST_Response([
                'ok'=>false,
                'tool'=>'Graph Studio',
                'summary'=>'The Graph Studio interface is loaded, but the graph backend is not reachable from WordPress.',
                'error'=>$res->get_error_message(),
                'values'=>[
                    'keyboard_input'=>$payload['input'],
                    'backend_status'=>'offline_or_unreachable',
                    'required_action'=>'Deploy or start the FastAPI backend and confirm the Backend URL in SC Workbench settings.'
                ],
                'warnings'=>['Graph Studio requires the FastAPI backend for symbolic parsing, parameter sliders, and SVG graph generation.'],
                'disclaimer'=>'Educational support only. Engineering outputs require qualified professional review.'
            ], 200);
        }
        return new WP_REST_Response($res, 200);
    }

    public function rest_engineering(WP_REST_Request $request) {
        $payload = $request->get_json_params();
        $payload = is_array($payload) ? $payload : [];
        $payload['input'] = sanitize_textarea_field($payload['input'] ?? '');
        $payload['variable'] = sanitize_text_field($payload['variable'] ?? '');
        $payload['include_solve'] = !empty($payload['include_solve']);
        $res = $this->backend_post('/engineering/analyze', $payload);
        if (is_wp_error($res)) {
            return new WP_REST_Response([
                'ok'=>false,
                'tool'=>'Engineering Mode',
                'summary'=>'The Engineering Mode interface is loaded, but the engineering analysis backend is not reachable from WordPress.',
                'error'=>$res->get_error_message(),
                'values'=>[
                    'keyboard_input'=>$payload['input'],
                    'backend_status'=>'offline_or_unreachable',
                    'required_action'=>'Deploy or start the FastAPI backend and confirm the Backend URL in SC Workbench settings.'
                ],
                'warnings'=>['Engineering Mode requires the FastAPI backend for symbolic parsing, unit analysis, and calculation-note generation.'],
                'disclaimer'=>'Educational support only. Engineering outputs require qualified professional review.'
            ], 200);
        }
        return new WP_REST_Response($res, 200);
    }

    public function rest_ask(WP_REST_Request $request) {
        if (get_option(self::OPTION_ENABLE_AI, '1') !== '1') { return new WP_REST_Response(['ok'=>false, 'answer'=>'AI is disabled in Workbench settings.'], 200); }
        $payload = $request->get_json_params();
        if (!is_array($payload)) { $payload = []; }
        if (empty($payload['topic'])) { $payload['topic'] = get_option(self::OPTION_DEFAULT_TOPIC, 'research-library'); }
        $payload['scope_gate_enabled'] = get_option(self::OPTION_ENABLE_SCOPE_GATE, '1') === '1';
        $res = $this->backend_post('/ai/ask', $payload, true);
        if (is_wp_error($res)) { return new WP_REST_Response(['ok'=>false, 'answer'=>'Workbench backend is unavailable: ' . $res->get_error_message()], 200); }
        return new WP_REST_Response($res, 200);
    }

    public function rest_models(WP_REST_Request $request) {
        $res = $this->backend_get('/models/registry');
        if (is_wp_error($res)) {
            return new WP_REST_Response(['ok'=>true, 'source'=>'wordpress-local-registry', 'backend_online'=>false, 'tools'=>$this->local_tools()], 200);
        }
        return new WP_REST_Response($res, 200);
    }

    public function rest_health() {
        $res = $this->backend_get('/health');
        if (is_wp_error($res)) { return new WP_REST_Response(['ok'=>false, 'error'=>$res->get_error_message()], 200); }
        return new WP_REST_Response($res, 200);
    }

    public function rest_ai_status() {
        $res = $this->backend_get('/ai/status', true);
        if (is_wp_error($res)) { return new WP_REST_Response(['ok'=>false, 'error'=>$res->get_error_message()], 200); }
        return new WP_REST_Response($res, 200);
    }

    private function backend_url($path='') {
        $base = rtrim(get_option(self::OPTION_BACKEND_URL, 'http://127.0.0.1:8088'), '/');
        return $base . $path;
    }

    private function request_headers($include_provider_key=false) {
        $headers = ['Accept'=>'application/json', 'Content-Type'=>'application/json'];
        $backend_key = get_option(self::OPTION_BACKEND_KEY, '');
        if ($backend_key) { $headers['X-SC-Workbench-Key'] = $backend_key; }
        if ($include_provider_key) {
            $provider = sanitize_key(get_option(self::OPTION_AI_PROVIDER, 'backend'));
            if ($provider && $provider !== 'backend') { $headers['X-SC-AI-Provider'] = $provider; }
            $provider_key = $this->decrypt(get_option(self::OPTION_PROVIDER_KEY, ''));
            if ($provider_key) {
                $headers['X-SC-Provider-Key'] = $provider_key;
                if ($provider === 'openai') { $headers['X-SC-OpenAI-Key'] = $provider_key; }
                if ($provider === 'gemini') { $headers['X-SC-Gemini-Key'] = $provider_key; }
                if ($provider === 'deepseek') { $headers['X-SC-DeepSeek-Key'] = $provider_key; }
            }
        }
        return $headers;
    }

    private function backend_get($path, $include_provider_key=false) {
        $response = wp_remote_get($this->backend_url($path), ['timeout'=>intval(get_option(self::OPTION_TIMEOUT, 45)), 'headers'=>$this->request_headers($include_provider_key)]);
        return $this->decode_response($response);
    }

    private function backend_post($path, $payload, $include_provider_key=false) {
        $response = wp_remote_post($this->backend_url($path), ['timeout'=>intval(get_option(self::OPTION_TIMEOUT, 45)), 'headers'=>$this->request_headers($include_provider_key), 'body'=>wp_json_encode($payload)]);
        return $this->decode_response($response);
    }

    private function decode_response($response) {
        if (is_wp_error($response)) { return $response; }
        $code = wp_remote_retrieve_response_code($response);
        $body = wp_remote_retrieve_body($response);
        $json = json_decode($body, true);
        if ($json === null) { return new WP_Error('scwb_bad_json', 'Backend returned non-JSON response: ' . substr($body, 0, 200)); }
        if ($code >= 400) { return new WP_Error('scwb_backend_error', isset($json['detail']) ? wp_json_encode($json['detail']) : 'Backend error ' . $code); }
        return $json;
    }

    
    private function local_tools() {
        static $tools = null;
        if ($tools !== null) { return $tools; }
        $file = plugin_dir_path(__FILE__) . 'includes/local-tools.php';
        $tools = file_exists($file) ? include $file : [];
        return is_array($tools) ? $tools : [];
    }

    private function local_tool($tool_id) {
        foreach ($this->local_tools() as $tool) {
            if (isset($tool['id']) && $tool['id'] === $tool_id) { return $tool; }
        }
        return null;
    }

    private function filter_local_tools($tools, $query) {
        if (!empty($query['domain'])) {
            $domain = strtolower((string)$query['domain']);
            $tools = array_values(array_filter($tools, function($tool) use ($domain) {
                return strpos(strtolower(($tool['domain'] ?? '') . ' ' . ($tool['topic'] ?? '') . ' ' . ($tool['description'] ?? '')), $domain) !== false;
            }));
        }
        if (!empty($query['topic'])) {
            $topic = strtolower(str_replace('-', ' ', (string)$query['topic']));
            $tools = array_values(array_filter($tools, function($tool) use ($topic) {
                return strpos(strtolower(($tool['domain'] ?? '') . ' ' . ($tool['topic'] ?? '') . ' ' . ($tool['family'] ?? '') . ' ' . ($tool['description'] ?? '')), $topic) !== false;
            }));
        }
        if (!empty($query['limit'])) { $tools = array_slice($tools, 0, max(1, intval($query['limit']))); }
        return $tools;
    }


    public function maybe_install() {
        $old_version = get_option(self::OPTION_VERSION, '');
        if ($old_version !== self::VERSION) {
            self::create_equation_table();
            self::create_calculator_backlog_table();
            self::create_feature_builder_table();
            self::create_shortcode_recommendations_table();
            if (!$this->calculator_backlog_count()) {
                $this->import_calculator_backlog_from_file($this->bundled_calculator_suggestions_csv(), true);
            }
            if (!$this->feature_builder_count()) {
                $this->import_feature_builder_from_file($this->bundled_feature_builder_queue_csv(), true);
            }
            // v0.9.6 keeps the scanner cache rebuild behavior and adds equation-derived calculator backlog management, feature-builder queue, article profiles, domain summaries, and 59 equation-derived built calculator tools, plus validation/routing dashboards and page-level calculator embed shortcode recommendations, stable v1.0 shortcode placement modes, validation dashboard, article placement assistant, public tool catalog endpoints, v1.1 Chalkboard Translator symbolic math plus engineering units, v1.2 Graph Studio with parameter sliders, and v1.3 Engineering Mode output templates.
            // The equation table is a generated cache, so it is safe to clear during scanner upgrades and rebuild from posts.
            if ($old_version && version_compare($old_version, '0.9.4', '<')) {
                $this->clear_equation_registry();
            }
            update_option(self::OPTION_VERSION, self::VERSION);
        }
    }

    private static function equation_table_name() {
        global $wpdb;
        return $wpdb->prefix . 'sc_workbench_equations';
    }

    public static function create_equation_table() {
        global $wpdb;
        $table = self::equation_table_name();
        $charset = $wpdb->get_charset_collate();
        require_once ABSPATH . 'wp-admin/includes/upgrade.php';
        $sql = "CREATE TABLE {$table} (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            post_id BIGINT UNSIGNED NOT NULL,
            post_title TEXT NOT NULL,
            post_slug VARCHAR(255) NOT NULL,
            post_type VARCHAR(64) NOT NULL,
            equation_raw LONGTEXT NOT NULL,
            equation_normalized LONGTEXT NULL,
            display_mode VARCHAR(32) NULL,
            context_before LONGTEXT NULL,
            context_after LONGTEXT NULL,
            equation_hash CHAR(64) NOT NULL,
            suggested_domain VARCHAR(255) NULL,
            suggested_tools LONGTEXT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY  (id),
            UNIQUE KEY equation_hash_unique (equation_hash),
            KEY post_id_idx (post_id),
            KEY post_slug_idx (post_slug),
            KEY display_mode_idx (display_mode)
        ) {$charset};";
        dbDelta($sql);
    }

    private function clear_equation_registry() {
        global $wpdb;
        $table = self::equation_table_name();
        // This table only stores generated equation-index cache records. Published content is not changed.
        $wpdb->query('TRUNCATE TABLE ' . $table);
    }

    private function prepare_content_for_equation_scan($content, $strip_html=false) {
        $charset = get_bloginfo('charset') ?: 'UTF-8';
        $content = (string)$content;

        // IMPORTANT: post_content is already stored in the database as content, not request input.
        // Do not call wp_unslash() here. wp_unslash()/stripslashes removes the literal LaTeX
        // backslashes from MathJax delimiters such as \( ... \), turning them into plain
        // parentheses/brackets and causing the scanner to find zero equations.
        $content = html_entity_decode($content, ENT_QUOTES | ENT_HTML5, $charset);
        $content = str_ireplace(['&bsol;', '&#92;', '&#x5c;'], '\\', $content);

        // Some editors/plugins persist MathJax delimiters with doubled slashes. Collapse only delimiter slashes,
        // not LaTeX line-breaks inside aligned equations.
        $content = str_replace(['\\(', '\\)', '\\[', '\\]'], ['\(', '\)', '\[', '\]'], $content);
        $content = str_replace(["\r\n", "\r"], "\n", $content);

        // Remove regions where LaTeX-looking delimiters often appear as literal code or generated output.
        $content = preg_replace('/<script\b[^>]*>.*?<\/script>/is', ' ', $content);
        $content = preg_replace('/<style\b[^>]*>.*?<\/style>/is', ' ', $content);
        $content = preg_replace('/<pre\b[^>]*>.*?<\/pre>/is', ' ', $content);
        $content = preg_replace('/<code\b[^>]*>.*?<\/code>/is', ' ', $content);

        if ($strip_html) {
            // Second-pass scanner: strip layout/table markup before delimiter detection so an equation inside
            // a table cell is read as the equation itself, not as broken HTML fragments.
            $content = wp_strip_all_tags($content);
            $content = html_entity_decode($content, ENT_QUOTES | ENT_HTML5, $charset);
        }
        return $content;
    }

    private function normalize_equation($raw) {
        $eq = trim((string)$raw);
        $pairs = [
            ['\\[','\\]'], ['\\(','\\)'], ['$$','$$'], ['[latex]','[/latex]']
        ];
        foreach ($pairs as $pair) {
            if (substr($eq, 0, strlen($pair[0])) === $pair[0] && substr($eq, -strlen($pair[1])) === $pair[1]) {
                $eq = substr($eq, strlen($pair[0]), strlen($eq) - strlen($pair[0]) - strlen($pair[1]));
                break;
            }
        }
        $eq = html_entity_decode($eq, ENT_QUOTES | ENT_HTML5, get_bloginfo('charset') ?: 'UTF-8');
        $eq = wp_strip_all_tags($eq);
        $eq = str_replace(["\r\n", "\r", "\n", "\t"], ' ', $eq);
        $eq = preg_replace('/\s+/', ' ', $eq);
        return trim($eq);
    }

    private function equation_candidate_has_math_signal($eq) {
        $eq = trim((string)$eq);
        if ($eq === '') { return false; }

        // v0.9.4 avoids a single fragile PCRE command pattern. These checks are intentionally simple.
        foreach (['=', '+', '*', '/', '^', '_', '{', '}', '>', '<'] as $signal) {
            if (strpos($eq, $signal) !== false) { return true; }
        }
        foreach (['\\frac','\\sum','\\prod','\\int','\\partial','\\nabla','\\times','\\cdot','\\sim','\\in','\\notin','\\geq','\\leq','\\approx','\\rightarrow','\\leftarrow','\\alpha','\\beta','\\gamma','\\delta','\\epsilon','\\lambda','\\mu','\\nu','\\theta','\\sigma','\\kappa','\\omega'] as $cmd) {
            if (strpos($eq, $cmd) !== false) { return true; }
        }
        if (preg_match('/[A-Za-z][A-Za-z0-9]*\s*\([^)]{1,60}\)/', $eq)) { return true; }
        if (preg_match('/\bO\s*\([^)]{1,60}\)/', $eq)) { return true; }
        return false;
    }

    private function is_valid_equation_candidate($raw, $normalized, $mode='inline') {
        $raw = (string)$raw;
        $eq = trim((string)$normalized);
        $len = strlen($eq);
        if ($len < 3 || $len > 700) { return false; }

        // Reject broken delimiter captures and HTML/table fragments.
        if (preg_match('/(<\/?[a-z][^>]*>|&lt;\/?[a-z]|&gt;|<|>)/i', $eq)) { return false; }
        if (preg_match('/(<\/?(td|tr|th|table|tbody|thead|div|p|span|pre)\b|&lt;\/?(td|tr|th|table|tbody|thead|div|p|span|pre)\b)/i', $raw)) { return false; }
        if (substr($eq, 0, 2) === '\\)' || substr($eq, 0, 2) === '\\]') { return false; }
        if (substr($eq, -2) === '\\(' || substr($eq, -2) === '\\[') { return false; }
        if ((strpos($eq, '\\)') !== false && strpos($eq, '\\(') !== false) || (strpos($eq, '\\]') !== false && strpos($eq, '\\[') !== false)) { return false; }

        // Reject prose, captions, code exports, and table/cell text accidentally captured between malformed delimiters.
        if (preg_match('/\b(interpretation|represents|exported|summary|article title|suggested domain|graphability|recommended tool|back to top|knowledge layer|computational expression|data logic|what changed|what is building|what procedure|policy coherence|long-horizon|capability expansion)\b/i', $eq)) { return false; }
        if (preg_match('/\b(print|return|import|output_file|summary exported|cross-territory|console\.log)\b/i', $eq)) { return false; }

        // Single-letter inline variables create noise in a site-wide registry; keep subscripted/superscripted variables and real expressions.
        if ($mode === 'inline' && preg_match('/^[A-Za-z]$/', $eq)) { return false; }
        if ($mode === 'inline' && $len < 6 && !$this->equation_candidate_has_math_signal($eq)) { return false; }

        if (!$this->equation_candidate_has_math_signal($eq)) { return false; }

        // A candidate with many ordinary words is almost certainly prose between broken delimiters.
        preg_match_all('/\b[A-Za-z]{4,}\b/', $eq, $word_matches);
        $word_count = count($word_matches[0]);
        if ($word_count > 5 && $mode === 'inline') { return false; }
        if ($word_count > 12 && $mode !== 'inline') { return false; }

        return true;
    }

    private function add_equation_candidate(&$found, $content, $raw, $mode, $offset) {
        $normalized = $this->normalize_equation($raw);
        if (!$this->is_valid_equation_candidate($raw, $normalized, $mode)) { return; }
        $before_raw = substr($content, max(0, $offset - 650), min(650, $offset));
        $after_raw = substr($content, $offset + strlen($raw), 650);
        $found[] = [
            'raw' => $raw,
            'inner' => $normalized,
            'normalized' => $normalized,
            'display_mode' => $mode,
            'offset' => $offset,
            'context_before' => $this->clean_equation_context($before_raw, true),
            'context_after' => $this->clean_equation_context($after_raw, false),
        ];
    }

    private function scan_token_delimited_equations($content, $open, $close, $mode, $max_len, &$found) {
        $pos = 0;
        $open_len = strlen($open);
        $close_len = strlen($close);
        while (($start = strpos($content, $open, $pos)) !== false) {
            $inner_start = $start + $open_len;
            $end = strpos($content, $close, $inner_start);
            if ($end === false) { break; }
            $inner_len = $end - $inner_start;
            $raw_len = $end + $close_len - $start;
            // If the next close is unreasonably far away, treat the open delimiter as malformed and continue.
            if ($inner_len > $max_len) {
                $pos = $inner_start;
                continue;
            }
            $raw = substr($content, $start, $raw_len);
            $this->add_equation_candidate($found, $content, $raw, $mode, $start);
            $pos = $end + $close_len;
        }
    }

    private function scan_prepared_content_for_equations($content, &$found) {
        // Token scanner is less brittle than regex on real WordPress HTML.
        $this->scan_token_delimited_equations($content, '\[', '\]', 'display', 1600, $found);
        $this->scan_token_delimited_equations($content, '\(', '\)', 'inline', 420, $found);
        $this->scan_token_delimited_equations($content, '$$', '$$', 'display', 1600, $found);

        // Shortcode form still benefits from regex because delimiters are longer and case-insensitive.
        if (preg_match_all('/\[latex\]([\s\S]{1,1600}?)\[\/latex\]/i', $content, $matches, PREG_SET_ORDER | PREG_OFFSET_CAPTURE)) {
            foreach ($matches as $m) {
                $raw = $m[0][0];
                $offset = intval($m[0][1]);
                $this->add_equation_candidate($found, $content, $raw, 'shortcode', $offset);
            }
        }
    }

    private function extract_equations_from_content($content) {
        $found = [];

        // First pass: raw post_content after entity/delimiter normalization.
        $raw_content = $this->prepare_content_for_equation_scan($content, false);
        $this->scan_prepared_content_for_equations($raw_content, $found);

        // Second pass: HTML-stripped content. This catches equations stored inside tables/cards
        // while avoiding HTML tag fragments in the indexed equation body.
        $text_content = $this->prepare_content_for_equation_scan($content, true);
        if ($text_content !== $raw_content) {
            $this->scan_prepared_content_for_equations($text_content, $found);
        }

        usort($found, fn($a,$b) => $a['offset'] <=> $b['offset']);
        $seen = [];
        $unique = [];
        foreach ($found as $item) {
            $key = hash('sha256', $item['display_mode'] . '|' . $item['normalized']);
            if (isset($seen[$key])) { continue; }
            $seen[$key] = true;
            $unique[] = $item;
        }
        return $unique;
    }

    private function clean_equation_context($text, $from_before=false) {
        $text = wp_strip_all_tags(strip_shortcodes((string)$text));
        $text = html_entity_decode($text, ENT_QUOTES | ENT_HTML5, get_bloginfo('charset') ?: 'UTF-8');
        $text = trim(preg_replace('/\s+/', ' ', $text));
        if (strlen($text) > 360) {
            $text = $from_before ? substr($text, -360) : substr($text, 0, 360);
        }
        return trim($text);
    }

    private function suggest_tools_for_equation($equation, $context='') {
        $haystack = strtolower($equation . ' ' . $context);
        $tools = [];
        $domain = 'Mathematical Modeling';
        $add = function($id) use (&$tools) { if (!in_array($id, $tools, true)) { $tools[] = $id; } };
        if (preg_match('/matrix|\\begin\{bmatrix\}|\\begin\{pmatrix\}|eigen|rank|det|vector|\\vec|\\mathbf|a_\{?ij|\\lambda/', $haystack)) { $domain='Linear Algebra and Systems Modeling'; $add('linear-system-solver'); $add('vector-geometry-calculator'); }
        if (preg_match('/derivative|integral|\\frac\{d|\\int|dx|dy|\\partial|lim_|\\nabla/', $haystack)) { $domain='Calculus and Scientific Computing'; $add('calculus-function-analyzer'); $add('differential-equation-simulator'); }
        if (preg_match('/probability|variance|standard deviation|\\sigma|\\mu|e\(|var\(|p\(|bayes|confidence|distribution|\\sim/', $haystack)) { $domain='Probability and Statistics'; $add('statistics-analyzer'); $add('probability-distribution-calculator'); }
        if (preg_match('/regression|\\hat\{?y|b_0|b_1|r\^2|correlation|forecast|time[- ]series|predict/', $haystack)) { $domain='Predictive Analytics'; $add('regression-analyzer'); $add('predictive-analytics-forecasting-tool'); $add('time-series-diagnostics-tool'); }
        if (preg_match('/stock|flow|s_\{?t|x_\{?t\+1|feedback|threshold|carrying capacity|limits to growth|system dynamics/', $haystack)) { $domain='Systems Modeling'; $add('systems-modeling-tool'); $add('limits-to-growth-system-dynamics-tool'); }
        if (preg_match('/elasticity|npv|discount|gdp|inflation|demand|supply|utility|cost|benefit|econom/', $haystack)) { $domain='Economics'; $add('economics-calculator'); $add('economics-forecasting-and-scenario-tool'); $add('econometrics-and-policy-model-tool'); }
        if (preg_match('/risk|hazard|consequence|resilience|scenario|impact|exposure|vulnerab/', $haystack)) { $domain='Risk, Resilience, and Global Impact'; $add('decision-analysis-tool'); $add('global-impact-assessment-matrix'); }
        if (preg_match('/energy|emission|carbon|co2|kwh|lcoe|grid|solar|battery/', $haystack)) { $domain='Energy and Climate'; $add('energy-systems-calculator'); $add('climate-change-scenario-tool'); }
        if (preg_match('/beam|stress|strain|force|torque|velocity|acceleration|pressure|thermal|fluid|mechanical|structural/', $haystack)) { $domain='Engineering'; $add('mechanical-systems-engineering-tool'); $add('structural-engineering-tool'); }
        if (preg_match('/voltage|current|impedance|frequency|antenna|rf|circuit|filter|resonance|power system/', $haystack)) { $domain='Electrical, RF, and Power Systems'; $add('electronics-engineering-calculator'); $add('rf-and-antenna-calculator'); $add('power-systems-engineering-tool'); }
        if (preg_match('/climate|sensor|monitoring|pollution|water quality|air quality|biodiversity|environment/', $haystack)) { $domain='Environmental Monitoring'; $add('environmental-monitoring-qaqc-tool'); $add('environmental-science-calculator'); }
        if (preg_match('/orbit|rocket|gravity|stellar|redshift|astronomy|astrophysics/', $haystack)) { $domain='Astrophysics and Aerospace'; $add('rocket-science-and-orbital-mechanics-calculator'); $add('astrophysics-research-calculator'); }
        if (preg_match('/dose|sensitivity|specificity|prevalence|trial|clinical|medical|health|diagnostic/', $haystack)) { $domain='Health and Clinical Research'; $add('clinical-research-calculator'); $add('health-and-medical-public-health-analytics-tool'); }
        if (!$tools) { $add('systems-modeling-tool'); $add('systems-thinking-tool'); }
        return ['domain'=>$domain, 'tools'=>$tools];
    }

    private function scan_equations($limit=500) {
        global $wpdb;
        self::create_equation_table();
        // Rebuild means rebuild: clear stale scanner output before indexing.
        $this->clear_equation_registry();
        $public_types = get_post_types(['public'=>true], 'names');
        $public_types = array_values(array_filter($public_types, fn($t) => !in_array($t, ['attachment'], true)));
        if (!$public_types) { $public_types = ['post','page']; }
        $placeholders = implode(',', array_fill(0, count($public_types), '%s'));
        $like_clauses = "(post_content LIKE '%\\(%' OR post_content LIKE '%\\[%' OR post_content LIKE '%" . '$$' . "%' OR post_content LIKE '%[latex]%')";
        $sql = $wpdb->prepare("SELECT ID, post_title, post_name, post_type, post_content FROM {$wpdb->posts} WHERE post_status='publish' AND post_type IN ({$placeholders}) AND {$like_clauses} ORDER BY post_modified_gmt DESC LIMIT %d", array_merge($public_types, [intval($limit)]));
        $posts = $wpdb->get_results($sql);
        $table = self::equation_table_name();
        $count = 0;
        $posts_scanned = 0;
        foreach ($posts as $post) {
            $posts_scanned++;
            $equations = $this->extract_equations_from_content($post->post_content);
            foreach ($equations as $eq) {
                $suggest = $this->suggest_tools_for_equation($eq['normalized'], $eq['context_before'] . ' ' . $eq['context_after'] . ' ' . $post->post_title);
                $hash = hash('sha256', $post->ID . '|' . $eq['display_mode'] . '|' . $eq['normalized']);
                $data = [
                    'post_id' => intval($post->ID),
                    'post_title' => $post->post_title,
                    'post_slug' => $post->post_name,
                    'post_type' => $post->post_type,
                    'equation_raw' => $eq['raw'],
                    'equation_normalized' => $eq['normalized'],
                    'display_mode' => $eq['display_mode'],
                    'context_before' => $eq['context_before'],
                    'context_after' => $eq['context_after'],
                    'equation_hash' => $hash,
                    'suggested_domain' => $suggest['domain'],
                    'suggested_tools' => wp_json_encode($suggest['tools']),
                    'updated_at' => current_time('mysql'),
                ];
                $existing = $wpdb->get_var($wpdb->prepare("SELECT id FROM {$table} WHERE equation_hash=%s", $hash));
                if ($existing) {
                    $wpdb->update($table, $data, ['id'=>intval($existing)]);
                } else {
                    $data['created_at'] = current_time('mysql');
                    $wpdb->insert($table, $data);
                }
                $count++;
            }
        }
        return ['ok'=>true, 'posts_scanned'=>$posts_scanned, 'equations_indexed'=>$count, 'table'=>$table];
    }

    public function rest_scan_equations(WP_REST_Request $request) {
        $limit = min(2000, max(10, intval($request->get_param('limit') ?: 500)));
        return new WP_REST_Response($this->scan_equations($limit), 200);
    }

    public function rest_equations(WP_REST_Request $request) {
        global $wpdb;
        self::create_equation_table();
        $table = self::equation_table_name();
        $limit = min(200, max(1, intval($request->get_param('limit') ?: 50)));
        $where = ['1=1'];
        $params = [];
        if ($request->get_param('post_id')) { $where[] = 'post_id=%d'; $params[] = intval($request->get_param('post_id')); }
        if ($request->get_param('slug')) { $where[] = 'post_slug=%s'; $params[] = sanitize_title($request->get_param('slug')); }
        if ($request->get_param('search')) { $where[] = '(equation_normalized LIKE %s OR post_title LIKE %s OR suggested_domain LIKE %s)'; $term = '%' . $wpdb->esc_like(sanitize_text_field($request->get_param('search'))) . '%'; $params = array_merge($params, [$term,$term,$term]); }
        $sql = "SELECT * FROM {$table} WHERE " . implode(' AND ', $where) . " ORDER BY post_title ASC, id ASC LIMIT %d";
        $params[] = $limit;
        $rows = $wpdb->get_results($wpdb->prepare($sql, $params), ARRAY_A);
        foreach ($rows as &$row) { $row['suggested_tools'] = json_decode($row['suggested_tools'] ?: '[]', true) ?: []; }
        return new WP_REST_Response(['ok'=>true, 'equations'=>$rows, 'count'=>count($rows)], 200);
    }

    public function rest_current_equations(WP_REST_Request $request) {
        return $this->rest_equations($request);
    }

    public function rest_analyze_equation(WP_REST_Request $request) {
        $payload = $request->get_json_params();
        $payload = is_array($payload) ? $payload : [];
        $res = $this->backend_post('/equations/analyze', $payload, true);
        if (is_wp_error($res)) {
            $equation = sanitize_textarea_field($payload['equation'] ?? '');
            $context = sanitize_textarea_field($payload['context'] ?? '');
            $suggest = $this->suggest_tools_for_equation($equation, $context);
            return new WP_REST_Response([
                'ok'=>true,
                'source'=>'wordpress-local-equation-analyzer',
                'equation'=>$equation,
                'summary'=>'Equation indexed locally. Backend equation analysis is unavailable, so this fallback provides deterministic tool recommendations only.',
                'suggested_domain'=>$suggest['domain'],
                'suggested_tools'=>$suggest['tools'],
                'graphability'=>'Unknown until backend analysis is reachable.',
                'warnings'=>['Run the FastAPI backend for richer equation explanation, graphing, and code translation.']
            ], 200);
        }
        return new WP_REST_Response($res, 200);
    }

    public function register_admin_menu() {
        add_menu_page('Sustainable Catalyst Workbench', 'SC Workbench', 'manage_options', 'sustainable-catalyst-workbench', [$this,'render_settings_page'], 'dashicons-chart-area', 58);
        add_submenu_page('sustainable-catalyst-workbench', 'Equation Registry', 'Equation Registry', 'manage_options', 'sustainable-catalyst-workbench-equations', [$this,'render_equations_page']);
        add_submenu_page('sustainable-catalyst-workbench', 'Calculator Backlog', 'Calculator Backlog', 'manage_options', 'sustainable-catalyst-workbench-calculator-backlog', [$this,'render_calculator_backlog_page']);
        add_submenu_page('sustainable-catalyst-workbench', 'Feature Builder', 'Feature Builder', 'manage_options', 'sustainable-catalyst-workbench-feature-builder', [$this,'render_feature_builder_page']);
        add_submenu_page('sustainable-catalyst-workbench', 'Embed Shortcodes', 'Embed Shortcodes', 'manage_options', 'sustainable-catalyst-workbench-embed-shortcodes', [$this,'render_embed_shortcodes_page']);
        add_submenu_page('sustainable-catalyst-workbench', 'Placement Assistant', 'Placement Assistant', 'manage_options', 'sustainable-catalyst-workbench-placement-assistant', [$this,'render_placement_assistant_page']);
        add_submenu_page('sustainable-catalyst-workbench', 'Validation Dashboard', 'Validation Dashboard', 'manage_options', 'sustainable-catalyst-workbench-validation-dashboard', [$this,'render_validation_dashboard_page']);
        add_submenu_page('sustainable-catalyst-workbench', 'Tool Catalog', 'Tool Catalog', 'manage_options', 'sustainable-catalyst-workbench-tool-catalog', [$this,'render_tool_catalog_page']);
    }

    public function handle_settings_save() {
        if (!is_admin() || !current_user_can('manage_options')) { return; }
        if (isset($_POST['sc_workbench_scan_equations'])) {
            check_admin_referer('sc_workbench_equations');
            $result = $this->scan_equations(2000);
            add_settings_error('sc_workbench_messages', 'equations_scanned', 'Equation scan complete: ' . intval($result['equations_indexed']) . ' equations indexed from ' . intval($result['posts_scanned']) . ' posts/pages.', 'updated');
            return;
        }
        if (isset($_POST['sc_workbench_clear_equations'])) {
            check_admin_referer('sc_workbench_equations');
            $this->clear_equation_registry();
            add_settings_error('sc_workbench_messages', 'equations_cleared', 'Equation registry cleared.', 'updated');
            return;
        }
        if (isset($_POST['sc_workbench_export_equations_csv'])) {
            check_admin_referer('sc_workbench_equations');
            $this->export_equation_registry_csv();
            exit;
        }
        if (isset($_POST['sc_workbench_import_calculator_backlog_seed'])) {
            check_admin_referer('sc_workbench_calculator_backlog');
            $result = $this->import_calculator_backlog_from_file($this->bundled_calculator_suggestions_csv(), true);
            add_settings_error('sc_workbench_messages', 'calculator_backlog_imported', 'Calculator backlog imported: ' . intval($result['imported']) . ' suggestions loaded.', 'updated');
            return;
        }
        if (isset($_POST['sc_workbench_upload_calculator_backlog_csv'])) {
            check_admin_referer('sc_workbench_calculator_backlog');
            if (!empty($_FILES['sc_workbench_calculator_backlog_csv']['tmp_name'])) {
                $result = $this->import_calculator_backlog_from_file($_FILES['sc_workbench_calculator_backlog_csv']['tmp_name'], true);
                add_settings_error('sc_workbench_messages', 'calculator_backlog_uploaded', 'Calculator backlog uploaded: ' . intval($result['imported']) . ' suggestions loaded.', 'updated');
            } else {
                add_settings_error('sc_workbench_messages', 'calculator_backlog_upload_missing', 'No CSV file was uploaded.', 'error');
            }
            return;
        }
        if (isset($_POST['sc_workbench_clear_calculator_backlog'])) {
            check_admin_referer('sc_workbench_calculator_backlog');
            $this->clear_calculator_backlog();
            add_settings_error('sc_workbench_messages', 'calculator_backlog_cleared', 'Calculator backlog cleared.', 'updated');
            return;
        }
        if (isset($_POST['sc_workbench_export_calculator_backlog_csv'])) {
            check_admin_referer('sc_workbench_calculator_backlog');
            $this->export_calculator_backlog_csv();
            exit;
        }

        if (isset($_POST['sc_workbench_import_feature_builder_seed'])) {
            check_admin_referer('sc_workbench_feature_builder');
            $result = $this->import_feature_builder_from_file($this->bundled_feature_builder_queue_csv(), true);
            add_settings_error('sc_workbench_messages', 'feature_builder_imported', 'Feature builder queue imported: ' . intval($result['imported']) . ' feature rows loaded.', 'updated');
            return;
        }
        if (isset($_POST['sc_workbench_upload_feature_builder_csv'])) {
            check_admin_referer('sc_workbench_feature_builder');
            if (!empty($_FILES['sc_workbench_feature_builder_csv']['tmp_name'])) {
                $result = $this->import_feature_builder_from_file($_FILES['sc_workbench_feature_builder_csv']['tmp_name'], true);
                add_settings_error('sc_workbench_messages', 'feature_builder_uploaded', 'Feature builder CSV uploaded: ' . intval($result['imported']) . ' feature rows loaded.', 'updated');
            } else {
                add_settings_error('sc_workbench_messages', 'feature_builder_upload_missing', 'No CSV file was uploaded.', 'error');
            }
            return;
        }
        if (isset($_POST['sc_workbench_clear_feature_builder'])) {
            check_admin_referer('sc_workbench_feature_builder');
            $this->clear_feature_builder_queue();
            add_settings_error('sc_workbench_messages', 'feature_builder_cleared', 'Feature builder queue cleared.', 'updated');
            return;
        }
        if (isset($_POST['sc_workbench_export_feature_builder_csv'])) {
            check_admin_referer('sc_workbench_feature_builder');
            $this->export_feature_builder_csv();
            exit;
        }

        if (isset($_POST['sc_workbench_build_shortcode_recommendations'])) {
            check_admin_referer('sc_workbench_embed_shortcodes');
            $result = $this->build_shortcode_recommendations();
            add_settings_error('sc_workbench_messages', 'shortcode_recommendations_built', 'Shortcode recommendations built: ' . intval($result['recommendations_built']) . ' pages/articles analyzed from ' . intval($result['equation_rows']) . ' indexed equations.', 'updated');
            return;
        }
        if (isset($_POST['sc_workbench_scan_and_build_shortcode_recommendations'])) {
            check_admin_referer('sc_workbench_embed_shortcodes');
            $scan = $this->scan_equations(3000);
            $result = $this->build_shortcode_recommendations();
            add_settings_error('sc_workbench_messages', 'shortcode_recommendations_scanned_built', 'Equation scan and shortcode build complete: ' . intval($scan['equations_indexed']) . ' equations indexed; ' . intval($result['recommendations_built']) . ' page-level calculator embeds recommended.', 'updated');
            return;
        }
        if (isset($_POST['sc_workbench_clear_shortcode_recommendations'])) {
            check_admin_referer('sc_workbench_embed_shortcodes');
            $this->clear_shortcode_recommendations();
            add_settings_error('sc_workbench_messages', 'shortcode_recommendations_cleared', 'Shortcode recommendations cleared.', 'updated');
            return;
        }
        if (isset($_POST['sc_workbench_export_shortcode_recommendations_csv'])) {
            check_admin_referer('sc_workbench_embed_shortcodes');
            $this->export_shortcode_recommendations_csv();
            exit;
        }
        if (!isset($_POST['sc_workbench_save_settings'])) { return; }
        check_admin_referer('sc_workbench_settings');
        update_option(self::OPTION_BACKEND_URL, esc_url_raw($_POST[self::OPTION_BACKEND_URL] ?? ''));
        update_option(self::OPTION_BACKEND_KEY, sanitize_text_field($_POST[self::OPTION_BACKEND_KEY] ?? ''));
        $provider = sanitize_key($_POST[self::OPTION_AI_PROVIDER] ?? 'backend');
        if (!in_array($provider, ['backend','disabled','gemini','deepseek','openai'], true)) { $provider = 'backend'; }
        update_option(self::OPTION_AI_PROVIDER, $provider);
        update_option(self::OPTION_ENABLE_AI, isset($_POST[self::OPTION_ENABLE_AI]) ? '1' : '0');
        update_option(self::OPTION_ENABLE_SCOPE_GATE, isset($_POST[self::OPTION_ENABLE_SCOPE_GATE]) ? '1' : '0');
        update_option(self::OPTION_DEBUG, isset($_POST[self::OPTION_DEBUG]) ? '1' : '0');
        update_option(self::OPTION_TIMEOUT, max(5, min(120, intval($_POST[self::OPTION_TIMEOUT] ?? 45))));
        update_option(self::OPTION_DEFAULT_TOPIC, sanitize_key($_POST[self::OPTION_DEFAULT_TOPIC] ?? 'research-library'));
        update_option(self::OPTION_THEME, sanitize_key($_POST[self::OPTION_THEME] ?? 'institutional'));
        $new_key = trim((string)($_POST['sc_workbench_provider_key_plain'] ?? ($_POST['sc_workbench_openai_key_plain'] ?? '')));
        if ($new_key !== '') {
            update_option(self::OPTION_PROVIDER_KEY, $this->encrypt($new_key));
            update_option(self::OPTION_PROVIDER_KEY_SET, '1');
        }
        if (isset($_POST['sc_workbench_clear_openai_key'])) {
            delete_option(self::OPTION_PROVIDER_KEY);
            update_option(self::OPTION_PROVIDER_KEY_SET, '0');
        }
        add_settings_error('sc_workbench_messages', 'saved', 'Workbench settings saved.', 'updated');
    }

    private function export_equation_registry_csv() {
        if (!current_user_can('manage_options')) { wp_die('Unauthorized'); }
        global $wpdb;
        self::create_equation_table();
        $table = self::equation_table_name();
        $rows = $wpdb->get_results("SELECT * FROM {$table} ORDER BY post_title ASC, id ASC", ARRAY_A);
        $filename = 'sustainable-catalyst-equation-registry-' . gmdate('Ymd-His') . '.csv';
        nocache_headers();
        header('Content-Type: text/csv; charset=utf-8');
        header('Content-Disposition: attachment; filename=' . $filename);
        $out = fopen('php://output', 'w');
        fputcsv($out, [
            'id', 'post_id', 'post_title', 'post_slug', 'post_type', 'permalink',
            'display_mode', 'equation_normalized', 'equation_raw', 'suggested_domain',
            'suggested_tools', 'context_before', 'context_after', 'equation_hash',
            'created_at', 'updated_at'
        ]);
        foreach ($rows as $row) {
            $tools = json_decode($row['suggested_tools'] ?: '[]', true);
            if (!is_array($tools)) { $tools = []; }
            fputcsv($out, [
                $row['id'] ?? '',
                $row['post_id'] ?? '',
                $row['post_title'] ?? '',
                $row['post_slug'] ?? '',
                $row['post_type'] ?? '',
                !empty($row['post_id']) ? get_permalink(intval($row['post_id'])) : '',
                $row['display_mode'] ?? '',
                $row['equation_normalized'] ?? '',
                $row['equation_raw'] ?? '',
                $row['suggested_domain'] ?? '',
                implode('|', $tools),
                $row['context_before'] ?? '',
                $row['context_after'] ?? '',
                $row['equation_hash'] ?? '',
                $row['created_at'] ?? '',
                $row['updated_at'] ?? '',
            ]);
        }
        fclose($out);
    }

    public function render_settings_page() {
        settings_errors('sc_workbench_messages'); ?>
        <div class="wrap scwb-admin-wrap">
            <h1>Sustainable Catalyst Workbench Settings</h1>
            <p>Configure the compact Workbench interface, advanced analytics backend, AI provider key handling, scope gate, and production defaults.</p>
            <form method="post">
                <?php wp_nonce_field('sc_workbench_settings'); ?>
                <input type="hidden" name="sc_workbench_save_settings" value="1" />
                <div class="scwb-admin-grid">
                    <section class="scwb-admin-card"><h2>Backend API</h2>
                        <label>Backend URL <input type="url" name="<?php echo esc_attr(self::OPTION_BACKEND_URL); ?>" value="<?php echo esc_attr(get_option(self::OPTION_BACKEND_URL, 'http://127.0.0.1:8088')); ?>" /></label>
                        <label>Shared backend key <input type="password" name="<?php echo esc_attr(self::OPTION_BACKEND_KEY); ?>" value="<?php echo esc_attr(get_option(self::OPTION_BACKEND_KEY, '')); ?>" autocomplete="off" /></label>
                        <label>Timeout seconds <input type="number" name="<?php echo esc_attr(self::OPTION_TIMEOUT); ?>" value="<?php echo esc_attr(get_option(self::OPTION_TIMEOUT, 45)); ?>" min="5" max="120" /></label>
                    </section>
                    <section class="scwb-admin-card"><h2>AI & Scope</h2>
                        <label>AI provider
                            <select name="<?php echo esc_attr(self::OPTION_AI_PROVIDER); ?>">
                                <option value="backend" <?php selected(get_option(self::OPTION_AI_PROVIDER, 'backend'), 'backend'); ?>>Use backend .env setting</option>
                                <option value="disabled" <?php selected(get_option(self::OPTION_AI_PROVIDER, 'backend'), 'disabled'); ?>>Disabled</option>
                                <option value="gemini" <?php selected(get_option(self::OPTION_AI_PROVIDER, 'backend'), 'gemini'); ?>>Gemini</option>
                                <option value="deepseek" <?php selected(get_option(self::OPTION_AI_PROVIDER, 'backend'), 'deepseek'); ?>>DeepSeek</option>
                                <option value="openai" <?php selected(get_option(self::OPTION_AI_PROVIDER, 'backend'), 'openai'); ?>>OpenAI</option>
                            </select>
                        </label>
                        <label><input type="checkbox" name="<?php echo esc_attr(self::OPTION_ENABLE_AI); ?>" <?php checked(get_option(self::OPTION_ENABLE_AI, '1'), '1'); ?> /> Enable AI panels</label>
                        <label><input type="checkbox" name="<?php echo esc_attr(self::OPTION_ENABLE_SCOPE_GATE); ?>" <?php checked(get_option(self::OPTION_ENABLE_SCOPE_GATE, '1'), '1'); ?> /> Enable Sustainable Catalyst scope gate</label>
                        <label><input type="checkbox" name="<?php echo esc_attr(self::OPTION_DEBUG); ?>" <?php checked(get_option(self::OPTION_DEBUG, '0'), '1'); ?> /> Debug mode</label>
                        <label>Provider API key <input type="password" name="sc_workbench_provider_key_plain" value="" placeholder="Paste Gemini, DeepSeek, or OpenAI key only if WordPress forwards it" autocomplete="off" /></label>
                        <p class="description">Key saved: <?php echo get_option(self::OPTION_PROVIDER_KEY_SET, '0') === '1' ? 'Yes' : 'No'; ?>. Prefer backend .env for production; use HTTPS if WordPress forwards a provider key.</p>
                        <label><input type="checkbox" name="sc_workbench_clear_openai_key" /> Clear saved provider key</label>
                    </section>
                    <section class="scwb-admin-card"><h2>Frontend Defaults</h2>
                        <label>Default topic <input type="text" name="<?php echo esc_attr(self::OPTION_DEFAULT_TOPIC); ?>" value="<?php echo esc_attr(get_option(self::OPTION_DEFAULT_TOPIC, 'research-library')); ?>" /></label>
                        <label>Theme <select name="<?php echo esc_attr(self::OPTION_THEME); ?>"><option value="institutional" <?php selected(get_option(self::OPTION_THEME), 'institutional'); ?>>Institutional</option><option value="compact" <?php selected(get_option(self::OPTION_THEME), 'compact'); ?>>Compact</option></select></label>
                    </section>
                    <section class="scwb-admin-card"><h2>Status</h2>
                        <button type="button" class="button button-primary" data-scwb-admin-test>Test Backend + AI</button>
                        <pre data-scwb-admin-output>Not tested yet.</pre>
                    </section>
                </div>
                <?php submit_button('Save Workbench Settings'); ?>
            </form>
            <section class="scwb-admin-card"><h2>Shortcodes</h2><code>[sc_workbench topic="research-library" title="Ask the Sustainable Catalyst Workbench"]</code><br><code>[sc_workbench mode="library" topic="research-library"]</code><br><code>[sc_workbench mode="auto"]</code><br><code>[sc_workbench article="article-slug"]</code><br><code>[sc_workbench_pathways]</code><br><code>[sc_workbench_chalkboard title="Chalkboard Translator"]</code><br><code>[sc_workbench_graph_studio title="Graph Studio"]</code><br><code>[sc_workbench mode="tool" display="compact" tool="systems-modeling-tool" article="article-slug"]</code><p><a href="<?php echo esc_url(admin_url('admin.php?page=sustainable-catalyst-workbench-equations')); ?>">Open Equation Registry →</a> · <a href="<?php echo esc_url(admin_url('admin.php?page=sustainable-catalyst-workbench-feature-builder')); ?>">Open Feature Builder →</a> · <a href="<?php echo esc_url(admin_url('admin.php?page=sustainable-catalyst-workbench-embed-shortcodes')); ?>">Open Embed Shortcodes →</a> · <a href="<?php echo esc_url(admin_url('admin.php?page=sustainable-catalyst-workbench-placement-assistant')); ?>">Open Placement Assistant →</a> · <a href="<?php echo esc_url(admin_url('admin.php?page=sustainable-catalyst-workbench-validation-dashboard')); ?>">Open Validation Dashboard →</a></p></section>
        </div>
    <?php }


    private static function calculator_backlog_table_name() {
        global $wpdb;
        return $wpdb->prefix . 'sc_workbench_calculator_backlog';
    }

    public static function create_calculator_backlog_table() {
        global $wpdb;
        $table = self::calculator_backlog_table_name();
        $charset = $wpdb->get_charset_collate();
        require_once ABSPATH . 'wp-admin/includes/upgrade.php';
        $sql = "CREATE TABLE {$table} (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            priority VARCHAR(16) NOT NULL,
            calculator_id VARCHAR(160) NOT NULL,
            calculator_name TEXT NOT NULL,
            category VARCHAR(255) NULL,
            estimated_matching_equations BIGINT UNSIGNED DEFAULT 0,
            example_equations_from_registry LONGTEXT NULL,
            why_build_it LONGTEXT NULL,
            recommended_inputs LONGTEXT NULL,
            recommended_outputs LONGTEXT NULL,
            implementation_notes LONGTEXT NULL,
            status VARCHAR(64) NOT NULL DEFAULT 'proposed',
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY  (id),
            UNIQUE KEY calculator_id_unique (calculator_id),
            KEY priority_idx (priority),
            KEY category_idx (category),
            KEY status_idx (status)
        ) {$charset};";
        dbDelta($sql);
    }

    private function bundled_calculator_suggestions_csv() {
        return plugin_dir_path(__FILE__) . 'data/calculator_suggestions_from_equation_registry.csv';
    }

    private function calculator_backlog_count() {
        global $wpdb;
        self::create_calculator_backlog_table();
        $table = self::calculator_backlog_table_name();
        return intval($wpdb->get_var("SELECT COUNT(*) FROM {$table}"));
    }

    private function clear_calculator_backlog() {
        global $wpdb;
        self::create_calculator_backlog_table();
        $table = self::calculator_backlog_table_name();
        $wpdb->query('TRUNCATE TABLE ' . $table);
    }

    private function import_calculator_backlog_from_file($path, $replace=true) {
        global $wpdb;
        self::create_calculator_backlog_table();
        if (!$path || !file_exists($path) || !is_readable($path)) {
            return ['ok'=>false, 'imported'=>0, 'error'=>'CSV file not found or not readable.'];
        }
        if ($replace) { $this->clear_calculator_backlog(); }
        $table = self::calculator_backlog_table_name();
        $handle = fopen($path, 'r');
        if (!$handle) { return ['ok'=>false, 'imported'=>0, 'error'=>'Could not open CSV file.']; }
        $header = fgetcsv($handle);
        if (!$header) { fclose($handle); return ['ok'=>false, 'imported'=>0, 'error'=>'CSV has no header row.']; }
        $header = array_map(function($h){ return sanitize_key($h); }, $header);
        $imported = 0;
        $now = current_time('mysql');
        while (($row = fgetcsv($handle)) !== false) {
            $data = [];
            foreach ($header as $i => $key) { $data[$key] = isset($row[$i]) ? $row[$i] : ''; }
            $calculator_id = sanitize_title($data['calculator_id'] ?? '');
            if (!$calculator_id) { continue; }
            $payload = [
                'priority' => sanitize_text_field($data['priority'] ?? 'P2'),
                'calculator_id' => $calculator_id,
                'calculator_name' => sanitize_text_field($data['calculator_name'] ?? $calculator_id),
                'category' => sanitize_text_field($data['category'] ?? ''),
                'estimated_matching_equations' => max(0, intval($data['estimated_matching_equations'] ?? 0)),
                'example_equations_from_registry' => sanitize_textarea_field($data['example_equations_from_registry'] ?? ''),
                'why_build_it' => sanitize_textarea_field($data['why_build_it'] ?? ''),
                'recommended_inputs' => sanitize_textarea_field($data['recommended_inputs'] ?? ''),
                'recommended_outputs' => sanitize_textarea_field($data['recommended_outputs'] ?? ''),
                'implementation_notes' => sanitize_textarea_field($data['implementation_notes'] ?? ''),
                'status' => sanitize_key($data['status'] ?? 'proposed') ?: 'proposed',
                'created_at' => $now,
                'updated_at' => $now,
            ];
            $wpdb->replace($table, $payload, ['%s','%s','%s','%s','%d','%s','%s','%s','%s','%s','%s','%s','%s']);
            $imported++;
        }
        fclose($handle);
        return ['ok'=>true, 'imported'=>$imported];
    }

    private function calculator_backlog_rows($limit=500) {
        global $wpdb;
        self::create_calculator_backlog_table();
        $table = self::calculator_backlog_table_name();
        $limit = max(1, min(1000, intval($limit)));
        return $wpdb->get_results($wpdb->prepare("SELECT * FROM {$table} ORDER BY FIELD(priority,'P0','P1','P2','P3'), estimated_matching_equations DESC, calculator_name ASC LIMIT %d", $limit), ARRAY_A);
    }

    private function calculator_backlog_summary() {
        global $wpdb;
        self::create_calculator_backlog_table();
        $table = self::calculator_backlog_table_name();
        $total = intval($wpdb->get_var("SELECT COUNT(*) FROM {$table}"));
        $by_priority = $wpdb->get_results("SELECT priority, COUNT(*) AS count, SUM(estimated_matching_equations) AS equation_matches FROM {$table} GROUP BY priority ORDER BY FIELD(priority,'P0','P1','P2','P3')", ARRAY_A);
        $by_category = $wpdb->get_results("SELECT category, COUNT(*) AS count, SUM(estimated_matching_equations) AS equation_matches FROM {$table} GROUP BY category ORDER BY equation_matches DESC, count DESC LIMIT 20", ARRAY_A);
        return ['total'=>$total, 'by_priority'=>$by_priority, 'by_category'=>$by_category];
    }

    public function rest_calculator_backlog(WP_REST_Request $request) {
        $limit = min(500, max(1, intval($request->get_param('limit') ?: 120)));
        return new WP_REST_Response(['ok'=>true, 'summary'=>$this->calculator_backlog_summary(), 'suggestions'=>$this->calculator_backlog_rows($limit)], 200);
    }

    private function export_calculator_backlog_csv() {
        if (!current_user_can('manage_options')) { wp_die('Unauthorized'); }
        $rows = $this->calculator_backlog_rows(1000);
        $filename = 'sustainable-catalyst-calculator-backlog-' . gmdate('Ymd-His') . '.csv';
        nocache_headers();
        header('Content-Type: text/csv; charset=utf-8');
        header('Content-Disposition: attachment; filename=' . $filename);
        $out = fopen('php://output', 'w');
        fputcsv($out, ['priority','calculator_id','calculator_name','category','estimated_matching_equations','example_equations_from_registry','why_build_it','recommended_inputs','recommended_outputs','implementation_notes','status']);
        foreach ($rows as $row) {
            fputcsv($out, [
                $row['priority'] ?? '', $row['calculator_id'] ?? '', $row['calculator_name'] ?? '', $row['category'] ?? '',
                $row['estimated_matching_equations'] ?? 0, $row['example_equations_from_registry'] ?? '', $row['why_build_it'] ?? '',
                $row['recommended_inputs'] ?? '', $row['recommended_outputs'] ?? '', $row['implementation_notes'] ?? '', $row['status'] ?? 'proposed'
            ]);
        }
        fclose($out);
    }


    private static function feature_builder_table_name() {
        global $wpdb;
        return $wpdb->prefix . 'sc_workbench_feature_builder';
    }

    public static function create_feature_builder_table() {
        global $wpdb;
        $table = self::feature_builder_table_name();
        $charset = $wpdb->get_charset_collate();
        require_once ABSPATH . 'wp-admin/includes/upgrade.php';
        $sql = "CREATE TABLE {$table} (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            build_order BIGINT UNSIGNED DEFAULT 0,
            priority VARCHAR(16) NOT NULL,
            feature_id VARCHAR(180) NOT NULL,
            feature_name TEXT NOT NULL,
            feature_type VARCHAR(120) NULL,
            category VARCHAR(255) NULL,
            source_signal VARCHAR(255) NULL,
            estimated_matching_equations BIGINT UNSIGNED DEFAULT 0,
            article_count BIGINT UNSIGNED DEFAULT 0,
            example_equations LONGTEXT NULL,
            source_articles LONGTEXT NULL,
            why_build_it LONGTEXT NULL,
            recommended_inputs LONGTEXT NULL,
            recommended_outputs LONGTEXT NULL,
            recommended_backend LONGTEXT NULL,
            recommended_ui LONGTEXT NULL,
            first_mvp_scope LONGTEXT NULL,
            depends_on LONGTEXT NULL,
            status VARCHAR(64) NOT NULL DEFAULT 'proposed',
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY  (id),
            UNIQUE KEY feature_id_unique (feature_id),
            KEY priority_idx (priority),
            KEY category_idx (category),
            KEY status_idx (status)
        ) {$charset};";
        dbDelta($sql);
    }

    private function bundled_feature_builder_queue_csv() {
        return plugin_dir_path(__FILE__) . 'data/workbench_feature_build_queue_v0.9.7.csv';
    }
    private function bundled_article_profiles_csv() {
        return plugin_dir_path(__FILE__) . 'data/article_tool_profiles_v0.9.7.csv';
    }
    private function bundled_domain_summary_csv() {
        return plugin_dir_path(__FILE__) . 'data/equation_domain_summary_v0.9.7.csv';
    }
    private function bundled_feature_clusters_csv() {
        return plugin_dir_path(__FILE__) . 'data/equation_feature_clusters_v0.9.7.csv';
    }

    private function feature_builder_count() {
        global $wpdb;
        self::create_feature_builder_table();
        $table = self::feature_builder_table_name();
        return intval($wpdb->get_var("SELECT COUNT(*) FROM {$table}"));
    }

    private function clear_feature_builder_queue() {
        global $wpdb;
        self::create_feature_builder_table();
        $table = self::feature_builder_table_name();
        $wpdb->query('TRUNCATE TABLE ' . $table);
    }

    private function import_feature_builder_from_file($path, $replace=true) {
        global $wpdb;
        self::create_feature_builder_table();
        if (!$path || !file_exists($path) || !is_readable($path)) {
            return ['ok'=>false, 'imported'=>0, 'error'=>'CSV file not found or not readable.'];
        }
        if ($replace) { $this->clear_feature_builder_queue(); }
        $table = self::feature_builder_table_name();
        $handle = fopen($path, 'r');
        if (!$handle) { return ['ok'=>false, 'imported'=>0, 'error'=>'Could not open CSV file.']; }
        $header = fgetcsv($handle);
        if (!$header) { fclose($handle); return ['ok'=>false, 'imported'=>0, 'error'=>'CSV has no header row.']; }
        $header = array_map(function($h){ return sanitize_key($h); }, $header);
        $imported = 0;
        $now = current_time('mysql');
        while (($row = fgetcsv($handle)) !== false) {
            $data = [];
            foreach ($header as $i => $key) { $data[$key] = isset($row[$i]) ? $row[$i] : ''; }
            $feature_id = sanitize_title($data['feature_id'] ?? '');
            if (!$feature_id) { continue; }
            $payload = [
                'build_order' => max(0, intval($data['build_order'] ?? 0)),
                'priority' => sanitize_text_field($data['priority'] ?? 'P2'),
                'feature_id' => $feature_id,
                'feature_name' => sanitize_text_field($data['feature_name'] ?? $feature_id),
                'feature_type' => sanitize_text_field($data['feature_type'] ?? ''),
                'category' => sanitize_text_field($data['category'] ?? ''),
                'source_signal' => sanitize_text_field($data['source_signal'] ?? ''),
                'estimated_matching_equations' => max(0, intval($data['estimated_matching_equations'] ?? 0)),
                'article_count' => max(0, intval($data['article_count'] ?? 0)),
                'example_equations' => sanitize_textarea_field($data['example_equations'] ?? ''),
                'source_articles' => sanitize_textarea_field($data['source_articles'] ?? ''),
                'why_build_it' => sanitize_textarea_field($data['why_build_it'] ?? ''),
                'recommended_inputs' => sanitize_textarea_field($data['recommended_inputs'] ?? ''),
                'recommended_outputs' => sanitize_textarea_field($data['recommended_outputs'] ?? ''),
                'recommended_backend' => sanitize_textarea_field($data['recommended_backend'] ?? ''),
                'recommended_ui' => sanitize_textarea_field($data['recommended_ui'] ?? ''),
                'first_mvp_scope' => sanitize_textarea_field($data['first_mvp_scope'] ?? ''),
                'depends_on' => sanitize_textarea_field($data['depends_on'] ?? ''),
                'status' => sanitize_key($data['status'] ?? 'proposed') ?: 'proposed',
                'created_at' => $now,
                'updated_at' => $now,
            ];
            $wpdb->replace($table, $payload, ['%d','%s','%s','%s','%s','%s','%s','%d','%d','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s']);
            $imported++;
        }
        fclose($handle);
        return ['ok'=>true, 'imported'=>$imported];
    }

    private function feature_builder_rows($limit=500) {
        global $wpdb;
        self::create_feature_builder_table();
        $table = self::feature_builder_table_name();
        $limit = max(1, min(1000, intval($limit)));
        return $wpdb->get_results($wpdb->prepare("SELECT * FROM {$table} ORDER BY FIELD(priority,'P0','P1','P2','P3'), estimated_matching_equations DESC, build_order ASC LIMIT %d", $limit), ARRAY_A);
    }

    private function feature_builder_summary() {
        global $wpdb;
        self::create_feature_builder_table();
        $table = self::feature_builder_table_name();
        $total = intval($wpdb->get_var("SELECT COUNT(*) FROM {$table}"));
        $by_priority = $wpdb->get_results("SELECT priority, COUNT(*) AS count, SUM(estimated_matching_equations) AS equation_matches, SUM(article_count) AS article_matches FROM {$table} GROUP BY priority ORDER BY FIELD(priority,'P0','P1','P2','P3')", ARRAY_A);
        $by_category = $wpdb->get_results("SELECT category, COUNT(*) AS count, SUM(estimated_matching_equations) AS equation_matches FROM {$table} GROUP BY category ORDER BY equation_matches DESC, count DESC LIMIT 25", ARRAY_A);
        return ['total'=>$total, 'by_priority'=>$by_priority, 'by_category'=>$by_category];
    }

    public function rest_feature_builder(WP_REST_Request $request) {
        $limit = min(500, max(1, intval($request->get_param('limit') ?: 120)));
        return new WP_REST_Response(['ok'=>true, 'summary'=>$this->feature_builder_summary(), 'features'=>$this->feature_builder_rows($limit)], 200);
    }

    private function export_feature_builder_csv() {
        if (!current_user_can('manage_options')) { wp_die('Unauthorized'); }
        $rows = $this->feature_builder_rows(1000);
        $filename = 'sustainable-catalyst-feature-builder-' . gmdate('Ymd-His') . '.csv';
        nocache_headers();
        header('Content-Type: text/csv; charset=utf-8');
        header('Content-Disposition: attachment; filename=' . $filename);
        $out = fopen('php://output', 'w');
        fputcsv($out, ['build_order','priority','feature_id','feature_name','feature_type','category','source_signal','estimated_matching_equations','article_count','example_equations','source_articles','why_build_it','recommended_inputs','recommended_outputs','recommended_backend','recommended_ui','first_mvp_scope','depends_on','status']);
        foreach ($rows as $row) {
            fputcsv($out, [
                $row['build_order'] ?? 0, $row['priority'] ?? '', $row['feature_id'] ?? '', $row['feature_name'] ?? '', $row['feature_type'] ?? '', $row['category'] ?? '', $row['source_signal'] ?? '',
                $row['estimated_matching_equations'] ?? 0, $row['article_count'] ?? 0, $row['example_equations'] ?? '', $row['source_articles'] ?? '', $row['why_build_it'] ?? '',
                $row['recommended_inputs'] ?? '', $row['recommended_outputs'] ?? '', $row['recommended_backend'] ?? '', $row['recommended_ui'] ?? '', $row['first_mvp_scope'] ?? '', $row['depends_on'] ?? '', $row['status'] ?? 'proposed'
            ]);
        }
        fclose($out);
    }

    private function count_csv_rows($path) {
        if (!$path || !file_exists($path) || !is_readable($path)) { return 0; }
        $handle = fopen($path, 'r');
        if (!$handle) { return 0; }
        $count = 0; $first = true;
        while (($row = fgetcsv($handle)) !== false) { if ($first) { $first = false; continue; } $count++; }
        fclose($handle);
        return $count;
    }

    public function render_feature_builder_page() {
        settings_errors('sc_workbench_messages');
        self::create_feature_builder_table();
        if (!$this->feature_builder_count()) {
            $this->import_feature_builder_from_file($this->bundled_feature_builder_queue_csv(), true);
        }
        $summary = $this->feature_builder_summary();
        $rows = $this->feature_builder_rows(250);
        $plugin_url = plugin_dir_url(__FILE__);
        ?>
        <div class="wrap scwb-admin-wrap">
            <h1>Sustainable Catalyst Workbench Feature Builder</h1>
            <p>Use the latest equation registry and calculator backlog to turn article equations into implementable Workbench features, article tool profiles, calculator modules, and future backend work.</p>
            <div class="scwb-admin-grid">
                <section class="scwb-admin-card">
                    <h2>Feature Queue Controls</h2>
                    <p><strong><?php echo esc_html($summary['total']); ?></strong> feature rows loaded from the equation-derived build queue.</p>
                    <form method="post" style="display:inline-block;margin-right:12px;">
                        <?php wp_nonce_field('sc_workbench_feature_builder'); ?>
                        <input type="hidden" name="sc_workbench_import_feature_builder_seed" value="1" />
                        <?php submit_button('Import Bundled Feature Queue', 'primary', 'submit', false); ?>
                    </form>
                    <form method="post" style="display:inline-block;margin-right:12px;" onsubmit="return confirm('Clear feature builder queue?');">
                        <?php wp_nonce_field('sc_workbench_feature_builder'); ?>
                        <input type="hidden" name="sc_workbench_clear_feature_builder" value="1" />
                        <?php submit_button('Clear Queue', 'secondary', 'submit', false); ?>
                    </form>
                    <form method="post" style="display:inline-block;">
                        <?php wp_nonce_field('sc_workbench_feature_builder'); ?>
                        <input type="hidden" name="sc_workbench_export_feature_builder_csv" value="1" />
                        <?php submit_button('Export Feature Queue CSV', 'secondary', 'submit', false); ?>
                    </form>
                </section>
                <section class="scwb-admin-card">
                    <h2>Upload Revised Feature CSV</h2>
                    <form method="post" enctype="multipart/form-data">
                        <?php wp_nonce_field('sc_workbench_feature_builder'); ?>
                        <input type="hidden" name="sc_workbench_upload_feature_builder_csv" value="1" />
                        <input type="file" name="sc_workbench_feature_builder_csv" accept=".csv,text/csv" />
                        <?php submit_button('Upload and Replace Feature Queue', 'secondary', 'submit', false); ?>
                    </form>
                    <p class="description">This lets you edit the feature queue externally and re-import it as the Workbench roadmap evolves.</p>
                </section>
                <section class="scwb-admin-card">
                    <h2>Bundled Analysis Files</h2>
                    <ul>
                        <li><a href="<?php echo esc_url($plugin_url . 'data/workbench_feature_build_queue_v0.9.7.csv'); ?>" target="_blank" rel="noopener">Feature build queue CSV</a> — <?php echo esc_html($this->count_csv_rows($this->bundled_feature_builder_queue_csv())); ?> rows</li>
                        <li><a href="<?php echo esc_url($plugin_url . 'data/sustainable-catalyst-feature-builder-built-v0.9.8.csv'); ?>" target="_blank" rel="noopener">Built feature tools CSV v0.9.8</a> — 59 rows implemented as calculator tools</li>
                        <li><a href="<?php echo esc_url($plugin_url . 'data/built_feature_tools_manifest_v0.9.8.json'); ?>" target="_blank" rel="noopener">Built feature tools manifest JSON</a></li>
                        <li><a href="<?php echo esc_url($plugin_url . 'data/article_tool_profiles_v0.9.7.csv'); ?>" target="_blank" rel="noopener">Article tool profiles CSV</a> — <?php echo esc_html($this->count_csv_rows($this->bundled_article_profiles_csv())); ?> rows</li>
                        <li><a href="<?php echo esc_url($plugin_url . 'data/equation_domain_summary_v0.9.7.csv'); ?>" target="_blank" rel="noopener">Equation domain summary CSV</a> — <?php echo esc_html($this->count_csv_rows($this->bundled_domain_summary_csv())); ?> rows</li>
                        <li><a href="<?php echo esc_url($plugin_url . 'data/equation_feature_clusters_v0.9.7.csv'); ?>" target="_blank" rel="noopener">Equation feature clusters CSV</a> — <?php echo esc_html($this->count_csv_rows($this->bundled_feature_clusters_csv())); ?> rows</li>
                    </ul>
                </section>
            </div>
            <h2>Priority Summary</h2>
            <table class="widefat striped">
                <thead><tr><th>Priority</th><th>Feature Count</th><th>Estimated Equation Matches</th><th>Article Matches</th></tr></thead>
                <tbody>
                    <?php foreach ($summary['by_priority'] as $p): ?>
                        <tr><td><strong><?php echo esc_html($p['priority']); ?></strong></td><td><?php echo esc_html($p['count']); ?></td><td><?php echo esc_html(number_format_i18n(intval($p['equation_matches']))); ?></td><td><?php echo esc_html(number_format_i18n(intval($p['article_matches']))); ?></td></tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
            <h2>Equation-Derived Feature Queue</h2>
            <table class="widefat striped">
                <thead><tr><th>Order</th><th>Priority</th><th>Feature</th><th>Category</th><th>Evidence</th><th>Build Notes</th></tr></thead>
                <tbody>
                <?php if (!$rows): ?>
                    <tr><td colspan="6">No feature rows loaded.</td></tr>
                <?php else: foreach ($rows as $row): ?>
                    <tr>
                        <td><?php echo esc_html($row['build_order']); ?></td>
                        <td><strong><?php echo esc_html($row['priority']); ?></strong><br><small><?php echo esc_html($row['status']); ?></small></td>
                        <td><strong><?php echo esc_html($row['feature_name']); ?></strong><br><code><?php echo esc_html($row['feature_id']); ?></code><br><small><?php echo esc_html($row['feature_type']); ?></small></td>
                        <td><?php echo esc_html($row['category']); ?><br><small><?php echo esc_html($row['source_signal']); ?></small></td>
                        <td><strong>Equations:</strong> <?php echo esc_html(number_format_i18n(intval($row['estimated_matching_equations']))); ?><br><strong>Articles:</strong> <?php echo esc_html(number_format_i18n(intval($row['article_count']))); ?><br><small><?php echo esc_html($row['example_equations']); ?></small></td>
                        <td><strong>Why:</strong> <?php echo esc_html($row['why_build_it']); ?><br><strong>Inputs:</strong> <?php echo esc_html($row['recommended_inputs']); ?><br><strong>Outputs:</strong> <?php echo esc_html($row['recommended_outputs']); ?><br><em><?php echo esc_html($row['first_mvp_scope']); ?></em></td>
                    </tr>
                <?php endforeach; endif; ?>
                </tbody>
            </table>
        </div>
    <?php }

    public function render_calculator_backlog_page() {
        settings_errors('sc_workbench_messages');
        self::create_calculator_backlog_table();
        if (!$this->calculator_backlog_count()) {
            $this->import_calculator_backlog_from_file($this->bundled_calculator_suggestions_csv(), true);
        }
        $summary = $this->calculator_backlog_summary();
        $rows = $this->calculator_backlog_rows(200);
        ?>
        <div class="wrap scwb-admin-wrap">
            <h1>Sustainable Catalyst Workbench Calculator Backlog</h1>
            <p>Turn the equation-registry CSV into an admin-visible feature map for building article-aware calculators, graphing tools, model routers, and Workbench modules.</p>
            <div class="scwb-admin-grid">
                <section class="scwb-admin-card">
                    <h2>Backlog Controls</h2>
                    <p><strong><?php echo esc_html($summary['total']); ?></strong> calculator suggestions loaded.</p>
                    <form method="post" style="display:inline-block;margin-right:12px;">
                        <?php wp_nonce_field('sc_workbench_calculator_backlog'); ?>
                        <input type="hidden" name="sc_workbench_import_calculator_backlog_seed" value="1" />
                        <?php submit_button('Import Bundled Suggestions', 'primary', 'submit', false); ?>
                    </form>
                    <form method="post" style="display:inline-block;margin-right:12px;" onsubmit="return confirm('Clear calculator backlog?');">
                        <?php wp_nonce_field('sc_workbench_calculator_backlog'); ?>
                        <input type="hidden" name="sc_workbench_clear_calculator_backlog" value="1" />
                        <?php submit_button('Clear Backlog', 'secondary', 'submit', false); ?>
                    </form>
                    <form method="post" style="display:inline-block;">
                        <?php wp_nonce_field('sc_workbench_calculator_backlog'); ?>
                        <input type="hidden" name="sc_workbench_export_calculator_backlog_csv" value="1" />
                        <?php submit_button('Export Backlog CSV', 'secondary', 'submit', false); ?>
                    </form>
                </section>
                <section class="scwb-admin-card">
                    <h2>Upload Updated CSV</h2>
                    <form method="post" enctype="multipart/form-data">
                        <?php wp_nonce_field('sc_workbench_calculator_backlog'); ?>
                        <input type="hidden" name="sc_workbench_upload_calculator_backlog_csv" value="1" />
                        <input type="file" name="sc_workbench_calculator_backlog_csv" accept=".csv,text/csv" />
                        <?php submit_button('Upload and Replace Backlog', 'secondary', 'submit', false); ?>
                    </form>
                    <p class="description">Expected columns: <code>priority</code>, <code>calculator_id</code>, <code>calculator_name</code>, <code>category</code>, <code>estimated_matching_equations</code>, <code>example_equations_from_registry</code>, <code>why_build_it</code>, <code>recommended_inputs</code>, <code>recommended_outputs</code>, <code>implementation_notes</code>.</p>
                </section>
            </div>
            <h2>Priority Summary</h2>
            <table class="widefat striped">
                <thead><tr><th>Priority</th><th>Suggestion Count</th><th>Estimated Equation Matches</th></tr></thead>
                <tbody>
                    <?php foreach ($summary['by_priority'] as $p): ?>
                        <tr><td><strong><?php echo esc_html($p['priority']); ?></strong></td><td><?php echo esc_html($p['count']); ?></td><td><?php echo esc_html(number_format_i18n(intval($p['equation_matches']))); ?></td></tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
            <h2>Feature Map</h2>
            <table class="widefat striped">
                <thead><tr><th>Priority</th><th>Calculator</th><th>Category</th><th>Equation Matches</th><th>Why Build It</th><th>Inputs / Outputs</th></tr></thead>
                <tbody>
                <?php if (!$rows): ?>
                    <tr><td colspan="6">No calculator suggestions loaded.</td></tr>
                <?php else: foreach ($rows as $row): ?>
                    <tr>
                        <td><strong><?php echo esc_html($row['priority']); ?></strong><br><small><?php echo esc_html($row['status']); ?></small></td>
                        <td><strong><?php echo esc_html($row['calculator_name']); ?></strong><br><code><?php echo esc_html($row['calculator_id']); ?></code><br><small><?php echo esc_html($row['example_equations_from_registry']); ?></small></td>
                        <td><?php echo esc_html($row['category']); ?></td>
                        <td><?php echo esc_html(number_format_i18n(intval($row['estimated_matching_equations']))); ?></td>
                        <td><?php echo esc_html($row['why_build_it']); ?><br><em><?php echo esc_html($row['implementation_notes']); ?></em></td>
                        <td><strong>Inputs:</strong> <?php echo esc_html($row['recommended_inputs']); ?><br><strong>Outputs:</strong> <?php echo esc_html($row['recommended_outputs']); ?></td>
                    </tr>
                <?php endforeach; endif; ?>
                </tbody>
            </table>
        </div>
    <?php }

    public function render_equations_page() {
        settings_errors('sc_workbench_messages');
        global $wpdb;
        self::create_equation_table();
        $table = self::equation_table_name();
        $total = intval($wpdb->get_var("SELECT COUNT(*) FROM {$table}"));
        $rows = $wpdb->get_results("SELECT * FROM {$table} ORDER BY updated_at DESC LIMIT 80", ARRAY_A);
        ?>
        <div class="wrap scwb-admin-wrap">
            <h1>Sustainable Catalyst Workbench Equation Registry</h1>
            <p>Scan published WordPress content for clean LaTeX equations, index surrounding article context, and map equations to Workbench calculators and article-aware tools. v0.9.5 preserves literal LaTeX backslashes, indexes clean equations, keeps Research Library display compact, and exports the registry as CSV for feature-building.</p>
            <div class="scwb-admin-grid">
                <section class="scwb-admin-card">
                    <h2>Scan WordPress Content</h2>
                    <p><strong><?php echo esc_html($total); ?></strong> equations currently indexed.</p>
                    <form method="post" style="display:inline-block;margin-right:12px;">
                        <?php wp_nonce_field('sc_workbench_equations'); ?>
                        <input type="hidden" name="sc_workbench_scan_equations" value="1" />
                        <?php submit_button('Scan / Rebuild Equation Registry', 'primary', 'submit', false); ?>
                    </form>
                    <form method="post" style="display:inline-block;" onsubmit="return confirm('Clear the equation registry? Published posts will not be changed.');">
                        <?php wp_nonce_field('sc_workbench_equations'); ?>
                        <input type="hidden" name="sc_workbench_clear_equations" value="1" />
                        <?php submit_button('Clear Registry', 'secondary', 'submit', false); ?>
                    </form>
                    <form method="post" style="display:inline-block;margin-left:12px;">
                        <?php wp_nonce_field('sc_workbench_equations'); ?>
                        <input type="hidden" name="sc_workbench_export_equations_csv" value="1" />
                        <?php submit_button('Download CSV Report', 'secondary', 'submit', false); ?>
                    </form>
                    <p class="description">Supported patterns: <code>\(...\)</code>, <code>\[...\]</code>, <code>$$...$$</code>, and <code>[latex]...[/latex]</code>. Single-dollar inline math is intentionally not scanned by default to avoid false positives.</p>
                </section>
                <section class="scwb-admin-card">
                    <h2>Article-Aware Shortcode</h2>
                    <p>Use <code>[sc_workbench mode="auto"]</code> on articles. Use <code>[sc_workbench mode="library" topic="research-library"]</code> on the Research Library to keep equation output compact.</p>
                    <p>For a specific article profile, use <code>[sc_workbench article="article-slug"]</code>.</p>
                </section>
            </div>
            <h2>Recent Equations</h2>
            <table class="widefat striped">
                <thead><tr><th>Article</th><th>Equation</th><th>Domain</th><th>Suggested Tools</th></tr></thead>
                <tbody>
                <?php if (!$rows): ?>
                    <tr><td colspan="4">No equations indexed yet.</td></tr>
                <?php else: foreach ($rows as $row): $tools = json_decode($row['suggested_tools'] ?: '[]', true) ?: []; ?>
                    <tr>
                        <td><strong><?php echo esc_html($row['post_title']); ?></strong><br><code><?php echo esc_html($row['post_slug']); ?></code></td>
                        <td><code><?php $eq_preview = (strlen($row['equation_normalized']) > 160) ? substr($row['equation_normalized'], 0, 160) . '…' : $row['equation_normalized']; echo esc_html($eq_preview); ?></code><br><small><?php echo esc_html($row['display_mode']); ?></small></td>
                        <td><?php echo esc_html($row['suggested_domain']); ?></td>
                        <td><?php echo esc_html(implode(', ', $tools)); ?></td>
                    </tr>
                <?php endforeach; endif; ?>
                </tbody>
            </table>
        </div>
    <?php }

    private function crypto_key() { return hash('sha256', wp_salt('auth')); }
    private function encrypt($plaintext) {
        if (!function_exists('openssl_encrypt')) { return base64_encode($plaintext); }
        $iv = random_bytes(16);
        $cipher = openssl_encrypt($plaintext, 'aes-256-cbc', $this->crypto_key(), OPENSSL_RAW_DATA, $iv);
        return base64_encode($iv . $cipher);
    }
    private function decrypt($encoded) {
        if (!$encoded) { return ''; }
        $raw = base64_decode($encoded, true);
        if ($raw === false) { return ''; }
        if (!function_exists('openssl_decrypt') || strlen($raw) <= 16) { return $raw; }
        $iv = substr($raw, 0, 16); $cipher = substr($raw, 16);
        $plain = openssl_decrypt($cipher, 'aes-256-cbc', $this->crypto_key(), OPENSSL_RAW_DATA, $iv);
        return $plain ?: '';
    }

    private static function shortcode_recommendations_table_name() {
        global $wpdb;
        return $wpdb->prefix . 'sc_workbench_shortcode_recommendations';
    }

    public static function create_shortcode_recommendations_table() {
        global $wpdb;
        $table = self::shortcode_recommendations_table_name();
        $charset = $wpdb->get_charset_collate();
        require_once ABSPATH . 'wp-admin/includes/upgrade.php';
        $sql = "CREATE TABLE {$table} (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            post_id BIGINT UNSIGNED NOT NULL,
            post_title TEXT NOT NULL,
            post_slug VARCHAR(255) NOT NULL,
            post_type VARCHAR(64) NOT NULL,
            permalink TEXT NULL,
            equation_count BIGINT UNSIGNED DEFAULT 0,
            display_equation_count BIGINT UNSIGNED DEFAULT 0,
            inline_equation_count BIGINT UNSIGNED DEFAULT 0,
            primary_domain VARCHAR(255) NULL,
            recommended_tool_id VARCHAR(180) NOT NULL,
            recommended_tool_title TEXT NOT NULL,
            confidence VARCHAR(32) NOT NULL DEFAULT 'medium',
            reason LONGTEXT NULL,
            example_equations LONGTEXT NULL,
            embed_shortcode LONGTEXT NOT NULL,
            article_shortcode LONGTEXT NULL,
            validation_status VARCHAR(64) NOT NULL DEFAULT 'needs_review',
            suggested_placement VARCHAR(255) NULL,
            display_mode VARCHAR(32) NOT NULL DEFAULT 'compact',
            placement_status VARCHAR(64) NOT NULL DEFAULT 'proposed',
            placement_notes LONGTEXT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY  (id),
            UNIQUE KEY post_tool_unique (post_id, recommended_tool_id),
            KEY post_id_idx (post_id),
            KEY tool_idx (recommended_tool_id),
            KEY confidence_idx (confidence),
            KEY validation_status_idx (validation_status)
        ) {$charset};";
        dbDelta($sql);
    }

    private function clear_shortcode_recommendations() {
        global $wpdb;
        self::create_shortcode_recommendations_table();
        $wpdb->query('TRUNCATE TABLE ' . self::shortcode_recommendations_table_name());
    }

    private function tool_title_from_id($tool_id) {
        $tool = $this->local_tool($tool_id);
        if ($tool && !empty($tool['title'])) { return $tool['title']; }
        return ucwords(str_replace('-', ' ', (string)$tool_id));
    }

    private function tool_confidence_label($equation_count, $tool_hits, $domain_hits, $tool_total) {
        $equation_count = max(0, intval($equation_count));
        $tool_hits = max(0, intval($tool_hits));
        $domain_hits = max(0, intval($domain_hits));
        $tool_total = max(1, intval($tool_total));
        $share = $tool_hits / $tool_total;
        if ($equation_count >= 4 && $tool_hits >= 3 && $share >= 0.33) { return 'high'; }
        if ($equation_count >= 2 && $tool_hits >= 2) { return 'medium'; }
        if ($domain_hits >= 3 && $tool_hits >= 1) { return 'medium'; }
        return 'low';
    }

    private function suggested_shortcode_display_mode($confidence, $rank, $equation_count) {
        $confidence = sanitize_key($confidence);
        $rank = max(1, intval($rank));
        $equation_count = max(0, intval($equation_count));
        if ($confidence === 'high' && $rank === 1 && $equation_count >= 4) { return 'compact'; }
        if ($confidence === 'medium') { return 'drawer'; }
        return 'inline';
    }

    private function suggested_calculator_placement($display_count, $inline_count, $rank) {
        $display_count = max(0, intval($display_count));
        $inline_count = max(0, intval($inline_count));
        $rank = max(1, intval($rank));
        if ($rank > 1) { return 'secondary embed after the main calculator or inside a collapsible drawer'; }
        if ($display_count >= 2) { return 'after the first major display-equation block'; }
        if ($display_count === 1) { return 'directly after the primary formula block'; }
        if ($inline_count >= 3) { return 'after the paragraph that introduces the recurring formula pattern'; }
        return 'near the first formula reference, preferably as an inline or drawer embed';
    }

    private function build_shortcode_recommendations() {
        global $wpdb;
        self::create_equation_table();
        self::create_shortcode_recommendations_table();
        $eq_table = self::equation_table_name();
        $out_table = self::shortcode_recommendations_table_name();
        $this->clear_shortcode_recommendations();
        $rows = $wpdb->get_results("SELECT * FROM {$eq_table} ORDER BY post_title ASC, id ASC", ARRAY_A);
        $groups = [];
        foreach ($rows as $row) {
            $post_id = intval($row['post_id']);
            if (!$post_id) { continue; }
            if (!isset($groups[$post_id])) {
                $groups[$post_id] = [
                    'post_id' => $post_id,
                    'post_title' => $row['post_title'],
                    'post_slug' => $row['post_slug'],
                    'post_type' => $row['post_type'],
                    'equation_count' => 0,
                    'display_equation_count' => 0,
                    'inline_equation_count' => 0,
                    'domains' => [],
                    'tools' => [],
                    'examples' => [],
                ];
            }
            $groups[$post_id]['equation_count']++;
            if (($row['display_mode'] ?? '') === 'display') { $groups[$post_id]['display_equation_count']++; }
            if (($row['display_mode'] ?? '') === 'inline') { $groups[$post_id]['inline_equation_count']++; }
            $domain = sanitize_text_field($row['suggested_domain'] ?? 'Mathematical Modeling');
            if ($domain) { $groups[$post_id]['domains'][$domain] = ($groups[$post_id]['domains'][$domain] ?? 0) + 1; }
            $tools = json_decode($row['suggested_tools'] ?: '[]', true);
            if (!is_array($tools)) { $tools = []; }
            foreach ($tools as $tid) {
                $tid = sanitize_key($tid);
                if ($tid) { $groups[$post_id]['tools'][$tid] = ($groups[$post_id]['tools'][$tid] ?? 0) + 1; }
            }
            $eq = trim((string)($row['equation_normalized'] ?: $row['equation_raw']));
            if ($eq && count($groups[$post_id]['examples']) < 5) { $groups[$post_id]['examples'][] = $eq; }
        }
        $built = 0;
        $now = current_time('mysql');
        foreach ($groups as $g) {
            if (!$g['tools']) { continue; }
            arsort($g['tools']);
            arsort($g['domains']);
            $top_tools = array_slice($g['tools'], 0, 3, true);
            $primary_domain = $g['domains'] ? array_key_first($g['domains']) : 'Mathematical Modeling';
            $domain_hits = $g['domains'][$primary_domain] ?? 0;
            $tool_total = array_sum($g['tools']);
            $rank = 0;
            foreach ($top_tools as $tool_id => $hits) {
                $rank++;
                $title = $this->tool_title_from_id($tool_id);
                $confidence = $this->tool_confidence_label($g['equation_count'], $hits, $domain_hits, $tool_total);
                if ($rank > 1 && $confidence === 'high') { $confidence = 'medium'; }
                $slug = sanitize_title($g['post_slug']);
                $safe_title = sanitize_text_field($title . ' for this article');
                $display_mode = $this->suggested_shortcode_display_mode($confidence, $rank, $g['equation_count']);
                $suggested_placement = $this->suggested_calculator_placement($g['display_equation_count'], $g['inline_equation_count'], $rank);
                $embed_shortcode = '[sc_workbench mode="tool" display="' . $display_mode . '" tool="' . $tool_id . '" article="' . $slug . '" title="' . esc_attr($safe_title) . '"]';
                $article_shortcode = '[sc_workbench mode="auto" display="drawer" article="' . $slug . '"]';
                $reason = sprintf('%s was recommended because %d indexed equation(s) on this page mapped to this tool family. Primary detected domain: %s. Suggested placement: %s. Review before embedding on public pages.', $title, intval($hits), $primary_domain, $suggested_placement);
                $validation = ($confidence === 'high') ? 'recommended' : (($confidence === 'medium') ? 'review' : 'weak_match');
                $wpdb->replace($out_table, [
                    'post_id' => intval($g['post_id']),
                    'post_title' => $g['post_title'],
                    'post_slug' => $slug,
                    'post_type' => $g['post_type'],
                    'permalink' => get_permalink(intval($g['post_id'])),
                    'equation_count' => intval($g['equation_count']),
                    'display_equation_count' => intval($g['display_equation_count']),
                    'inline_equation_count' => intval($g['inline_equation_count']),
                    'primary_domain' => $primary_domain,
                    'recommended_tool_id' => $tool_id,
                    'recommended_tool_title' => $title,
                    'confidence' => $confidence,
                    'reason' => $reason,
                    'example_equations' => implode(' ; ', $g['examples']),
                    'embed_shortcode' => $embed_shortcode,
                    'article_shortcode' => $article_shortcode,
                    'validation_status' => $validation,
                    'suggested_placement' => $suggested_placement,
                    'display_mode' => $display_mode,
                    'placement_status' => 'proposed',
                    'placement_notes' => 'v1.0.0 generated placement recommendation. Confirm location in article editor before publishing.',
                    'created_at' => $now,
                    'updated_at' => $now,
                ], ['%d','%s','%s','%s','%s','%d','%d','%d','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s']);
                $built++;
            }
        }
        return ['ok'=>true, 'recommendations_built'=>$built, 'pages_analyzed'=>count($groups), 'equation_rows'=>count($rows)];
    }

    private function shortcode_recommendation_rows($limit=500) {
        global $wpdb;
        self::create_shortcode_recommendations_table();
        $limit = max(1, min(2000, intval($limit)));
        $table = self::shortcode_recommendations_table_name();
        return $wpdb->get_results($wpdb->prepare("SELECT * FROM {$table} ORDER BY FIELD(confidence,'high','medium','low'), equation_count DESC, post_title ASC, id ASC LIMIT %d", $limit), ARRAY_A);
    }

    private function shortcode_recommendation_summary() {
        global $wpdb;
        self::create_shortcode_recommendations_table();
        $table = self::shortcode_recommendations_table_name();
        $total = intval($wpdb->get_var("SELECT COUNT(*) FROM {$table}"));
        $by_confidence = $wpdb->get_results("SELECT confidence, COUNT(*) AS count FROM {$table} GROUP BY confidence ORDER BY FIELD(confidence,'high','medium','low')", ARRAY_A);
        $by_domain = $wpdb->get_results("SELECT primary_domain, COUNT(*) AS count, SUM(equation_count) AS equation_count FROM {$table} GROUP BY primary_domain ORDER BY count DESC, equation_count DESC LIMIT 20", ARRAY_A);
        $by_tool = $wpdb->get_results("SELECT recommended_tool_id, recommended_tool_title, COUNT(*) AS count, SUM(equation_count) AS equation_count FROM {$table} GROUP BY recommended_tool_id, recommended_tool_title ORDER BY count DESC, equation_count DESC LIMIT 20", ARRAY_A);
        $by_placement_status = $wpdb->get_results("SELECT placement_status, COUNT(*) AS count FROM {$table} GROUP BY placement_status ORDER BY count DESC", ARRAY_A);
        return ['total'=>$total, 'by_confidence'=>$by_confidence, 'by_domain'=>$by_domain, 'by_tool'=>$by_tool, 'by_placement_status'=>$by_placement_status];
    }

    public function rest_shortcode_recommendations(WP_REST_Request $request) {
        $limit = min(1000, max(1, intval($request->get_param('limit') ?: 250)));
        return new WP_REST_Response(['ok'=>true, 'summary'=>$this->shortcode_recommendation_summary(), 'recommendations'=>$this->shortcode_recommendation_rows($limit)], 200);
    }

    public function rest_validation_summary(WP_REST_Request $request) {
        global $wpdb;
        self::create_equation_table();
        self::create_shortcode_recommendations_table();
        $eq_table = self::equation_table_name();
        $sc_table = self::shortcode_recommendations_table_name();
        $equations = intval($wpdb->get_var("SELECT COUNT(*) FROM {$eq_table}"));
        $articles = intval($wpdb->get_var("SELECT COUNT(DISTINCT post_id) FROM {$eq_table}"));
        $recommendations = intval($wpdb->get_var("SELECT COUNT(*) FROM {$sc_table}"));
        $weak = intval($wpdb->get_var("SELECT COUNT(*) FROM {$sc_table} WHERE confidence='low' OR validation_status='weak_match'"));
        return new WP_REST_Response(['ok'=>true, 'version'=>self::VERSION, 'equations_indexed'=>$equations, 'articles_with_equations'=>$articles, 'shortcode_recommendations'=>$recommendations, 'weak_matches'=>$weak, 'tool_validation'=>$this->tool_validation_counts(), 'validation_notes'=>['High confidence still requires editorial review before embedding.', 'Use the tool-specific shortcode on articles where readers need a calculator directly under a formula.', 'v1.0.0 separates built, recommended, review, and weak-match states for editorial placement.']], 200);
    }

    private function export_shortcode_recommendations_csv() {
        if (!current_user_can('manage_options')) { wp_die('Unauthorized'); }
        $rows = $this->shortcode_recommendation_rows(2000);
        $filename = 'sustainable-catalyst-shortcode-recommendations-' . gmdate('Ymd-His') . '.csv';
        nocache_headers();
        header('Content-Type: text/csv; charset=utf-8');
        header('Content-Disposition: attachment; filename=' . $filename);
        $out = fopen('php://output', 'w');
        fputcsv($out, ['post_id','post_title','post_slug','post_type','permalink','equation_count','display_equation_count','inline_equation_count','primary_domain','recommended_tool_id','recommended_tool_title','confidence','validation_status','suggested_placement','display_mode','placement_status','placement_notes','reason','example_equations','embed_shortcode','article_shortcode']);
        foreach ($rows as $row) {
            fputcsv($out, [
                $row['post_id'], $row['post_title'], $row['post_slug'], $row['post_type'], $row['permalink'],
                $row['equation_count'], $row['display_equation_count'], $row['inline_equation_count'],
                $row['primary_domain'], $row['recommended_tool_id'], $row['recommended_tool_title'],
                $row['confidence'], $row['validation_status'], $row['suggested_placement'] ?? '', $row['display_mode'] ?? 'compact', $row['placement_status'] ?? 'proposed', $row['placement_notes'] ?? '', $row['reason'], $row['example_equations'],
                $row['embed_shortcode'], $row['article_shortcode']
            ]);
        }
        fclose($out);
    }

    
    private function validation_status_for_tool($tool_id) {
        $tool_id = sanitize_key($tool_id);
        $tool = $this->local_tool($tool_id);
        if (!$tool) { return 'missing_local_registry'; }
        $engine = sanitize_key($tool['engine'] ?? '');
        if (strpos($engine, 'deterministic') !== false || strpos($engine, 'python') !== false || strpos($engine, 'backend') !== false) { return 'built'; }
        if (strpos($engine, 'fallback') !== false || strpos($engine, 'mvp') !== false) { return 'experimental'; }
        return 'needs_review';
    }

    private function tool_validation_counts() {
        $counts = ['built'=>0, 'experimental'=>0, 'needs_review'=>0, 'missing_local_registry'=>0];
        foreach ($this->local_tools() as $tool) {
            $status = $this->validation_status_for_tool($tool['id'] ?? '');
            if (!isset($counts[$status])) { $counts[$status] = 0; }
            $counts[$status]++;
        }
        return $counts;
    }

    public function rest_tool_catalog(WP_REST_Request $request) {
        $tools = [];
        foreach ($this->local_tools() as $tool) {
            $id = sanitize_key($tool['id'] ?? '');
            if (!$id) { continue; }
            $tools[] = [
                'id' => $id,
                'title' => $tool['title'] ?? $this->tool_title_from_id($id),
                'domain' => $tool['domain'] ?? '',
                'family' => $tool['family'] ?? '',
                'engine' => $tool['engine'] ?? '',
                'description' => $tool['description'] ?? '',
                'validation_status' => $this->validation_status_for_tool($id),
                'shortcode_compact' => '[sc_workbench mode="tool" display="compact" tool="' . $id . '"]',
                'shortcode_drawer' => '[sc_workbench mode="tool" display="drawer" tool="' . $id . '"]',
                'shortcode_inline' => '[sc_workbench mode="tool" display="inline" tool="' . $id . '"]',
            ];
        }
        return new WP_REST_Response(['ok'=>true, 'version'=>self::VERSION, 'tool_count'=>count($tools), 'validation_counts'=>$this->tool_validation_counts(), 'tools'=>$tools], 200);
    }

    public function rest_placement_assistant(WP_REST_Request $request) {
        $limit = min(1000, max(1, intval($request->get_param('limit') ?: 250)));
        return new WP_REST_Response(['ok'=>true, 'version'=>self::VERSION, 'summary'=>$this->shortcode_recommendation_summary(), 'placements'=>$this->shortcode_recommendation_rows($limit)], 200);
    }

    public function render_validation_dashboard_page() {
        if (!current_user_can('manage_options')) { return; }
        settings_errors('sc_workbench_messages');
        $counts = $this->tool_validation_counts();
        $summary = $this->shortcode_recommendation_summary();
        global $wpdb;
        self::create_equation_table();
        self::create_shortcode_recommendations_table();
        $eq_count = intval($wpdb->get_var('SELECT COUNT(*) FROM ' . self::equation_table_name()));
        $article_count = intval($wpdb->get_var('SELECT COUNT(DISTINCT post_id) FROM ' . self::equation_table_name()));
        $weak = intval($wpdb->get_var("SELECT COUNT(*) FROM " . self::shortcode_recommendations_table_name() . " WHERE confidence='low' OR validation_status='weak_match'"));
        ?>
        <div class="wrap scwb-admin-wrap">
            <h1>Workbench Validation Dashboard</h1>
            <p>v1.0.0 stabilization view for calculator coverage, equation indexing, shortcode routing quality, and editorial placement readiness.</p>
            <div class="scwb-admin-grid">
                <section class="scwb-admin-card"><h2>Equation Registry</h2><p><strong><?php echo esc_html(number_format_i18n($eq_count)); ?></strong> equations indexed.</p><p><strong><?php echo esc_html(number_format_i18n($article_count)); ?></strong> articles/pages represented.</p></section>
                <section class="scwb-admin-card"><h2>Calculator Tool Validation</h2><ul><?php foreach ($counts as $status=>$count): ?><li><strong><?php echo esc_html(ucwords(str_replace('_',' ', $status))); ?>:</strong> <?php echo esc_html(number_format_i18n(intval($count))); ?></li><?php endforeach; ?></ul></section>
                <section class="scwb-admin-card"><h2>Shortcode Routing</h2><p><strong><?php echo esc_html(number_format_i18n(intval($summary['total'] ?? 0))); ?></strong> placement recommendations.</p><p><strong><?php echo esc_html(number_format_i18n($weak)); ?></strong> weak matches needing review.</p></section>
            </div>
            <section class="scwb-admin-card scwb-admin-wide"><h2>v1.0 Quality Rules</h2><ul><li>Use high-confidence recommendations first.</li><li>Use <code>display="compact"</code> for primary article calculators and <code>display="drawer"</code> for secondary calculators.</li><li>Review low-confidence placements manually before inserting public shortcodes.</li><li>Backend-powered tools should be tested on Render before being treated as production-ready.</li></ul></section>
        </div>
        <?php
    }

    public function render_tool_catalog_page() {
        if (!current_user_can('manage_options')) { return; }
        $tools = $this->local_tools();
        ?>
        <div class="wrap scwb-admin-wrap">
            <h1>Workbench Tool Catalog</h1>
            <p>Stable v1.0 catalog of calculator IDs, domains, validation status, and shortcode forms.</p>
            <section class="scwb-admin-card scwb-admin-wide">
                <table class="widefat striped scwb-admin-table"><thead><tr><th>Tool</th><th>Domain</th><th>Status</th><th>Shortcode</th></tr></thead><tbody>
                <?php foreach ($tools as $tool): $id = sanitize_key($tool['id'] ?? ''); if (!$id) { continue; } ?>
                    <tr><td><strong><?php echo esc_html($tool['title'] ?? $id); ?></strong><br><code><?php echo esc_html($id); ?></code></td><td><?php echo esc_html($tool['domain'] ?? ''); ?></td><td><?php echo esc_html($this->validation_status_for_tool($id)); ?></td><td><textarea readonly class="scwb-shortcode-copy" rows="2">[sc_workbench mode="tool" display="compact" tool="<?php echo esc_attr($id); ?>"]</textarea><button type="button" class="button button-small" data-scwb-copy-shortcode>Copy</button></td></tr>
                <?php endforeach; ?>
                </tbody></table>
            </section>
        </div>
        <?php
    }

    public function render_placement_assistant_page() {
        if (!current_user_can('manage_options')) { return; }
        settings_errors('sc_workbench_messages');
        $rows = $this->shortcode_recommendation_rows(500);
        ?>
        <div class="wrap scwb-admin-wrap">
            <h1>Article Calculator Placement Assistant</h1>
            <p>Use this editorial view to decide where calculator embeds should be inserted near article formulas.</p>
            <section class="scwb-admin-card scwb-admin-wide">
                <table class="widefat striped scwb-admin-table"><thead><tr><th>Article</th><th>Recommended placement</th><th>Display</th><th>Calculator</th><th>Confidence</th><th>Shortcode</th></tr></thead><tbody>
                <?php if (!$rows): ?><tr><td colspan="6">No placements yet. Open Embed Shortcodes and build recommendations.</td></tr><?php endif; ?>
                <?php foreach ($rows as $row): ?>
                    <tr><td><strong><?php echo esc_html($row['post_title']); ?></strong><br><a href="<?php echo esc_url($row['permalink']); ?>" target="_blank" rel="noopener">View article</a></td><td><?php echo esc_html($row['suggested_placement'] ?? 'Review article and place after the relevant equation.'); ?></td><td><code><?php echo esc_html($row['display_mode'] ?? 'compact'); ?></code></td><td><?php echo esc_html($row['recommended_tool_title']); ?><br><code><?php echo esc_html($row['recommended_tool_id']); ?></code></td><td><span class="scwb-confidence scwb-confidence-<?php echo esc_attr($row['confidence']); ?>"><?php echo esc_html($row['confidence']); ?></span></td><td><textarea readonly class="scwb-shortcode-copy" rows="3"><?php echo esc_textarea($row['embed_shortcode']); ?></textarea><button type="button" class="button button-small" data-scwb-copy-shortcode>Copy</button></td></tr>
                <?php endforeach; ?>
                </tbody></table>
            </section>
        </div>
        <?php
    }

public function render_embed_shortcodes_page() {
        if (!current_user_can('manage_options')) { return; }
        settings_errors('sc_workbench_messages');
        $summary = $this->shortcode_recommendation_summary();
        $rows = $this->shortcode_recommendation_rows(300);
        global $wpdb;
        self::create_equation_table();
        $eq_count = intval($wpdb->get_var('SELECT COUNT(*) FROM ' . self::equation_table_name()));
        $article_count = intval($wpdb->get_var('SELECT COUNT(DISTINCT post_id) FROM ' . self::equation_table_name()));
        ?>
        <div class="wrap scwb-admin-wrap">
            <h1>Embed Shortcodes</h1>
            <p>Analyze indexed equations across articles and generate calculator-specific shortcodes that can be pasted directly into formula-heavy pages.</p>
            <div class="scwb-admin-grid">
                <section class="scwb-admin-card">
                    <h2>Build Recommendations</h2>
                    <p><strong><?php echo esc_html(number_format_i18n($eq_count)); ?></strong> indexed equations across <strong><?php echo esc_html(number_format_i18n($article_count)); ?></strong> pages/articles.</p>
                    <form method="post">
                        <?php wp_nonce_field('sc_workbench_embed_shortcodes'); ?>
                        <p><button type="submit" class="button button-primary" name="sc_workbench_build_shortcode_recommendations" value="1">Build Shortcode Recommendations</button></p>
                        <p><button type="submit" class="button" name="sc_workbench_scan_and_build_shortcode_recommendations" value="1">Scan Equations + Build Recommendations</button></p>
                        <p><button type="submit" class="button" name="sc_workbench_export_shortcode_recommendations_csv" value="1">Export Shortcode CSV</button></p>
                        <p><button type="submit" class="button button-link-delete" name="sc_workbench_clear_shortcode_recommendations" value="1">Clear Recommendations</button></p>
                    </form>
                </section>
                <section class="scwb-admin-card">
                    <h2>Validation Summary</h2>
                    <p><strong><?php echo esc_html(number_format_i18n(intval($summary['total']))); ?></strong> shortcode recommendations built.</p>
                    <ul>
                        <?php foreach (($summary['by_confidence'] ?? []) as $row): ?>
                            <li><strong><?php echo esc_html(ucfirst($row['confidence'])); ?>:</strong> <?php echo esc_html(number_format_i18n(intval($row['count']))); ?></li>
                        <?php endforeach; ?>
                    </ul>
                    <p class="description">Use high-confidence rows first. Medium and low rows should be reviewed because math notation can be ambiguous.</p>
                </section>
            </div>
            <section class="scwb-admin-card scwb-admin-wide">
                <h2>Recommended Calculator Embeds</h2>
                <p>Copy the tool-specific shortcode into the article near the formula it supports. The shortcode opens the Workbench directly to the recommended calculator.</p>
                <table class="widefat striped scwb-admin-table">
                    <thead><tr><th>Article</th><th>Equations</th><th>Domain</th><th>Calculator</th><th>Placement</th><th>Confidence</th><th>Shortcode</th></tr></thead>
                    <tbody>
                    <?php if (!$rows): ?>
                        <tr><td colspan="7">No recommendations yet. Build recommendations from the equation registry.</td></tr>
                    <?php endif; ?>
                    <?php foreach ($rows as $row): ?>
                        <tr>
                            <td><strong><?php echo esc_html($row['post_title']); ?></strong><br><a href="<?php echo esc_url($row['permalink']); ?>" target="_blank" rel="noopener">View article</a></td>
                            <td><?php echo esc_html(intval($row['equation_count'])); ?></td>
                            <td><?php echo esc_html($row['primary_domain']); ?></td>
                            <td><code><?php echo esc_html($row['recommended_tool_id']); ?></code><br><?php echo esc_html($row['recommended_tool_title']); ?></td>
                            <td><?php echo esc_html($row['suggested_placement'] ?? 'Review placement.'); ?><br><code><?php echo esc_html($row['display_mode'] ?? 'compact'); ?></code></td>
                            <td><span class="scwb-confidence scwb-confidence-<?php echo esc_attr($row['confidence']); ?>"><?php echo esc_html($row['confidence']); ?></span></td>
                            <td><textarea readonly class="scwb-shortcode-copy" rows="3"><?php echo esc_textarea($row['embed_shortcode']); ?></textarea><button type="button" class="button button-small" data-scwb-copy-shortcode>Copy</button></td>
                        </tr>
                    <?php endforeach; ?>
                    </tbody>
                </table>
            </section>
        </div>
        <?php
    }

}

register_activation_hook(__FILE__, ['SC_Workbench_Plugin', 'activate']);
new SC_Workbench_Plugin();
