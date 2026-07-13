<?php
$root = dirname(__DIR__);
$plugin = $root . '/wordpress-plugin/sustainable-catalyst-workbench';
$main = file_get_contents($plugin . '/sustainable-catalyst-workbench.php');
if (strpos($main, 'Version: 3.3.1') === false || strpos($main, "define('SCWB_VERSION', '3.3.1')") === false) {
    fwrite(STDERR, "FAIL: v3.3.1 version marker missing\n"); exit(1);
}
$checks = array(
    'includes/scwb-v230-robotics-controls.php' => "array('sc_workbench_hardware_studio')",
    'includes/scwb-v240-instrumentation.php' => "array('sc_workbench_hardware_studio', 'sc_workbench_robotics_studio')",
    'includes/scwb-v260-multilanguage-runtime.php' => "array('sc_workbench_simulation_studio', 'sc_workbench_code_studio')",
);
foreach ($checks as $relative => $expected) {
    $source = file_get_contents($plugin . '/' . $relative);
    if (strpos($source, $expected) === false) {
        fwrite(STDERR, "FAIL: repaired parent list missing in {$relative}\n"); exit(1);
    }
    if (preg_match('/\$parents?\s*=.*sc_workbench_embedded_device_studio/', $source) ||
        preg_match('/in_array\(\$tag,\s*array\([^\)]*sc_workbench_embedded_device_studio/', $source)) {
        fwrite(STDERR, "FAIL: legacy suite still appends to Embedded Devices in {$relative}\n"); exit(1);
    }
}
$required = array(
    'sc_workbench_robotics_studio', 'sc_workbench_instrumentation_studio',
    'sc_workbench_multilanguage_runtime'
);
$all = '';
foreach (glob($plugin . '/includes/*.php') as $file) { $all .= file_get_contents($file); }
foreach ($required as $tag) {
    if (strpos($all, $tag) === false) {
        fwrite(STDERR, "FAIL: specialist shortcode registration missing: {$tag}\n"); exit(1);
    }
}
echo "Workbench v3.3.1 embedded suite suppression passed.\n";
