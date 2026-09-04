<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$php=file_get_contents($plugin.'/includes/scwb-v532-compact-showcase-experience.php');
$graph=file_get_contents($plugin.'/includes/scwb-v520-graph-mathematics.php');
foreach(['data-scwb-v532-home','Open Workbench →','data-scwb-v532-experience','Sound &amp; Mathematics','Prototype Bench'] as $m){if(strpos($php,$m)===false){fwrite(STDERR,"Missing v5.3.2 runtime marker: $m\n");exit(1);}}
foreach(['ADVANCED GRAPH VIEW','Reset view','Fullscreen','data-scwb-v520-trace'] as $m){if(strpos($graph,$m)===false){fwrite(STDERR,"Missing graph runtime marker: $m\n");exit(1);}}
echo "Workbench v5.3.2 WordPress showcase/experience runtime passed.\n";
