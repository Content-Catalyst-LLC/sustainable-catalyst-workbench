<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';$failures=array();
function must_contain_v401($file,$needle,&$failures){$text=is_file($file)?file_get_contents($file):'';if(false===strpos($text,$needle))$failures[]='Missing marker '.$needle.' in '.$file;}
must_contain_v401($plugin.'/sustainable-catalyst-workbench.php','Version: 4.0.1',$failures);
must_contain_v401($plugin.'/sustainable-catalyst-workbench.php',"define('SCWB_VERSION', '4.0.1')",$failures);
must_contain_v401($plugin.'/sustainable-catalyst-workbench.php','scwb-v401-connected-reliability.php',$failures);
must_contain_v401($root.'/backend/app/main.py','version="4.0.1"',$failures);
must_contain_v401($root.'/backend/app/main.py','from app.v401 import router as v401_router',$failures);
must_contain_v401($plugin.'/includes/scwb-primary-shortcode.php','data-scwb-version="4.0.1"',$failures);
must_contain_v401($plugin.'/assets/js/scwb-primary-repair.js',"version: '4.0.1'",$failures);
foreach(array('sc-workbench-v401.css','sc-workbench-v401.js') as $file){$path=$plugin.'/assets/'.(str_ends_with($file,'.css')?'css/':'js/').$file;if(!is_file($path)||filesize($path)<1000)$failures[]='Missing or incomplete asset: '.$file;}
if($failures){fwrite(STDERR,"Workbench v4.0.1 activation audit failed:\n- ".implode("\n- ",$failures)."\n");exit(1);}echo "Workbench v4.0.1 activation audit passed.\n";
