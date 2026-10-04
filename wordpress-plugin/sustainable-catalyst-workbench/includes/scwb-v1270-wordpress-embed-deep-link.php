<?php
/**
 * Workbench v12.7.0 — WordPress Embed & Deep-Link Compatibility.
 * wordpressRequired = false.
 * WordPress does not own standalone authentication credentials, computation,
 * project state, notebooks, packages, or rendering.
 */
if (!defined('ABSPATH')) { exit; }

/**
 * Shortcode:
 * [sc_workbench_embed route="/calculator" height="760" app_url="https://workbench.sustainablecatalyst.com"]
 *
 * Optional non-sensitive launch context can be supplied with target_type and target_id.
 * Authentication credentials are never embedded by this shortcode.
 */
function sc_workbench_embed($atts=array()){
    $atts=shortcode_atts(array(
        'route'=>'/calculator',
        'height'=>'760',
        'app_url'=>'https://workbench.sustainablecatalyst.com',
        'target_type'=>'none',
        'target_id'=>'',
        'title'=>'Sustainable Catalyst Workbench'
    ),$atts,'sc_workbench_embed');

    $allowed_routes=array('/calculator','/workspace','/graphs','/history','/packages','/settings');
    $route=in_array($atts['route'],$allowed_routes,true)?$atts['route']:'/calculator';
    $app_url=rtrim(esc_url_raw($atts['app_url']),'/');
    $height=max(360,min(1600,intval($atts['height'])));

    // Static embed/deep-link compatibility. Sensitive state and credentials remain standalone.
    $params=array(
        'embed'=>'1',
        'source'=>'wordpress',
        'targetType'=>sanitize_key($atts['target_type']),
        'targetId'=>sanitize_text_field($atts['target_id'])
    );
    $src=add_query_arg($params,$app_url.$route);

    return sprintf(
        '<iframe class="sc-workbench-embed" src="%s" title="%s" loading="lazy" style="width:100%%;height:%dpx;border:0;" sandbox="allow-scripts allow-same-origin allow-forms allow-popups"></iframe>',
        esc_url($src),esc_attr($atts['title']),$height
    );
}
add_shortcode('sc_workbench_embed','sc_workbench_embed');

function scwb_v1270_backend_request($path,$method='GET',$body=null){
    if(function_exists('scwb_v1100_backend_request')) return scwb_v1100_backend_request($path,$method,$body);
    return array('ok'=>false,'error'=>'Workbench backend adapter unavailable','_httpStatus'=>503);
}

add_action('rest_api_init',function(){
    $permission=function(){return current_user_can('edit_posts');};

    register_rest_route('sc-workbench/v1/v1270','/status',array(
      'methods'=>'GET','permission_callback'=>$permission,
      'callback'=>function(){return new WP_REST_Response(scwb_v1270_backend_request('/v1270/status'),200);}));

    register_rest_route('sc-workbench/v1/v1270','/launch-config',array(
      'methods'=>'GET','permission_callback'=>$permission,
      'callback'=>function(){return new WP_REST_Response(scwb_v1270_backend_request('/standalone/v1/launch/config'),200);}));

    register_rest_route('sc-workbench/v1/v1270','/launch',array(
      'methods'=>'POST','permission_callback'=>$permission,
      'callback'=>function($request){
          return new WP_REST_Response(
              scwb_v1270_backend_request('/standalone/v1/launch','POST',$request->get_json_params()),
              200
          );
      }));
});
