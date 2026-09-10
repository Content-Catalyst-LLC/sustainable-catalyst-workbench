<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$php=file_get_contents($plugin.'/includes/scwb-v580-electronics-embedded-systems.php');
$settings=file_get_contents($plugin.'/includes/scwb-v531-settings-backend-repair.php');
foreach(['data-scwb-v580','ELECTRONICS / EMBEDDED OUTPUT','data-scwb-v580-mode="circuit"','data-scwb-v580-mode="adc"','data-scwb-v580-mode="prototype"','data-scwb-v580-run="gpio"','Governed electronics and embedded planning','Electronics &amp; Embedded'] as $m){if(strpos($php,$m)===false){fwrite(STDERR,"Missing v5.8.0 runtime marker: $m\n");exit(1);}}
foreach(["'/v580/status'",'ELECTRONICS + EMBEDDED','electronicsEmbedded'] as $m){if(strpos($settings,$m)===false){fwrite(STDERR,"Missing v5.8.0 settings marker: $m\n");exit(1);}}
echo "Workbench v5.8.0 WordPress electronics/embedded runtime passed.\n";
