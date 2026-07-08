<?php
/**
 * Plugin Name: Sustainable Catalyst Workbench
 * Description: Site-scoped Workbench tools, calculators, diagnostics, and Research Library AI panels for Sustainable Catalyst.
 * Version: 0.1.0
 * Author: Content Catalyst LLC
 * License: MIT
 * Text Domain: sustainable-catalyst-workbench
 */

if (!defined('ABSPATH')) {
    exit;
}

final class SC_Workbench_Plugin {
    const VERSION = '0.1.0';
    const OPTION_BACKEND_URL = 'sc_workbench_backend_url';

    public function __construct() {
        add_action('init', [$this, 'register_shortcodes']);
        add_action('wp_enqueue_scripts', [$this, 'enqueue_assets']);
        add_action('rest_api_init', [$this, 'register_rest_routes']);
        add_action('admin_menu', [$this, 'register_admin_menu']);
        add_action('admin_init', [$this, 'register_settings']);
    }

    public static function activate() {
        if (!get_option(self::OPTION_BACKEND_URL)) {
            add_option(self::OPTION_BACKEND_URL, 'http://127.0.0.1:8088');
        }
    }

    public function enqueue_assets() {
        wp_register_style(
            'sc-workbench',
            plugin_dir_url(__FILE__) . 'assets/sc-workbench.css',
            [],
            self::VERSION
        );

        wp_register_script(
            'sc-workbench',
            plugin_dir_url(__FILE__) . 'assets/sc-workbench.js',
            [],
            self::VERSION,
            true
        );

        wp_localize_script('sc-workbench', 'SCWorkbench', [
            'restUrl' => esc_url_raw(rest_url('sc-workbench/v1')),
            'nonce' => wp_create_nonce('wp_rest'),
        ]);
    }

    public function register_shortcodes() {
        add_shortcode('sc_workbench', [$this, 'render_workbench_shortcode']);
        add_shortcode('sc_workbench_tools', [$this, 'render_tools_shortcode']);
        add_shortcode('sc_workbench_ai', [$this, 'render_ai_shortcode']);
    }

    private function ensure_assets() {
        wp_enqueue_style('sc-workbench');
        wp_enqueue_script('sc-workbench');
    }

    public function render_workbench_shortcode($atts) {
        $this->ensure_assets();
        $atts = shortcode_atts([
            'tool' => '',
            'topic' => '',
        ], $atts, 'sc_workbench');

        $tool = sanitize_key($atts['tool']);
        $topic = sanitize_key($atts['topic']);
        $uid = 'scwb-' . wp_generate_uuid4();

        ob_start();
        ?>
        <section id="<?php echo esc_attr($uid); ?>" class="scwb-panel" data-scwb-panel data-tool="<?php echo esc_attr($tool); ?>" data-topic="<?php echo esc_attr($topic); ?>">
            <p class="scwb-eyebrow">Sustainable Catalyst Workbench</p>
            <h2 class="scwb-title"><?php echo $tool ? esc_html($this->tool_title_from_id($tool)) : esc_html__('Workbench Tools', 'sustainable-catalyst-workbench'); ?></h2>
            <p class="scwb-lede">Use site-scoped calculators, diagnostics, models, and interpretive frameworks connected to Sustainable Catalyst.</p>
            <div class="scwb-body" data-scwb-body>
                <div class="scwb-loading">Loading Workbench tools…</div>
            </div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function render_tools_shortcode($atts) {
        $this->ensure_assets();
        $atts = shortcode_atts([
            'topic' => '',
            'domain' => '',
        ], $atts, 'sc_workbench_tools');

        $uid = 'scwb-tools-' . wp_generate_uuid4();
        ob_start();
        ?>
        <section id="<?php echo esc_attr($uid); ?>" class="scwb-panel scwb-tools-panel" data-scwb-tools data-topic="<?php echo esc_attr(sanitize_key($atts['topic'])); ?>" data-domain="<?php echo esc_attr(sanitize_text_field($atts['domain'])); ?>">
            <p class="scwb-eyebrow">Related Workbench Tools</p>
            <h2 class="scwb-title">Tools for This Research Area</h2>
            <div class="scwb-card-grid" data-scwb-tools-grid>
                <div class="scwb-loading">Loading tools…</div>
            </div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function render_ai_shortcode($atts) {
        $this->ensure_assets();
        $atts = shortcode_atts([
            'mode' => 'library-guide',
            'topic' => '',
        ], $atts, 'sc_workbench_ai');

        $uid = 'scwb-ai-' . wp_generate_uuid4();
        ob_start();
        ?>
        <section id="<?php echo esc_attr($uid); ?>" class="scwb-panel scwb-ai-panel" data-scwb-ai data-mode="<?php echo esc_attr(sanitize_key($atts['mode'])); ?>" data-topic="<?php echo esc_attr(sanitize_key($atts['topic'])); ?>">
            <p class="scwb-eyebrow">Sustainable Catalyst AI</p>
            <h2 class="scwb-title">Ask the Research Library</h2>
            <p class="scwb-lede">This assistant is restricted to Sustainable Catalyst topics, tools, research paths, repositories, and educational frameworks.</p>
            <form class="scwb-ai-form" data-scwb-ai-form>
                <label class="screen-reader-text" for="<?php echo esc_attr($uid); ?>-question">Question</label>
                <textarea id="<?php echo esc_attr($uid); ?>-question" name="question" rows="4" placeholder="Ask about sustainability, governance, systems thinking, mathematical modeling, AI, natural science, psychology, philosophy, meaning, or related Sustainable Catalyst topics."></textarea>
                <button type="submit" class="scwb-button">Ask Sustainable Catalyst</button>
            </form>
            <div class="scwb-ai-result" data-scwb-ai-result></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function register_rest_routes() {
        register_rest_route('sc-workbench/v1', '/tools', [
            'methods' => 'GET',
            'callback' => [$this, 'rest_tools'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route('sc-workbench/v1', '/run', [
            'methods' => 'POST',
            'callback' => [$this, 'rest_run_tool'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route('sc-workbench/v1', '/ask', [
            'methods' => 'POST',
            'callback' => [$this, 'rest_ask'],
            'permission_callback' => '__return_true',
        ]);
    }

    public function rest_tools(WP_REST_Request $request) {
        $response = $this->backend_get('/tools');
        if (is_wp_error($response)) {
            return new WP_REST_Response([
                'ok' => false,
                'error' => $response->get_error_message(),
                'fallback_tools' => $this->local_tool_registry(),
            ], 200);
        }
        return new WP_REST_Response($response, 200);
    }

    public function rest_run_tool(WP_REST_Request $request) {
        $payload = $request->get_json_params();
        $response = $this->backend_post('/tools/run', $payload ?: []);
        if (is_wp_error($response)) {
            return new WP_REST_Response([
                'ok' => false,
                'error' => $response->get_error_message(),
            ], 502);
        }
        return new WP_REST_Response($response, 200);
    }

    public function rest_ask(WP_REST_Request $request) {
        $payload = $request->get_json_params();
        $response = $this->backend_post('/ai/ask-library', $payload ?: []);
        if (is_wp_error($response)) {
            return new WP_REST_Response([
                'ok' => false,
                'error' => $response->get_error_message(),
                'answer' => 'The Workbench backend is not reachable yet. Check the backend URL in Settings → Sustainable Catalyst Workbench.',
            ], 200);
        }
        return new WP_REST_Response($response, 200);
    }

    private function backend_get($path) {
        $url = trailingslashit(get_option(self::OPTION_BACKEND_URL, 'http://127.0.0.1:8088')) . ltrim($path, '/');
        $res = wp_remote_get($url, ['timeout' => 15]);
        return $this->decode_backend_response($res);
    }

    private function backend_post($path, $payload) {
        $url = trailingslashit(get_option(self::OPTION_BACKEND_URL, 'http://127.0.0.1:8088')) . ltrim($path, '/');
        $res = wp_remote_post($url, [
            'timeout' => 30,
            'headers' => ['Content-Type' => 'application/json'],
            'body' => wp_json_encode($payload),
        ]);
        return $this->decode_backend_response($res);
    }

    private function decode_backend_response($res) {
        if (is_wp_error($res)) {
            return $res;
        }
        $code = wp_remote_retrieve_response_code($res);
        $body = wp_remote_retrieve_body($res);
        $json = json_decode($body, true);
        if ($code < 200 || $code >= 300) {
            return new WP_Error('scwb_backend_error', 'Workbench backend returned HTTP ' . $code);
        }
        if (!is_array($json)) {
            return new WP_Error('scwb_invalid_json', 'Workbench backend returned invalid JSON.');
        }
        return $json;
    }

    public function register_admin_menu() {
        add_options_page(
            'Sustainable Catalyst Workbench',
            'Sustainable Catalyst Workbench',
            'manage_options',
            'sustainable-catalyst-workbench',
            [$this, 'render_admin_page']
        );
    }

    public function register_settings() {
        register_setting('sc_workbench_settings', self::OPTION_BACKEND_URL, [
            'type' => 'string',
            'sanitize_callback' => 'esc_url_raw',
            'default' => 'http://127.0.0.1:8088',
        ]);
    }

    public function render_admin_page() {
        ?>
        <div class="wrap">
            <h1>Sustainable Catalyst Workbench</h1>
            <p>Configure the backend API used by Workbench tools and site-scoped AI panels.</p>
            <form method="post" action="options.php">
                <?php settings_fields('sc_workbench_settings'); ?>
                <table class="form-table" role="presentation">
                    <tr>
                        <th scope="row"><label for="<?php echo esc_attr(self::OPTION_BACKEND_URL); ?>">Backend API URL</label></th>
                        <td>
                            <input name="<?php echo esc_attr(self::OPTION_BACKEND_URL); ?>" id="<?php echo esc_attr(self::OPTION_BACKEND_URL); ?>" type="url" class="regular-text" value="<?php echo esc_attr(get_option(self::OPTION_BACKEND_URL, 'http://127.0.0.1:8088')); ?>" />
                            <p class="description">Example: http://127.0.0.1:8088 or https://api.sustainablecatalyst.com</p>
                        </td>
                    </tr>
                </table>
                <?php submit_button(); ?>
            </form>
        </div>
        <?php
    }

    private function tool_title_from_id($tool) {
        $map = [];
        foreach ($this->local_tool_registry() as $entry) {
            $map[$entry['id']] = $entry['title'];
        }
        return isset($map[$tool]) ? $map[$tool] : ucwords(str_replace('-', ' ', $tool));
    }

    private function local_tool_registry() {
        return [
            ['id' => 'linear-system-solver', 'title' => 'Linear Algebra Systems Solver', 'type' => 'calculator', 'domain' => 'Mathematical Modeling'],
            ['id' => 'decision-matrix', 'title' => 'Decision Matrix', 'type' => 'decision-support', 'domain' => 'Problem Solving'],
            ['id' => 'risk-resilience-scorecard', 'title' => 'Risk & Resilience Scorecard', 'type' => 'diagnostic', 'domain' => 'Sustainable Systems'],
            ['id' => 'ai-governance-audit', 'title' => 'AI Governance Audit', 'type' => 'audit', 'domain' => 'Technology & Systems Intelligence'],
            ['id' => 'sustainability-tradeoff-matrix', 'title' => 'Sustainability Tradeoff Matrix', 'type' => 'hybrid', 'domain' => 'Sustainable Systems'],
            ['id' => 'qualitative-interpretation-matrix', 'title' => 'Qualitative Interpretation Matrix', 'type' => 'interpretive', 'domain' => 'Meaning'],
            ['id' => 'research-library-assistant', 'title' => 'Research Library Assistant', 'type' => 'ai-guide', 'domain' => 'Research Library'],
            ['id' => 'workbench-tool-finder', 'title' => 'Workbench Tool Finder', 'type' => 'router', 'domain' => 'Research Library'],
        ];
    }
}

register_activation_hook(__FILE__, ['SC_Workbench_Plugin', 'activate']);
new SC_Workbench_Plugin();
