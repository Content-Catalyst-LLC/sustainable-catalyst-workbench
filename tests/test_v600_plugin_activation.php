<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$main=file_get_contents($plugin.'/sustainable-catalyst-workbench.php');
$php=file_get_contents($plugin.'/includes/scwb-v600-unified-computational-workbench.php');
$primary=file_get_contents($plugin.'/includes/scwb-primary-shortcode.php');
$catalog=file_get_contents($plugin.'/includes/scwb-v301-production-reliability.php');
$ok=strpos($main,'Version: 6.0.1')!==false
    && strpos($main,"define('SCWB_VERSION', '6.0.1')")!==false
    && strpos($main,'SCWB_V600_PLUGIN_FILE')!==false
    && strpos($php,"const VERSION = '6.0.1'")!==false
    && strpos($php,'sc_workbench_computational_project')!==false
    && strpos($primary,"const VERSION = '6.0.1'")!==false
    && strpos($primary,'data-scwb-version="6.0.1"')!==false
    && strpos($catalog,"'computational-project' => array")!==false;
if(!$ok){fwrite(STDERR,"Workbench v6.0.1 activation audit failed.\n");exit(1);}echo "Workbench v6.0.1 activation audit passed.\n";
