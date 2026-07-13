<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';$failures=array();
function must_contain_v390($file,$needle,&$failures){$text=is_file($file)?file_get_contents($file):'';if(false===strpos($text,$needle))$failures[]='Missing marker '.$needle.' in '.$file;}
must_contain_v390($plugin.'/sustainable-catalyst-workbench.php','Version: 4.0.0',$failures);
must_contain_v390($plugin.'/sustainable-catalyst-workbench.php',"define('SCWB_VERSION', '4.0.0')",$failures);
must_contain_v390($plugin.'/sustainable-catalyst-workbench.php','scwb-v390-production-hardening.php',$failures);
must_contain_v390($root.'/backend/app/main.py','version="4.0.0"',$failures);
must_contain_v390($root.'/backend/app/main.py','from app.v390 import router as v390_router',$failures);
must_contain_v390($plugin.'/includes/scwb-v301-production-reliability.php',"'hardening' =>",$failures);
must_contain_v390($plugin.'/assets/js/scwb-primary-repair.js',"'hardening'",$failures);
must_contain_v390($plugin.'/assets/js/scwb-primary-repair.js','[data-scwb-v390]',$failures);
foreach(array('sc-workbench-v390.css','sc-workbench-v390.js') as $file){$path=$plugin.'/assets/'.(str_ends_with($file,'.css')?'css/':'js/').$file;if(!is_file($path)||filesize($path)<1000)$failures[]='Missing or incomplete asset: '.$file;}
if($failures){fwrite(STDERR,"Workbench v3.9.0 compatibility activation audit failed:\n- ".implode("\n- ",$failures)."\n");exit(1);}echo "Workbench v3.9.0 compatibility activation audit passed.\n";
