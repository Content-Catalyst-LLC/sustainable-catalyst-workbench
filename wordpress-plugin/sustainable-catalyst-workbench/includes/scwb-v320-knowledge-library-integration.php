<?php
/**
 * Workbench v3.2.0 — Knowledge Library and Article Integration.
 */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V320_Knowledge_Library_Integration {
    const VERSION = '3.2.0';
    const LINK_POST_TYPE = 'scwb_library_link';
    const DRAFT_POST_TYPE = 'scwb_article_draft';
    const RECORD_META = '_scwb_v320_record';
    const HASH_META = '_scwb_v320_hash';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 6);
        add_action('init', array(__CLASS__, 'register_post_types'), 7);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 1003);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V320_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v320.css';
        $js = $base . '/assets/js/sc-workbench-v320.js';
        wp_register_style('scwb-v320', plugins_url('assets/css/sc-workbench-v320.css', SCWB_V320_PLUGIN_FILE), array('scwb-primary-repair'), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v320', plugins_url('assets/js/sc-workbench-v320.js', SCWB_V320_PLUGIN_FILE), array('scwb-primary-repair'), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_post_types() {
        register_post_type(self::LINK_POST_TYPE, array(
            'labels' => array('name' => __('Workbench Library Links', 'sustainable-catalyst-workbench')),
            'public' => false, 'show_ui' => true, 'show_in_menu' => false, 'show_in_rest' => false,
            'supports' => array('title', 'author'), 'capability_type' => 'post', 'map_meta_cap' => true,
        ));
        register_post_type(self::DRAFT_POST_TYPE, array(
            'labels' => array('name' => __('Workbench Article Drafts', 'sustainable-catalyst-workbench')),
            'public' => false, 'show_ui' => true, 'show_in_menu' => true, 'show_in_rest' => false,
            'supports' => array('title', 'editor', 'author', 'excerpt'), 'capability_type' => 'post', 'map_meta_cap' => true,
        ));
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_library_integration' => 'workspace',
            'sc_workbench_article_linker' => 'articles',
            'sc_workbench_formula_registry' => 'formulas',
            'sc_workbench_calculator_embed' => 'embeds',
            'sc_workbench_librarian_handoff' => 'librarian',
            'sc_workbench_article_draft_return' => 'drafts',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, static function($atts = array()) use ($panel) {
                    return SCWB_V320_Knowledge_Library_Integration::render($panel, $atts);
                });
            }
        }
    }

    private static function can_write() {
        return function_exists('is_user_logged_in') && is_user_logged_in() && function_exists('current_user_can') && current_user_can('edit_posts');
    }

    private static function enqueue_assets() {
        self::register_assets();
        wp_enqueue_style('scwb-v320');
        wp_enqueue_script('scwb-v320');
        if (function_exists('wp_localize_script')) {
            wp_localize_script('scwb-v320', 'SCWBV320Config', array(
                'version' => self::VERSION,
                'restUrl' => function_exists('rest_url') ? esc_url_raw(rest_url('scwb/v1')) : '/wp-json/scwb/v1',
                'nonce' => function_exists('wp_create_nonce') ? wp_create_nonce('wp_rest') : '',
                'authenticated' => self::can_write(),
                'currentPostId' => function_exists('get_the_ID') ? (int) get_the_ID() : 0,
                'currentPostTitle' => function_exists('get_the_title') ? sanitize_text_field(get_the_title()) : '',
                'currentPostUrl' => function_exists('get_permalink') ? esc_url_raw(get_permalink()) : '',
            ));
        }
    }

    private static function field($label, $name, $type = 'text', $value = '', $wide = false) { ?>
        <label class="scwb-v320__field<?php echo $wide ? ' scwb-v320__field--wide' : ''; ?>">
            <span><?php echo esc_html($label); ?></span>
            <?php if ('textarea' === $type) : ?>
                <textarea data-scwb-v320-field="<?php echo esc_attr($name); ?>"><?php echo esc_textarea($value); ?></textarea>
            <?php else : ?>
                <input type="<?php echo esc_attr($type); ?>" data-scwb-v320-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>">
            <?php endif; ?>
        </label>
    <?php }

    public static function render($panel = 'workspace', $atts = array()) {
        self::enqueue_assets();
        $atts = shortcode_atts(array('project' => 'default', 'title' => 'Knowledge Library and Article Integration', 'display' => 'full', 'article' => ''), $atts, 'sc_workbench_library_integration');
        $display = sanitize_key($atts['display']);
        if (!in_array($display, array('inline','compact','full','drawer'), true)) { $display = 'full'; }
        $allowed = array('workspace','articles','formulas','embeds','librarian','drafts');
        if (!in_array($panel, $allowed, true)) { $panel = 'workspace'; }
        $instance = 'scwb-v320-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v320 scwb-v320--<?php echo esc_attr($display); ?>" data-scwb-v320 data-scwb-v320-panel="<?php echo esc_attr($panel); ?>" data-scwb-v320-project="<?php echo esc_attr(sanitize_key($atts['project']) ?: 'default'); ?>" data-scwb-v320-version="3.2.0">
            <header class="scwb-v320__header">
                <div><p class="scwb-v320__eyebrow">Sustainable Catalyst Workbench · v3.2.0</p><h2><?php echo esc_html($atts['title']); ?></h2><p>Connect Knowledge Library articles, formulas, calculators, citations, Research Librarian routes, persistent projects, and private draft-return records.</p></div>
                <span class="scwb-v320__status" data-scwb-v320-status aria-live="polite"><?php echo self::can_write() ? 'Browser + private WordPress integration' : 'Browser-local planning'; ?></span>
            </header>
            <nav class="scwb-v320__nav" role="tablist" aria-label="Knowledge Library integration tools">
                <?php foreach (array('workspace'=>'Overview','articles'=>'Article links','formulas'=>'Formula registry','embeds'=>'Calculator embeds','librarian'=>'Research Librarian','drafts'=>'Draft return') as $key=>$label) : ?>
                    <button type="button" role="tab" class="scwb-v320__tab<?php echo $panel === $key ? ' is-active' : ''; ?>" aria-selected="<?php echo $panel === $key ? 'true' : 'false'; ?>" data-scwb-v320-tab="<?php echo esc_attr($key); ?>"><?php echo esc_html($label); ?></button>
                <?php endforeach; ?>
            </nav>
            <div class="scwb-v320__body">
                <section class="scwb-v320__panel<?php echo 'workspace' === $panel ? ' is-active' : ''; ?>" data-scwb-v320-view="workspace">
                    <div class="scwb-v320__cards">
                        <article><strong>Article-aware projects</strong><span>Turn a Library article into a persistent Workbench project with source, formula, citation, and topic context.</span></article>
                        <article><strong>Formula-aware embeds</strong><span>Register article equations and produce reviewable compact-calculator shortcode plans.</span></article>
                        <article><strong>Grounded routing</strong><span>Send an article question to a relevant Workbench studio through a site-scoped Research Librarian packet.</span></article>
                        <article><strong>Human-reviewed return</strong><span>Save generated reports as private or draft WordPress records, never automatic public posts.</span></article>
                    </div>
                    <div class="scwb-v320__summary" data-scwb-v320-summary>No article record loaded.</div>
                </section>
                <section class="scwb-v320__panel<?php echo 'articles' === $panel ? ' is-active' : ''; ?>" data-scwb-v320-view="articles">
                    <div class="scwb-v320__actions"><button type="button" class="scwb-v320__button" data-scwb-v320-action="inspect-page">Inspect current page</button><button type="button" class="scwb-v320__button scwb-v320__button--primary" data-scwb-v320-action="normalize-article">Normalize article</button><button type="button" class="scwb-v320__button" data-scwb-v320-action="create-project">Create persistent project</button><button type="button" class="scwb-v320__button" data-scwb-v320-action="save-link">Save private link</button></div>
                    <div class="scwb-v320__form-grid">
                        <?php self::field('Article ID', 'article_id', 'text', sanitize_key($atts['article'])); ?>
                        <?php self::field('WordPress ID', 'wordpress_id', 'number', '0'); ?>
                        <?php self::field('Article title', 'title', 'text', ''); ?>
                        <?php self::field('Article URL', 'url', 'url', ''); ?>
                        <?php self::field('Topics, comma separated', 'topics', 'text', ''); ?>
                        <?php self::field('Excerpt', 'excerpt', 'textarea', '', true); ?>
                        <?php self::field('Article record JSON', 'article_json', 'textarea', '{"post_type":"post","status":"publish","citations":[],"formulas":[],"metadata":{}}', true); ?>
                    </div>
                </section>
                <section class="scwb-v320__panel<?php echo 'formulas' === $panel ? ' is-active' : ''; ?>" data-scwb-v320-view="formulas">
                    <div class="scwb-v320__actions"><button type="button" class="scwb-v320__button scwb-v320__button--primary" data-scwb-v320-action="build-formula-registry">Build registry</button><button type="button" class="scwb-v320__button" data-scwb-v320-action="add-formula">Add formula</button><button type="button" class="scwb-v320__button" data-scwb-v320-action="export-record">Export JSON</button></div>
                    <?php self::field('Formula records JSON', 'formulas_json', 'textarea', '[{"expression":"F = ma","label":"Newton second law","context":"Force relationship","variables":{"F":"force","m":"mass","a":"acceleration"},"units":{"F":"N","m":"kg","a":"m/s^2"},"calculator":"force","placement":"compact"}]', true); ?>
                    <div class="scwb-v320__registry" data-scwb-v320-registry></div>
                </section>
                <section class="scwb-v320__panel<?php echo 'embeds' === $panel ? ' is-active' : ''; ?>" data-scwb-v320-view="embeds">
                    <div class="scwb-v320__actions"><button type="button" class="scwb-v320__button scwb-v320__button--primary" data-scwb-v320-action="build-embed-plan">Generate embed plan</button><button type="button" class="scwb-v320__button" data-scwb-v320-action="copy-shortcodes">Copy shortcodes</button><button type="button" class="scwb-v320__button" data-scwb-v320-action="export-record">Export JSON</button></div>
                    <p class="scwb-v320__note">Generated shortcodes are placement recommendations. Review calculator maturity, article context, and responsible-use boundaries before publishing.</p>
                    <div class="scwb-v320__embeds" data-scwb-v320-embeds></div>
                </section>
                <section class="scwb-v320__panel<?php echo 'librarian' === $panel ? ' is-active' : ''; ?>" data-scwb-v320-view="librarian">
                    <div class="scwb-v320__form-grid">
                        <?php self::field('Question grounded in this article', 'question', 'textarea', 'What calculation or model best supports this article?', true); ?>
                        <label class="scwb-v320__field"><span>Requested action</span><select data-scwb-v320-field="requested_action"><option>explain</option><option selected>calculate</option><option>graph</option><option>simulate</option><option>validate</option><option>build</option><option>document</option></select></label>
                    </div>
                    <div class="scwb-v320__actions"><button type="button" class="scwb-v320__button scwb-v320__button--primary" data-scwb-v320-action="build-librarian-route">Build grounded route</button><button type="button" class="scwb-v320__button" data-scwb-v320-action="open-target-studio">Open target studio</button><button type="button" class="scwb-v320__button" data-scwb-v320-action="export-record">Export route</button></div>
                </section>
                <section class="scwb-v320__panel<?php echo 'drafts' === $panel ? ' is-active' : ''; ?>" data-scwb-v320-view="drafts">
                    <div class="scwb-v320__form-grid">
                        <?php self::field('Draft title', 'draft_title', 'text', ''); ?>
                        <?php self::field('Project ID', 'draft_project_id', 'text', sanitize_key($atts['project']) ?: 'default'); ?>
                        <label class="scwb-v320__field"><span>Visibility</span><select data-scwb-v320-field="draft_visibility"><option value="draft">Draft</option><option value="private">Private</option></select></label>
                        <?php self::field('Evidence IDs, one per line', 'draft_evidence_ids', 'textarea', '', true); ?>
                        <?php self::field('Artifact IDs, one per line', 'draft_artifact_ids', 'textarea', '', true); ?>
                        <?php self::field('Draft content (Markdown)', 'draft_content', 'textarea', '# Workbench article return\n\nHuman review required before publication.', true); ?>
                    </div>
                    <div class="scwb-v320__actions"><button type="button" class="scwb-v320__button scwb-v320__button--primary" data-scwb-v320-action="build-draft-plan">Build draft plan</button><button type="button" class="scwb-v320__button" data-scwb-v320-action="save-wordpress-draft">Save private WordPress draft</button><button type="button" class="scwb-v320__button" data-scwb-v320-action="export-record">Export plan</button></div>
                </section>
            </div>
            <div class="scwb-v320__workspace"><div class="scwb-v320__message" data-scwb-v320-message aria-live="polite"></div><pre class="scwb-v320__result" data-scwb-v320-result>{}</pre></div>
            <p class="scwb-v320__boundary"><strong>Publication boundary:</strong> article links, formula matches, calculator placements, Research Librarian routes, citations, and generated drafts require human review. Workbench does not automatically publish or certify content.</p>
        </section>
        <?php return ob_get_clean();
    }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/library-integration-status', array('methods'=>'GET','callback'=>array(__CLASS__,'rest_status'),'permission_callback'=>'__return_true'));
        register_rest_route('scwb/v1', '/library-links', array(
            array('methods'=>'GET','callback'=>array(__CLASS__,'rest_list_links'),'permission_callback'=>array(__CLASS__,'permission')),
            array('methods'=>'POST','callback'=>array(__CLASS__,'rest_save_link'),'permission_callback'=>array(__CLASS__,'permission')),
        ));
        register_rest_route('scwb/v1', '/article-drafts', array('methods'=>'POST','callback'=>array(__CLASS__,'rest_save_draft'),'permission_callback'=>array(__CLASS__,'permission')));
        register_rest_route('scwb/v1', '/library-article/(?P<id>\\d+)', array('methods'=>'GET','callback'=>array(__CLASS__,'rest_article'),'permission_callback'=>'__return_true'));
    }

    public static function permission() { return self::can_write(); }
    private static function payload($request) { $data = method_exists($request,'get_json_params') ? $request->get_json_params() : array(); return is_array($data) ? $data : array(); }
    public static function rest_status() { return rest_ensure_response(array('ok'=>true,'version'=>self::VERSION,'schema'=>'sc-workbench-library-integration-status/1.0','authenticated'=>self::can_write(),'linkPostType'=>self::LINK_POST_TYPE,'draftPostType'=>self::DRAFT_POST_TYPE)); }

    public static function rest_article($request) {
        $id = absint($request['id']); $post = function_exists('get_post') ? get_post($id) : null;
        if (!$post) { return new WP_Error('scwb_article_missing', 'Article not found.', array('status'=>404)); }
        return rest_ensure_response(array('ok'=>true,'article'=>array('article_id'=>'wp-'.$id,'wordpress_id'=>$id,'title'=>get_the_title($id),'url'=>get_permalink($id),'excerpt'=>wp_strip_all_tags(get_the_excerpt($id)),'post_type'=>$post->post_type,'status'=>$post->post_status,'topics'=>array(),'citations'=>array(),'formulas'=>array(),'metadata'=>array())));
    }

    public static function rest_list_links() {
        $posts = get_posts(array('post_type'=>self::LINK_POST_TYPE,'post_status'=>'private','author'=>get_current_user_id(),'posts_per_page'=>200,'orderby'=>'modified','order'=>'DESC'));
        $items = array(); foreach ($posts as $post) { $data = json_decode((string)get_post_meta($post->ID,self::RECORD_META,true),true); if (is_array($data)) { $data['wordpress_id']=(int)$post->ID; $items[]=$data; } }
        return rest_ensure_response(array('ok'=>true,'links'=>$items,'count'=>count($items)));
    }

    public static function rest_save_link($request) {
        $data = self::payload($request); $title = sanitize_text_field(isset($data['title']) ? $data['title'] : 'Workbench Library link');
        $post_id = wp_insert_post(array('post_type'=>self::LINK_POST_TYPE,'post_status'=>'private','post_title'=>$title,'post_author'=>get_current_user_id()),true);
        if (is_wp_error($post_id)) { return $post_id; }
        $record = array('schema'=>'sc-workbench-library-link/1.0','version'=>self::VERSION,'created_at'=>gmdate('c'),'article'=>isset($data['article'])&&is_array($data['article'])?$data['article']:array(),'project_id'=>sanitize_key(isset($data['project_id'])?$data['project_id']:'default'),'formula_ids'=>isset($data['formula_ids'])&&is_array($data['formula_ids'])?array_values($data['formula_ids']):array(),'metadata'=>isset($data['metadata'])&&is_array($data['metadata'])?$data['metadata']:array());
        $record['record_hash']=hash('sha256',wp_json_encode($record,JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE));
        update_post_meta($post_id,self::RECORD_META,wp_json_encode($record,JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE)); update_post_meta($post_id,self::HASH_META,$record['record_hash']);
        return rest_ensure_response(array('ok'=>true,'wordpress_id'=>(int)$post_id,'record'=>$record));
    }

    public static function rest_save_draft($request) {
        $data = self::payload($request); $plan = isset($data['draftPlan'])&&is_array($data['draftPlan'])?$data['draftPlan']:$data;
        $status = isset($plan['visibility'])&&'private'===$plan['visibility']?'private':'draft';
        $title = sanitize_text_field(isset($plan['title'])?$plan['title']:'Workbench article draft');
        $content = isset($plan['contentMarkdown'])?wp_kses_post($plan['contentMarkdown']):'';
        $post_id = wp_insert_post(array('post_type'=>self::DRAFT_POST_TYPE,'post_status'=>$status,'post_title'=>$title,'post_content'=>$content,'post_author'=>get_current_user_id()),true);
        if (is_wp_error($post_id)) { return $post_id; }
        $plan['wordpress_id']=(int)$post_id; $plan['saved_at']=gmdate('c'); $plan['draftHash']=hash('sha256',wp_json_encode($plan,JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE));
        update_post_meta($post_id,self::RECORD_META,wp_json_encode($plan,JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE)); update_post_meta($post_id,self::HASH_META,$plan['draftHash']);
        return rest_ensure_response(array('ok'=>true,'wordpress_id'=>(int)$post_id,'status'=>$status,'draftPlan'=>$plan));
    }
}
SCWB_V320_Knowledge_Library_Integration::boot();
