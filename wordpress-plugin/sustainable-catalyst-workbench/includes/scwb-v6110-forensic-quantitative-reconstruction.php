<?php
if (!defined('ABSPATH')) { exit; }
function scwb_v6110_forensic_quantitative_status() {
    $base = rtrim((string) get_option('scwb_backend_url', 'https://workbench-api.sustainablecatalyst.com'), '/');
    $response = wp_remote_get($base . '/v6110/status', array('timeout' => 8));
    if (is_wp_error($response)) { return array('ok'=>false,'version'=>SCWB_VERSION,'error'=>$response->get_error_message()); }
    $body = json_decode(wp_remote_retrieve_body($response), true);
    return is_array($body) ? $body : array('ok'=>false,'version'=>SCWB_VERSION,'error'=>'invalid-json');
}
function scwb_v6110_forensic_quantitative_shortcode() {
    $status=scwb_v6110_forensic_quantitative_status(); $ok=!empty($status['ok']);
    $label=$ok?'Forensic Quantitative Reconstruction Runtime Online':'Forensic Quantitative Reconstruction Runtime Unavailable';
    $version=isset($status['version'])?esc_html($status['version']):esc_html(SCWB_VERSION);
    return '<div class="scwb-runtime-status scwb-v6110"><strong>'.esc_html($label).'</strong><br><span>Workbench '.$version.'</span></div>';
}
add_shortcode('sc_workbench_forensic_quantitative_status','scwb_v6110_forensic_quantitative_shortcode');
