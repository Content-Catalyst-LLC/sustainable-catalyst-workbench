<?php
/** Workbench v4.5.0 — Extension SDK, Plugin Registry, and Third-Party Module Framework. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V450_Extension_Framework {
    const VERSION = '4.5.0';
    const EXPECTED_STUDIOS = 27;

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_records'), 4);
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 50);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_records() {
        $common = array(
            'public' => false,
            'show_ui' => false,
            'show_in_rest' => false,
            'exclude_from_search' => true,
            'supports' => array('title', 'author', 'custom-fields'),
        );
        register_post_type('scwb_extension', array_merge($common, array('label' => 'Workbench Extensions')));
        register_post_type('scwb_ext_release', array_merge($common, array('label' => 'Workbench Extension Releases')));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V450_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v450.css';
        $js = $base . '/assets/js/sc-workbench-v450.js';
        wp_register_style('scwb-v450', plugins_url('assets/css/sc-workbench-v450.css', SCWB_V450_PLUGIN_FILE), array('scwb-v440'), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v450', plugins_url('assets/js/sc-workbench-v450.js', SCWB_V450_PLUGIN_FILE), array('scwb-v440'), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_extension_sdk' => 'workspace',
            'sc_workbench_extension_registry' => 'registry',
            'sc_workbench_extension_manifest' => 'manifest',
            'sc_workbench_extension_compatibility' => 'compatibility',
            'sc_workbench_extension_permissions' => 'permissions',
            'sc_workbench_extension_hooks' => 'hooks',
            'sc_workbench_extension_lifecycle' => 'lifecycle',
            'sc_workbench_extension_validator' => 'validator',
            'sc_workbench_extension_package' => 'package',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, function($atts = array()) use ($panel) {
                    $atts = shortcode_atts(array(
                        'project' => 'default',
                        'extension' => 'default',
                        'display' => 'full',
                        'title' => 'Extension SDK and Plugin Registry',
                    ), $atts);
                    return SCWB_V450_Extension_Framework::render($atts, $panel);
                });
            }
        }
    }

    private static function can_persist() { return is_user_logged_in() && current_user_can('edit_posts'); }
    public static function permission_persist() { return self::can_persist(); }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/extension-framework-status', array('methods' => 'GET', 'callback' => array(__CLASS__, 'status'), 'permission_callback' => '__return_true'));
        register_rest_route('scwb/v1', '/extensions', array('methods' => array('GET', 'POST'), 'callback' => array(__CLASS__, 'extensions'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
        register_rest_route('scwb/v1', '/extension-releases', array('methods' => array('GET', 'POST'), 'callback' => array(__CLASS__, 'extension_releases'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
        register_rest_route('scwb/v1', '/extension-validation', array('methods' => 'POST', 'callback' => array(__CLASS__, 'validation_plan'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
        register_rest_route('scwb/v1', '/extension-install-plans', array('methods' => 'POST', 'callback' => array(__CLASS__, 'install_plan'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
        register_rest_route('scwb/v1', '/extension-hooks', array('methods' => 'POST', 'callback' => array(__CLASS__, 'hook_plan'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
    }

    public static function status() {
        return array(
            'ok' => true,
            'version' => self::VERSION,
            'expectedStudioCount' => self::EXPECTED_STUDIOS,
            'authenticated' => is_user_logged_in(),
            'canPersistPrivateExtensionRecords' => self::can_persist(),
            'privateRegistryByDefault' => true,
            'browserDevelopmentMode' => true,
            'offlineSDK' => true,
            'paidExternalRegistryRequired' => false,
            'automaticExtensionInstallationAuthorized' => false,
            'automaticExtensionActivationAuthorized' => false,
            'automaticPrivilegeEscalationAuthorized' => false,
            'arbitraryCodeExecutionAuthorized' => false,
            'remoteShellAuthorized' => false,
            'automaticPublicationAuthorized' => false,
        );
    }

    private static function list_records($type) {
        if (!function_exists('get_posts')) { return array(); }
        $posts = get_posts(array('post_type' => $type, 'post_status' => array('private', 'draft'), 'numberposts' => 100, 'orderby' => 'modified', 'order' => 'DESC'));
        $records = array();
        foreach ($posts as $post) {
            $records[] = array('id' => (int) $post->ID, 'title' => $post->post_title, 'status' => $post->post_status, 'modified' => $post->post_modified_gmt);
        }
        return $records;
    }

    private static function collection_response($type, $request) {
        $method = is_object($request) && method_exists($request, 'get_method') ? $request->get_method() : 'GET';
        if ('POST' !== strtoupper($method)) {
            return rest_ensure_response(array('ok' => true, 'records' => self::list_records($type)));
        }
        if (!function_exists('wp_insert_post')) {
            return rest_ensure_response(array('ok' => false, 'message' => 'Private WordPress persistence is unavailable.'));
        }
        $params = is_object($request) && method_exists($request, 'get_json_params') ? (array) $request->get_json_params() : array();
        $title = isset($params['title']) ? sanitize_text_field($params['title']) : 'Workbench extension record';
        $post_id = wp_insert_post(array('post_type' => $type, 'post_status' => 'private', 'post_title' => $title, 'post_author' => get_current_user_id()), true);
        if (is_wp_error($post_id)) {
            return rest_ensure_response(array('ok' => false, 'message' => $post_id->get_error_message()));
        }
        if (function_exists('update_post_meta')) {
            update_post_meta($post_id, '_scwb_v450_record', wp_json_encode($params));
        }
        return rest_ensure_response(array('ok' => true, 'id' => (int) $post_id, 'private' => true, 'automaticPublicationAuthorized' => false, 'automaticExtensionActivationAuthorized' => false));
    }

    public static function extensions($request = null) { return self::collection_response('scwb_extension', $request); }
    public static function extension_releases($request = null) { return self::collection_response('scwb_ext_release', $request); }
    public static function validation_plan() { return rest_ensure_response(array('ok' => true, 'humanSecurityReviewRequired' => true, 'arbitraryCodeExecutionAuthorized' => false)); }
    public static function install_plan() { return rest_ensure_response(array('ok' => true, 'requiresExplicitApproval' => true, 'requiresVerifiedBackupForUpdateOrUninstall' => true, 'automaticExtensionInstallationAuthorized' => false)); }
    public static function hook_plan() { return rest_ensure_response(array('ok' => true, 'isolatedExecutionRequired' => true, 'automaticHookExecutionAuthorized' => false)); }

    private static function enqueue_assets() {
        self::register_assets();
        wp_enqueue_style('scwb-v450');
        wp_enqueue_script('scwb-v450');
    }

    private static function field($label, $name, $value = '', $type = 'text', $wide = false) {
        echo '<label class="scwb-v450__field' . ($wide ? ' scwb-v450__field--wide' : '') . '"><span>' . esc_html($label) . '</span>';
        if ('textarea' === $type) {
            echo '<textarea data-scwb-v450-field="' . esc_attr($name) . '">' . esc_textarea($value) . '</textarea>';
        } else {
            echo '<input type="' . esc_attr($type) . '" data-scwb-v450-field="' . esc_attr($name) . '" value="' . esc_attr($value) . '">';
        }
        echo '</label>';
    }

    private static function actions($primary) {
        echo '<div class="scwb-v450__actions"><button type="button" class="scwb-v450__button scwb-v450__button--primary" data-scwb-v450-action="build">' . esc_html($primary) . '</button><button type="button" class="scwb-v450__button" data-scwb-v450-action="save-local">Save browser record</button><button type="button" class="scwb-v450__button" data-scwb-v450-action="export">Export JSON</button></div><div class="scwb-v450__result" aria-live="polite"><p data-scwb-v450-summary>Ready to prepare a capability-scoped extension record.</p><pre data-scwb-v450-output>{}</pre></div>';
    }

    private static function render_panel($panel, $extension) {
        echo '<div class="scwb-v450__grid">';
        if ('workspace' === $panel) {
            echo '<article class="scwb-v450__card"><strong>Define an extension</strong><span>Create a versioned manifest with explicit capabilities, hooks, compatibility bounds, provenance, licensing, and package integrity.</span></article>';
            echo '<article class="scwb-v450__card"><strong>Restrict privileges</strong><span>Use least-privilege capability scopes, hostname allowlists, project boundaries, and explicit approval for high-risk operations.</span></article>';
            echo '<article class="scwb-v450__card"><strong>Validate lifecycle changes</strong><span>Plan installation, activation, updates, deactivation, and uninstall with compatibility, signature, backup, and receipt checks.</span></article>';
            echo '<article class="scwb-v450__card"><strong>Package reproducibly</strong><span>Preserve file hashes, tests, documentation, compatibility reports, security audits, and human review records.</span></article>';
            self::field('Extension ID', 'extensionId', $extension);
            self::field('Name', 'name', 'Example Workbench Extension');
            self::field('Publisher', 'publisher', 'Sustainable Catalyst Developer');
            self::field('Version', 'extensionVersion', '0.1.0');
            self::field('Capabilities JSON', 'capabilities', '["project.read","ui.panel"]', 'textarea', true);
            self::field('Hooks JSON', 'hooks', '["workbench.ready"]', 'textarea', true);
            self::actions('Build extension workspace record');
        } elseif ('manifest' === $panel) {
            self::field('Manifest JSON', 'manifest', '{"name":"Example","version":"0.1.0","publisher":"Developer","minimumCoreVersion":"4.5.0","capabilities":["project.read","ui.panel"],"hooks":["workbench.ready"]}', 'textarea', true);
            self::actions('Normalize manifest');
        } elseif ('compatibility' === $panel) {
            self::field('Manifest JSON', 'manifest', '{"extensionId":"example","version":"0.1.0","coreCompatibility":{"minimum":"4.5.0","maximum":""},"capabilities":["project.read"]}', 'textarea', true);
            self::field('Core version', 'coreVersion', '4.5.0');
            self::field('Installed extensions JSON', 'installedExtensions', '{}', 'textarea', true);
            self::actions('Evaluate compatibility');
        } elseif ('permissions' === $panel) {
            self::field('Capabilities JSON', 'capabilities', '["project.read","ui.panel"]', 'textarea', true);
            self::field('Allowed hosts JSON', 'allowedHosts', '[]', 'textarea', true);
            self::field('Data scopes JSON', 'dataScopes', '["project:default"]', 'textarea', true);
            self::actions('Audit permissions');
        } elseif ('hooks' === $panel) {
            self::field('Extension ID', 'extensionId', $extension);
            self::field('Hook', 'hook', 'project.saved');
            self::field('Handler', 'handler', 'extension.onProjectSaved');
            self::field('Capability scopes JSON', 'capabilityScopes', '["project.read"]', 'textarea', true);
            self::actions('Build hook contract');
        } elseif ('lifecycle' === $panel) {
            self::field('Action', 'action', 'install');
            self::field('Manifest JSON', 'manifest', '{"extensionId":"example","version":"0.1.0"}', 'textarea', true);
            self::field('Compatibility JSON', 'compatibility', '{"compatible":true}', 'textarea', true);
            self::field('Confirmation phrase', 'confirmationPhrase', '');
            self::actions('Build lifecycle plan');
        } elseif ('validator' === $panel) {
            self::field('Manifest JSON', 'manifest', '{"extensionId":"example","version":"0.1.0","capabilities":["project.read"]}', 'textarea', true);
            self::field('Source files JSON', 'sourceFiles', '["src/extension.js"]', 'textarea', true);
            self::field('Source text', 'sourceText', 'export function activate(api) { return api.project.read(); }', 'textarea', true);
            self::actions('Audit extension');
        } elseif ('registry' === $panel) {
            self::field('Manifest JSON', 'manifest', '{"extensionId":"example","version":"0.1.0","manifestHash":""}', 'textarea', true);
            self::field('State', 'state', 'review');
            self::field('Trust tier', 'trustTier', 'community');
            self::field('Reviewer', 'reviewer', '');
            self::actions('Build registry entry');
        } else {
            self::field('Manifest JSON', 'manifest', '{"extensionId":"example","version":"0.1.0"}', 'textarea', true);
            self::field('Files JSON', 'files', '{"src/extension.js":"export function activate(){}"}', 'textarea', true);
            self::field('Compatibility JSON', 'compatibility', '{"compatible":true}', 'textarea', true);
            self::field('Audit JSON', 'audit', '{"ready":true}', 'textarea', true);
            self::actions('Build extension package');
        }
        echo '</div>';
    }

    public static function render($atts, $panel = 'workspace') {
        self::enqueue_assets();
        $project = sanitize_key($atts['project']) ?: 'default';
        $extension = sanitize_key($atts['extension']) ?: 'default';
        $display = sanitize_key($atts['display']);
        if (!in_array($display, array('full', 'compact', 'inline'), true)) { $display = 'full'; }
        $authenticated = self::can_persist();
        $instance = 'scwb-v450-' . wp_generate_uuid4();
        ob_start();
        ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v450 scwb-v450--<?php echo esc_attr($display); ?>" data-scwb-v450 data-scwb-v450-panel="<?php echo esc_attr($panel); ?>" data-scwb-project="<?php echo esc_attr($project); ?>" data-scwb-extension="<?php echo esc_attr($extension); ?>" data-scwb-authenticated="<?php echo $authenticated ? 'true' : 'false'; ?>">
            <header class="scwb-v450__header"><div><p class="scwb-v450__eyebrow">Sustainable Catalyst Workbench · v4.5.0</p><h2><?php echo esc_html($atts['title']); ?></h2><p>Capability-scoped extension manifests, compatibility reports, private registry records, hook contracts, lifecycle plans, developer scaffolds, security audits, and portable extension packages.</p></div><span class="scwb-v450__status <?php echo $authenticated ? 'is-online' : 'is-local'; ?>"><?php echo $authenticated ? 'Private WordPress registry available' : 'Browser-local extension development'; ?></span></header>
            <?php self::render_panel($panel, $extension); ?>
            <?php if (!$authenticated) : ?><div class="scwb-v450__notice" role="status"><strong>Local-first mode.</strong><span>Sign in with an authorized WordPress account to preserve private extension and release records on this site.</span></div><?php endif; ?>
            <p class="scwb-v450__boundary"><strong>Extension boundary:</strong> manifests, hooks, packages, and lifecycle records never authorize arbitrary code execution, remote shells, automatic installation, automatic activation, privilege escalation, publication, device execution, or safety-control bypasses.</p>
        </section>
        <?php
        return ob_get_clean();
    }
}

SCWB_V450_Extension_Framework::boot();
