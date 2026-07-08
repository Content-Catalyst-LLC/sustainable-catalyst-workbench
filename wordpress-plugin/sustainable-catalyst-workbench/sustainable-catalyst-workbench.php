<?php
/**
 * Plugin Name: Sustainable Catalyst Workbench
 * Description: Compact AI-enabled research and analytics workbench with Python/R/Julia/Haskell-ready backend, advanced calculators, serious global-impact tools, SVG visual analytics, and Gemini/DeepSeek/OpenAI provider support, exportable SVG/PNG graph images, and PDF-ready reports.
 * Version: 0.8.1
 * Author: Content Catalyst LLC
 * License: MIT
 * Text Domain: sustainable-catalyst-workbench
 */

if (!defined('ABSPATH')) { exit; }

final class SC_Workbench_Plugin {
    const VERSION = '0.8.1';
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

    public function __construct() {
        add_action('init', [$this, 'register_shortcodes']);
        add_action('wp_enqueue_scripts', [$this, 'enqueue_assets']);
        add_action('admin_enqueue_scripts', [$this, 'enqueue_admin_assets']);
        add_action('rest_api_init', [$this, 'register_rest_routes']);
        add_action('admin_menu', [$this, 'register_admin_menu']);
        add_action('admin_init', [$this, 'handle_settings_save']);
    }

    public static function activate() {
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
            'mode' => 'guided'
        ], $atts, 'sc_workbench');
        $uid = 'scwb-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($uid); ?>" class="scwb scwb-theme-<?php echo esc_attr(get_option(self::OPTION_THEME, 'institutional')); ?>" data-scwb data-topic="<?php echo esc_attr(sanitize_key($atts['topic'])); ?>" data-mode="<?php echo esc_attr(sanitize_key($atts['mode'])); ?>">
            <div class="scwb-head">
                <p class="scwb-eyebrow">Sustainable Catalyst Workbench</p>
                <h2><?php echo esc_html(sanitize_text_field($atts['title'])); ?></h2>
                <p>A compact research and analytics tool for asking questions, running calculators, generating graphs, and following model-aware pathways across the Sustainable Catalyst knowledge system.</p>
            </div>
            <div class="scwb-mode-row" role="tablist" aria-label="Workbench modes">
                <button type="button" class="is-active" data-scwb-tab="ask">Ask</button>
                <button type="button" data-scwb-tab="calculate">Calculate</button>
                <button type="button" data-scwb-tab="models">Models</button>
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

            <div class="scwb-panel" data-scwb-panel="pathways">
                <?php echo $this->pathways_html(); ?>
            </div>
            <p class="scwb-fineprint">Educational and analytical support only. Not a substitute for licensed engineering, architecture, clinical, legal, financial, or safety-critical professional judgment.</p>
        </section>
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

    public function register_admin_menu() {
        add_menu_page('Sustainable Catalyst Workbench', 'SC Workbench', 'manage_options', 'sustainable-catalyst-workbench', [$this,'render_settings_page'], 'dashicons-chart-area', 58);
    }

    public function handle_settings_save() {
        if (!is_admin() || !current_user_can('manage_options')) { return; }
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
            <section class="scwb-admin-card"><h2>Shortcodes</h2><code>[sc_workbench topic="research-library" title="Ask the Sustainable Catalyst Workbench"]</code><br><code>[sc_workbench_pathways]</code></section>
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
}

register_activation_hook(__FILE__, ['SC_Workbench_Plugin', 'activate']);
new SC_Workbench_Plugin();
