<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';$failures=array();
function must_contain_v440($file,$needle,&$failures){$text=is_file($file)?file_get_contents($file):'';if(false===strpos($text,$needle))$failures[]='Missing marker '.$needle.' in '.$file;}
must_contain_v440($plugin.'/sustainable-catalyst-workbench.php','Version: 4.4.0',$failures);
must_contain_v440($plugin.'/sustainable-catalyst-workbench.php',"define('SCWB_VERSION', '4.4.0')",$failures);
must_contain_v440($plugin.'/sustainable-catalyst-workbench.php','scwb-v440-evaluation-laboratory.php',$failures);
must_contain_v440($root.'/backend/app/main.py','version="4.4.0"',$failures);
must_contain_v440($root.'/backend/app/main.py','from app.v440 import router as v440_router',$failures);
must_contain_v440($plugin.'/includes/scwb-primary-shortcode.php','data-scwb-version="4.4.0"',$failures);
must_contain_v440($plugin.'/assets/js/scwb-primary-repair.js',"version: '4.4.0'",$failures);
must_contain_v440($plugin.'/includes/scwb-v301-production-reliability.php',"'evaluation' => array",$failures);
foreach(array('sc-workbench-v440.css','sc-workbench-v440.js') as $file){$path=$plugin.'/assets/'.(str_ends_with($file,'.css')?'css/':'js/').$file;if(!is_file($path)||filesize($path)<1000)$failures[]='Missing or incomplete asset: '.$file;}
if($failures){fwrite(STDERR,"Workbench v4.4.0 activation audit failed:\n- ".implode("\n- ",$failures)."\n");exit(1);}echo "Workbench v4.4.0 activation audit passed.\n";
