<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$main=file_get_contents($plugin.'/sustainable-catalyst-workbench.php');
$primary=file_get_contents($plugin.'/includes/scwb-primary-shortcode.php');
$exp=file_get_contents($plugin.'/includes/scwb-v601-unified-experience-hardening.php');
$ok=strpos($main,'Version: 6.0.1')!==false
 && strpos($main,"define('SCWB_VERSION', '6.0.1')")!==false
 && strpos($main,'SCWB_V601_PLUGIN_FILE')!==false
 && strpos($primary,"const VERSION = '6.0.1'")!==false
 && strpos($primary,'data-scwb-version="6.0.1"')!==false
 && strpos($exp,"const VERSION = '6.0.1'")!==false
 && strpos($exp,'sc_workbench_v601_experience')!==false;
if(!$ok){fwrite(STDERR,"Workbench v6.0.1 activation audit failed.\n");exit(1);}echo "Workbench v6.0.1 activation audit passed.\n";
