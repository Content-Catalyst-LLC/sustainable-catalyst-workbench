<?php
/**
 * Workbench v3.1.0 — Persistent Project Workspace.
 *
 * Browser-local persistence remains available to every visitor. Authenticated
 * users with edit_posts capability can optionally store private projects and
 * revision snapshots in WordPress.
 */
if (!defined('ABSPATH')) {
    exit;
}

final class SCWB_V310_Persistent_Project_Workspace {
    const VERSION = '3.1.0';
    const PROJECT_POST_TYPE = 'scwb_project';
    const REVISION_POST_TYPE = 'scwb_revision';
    const PROJECT_META = '_scwb_project_json';
    const HASH_META = '_scwb_project_hash';
    const REVISION_META = '_scwb_project_revision';
    const UPDATED_META = '_scwb_project_updated';
    const MAX_REVISIONS = 100;

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 6);
        add_action('init', array(__CLASS__, 'register_post_types'), 7);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 1002);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = defined('SCWB_V310_PLUGIN_FILE') ? SCWB_V310_PLUGIN_FILE : dirname(__DIR__) . '/sustainable-catalyst-workbench.php';
        $directory = dirname($base);
        $css = $directory . '/assets/css/sc-workbench-v310.css';
        $js = $directory . '/assets/js/sc-workbench-v310.js';

        wp_register_style(
            'scwb-v310',
            plugins_url('assets/css/sc-workbench-v310.css', $base),
            array('scwb-primary-repair'),
            file_exists($css) ? (string) filemtime($css) : self::VERSION
        );
        wp_register_script(
            'scwb-v310',
            plugins_url('assets/js/sc-workbench-v310.js', $base),
            array('scwb-primary-repair'),
            file_exists($js) ? (string) filemtime($js) : self::VERSION,
            true
        );
    }

    public static function register_post_types() {
        if (!function_exists('register_post_type')) {
            return;
        }

        register_post_type(self::PROJECT_POST_TYPE, array(
            'labels' => array(
                'name' => 'Workbench Projects',
                'singular_name' => 'Workbench Project',
                'add_new_item' => 'Add Workbench Project',
                'edit_item' => 'Edit Workbench Project',
            ),
            'public' => false,
            'show_ui' => true,
            'show_in_menu' => 'tools.php',
            'show_in_rest' => false,
            'supports' => array('title', 'author'),
            'capability_type' => 'post',
            'map_meta_cap' => true,
        ));

        register_post_type(self::REVISION_POST_TYPE, array(
            'labels' => array(
                'name' => 'Workbench Revisions',
                'singular_name' => 'Workbench Revision',
            ),
            'public' => false,
            'show_ui' => false,
            'show_in_rest' => false,
            'supports' => array('title', 'author'),
            'capability_type' => 'post',
            'map_meta_cap' => true,
        ));
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_persistent_workspace' => 'workspace',
            'sc_workbench_project_manager' => 'projects',
            'sc_workbench_project_switcher' => 'projects',
            'sc_workbench_project_revisions' => 'revisions',
            'sc_workbench_project_storage' => 'storage',
            'sc_workbench_project_autosave' => 'editor',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, static function($atts = array()) use ($panel) {
                    return SCWB_V310_Persistent_Project_Workspace::render($panel, $atts);
                });
            }
        }
    }

    private static function can_persist() {
        return function_exists('is_user_logged_in')
            && is_user_logged_in()
            && function_exists('current_user_can')
            && current_user_can('edit_posts');
    }

    private static function enqueue_assets() {
        self::register_assets();
        wp_enqueue_style('scwb-v310');
        wp_enqueue_script('scwb-v310');

        if (function_exists('wp_localize_script')) {
            wp_localize_script('scwb-v310', 'SCWBV310Config', array(
                'version' => self::VERSION,
                'restUrl' => function_exists('rest_url') ? esc_url_raw(rest_url('scwb/v1')) : '/wp-json/scwb/v1',
                'nonce' => function_exists('wp_create_nonce') ? wp_create_nonce('wp_rest') : '',
                'authenticated' => self::can_persist(),
                'currentUser' => function_exists('get_current_user_id') ? (int) get_current_user_id() : 0,
                'autosaveDelay' => 1800,
                'maxLocalRevisions' => 50,
            ));
        }
    }

    public static function render($panel = 'workspace', $atts = array()) {
        self::enqueue_assets();
        $atts = shortcode_atts(array(
            'project' => 'default',
            'title' => 'Persistent Project Workspace',
            'display' => 'full',
        ), $atts, 'sc_workbench_persistent_workspace');

        $project = sanitize_key($atts['project']) ?: 'default';
        $display = sanitize_key($atts['display']);
        if (!in_array($display, array('inline', 'compact', 'full', 'drawer'), true)) {
            $display = 'full';
        }
        $allowed_panels = array('workspace', 'projects', 'editor', 'revisions', 'storage', 'sync');
        if (!in_array($panel, $allowed_panels, true)) {
            $panel = 'workspace';
        }
        $instance = 'scwb-v310-' . wp_generate_uuid4();
        $server_enabled = self::can_persist();

        ob_start();
        ?>
        <section
            id="<?php echo esc_attr($instance); ?>"
            class="scwb-v310 scwb-v310--<?php echo esc_attr($display); ?>"
            data-scwb-v310
            data-scwb-v310-project="<?php echo esc_attr($project); ?>"
            data-scwb-v310-panel="<?php echo esc_attr($panel); ?>"
            data-scwb-v310-version="3.1.0"
            data-scwb-v310-server="<?php echo $server_enabled ? 'enabled' : 'browser-only'; ?>"
        >
            <header class="scwb-v310__header">
                <div>
                    <p class="scwb-v310__eyebrow">Sustainable Catalyst Workbench · v3.1.0</p>
                    <h2><?php echo esc_html($atts['title']); ?></h2>
                    <p>Create, switch, autosave, version, export, and optionally synchronize private Workbench projects while retaining a browser-local fallback.</p>
                </div>
                <span class="scwb-v310__status" data-scwb-v310-status aria-live="polite">
                    <?php echo $server_enabled ? 'Browser + private WordPress storage' : 'Browser-local storage'; ?>
                </span>
            </header>

            <div class="scwb-v310__toolbar">
                <label class="scwb-v310__project-select"><span>Active project</span><select data-scwb-v310-project-select><option value="">Loading projects…</option></select></label>
                <button type="button" class="scwb-v310__button scwb-v310__button--primary" data-scwb-v310-action="new-project">New project</button>
                <button type="button" class="scwb-v310__button" data-scwb-v310-action="save-project">Save now</button>
                <button type="button" class="scwb-v310__button" data-scwb-v310-action="snapshot">Create revision</button>
                <button type="button" class="scwb-v310__button" data-scwb-v310-action="export-project">Export</button>
            </div>

            <nav class="scwb-v310__nav" aria-label="Persistent project tools" role="tablist">
                <?php
                $tabs = array(
                    'workspace' => 'Workspace',
                    'projects' => 'Projects',
                    'editor' => 'Project record',
                    'revisions' => 'Revisions',
                    'storage' => 'Storage',
                    'sync' => 'Synchronization',
                );
                foreach ($tabs as $key => $label) :
                    $active = $key === $panel || ('workspace' === $panel && 'workspace' === $key);
                ?>
                    <button type="button" class="scwb-v310__tab<?php echo $active ? ' is-active' : ''; ?>" role="tab" aria-selected="<?php echo $active ? 'true' : 'false'; ?>" data-scwb-v310-tab="<?php echo esc_attr($key); ?>"><?php echo esc_html($label); ?></button>
                <?php endforeach; ?>
            </nav>

            <div class="scwb-v310__body">
                <section class="scwb-v310__panel<?php echo 'workspace' === $panel ? ' is-active' : ''; ?>" data-scwb-v310-view="workspace">
                    <div class="scwb-v310__cards">
                        <article><strong>Local first</strong><span>Projects save in this browser even when no account or backend is available.</span></article>
                        <article><strong>Private persistence</strong><span>Signed-in editors can store private project records and revisions in WordPress.</span></article>
                        <article><strong>Autosave</strong><span>Dirty project records save after an idle delay and before page exit.</span></article>
                        <article><strong>Revision safety</strong><span>Manual and server saves create recoverable, content-hashed snapshots.</span></article>
                    </div>
                    <div class="scwb-v310__project-summary" data-scwb-v310-project-summary>No active project loaded.</div>
                    <div class="scwb-v310__recent" data-scwb-v310-recent></div>
                </section>

                <section class="scwb-v310__panel<?php echo 'projects' === $panel ? ' is-active' : ''; ?>" data-scwb-v310-view="projects">
                    <div class="scwb-v310__filters">
                        <label><span>Search projects</span><input type="search" data-scwb-v310-filter="search" placeholder="Title, tag, or status"></label>
                        <label><span>Status</span><select data-scwb-v310-filter="status"><option value="">All statuses</option><option>draft</option><option>active</option><option>review</option><option>complete</option><option>archived</option></select></label>
                        <label class="scwb-v310__check"><input type="checkbox" data-scwb-v310-filter="pinned"> Pinned only</label>
                    </div>
                    <div class="scwb-v310__project-list" data-scwb-v310-project-list></div>
                </section>

                <section class="scwb-v310__panel<?php echo 'editor' === $panel ? ' is-active' : ''; ?>" data-scwb-v310-view="editor">
                    <div class="scwb-v310__form-grid">
                        <?php self::field('Project ID', 'project_id', 'text', $project); ?>
                        <?php self::field('Title', 'title', 'text', 'Untitled Workbench project'); ?>
                        <?php self::field('Status', 'status', 'select', 'draft', array('draft','active','review','complete','archived')); ?>
                        <?php self::field('Storage mode', 'storage_mode', 'select', $server_enabled ? 'hybrid' : 'browser', array('browser','hybrid','wordpress')); ?>
                        <?php self::field('Tags, comma separated', 'tags', 'text', ''); ?>
                        <label class="scwb-v310__check"><input type="checkbox" data-scwb-v310-field="pinned"> Pin this project</label>
                        <?php self::field('Description', 'description', 'textarea', '', array(), true); ?>
                        <?php self::field('Project metadata and shared studio state (JSON)', 'project_json', 'textarea', '{"active_studio":"unified","studio_records":{},"evidence_ids":[],"artifact_ids":[],"metadata":{}}', array(), true); ?>
                    </div>
                    <div class="scwb-v310__save-state" data-scwb-v310-save-state>Not modified.</div>
                </section>

                <section class="scwb-v310__panel<?php echo 'revisions' === $panel ? ' is-active' : ''; ?>" data-scwb-v310-view="revisions">
                    <div class="scwb-v310__revision-controls">
                        <label><span>Revision reason</span><input type="text" data-scwb-v310-field="revision_reason" value="manual-save"></label>
                        <button type="button" class="scwb-v310__button scwb-v310__button--primary" data-scwb-v310-action="snapshot">Create revision</button>
                    </div>
                    <div class="scwb-v310__revision-list" data-scwb-v310-revision-list></div>
                </section>

                <section class="scwb-v310__panel<?php echo 'storage' === $panel ? ' is-active' : ''; ?>" data-scwb-v310-view="storage">
                    <div class="scwb-v310__storage-grid">
                        <article><strong>Browser records</strong><span data-scwb-v310-stat="local-projects">0</span></article>
                        <article><strong>Local revisions</strong><span data-scwb-v310-stat="local-revisions">0</span></article>
                        <article><strong>Estimated usage</strong><span data-scwb-v310-stat="bytes">0 B</span></article>
                        <article><strong>Server access</strong><span data-scwb-v310-stat="server"><?php echo $server_enabled ? 'Available' : 'Sign in to enable'; ?></span></article>
                    </div>
                    <div class="scwb-v310__actions">
                        <button type="button" class="scwb-v310__button" data-scwb-v310-action="import-project">Import project</button>
                        <input type="file" accept="application/json,.json" hidden data-scwb-v310-import>
                        <button type="button" class="scwb-v310__button" data-scwb-v310-action="prune-revisions">Prune old local revisions</button>
                        <button type="button" class="scwb-v310__button" data-scwb-v310-action="open-recovery">Open migration & recovery</button>
                    </div>
                </section>

                <section class="scwb-v310__panel<?php echo 'sync' === $panel ? ' is-active' : ''; ?>" data-scwb-v310-view="sync">
                    <p class="scwb-v310__sync-note"><?php echo $server_enabled ? 'Private WordPress synchronization is available for this signed-in account.' : 'This session is using browser-local storage. Sign in with editing access to enable private WordPress synchronization.'; ?></p>
                    <label class="scwb-v310__field"><span>Conflict strategy</span><select data-scwb-v310-field="sync_strategy"><option value="newest">Use newest revision</option><option value="local">Keep browser copy</option><option value="remote">Keep WordPress copy</option><option value="manual">Require manual review</option></select></label>
                    <div class="scwb-v310__actions">
                        <button type="button" class="scwb-v310__button" data-scwb-v310-action="refresh-server" <?php disabled(!$server_enabled); ?>>Refresh server projects</button>
                        <button type="button" class="scwb-v310__button scwb-v310__button--primary" data-scwb-v310-action="sync-project" <?php disabled(!$server_enabled); ?>>Synchronize active project</button>
                    </div>
                    <pre class="scwb-v310__sync-result" data-scwb-v310-sync-result>{}</pre>
                </section>
            </div>

            <div class="scwb-v310__notice" data-scwb-v310-notice aria-live="polite">Persistent workspace ready.</div>
            <p class="scwb-v310__boundary"><strong>Storage boundary:</strong> browser projects remain tied to the current browser profile unless exported or synchronized. WordPress projects are private application records, not certified records of engineering approval. Export backups before account changes, cleanup, migration, or reset.</p>
        </section>
        <?php
        return ob_get_clean();
    }

    private static function field($label, $name, $type = 'text', $value = '', $options = array(), $wide = false) {
        ?>
        <label class="scwb-v310__field<?php echo $wide ? ' scwb-v310__field--wide' : ''; ?>">
            <span><?php echo esc_html($label); ?></span>
            <?php if ('textarea' === $type) : ?>
                <textarea data-scwb-v310-field="<?php echo esc_attr($name); ?>"><?php echo esc_textarea($value); ?></textarea>
            <?php elseif ('select' === $type) : ?>
                <select data-scwb-v310-field="<?php echo esc_attr($name); ?>">
                    <?php foreach ($options as $option) : ?>
                        <option value="<?php echo esc_attr($option); ?>" <?php selected($option, $value); ?>><?php echo esc_html($option); ?></option>
                    <?php endforeach; ?>
                </select>
            <?php else : ?>
                <input type="<?php echo esc_attr($type); ?>" value="<?php echo esc_attr($value); ?>" data-scwb-v310-field="<?php echo esc_attr($name); ?>">
            <?php endif; ?>
        </label>
        <?php
    }

    public static function register_rest_routes() {
        if (!function_exists('register_rest_route')) {
            return;
        }

        register_rest_route('scwb/v1', '/persistent-status', array(
            'methods' => 'GET',
            'permission_callback' => '__return_true',
            'callback' => array(__CLASS__, 'rest_status'),
        ));
        register_rest_route('scwb/v1', '/projects', array(
            array('methods' => 'GET', 'permission_callback' => array(__CLASS__, 'rest_permission'), 'callback' => array(__CLASS__, 'rest_list_projects')),
            array('methods' => 'POST', 'permission_callback' => array(__CLASS__, 'rest_permission'), 'callback' => array(__CLASS__, 'rest_create_project')),
        ));
        register_rest_route('scwb/v1', '/projects/(?P<id>\d+)', array(
            array('methods' => 'GET', 'permission_callback' => array(__CLASS__, 'rest_project_permission'), 'callback' => array(__CLASS__, 'rest_get_project')),
            array('methods' => array('PUT','PATCH'), 'permission_callback' => array(__CLASS__, 'rest_project_permission'), 'callback' => array(__CLASS__, 'rest_update_project')),
            array('methods' => 'DELETE', 'permission_callback' => array(__CLASS__, 'rest_project_permission'), 'callback' => array(__CLASS__, 'rest_delete_project')),
        ));
        register_rest_route('scwb/v1', '/projects/(?P<id>\d+)/revisions', array(
            array('methods' => 'GET', 'permission_callback' => array(__CLASS__, 'rest_project_permission'), 'callback' => array(__CLASS__, 'rest_list_revisions')),
            array('methods' => 'POST', 'permission_callback' => array(__CLASS__, 'rest_project_permission'), 'callback' => array(__CLASS__, 'rest_create_revision')),
        ));
    }

    public static function rest_permission() {
        return self::can_persist();
    }

    public static function rest_project_permission($request) {
        if (!self::can_persist()) {
            return false;
        }
        $id = absint($request['id']);
        $post = get_post($id);
        if (!$post || self::PROJECT_POST_TYPE !== $post->post_type) {
            return false;
        }
        $user_id = get_current_user_id();
        return (int) $post->post_author === (int) $user_id || current_user_can('edit_others_posts');
    }

    public static function rest_status() {
        return rest_ensure_response(array(
            'ok' => true,
            'version' => self::VERSION,
            'authenticated' => self::can_persist(),
            'storage' => self::can_persist() ? 'browser+wordpress' : 'browser',
            'projectPostType' => self::PROJECT_POST_TYPE,
            'revisionPostType' => self::REVISION_POST_TYPE,
        ));
    }

    private static function request_payload($request) {
        $payload = method_exists($request, 'get_json_params') ? $request->get_json_params() : array();
        return is_array($payload) ? $payload : array();
    }

    private static function normalize_payload($payload, $post_id = 0) {
        $now = gmdate('c');
        $project_id = sanitize_key(isset($payload['project_id']) ? $payload['project_id'] : 'project-' . ($post_id ?: wp_generate_uuid4()));
        $title = sanitize_text_field(isset($payload['title']) ? $payload['title'] : 'Untitled Workbench project');
        $status = sanitize_key(isset($payload['status']) ? $payload['status'] : 'draft');
        if (!in_array($status, array('draft','active','review','complete','archived'), true)) {
            $status = 'draft';
        }
        $storage = sanitize_key(isset($payload['storage_mode']) ? $payload['storage_mode'] : 'hybrid');
        if (!in_array($storage, array('browser','hybrid','wordpress'), true)) {
            $storage = 'hybrid';
        }
        $record = array(
            'schema' => 'sc-workbench-persistent-project/1.0',
            'project_id' => $project_id ?: 'project-' . ($post_id ?: time()),
            'wordpress_id' => (int) $post_id,
            'title' => $title ?: 'Untitled Workbench project',
            'description' => sanitize_textarea_field(isset($payload['description']) ? $payload['description'] : ''),
            'status' => $status,
            'owner_id' => (string) get_current_user_id(),
            'storage_mode' => $storage,
            'tags' => array_values(array_unique(array_filter(array_map('sanitize_text_field', isset($payload['tags']) && is_array($payload['tags']) ? $payload['tags'] : array())))),
            'pinned' => !empty($payload['pinned']),
            'created_at' => sanitize_text_field(isset($payload['created_at']) ? $payload['created_at'] : $now),
            'updated_at' => $now,
            'local_revision' => max(0, absint(isset($payload['local_revision']) ? $payload['local_revision'] : 0)),
            'server_revision' => max(0, absint(isset($payload['server_revision']) ? $payload['server_revision'] : 0)),
            'active_studio' => sanitize_key(isset($payload['active_studio']) ? $payload['active_studio'] : 'unified'),
            'studio_records' => isset($payload['studio_records']) && is_array($payload['studio_records']) ? $payload['studio_records'] : array(),
            'evidence_ids' => isset($payload['evidence_ids']) && is_array($payload['evidence_ids']) ? array_values($payload['evidence_ids']) : array(),
            'artifact_ids' => isset($payload['artifact_ids']) && is_array($payload['artifact_ids']) ? array_values($payload['artifact_ids']) : array(),
            'metadata' => isset($payload['metadata']) && is_array($payload['metadata']) ? $payload['metadata'] : array(),
        );
        $record['server_revision']++;
        $record['content_hash'] = hash('sha256', wp_json_encode($record, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));
        return $record;
    }

    private static function project_response($post) {
        $json = get_post_meta($post->ID, self::PROJECT_META, true);
        $data = json_decode((string) $json, true);
        if (!is_array($data)) {
            $data = array();
        }
        $data['wordpress_id'] = (int) $post->ID;
        $data['title'] = isset($data['title']) ? $data['title'] : $post->post_title;
        return $data;
    }

    public static function rest_list_projects($request) {
        $query = new WP_Query(array(
            'post_type' => self::PROJECT_POST_TYPE,
            'post_status' => 'private',
            'author' => get_current_user_id(),
            'posts_per_page' => 200,
            'orderby' => 'modified',
            'order' => 'DESC',
            'no_found_rows' => true,
        ));
        $projects = array_map(array(__CLASS__, 'project_response'), $query->posts);
        return rest_ensure_response(array('ok' => true, 'version' => self::VERSION, 'projects' => $projects, 'count' => count($projects)));
    }

    public static function rest_create_project($request) {
        $payload = self::request_payload($request);
        $post_id = wp_insert_post(array(
            'post_type' => self::PROJECT_POST_TYPE,
            'post_status' => 'private',
            'post_title' => sanitize_text_field(isset($payload['title']) ? $payload['title'] : 'Untitled Workbench project'),
            'post_author' => get_current_user_id(),
        ), true);
        if (is_wp_error($post_id)) {
            return $post_id;
        }
        $record = self::normalize_payload($payload, $post_id);
        self::store_project($post_id, $record);
        self::create_revision_post($post_id, $record, 'project-created');
        return rest_ensure_response(array('ok' => true, 'project' => $record));
    }

    public static function rest_get_project($request) {
        return rest_ensure_response(array('ok' => true, 'project' => self::project_response(get_post(absint($request['id'])))));
    }

    public static function rest_update_project($request) {
        $id = absint($request['id']);
        $payload = self::request_payload($request);
        $record = self::normalize_payload($payload, $id);
        wp_update_post(array('ID' => $id, 'post_title' => $record['title']));
        self::store_project($id, $record);
        $reason = sanitize_text_field(isset($payload['revision_reason']) ? $payload['revision_reason'] : 'server-save');
        self::create_revision_post($id, $record, $reason ?: 'server-save');
        return rest_ensure_response(array('ok' => true, 'project' => $record));
    }

    public static function rest_delete_project($request) {
        $id = absint($request['id']);
        $revisions = get_posts(array('post_type' => self::REVISION_POST_TYPE, 'post_parent' => $id, 'post_status' => 'private', 'posts_per_page' => -1, 'fields' => 'ids'));
        foreach ($revisions as $revision_id) {
            wp_delete_post($revision_id, true);
        }
        wp_delete_post($id, true);
        return rest_ensure_response(array('ok' => true, 'deleted' => $id));
    }

    public static function rest_list_revisions($request) {
        $id = absint($request['id']);
        $posts = get_posts(array(
            'post_type' => self::REVISION_POST_TYPE,
            'post_parent' => $id,
            'post_status' => 'private',
            'posts_per_page' => self::MAX_REVISIONS,
            'orderby' => 'date',
            'order' => 'DESC',
        ));
        $revisions = array();
        foreach ($posts as $post) {
            $data = json_decode((string) get_post_meta($post->ID, self::PROJECT_META, true), true);
            if (is_array($data)) {
                $data['wordpress_revision_id'] = (int) $post->ID;
                $revisions[] = $data;
            }
        }
        return rest_ensure_response(array('ok' => true, 'revisions' => $revisions, 'count' => count($revisions)));
    }

    public static function rest_create_revision($request) {
        $id = absint($request['id']);
        $payload = self::request_payload($request);
        $record = isset($payload['project']) && is_array($payload['project']) ? self::normalize_payload($payload['project'], $id) : self::project_response(get_post($id));
        $reason = sanitize_text_field(isset($payload['reason']) ? $payload['reason'] : 'manual-snapshot');
        $revision_id = self::create_revision_post($id, $record, $reason ?: 'manual-snapshot');
        return rest_ensure_response(array('ok' => true, 'revisionId' => $revision_id, 'project' => $record));
    }

    private static function store_project($post_id, $record) {
        update_post_meta($post_id, self::PROJECT_META, wp_json_encode($record, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));
        update_post_meta($post_id, self::HASH_META, $record['content_hash']);
        update_post_meta($post_id, self::REVISION_META, $record['server_revision']);
        update_post_meta($post_id, self::UPDATED_META, $record['updated_at']);
    }

    private static function create_revision_post($project_id, $record, $reason) {
        $revision_number = max((int) get_post_meta($project_id, self::REVISION_META, true), (int) $record['server_revision']);
        $snapshot = array(
            'schema' => 'sc-workbench-project-revision/1.0',
            'version' => self::VERSION,
            'project_id' => $record['project_id'],
            'revision' => $revision_number,
            'reason' => $reason,
            'created_at' => gmdate('c'),
            'project_hash' => $record['content_hash'],
            'snapshot' => $record,
        );
        $snapshot['revision_hash'] = hash('sha256', wp_json_encode($snapshot, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));
        $revision_id = wp_insert_post(array(
            'post_type' => self::REVISION_POST_TYPE,
            'post_status' => 'private',
            'post_title' => sprintf('%s · r%d · %s', $record['title'], $revision_number, $reason),
            'post_parent' => $project_id,
            'post_author' => get_current_user_id(),
        ));
        if ($revision_id && !is_wp_error($revision_id)) {
            update_post_meta($revision_id, self::PROJECT_META, wp_json_encode($snapshot, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));
            self::prune_server_revisions($project_id);
        }
        return $revision_id;
    }

    private static function prune_server_revisions($project_id) {
        $ids = get_posts(array(
            'post_type' => self::REVISION_POST_TYPE,
            'post_parent' => $project_id,
            'post_status' => 'private',
            'posts_per_page' => -1,
            'orderby' => 'date',
            'order' => 'DESC',
            'fields' => 'ids',
        ));
        foreach (array_slice($ids, self::MAX_REVISIONS) as $revision_id) {
            wp_delete_post($revision_id, true);
        }
    }
}

SCWB_V310_Persistent_Project_Workspace::boot();
