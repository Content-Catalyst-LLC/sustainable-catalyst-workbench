<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';$failures=array();
function must_contain_v531($file,$needle,&$failures){$text=is_file($file)?file_get_contents($file):'';if(false===strpos($text,$needle))$failures[]='Missing marker '.$needle.' in '.$file;}
must_contain_v531($plugin.'/sustainable-catalyst-workbench.php','Version: 5.3.1',$failures);
must_contain_v531($plugin.'/sustainable-catalyst-workbench.php',"define('SCWB_VERSION', '5.3.1')",$failures);
must_contain_v531($plugin.'/sustainable-catalyst-workbench.php','scwb-v531-settings-backend-repair.php',$failures);
must_contain_v531($plugin.'/includes/scwb-primary-shortcode.php','data-scwb-version="5.3.1"',$failures);
must_contain_v531($plugin.'/includes/scwb-v531-settings-backend-repair.php','Workbench Settings',$failures);
must_contain_v531($plugin.'/includes/scwb-v531-settings-backend-repair.php','scwb_workbench_backend_url',$failures);
must_contain_v531($plugin.'/includes/scwb-v531-settings-backend-repair.php','wp_ajax_scwb_v531_test_backend',$failures);
must_contain_v531($plugin.'/includes/scwb-v531-settings-backend-repair.php','https://workbench-api.sustainablecatalyst.com',$failures);
must_contain_v531($plugin.'/includes/scwb-v530-blackboard-creative-prototyping.php','scwb-v531-home',$failures);
foreach(array('assets/css/sc-workbench-v531-admin.css','assets/js/sc-workbench-v531-admin.js') as $rel){$path=$plugin.'/'.$rel;if(!is_file($path)||filesize($path)<1000)$failures[]='Missing or incomplete asset: '.$rel;}
if($failures){fwrite(STDERR,"Workbench v5.3.1 activation audit failed:\n- ".implode("\n- ",$failures)."\n");exit(1);}echo "Workbench v5.3.1 activation audit passed.\n";
