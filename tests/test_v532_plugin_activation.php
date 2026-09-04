<?php
$root=dirname(__DIR__);
$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$main=file_get_contents($plugin.'/sustainable-catalyst-workbench.php');
$php=file_get_contents($plugin.'/includes/scwb-v532-compact-showcase-experience.php');
$ok=strpos($main,'Version: 5.3.2')!==false&&strpos($main,'SCWB_V532_PLUGIN_FILE')!==false&&strpos($php,"const VERSION = '5.3.2'")!==false&&strpos($php,'sc_workbench_experience')!==false;
if(!$ok){fwrite(STDERR,"Workbench v5.3.2 activation audit failed.\n");exit(1);}echo "Workbench v5.3.2 activation audit passed.\n";
