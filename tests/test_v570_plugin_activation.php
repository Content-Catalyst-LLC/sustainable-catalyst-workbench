<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$main=file_get_contents($plugin.'/sustainable-catalyst-workbench.php');
$php=file_get_contents($plugin.'/includes/scwb-v570-signals-systems-control-mathematics.php');
$primary=file_get_contents($plugin.'/includes/scwb-primary-shortcode.php');
$ok=strpos($main,'Version: 5.7.0')!==false
    && strpos($main,"define('SCWB_VERSION', '5.7.0')")!==false
    && strpos($main,'SCWB_V570_PLUGIN_FILE')!==false
    && strpos($php,"const VERSION = '5.7.0'")!==false
    && strpos($php,'sc_workbench_signals_systems_controls')!==false
    && strpos($primary,"const VERSION = '5.7.0'")!==false
    && strpos($primary,'data-scwb-version="5.7.0"')!==false;
if(!$ok){fwrite(STDERR,"Workbench v5.7.0 activation audit failed.\n");exit(1);}echo "Workbench v5.7.0 activation audit passed.\n";
