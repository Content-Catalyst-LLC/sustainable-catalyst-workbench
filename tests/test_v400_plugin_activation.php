<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';$failures=array();
function must_contain_v400($file,$needle,&$failures){$text=is_file($file)?file_get_contents($file):'';if(false===strpos($text,$needle))$failures[]='Missing marker '.$needle.' in '.$file;}
must_contain_v400($plugin.'/sustainable-catalyst-workbench.php','Version: 4.0.0',$failures);
must_contain_v400($plugin.'/sustainable-catalyst-workbench.php',"define('SCWB_VERSION', '4.0.0')",$failures);
must_contain_v400($plugin.'/sustainable-catalyst-workbench.php','scwb-v400-connected-workbench.php',$failures);
must_contain_v400($root.'/backend/app/main.py','version="4.0.0"',$failures);
must_contain_v400($root.'/backend/app/main.py','from app.v400 import router as v400_router',$failures);
must_contain_v400($plugin.'/includes/scwb-v301-production-reliability.php',"'connected' =>",$failures);
must_contain_v400($plugin.'/assets/js/scwb-primary-repair.js',"'connected'",$failures);
must_contain_v400($plugin.'/assets/js/scwb-primary-repair.js','[data-scwb-v400]',$failures);
foreach(array('sc-workbench-v400.css','sc-workbench-v400.js') as $file){$path=$plugin.'/assets/'.(str_ends_with($file,'.css')?'css/':'js/').$file;if(!is_file($path)||filesize($path)<1000)$failures[]='Missing or incomplete asset: '.$file;}
if($failures){fwrite(STDERR,"Workbench v4.0.0 activation audit failed:\n- ".implode("\n- ",$failures)."\n");exit(1);}echo "Workbench v4.0.0 activation audit passed.\n";
