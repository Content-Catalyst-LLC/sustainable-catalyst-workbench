<?php
/**
 * Workbench v3.3.0 — Platform Handoffs and Shared Evidence.
 */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V330_Platform_Handoffs {
    const VERSION = '3.3.0';
    const EVIDENCE_POST_TYPE = 'scwb_evidence';
    const HANDOFF_POST_TYPE = 'scwb_handoff';
    const RECORD_META = '_scwb_v330_record';
    const HASH_META = '_scwb_v330_hash';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 6);
        add_action('init', array(__CLASS__, 'register_post_types'), 7);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 1004);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V330_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v330.css';
        $js = $base . '/assets/js/sc-workbench-v330.js';
        wp_register_style('scwb-v330', plugins_url('assets/css/sc-workbench-v330.css', SCWB_V330_PLUGIN_FILE), array('scwb-primary-repair'), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v330', plugins_url('assets/js/sc-workbench-v330.js', SCWB_V330_PLUGIN_FILE), array('scwb-primary-repair'), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_post_types() {
        register_post_type(self::EVIDENCE_POST_TYPE, array(
            'labels' => array('name' => __('Workbench Shared Evidence', 'sustainable-catalyst-workbench')),
            'public' => false, 'show_ui' => true, 'show_in_menu' => false, 'show_in_rest' => false,
            'supports' => array('title', 'author'), 'capability_type' => 'post', 'map_meta_cap' => true,
        ));
        register_post_type(self::HANDOFF_POST_TYPE, array(
            'labels' => array('name' => __('Workbench Platform Handoffs', 'sustainable-catalyst-workbench')),
            'public' => false, 'show_ui' => true, 'show_in_menu' => true, 'show_in_rest' => false,
            'supports' => array('title', 'author', 'excerpt'), 'capability_type' => 'post', 'map_meta_cap' => true,
        ));
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_platform_handoffs' => 'workspace',
            'sc_workbench_shared_evidence' => 'evidence',
            'sc_workbench_site_intelligence_handoff' => 'site',
            'sc_workbench_decision_studio_handoff' => 'decision',
            'sc_workbench_librarian_platform_handoff' => 'librarian',
            'sc_workbench_handoff_validation' => 'validation',
            'sc_workbench_portable_handoff_bundle' => 'bundles',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, static function($atts = array()) use ($panel) {
                    return SCWB_V330_Platform_Handoffs::render($panel, $atts);
                });
            }
        }
    }

    private static function can_write() {
        return function_exists('is_user_logged_in') && is_user_logged_in() && function_exists('current_user_can') && current_user_can('edit_posts');
    }

    private static function enqueue_assets() {
        self::register_assets();
        wp_enqueue_style('scwb-v330');
        wp_enqueue_script('scwb-v330');
        if (function_exists('wp_localize_script')) {
            wp_localize_script('scwb-v330', 'SCWBV330Config', array(
                'version' => self::VERSION,
                'restUrl' => function_exists('rest_url') ? esc_url_raw(rest_url('scwb/v1')) : '/wp-json/scwb/v1',
                'nonce' => function_exists('wp_create_nonce') ? wp_create_nonce('wp_rest') : '',
                'authenticated' => self::can_write(),
                'siteIntelligenceUrl' => apply_filters('scwb_v330_site_intelligence_url', '/lab/site-intelligence/'),
                'decisionStudioUrl' => apply_filters('scwb_v330_decision_studio_url', '/lab/decision-studio/'),
                'researchLibrarianUrl' => apply_filters('scwb_v330_research_librarian_url', '/platform/research-librarian/'),
            ));
        }
    }

    private static function field($label, $name, $type = 'text', $value = '', $wide = false) { ?>
        <label class="scwb-v330__field<?php echo $wide ? ' scwb-v330__field--wide' : ''; ?>">
            <span><?php echo esc_html($label); ?></span>
            <?php if ('textarea' === $type) : ?>
                <textarea data-scwb-v330-field="<?php echo esc_attr($name); ?>"><?php echo esc_textarea($value); ?></textarea>
            <?php else : ?>
                <input type="<?php echo esc_attr($type); ?>" data-scwb-v330-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>">
            <?php endif; ?>
        </label>
    <?php }

    private static function select_field($label, $name, $options, $selected = '') { ?>
        <label class="scwb-v330__field"><span><?php echo esc_html($label); ?></span><select data-scwb-v330-field="<?php echo esc_attr($name); ?>">
            <?php foreach ($options as $value => $caption) : ?><option value="<?php echo esc_attr($value); ?>" <?php selected($selected, $value); ?>><?php echo esc_html($caption); ?></option><?php endforeach; ?>
        </select></label>
    <?php }

    public static function render($panel = 'workspace', $atts = array()) {
        self::enqueue_assets();
        $atts = shortcode_atts(array('project' => 'default', 'title' => 'Platform Handoffs and Shared Evidence', 'display' => 'full'), $atts, 'sc_workbench_platform_handoffs');
        $display = sanitize_key($atts['display']);
        if (!in_array($display, array('inline','compact','full','drawer'), true)) { $display = 'full'; }
        $allowed = array('workspace','evidence','site','decision','librarian','validation','bundles');
        if (!in_array($panel, $allowed, true)) { $panel = 'workspace'; }
        $project = sanitize_key($atts['project']) ?: 'default';
        $instance = 'scwb-v330-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v330 scwb-v330--<?php echo esc_attr($display); ?>" data-scwb-v330 data-scwb-v330-panel="<?php echo esc_attr($panel); ?>" data-scwb-v330-project="<?php echo esc_attr($project); ?>" data-scwb-v330-version="3.3.0">
            <header class="scwb-v330__header">
                <div><p class="scwb-v330__eyebrow">Sustainable Catalyst Workbench · v3.3.0</p><h2><?php echo esc_html($atts['title']); ?></h2><p>Move evidence, datasets, calculations, scenarios, research routes, and project links between Sustainable Catalyst applications without losing provenance or review boundaries.</p></div>
                <span class="scwb-v330__status" data-scwb-v330-status aria-live="polite"><?php echo self::can_write() ? 'Private WordPress records available' : 'Browser-local mode'; ?></span>
            </header>
            <nav class="scwb-v330__tabs" role="tablist" aria-label="Platform handoff tools">
                <?php foreach (array('workspace'=>'Handoff Center','evidence'=>'Shared Evidence','site'=>'Site Intelligence','decision'=>'Decision Studio','librarian'=>'Research Librarian','validation'=>'Compatibility','bundles'=>'Portable Bundles') as $key=>$label) : ?>
                    <button type="button" role="tab" data-scwb-v330-tab="<?php echo esc_attr($key); ?>" class="<?php echo $key === $panel ? 'is-active' : ''; ?>" aria-selected="<?php echo $key === $panel ? 'true' : 'false'; ?>"><?php echo esc_html($label); ?></button>
                <?php endforeach; ?>
            </nav>
            <div class="scwb-v330__views">
                <section data-scwb-v330-view="workspace" class="scwb-v330__view<?php echo 'workspace' === $panel ? ' is-active' : ''; ?>" <?php echo 'workspace' === $panel ? '' : 'hidden'; ?>>
                    <h3>Build a cross-application handoff</h3>
                    <div class="scwb-v330__grid">
                        <?php self::select_field('Source application','source_app',array('workbench'=>'Workbench','site-intelligence'=>'Site Intelligence','decision-studio'=>'Decision Studio','research-librarian'=>'Research Librarian','knowledge-library'=>'Knowledge Library','lab'=>'Lab'),'workbench'); ?>
                        <?php self::select_field('Target application','target_app',array('decision-studio'=>'Decision Studio','site-intelligence'=>'Site Intelligence','research-librarian'=>'Research Librarian','workbench'=>'Workbench','knowledge-library'=>'Knowledge Library','lab'=>'Lab'),'decision-studio'); ?>
                        <?php self::select_field('Handoff type','handoff_type',array('workbench-to-decision-studio'=>'Workbench → Decision Studio','site-intelligence-to-workbench'=>'Site Intelligence → Workbench','decision-studio-to-workbench'=>'Decision Studio → Workbench','research-librarian-to-workbench'=>'Research Librarian → Workbench','workbench-to-research-librarian'=>'Workbench → Research Librarian','workbench-to-site-intelligence'=>'Workbench → Site Intelligence','workbench-to-lab'=>'Workbench → Lab','lab-to-workbench'=>'Lab → Workbench','generic'=>'Generic evidence handoff'),'workbench-to-decision-studio'); ?>
                        <?php self::field('Source project ID','source_project_id','text',$project); ?>
                        <?php self::field('Target project ID','target_project_id'); ?>
                        <?php self::field('Handoff title','title','text','Workbench platform handoff',true); ?>
                        <?php self::field('Objective','objective','textarea','',true); ?>
                        <?php self::field('Payload JSON','payload_json','textarea','{"capabilities":["evidence","calculations"],"records":[]}',true); ?>
                    </div>
                    <div class="scwb-v330__actions"><button data-scwb-v330-action="build-handoff">Build handoff</button><button data-scwb-v330-action="validate-handoff">Validate compatibility</button><button data-scwb-v330-action="save-handoff">Save private handoff</button><button data-scwb-v330-action="open-target">Open target</button></div>
                </section>
                <section data-scwb-v330-view="evidence" class="scwb-v330__view<?php echo 'evidence' === $panel ? ' is-active' : ''; ?>" <?php echo 'evidence' === $panel ? '' : 'hidden'; ?>>
                    <h3>Create a shared evidence record</h3>
                    <div class="scwb-v330__grid">
                        <?php self::field('Evidence ID','evidence_id'); ?><?php self::field('Title','evidence_title'); ?>
                        <?php self::select_field('Originating application','originating_app',array('workbench'=>'Workbench','site-intelligence'=>'Site Intelligence','decision-studio'=>'Decision Studio','research-librarian'=>'Research Librarian','knowledge-library'=>'Knowledge Library','lab'=>'Lab','external'=>'External'),'workbench'); ?>
                        <?php self::field('Source record ID','source_record_id'); ?><?php self::field('Source URL','source_url','url'); ?><?php self::field('Source type','source_type','text','record'); ?>
                        <?php self::field('Summary','evidence_summary','textarea','',true); ?>
                        <?php self::field('Claims JSON','claims_json','textarea','[]',true); ?><?php self::field('Citations JSON','citations_json','textarea','[]',true); ?>
                        <?php self::field('Methods, one per line','methods','textarea','',true); ?><?php self::field('Artifact IDs, one per line','artifact_ids','textarea','',true); ?>
                        <?php self::field('Data quality','data_quality','text','unreviewed'); ?><?php self::field('Uncertainty','uncertainty','text','not-recorded'); ?><?php self::field('Freshness','freshness','text','unknown'); ?><?php self::field('License','license','text','not-specified'); ?>
                    </div>
                    <div class="scwb-v330__actions"><button data-scwb-v330-action="normalize-evidence">Normalize evidence</button><button data-scwb-v330-action="add-evidence">Add to handoff</button><button data-scwb-v330-action="save-evidence">Save private evidence</button></div>
                    <div class="scwb-v330__evidence-list" data-scwb-v330-evidence-list></div>
                </section>
                <section data-scwb-v330-view="site" class="scwb-v330__view<?php echo 'site' === $panel ? ' is-active' : ''; ?>" <?php echo 'site' === $panel ? '' : 'hidden'; ?>>
                    <h3>Site Intelligence handoff</h3><p>Package indicators, maps, events, source records, and place-based datasets for Workbench modeling—or return modeled datasets and uncertainty records to Site Intelligence.</p>
                    <div class="scwb-v330__actions"><button data-scwb-v330-preset="site-intelligence-to-workbench">Prepare Site Intelligence → Workbench</button><button data-scwb-v330-preset="workbench-to-site-intelligence">Prepare Workbench → Site Intelligence</button></div>
                </section>
                <section data-scwb-v330-view="decision" class="scwb-v330__view<?php echo 'decision' === $panel ? ' is-active' : ''; ?>" <?php echo 'decision' === $panel ? '' : 'hidden'; ?>>
                    <h3>Decision Studio handoff</h3><p>Send alternatives, assumptions, scenario requirements, and trade-off questions into Workbench; return calculations, scenario results, sensitivities, and validation evidence to Decision Studio.</p>
                    <div class="scwb-v330__actions"><button data-scwb-v330-preset="decision-studio-to-workbench">Prepare Decision Studio → Workbench</button><button data-scwb-v330-preset="workbench-to-decision-studio">Prepare Workbench → Decision Studio</button></div>
                </section>
                <section data-scwb-v330-view="librarian" class="scwb-v330__view<?php echo 'librarian' === $panel ? ' is-active' : ''; ?>" <?php echo 'librarian' === $panel ? '' : 'hidden'; ?>>
                    <h3>Research Librarian handoff</h3><p>Convert grounded research routes, citations, article context, and unresolved questions into a Workbench project request; return evidence gaps, calculation records, and new source needs for continued research.</p>
                    <div class="scwb-v330__actions"><button data-scwb-v330-preset="research-librarian-to-workbench">Prepare Research Librarian → Workbench</button><button data-scwb-v330-preset="workbench-to-research-librarian">Prepare Workbench → Research Librarian</button></div>
                </section>
                <section data-scwb-v330-view="validation" class="scwb-v330__view<?php echo 'validation' === $panel ? ' is-active' : ''; ?>" <?php echo 'validation' === $panel ? '' : 'hidden'; ?>>
                    <h3>Compatibility and evidence merge</h3><p>Check required capabilities, schema expectations, missing evidence, and offline delivery needs before accepting a packet.</p>
                    <div class="scwb-v330__actions"><button data-scwb-v330-action="validate-handoff">Run compatibility report</button><button data-scwb-v330-action="merge-evidence">Check evidence conflicts</button><button data-scwb-v330-action="build-receipt">Build target receipt</button></div>
                </section>
                <section data-scwb-v330-view="bundles" class="scwb-v330__view<?php echo 'bundles' === $panel ? ' is-active' : ''; ?>" <?php echo 'bundles' === $panel ? '' : 'hidden'; ?>>
                    <h3>Portable handoff bundles</h3><p>Create a content-hashed JSON bundle when the receiving application is offline, hosted separately, or not yet connected through a live API.</p>
                    <div class="scwb-v330__actions"><button data-scwb-v330-action="build-bundle">Build bundle</button><button data-scwb-v330-action="download-bundle">Download bundle</button><button data-scwb-v330-action="export-last">Export current record</button></div>
                </section>
            </div>
            <aside class="scwb-v330__output"><header><strong>Handoff record</strong><span data-scwb-v330-message aria-live="polite">Ready.</span></header><pre data-scwb-v330-output>{}</pre></aside>
            <footer class="scwb-v330__boundary"><strong>Evidence boundary:</strong> Handoffs preserve context and provenance but do not automatically approve, publish, certify, or execute receiving-application decisions. Human review remains required.</footer>
        </section>
        <?php return ob_get_clean();
    }

    public static function permission() { return self::can_write(); }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/platform-handoff-status', array('methods'=>'GET','callback'=>array(__CLASS__,'rest_status'),'permission_callback'=>'__return_true'));
        register_rest_route('scwb/v1', '/shared-evidence', array(
            array('methods'=>'GET','callback'=>array(__CLASS__,'rest_list_evidence'),'permission_callback'=>array(__CLASS__,'permission')),
            array('methods'=>'POST','callback'=>array(__CLASS__,'rest_save_evidence'),'permission_callback'=>array(__CLASS__,'permission')),
        ));
        register_rest_route('scwb/v1', '/platform-handoffs', array(
            array('methods'=>'GET','callback'=>array(__CLASS__,'rest_list_handoffs'),'permission_callback'=>array(__CLASS__,'permission')),
            array('methods'=>'POST','callback'=>array(__CLASS__,'rest_save_handoff'),'permission_callback'=>array(__CLASS__,'permission')),
        ));
        register_rest_route('scwb/v1', '/handoff-receipts', array('methods'=>'POST','callback'=>array(__CLASS__,'rest_save_receipt'),'permission_callback'=>array(__CLASS__,'permission')));
    }

    public static function rest_status() {
        return rest_ensure_response(array('ok'=>true,'version'=>self::VERSION,'schema'=>'sc-workbench-platform-handoff-status/1.0','authenticated'=>self::can_write(),'evidencePostType'=>self::EVIDENCE_POST_TYPE,'handoffPostType'=>self::HANDOFF_POST_TYPE));
    }

    private static function list_records($type) {
        $posts = get_posts(array('post_type'=>$type,'post_status'=>'private','author'=>get_current_user_id(),'numberposts'=>100,'orderby'=>'modified','order'=>'DESC'));
        $items = array(); foreach ($posts as $post) { $record = get_post_meta($post->ID,self::RECORD_META,true); if (is_array($record)) { $record['wordpress_id']=(int)$post->ID; $items[]=$record; } }
        return $items;
    }

    public static function rest_list_evidence() { $items=self::list_records(self::EVIDENCE_POST_TYPE); return rest_ensure_response(array('ok'=>true,'evidence'=>$items,'count'=>count($items))); }
    public static function rest_list_handoffs() { $items=self::list_records(self::HANDOFF_POST_TYPE); return rest_ensure_response(array('ok'=>true,'handoffs'=>$items,'count'=>count($items))); }

    private static function save_record($type, $record, $fallback_title) {
        $title = sanitize_text_field($record['title'] ?? $fallback_title);
        $post_id = wp_insert_post(array('post_type'=>$type,'post_status'=>'private','post_title'=>$title,'post_author'=>get_current_user_id()), true);
        if (is_wp_error($post_id)) { return $post_id; }
        update_post_meta($post_id,self::RECORD_META,$record);
        $hash = sanitize_text_field($record['evidence_hash'] ?? $record['packetHash'] ?? $record['receiptHash'] ?? '');
        update_post_meta($post_id,self::HASH_META,$hash);
        return (int)$post_id;
    }

    public static function rest_save_evidence($request) {
        $record = (array)$request->get_json_params();
        $post_id = self::save_record(self::EVIDENCE_POST_TYPE,$record,'Shared evidence');
        if (is_wp_error($post_id)) { return $post_id; }
        return rest_ensure_response(array('ok'=>true,'wordpress_id'=>$post_id,'record'=>$record));
    }

    public static function rest_save_handoff($request) {
        $record = (array)$request->get_json_params();
        $packet = isset($record['packet']) && is_array($record['packet']) ? $record['packet'] : $record;
        $post_id = self::save_record(self::HANDOFF_POST_TYPE,$packet,'Platform handoff');
        if (is_wp_error($post_id)) { return $post_id; }
        return rest_ensure_response(array('ok'=>true,'wordpress_id'=>$post_id,'record'=>$packet));
    }

    public static function rest_save_receipt($request) {
        $record = (array)$request->get_json_params();
        $post_id = self::save_record(self::HANDOFF_POST_TYPE,$record,'Handoff receipt');
        if (is_wp_error($post_id)) { return $post_id; }
        return rest_ensure_response(array('ok'=>true,'wordpress_id'=>$post_id,'receipt'=>$record));
    }
}

SCWB_V330_Platform_Handoffs::boot();
