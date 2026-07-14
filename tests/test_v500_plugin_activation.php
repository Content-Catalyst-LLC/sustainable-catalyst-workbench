<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';$failures=array();
function must_contain_v500($file,$needle,&$failures){$text=is_file($file)?file_get_contents($file):'';if(false===strpos($text,$needle))$failures[]='Missing marker '.$needle.' in '.$file;}
must_contain_v500($plugin.'/sustainable-catalyst-workbench.php','Version: 5.0.0',$failures);
must_contain_v500($plugin.'/sustainable-catalyst-workbench.php',"define('SCWB_VERSION', '5.0.0')",$failures);
must_contain_v500($plugin.'/sustainable-catalyst-workbench.php','scwb-v500-integrated-platform.php',$failures);
must_contain_v500($root.'/backend/app/main.py','version="5.0.0"',$failures);
must_contain_v500($root.'/backend/app/main.py','from app.v500 import router as v500_router',$failures);
must_contain_v500($plugin.'/includes/scwb-primary-shortcode.php','data-scwb-version="5.0.0"',$failures);
must_contain_v500($plugin.'/assets/js/scwb-primary-repair.js',"version: '5.0.0'",$failures);
must_contain_v500($plugin.'/includes/scwb-v301-production-reliability.php',"'platform' => array",$failures);
foreach(array('sc-workbench-v500.css','sc-workbench-v500.js') as $file){$path=$plugin.'/assets/'.(str_ends_with($file,'.css')?'css/':'js/').$file;if(!is_file($path)||filesize($path)<1000)$failures[]='Missing or incomplete asset: '.$file;}
if($failures){fwrite(STDERR,"Workbench v5.0.0 activation audit failed:\n- ".implode("\n- ",$failures)."\n");exit(1);}echo "Workbench v5.0.0 activation audit passed.\n";
