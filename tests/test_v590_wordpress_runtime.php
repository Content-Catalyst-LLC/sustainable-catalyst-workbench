<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$php=file_get_contents($plugin.'/includes/scwb-v590-fpga-pynq-digital-logic.php');
$settings=file_get_contents($plugin.'/includes/scwb-v531-settings-backend-repair.php');
foreach(['data-scwb-v590','DIGITAL LOGIC / FPGA OUTPUT','data-scwb-v590-mode="logic"','data-scwb-v590-mode="kmap"','data-scwb-v590-mode="fsm"','data-scwb-v590-mode="timing"','data-scwb-v590-mode="hdl"','data-scwb-v590-mode="pynq"','Logic analysis, simulation, and export only.','FPGA, PYNQ &amp; Digital Logic'] as $m){if(strpos($php,$m)===false){fwrite(STDERR,"Missing v5.9.0 runtime marker: $m\n");exit(1);}}
foreach(["'/v590/status'",'FPGA + DIGITAL LOGIC','digitalLogic'] as $m){if(strpos($settings,$m)===false){fwrite(STDERR,"Missing v5.9.0 settings marker: $m\n");exit(1);}}
echo "Workbench v5.9.0 WordPress FPGA/digital-logic runtime passed.\n";
