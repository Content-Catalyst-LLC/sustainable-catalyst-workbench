<?php
define('ABSPATH',__DIR__.'/');
$GLOBALS['scwb_actions']=array();
$GLOBALS['scwb_shortcodes']=array();
$GLOBALS['scwb_post_types']=array();
$GLOBALS['scwb_rest_routes']=array();
function add_action($h,$c,$p=10,$a=1){$GLOBALS['scwb_actions'][$h][$p][]=$c;}
function add_filter(){return true;}
function apply_filters($h,$v){return$v;}
function add_shortcode($t,$c){$GLOBALS['scwb_shortcodes'][$t]=$c;}
function remove_shortcode($t){unset($GLOBALS['scwb_shortcodes'][$t]);}
function shortcode_exists($t){return isset($GLOBALS['scwb_shortcodes'][$t]);}
function wp_register_style(){return true;}
function wp_register_script(){return true;}
function plugins_url($p='',$f=''){return'/plugins/'.ltrim($p,'/');}
function plugin_dir_path($f){return dirname($f).'/';}
function register_post_type($t,$a){$GLOBALS['scwb_post_types'][$t]=$a;}
function register_rest_route($n,$r,$a){$GLOBALS['scwb_rest_routes'][$n.$r]=$a;}
function current_user_can(){return false;}
function is_user_logged_in(){return false;}
function __($t,$d=null){return$t;}
function selected(){return'';}
function run_hook($h){if(empty($GLOBALS['scwb_actions'][$h]))return;ksort($GLOBALS['scwb_actions'][$h]);foreach($GLOBALS['scwb_actions'][$h] as $cs)foreach($cs as $c)call_user_func($c);}
require dirname(__DIR__).'/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php';
run_hook('init');
run_hook('wp_loaded');
run_hook('rest_api_init');
foreach(array('scwb_offline_node','scwb_sync_bundle') as $type){
    if(!isset($GLOBALS['scwb_post_types'][$type])){fwrite(STDERR,"Missing post type: $type\n");exit(1);}
    if(!empty($GLOBALS['scwb_post_types'][$type]['public'])){fwrite(STDERR,"Post type must be private: $type\n");exit(1);}
}
foreach(array(
    'scwb/v1/offline-installable-status',
    'scwb/v1/offline-nodes',
    'scwb/v1/offline-sync-bundles',
    'scwb/v1/offline-install-plans',
    'scwb/v1/offline-service-records',
    'scwb/v1/offline-update-plans'
) as $route){
    if(!isset($GLOBALS['scwb_rest_routes'][$route])){fwrite(STDERR,"Missing route: $route\n");exit(1);}
}
foreach(array(
    'sc_workbench_offline_installable',
    'sc_workbench_offline_status',
    'sc_workbench_installer_builder',
    'sc_workbench_local_service',
    'sc_workbench_offline_storage',
    'sc_workbench_runner_manager',
    'sc_workbench_offline_sync',
    'sc_workbench_update_recovery'
) as $tag){
    if(!shortcode_exists($tag)){fwrite(STDERR,"Missing shortcode: $tag\n");exit(1);}
}
$catalog=SCWB_V301_Production_Reliability::studio_catalog();
if(!isset($catalog['offline'])||'sc_workbench_offline_installable'!==$catalog['offline']['shortcode']){
    fwrite(STDERR,"Offline studio missing.\n");exit(1);
}
if(count($catalog)<20){fwrite(STDERR,"Expected at least 20 studios, found ".count($catalog).".\n");exit(1);}
echo "Workbench v3.8.0 WordPress offline runtime passed.\n";
