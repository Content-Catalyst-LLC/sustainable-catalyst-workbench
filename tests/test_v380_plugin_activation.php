<?php
$root=dirname(__DIR__);
$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$failures=array();
function must_contain_v380($file,$needle,&$failures){
    $text=is_file($file)?file_get_contents($file):'';
    if(false===strpos($text,$needle))$failures[]='Missing marker '.$needle.' in '.$file;
}
must_contain_v380($plugin.'/sustainable-catalyst-workbench.php','Version: 3.8.0',$failures);
must_contain_v380($plugin.'/sustainable-catalyst-workbench.php',"define('SCWB_VERSION', '3.8.0')",$failures);
must_contain_v380($plugin.'/sustainable-catalyst-workbench.php','scwb-v380-offline-installable-workbench.php',$failures);
must_contain_v380($root.'/backend/app/main.py','version="3.8.0"',$failures);
must_contain_v380($root.'/backend/app/main.py','from app.v380 import router as v380_router',$failures);
must_contain_v380($plugin.'/includes/scwb-v301-production-reliability.php',"'offline' =>",$failures);
must_contain_v380($plugin.'/assets/js/scwb-primary-repair.js',"'offline'",$failures);
must_contain_v380($plugin.'/assets/js/scwb-primary-repair.js','[data-scwb-v380]',$failures);
foreach(array('sc-workbench-v380.css','sc-workbench-v380.js') as $file){
    $path=$plugin.'/assets/'.(str_ends_with($file,'.css')?'css/':'js/').$file;
    if(!is_file($path)||filesize($path)<1000)$failures[]='Missing or incomplete asset: '.$file;
}
foreach(array(
    'offline/start_local_workbench.py',
    'offline/web/index.html',
    'offline/web/service-worker.js',
    'installers/macos/install_workbench_macos.command',
    'installers/linux/install_workbench_linux.sh',
    'installers/raspberry-pi/install_workbench_raspberry_pi.sh'
) as $file){
    if(!is_file($root.'/'.$file))$failures[]='Missing offline package file: '.$file;
}
if($failures){
    fwrite(STDERR,"Workbench v3.8.0 activation audit failed:\n- ".implode("\n- ",$failures)."\n");
    exit(1);
}
echo "Workbench v3.8.0 activation audit passed.\n";
