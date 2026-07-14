<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';$failures=array();
function must_contain_v450($file,$needle,&$failures){$text=is_file($file)?file_get_contents($file):'';if(false===strpos($text,$needle))$failures[]='Missing marker '.$needle.' in '.$file;}
must_contain_v450($plugin.'/sustainable-catalyst-workbench.php','Version: 4.5.0',$failures);
must_contain_v450($plugin.'/sustainable-catalyst-workbench.php',"define('SCWB_VERSION', '4.5.0')",$failures);
must_contain_v450($plugin.'/sustainable-catalyst-workbench.php','scwb-v450-extension-framework.php',$failures);
must_contain_v450($root.'/backend/app/main.py','version="4.5.0"',$failures);
must_contain_v450($root.'/backend/app/main.py','from app.v450 import router as v450_router',$failures);
must_contain_v450($plugin.'/includes/scwb-primary-shortcode.php','data-scwb-version="4.5.0"',$failures);
must_contain_v450($plugin.'/assets/js/scwb-primary-repair.js',"version: '4.5.0'",$failures);
must_contain_v450($plugin.'/includes/scwb-v301-production-reliability.php',"'extensions' => array",$failures);
foreach(array('sc-workbench-v450.css','sc-workbench-v450.js') as $file){$path=$plugin.'/assets/'.(str_ends_with($file,'.css')?'css/':'js/').$file;if(!is_file($path)||filesize($path)<1000)$failures[]='Missing or incomplete asset: '.$file;}
if($failures){fwrite(STDERR,"Workbench v4.5.0 activation audit failed:\n- ".implode("\n- ",$failures)."\n");exit(1);}echo "Workbench v4.5.0 activation audit passed.\n";
