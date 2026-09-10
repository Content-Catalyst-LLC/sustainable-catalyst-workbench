<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$php=file_get_contents($plugin.'/includes/scwb-v600-unified-computational-workbench.php');
$settings=file_get_contents($plugin.'/includes/scwb-v531-settings-backend-repair.php');
foreach(['data-scwb-v600','PROJECT GRAPH / TECHNICAL RECORD','data-scwb-v600-action="build"','data-scwb-v600-action="variables"','data-scwb-v600-action="links"','data-scwb-v600-action="export"','data-scwb-v600-action="handoff"','Unified project orchestration, not autonomous execution.','Unified Computational Project'] as $m){if(strpos($php,$m)===false){fwrite(STDERR,"Missing v6.0.1 runtime marker: $m\n");exit(1);}}
foreach(["'/v601/status'",'UNIFIED EXPERIENCE','unifiedComputational'] as $m){if(strpos($settings,$m)===false){fwrite(STDERR,"Missing v6.0.1 settings marker: $m\n");exit(1);}}
echo "Workbench v6.0.1 WordPress unified computational runtime passed.\n";
