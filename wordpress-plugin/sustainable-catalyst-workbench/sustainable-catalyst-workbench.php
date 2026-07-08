<?php
/**
 * Plugin Name: Sustainable Catalyst Workbench
 * Description: Compact AI-enabled research and analytics workbench with Python/R/Julia/Haskell-ready backend, advanced calculators, serious global-impact tools, SVG visual analytics, and Gemini/DeepSeek/OpenAI provider support, exportable SVG/PNG graph images, and PDF-ready reports.
 * Version: 0.9.1
 * Author: Content Catalyst LLC
 * License: MIT
 * Text Domain: sustainable-catalyst-workbench
 */

if (!defined('ABSPATH')) { exit; }

final class SC_Workbench_Plugin {
    const VERSION = '0.9.1';
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
            'article' => ''
        ], $atts, 'sc_workbench');
        $uid = 'scwb-' . wp_generate_uuid4();
        $current_post_id = get_queried_object_id();
        $article_slug = $atts['article'] ? sanitize_title($atts['article']) : ($current_post_id ? get_post_field('post_name', $current_post_id) : '');
        ob_start(); ?>
        <section id="<?php echo esc_attr($uid); ?>" class="scwb scwb-theme-<?php echo esc_attr(get_option(self::OPTION_THEME, 'institutional')); ?>" data-scwb data-topic="<?php echo esc_attr(sanitize_key($atts['topic'])); ?>" data-mode="<?php echo esc_attr(sanitize_key($atts['mode'])); ?>" data-post-id="<?php echo esc_attr($current_post_id); ?>" data-article-slug="<?php echo esc_attr($article_slug); ?>">
            <div class="scwb-head">
                <p class="scwb-eyebrow">Sustainable Catalyst Workbench</p>
                <h2><?php echo esc_html(sanitize_text_field($atts['title'])); ?></h2>
                <p>A compact research and analytics tool for asking questions, running calculators, generating graphs, and following model-aware pathways across the Sustainable Catalyst knowledge system.</p>
            </div>
            <div class="scwb-mode-row" role="tablist" aria-label="Workbench modes">
                <button type="button" class="is-active" data-scwb-tab="ask">Ask</button>
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


    public function maybe_install() {
        $old_version = get_option(self::OPTION_VERSION, '');
        if ($old_version !== self::VERSION) {
            self::create_equation_table();
            // v0.9.1 fixes the first equation scanner, which was too permissive and could index HTML table fragments.
            // The equation table is a generated cache, so it is safe to clear during this upgrade and rebuild from posts.
            if ($old_version && version_compare($old_version, '0.9.1', '<')) {
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
        return trim(preg_replace('/\s+/', ' ', $eq));
    }

    private function equation_candidate_has_math_signal($eq) {
        $eq = trim((string)$eq);
        if ($eq === '') { return false; }
        return (bool) preg_match('/(=|\+|\-|\*|\/|\^|_|:|\\(frac|sum|prod|int|partial|nabla|times|cdot|sim|in|notin|geq|leq|approx|rightarrow|leftarrow|alpha|beta|gamma|delta|epsilon|lambda|mu|nu|theta|sigma|kappa|omega)|[A-Za-z]_\{?[A-Za-z0-9]|[A-Za-z]\([0-9A-Za-z]+\))/', $eq);
    }

    private function is_valid_equation_candidate($raw, $normalized, $mode='inline') {
        $raw = (string)$raw;
        $eq = trim((string)$normalized);
        $len = strlen($eq);
        if ($len < 3 || $len > 520) { return false; }

        // Reject broken delimiter captures and HTML/table fragments.
        if (preg_match('/(<\/?[a-z][^>]*>|&lt;\/?[a-z]|&gt;|<|>)/i', $eq)) { return false; }
        if (preg_match('/(<\/?(td|tr|th|table|tbody|thead|div|p|span|code|strong|em|pre)\b|&lt;\/?(td|tr|th|table|tbody|thead|div|p|span|code|strong|em|pre)\b)/i', $raw)) { return false; }
        if (preg_match('/(^\\\)|^\\\]|\\\($|\\\[$|\\\)$|\\\]$)/', $eq)) { return false; }
        if (preg_match('/\\\)\s*.*\\\(|\\\]\s*.*\\\[/', $eq)) { return false; }

        // Reject prose, captions, code exports, and table/cell text accidentally captured between malformed delimiters.
        if (preg_match('/\b(interpretation|represents|exported|summary|article title|suggested domain|graphability|recommended tool|back to top|knowledge layer|computational expression|data logic|what changed|what is building|what procedure|policy coherence|long-horizon|capability expansion)\b/i', $eq)) { return false; }
        if (preg_match('/\b(print|return|import|output_file|summary exported|cross-territory|console\.log)\b/i', $eq)) { return false; }

        // Single-letter inline variables create noise in a site-wide registry; keep subscripted/superscripted variables and real expressions.
        if ($mode === 'inline' && preg_match('/^[A-Za-z]$/', $eq)) { return false; }
        if ($mode === 'inline' && $len < 6 && !preg_match('/[_^=+\-*\/]|\\(alpha|beta|gamma|delta|lambda|mu|nu|theta|sigma)/', $eq)) { return false; }

        if (!$this->equation_candidate_has_math_signal($eq)) { return false; }

        // A candidate with many ordinary words is almost certainly prose between broken delimiters.
        preg_match_all('/\b[A-Za-z]{4,}\b/', $eq, $word_matches);
        $word_count = count($word_matches[0]);
        if ($word_count > 5 && $mode === 'inline') { return false; }
        if ($word_count > 10 && $mode !== 'inline') { return false; }

        return true;
    }

    private function extract_equations_from_content($content) {
        $content = (string)$content;

        // Remove regions where LaTeX-looking delimiters often appear as literal code or generated output.
        $content = preg_replace('/<script\b[^>]*>.*?<\/script>/is', ' ', $content);
        $content = preg_replace('/<style\b[^>]*>.*?<\/style>/is', ' ', $content);
        $content = preg_replace('/<pre\b[^>]*>.*?<\/pre>/is', ' ', $content);
        $content = preg_replace('/<code\b[^>]*>.*?<\/code>/is', ' ', $content);

        $patterns = [
            ['pattern' => '/\[latex\]([\s\S]{1,1200}?)\[\/latex\]/i', 'mode' => 'shortcode'],
            ['pattern' => '/\\\[((?:(?!\\\]).){1,1200})\\\]/s', 'mode' => 'display'],
            ['pattern' => '/\$\$([\s\S]{1,1200}?)\$\$/s', 'mode' => 'display'],
            ['pattern' => '/\\\(((?:(?!\\\)).){1,420})\\\)/s', 'mode' => 'inline'],
        ];
        $found = [];
        foreach ($patterns as $p) {
            if (preg_match_all($p['pattern'], $content, $matches, PREG_SET_ORDER | PREG_OFFSET_CAPTURE)) {
                foreach ($matches as $m) {
                    $raw = $m[0][0];
                    $inner = $m[1][0] ?? $raw;
                    $offset = intval($m[0][1]);
                    $normalized = $this->normalize_equation($raw);
                    if (!$this->is_valid_equation_candidate($raw, $normalized, $p['mode'])) { continue; }
                    $before_raw = substr($content, max(0, $offset - 650), min(650, $offset));
                    $after_raw = substr($content, $offset + strlen($raw), 650);
                    $found[] = [
                        'raw' => $raw,
                        'inner' => $inner,
                        'normalized' => $normalized,
                        'display_mode' => $p['mode'],
                        'offset' => $offset,
                        'context_before' => $this->clean_equation_context($before_raw, true),
                        'context_after' => $this->clean_equation_context($after_raw, false),
                    ];
                }
            }
        }
        usort($found, fn($a,$b) => $a['offset'] <=> $b['offset']);
        $seen = [];
        $unique = [];
        foreach ($found as $item) {
            $key = hash('sha256', $item['display_mode'] . '|' . $item['normalized'] . '|' . $item['offset']);
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
            <section class="scwb-admin-card"><h2>Shortcodes</h2><code>[sc_workbench topic="research-library" title="Ask the Sustainable Catalyst Workbench"]</code><br><code>[sc_workbench mode="auto"]</code><br><code>[sc_workbench article="article-slug"]</code><br><code>[sc_workbench_pathways]</code><p><a href="<?php echo esc_url(admin_url('admin.php?page=sustainable-catalyst-workbench-equations')); ?>">Open Equation Registry →</a></p></section>
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
            <p>Scan published WordPress content for clean LaTeX equations, index surrounding article context, and map equations to Workbench calculators and article-aware tools. v0.9.1 uses a stricter scanner that rejects broken delimiters, HTML table fragments, code exports, and one-letter inline variables.</p>
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
                    <p class="description">Supported patterns: <code>\(...\)</code>, <code>\[...\]</code>, <code>$$...$$</code>, and <code>[latex]...[/latex]</code>. Single-dollar inline math is intentionally not scanned by default to avoid false positives.</p>
                </section>
                <section class="scwb-admin-card">
                    <h2>Article-Aware Shortcode</h2>
                    <p>Use <code>[sc_workbench mode="auto"]</code> on articles or maps. The Workbench will detect the current post and surface article equations when available.</p>
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
}

register_activation_hook(__FILE__, ['SC_Workbench_Plugin', 'activate']);
new SC_Workbench_Plugin();
