<?php
/** Workbench v3.8.0 — Offline and Installable Workbench. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V380_Offline_Installable_Workbench {
    const VERSION = '3.8.0';
    const NODE_POST_TYPE = 'scwb_offline_node';
    const BUNDLE_POST_TYPE = 'scwb_sync_bundle';
    const NODE_META = '_scwb_offline_node_record';
    const BUNDLE_META = '_scwb_sync_bundle_record';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_records'), 7);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 40);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V380_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v380.css';
        $js = $base . '/assets/js/sc-workbench-v380.js';
        wp_register_style(
            'scwb-v380',
            plugins_url('assets/css/sc-workbench-v380.css', SCWB_V380_PLUGIN_FILE),
            array(),
            file_exists($css) ? (string) filemtime($css) : self::VERSION
        );
        wp_register_script(
            'scwb-v380',
            plugins_url('assets/js/sc-workbench-v380.js', SCWB_V380_PLUGIN_FILE),
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
        register_post_type(self::NODE_POST_TYPE, array_merge($common, array(
            'labels' => array(
                'name' => __('Workbench Offline Nodes', 'scwb'),
                'singular_name' => __('Workbench Offline Node', 'scwb'),
            ),
        )));
        register_post_type(self::BUNDLE_POST_TYPE, array_merge($common, array(
            'labels' => array(
                'name' => __('Workbench Sync Bundles', 'scwb'),
                'singular_name' => __('Workbench Sync Bundle', 'scwb'),
            ),
        )));
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_offline_installable' => 'workspace',
            'sc_workbench_offline_status' => 'status',
            'sc_workbench_installer_builder' => 'installers',
            'sc_workbench_local_service' => 'service',
            'sc_workbench_offline_storage' => 'storage',
            'sc_workbench_runner_manager' => 'runtimes',
            'sc_workbench_offline_sync' => 'sync',
            'sc_workbench_update_recovery' => 'recovery',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, function($atts) use ($panel) {
                    $atts = shortcode_atts(array(
                        'project' => 'default',
                        'platform' => 'macos',
                        'display' => 'full',
                        'title' => 'Offline and Installable Workbench',
                    ), $atts);
                    return SCWB_V380_Offline_Installable_Workbench::render($atts, $panel);
                });
            }
        }
    }

    public static function can_write() {
        return is_user_logged_in() && current_user_can('edit_posts');
    }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/offline-installable-status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'status'),
            'permission_callback' => '__return_true',
        ));
        register_rest_route('scwb/v1', '/offline-nodes', array(
            'methods' => array('GET', 'POST'),
            'callback' => array(__CLASS__, 'nodes'),
            'permission_callback' => array(__CLASS__, 'can_write'),
        ));
        register_rest_route('scwb/v1', '/offline-sync-bundles', array(
            'methods' => array('GET', 'POST'),
            'callback' => array(__CLASS__, 'bundles'),
            'permission_callback' => array(__CLASS__, 'can_write'),
        ));
        register_rest_route('scwb/v1', '/offline-install-plans', array(
            'methods' => 'POST',
            'callback' => array(__CLASS__, 'save_install_plan'),
            'permission_callback' => array(__CLASS__, 'can_write'),
        ));
        register_rest_route('scwb/v1', '/offline-service-records', array(
            'methods' => 'POST',
            'callback' => array(__CLASS__, 'save_service_record'),
            'permission_callback' => array(__CLASS__, 'can_write'),
        ));
        register_rest_route('scwb/v1', '/offline-update-plans', array(
            'methods' => 'POST',
            'callback' => array(__CLASS__, 'save_update_plan'),
            'permission_callback' => array(__CLASS__, 'can_write'),
        ));
    }

    public static function status() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-offline-installable-status/1.0',
            'version' => self::VERSION,
            'platforms' => array('macos', 'linux', 'raspberry-pi'),
            'localServiceHost' => '127.0.0.1',
            'defaultPort' => 8787,
            'privateStorageAvailable' => self::can_write(),
            'renderRequired' => false,
            'paidServiceRequired' => false,
            'remoteShell' => false,
            'automaticCloudUpload' => false,
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

    private static function save_record($request, $type, $meta, $fallback) {
        if ('GET' === $request->get_method()) {
            return self::list_records($type, $meta);
        }
        $record = self::request_record($request);
        $title = sanitize_text_field(isset($record['title']) ? $record['title'] : $fallback);
        $post_id = wp_insert_post(array(
            'post_type' => $type,
            'post_status' => 'private',
            'post_title' => $title,
            'post_author' => get_current_user_id(),
        ), true);
        if (is_wp_error($post_id)) { return $post_id; }
        update_post_meta($post_id, $meta, $record);
        return rest_ensure_response(array('ok' => true, 'wordpressId' => $post_id, 'record' => $record));
    }

    public static function nodes($request) {
        return self::save_record($request, self::NODE_POST_TYPE, self::NODE_META, 'Offline Workbench node');
    }

    public static function bundles($request) {
        return self::save_record($request, self::BUNDLE_POST_TYPE, self::BUNDLE_META, 'Offline synchronization bundle');
    }

    public static function save_install_plan($request) {
        return self::save_record($request, self::NODE_POST_TYPE, self::NODE_META, 'Offline installation plan');
    }

    public static function save_service_record($request) {
        return self::save_record($request, self::NODE_POST_TYPE, self::NODE_META, 'Local service record');
    }

    public static function save_update_plan($request) {
        return self::save_record($request, self::BUNDLE_POST_TYPE, self::BUNDLE_META, 'Offline update plan');
    }

    private static function platform_options() {
        return array(
            'macos' => 'macOS',
            'linux' => 'Linux',
            'raspberry-pi' => 'Raspberry Pi OS',
        );
    }

    private static function field($label, $name, $type = 'text', $value = '', $wide = false) { ?>
        <label class="scwb-v380__field<?php echo $wide ? ' scwb-v380__field--wide' : ''; ?>">
            <span><?php echo esc_html($label); ?></span>
            <?php if ('textarea' === $type) : ?>
                <textarea data-scwb-v380-field="<?php echo esc_attr($name); ?>"><?php echo esc_textarea($value); ?></textarea>
            <?php else : ?>
                <input type="<?php echo esc_attr($type); ?>" data-scwb-v380-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>">
            <?php endif; ?>
        </label><?php
    }

    public static function render($atts, $panel = 'workspace') {
        self::register_assets();
        wp_enqueue_style('scwb-v380');
        wp_enqueue_script('scwb-v380');
        wp_localize_script('scwb-v380', 'SCWBV380Config', array(
            'version' => self::VERSION,
            'restUrl' => esc_url_raw(rest_url('scwb/v1')),
            'backendUrl' => '',
            'nonce' => wp_create_nonce('wp_rest'),
            'authenticated' => self::can_write(),
            'localHost' => '127.0.0.1',
            'localPort' => 8787,
        ));
        $project = sanitize_key($atts['project']) ?: 'default';
        $display = sanitize_key($atts['display']) ?: 'full';
        $platform = sanitize_key($atts['platform']);
        if (!isset(self::platform_options()[$platform])) { $platform = 'macos'; }
        $tabs = array(
            'workspace' => 'Overview',
            'status' => 'Readiness',
            'installers' => 'Installers',
            'service' => 'Local Service',
            'storage' => 'Offline Storage',
            'runtimes' => 'Runtimes',
            'sync' => 'Synchronization',
            'recovery' => 'Updates & Recovery',
        );
        $instance = 'scwb-v380-' . wp_generate_uuid4();
        ob_start(); ?>
        <section
            id="<?php echo esc_attr($instance); ?>"
            class="scwb-v380 scwb-v380--<?php echo esc_attr($display); ?>"
            data-scwb-v380
            data-scwb-v380-panel="<?php echo esc_attr($panel); ?>"
            data-scwb-v380-project="<?php echo esc_attr($project); ?>"
            data-scwb-v380-platform="<?php echo esc_attr($platform); ?>"
            data-scwb-v380-version="3.8.0"
        >
            <header class="scwb-v380__header">
                <div>
                    <p class="scwb-v380__eyebrow">Sustainable Catalyst Workbench · v3.8.0</p>
                    <h2><?php echo esc_html($atts['title']); ?></h2>
                    <p>Install and operate Workbench locally on macOS, Linux, or Raspberry Pi with browser-local projects, a loopback-only service, portable synchronization bundles, and no Render dependency.</p>
                </div>
                <span class="scwb-v380__status">Local-first · cloud optional</span>
            </header>

            <nav class="scwb-v380__tabs" aria-label="Offline Workbench tools">
                <?php foreach ($tabs as $key => $label) : ?>
                    <button type="button" class="<?php echo $key === $panel ? 'is-active' : ''; ?>" data-scwb-v380-tab="<?php echo esc_attr($key); ?>"><?php echo esc_html($label); ?></button>
                <?php endforeach; ?>
            </nav>

            <div class="scwb-v380__toolbar">
                <label><span>Target platform</span>
                    <select data-scwb-v380-platform-select>
                        <?php foreach (self::platform_options() as $key => $label) : ?>
                            <option value="<?php echo esc_attr($key); ?>" <?php selected($key, $platform); ?>><?php echo esc_html($label); ?></option>
                        <?php endforeach; ?>
                    </select>
                </label>
                <p><strong>Service:</strong> <code>http://127.0.0.1:8787</code> · no public bind · no automatic cloud upload</p>
            </div>

            <div class="scwb-v380__views">
                <section class="scwb-v380__view" data-scwb-v380-view="workspace" <?php echo 'workspace' === $panel ? '' : 'hidden'; ?>>
                    <h3>Offline Workbench architecture</h3>
                    <div class="scwb-v380__cards">
                        <article><strong>Installable packages</strong><p>Platform-specific launchers for macOS, Linux, and Raspberry Pi OS.</p></article>
                        <article><strong>Loopback service</strong><p>FastAPI and the Workbench backend bind only to 127.0.0.1 by default.</p></article>
                        <article><strong>Persistent local storage</strong><p>Projects, backups, revisions, and evidence remain usable without network access.</p></article>
                        <article><strong>Portable synchronization</strong><p>Explicit import/export bundles preserve hashes, conflicts, and rollback requirements.</p></article>
                    </div>
                    <div class="scwb-v380__boundary"><strong>Boundary:</strong> This interface prepares plans and records. It does not run arbitrary shell commands, expose a remote shell, or silently upload local projects.</div>
                </section>

                <section class="scwb-v380__view" data-scwb-v380-view="status" <?php echo 'status' === $panel ? '' : 'hidden'; ?>>
                    <h3>Local readiness audit</h3>
                    <div class="scwb-v380__grid">
                        <?php self::field('Architecture', 'architecture', 'text', 'arm64'); ?>
                        <?php self::field('Python version', 'pythonVersion', 'text', '3.12'); ?>
                        <?php self::field('Free disk space (MB)', 'diskFreeMb', 'number', '8192'); ?>
                        <?php self::field('Memory (MB)', 'memoryMb', 'number', '8192'); ?>
                        <?php self::field('Available commands', 'commands', 'text', 'python3,git,node,go', true); ?>
                    </div>
                    <button type="button" data-scwb-v380-action="audit">Run readiness audit</button>
                </section>

                <section class="scwb-v380__view" data-scwb-v380-view="installers" <?php echo 'installers' === $panel ? '' : 'hidden'; ?>>
                    <h3>Installation plan</h3>
                    <div class="scwb-v380__grid">
                        <?php self::field('Install root', 'installRoot', 'text', ''); ?>
                        <?php self::field('Components', 'components', 'text', 'local-fastapi-service,offline-web-app,browser-project-store,backup-and-restore,sync-bundle-tools,documentation,go-runner', true); ?>
                    </div>
                    <button type="button" data-scwb-v380-action="install">Build installation plan</button>
                </section>

                <section class="scwb-v380__view" data-scwb-v380-view="service" <?php echo 'service' === $panel ? '' : 'hidden'; ?>>
                    <h3>Loopback service configuration</h3>
                    <div class="scwb-v380__cards">
                        <article><strong>Host</strong><p><code>127.0.0.1</code></p></article>
                        <article><strong>Default port</strong><p><code>8787</code></p></article>
                        <article><strong>Public bind</strong><p>Disabled by default</p></article>
                        <article><strong>Render dependency</strong><p>Not required</p></article>
                    </div>
                    <button type="button" data-scwb-v380-action="service">Create service record</button>
                </section>

                <section class="scwb-v380__view" data-scwb-v380-view="storage" <?php echo 'storage' === $panel ? '' : 'hidden'; ?>>
                    <h3>Offline storage and backup</h3>
                    <p>Projects remain browser-local by default and can be exported to versioned JSON bundles. The local application can also use a file-backed project directory with explicit backup and restore actions.</p>
                    <button type="button" data-scwb-v380-action="backup">Build local backup record</button>
                </section>

                <section class="scwb-v380__view" data-scwb-v380-view="runtimes" <?php echo 'runtimes' === $panel ? '' : 'hidden'; ?>>
                    <h3>Runtime and dependency plan</h3>
                    <div class="scwb-v380__grid">
                        <?php self::field('Requested languages', 'languages', 'text', 'python,javascript,go,r,rust', true); ?>
                        <?php self::field('Available runtimes', 'runtimeCommands', 'text', 'python3,node,go', true); ?>
                    </div>
                    <button type="button" data-scwb-v380-action="runtimes">Build runtime plan</button>
                </section>

                <section class="scwb-v380__view" data-scwb-v380-view="sync" <?php echo 'sync' === $panel ? '' : 'hidden'; ?>>
                    <h3>Portable project synchronization</h3>
                    <div class="scwb-v380__grid">
                        <?php self::field('Project ID', 'projectId', 'text', $project); ?>
                        <?php self::field('Project records (JSON)', 'records', 'textarea', '[{"id":"project-' . esc_attr($project) . '","title":"Offline project"}]', true); ?>
                    </div>
                    <button type="button" data-scwb-v380-action="export">Build sync bundle</button>
                    <button type="button" data-scwb-v380-action="download">Download latest bundle</button>
                </section>

                <section class="scwb-v380__view" data-scwb-v380-view="recovery" <?php echo 'recovery' === $panel ? '' : 'hidden'; ?>>
                    <h3>Update and recovery planning</h3>
                    <div class="scwb-v380__grid">
                        <?php self::field('Current version', 'currentVersion', 'text', '3.8.0'); ?>
                        <?php self::field('Target version', 'targetVersion', 'text', '3.8.0'); ?>
                        <?php self::field('Package SHA-256', 'packageHash', 'text', '', true); ?>
                        <?php self::field('Recovery issue', 'issue', 'textarea', 'Local service is unavailable.', true); ?>
                    </div>
                    <button type="button" data-scwb-v380-action="update">Build update plan</button>
                    <button type="button" data-scwb-v380-action="recovery">Build recovery plan</button>
                </section>
            </div>

            <div class="scwb-v380__result" data-scwb-v380-result aria-live="polite">
                <strong>Offline Workbench ready.</strong>
                <p>Select a tool to create a local-first installation, runtime, synchronization, or recovery record.</p>
                <pre data-scwb-v380-output>{}</pre>
            </div>
        </section>
        <?php
        return ob_get_clean();
    }
}

SCWB_V380_Offline_Installable_Workbench::boot();
