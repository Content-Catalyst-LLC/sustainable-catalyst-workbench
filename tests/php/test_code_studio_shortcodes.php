<?php
const ABSPATH = '/tmp';
function add_action(...$args) {}
function register_activation_hook(...$args) {}
function add_shortcode(...$args) {}
function wp_register_style(...$args) {}
function wp_register_script(...$args) {}
function wp_localize_script(...$args) {}
function wp_enqueue_style(...$args) {}
function wp_enqueue_script(...$args) {}
function plugin_dir_url($file) { return 'https://example.test/plugin/'; }
function rest_url($path = '') { return 'https://example.test/wp-json/' . $path; }
function wp_create_nonce($action) { return 'nonce'; }
function get_option($key, $default = null) { return $default; }
function shortcode_atts($defaults, $atts, $shortcode = '') { return array_merge($defaults, (array) $atts); }
function wp_generate_uuid4() { return '12345678-1234-1234-1234-123456789abc'; }
function sanitize_key($value) { return strtolower(preg_replace('/[^a-z0-9_\-]/', '', (string) $value)); }
function sanitize_text_field($value) { return trim(strip_tags((string) $value)); }
function esc_attr($value) { return htmlspecialchars((string) $value, ENT_QUOTES); }
function esc_html($value) { return htmlspecialchars((string) $value, ENT_QUOTES); }

require dirname(__DIR__, 2) . '/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php';

$plugin = new SC_Workbench_Plugin();
$studio = $plugin->render_code_studio(['project' => 'test-project']);
$terminal = $plugin->render_terminal(['project' => 'test-project']);

$requiredStudioMarkers = [
    'data-scwb-code-studio',
    'data-scwb-terminal-input',
    'data-scwb-code-editor',
    'data-scwb-code-files',
    'data-scwb-code-events',
    'data-scwb-code-panel="code"',
    'data-scwb-code-panel="results"',
    'data-scwb-run-output',
    'data-scwb-file-select',
    'data-scwb-line-numbers',
    'data-scwb-code-panel="documentation"',
    'data-scwb-runtime-select',
    'data-scwb-load-runtime',
    'data-scwb-run-active',
    'data-scwb-stop-active',
    'data-scwb-chart-results',
];

foreach ($requiredStudioMarkers as $marker) {
    if (strpos($studio, $marker) === false) {
        throw new RuntimeException('Missing Code Studio marker: ' . $marker);
    }
}

if (strpos($terminal, 'scwb-code-studio-terminal-only') === false) {
    throw new RuntimeException('Terminal-only presentation marker missing.');
}

if (strpos($studio, 'Workbench v1.9.1') === false) {
    throw new RuntimeException('v1.9.1 release marker missing.');
}

if (strpos($studio, 'Write code, click Run') === false) {
    throw new RuntimeException('Editor-first Run experience marker missing.');
}

fwrite(STDOUT, "WordPress Code Studio shortcode tests passed.\n");
