<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$main=file_get_contents($plugin.'/sustainable-catalyst-workbench.php');
$php=file_get_contents($plugin.'/includes/scwb-v580-electronics-embedded-systems.php');
$primary=file_get_contents($plugin.'/includes/scwb-primary-shortcode.php');
$catalog=file_get_contents($plugin.'/includes/scwb-v301-production-reliability.php');
$ok=strpos($main,'Version: 5.8.0')!==false
    && strpos($main,"define('SCWB_VERSION', '5.8.0')")!==false
    && strpos($main,'SCWB_V580_PLUGIN_FILE')!==false
    && strpos($php,"const VERSION = '5.8.0'")!==false
    && strpos($php,'sc_workbench_electronics_embedded')!==false
    && strpos($primary,"const VERSION = '5.8.0'")!==false
    && strpos($primary,'data-scwb-version="5.8.0"')!==false
    && strpos($catalog,"'electronics' => array")!==false;
if(!$ok){fwrite(STDERR,"Workbench v5.8.0 activation audit failed.\n");exit(1);}echo "Workbench v5.8.0 activation audit passed.\n";
