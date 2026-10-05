<?php
/**
 * Workbench v13.0.0 — Functional Standalone Workbench Interface.
 * WordPress remains an optional public-site compatibility surface.
 */
if (!defined('ABSPATH')) { exit; }

function scwb_v1300_launch_url($route='/calculator'){
    $base='https://workbench.sustainablecatalyst.com';
    $allowed=array('/calculator','/workspace','/graphs','/history','/packages','/settings');
    if(!in_array($route,$allowed,true)){$route='/calculator';}
    return $base.$route;
}

function scwb_v1300_launch_shortcode($atts=array()){
    $atts=shortcode_atts(array('route'=>'/calculator','label'=>'Open Workbench'),$atts,'sc_workbench_launch');
    return sprintf(
        '<a class="sc-workbench-launch" href="%s">%s</a>',
        esc_url(scwb_v1300_launch_url($atts['route'])),
        esc_html($atts['label'])
    );
}
add_shortcode('sc_workbench_launch','scwb_v1300_launch_shortcode');
