<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$main=file_get_contents($plugin.'/sustainable-catalyst-workbench.php');
$php=file_get_contents($plugin.'/includes/scwb-v550-dynamic-geometry.php');
$primary=file_get_contents($plugin.'/includes/scwb-primary-shortcode.php');
$catalog=file_get_contents($plugin.'/includes/scwb-v301-production-reliability.php');
$ok=strpos($main,'Version: 5.5.0')!==false
    && strpos($main,"define('SCWB_VERSION', '5.5.0')")!==false
    && strpos($main,'SCWB_V550_PLUGIN_FILE')!==false
    && strpos($php,"const VERSION = '5.5.0'")!==false
    && strpos($php,'sc_workbench_dynamic_geometry')!==false
    && strpos($primary,"const VERSION = '5.5.0'")!==false
    && strpos($catalog,"'geometry' => array")!==false;
if(!$ok){fwrite(STDERR,"Workbench v5.5.0 activation audit failed.\n");exit(1);}echo "Workbench v5.5.0 activation audit passed.\n";
