<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$main=file_get_contents($plugin.'/sustainable-catalyst-workbench.php');
$php=file_get_contents($plugin.'/includes/scwb-v533-integration-hardening.php');
$ok=strpos($main,'Version: 5.3.3')!==false
    && strpos($main,"define('SCWB_VERSION', '5.3.3')")!==false
    && strpos($main,'SCWB_V533_PLUGIN_FILE')!==false
    && strpos($php,"const VERSION = '5.3.3'")!==false
    && strpos($php,'sc_workbench_homepage_instrument')!==false
    && strpos($php,'render_legacy_showcase_guard')!==false;
if(!$ok){fwrite(STDERR,"Workbench v5.3.3 activation audit failed.\n");exit(1);}echo "Workbench v5.3.3 activation audit passed.\n";
