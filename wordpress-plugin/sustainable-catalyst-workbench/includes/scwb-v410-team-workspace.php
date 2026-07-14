<?php
/** Workbench v4.1.0 — Hosted Collaborative Workspace and Authenticated Team Projects. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V410_Team_Workspace {
    const VERSION = '4.1.0';
    const EXPECTED_STUDIOS = 23;

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_records'), 4);
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 47);
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
        register_post_type('scwb_org', array_merge($common, array('label' => 'Workbench Organizations')));
        register_post_type('scwb_team', array_merge($common, array('label' => 'Workbench Teams')));
        register_post_type('scwb_team_prj', array_merge($common, array('label' => 'Workbench Team Projects')));
        register_post_type('scwb_invite', array_merge($common, array('label' => 'Workbench Team Invitations')));
        register_post_type('scwb_activity', array_merge($common, array('label' => 'Workbench Team Activity')));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V410_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v410.css';
        $js = $base . '/assets/js/sc-workbench-v410.js';
        wp_register_style('scwb-v410', plugins_url('assets/css/sc-workbench-v410.css', SCWB_V410_PLUGIN_FILE), array('scwb-v402'), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v410', plugins_url('assets/js/sc-workbench-v410.js', SCWB_V410_PLUGIN_FILE), array('scwb-v402'), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_team_workspace' => 'workspace',
            'sc_workbench_organization_manager' => 'organization',
            'sc_workbench_team_manager' => 'team',
            'sc_workbench_membership_roles' => 'roles',
            'sc_workbench_team_invitations' => 'invitations',
            'sc_workbench_shared_project_space' => 'projects',
            'sc_workbench_collaborative_revisions' => 'revisions',
            'sc_workbench_team_activity' => 'activity',
            'sc_workbench_team_export' => 'export',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, function($atts = array()) use ($panel) {
                    $atts = shortcode_atts(array('project' => 'default', 'team' => 'default', 'display' => 'full', 'title' => 'Hosted Collaborative Workspace'), $atts);
                    return SCWB_V410_Team_Workspace::render($atts, $panel);
                });
            }
        }
    }

    private static function can_collaborate() {
        return is_user_logged_in() && current_user_can('edit_posts');
    }

    private static function can_administer() {
        return is_user_logged_in() && (current_user_can('manage_options') || current_user_can('edit_others_posts'));
    }

    private static function permission_manage() { return self::can_collaborate(); }
    private static function permission_admin() { return self::can_administer(); }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/team-workspace-status', array('methods' => 'GET', 'callback' => array(__CLASS__, 'status'), 'permission_callback' => '__return_true'));
        register_rest_route('scwb/v1', '/organizations', array('methods' => array('GET', 'POST'), 'callback' => array(__CLASS__, 'organizations'), 'permission_callback' => array(__CLASS__, 'permission_admin')));
        register_rest_route('scwb/v1', '/teams', array('methods' => array('GET', 'POST'), 'callback' => array(__CLASS__, 'teams'), 'permission_callback' => array(__CLASS__, 'permission_manage')));
        register_rest_route('scwb/v1', '/team-projects', array('methods' => array('GET', 'POST'), 'callback' => array(__CLASS__, 'projects'), 'permission_callback' => array(__CLASS__, 'permission_manage')));
        register_rest_route('scwb/v1', '/team-invitations', array('methods' => array('GET', 'POST'), 'callback' => array(__CLASS__, 'invitations'), 'permission_callback' => array(__CLASS__, 'permission_admin')));
        register_rest_route('scwb/v1', '/team-activity', array('methods' => 'GET', 'callback' => array(__CLASS__, 'activity'), 'permission_callback' => array(__CLASS__, 'permission_manage')));
        register_rest_route('scwb/v1', '/team-access-check', array('methods' => 'POST', 'callback' => array(__CLASS__, 'access_check'), 'permission_callback' => array(__CLASS__, 'permission_manage')));
    }

    public static function status() {
        return array(
            'ok' => true,
            'version' => self::VERSION,
            'expectedStudioCount' => self::EXPECTED_STUDIOS,
            'authenticated' => is_user_logged_in(),
            'canCollaborate' => self::can_collaborate(),
            'canAdministerTeams' => self::can_administer(),
            'privateByDefault' => true,
            'browserFallback' => true,
            'offlineFallback' => true,
            'paidExternalDatabaseRequired' => false,
            'automaticInvitationAcceptanceAuthorized' => false,
            'automaticMembershipEscalationAuthorized' => false,
            'automaticProjectDeletionAuthorized' => false,
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
        if ('POST' !== strtoupper($method)) { return rest_ensure_response(array('ok' => true, 'records' => self::list_records($type))); }
        if (!function_exists('wp_insert_post')) { return rest_ensure_response(array('ok' => false, 'message' => 'WordPress persistence is unavailable.')); }
        $params = is_object($request) && method_exists($request, 'get_json_params') ? (array) $request->get_json_params() : array();
        $title = isset($params['title']) ? sanitize_text_field($params['title']) : 'Workbench team record';
        $post_id = wp_insert_post(array('post_type' => $type, 'post_status' => 'private', 'post_title' => $title, 'post_author' => get_current_user_id()), true);
        if (is_wp_error($post_id)) { return rest_ensure_response(array('ok' => false, 'message' => $post_id->get_error_message())); }
        if (function_exists('update_post_meta')) { update_post_meta($post_id, '_scwb_v410_record', wp_json_encode($params)); }
        return rest_ensure_response(array('ok' => true, 'id' => (int) $post_id, 'private' => true));
    }

    public static function organizations($request = null) { return self::collection_response('scwb_org', $request); }
    public static function teams($request = null) { return self::collection_response('scwb_team', $request); }
    public static function projects($request = null) { return self::collection_response('scwb_team_prj', $request); }
    public static function invitations($request = null) { return self::collection_response('scwb_invite', $request); }
    public static function activity() { return rest_ensure_response(array('ok' => true, 'records' => self::list_records('scwb_activity'))); }
    public static function access_check($request = null) { return rest_ensure_response(array('ok' => self::can_collaborate(), 'humanAuthorizationRequired' => true)); }

    private static function enqueue_assets() {
        self::register_assets();
        wp_enqueue_style('scwb-v410');
        wp_enqueue_script('scwb-v410');
    }

    private static function field($label, $name, $value = '', $type = 'text', $wide = false) {
        echo '<label class="scwb-v410__field' . ($wide ? ' scwb-v410__field--wide' : '') . '"><span>' . esc_html($label) . '</span>';
        if ('textarea' === $type) {
            echo '<textarea data-scwb-v410-field="' . esc_attr($name) . '">' . esc_textarea($value) . '</textarea>';
        } else {
            echo '<input type="' . esc_attr($type) . '" data-scwb-v410-field="' . esc_attr($name) . '" value="' . esc_attr($value) . '">';
        }
        echo '</label>';
    }

    private static function actions($primary) {
        echo '<div class="scwb-v410__actions">';
        echo '<button type="button" class="scwb-v410__button scwb-v410__button--primary" data-scwb-v410-action="build">' . esc_html($primary) . '</button>';
        echo '<button type="button" class="scwb-v410__button" data-scwb-v410-action="save-local">Save browser draft</button>';
        echo '<button type="button" class="scwb-v410__button" data-scwb-v410-action="export">Export record</button>';
        echo '</div><div class="scwb-v410__result" aria-live="polite"><p data-scwb-v410-summary>Ready for authenticated collaboration planning.</p><pre data-scwb-v410-output>{}</pre></div>';
    }

    private static function render_panel($panel, $authenticated) {
        echo '<div class="scwb-v410__grid">';
        if ('workspace' === $panel) {
            echo '<article class="scwb-v410__card"><strong>Organization and teams</strong><span>Private organizational boundaries, team membership, invitations, and role-based capabilities.</span></article>';
            echo '<article class="scwb-v410__card"><strong>Shared project spaces</strong><span>Authenticated team projects with revisions, ownership, activity records, and explicit access checks.</span></article>';
            echo '<article class="scwb-v410__card"><strong>Local-first fallback</strong><span>Anonymous and offline users retain browser-local projects. No paid database is required.</span></article>';
            self::field('Organization name', 'organizationName', 'Sustainable Catalyst');
            self::field('Team name', 'teamName', 'Research and Engineering');
            self::field('Project title', 'projectTitle', 'Connected Team Project');
            self::field('Members (JSON)', 'members', '[{"userId":"owner-1","role":"owner","status":"active"},{"userId":"reviewer-1","role":"reviewer","status":"active"}]', 'textarea', true);
            self::actions('Build team workspace plan');
        } elseif ('organization' === $panel) {
            self::field('Organization name', 'organizationName', 'Sustainable Catalyst');
            self::field('Owner user IDs, one per line', 'owners', "owner-1");
            self::field('Retention days', 'retentionDays', '365', 'number');
            self::field('Allow external invitations', 'allowExternalInvitations', 'false');
            self::actions('Build organization record');
        } elseif ('team' === $panel) {
            self::field('Organization ID', 'organizationId', 'sustainable-catalyst');
            self::field('Team name', 'teamName', 'Research and Engineering');
            self::field('Members (JSON)', 'members', '[{"userId":"owner-1","role":"owner","status":"active"},{"userId":"editor-1","role":"editor","status":"active"}]', 'textarea', true);
            self::actions('Build team record');
        } elseif ('roles' === $panel) {
            self::field('User ID', 'userId', 'reviewer-1');
            self::field('Requested action', 'requestedAction', 'review:write');
            self::field('Memberships (JSON)', 'memberships', '[{"userId":"reviewer-1","role":"reviewer","status":"active"}]', 'textarea', true);
            self::actions('Evaluate project access');
        } elseif ('invitations' === $panel) {
            self::field('Team ID', 'teamId', 'research-engineering');
            self::field('Invitee email', 'email', 'collaborator@example.org', 'email');
            self::field('Role', 'role', 'viewer');
            self::field('Expiration', 'expiresAt', '2026-08-13T23:59:59Z');
            self::actions('Build invitation plan');
        } elseif ('projects' === $panel) {
            self::field('Organization ID', 'organizationId', 'sustainable-catalyst');
            self::field('Team ID', 'teamId', 'research-engineering');
            self::field('Project ID', 'projectId', 'connected-team-project');
            self::field('Project title', 'projectTitle', 'Connected Team Project');
            self::field('Role bindings (JSON)', 'roleBindings', '[{"userId":"owner-1","role":"owner","status":"active"},{"userId":"editor-1","role":"editor","status":"active"}]', 'textarea', true);
            self::actions('Build shared project space');
        } elseif ('revisions' === $panel) {
            self::field('Base revision (JSON)', 'base', '{"title":"Project","status":"draft","value":1}', 'textarea', true);
            self::field('Local revision (JSON)', 'local', '{"title":"Project","status":"review","value":2}', 'textarea', true);
            self::field('Remote revision (JSON)', 'remote', '{"title":"Project","status":"draft","value":3}', 'textarea', true);
            self::field('Merge strategy', 'strategy', 'manual');
            self::actions('Build collaborative merge plan');
        } elseif ('activity' === $panel) {
            self::field('Actor user ID', 'actorUserId', 'editor-1');
            self::field('Action', 'activityAction', 'project.updated');
            self::field('Target ID', 'targetId', 'connected-team-project');
            self::field('Metadata (JSON)', 'metadata', '{"revision":2,"summary":"Updated assumptions"}', 'textarea', true);
            self::actions('Build immutable activity record');
        } else {
            self::field('Organization record (JSON)', 'organization', '{"organizationId":"sustainable-catalyst","name":"Sustainable Catalyst"}', 'textarea', true);
            self::field('Team record (JSON)', 'team', '{"teamId":"research-engineering","members":[{"userId":"owner-1","role":"owner"}]}', 'textarea', true);
            self::field('Projects (JSON)', 'projects', '[{"projectId":"connected-team-project","title":"Connected Team Project"}]', 'textarea', true);
            self::actions('Build portable team export');
        }
        echo '</div>';
        if (!$authenticated) {
            echo '<div class="scwb-v410__notice" role="status"><strong>Browser-local mode.</strong><span>Sign in with an authorized WordPress account to create private hosted organizations, teams, invitations, and team projects.</span></div>';
        }
    }

    public static function render($atts, $panel) {
        self::enqueue_assets();
        $project = sanitize_key($atts['project']) ?: 'default';
        $team = sanitize_key($atts['team']) ?: 'default';
        $display = sanitize_key($atts['display']);
        if (!in_array($display, array('compact', 'full', 'inline', 'drawer'), true)) { $display = 'full'; }
        $authenticated = is_user_logged_in();
        $instance = 'scwb-v410-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v410 scwb-v410--<?php echo esc_attr($display); ?>" data-scwb-v410 data-scwb-v410-panel="<?php echo esc_attr($panel); ?>" data-scwb-project="<?php echo esc_attr($project); ?>" data-scwb-team="<?php echo esc_attr($team); ?>" data-scwb-authenticated="<?php echo $authenticated ? 'true' : 'false'; ?>">
            <header class="scwb-v410__header">
                <div><p class="scwb-v410__eyebrow">Sustainable Catalyst Workbench · v4.1.0</p><h2><?php echo esc_html($atts['title']); ?></h2><p>Private organizations, authenticated teams, role-based access, shared project spaces, invitations, revisions, activity records, and portable collaboration packages.</p></div>
                <span class="scwb-v410__status <?php echo $authenticated ? 'is-online' : 'is-local'; ?>"><?php echo $authenticated ? 'Authenticated team mode' : 'Browser-local fallback'; ?></span>
            </header>
            <?php self::render_panel($panel, $authenticated); ?>
            <p class="scwb-v410__boundary"><strong>Collaboration boundary:</strong> invitations, access changes, conflict resolution, deletion, publication, and professional sign-off require authenticated human authorization. Workbench does not automatically escalate roles, accept invitations, delete projects, or expose private records publicly.</p>
        </section>
        <?php return ob_get_clean();
    }
}
SCWB_V410_Team_Workspace::boot();
