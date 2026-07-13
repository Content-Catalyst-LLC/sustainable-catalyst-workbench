<?php
/** Workbench v4.0.0 — Connected Scientific and Engineering Workbench. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V400_Connected_Workbench {
    const VERSION = '4.0.0';
    const PROJECT_POST_TYPE = 'scwb_connected_prj';
    const WORKFLOW_POST_TYPE = 'scwb_workflow';
    const PROJECT_META = '_scwb_connected_project';
    const WORKFLOW_META = '_scwb_connected_workflow';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_records'), 7);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 40);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V400_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v400.css';
        $js = $base . '/assets/js/sc-workbench-v400.js';
        wp_register_style(
            'scwb-v400',
            plugins_url('assets/css/sc-workbench-v400.css', SCWB_V400_PLUGIN_FILE),
            array(),
            file_exists($css) ? (string) filemtime($css) : self::VERSION
        );
        wp_register_script(
            'scwb-v400',
            plugins_url('assets/js/sc-workbench-v400.js', SCWB_V400_PLUGIN_FILE),
            array(),
            file_exists($js) ? (string) filemtime($js) : self::VERSION,
            true
        );
    }

    public static function register_records() {
        $common = array(
            'public' => false,
            'show_ui' => true,
            'show_in_rest' => false,
            'exclude_from_search' => true,
            'supports' => array('title', 'author'),
            'map_meta_cap' => true,
            'capability_type' => 'post',
        );
        register_post_type(self::PROJECT_POST_TYPE, array_merge($common, array('labels' => array(
            'name' => __('Connected Workbench Projects', 'scwb'),
            'singular_name' => __('Connected Workbench Project', 'scwb'),
        ))));
        register_post_type(self::WORKFLOW_POST_TYPE, array_merge($common, array('labels' => array(
            'name' => __('Connected Workbench Workflows', 'scwb'),
            'singular_name' => __('Connected Workbench Workflow', 'scwb'),
        ))));
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_connected_environment' => 'workspace',
            'sc_workbench_connected_project' => 'project',
            'sc_workbench_connection_graph' => 'graph',
            'sc_workbench_workflow_orchestrator' => 'workflow',
            'sc_workbench_shared_context' => 'context',
            'sc_workbench_integration_health' => 'health',
            'sc_workbench_traceability_matrix' => 'traceability',
            'sc_workbench_connected_dossier' => 'dossier',
            'sc_workbench_connected_release' => 'release',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, function($atts) use ($panel) {
                    $atts = shortcode_atts(array(
                        'project' => 'default',
                        'display' => 'full',
                        'title' => 'Connected Scientific and Engineering Workbench',
                    ), $atts);
                    return SCWB_V400_Connected_Workbench::render($atts, $panel);
                });
            }
        }
    }

    public static function can_write() {
        return is_user_logged_in() && current_user_can('edit_posts');
    }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/connected-workbench-status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'status'),
            'permission_callback' => '__return_true',
        ));
        register_rest_route('scwb/v1', '/connected-integration-health', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'integration_health'),
            'permission_callback' => '__return_true',
        ));
        register_rest_route('scwb/v1', '/connected-projects', array(
            'methods' => array('GET', 'POST'),
            'callback' => array(__CLASS__, 'projects'),
            'permission_callback' => array(__CLASS__, 'can_write'),
        ));
        register_rest_route('scwb/v1', '/connected-workflows', array(
            'methods' => array('GET', 'POST'),
            'callback' => array(__CLASS__, 'workflows'),
            'permission_callback' => array(__CLASS__, 'can_write'),
        ));
        register_rest_route('scwb/v1', '/connected-manifests', array(
            'methods' => 'POST',
            'callback' => array(__CLASS__, 'save_manifest'),
            'permission_callback' => array(__CLASS__, 'can_write'),
        ));
    }

    public static function status() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-connected-environment-status/1.0',
            'version' => self::VERSION,
            'milestone' => 'Connected Scientific and Engineering Workbench',
            'studioCountTarget' => 22,
            'platforms' => array('workbench', 'sustainable-catalyst-lab', 'site-intelligence', 'decision-studio', 'research-librarian', 'knowledge-library'),
            'privateStorageAvailable' => self::can_write(),
            'offlineSupported' => true,
            'renderRequired' => false,
            'paidServiceRequired' => false,
            'humanControlRequired' => true,
            'automaticPublicationAuthorized' => false,
            'remoteShellAllowed' => false,
        ));
    }

    public static function integration_health() {
        $studios = class_exists('SCWB_V301_Production_Reliability')
            ? SCWB_V301_Production_Reliability::availability()
            : array();
        $missing = array_values(array_filter($studios, static function($item) {
            return empty($item['available']);
        }));
        return rest_ensure_response(array(
            'ok' => empty($missing),
            'schema' => 'sc-workbench-connected-integration-health/1.0',
            'version' => self::VERSION,
            'registeredStudios' => count($studios) - count($missing),
            'expectedStudios' => count($studios),
            'missingStudios' => $missing,
            'offlineFallbackAvailable' => true,
        ));
    }

    private static function request_record($request) {
        $record = method_exists($request, 'get_json_params') ? $request->get_json_params() : array();
        return is_array($record) ? $record : array();
    }

    private static function list_records($type, $meta) {
        $posts = get_posts(array(
            'post_type' => $type,
            'post_status' => 'private',
            'author' => get_current_user_id(),
            'numberposts' => 100,
            'orderby' => 'modified',
            'order' => 'DESC',
        ));
        $records = array();
        foreach ($posts as $post) {
            $records[] = array(
                'wordpressId' => $post->ID,
                'title' => $post->post_title,
                'record' => get_post_meta($post->ID, $meta, true),
            );
        }
        return rest_ensure_response(array('ok' => true, 'records' => $records));
    }

    private static function save_record($type, $meta, $request, $prefix) {
        $record = self::request_record($request);
        if (!$record) {
            return new WP_Error('scwb_empty_record', 'A record is required.', array('status' => 400));
        }
        $title = sanitize_text_field(isset($record['title']) ? $record['title'] : $prefix . ' ' . gmdate('Y-m-d H:i:s'));
        $id = wp_insert_post(array(
            'post_type' => $type,
            'post_status' => 'private',
            'post_title' => $title,
            'post_author' => get_current_user_id(),
        ), true);
        if (is_wp_error($id)) { return $id; }
        update_post_meta($id, $meta, $record);
        return rest_ensure_response(array('ok' => true, 'wordpressId' => $id, 'record' => $record));
    }

    public static function projects($request) {
        return 'GET' === $request->get_method()
            ? self::list_records(self::PROJECT_POST_TYPE, self::PROJECT_META)
            : self::save_record(self::PROJECT_POST_TYPE, self::PROJECT_META, $request, 'Connected project');
    }

    public static function workflows($request) {
        return 'GET' === $request->get_method()
            ? self::list_records(self::WORKFLOW_POST_TYPE, self::WORKFLOW_META)
            : self::save_record(self::WORKFLOW_POST_TYPE, self::WORKFLOW_META, $request, 'Connected workflow');
    }

    public static function save_manifest($request) {
        return self::save_record(self::PROJECT_POST_TYPE, self::PROJECT_META, $request, 'Connected release manifest');
    }

    private static function card($title, $text, $action, $button) {
        ?>
        <article class="scwb-v400__card">
            <h4><?php echo esc_html($title); ?></h4>
            <p><?php echo esc_html($text); ?></p>
            <button type="button" data-scwb-v400-action="<?php echo esc_attr($action); ?>"><?php echo esc_html($button); ?></button>
        </article>
        <?php
    }

    public static function render($atts, $panel = 'workspace') {
        self::register_assets();
        wp_enqueue_style('scwb-v400');
        wp_enqueue_script('scwb-v400');
        wp_localize_script('scwb-v400', 'SCWBV400Config', array(
            'version' => self::VERSION,
            'restUrl' => esc_url_raw(rest_url('scwb/v1')),
            'backendUrl' => '',
            'nonce' => wp_create_nonce('wp_rest'),
            'authenticated' => self::can_write(),
        ));
        $project = sanitize_key($atts['project']) ?: 'default';
        $display = sanitize_key($atts['display']) ?: 'full';
        $tabs = array(
            'workspace' => 'Connected Overview',
            'project' => 'Project Contract',
            'graph' => 'Connection Graph',
            'workflow' => 'Workflow',
            'context' => 'Shared Context',
            'health' => 'Integration Health',
            'traceability' => 'Traceability',
            'dossier' => 'Dossier',
            'release' => 'Release Manifest',
        );
        $instance = 'scwb-v400-' . wp_generate_uuid4();
        ob_start();
        ?>
        <section
            id="<?php echo esc_attr($instance); ?>"
            class="scwb-v400 scwb-v400--<?php echo esc_attr($display); ?>"
            data-scwb-v400
            data-scwb-v400-panel="<?php echo esc_attr($panel); ?>"
            data-scwb-v400-project="<?php echo esc_attr($project); ?>"
            data-scwb-v400-version="4.0.0"
        >
            <header class="scwb-v400__header">
                <div>
                    <p class="scwb-v400__eyebrow">Sustainable Catalyst Workbench · v4.0.0</p>
                    <h3><?php echo esc_html($atts['title']); ?></h3>
                    <p>Connect calculations, code, simulations, instruments, experiments, evidence, reviews, domain laboratories, public intelligence, decision workflows, research guidance, documentation, and offline projects under one auditable project contract.</p>
                </div>
                <span class="scwb-v400__status" data-scwb-v400-status>Local-first · human-controlled</span>
            </header>

            <div class="scwb-v400__tabs" role="tablist" aria-label="Connected Workbench panels">
                <?php foreach ($tabs as $key => $label) : ?>
                    <button type="button" role="tab" data-scwb-v400-tab="<?php echo esc_attr($key); ?>" aria-selected="<?php echo $key === $panel ? 'true' : 'false'; ?>" class="<?php echo $key === $panel ? 'is-active' : ''; ?>"><?php echo esc_html($label); ?></button>
                <?php endforeach; ?>
            </div>

            <div class="scwb-v400__panels">
                <?php foreach ($tabs as $key => $label) : ?>
                    <section class="scwb-v400__panel<?php echo $key === $panel ? ' is-active' : ''; ?>" data-scwb-v400-panel-view="<?php echo esc_attr($key); ?>" <?php echo $key === $panel ? '' : 'hidden'; ?>>
                        <h4><?php echo esc_html($label); ?></h4>
                        <?php if ('workspace' === $key) : ?>
                            <div class="scwb-v400__grid">
                                <?php self::card('Connected project', 'Create one canonical project contract across every Workbench and Sustainable Catalyst surface.', 'project', 'Build project contract'); ?>
                                <?php self::card('Capability registry', 'Audit studios, runtimes, domains, services, and required capabilities before a workflow begins.', 'registry', 'Build capability registry'); ?>
                                <?php self::card('Integration health', 'Check required and optional platform connections while preserving offline fallback.', 'health', 'Audit integrations'); ?>
                                <?php self::card('Release manifest', 'Assemble traceability, evaluation, review, and human-approval evidence without publishing automatically.', 'release', 'Build release manifest'); ?>
                            </div>
                        <?php else : ?>
                            <div class="scwb-v400__workspace" data-scwb-v400-workspace="<?php echo esc_attr($key); ?>">
                                <label><span>Project ID</span><input type="text" data-scwb-v400-field="projectId" value="<?php echo esc_attr($project); ?>"></label>
                                <label><span>Project title</span><input type="text" data-scwb-v400-field="title" value="Connected Workbench Project"></label>
                                <label class="scwb-v400__wide"><span>Objective or notes</span><textarea data-scwb-v400-field="notes" rows="5"></textarea></label>
                                <div class="scwb-v400__actions">
                                    <button type="button" data-scwb-v400-action="<?php echo esc_attr($key); ?>">Build <?php echo esc_html(strtolower($label)); ?></button>
                                    <button type="button" class="is-secondary" data-scwb-v400-action="export">Export local record</button>
                                </div>
                            </div>
                        <?php endif; ?>
                    </section>
                <?php endforeach; ?>
            </div>

            <section class="scwb-v400__output" aria-live="polite">
                <div><strong>Connected record</strong><span data-scwb-v400-mode>Browser-local fallback active</span></div>
                <pre data-scwb-v400-output>{}</pre>
            </section>
        </section>
        <?php
        return ob_get_clean();
    }
}

SCWB_V400_Connected_Workbench::boot();
