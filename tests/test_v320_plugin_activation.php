<?php
$repo = dirname(__DIR__); $plugin = $repo . '/wordpress-plugin/sustainable-catalyst-workbench'; $failures = array();
function v320_marker($path,$marker,&$failures){if(!is_file($path)||false===strpos(file_get_contents($path),$marker))$failures[]=basename($path).': '.$marker;}
$bootstrap=$plugin.'/sustainable-catalyst-workbench.php';
v320_marker($bootstrap,'Version: 3.2.0',$failures); v320_marker($bootstrap,"define('SCWB_VERSION', '3.2.0')",$failures); v320_marker($bootstrap,'scwb-v320-knowledge-library-integration.php',$failures);
$module=$plugin.'/includes/scwb-v320-knowledge-library-integration.php';
foreach(array('sc_workbench_library_integration','sc_workbench_article_linker','sc_workbench_formula_registry','sc_workbench_calculator_embed','sc_workbench_librarian_handoff','sc_workbench_article_draft_return','register_post_type(self::LINK_POST_TYPE','register_post_type(self::DRAFT_POST_TYPE','/library-integration-status','/library-links','/article-drafts','/library-article/','human review') as $marker)v320_marker($module,$marker,$failures);
v320_marker($plugin.'/includes/scwb-v301-production-reliability.php',"'library' => array",$failures); v320_marker($plugin.'/includes/scwb-primary-shortcode.php','data-scwb-version="3.2.0"',$failures);
foreach(array('sc-workbench-v320.css','sc-workbench-v320.js') as $file){$path=$plugin.'/assets/'.(str_ends_with($file,'.css')?'css/':'js/').$file;if(!is_file($path)||filesize($path)<1000)$failures[]='Missing or incomplete asset: '.$file;}
if($failures){fwrite(STDERR,"Workbench v3.2.0 activation audit failed:\n- ".implode("\n- ",$failures)."\n");exit(1);} echo "Workbench v3.2.0 activation audit passed.\n";
