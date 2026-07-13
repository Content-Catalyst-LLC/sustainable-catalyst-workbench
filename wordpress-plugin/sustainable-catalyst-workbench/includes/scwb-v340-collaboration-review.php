<?php
/**
 * Workbench v3.4.0 — Collaboration, Review, and Technical Sign-Off.
 */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V340_Collaboration_Review {
    const VERSION = '3.4.0';
    const REVIEW_POST_TYPE = 'scwb_review';
    const SNAPSHOT_POST_TYPE = 'scwb_review_snap';
    const RECORD_META = '_scwb_v340_record';
    const HASH_META = '_scwb_v340_hash';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 6);
        add_action('init', array(__CLASS__, 'register_post_types'), 7);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 1005);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V340_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v340.css';
        $js = $base . '/assets/js/sc-workbench-v340.js';
        wp_register_style('scwb-v340', plugins_url('assets/css/sc-workbench-v340.css', SCWB_V340_PLUGIN_FILE), array('scwb-primary-repair'), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v340', plugins_url('assets/js/sc-workbench-v340.js', SCWB_V340_PLUGIN_FILE), array('scwb-primary-repair'), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_post_types() {
        register_post_type(self::REVIEW_POST_TYPE, array(
            'labels' => array('name' => __('Workbench Technical Reviews', 'sustainable-catalyst-workbench')),
            'public' => false, 'show_ui' => true, 'show_in_menu' => true, 'show_in_rest' => false,
            'supports' => array('title', 'author', 'excerpt'), 'capability_type' => 'post', 'map_meta_cap' => true,
        ));
        register_post_type(self::SNAPSHOT_POST_TYPE, array(
            'labels' => array('name' => __('Workbench Review Snapshots', 'sustainable-catalyst-workbench')),
            'public' => false, 'show_ui' => true, 'show_in_menu' => false, 'show_in_rest' => false,
            'supports' => array('title', 'author'), 'capability_type' => 'post', 'map_meta_cap' => true,
        ));
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_collaboration_review' => 'workspace',
            'sc_workbench_review_queue' => 'queue',
            'sc_workbench_record_comments' => 'comments',
            'sc_workbench_change_requests' => 'changes',
            'sc_workbench_revision_compare' => 'compare',
            'sc_workbench_technical_signoff' => 'signoff',
            'sc_workbench_review_dossier' => 'dossier',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, static function($atts = array()) use ($panel) {
                    return SCWB_V340_Collaboration_Review::render($panel, $atts);
                });
            }
        }
    }

    private static function can_write() {
        return function_exists('is_user_logged_in') && is_user_logged_in() && function_exists('current_user_can') && current_user_can('edit_posts');
    }

    private static function enqueue_assets() {
        self::register_assets();
        wp_enqueue_style('scwb-v340');
        wp_enqueue_script('scwb-v340');
        if (function_exists('wp_localize_script')) {
            wp_localize_script('scwb-v340', 'SCWBV340Config', array(
                'version' => self::VERSION,
                'restUrl' => function_exists('rest_url') ? esc_url_raw(rest_url('scwb/v1')) : '/wp-json/scwb/v1',
                'nonce' => function_exists('wp_create_nonce') ? wp_create_nonce('wp_rest') : '',
                'authenticated' => self::can_write(),
            ));
        }
    }

    private static function field($label, $name, $type = 'text', $value = '', $wide = false) { ?>
        <label class="scwb-v340__field<?php echo $wide ? ' scwb-v340__field--wide' : ''; ?>">
            <span><?php echo esc_html($label); ?></span>
            <?php if ('textarea' === $type) : ?>
                <textarea data-scwb-v340-field="<?php echo esc_attr($name); ?>"><?php echo esc_textarea($value); ?></textarea>
            <?php else : ?>
                <input type="<?php echo esc_attr($type); ?>" data-scwb-v340-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>">
            <?php endif; ?>
        </label>
    <?php }

    private static function select_field($label, $name, $options, $selected = '') { ?>
        <label class="scwb-v340__field"><span><?php echo esc_html($label); ?></span><select data-scwb-v340-field="<?php echo esc_attr($name); ?>">
            <?php foreach ($options as $value => $caption) : ?><option value="<?php echo esc_attr($value); ?>" <?php selected($selected, $value); ?>><?php echo esc_html($caption); ?></option><?php endforeach; ?>
        </select></label>
    <?php }

    public static function render($panel = 'workspace', $atts = array()) {
        self::enqueue_assets();
        $atts = shortcode_atts(array('project' => 'default', 'title' => 'Collaboration, Review, and Technical Sign-Off', 'display' => 'full'), $atts, 'sc_workbench_collaboration_review');
        $display = sanitize_key($atts['display']);
        if (!in_array($display, array('inline','compact','full','drawer'), true)) { $display = 'full'; }
        $allowed = array('workspace','queue','comments','changes','compare','signoff','dossier');
        if (!in_array($panel, $allowed, true)) { $panel = 'workspace'; }
        $project = sanitize_key($atts['project']) ?: 'default';
        $instance = 'scwb-v340-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v340 scwb-v340--<?php echo esc_attr($display); ?>" data-scwb-v340 data-scwb-v340-panel="<?php echo esc_attr($panel); ?>" data-scwb-v340-project="<?php echo esc_attr($project); ?>" data-scwb-v340-version="3.4.0">
            <header class="scwb-v340__header">
                <div><p class="scwb-v340__eyebrow">Sustainable Catalyst Workbench · v3.4.0</p><h2><?php echo esc_html($atts['title']); ?></h2><p>Assign reviewers, discuss exact records, request and resolve changes, compare revisions, preserve immutable review snapshots, and export auditable approval dossiers.</p></div>
                <span class="scwb-v340__status" data-scwb-v340-status aria-live="polite"><?php echo self::can_write() ? 'Private review records available' : 'Browser-local review mode'; ?></span>
            </header>
            <nav class="scwb-v340__tabs" role="tablist" aria-label="Review and sign-off tools">
                <?php foreach (array('workspace'=>'Review Workspace','queue'=>'Review Queue','comments'=>'Comments','changes'=>'Changes','compare'=>'Revision Compare','signoff'=>'Sign-Off','dossier'=>'Review Dossier') as $key=>$label) : ?>
                    <button type="button" role="tab" data-scwb-v340-tab="<?php echo esc_attr($key); ?>" class="<?php echo $key === $panel ? 'is-active' : ''; ?>" aria-selected="<?php echo $key === $panel ? 'true' : 'false'; ?>"><?php echo esc_html($label); ?></button>
                <?php endforeach; ?>
            </nav>
            <div class="scwb-v340__views">
                <section data-scwb-v340-view="workspace" class="scwb-v340__view<?php echo 'workspace' === $panel ? ' is-active' : ''; ?>" <?php echo 'workspace' === $panel ? '' : 'hidden'; ?>>
                    <h3>Build a technical review record</h3><p>Review calculations, code, models, experiments, hardware evidence, requirements, and documents without treating internal approval as professional certification.</p>
                    <div class="scwb-v340__grid">
                        <?php self::field('Project ID','project_id','text',$project); ?><?php self::field('Review ID','review_id'); ?>
                        <?php self::field('Review title','title','text','Technical review',true); ?><?php self::field('Revision','revision','text','1'); ?>
                        <?php self::select_field('Review state','state',array('draft'=>'Draft','queued'=>'Queued','in-review'=>'In review','changes-requested'=>'Changes requested','conditionally-approved'=>'Conditionally approved','approved'=>'Approved','rejected'=>'Rejected','closed'=>'Closed'),'draft'); ?>
                        <?php self::field('Owner ID','owner_id'); ?>
                        <?php self::field('Reviewers JSON','reviewers_json','textarea','[{"reviewer_id":"reviewer-1","display_name":"Reviewer","role":"reviewer","independent":false}]',true); ?>
                        <?php self::field('Review items JSON','items_json','textarea','[{"record_id":"calculation-1","record_type":"calculation","title":"Calculation record","revision":"1","criticality":"high","requirement_ids":["REQ-1"],"evidence_ids":[]}]',true); ?>
                        <?php self::field('Requirement IDs, one per line','requirement_ids','textarea','REQ-1',true); ?>
                    </div>
                    <div class="scwb-v340__actions"><button data-scwb-v340-action="build-review">Build review</button><button data-scwb-v340-action="queue-review">Add to queue</button><button data-scwb-v340-action="save-review">Save private review</button></div>
                </section>
                <section data-scwb-v340-view="queue" class="scwb-v340__view<?php echo 'queue' === $panel ? ' is-active' : ''; ?>" <?php echo 'queue' === $panel ? '' : 'hidden'; ?>>
                    <h3>Reviewer queue</h3><p>Prioritize queued reviews, changes requested, unresolved critical items, and conditional approvals.</p>
                    <div class="scwb-v340__actions"><button data-scwb-v340-action="build-queue">Build queue</button><button data-scwb-v340-action="load-private-reviews">Load private reviews</button></div><div data-scwb-v340-queue class="scwb-v340__queue"></div>
                </section>
                <section data-scwb-v340-view="comments" class="scwb-v340__view<?php echo 'comments' === $panel ? ' is-active' : ''; ?>" <?php echo 'comments' === $panel ? '' : 'hidden'; ?>>
                    <h3>Record-level comments</h3><p>Attach discussion to a record, field path, revision, calculation, code block, test, or evidence item.</p>
                    <div class="scwb-v340__grid"><?php self::field('Reviewer ID','comment_reviewer_id','text','reviewer-1'); ?><?php self::field('Target record ID','comment_target_record_id','text','calculation-1'); ?><?php self::field('Target path','comment_target_path','text','result.value'); ?><?php self::field('Comment','comment_body','textarea','',true); ?></div>
                    <div class="scwb-v340__actions"><button data-scwb-v340-action="add-comment">Add comment</button><button data-scwb-v340-action="resolve-comment">Resolve latest</button></div>
                </section>
                <section data-scwb-v340-view="changes" class="scwb-v340__view<?php echo 'changes' === $panel ? ' is-active' : ''; ?>" <?php echo 'changes' === $panel ? '' : 'hidden'; ?>>
                    <h3>Requested changes and resolutions</h3><p>Track priority, assignment, evidence, resolution, accepted risk, and closure.</p>
                    <div class="scwb-v340__grid"><?php self::field('Change title','change_title','text','Review required'); ?><?php self::select_field('Priority','change_priority',array('low'=>'Low','medium'=>'Medium','high'=>'High','critical'=>'Critical'),'high'); ?><?php self::field('Target record ID','change_target_record_id','text','calculation-1'); ?><?php self::field('Assigned to','change_assigned_to'); ?><?php self::field('Description','change_description','textarea','',true); ?><?php self::field('Resolution','change_resolution','textarea','',true); ?></div>
                    <div class="scwb-v340__actions"><button data-scwb-v340-action="request-change">Request change</button><button data-scwb-v340-action="resolve-change">Resolve latest</button></div>
                </section>
                <section data-scwb-v340-view="compare" class="scwb-v340__view<?php echo 'compare' === $panel ? ' is-active' : ''; ?>" <?php echo 'compare' === $panel ? '' : 'hidden'; ?>>
                    <h3>Revision comparison</h3><p>Compare canonical JSON revisions and create a field-level added, removed, and modified record.</p>
                    <div class="scwb-v340__grid"><?php self::field('Left revision JSON','left_json','textarea','{"revision":"1","result":{"value":10}}',true); ?><?php self::field('Right revision JSON','right_json','textarea','{"revision":"2","result":{"value":12}}',true); ?></div>
                    <div class="scwb-v340__actions"><button data-scwb-v340-action="compare-revisions">Compare revisions</button><button data-scwb-v340-action="build-traceability">Build traceability</button></div>
                </section>
                <section data-scwb-v340-view="signoff" class="scwb-v340__view<?php echo 'signoff' === $panel ? ' is-active' : ''; ?>" <?php echo 'signoff' === $panel ? '' : 'hidden'; ?>>
                    <h3>Technical sign-off</h3><p>Create an internal review decision or document a qualified-professional review with an explicit credential reference. Workbench never creates a professional license or regulatory approval.</p>
                    <div class="scwb-v340__grid"><?php self::field('Reviewer ID','signoff_reviewer_id','text','reviewer-1'); ?><?php self::field('Reviewer name','signoff_reviewer_name','text','Reviewer'); ?><?php self::select_field('Decision','signoff_decision',array('approved'=>'Approved','conditionally-approved'=>'Conditionally approved','rejected'=>'Rejected','returned-for-changes'=>'Returned for changes'),'returned-for-changes'); ?><?php self::select_field('Scope','signoff_scope',array('internal-review'=>'Internal review','qualified-professional-review'=>'Qualified professional review'),'internal-review'); ?><?php self::field('Credential reference','credential_reference'); ?><?php self::field('Rationale','signoff_rationale','textarea','',true); ?><?php self::field('Conditions, one per line','signoff_conditions','textarea','',true); ?></div>
                    <div class="scwb-v340__actions"><button data-scwb-v340-action="build-snapshot">Lock review snapshot</button><button data-scwb-v340-action="build-signoff">Build sign-off</button><button data-scwb-v340-action="save-snapshot">Save private snapshot</button></div>
                </section>
                <section data-scwb-v340-view="dossier" class="scwb-v340__view<?php echo 'dossier' === $panel ? ' is-active' : ''; ?>" <?php echo 'dossier' === $panel ? '' : 'hidden'; ?>>
                    <h3>Review and approval dossier</h3><p>Export the review, comments, changes, revision comparison, traceability, snapshots, decisions, rationale, conditions, and scope boundary as a content-hashed record.</p>
                    <div class="scwb-v340__actions"><button data-scwb-v340-action="build-dossier">Build dossier</button><button data-scwb-v340-action="download-dossier">Download JSON dossier</button><button data-scwb-v340-action="export-last">Export current record</button></div>
                </section>
            </div>
            <aside class="scwb-v340__output"><header><strong>Review record</strong><span data-scwb-v340-message aria-live="polite">Ready.</span></header><pre data-scwb-v340-output>{}</pre></aside>
            <footer class="scwb-v340__boundary"><strong>Sign-off boundary:</strong> Internal approvals document organizational review only. Qualified-professional review must include a credential reference and still does not substitute for legally required seals, filings, certifications, permits, or regulatory decisions.</footer>
        </section>
        <?php return ob_get_clean();
    }

    public static function permission() { return self::can_write(); }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/collaboration-review-status', array('methods'=>'GET','callback'=>array(__CLASS__,'rest_status'),'permission_callback'=>'__return_true'));
        register_rest_route('scwb/v1', '/technical-reviews', array(
            array('methods'=>'GET','callback'=>array(__CLASS__,'rest_list_reviews'),'permission_callback'=>array(__CLASS__,'permission')),
            array('methods'=>'POST','callback'=>array(__CLASS__,'rest_save_review'),'permission_callback'=>array(__CLASS__,'permission')),
        ));
        register_rest_route('scwb/v1', '/review-snapshots', array(
            array('methods'=>'GET','callback'=>array(__CLASS__,'rest_list_snapshots'),'permission_callback'=>array(__CLASS__,'permission')),
            array('methods'=>'POST','callback'=>array(__CLASS__,'rest_save_snapshot'),'permission_callback'=>array(__CLASS__,'permission')),
        ));
        register_rest_route('scwb/v1', '/review-signoffs', array('methods'=>'POST','callback'=>array(__CLASS__,'rest_save_signoff'),'permission_callback'=>array(__CLASS__,'permission')));
        register_rest_route('scwb/v1', '/review-comments', array('methods'=>'POST','callback'=>array(__CLASS__,'rest_save_comment'),'permission_callback'=>array(__CLASS__,'permission')));
    }

    public static function rest_status() {
        return rest_ensure_response(array('ok'=>true,'version'=>self::VERSION,'schema'=>'sc-workbench-collaboration-review-status/1.0','authenticated'=>self::can_write(),'reviewPostType'=>self::REVIEW_POST_TYPE,'snapshotPostType'=>self::SNAPSHOT_POST_TYPE));
    }

    private static function list_records($type) {
        $posts = get_posts(array('post_type'=>$type,'post_status'=>'private','author'=>get_current_user_id(),'numberposts'=>100,'orderby'=>'modified','order'=>'DESC'));
        $items = array(); foreach ($posts as $post) { $record = get_post_meta($post->ID,self::RECORD_META,true); if (is_array($record)) { $record['wordpress_id']=(int)$post->ID; $items[]=$record; } }
        return $items;
    }

    private static function save_record($type, $record, $fallback_title) {
        $title = sanitize_text_field($record['title'] ?? $record['review']['title'] ?? $fallback_title);
        $post_id = wp_insert_post(array('post_type'=>$type,'post_status'=>'private','post_title'=>$title,'post_author'=>get_current_user_id()), true);
        if (is_wp_error($post_id)) { return $post_id; }
        update_post_meta($post_id,self::RECORD_META,$record);
        $hash = sanitize_text_field($record['reviewHash'] ?? $record['snapshotHash'] ?? $record['signoffHash'] ?? $record['comment_hash'] ?? '');
        update_post_meta($post_id,self::HASH_META,$hash);
        return (int)$post_id;
    }

    public static function rest_list_reviews() { $items=self::list_records(self::REVIEW_POST_TYPE); return rest_ensure_response(array('ok'=>true,'reviews'=>$items,'count'=>count($items))); }
    public static function rest_list_snapshots() { $items=self::list_records(self::SNAPSHOT_POST_TYPE); return rest_ensure_response(array('ok'=>true,'snapshots'=>$items,'count'=>count($items))); }
    public static function rest_save_review($request) { $record=(array)$request->get_json_params(); $id=self::save_record(self::REVIEW_POST_TYPE,$record,'Technical review'); if(is_wp_error($id))return$id; return rest_ensure_response(array('ok'=>true,'wordpress_id'=>$id,'record'=>$record)); }
    public static function rest_save_snapshot($request) { $record=(array)$request->get_json_params(); $id=self::save_record(self::SNAPSHOT_POST_TYPE,$record,'Review snapshot'); if(is_wp_error($id))return$id; return rest_ensure_response(array('ok'=>true,'wordpress_id'=>$id,'record'=>$record)); }
    public static function rest_save_signoff($request) { $record=(array)$request->get_json_params(); $id=self::save_record(self::REVIEW_POST_TYPE,$record,'Technical sign-off'); if(is_wp_error($id))return$id; return rest_ensure_response(array('ok'=>true,'wordpress_id'=>$id,'record'=>$record)); }
    public static function rest_save_comment($request) { $record=(array)$request->get_json_params(); $id=self::save_record(self::REVIEW_POST_TYPE,$record,'Review comment'); if(is_wp_error($id))return$id; return rest_ensure_response(array('ok'=>true,'wordpress_id'=>$id,'record'=>$record)); }
}

SCWB_V340_Collaboration_Review::boot();
