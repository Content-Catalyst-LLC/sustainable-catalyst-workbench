<?php
$repo = dirname(__DIR__);
$plugin = $repo . '/wordpress-plugin/sustainable-catalyst-workbench';
$failures = array();
function v310_marker($path, $marker, &$failures) {
    if (!is_file($path) || false === strpos(file_get_contents($path), $marker)) {
        $failures[] = basename($path) . ': ' . $marker;
    }
}
$bootstrap = $plugin . '/sustainable-catalyst-workbench.php';
v310_marker($bootstrap, 'Version: 3.2.0', $failures);
v310_marker($bootstrap, "define('SCWB_VERSION', '3.2.0')", $failures);
v310_marker($bootstrap, 'scwb-v310-persistent-project-workspace.php', $failures);
$module = $plugin . '/includes/scwb-v310-persistent-project-workspace.php';
foreach (array(
    'sc_workbench_persistent_workspace',
    'sc_workbench_project_manager',
    'sc_workbench_project_switcher',
    'sc_workbench_project_revisions',
    'sc_workbench_project_storage',
    'sc_workbench_project_autosave',
    "register_post_type(self::PROJECT_POST_TYPE",
    "register_post_type(self::REVISION_POST_TYPE",
    "register_rest_route('scwb/v1', '/projects'",
    "register_rest_route('scwb/v1', '/projects/(?P<id>\\d+)'",
    "register_rest_route('scwb/v1', '/projects/(?P<id>\\d+)/revisions'",
    '/persistent-status',
    'browser-local fallback',
) as $marker) v310_marker($module, $marker, $failures);
$catalog = $plugin . '/includes/scwb-v301-production-reliability.php';
v310_marker($catalog, "'projects' => array", $failures);
v310_marker($catalog, "'shortcode' => 'sc_workbench_persistent_workspace'", $failures);
$primary = $plugin . '/includes/scwb-primary-shortcode.php';
v310_marker($primary, 'data-scwb-version="3.2.0"', $failures);
foreach (array('sc-workbench-v310.css','sc-workbench-v310.js') as $file) {
    $path = $plugin . '/assets/' . (str_ends_with($file, '.css') ? 'css/' : 'js/') . $file;
    if (!is_file($path) || filesize($path) < 1000) $failures[] = 'Missing or incomplete asset: ' . $file;
}
if ($failures) {
    fwrite(STDERR, "Workbench v3.2.0 activation audit failed:\n- " . implode("\n- ", $failures) . "\n");
    exit(1);
}
echo "Workbench v3.2.0 activation audit passed.\n";
