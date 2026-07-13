<?php
$repo = dirname(__DIR__);
$plugin = $repo . '/wordpress-plugin/sustainable-catalyst-workbench';
$failures = array();

function require_marker($path, $marker, &$failures) {
    if (!is_file($path)) {
        $failures[] = "Missing file: {$path}";
        return;
    }
    $source = file_get_contents($path);
    if (false === strpos($source, $marker)) {
        $failures[] = "Missing marker in " . basename($path) . ": {$marker}";
    }
}

$bootstrap = $plugin . '/sustainable-catalyst-workbench.php';
require_marker($bootstrap, 'Version: 3.0.1', $failures);
require_marker($bootstrap, "define('SCWB_VERSION', '3.0.1')", $failures);
require_marker($bootstrap, 'scwb-v301-production-reliability.php', $failures);
require_marker($bootstrap, 'scwb-primary-shortcode.php', $failures);

$primary = $plugin . '/includes/scwb-primary-shortcode.php';
require_marker($primary, "remove_shortcode('sc_workbench')", $failures);
require_marker($primary, "add_shortcode('sc_workbench'", $failures);
require_marker($primary, "add_action('wp_loaded'", $failures);
require_marker($primary, 'data-scwb-primary-tab', $failures);
require_marker($primary, 'data-scwb-primary-panel', $failures);
require_marker($primary, 'data-scwb-activation', $failures);

$reliability = $plugin . '/includes/scwb-v301-production-reliability.php';
$expected = array(
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
);
foreach ($expected as $shortcode) {
    require_marker($reliability, "'shortcode' => '{$shortcode}'", $failures);
}
require_marker($reliability, "add_shortcode('sc_workbench_diagnostics'", $failures);
require_marker($reliability, '/production-status', $failures);

$all_php = '';
foreach (glob($plugin . '/includes/*.php') as $path) {
    $all_php .= file_get_contents($path) . "\n";
}
foreach ($expected as $shortcode) {
    if (false === strpos($all_php, "'{$shortcode}'") && false === strpos($all_php, "\"{$shortcode}\"")) {
        $failures[] = "Studio shortcode not implemented: {$shortcode}";
    }
}

foreach (array(
    $plugin . '/assets/css/scwb-primary-repair.css',
    $plugin . '/assets/css/sc-workbench-v301.css',
    $plugin . '/assets/js/scwb-primary-repair.js',
    $plugin . '/assets/js/sc-workbench-v301.js',
) as $path) {
    if (!is_file($path) || 20 > filesize($path)) {
        $failures[] = 'Missing or empty reliability asset: ' . basename($path);
    }
}

$router = $plugin . '/assets/js/scwb-primary-repair.js';
foreach (array('MutationObserver', 'hashchange', 'ArrowRight', 'scwb:studio-activated', 'data-scwb-panel-state', 'expectedStudios') as $marker) {
    require_marker($router, $marker, $failures);
}

if ($failures) {
    fwrite(STDERR, "Workbench v3.0.1 activation audit failed:\n- " . implode("\n- ", $failures) . "\n");
    exit(1);
}

echo "Workbench v3.0.1 plugin activation audit passed for " . count($expected) . " studios.\n";
