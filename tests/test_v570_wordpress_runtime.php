<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$php=file_get_contents($plugin.'/includes/scwb-v570-signals-systems-control-mathematics.php');
$settings=file_get_contents($plugin.'/includes/scwb-v531-settings-backend-repair.php');
foreach(['data-scwb-v570','SIGNALS / SYSTEMS / CONTROL OUTPUT','data-scwb-v570-mode="spectrum"','data-scwb-v570-mode="root-locus"','data-scwb-v570-run="state-space"','data-scwb-v570-run="pid"','Governed signals and control computation','Signals &amp; Control'] as $m){if(strpos($php,$m)===false){fwrite(STDERR,"Missing v5.7.0 runtime marker: $m\n");exit(1);}}
foreach(["'/v570/status'",'SIGNALS + CONTROL','signalsControl'] as $m){if(strpos($settings,$m)===false){fwrite(STDERR,"Missing v5.7.0 settings marker: $m\n");exit(1);}}
echo "Workbench v5.7.0 WordPress signals/control runtime passed.\n";
