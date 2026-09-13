<?php
/** Workbench v6.3.0 — Grid, Storage & Reliability Analysis status bridge. */
if (!defined('ABSPATH')) { exit; }
final class SCWB_V630_Grid_Storage_Reliability {
    const VERSION='6.3.0'; const ENERGY_SYSTEMS_VERSION='1.6.0';
    public static function boot(){ add_action('rest_api_init',array(__CLASS__,'register_routes')); add_shortcode('sc_workbench_grid_reliability_status',array(__CLASS__,'shortcode')); }
    public static function register_routes(){ register_rest_route('sc-workbench/v1','/grid-storage-reliability/status',array('methods'=>'GET','callback'=>array(__CLASS__,'status'),'permission_callback'=>'__return_true')); }
    private static function backend_url(){ if(class_exists('SCWB_V531_Settings_Backend_Repair')) return rtrim((string)SCWB_V531_Settings_Backend_Repair::backend_url(),'/'); if(defined('SCWB_WORKBENCH_BACKEND_URL')) return rtrim((string)SCWB_WORKBENCH_BACKEND_URL,'/'); return 'https://workbench-api.sustainablecatalyst.com'; }
    public static function status(){ $response=wp_remote_get(self::backend_url().'/v630/status',array('timeout'=>8,'redirection'=>2)); if(is_wp_error($response)) return new WP_REST_Response(array('ok'=>false,'version'=>self::VERSION,'detail'=>$response->get_error_message()),502); $code=(int)wp_remote_retrieve_response_code($response); $body=json_decode((string)wp_remote_retrieve_body($response),true); if($code<200||$code>=300||!is_array($body)) return new WP_REST_Response(array('ok'=>false,'version'=>self::VERSION,'httpStatus'=>$code),502); return new WP_REST_Response($body,200); }
    public static function shortcode(){ return '<div class="scwb-grid-reliability-status">Grid, Storage &amp; Reliability Analysis · Workbench v'.esc_html(self::VERSION).' · Energy Systems v'.esc_html(self::ENERGY_SYSTEMS_VERSION).'</div>'; }
}
SCWB_V630_Grid_Storage_Reliability::boot();
