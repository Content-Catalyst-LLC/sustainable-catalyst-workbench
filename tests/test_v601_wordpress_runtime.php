<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$primary=file_get_contents($plugin.'/includes/scwb-primary-shortcode.php');
$exp=file_get_contents($plugin.'/includes/scwb-v601-unified-experience-hardening.php');
$graph=file_get_contents($plugin.'/assets/js/sc-workbench-v540.js');
foreach(['data-scwb-studio-search','data-scwb-studio-filter','data-scwb-favorite','data-scwb-active-label','data-scwb-version="6.0.1"'] as $m){if(strpos($primary,$m)===false){fwrite(STDERR,"Missing v6.0.1 primary runtime marker: $m\n");exit(1);}}
foreach(['data-scwb-v601-experience','Full Workbench','Unified computational project','Advanced graph mathematics','sc_workbench_homepage_instrument'] as $m){$has=strpos($exp,$m)!==false;if($m==='sc_workbench_homepage_instrument'){$has=!$has;}if(!$has){fwrite(STDERR,"v6.0.1 experience contract failed at: $m\n");exit(1);}}
foreach(['ResizeObserver','scwb:visual-resize','redrawStable'] as $m){if(strpos($graph,$m)===false){fwrite(STDERR,"Missing v6.0.1 graph hardening marker: $m\n");exit(1);}}
echo "Workbench v6.0.1 WordPress unified experience runtime passed.\n";
