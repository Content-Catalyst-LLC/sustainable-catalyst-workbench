<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$php=file_get_contents($plugin.'/includes/scwb-v540-advanced-graph-mathematics.php');
$settings=file_get_contents($plugin.'/includes/scwb-v531-settings-backend-repair.php');
foreach(['data-scwb-v540','EXPRESSION STACK','data-scwb-v540-series-stack','data-scwb-v540-analysis','data-scwb-v540-region-expression','data-scwb-v540-stage-action="table"','data-scwb-v540-canvas','Governed mathematics'] as $m){if(strpos($php,$m)===false){fwrite(STDERR,"Missing v5.4.0 runtime marker: $m\n");exit(1);}}
foreach(["'/v540/status'",'ADVANCED GRAPH','advancedGraph'] as $m){if(strpos($settings,$m)===false){fwrite(STDERR,"Missing v5.4.0 settings marker: $m\n");exit(1);}}
echo "Workbench v5.4.0 WordPress advanced graph runtime passed.\n";
