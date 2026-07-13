<?php
/** Minimal WordPress harness for v3.1.0 content-type and REST registration. */
define('ABSPATH', __DIR__ . '/');
$GLOBALS['scwb_actions'] = array();
$GLOBALS['scwb_shortcodes'] = array();
$GLOBALS['scwb_post_types'] = array();
$GLOBALS['scwb_rest_routes'] = array();
function add_action($hook,$callback,$priority=10,$accepted_args=1){$GLOBALS['scwb_actions'][$hook][$priority][]=$callback;}
function add_filter(){return true;}
function add_shortcode($tag,$callback){$GLOBALS['scwb_shortcodes'][$tag]=$callback;}
function remove_shortcode($tag){unset($GLOBALS['scwb_shortcodes'][$tag]);}
function shortcode_exists($tag){return isset($GLOBALS['scwb_shortcodes'][$tag]);}
function wp_register_style(){return true;}
function wp_register_script(){return true;}
function plugins_url($path='',$plugin=''){return '/plugins/'.ltrim($path,'/');}
function register_post_type($type,$args){$GLOBALS['scwb_post_types'][$type]=$args;}
function register_rest_route($namespace,$route,$args){$GLOBALS['scwb_rest_routes'][$namespace.$route]=$args;}
function __($text,$domain=null){return $text;}
function run_hook($hook){if(empty($GLOBALS['scwb_actions'][$hook]))return;ksort($GLOBALS['scwb_actions'][$hook]);foreach($GLOBALS['scwb_actions'][$hook] as $callbacks){foreach($callbacks as $callback){call_user_func($callback);}}}
require dirname(__DIR__) . '/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php';
run_hook('init');
run_hook('wp_loaded');
run_hook('rest_api_init');
foreach (array('scwb_project','scwb_revision') as $type) {
    if (!isset($GLOBALS['scwb_post_types'][$type])) { fwrite(STDERR,"Missing post type: $type\n"); exit(1); }
    if (!empty($GLOBALS['scwb_post_types'][$type]['public'])) { fwrite(STDERR,"Post type must be private: $type\n"); exit(1); }
}
foreach (array('scwb/v1/persistent-status','scwb/v1/projects','scwb/v1/projects/(?P<id>\d+)','scwb/v1/projects/(?P<id>\d+)/revisions') as $route) {
    if (!isset($GLOBALS['scwb_rest_routes'][$route])) { fwrite(STDERR,"Missing REST route: $route\n"); exit(1); }
}
foreach (array('sc_workbench_persistent_workspace','sc_workbench_project_manager','sc_workbench_project_switcher','sc_workbench_project_revisions','sc_workbench_project_storage','sc_workbench_project_autosave') as $tag) {
    if (!shortcode_exists($tag)) { fwrite(STDERR,"Missing shortcode: $tag\n"); exit(1); }
}
echo "Workbench v3.1.0 WordPress persistence runtime passed.\n";
