<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$php=file_get_contents($plugin.'/includes/scwb-v560-numerical-scientific-computing.php');
$settings=file_get_contents($plugin.'/includes/scwb-v531-settings-backend-repair.php');
foreach(['data-scwb-v560','SCIENTIFIC COMPUTING OUTPUT','data-scwb-v560-mode="root"','data-scwb-v560-mode="ode"','data-scwb-v560-run="linear"','data-scwb-v560-run="optimize"','Governed numerical computation','Numerical Computing'] as $m){if(strpos($php,$m)===false){fwrite(STDERR,"Missing v5.6.0 runtime marker: $m\n");exit(1);}}
foreach(["'/v560/status'",'NUMERICAL COMPUTING','numericalComputing'] as $m){if(strpos($settings,$m)===false){fwrite(STDERR,"Missing v5.6.0 settings marker: $m\n");exit(1);}}
echo "Workbench v5.6.0 WordPress numerical methods runtime passed.\n";
