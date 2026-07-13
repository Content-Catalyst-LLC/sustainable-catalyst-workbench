<?php
$repo = dirname(__DIR__);
$plugin = $repo . '/wordpress-plugin/sustainable-catalyst-workbench';
$failures = array();
function marker($path, $value, &$failures) {
    if (!is_file($path) || false === strpos(file_get_contents($path), $value)) $failures[] = basename($path) . ': ' . $value;
}
marker($plugin . '/sustainable-catalyst-workbench.php', 'Version: 3.2.0', $failures);
marker($plugin . '/sustainable-catalyst-workbench.php', "define('SCWB_VERSION', '3.2.0')", $failures);
marker($plugin . '/sustainable-catalyst-workbench.php', 'scwb-v302-project-migration-recovery.php', $failures);
$module = $plugin . '/includes/scwb-v302-project-migration-recovery.php';
foreach (array('sc_workbench_migration_recovery','sc_workbench_migration_center','sc_workbench_storage_health_v302','sc_workbench_backup_restore','sc_workbench_restore_center','sc_workbench_orphan_cleanup','sc_workbench_rollback_center','/recovery-status') as $value) marker($module, $value, $failures);
$catalog = $plugin . '/includes/scwb-v301-production-reliability.php';
marker($catalog, "'recovery' => array", $failures);
marker($catalog, "'shortcode' => 'sc_workbench_migration_recovery'", $failures);
foreach (array('sc-workbench-v302.css','sc-workbench-v302.js') as $file) if (!is_file($plugin . '/assets/' . (str_ends_with($file, '.css') ? 'css/' : 'js/') . $file)) $failures[] = 'Missing asset: ' . $file;
if ($failures) { fwrite(STDERR, "Workbench v3.2.0 activation audit failed:\n- " . implode("\n- ", $failures) . "\n"); exit(1); }
echo "Workbench v3.2.0 activation audit passed.\n";
