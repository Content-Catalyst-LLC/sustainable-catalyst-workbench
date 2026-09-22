<?php
/** Workbench v6.6.0 — Unified Research Project & Session Bridge. */
if (!defined('ABSPATH')) { exit; }
final class SCWB_V660_Unified_Research_Session_Bridge {
    const VERSION = '6.6.0';
    public static function boot() { add_action('rest_api_init', array(__CLASS__, 'register_routes')); add_shortcode('sc_workbench_core_session_status', array(__CLASS__, 'shortcode')); }
    public static function register_routes() { register_rest_route('sc-workbench/v1', '/core-session/status', array('methods'=>'GET','callback'=>array(__CLASS__,'status'),'permission_callback'=>'__return_true')); }
    private static function backend_url() {
        if (class_exists('SCWB_V531_Settings_Backend_Repair')) { $url=SCWB_V531_Settings_Backend_Repair::backend_url(); if ($url) { return rtrim((string)$url,'/'); } }
        if (defined('SCWB_WORKBENCH_BACKEND_URL')) { return rtrim((string)SCWB_WORKBENCH_BACKEND_URL,'/'); }
        return 'https://workbench-api.sustainablecatalyst.com';
    }
    public static function status() {
        $response=wp_remote_get(self::backend_url().'/v660/status',array('timeout'=>6));
        if (is_wp_error($response)) { return new WP_REST_Response(array('ok'=>false,'schema'=>'sc-workbench-wordpress-core-session-bridge/1.0','version'=>self::VERSION,'backend'=>'unavailable'),502); }
        $code=wp_remote_retrieve_response_code($response); $body=json_decode(wp_remote_retrieve_body($response),true);
        if ($code!==200 || !is_array($body)) { return new WP_REST_Response(array('ok'=>false,'schema'=>'sc-workbench-wordpress-core-session-bridge/1.0','version'=>self::VERSION,'backend'=>'invalid-response','httpStatus'=>$code),502); }
        return new WP_REST_Response(array('ok'=>!empty($body['ok']),'schema'=>'sc-workbench-wordpress-core-session-bridge/1.0','version'=>self::VERSION,'backend'=>'connected','runtimeContractRef'=>isset($body['runtimeContractRef'])?$body['runtimeContractRef']:'','coreUnifiedRuntimeContract'=>isset($body['coreUnifiedRuntimeContract'])?$body['coreUnifiedRuntimeContract']:'','twoPhaseSessionBinding'=>!empty($body['twoPhaseSessionBinding']),'runtime'=>$body),200);
    }
    public static function shortcode() { return '<div class="scwb-core-session-status" data-workbench-version="'.esc_attr(self::VERSION).'">Unified Research Session Bridge · Workbench v'.esc_html(self::VERSION).'</div>'; }
}
SCWB_V660_Unified_Research_Session_Bridge::boot();
