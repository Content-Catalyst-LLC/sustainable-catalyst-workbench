<?php
/** Workbench v6.7.0 — Computation, Analysis & Execution Lineage Bridge. */
if (!defined('ABSPATH')) { exit; }
final class SCWB_V670_Computation_Execution_Lineage {
    const VERSION = '6.7.0';
    public static function boot() { add_action('rest_api_init', array(__CLASS__, 'register_routes')); add_shortcode('sc_workbench_core_execution_lineage_status', array(__CLASS__, 'shortcode')); }
    public static function register_routes() { register_rest_route('sc-workbench/v1', '/core-execution-lineage/status', array('methods'=>'GET','callback'=>array(__CLASS__,'status'),'permission_callback'=>'__return_true')); }
    private static function backend_url() {
        if (class_exists('SCWB_V531_Settings_Backend_Repair')) { $url=SCWB_V531_Settings_Backend_Repair::backend_url(); if ($url) { return rtrim((string)$url,'/'); } }
        if (defined('SCWB_WORKBENCH_BACKEND_URL')) { return rtrim((string)SCWB_WORKBENCH_BACKEND_URL,'/'); }
        return 'https://workbench-api.sustainablecatalyst.com';
    }
    public static function status() {
        $response=wp_remote_get(self::backend_url().'/v670/status',array('timeout'=>6));
        if (is_wp_error($response)) { return new WP_REST_Response(array('ok'=>false,'schema'=>'sc-workbench-wordpress-core-execution-lineage/1.0','version'=>self::VERSION,'backend'=>'unavailable'),502); }
        $code=wp_remote_retrieve_response_code($response); $body=json_decode(wp_remote_retrieve_body($response),true);
        if ($code!==200 || !is_array($body)) { return new WP_REST_Response(array('ok'=>false,'schema'=>'sc-workbench-wordpress-core-execution-lineage/1.0','version'=>self::VERSION,'backend'=>'invalid-response','httpStatus'=>$code),502); }
        return new WP_REST_Response(array('ok'=>!empty($body['ok']),'schema'=>'sc-workbench-wordpress-core-execution-lineage/1.0','version'=>self::VERSION,'backend'=>'connected','coreComputationLineageContract'=>isset($body['coreComputationLineageContract'])?$body['coreComputationLineageContract']:'','twoPhaseExecutionLineage'=>!empty($body['twoPhaseExecutionLineage']),'unifiedSessionExecutionBinding'=>!empty($body['unifiedSessionExecutionBinding']),'runtime'=>$body),200);
    }
    public static function shortcode() { return '<div class="scwb-core-execution-lineage-status" data-workbench-version="'.esc_attr(self::VERSION).'">Computation &amp; Execution Lineage Bridge · Workbench v'.esc_html(self::VERSION).'</div>'; }
}
SCWB_V670_Computation_Execution_Lineage::boot();
