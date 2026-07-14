<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';$failures=array();
function must_contain_v402($file,$needle,&$failures){$text=is_file($file)?file_get_contents($file):'';if(false===strpos($text,$needle))$failures[]='Missing marker '.$needle.' in '.$file;}
must_contain_v402($plugin.'/sustainable-catalyst-workbench.php','Version: 4.0.2',$failures);
must_contain_v402($plugin.'/sustainable-catalyst-workbench.php',"define('SCWB_VERSION', '4.0.2')",$failures);
must_contain_v402($plugin.'/sustainable-catalyst-workbench.php','scwb-v402-graph-sync-recovery.php',$failures);
must_contain_v402($root.'/backend/app/main.py','version="4.0.2"',$failures);
must_contain_v402($root.'/backend/app/main.py','from app.v402 import router as v402_router',$failures);
must_contain_v402($plugin.'/includes/scwb-primary-shortcode.php','data-scwb-version="4.0.2"',$failures);
must_contain_v402($plugin.'/assets/js/scwb-primary-repair.js',"version: '4.0.2'",$failures);
foreach(array('sc-workbench-v402.css','sc-workbench-v402.js') as $file){$path=$plugin.'/assets/'.(str_ends_with($file,'.css')?'css/':'js/').$file;if(!is_file($path)||filesize($path)<1000)$failures[]='Missing or incomplete asset: '.$file;}
if($failures){fwrite(STDERR,"Workbench v4.0.2 activation audit failed:\n- ".implode("\n- ",$failures)."\n");exit(1);}echo "Workbench v4.0.2 activation audit passed.\n";
