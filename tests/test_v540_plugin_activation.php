<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$main=file_get_contents($plugin.'/sustainable-catalyst-workbench.php');
$php=file_get_contents($plugin.'/includes/scwb-v540-advanced-graph-mathematics.php');
$ok=strpos($main,'Version: 5.4.0')!==false
    && strpos($main,"define('SCWB_VERSION', '5.4.0')")!==false
    && strpos($main,'SCWB_V540_PLUGIN_FILE')!==false
    && strpos($php,"const VERSION = '5.4.0'")!==false
    && strpos($php,'sc_workbench_advanced_graph_mathematics')!==false
    && strpos($php,'sc_workbench_graph_mathematics')!==false;
if(!$ok){fwrite(STDERR,"Workbench v5.4.0 activation audit failed.\n");exit(1);}echo "Workbench v5.4.0 activation audit passed.\n";
