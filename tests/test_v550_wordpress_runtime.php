<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$php=file_get_contents($plugin.'/includes/scwb-v550-dynamic-geometry.php');
$settings=file_get_contents($plugin.'/includes/scwb-v531-settings-backend-repair.php');
foreach(['data-scwb-v550','DYNAMIC PLANE','data-scwb-v550-tool="move"','data-scwb-v550-tool="polygon"','data-scwb-v550-add-constraint','data-scwb-v550-transform="rotate30"','data-scwb-v550-locus-generate','ALGEBRA ↔ GEOMETRY','MEASUREMENTS','CONSTRUCTION HISTORY','Governed interactive mathematics'] as $m){if(strpos($php,$m)===false){fwrite(STDERR,"Missing v5.5.0 runtime marker: $m\n");exit(1);}}
foreach(["'/v550/status'",'DYNAMIC GEOMETRY','dynamicGeometry'] as $m){if(strpos($settings,$m)===false){fwrite(STDERR,"Missing v5.5.0 settings marker: $m\n");exit(1);}}
echo "Workbench v5.5.0 WordPress dynamic geometry runtime passed.\n";
