<?php
/** Minimal WordPress action/shortcode harness for Workbench activation. */
define('ABSPATH', __DIR__ . '/');
$GLOBALS['scwb_actions'] = array();
$GLOBALS['scwb_shortcodes'] = array();
$GLOBALS['scwb_filters'] = array();

function add_action($hook, $callback, $priority = 10, $accepted_args = 1) {
    $GLOBALS['scwb_actions'][$hook][$priority][] = $callback;
}
function add_filter($hook, $callback, $priority = 10, $accepted_args = 1) {
    $GLOBALS['scwb_filters'][$hook][$priority][] = $callback;
}
function add_shortcode($tag, $callback) { $GLOBALS['scwb_shortcodes'][$tag] = $callback; }
function remove_shortcode($tag) { unset($GLOBALS['scwb_shortcodes'][$tag]); }
function shortcode_exists($tag) { return isset($GLOBALS['scwb_shortcodes'][$tag]); }
function wp_register_style() { return true; }
function wp_register_script() { return true; }
function plugins_url($path = '', $plugin = '') { return '/plugins/' . ltrim($path, '/'); }
function __($text, $domain = null) { return $text; }
function run_hook($hook) {
    if (empty($GLOBALS['scwb_actions'][$hook])) return;
    ksort($GLOBALS['scwb_actions'][$hook]);
    foreach ($GLOBALS['scwb_actions'][$hook] as $callbacks) {
        foreach ($callbacks as $callback) { call_user_func($callback); }
    }
}

$plugin = dirname(__DIR__) . '/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php';
require $plugin;
run_hook('init');
run_hook('wp_loaded');

$expected = array(
    'sc_workbench',
    'sc_workbench_diagnostics',
    'sc_workbench_unified',
    'sc_workbench_lab_canvas',
    'sc_workbench_embedded_device_studio',
    'sc_workbench_fpga_studio',
    'sc_workbench_robotics_studio',
    'sc_workbench_instrumentation_studio',
    'sc_workbench_simulation_studio',
    'sc_workbench_multilanguage_runtime',
    'sc_workbench_scientific_visualization',
    'sc_workbench_experiment_automation',
    'sc_workbench_documentation_dossier',
    'sc_workbench_migration_recovery',
);

$missing = array_values(array_filter($expected, static function($tag) { return !shortcode_exists($tag); }));
if ($missing) {
    fwrite(STDERR, 'Missing runtime shortcodes: ' . implode(', ', $missing) . "\n");
    exit(1);
}

$primary = $GLOBALS['scwb_shortcodes']['sc_workbench'];
if (!is_array($primary) || 'SCWB_Primary_Shortcode_Repair' !== $primary[0] || 'render' !== $primary[1]) {
    fwrite(STDERR, "Canonical sc_workbench ownership was not restored.\n");
    exit(1);
}

echo 'Workbench v3.0.2 WordPress runtime activation passed for ' . count($expected) . " required shortcodes.\n";
