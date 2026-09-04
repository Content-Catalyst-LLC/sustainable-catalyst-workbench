<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';$failures=array();
function must_contain_v530($file,$needle,&$failures){$text=is_file($file)?file_get_contents($file):'';if(false===strpos($text,$needle))$failures[]='Missing marker '.$needle.' in '.$file;}
must_contain_v530($plugin.'/sustainable-catalyst-workbench.php','Version: 5.3.0',$failures);
must_contain_v530($plugin.'/sustainable-catalyst-workbench.php',"define('SCWB_VERSION', '5.3.0')",$failures);
must_contain_v530($plugin.'/sustainable-catalyst-workbench.php','scwb-v530-blackboard-creative-prototyping.php',$failures);
must_contain_v530($root.'/backend/app/main.py','version="5.3.0"',$failures);
must_contain_v530($root.'/backend/app/main.py','from app.v530 import router as v530_router',$failures);
must_contain_v530($plugin.'/includes/scwb-primary-shortcode.php','data-scwb-version="5.3.0"',$failures);
must_contain_v530($plugin.'/assets/js/scwb-primary-repair.js',"version: '5.3.0'",$failures);
must_contain_v530($plugin.'/includes/scwb-v301-production-reliability.php',"'blackboard' => array",$failures);
must_contain_v530($plugin.'/includes/scwb-v301-production-reliability.php',"'prototype-bench' => array",$failures);
must_contain_v530($plugin.'/includes/scwb-v520-graph-mathematics.php','ADVANCED PROCESSES',$failures);
foreach(array('sc-workbench-v530.css','sc-workbench-v530.js') as $file){$path=$plugin.'/assets/'.(str_ends_with($file,'.css')?'css/':'js/').$file;if(!is_file($path)||filesize($path)<5000)$failures[]='Missing or incomplete asset: '.$file;}
if($failures){fwrite(STDERR,"Workbench v5.3.0 activation audit failed:\n- ".implode("\n- ",$failures)."\n");exit(1);}echo "Workbench v5.3.0 activation audit passed.\n";
