<?php
/** Workbench v4.2.0 — Workflow Templates and Guided Scientific/Engineering Project Creation. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V420_Guided_Projects {
    const VERSION = '4.2.0';
    const EXPECTED_STUDIOS = 24;

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_records'), 4);
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 48);
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
        register_post_type('scwb_template', array_merge($common, array('label' => 'Workbench Workflow Templates')));
        register_post_type('scwb_guided_prj', array_merge($common, array('label' => 'Workbench Guided Projects')));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V420_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v420.css';
        $js = $base . '/assets/js/sc-workbench-v420.js';
        wp_register_style('scwb-v420', plugins_url('assets/css/sc-workbench-v420.css', SCWB_V420_PLUGIN_FILE), array('scwb-v410'), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v420', plugins_url('assets/js/sc-workbench-v420.js', SCWB_V420_PLUGIN_FILE), array('scwb-v410'), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_guided_projects' => 'workspace',
            'sc_workbench_template_catalog' => 'catalog',
            'sc_workbench_project_intake' => 'intake',
            'sc_workbench_requirement_planner' => 'requirements',
            'sc_workbench_milestone_planner' => 'milestones',
            'sc_workbench_validation_gates' => 'gates',
            'sc_workbench_starter_evidence' => 'evidence',
            'sc_workbench_project_scaffold' => 'scaffold',
            'sc_workbench_template_package' => 'package',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, function($atts = array()) use ($panel) {
                    $atts = shortcode_atts(array(
                        'project' => 'default',
                        'template' => 'scientific-investigation',
                        'domain' => 'general',
                        'display' => 'full',
                        'title' => 'Guided Scientific and Engineering Projects',
                    ), $atts);
                    return SCWB_V420_Guided_Projects::render($atts, $panel);
                });
            }
        }
    }

    private static function can_persist() {
        return is_user_logged_in() && current_user_can('edit_posts');
    }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/workflow-template-status', array('methods' => 'GET', 'callback' => array(__CLASS__, 'status'), 'permission_callback' => '__return_true'));
        register_rest_route('scwb/v1', '/workflow-templates', array('methods' => array('GET', 'POST'), 'callback' => array(__CLASS__, 'templates'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
        register_rest_route('scwb/v1', '/guided-projects', array('methods' => array('GET', 'POST'), 'callback' => array(__CLASS__, 'projects'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
        register_rest_route('scwb/v1', '/guided-project-scaffolds', array('methods' => 'POST', 'callback' => array(__CLASS__, 'scaffold_plan'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
        register_rest_route('scwb/v1', '/guided-project-validation', array('methods' => 'POST', 'callback' => array(__CLASS__, 'validation_plan'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
    }

    public static function permission_persist() { return self::can_persist(); }

    public static function status() {
        return array(
            'ok' => true,
            'version' => self::VERSION,
            'expectedStudioCount' => self::EXPECTED_STUDIOS,
            'authenticated' => is_user_logged_in(),
            'canPersistPrivateProjects' => self::can_persist(),
            'templateCount' => 6,
            'privateByDefault' => true,
            'browserFallback' => true,
            'offlineFallback' => true,
            'teamReady' => true,
            'paidExternalDatabaseRequired' => false,
            'automaticExperimentExecutionAuthorized' => false,
            'automaticDeviceControlAuthorized' => false,
            'automaticPublicationAuthorized' => false,
            'automaticCertificationAuthorized' => false,
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
        if (!function_exists('wp_insert_post')) { return rest_ensure_response(array('ok' => false, 'message' => 'Private WordPress persistence is unavailable.')); }
        $params = is_object($request) && method_exists($request, 'get_json_params') ? (array) $request->get_json_params() : array();
        $title = isset($params['title']) ? sanitize_text_field($params['title']) : 'Guided Workbench project';
        $post_id = wp_insert_post(array('post_type' => $type, 'post_status' => 'private', 'post_title' => $title, 'post_author' => get_current_user_id()), true);
        if (is_wp_error($post_id)) { return rest_ensure_response(array('ok' => false, 'message' => $post_id->get_error_message())); }
        if (function_exists('update_post_meta')) { update_post_meta($post_id, '_scwb_v420_record', wp_json_encode($params)); }
        return rest_ensure_response(array('ok' => true, 'id' => (int) $post_id, 'private' => true, 'humanReviewRequired' => true));
    }

    public static function templates($request = null) { return self::collection_response('scwb_template', $request); }
    public static function projects($request = null) { return self::collection_response('scwb_guided_prj', $request); }
    public static function scaffold_plan() { return rest_ensure_response(array('ok' => true, 'automaticProjectCreationAuthorized' => false, 'humanReviewRequired' => true)); }
    public static function validation_plan() { return rest_ensure_response(array('ok' => true, 'automaticCertificationAuthorized' => false, 'humanApprovalRequired' => true)); }

    private static function enqueue_assets() {
        self::register_assets();
        wp_enqueue_style('scwb-v420');
        wp_enqueue_script('scwb-v420');
    }

    private static function field($label, $name, $value = '', $type = 'text', $wide = false) {
        echo '<label class="scwb-v420__field' . ($wide ? ' scwb-v420__field--wide' : '') . '"><span>' . esc_html($label) . '</span>';
        if ('textarea' === $type) {
            echo '<textarea data-scwb-v420-field="' . esc_attr($name) . '">' . esc_textarea($value) . '</textarea>';
        } else {
            echo '<input type="' . esc_attr($type) . '" data-scwb-v420-field="' . esc_attr($name) . '" value="' . esc_attr($value) . '">';
        }
        echo '</label>';
    }

    private static function actions($primary) {
        echo '<div class="scwb-v420__actions">';
        echo '<button type="button" class="scwb-v420__button scwb-v420__button--primary" data-scwb-v420-action="build">' . esc_html($primary) . '</button>';
        echo '<button type="button" class="scwb-v420__button" data-scwb-v420-action="save-local">Save browser draft</button>';
        echo '<button type="button" class="scwb-v420__button" data-scwb-v420-action="export">Export record</button>';
        echo '</div><div class="scwb-v420__result" aria-live="polite"><p data-scwb-v420-summary>Ready to create a guided project plan.</p><pre data-scwb-v420-output>{}</pre></div>';
    }

    private static function render_panel($panel, $atts) {
        $template = $atts['template'];
        $domain = $atts['domain'];
        echo '<div class="scwb-v420__grid">';
        if ('workspace' === $panel) {
            echo '<article class="scwb-v420__card"><strong>Choose a workflow</strong><span>Start from a scientific, engineering, measurement, analytics, sustainability, or connected Lab-to-decision template.</span></article>';
            echo '<article class="scwb-v420__card"><strong>Build traceability early</strong><span>Create requirements, milestones, evidence placeholders, validation gates, deliverables, and recommended studio routes before execution.</span></article>';
            echo '<article class="scwb-v420__card"><strong>Prepare for teams</strong><span>Add role bindings and private WordPress storage without making hosted services mandatory.</span></article>';
            echo '<article class="scwb-v420__card"><strong>Keep humans in control</strong><span>Templates never authorize experiments, device control, publication, certification, or professional sign-off.</span></article>';
            self::field('Project title', 'title', 'Guided Workbench Project');
            self::field('Template ID', 'templateId', $template);
            self::field('Domain', 'domain', $domain);
            self::field('Objective', 'objective', 'Define the project objective and expected decision or deliverable.', 'textarea', true);
            self::field('Constraints, one per line', 'constraints', "Time\nBudget\nData availability", 'textarea', true);
            self::field('Team role bindings JSON', 'teamBindings', '[{"userId":"owner","role":"project-owner"}]', 'textarea', true);
            self::actions('Build guided scaffold');
        } elseif ('catalog' === $panel) {
            self::field('Domain filter', 'domain', $domain);
            self::field('Project type filter', 'projectType', '');
            self::actions('Browse templates');
        } elseif ('intake' === $panel) {
            self::field('Project title', 'title', 'Guided Workbench Project');
            self::field('Domain', 'domain', $domain);
            self::field('Project type', 'projectType', 'research');
            self::field('Objective', 'objective', '', 'textarea', true);
            self::field('Research or design question', 'researchQuestion', '', 'textarea', true);
            self::field('Constraints JSON', 'constraints', '["time","budget"]', 'textarea', true);
            self::field('Stakeholders JSON', 'stakeholders', '[]', 'textarea', true);
            self::actions('Build intake');
        } elseif ('requirements' === $panel) {
            self::field('Template ID', 'templateId', $template);
            self::field('Domain', 'domain', $domain);
            self::field('Additional requirements JSON', 'requirements', '[{"id":"custom","title":"Define a project-specific requirement","priority":"should"}]', 'textarea', true);
            self::actions('Build requirement plan');
        } elseif ('milestones' === $panel) {
            self::field('Template ID', 'templateId', $template);
            self::field('Start date', 'startDate', gmdate('Y-m-d'));
            self::field('Target date', 'targetDate', '');
            self::field('Stage durations JSON', 'durations', '{}', 'textarea', true);
            self::actions('Build milestone plan');
        } elseif ('gates' === $panel) {
            self::field('Template ID', 'templateId', $template);
            self::field('Evidence records JSON', 'evidence', '[]', 'textarea', true);
            self::field('Human approvals JSON', 'approvals', '[]', 'textarea', true);
            self::actions('Evaluate gates');
        } elseif ('evidence' === $panel) {
            self::field('Domain', 'domain', $domain);
            self::field('Objective', 'objective', '', 'textarea', true);
            self::field('Source hints JSON', 'sourceHints', '[]', 'textarea', true);
            self::actions('Build starter evidence');
        } elseif ('scaffold' === $panel) {
            self::field('Template ID', 'templateId', $template);
            self::field('Intake JSON', 'intake', '{}', 'textarea', true);
            self::field('Requirements JSON', 'requirements', '[]', 'textarea', true);
            self::field('Milestones JSON', 'milestones', '[]', 'textarea', true);
            self::field('Validation gates JSON', 'validationGates', '[]', 'textarea', true);
            self::field('Team bindings JSON', 'teamBindings', '[]', 'textarea', true);
            self::actions('Build project scaffold');
        } else {
            self::field('Template JSON', 'template', '{}', 'textarea', true);
            self::field('Scaffold JSON', 'scaffold', '{}', 'textarea', true);
            self::actions('Build portable package');
        }
        echo '</div>';
    }

    public static function render($atts, $panel = 'workspace') {
        self::enqueue_assets();
        $project = sanitize_key($atts['project']);
        $template = sanitize_key($atts['template']);
        $domain = sanitize_key($atts['domain']);
        $display = in_array($atts['display'], array('full', 'compact'), true) ? $atts['display'] : 'full';
        $authenticated = self::can_persist();
        $instance = 'scwb-v420-' . wp_generate_uuid4();
        ob_start();
        ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v420 scwb-v420--<?php echo esc_attr($display); ?>" data-scwb-v420 data-scwb-v420-panel="<?php echo esc_attr($panel); ?>" data-scwb-project="<?php echo esc_attr($project); ?>" data-scwb-template="<?php echo esc_attr($template); ?>" data-scwb-domain="<?php echo esc_attr($domain); ?>" data-scwb-authenticated="<?php echo $authenticated ? 'true' : 'false'; ?>">
            <header class="scwb-v420__header">
                <div><p class="scwb-v420__eyebrow">Sustainable Catalyst Workbench · v4.2.0</p><h2><?php echo esc_html($atts['title']); ?></h2><p>Reusable scientific and engineering workflow templates, guided intake, requirements, milestones, validation gates, evidence placeholders, team bindings, and portable project scaffolds.</p></div>
                <span class="scwb-v420__status <?php echo $authenticated ? 'is-online' : 'is-local'; ?>"><?php echo $authenticated ? 'Private WordPress storage available' : 'Browser-local planning'; ?></span>
            </header>
            <?php self::render_panel($panel, array('template' => $template, 'domain' => $domain)); ?>
            <?php if (!$authenticated) : ?><div class="scwb-v420__notice" role="status"><strong>Local-first mode.</strong><span>Sign in with an authorized WordPress account to preserve private templates and guided projects on this site.</span></div><?php endif; ?>
            <p class="scwb-v420__boundary"><strong>Guidance boundary:</strong> templates organize work but do not execute experiments, operate devices, approve findings, publish records, certify compliance, diagnose people, or replace qualified scientific, engineering, medical, legal, or professional review.</p>
        </section>
        <?php
        return ob_get_clean();
    }
}

SCWB_V420_Guided_Projects::boot();
