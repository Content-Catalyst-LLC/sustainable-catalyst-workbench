<?php
/**
 * Plugin Name: Sustainable Catalyst Workbench
 * Description: Compact site-scoped Workbench interface with Python/R/Julia/Haskell-ready analytics backend, AI assistant, calculators, and SVG graph output.
 * Version: 0.4.2
 * Author: Content Catalyst LLC
 * License: MIT
 * Text Domain: sustainable-catalyst-workbench
 */

if (!defined('ABSPATH')) { exit; }

final class SC_Workbench_Plugin {
    const VERSION = '0.4.2';
    const OPTION_GROUP = 'sc_workbench_settings';
    const OPTION_BACKEND_URL = 'sc_workbench_backend_url';
    const OPTION_API_KEY = 'sc_workbench_api_key';
    const OPTION_PROVIDER_KEY = 'sc_workbench_provider_key_encrypted';
    const OPTION_ENABLE_AI = 'sc_workbench_enable_ai';
    const OPTION_ENABLE_SCOPE_GATE = 'sc_workbench_enable_scope_gate';
    const OPTION_DEBUG = 'sc_workbench_debug';
    const OPTION_TIMEOUT = 'sc_workbench_timeout';
    const OPTION_DEFAULT_TOPIC = 'sc_workbench_default_topic';
    const OPTION_THEME = 'sc_workbench_theme';

    public function __construct() {
        add_action('init', [$this, 'register_shortcodes']);
        add_action('wp_enqueue_scripts', [$this, 'enqueue_assets']);
        add_action('admin_enqueue_scripts', [$this, 'enqueue_admin_assets']);
        add_action('rest_api_init', [$this, 'register_rest_routes']);
        add_action('admin_menu', [$this, 'register_admin_menu']);
        add_action('admin_init', [$this, 'register_settings']);
    }

    public static function activate() {
        add_option(self::OPTION_BACKEND_URL, 'http://127.0.0.1:8088');
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
            'fallbackTools' => $this->local_tools(),
        ]);
    }

    public function enqueue_admin_assets($hook) {
        if (strpos($hook, 'sustainable-catalyst-workbench') !== false || strpos($hook, 'sc-workbench') !== false) {
            wp_enqueue_style('sc-workbench-admin', plugin_dir_url(__FILE__) . 'assets/sc-workbench-admin.css', [], self::VERSION);
            wp_enqueue_script('sc-workbench-admin', plugin_dir_url(__FILE__) . 'assets/sc-workbench-admin.js', [], self::VERSION, true);
            wp_localize_script('sc-workbench-admin', 'SCWorkbenchAdmin', [
                'restUrl' => esc_url_raw(rest_url('sc-workbench/v1')),
                'nonce' => wp_create_nonce('wp_rest'),
            ]);
        }
    }

    public function register_shortcodes() {
        add_shortcode('sc_workbench', [$this, 'render_compact_shortcode']);
        add_shortcode('sc_workbench_compact', [$this, 'render_compact_shortcode']);
        add_shortcode('sc_workbench_pathways', [$this, 'render_pathways_shortcode']);
    }

    private function ensure_assets() { wp_enqueue_style('sc-workbench'); wp_enqueue_script('sc-workbench'); }

    public function render_compact_shortcode($atts) {
        $this->ensure_assets();
        $atts = shortcode_atts(['topic'=>'research-library', 'title'=>'Sustainable Catalyst Workbench'], $atts, 'sc_workbench');
        $uid = 'scwb-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($uid); ?>" class="scwb-compact scwb-theme-<?php echo esc_attr(get_option(self::OPTION_THEME, 'institutional')); ?>" data-scwb-compact data-topic="<?php echo esc_attr(sanitize_key($atts['topic'])); ?>">
            <div class="scwb-compact-head">
                <p class="scwb-eyebrow">Sustainable Catalyst Workbench</p>
                <h2><?php echo esc_html(sanitize_text_field($atts['title'])); ?></h2>
                <p>Ask a site-scoped question, run an advanced calculator, or follow a learning pathway. Calculations, visual analytics, and graphs run through the analytics backend.</p>
            </div>
            <div class="scwb-tabs" role="tablist" aria-label="Workbench modes">
                <button type="button" class="is-active" data-scwb-tab="ask">Ask</button>
                <button type="button" data-scwb-tab="tools">Calculators</button>
                <button type="button" data-scwb-tab="visualize">Visualize</button>
                <button type="button" data-scwb-tab="pathways">Pathways</button>
            </div>
            <div class="scwb-tab-panel is-active" data-scwb-panel="ask">
                <form class="scwb-ask-form" data-scwb-ask-form>
                    <label class="scwb-label">Question
                        <textarea name="question" rows="4" placeholder="Ask about Sustainable Catalyst topics, analytics, calculators, modeling, energy, economics, psychology, science, governance, meaning, or research pathways."></textarea>
                    </label>
                    <button class="scwb-button" type="submit">Ask Workbench</button>
                </form>
                <div class="scwb-output" data-scwb-ask-output hidden></div>
            </div>
            <div class="scwb-tab-panel" data-scwb-panel="tools">
                <div class="scwb-toolbar">
                    <label>Choose a calculator <select data-scwb-tool-select><option value="">Loading tools…</option></select></label>
                    <button type="button" class="scwb-button scwb-button-secondary" data-scwb-load-tool>Open</button>
                    <p class="scwb-tool-note" data-scwb-tool-note>Loading calculator registry…</p>
                </div>
                <div class="scwb-tool-shell" data-scwb-tool-shell></div>
            </div>
            <div class="scwb-tab-panel" data-scwb-panel="visualize">
                <form class="scwb-visual-form" data-scwb-visual-form>
                    <div class="scwb-visual-grid">
                        <label class="scwb-label">Chart type
                            <select name="chart_type">
                                <option value="line">Line chart</option>
                                <option value="bar">Bar chart</option>
                                <option value="scatter">Scatter plot</option>
                                <option value="histogram">Histogram</option>
                                <option value="box">Box plot</option>
                            </select>
                        </label>
                        <label class="scwb-label">Chart title
                            <input name="title" type="text" placeholder="Energy demand scenario">
                        </label>
                    </div>
                    <div class="scwb-visual-grid">
                        <label class="scwb-label">X values or labels
                            <textarea name="x_values" rows="4" placeholder="Jan, Feb, Mar, Apr or 1,2,3,4"></textarea>
                        </label>
                        <label class="scwb-label">Y values
                            <textarea name="y_values" rows="4" placeholder="10, 14, 19, 25"></textarea>
                        </label>
                    </div>
                    <div class="scwb-visual-grid">
                        <label class="scwb-label">Category labels
                            <textarea name="labels" rows="3" placeholder="Energy, Economics, Psychology, Governance"></textarea>
                        </label>
                        <label class="scwb-label">Values
                            <textarea name="values" rows="3" placeholder="42, 38, 35, 31"></textarea>
                        </label>
                    </div>
                    <div class="scwb-visual-grid">
                        <label class="scwb-label">X-axis label
                            <input name="x_label" type="text" placeholder="Time, category, or scenario">
                        </label>
                        <label class="scwb-label">Y-axis label
                            <input name="y_label" type="text" placeholder="Value">
                        </label>
                    </div>
                    <button class="scwb-button" type="submit">Generate Visualization</button>
                    <p class="scwb-tool-note">Visualizations are rendered by the Python analytics backend as SVG graphs.</p>
                </form>
                <div class="scwb-output" data-scwb-visual-output hidden></div>
            </div>
            <div class="scwb-tab-panel" data-scwb-panel="pathways">
                <div class="scwb-pathways" data-scwb-pathways>
                    <article><strong>Systems Reasoning</strong><span>Feedback, resilience, thresholds, interdependence, and long-term change.</span></article>
                    <article><strong>Scientific and Mathematical Reasoning</strong><span>Symbols, variables, models, uncertainty, computation, and interpretation.</span></article>
                    <article><strong>Computational and Algorithmic Reasoning</strong><span>Formal procedure, data structures, search, optimization, AI systems, and governance.</span></article>
                    <article><strong>Sustainable Human Futures</strong><span>Development, ecological limits, risk, resilience, energy systems, and public responsibility.</span></article>
                </div>
            </div>
            <p class="scwb-fineprint">Educational and research support only. The Workbench does not provide legal, medical, financial, clinical, or engineering certification.</p>
        </section>
        <?php return ob_get_clean();
    }

    public function render_pathways_shortcode($atts) {
        $this->ensure_assets();
        return '<div class="scwb-pathways scwb-pathways-standalone"><article><strong>Systems Reasoning</strong><span>Feedback, resilience, interdependence, and complexity.</span></article><article><strong>Modeling and Analytics</strong><span>Math, statistics, economics, energy, science, and simulation tools.</span></article><article><strong>Human Meaning and Institutions</strong><span>Psychology, culture, ethics, philosophy, governance, and interpretation.</span></article></div>';
    }

    private function local_tools() {
        $json = <<<'JSON'
[{"id":"linear-system-solver","title":"Linear System Solver","domain":"Mathematical Modeling","type":"calculator","description":"Solve Ax=b, estimate rank, determinant, condition number, residual, and stability warnings.","featured":true,"schema":{"fields":[{"name":"A","label":"Matrix A","type":"textarea","placeholder":"[[2,1],[1,3]]"},{"name":"b","label":"Vector b","type":"text","placeholder":"[1,2]"}]}},{"id":"calculus-function-analyzer","title":"Calculus Function Analyzer","domain":"Mathematical Modeling","type":"calculator","description":"Differentiate, integrate, locate critical points, and graph a symbolic function.","featured":true,"schema":{"fields":[{"name":"function","label":"Function f(x)","type":"text","placeholder":"x**3 - 3*x + 1"},{"name":"x_min","label":"Graph x-min","type":"number","placeholder":"-5"},{"name":"x_max","label":"Graph x-max","type":"number","placeholder":"5"}]}},{"id":"statistics-analyzer","title":"Statistics Analyzer","domain":"Statistics for Systems Modeling","type":"analytics","description":"Summarize data, compute distribution diagnostics, confidence intervals, and detailed SVG graphs.","featured":true,"schema":{"fields":[{"name":"data","label":"Data values","type":"textarea","placeholder":"12, 15, 18, 19, 21, 25, 29"}]}},{"id":"regression-analyzer","title":"Regression Analyzer","domain":"Statistics and Economics","type":"analytics","description":"Fit a simple linear model with diagnostics and a fitted-line graph.","featured":true,"schema":{"fields":[{"name":"x","label":"X values","type":"textarea","placeholder":"1,2,3,4,5"},{"name":"y","label":"Y values","type":"textarea","placeholder":"2,4,5,4,6"}]}},{"id":"visual-analytics-studio","title":"Visual Analytics Studio","domain":"Data Systems & Analytics","type":"visualization","description":"Create publication-ready SVG bar, line, scatter, histogram, and box-plot visualizations from data using the Python analytics backend.","featured":true,"schema":{"fields":[{"name":"chart_type","label":"Chart type","type":"select","options":["bar","line","scatter","histogram","box"]},{"name":"title","label":"Chart title","type":"text","placeholder":"Energy demand scenario"},{"name":"x_values","label":"X values","type":"textarea","placeholder":"1,2,3,4,5 or Jan,Feb,Mar,Apr"},{"name":"y_values","label":"Y values","type":"textarea","placeholder":"10,14,19,25,31"},{"name":"labels","label":"Category labels","type":"textarea","placeholder":"Energy, Economics, Psychology, Governance"},{"name":"values","label":"Values","type":"textarea","placeholder":"42, 38, 35, 31"},{"name":"x_label","label":"X-axis label","type":"text","placeholder":"Scenario or time"},{"name":"y_label","label":"Y-axis label","type":"text","placeholder":"Value"}]}},{"id":"probability-distribution-calculator","title":"Probability Distribution Calculator","domain":"Probability for Systems Modeling","type":"calculator","description":"Analyze normal, binomial, and Poisson probabilities with distribution graphs.","featured":true,"schema":{"fields":[{"name":"distribution","label":"Distribution","type":"select","options":["normal","binomial","poisson"]},{"name":"params","label":"Parameters","type":"text","placeholder":"normal: mean=0,sd=1 | binomial: n=20,p=0.4 | poisson: lambda=3"},{"name":"value","label":"Value / threshold","type":"number","placeholder":"1"}]}},{"id":"differential-equation-simulator","title":"Differential Equation Simulator","domain":"Differential Equations for Systems Modeling","type":"simulation","description":"Simulate logistic growth and first-order system dynamics with plotted trajectories. Julia bridge available when installed.","featured":true,"schema":{"fields":[{"name":"model","label":"Model","type":"select","options":["logistic","exponential_decay"]},{"name":"initial","label":"Initial value","type":"number","placeholder":"10"},{"name":"rate","label":"Rate","type":"number","placeholder":"0.25"},{"name":"carrying_capacity","label":"Carrying capacity","type":"number","placeholder":"100"},{"name":"t_end","label":"Time horizon","type":"number","placeholder":"30"}]}},{"id":"economics-calculator","title":"Economics Calculator","domain":"Economic Systems","type":"calculator","description":"Calculate NPV, elasticity, break-even, and supply-demand equilibrium with graphs where relevant.","featured":true,"schema":{"fields":[{"name":"mode","label":"Mode","type":"select","options":["npv","elasticity","supply_demand","break_even"]},{"name":"inputs","label":"Inputs","type":"textarea","placeholder":"npv: rate=0.08; cashflows=-1000,300,400,500\nelasticity: p1=10,p2=12,q1=100,q2=85\nsupply_demand: demand_intercept=100,demand_slope=2,supply_intercept=20,supply_slope=1"}]}},{"id":"energy-systems-calculator","title":"Energy Systems Calculator","domain":"Energy Systems","type":"calculator","description":"Estimate electricity cost, emissions, solar PV generation, and battery autonomy.","featured":true,"schema":{"fields":[{"name":"mode","label":"Mode","type":"select","options":["electricity_cost_emissions","solar_pv","battery_autonomy"]},{"name":"inputs","label":"Inputs","type":"textarea","placeholder":"electricity_cost_emissions: kwh=500,rate=0.16,kgco2_per_kwh=0.4\nsolar_pv: kw=5,sun_hours=4.2,performance_ratio=0.8\nbattery_autonomy: battery_kwh=13.5,load_kw=1.2,depth_of_discharge=0.9"}]}},{"id":"psychology-scale-analyzer","title":"Psychology Scale Analyzer","domain":"Psychology","type":"analytics","description":"Analyze Likert-style responses, subscales, summary scores, and Cronbach alpha when item-level data are provided. R bridge available when installed.","featured":true,"schema":{"fields":[{"name":"responses","label":"Responses","type":"textarea","placeholder":"Rows of comma-separated item scores, e.g.\n4,5,4,3\n3,4,4,2\n5,5,4,4"},{"name":"scale_min","label":"Scale minimum","type":"number","placeholder":"1"},{"name":"scale_max","label":"Scale maximum","type":"number","placeholder":"5"}]}},{"id":"scientific-calculator","title":"Scientific Calculator","domain":"Natural Science","type":"calculator","description":"Open science calculator for physics, chemistry, materials, and environmental science examples.","featured":true,"schema":{"fields":[{"name":"mode","label":"Mode","type":"select","options":["ideal_gas","kinetic_energy","stress_strain","dilution"]},{"name":"inputs","label":"Inputs","type":"textarea","placeholder":"ideal_gas: n=1,R=8.314,T=298,V=0.024\nkinetic_energy: mass=2,velocity=10\nstress_strain: force=1000,area=0.01,delta_length=0.002,length=1"}]}},{"id":"sustainability-resilience-scorecard","title":"Sustainability & Resilience Scorecard","domain":"Sustainable Systems","type":"diagnostic","description":"Weighted diagnostic for exposure, sensitivity, adaptive capacity, governance, equity, and recovery capacity.","featured":true,"schema":{"fields":[{"name":"scores","label":"Scores","type":"textarea","placeholder":"exposure=4,sensitivity=3,adaptive_capacity=2,governance=3,equity=2,recovery=4"}]}},{"id":"ai-governance-audit","title":"AI Governance Audit","domain":"Technology & Systems Intelligence","type":"audit","description":"Structured audit for model purpose, data quality, proxy variables, human oversight, contestability, and documentation.","featured":true,"schema":{"fields":[{"name":"system_description","label":"AI system description","type":"textarea","placeholder":"Describe the AI system, use case, data, decision impact, and oversight model."},{"name":"risk_factors","label":"Risk factors","type":"textarea","placeholder":"high impact, personal data, automation, vulnerable users, opaque model..."}]}},{"id":"haskell-rule-checker","title":"Haskell Rule Checker","domain":"Algorithms & Computational Reasoning","type":"formal-logic","description":"Validate simple rule consistency using a Haskell bridge when available, with a Python fallback.","featured":false,"schema":{"fields":[{"name":"rules","label":"Rules","type":"textarea","placeholder":"must:scope_gate\nmust:not_general_chat\nconflict:allow_all_topics"}]}},{"id":"qualitative-interpretation-matrix","title":"Qualitative Interpretation Matrix","domain":"Meaning and Humanities","type":"interpretive-framework","description":"Structured qualitative analysis for narrative, symbolism, philosophy, religion, culture, and meaning.","featured":true,"schema":{"fields":[{"name":"subject","label":"Subject","type":"text","placeholder":"ritual, myth, institution, symbol, text, policy, design"},{"name":"context","label":"Context","type":"textarea","placeholder":"Describe the material to interpret."}]}}]
JSON;
        $tools = json_decode($json, true);
        return is_array($tools) ? $tools : [];
    }

    private function filter_local_tools($tools, $query) {
        $topic = isset($query['topic']) ? strtolower(str_replace('-', ' ', (string)$query['topic'])) : '';
        $domain = isset($query['domain']) ? strtolower((string)$query['domain']) : '';
        $limit = isset($query['limit']) ? max(1, min(100, absint($query['limit']))) : 100;
        $filtered = [];
        foreach ($tools as $tool) {
            $haystack = strtolower(($tool['id'] ?? '') . ' ' . ($tool['title'] ?? '') . ' ' . ($tool['domain'] ?? '') . ' ' . ($tool['description'] ?? ''));
            if ($domain && strpos(strtolower($tool['domain'] ?? ''), $domain) === false) { continue; }
            if ($topic && strpos($haystack, $topic) === false) { continue; }
            $filtered[] = $tool;
        }
        if (!$filtered) {
            foreach ($tools as $tool) { if (!empty($tool['featured'])) { $filtered[] = $tool; } }
        }
        return array_slice($filtered ?: $tools, 0, $limit);
    }

    public function register_rest_routes() {
        register_rest_route('sc-workbench/v1', '/tools', ['methods'=>'GET', 'callback'=>[$this,'rest_tools'], 'permission_callback'=>'__return_true']);
        register_rest_route('sc-workbench/v1', '/run', ['methods'=>'POST', 'callback'=>[$this,'rest_run_tool'], 'permission_callback'=>'__return_true']);
        register_rest_route('sc-workbench/v1', '/ask', ['methods'=>'POST', 'callback'=>[$this,'rest_ask'], 'permission_callback'=>'__return_true']);
        register_rest_route('sc-workbench/v1', '/health', ['methods'=>'GET', 'callback'=>[$this,'rest_health'], 'permission_callback'=>[$this,'admin_permission']]);
        register_rest_route('sc-workbench/v1', '/ai-status', ['methods'=>'GET', 'callback'=>[$this,'rest_ai_status'], 'permission_callback'=>[$this,'admin_permission']]);
    }

    public function admin_permission() { return current_user_can('manage_options'); }

    public function rest_tools(WP_REST_Request $request) {
        $query = [];
        foreach (['topic','domain','limit'] as $key) { if ($request->get_param($key)) { $query[$key] = sanitize_text_field($request->get_param($key)); } }
        $response = $this->backend_get('/tools' . ($query ? '?' . http_build_query($query) : ''));
        if (!is_wp_error($response) && !empty($response['tools']) && is_array($response['tools'])) {
            return new WP_REST_Response($response, 200);
        }
        $tools = $this->filter_local_tools($this->local_tools(), $query);
        return new WP_REST_Response([
            'ok' => true,
            'fallback' => true,
            'message' => is_wp_error($response) ? $response->get_error_message() : 'Backend returned no tools; using bundled Workbench tool schemas.',
            'tools' => $tools,
        ], 200);
    }

    public function rest_run_tool(WP_REST_Request $request) {
        $payload = $request->get_json_params();
        $response = $this->backend_post('/tools/run', is_array($payload) ? $payload : []);
        if (is_wp_error($response)) { return new WP_REST_Response(['ok'=>false, 'error'=>'The calculator is available, but the analytics backend is not reachable. Start the FastAPI backend or set a deployed HTTPS Backend URL in SC Workbench settings. Details: ' . $response->get_error_message()], 200); }
        return new WP_REST_Response($response, 200);
    }

    public function rest_ask(WP_REST_Request $request) {
        if (get_option(self::OPTION_ENABLE_AI, '1') !== '1') { return new WP_REST_Response(['ok'=>false, 'answer'=>'AI is disabled in Workbench settings.'], 200); }
        $payload = $request->get_json_params();
        if (!is_array($payload)) { $payload = []; }
        if (empty($payload['topic'])) { $payload['topic'] = get_option(self::OPTION_DEFAULT_TOPIC, 'research-library'); }
        $payload['scope_gate_enabled'] = get_option(self::OPTION_ENABLE_SCOPE_GATE, '1') === '1';
        $response = $this->backend_post('/ai/ask-library', $payload);
        if (is_wp_error($response)) { return new WP_REST_Response(['ok'=>false, 'answer'=>'The Workbench analytics backend is not reachable. Start the FastAPI backend locally or deploy it to a public HTTPS URL. Calculators require the backend in v0.4.2.', 'error'=>$response->get_error_message()], 200); }
        return new WP_REST_Response($response, 200);
    }

    public function rest_health() { $res = $this->backend_get('/health'); return new WP_REST_Response(is_wp_error($res) ? ['ok'=>false,'error'=>$res->get_error_message()] : $res, 200); }
    public function rest_ai_status() { $res = $this->backend_get('/ai/status'); return new WP_REST_Response(is_wp_error($res) ? ['ok'=>false,'error'=>$res->get_error_message()] : $res, 200); }

    private function backend_get($path) {
        $url = trailingslashit(get_option(self::OPTION_BACKEND_URL, 'http://127.0.0.1:8088')) . ltrim($path, '/');
        $args = ['timeout'=>(int)get_option(self::OPTION_TIMEOUT, '45'), 'headers'=>$this->backend_headers()];
        return $this->decode_backend_response(wp_remote_get($url, $args));
    }

    private function backend_post($path, $payload) {
        $url = trailingslashit(get_option(self::OPTION_BACKEND_URL, 'http://127.0.0.1:8088')) . ltrim($path, '/');
        $args = ['timeout'=>(int)get_option(self::OPTION_TIMEOUT, '45'), 'headers'=>array_merge(['Content-Type'=>'application/json'], $this->backend_headers()), 'body'=>wp_json_encode($payload)];
        return $this->decode_backend_response(wp_remote_post($url, $args));
    }

    private function backend_headers() {
        $headers = [];
        $key = get_option(self::OPTION_API_KEY, '');
        if ($key) { $headers['X-SC-Workbench-Key'] = $key; }
        $provider = $this->decrypt_provider_key();
        if ($provider) { $headers['X-SC-Provider-Key'] = $provider; }
        return $headers;
    }

    private function decode_backend_response($res) {
        if (is_wp_error($res)) { return $res; }
        $code = wp_remote_retrieve_response_code($res);
        $body = wp_remote_retrieve_body($res);
        $json = json_decode($body, true);
        if ($code < 200 || $code >= 300) { return new WP_Error('scwb_backend_error', 'Workbench backend returned HTTP ' . $code . ': ' . wp_strip_all_tags($body)); }
        if (!is_array($json)) { return new WP_Error('scwb_invalid_json', 'Workbench backend returned invalid JSON.'); }
        return $json;
    }

    public function register_admin_menu() {
        add_menu_page('SC Workbench', 'SC Workbench', 'manage_options', 'sustainable-catalyst-workbench', [$this,'render_admin_page'], 'dashicons-chart-area', 58);
    }

    public function register_settings() {
        register_setting(self::OPTION_GROUP, self::OPTION_BACKEND_URL, ['sanitize_callback'=>'esc_url_raw']);
        register_setting(self::OPTION_GROUP, self::OPTION_API_KEY, ['sanitize_callback'=>'sanitize_text_field']);
        register_setting(self::OPTION_GROUP, self::OPTION_ENABLE_AI, ['sanitize_callback'=>[$this,'checkbox']]);
        register_setting(self::OPTION_GROUP, self::OPTION_ENABLE_SCOPE_GATE, ['sanitize_callback'=>[$this,'checkbox']]);
        register_setting(self::OPTION_GROUP, self::OPTION_DEBUG, ['sanitize_callback'=>[$this,'checkbox']]);
        register_setting(self::OPTION_GROUP, self::OPTION_TIMEOUT, ['sanitize_callback'=>'absint']);
        register_setting(self::OPTION_GROUP, self::OPTION_DEFAULT_TOPIC, ['sanitize_callback'=>'sanitize_key']);
        register_setting(self::OPTION_GROUP, self::OPTION_THEME, ['sanitize_callback'=>'sanitize_key']);
        register_setting(self::OPTION_GROUP, self::OPTION_PROVIDER_KEY, ['sanitize_callback'=>[$this,'sanitize_provider_key']]);
    }

    public function checkbox($value) { return $value ? '1' : '0'; }

    public function sanitize_provider_key($value) {
        $value = trim((string)$value);
        if ($value === '') { return get_option(self::OPTION_PROVIDER_KEY, ''); }
        if ($value === '__delete__') { return ''; }
        return $this->encrypt_provider_key($value);
    }

    private function secret_key_material() {
        $salt = (defined('AUTH_KEY') ? AUTH_KEY : '') . (defined('SECURE_AUTH_KEY') ? SECURE_AUTH_KEY : '') . (defined('LOGGED_IN_KEY') ? LOGGED_IN_KEY : '');
        if (!$salt) { $salt = wp_salt('auth'); }
        return hash('sha256', $salt, true);
    }

    private function encrypt_provider_key($plain) {
        if (!function_exists('openssl_encrypt')) { return 'plain:' . base64_encode($plain); }
        $iv = random_bytes(16);
        $ct = openssl_encrypt($plain, 'AES-256-CBC', $this->secret_key_material(), OPENSSL_RAW_DATA, $iv);
        return 'enc:' . base64_encode(json_encode(['iv'=>base64_encode($iv), 'ct'=>base64_encode($ct)]));
    }

    private function decrypt_provider_key() {
        $stored = get_option(self::OPTION_PROVIDER_KEY, '');
        if (!$stored) { return ''; }
        if (strpos($stored, 'plain:') === 0) { return base64_decode(substr($stored, 6)); }
        if (strpos($stored, 'enc:') !== 0 || !function_exists('openssl_decrypt')) { return ''; }
        $data = json_decode(base64_decode(substr($stored, 4)), true);
        if (!$data || empty($data['iv']) || empty($data['ct'])) { return ''; }
        return (string)openssl_decrypt(base64_decode($data['ct']), 'AES-256-CBC', $this->secret_key_material(), OPENSSL_RAW_DATA, base64_decode($data['iv']));
    }

    public function render_admin_page() {
        $has_provider = $this->decrypt_provider_key() ? true : false;
        ?>
        <div class="wrap scwb-admin-wrap">
            <h1>Sustainable Catalyst Workbench</h1>
            <p>Configure the compact Research Library assistant, analytics backend, AI scope gate, and calculator engine.</p>
            <form method="post" action="options.php" class="scwb-admin-card">
                <?php settings_fields(self::OPTION_GROUP); ?>
                <h2>Backend API</h2>
                <table class="form-table" role="presentation">
                    <tr><th scope="row">Backend URL</th><td><input class="regular-text" type="url" name="<?php echo esc_attr(self::OPTION_BACKEND_URL); ?>" value="<?php echo esc_attr(get_option(self::OPTION_BACKEND_URL, 'http://127.0.0.1:8088')); ?>"><p class="description">Local: http://127.0.0.1:8088. Production: use a public HTTPS backend URL.</p></td></tr>
                    <tr><th scope="row">Shared Backend Key</th><td><input class="regular-text" type="password" name="<?php echo esc_attr(self::OPTION_API_KEY); ?>" value="<?php echo esc_attr(get_option(self::OPTION_API_KEY, '')); ?>"><p class="description">Optional X-SC-Workbench-Key for backend access control.</p></td></tr>
                    <tr><th scope="row">Timeout</th><td><input type="number" min="5" max="120" name="<?php echo esc_attr(self::OPTION_TIMEOUT); ?>" value="<?php echo esc_attr(get_option(self::OPTION_TIMEOUT, '45')); ?>"> seconds</td></tr>
                </table>
                <h2>AI Provider</h2>
                <p class="notice notice-warning inline"><strong>Preferred production setup:</strong> store the provider key in the Python backend .env file. This WordPress field is included for local testing or controlled deployments.</p>
                <table class="form-table" role="presentation">
                    <tr><th scope="row">OpenAI API Key</th><td><input class="regular-text" type="password" name="<?php echo esc_attr(self::OPTION_PROVIDER_KEY); ?>" value="" placeholder="<?php echo $has_provider ? esc_attr('Key saved — leave blank to keep it') : esc_attr('Paste key here if you choose WordPress-managed key'); ?>"><p class="description">Saved keys are encrypted using WordPress salts when OpenSSL is available. Enter <code>__delete__</code> to remove the saved key.</p></td></tr>
                    <tr><th scope="row">Enable AI panels</th><td><label><input type="checkbox" name="<?php echo esc_attr(self::OPTION_ENABLE_AI); ?>" value="1" <?php checked(get_option(self::OPTION_ENABLE_AI, '1'), '1'); ?>> Enabled</label></td></tr>
                    <tr><th scope="row">Enable scope gate</th><td><label><input type="checkbox" name="<?php echo esc_attr(self::OPTION_ENABLE_SCOPE_GATE); ?>" value="1" <?php checked(get_option(self::OPTION_ENABLE_SCOPE_GATE, '1'), '1'); ?>> Restrict assistant to Sustainable Catalyst topics</label></td></tr>
                    <tr><th scope="row">Default Topic</th><td><input class="regular-text" type="text" name="<?php echo esc_attr(self::OPTION_DEFAULT_TOPIC); ?>" value="<?php echo esc_attr(get_option(self::OPTION_DEFAULT_TOPIC, 'research-library')); ?>"></td></tr>
                    <tr><th scope="row">Theme</th><td><select name="<?php echo esc_attr(self::OPTION_THEME); ?>"><option value="institutional" <?php selected(get_option(self::OPTION_THEME, 'institutional'), 'institutional'); ?>>Institutional</option><option value="compact" <?php selected(get_option(self::OPTION_THEME, 'institutional'), 'compact'); ?>>Compact</option></select></td></tr>
                    <tr><th scope="row">Debug mode</th><td><label><input type="checkbox" name="<?php echo esc_attr(self::OPTION_DEBUG); ?>" value="1" <?php checked(get_option(self::OPTION_DEBUG, '0'), '1'); ?>> Enabled</label></td></tr>
                </table>
                <?php submit_button('Save Workbench Settings'); ?>
            </form>
            <div class="scwb-admin-card">
                <h2>Shortcode</h2>
                <p>Use this compact Workbench on the Research Library page or any article page:</p>
                <code>[sc_workbench]</code>
                <p><button class="button button-primary" type="button" data-scwb-admin-test>Test Backend + AI</button></p>
                <pre data-scwb-admin-output></pre>
            </div>
        </div>
        <?php
    }
}

new SC_Workbench_Plugin();
register_activation_hook(__FILE__, ['SC_Workbench_Plugin', 'activate']);
