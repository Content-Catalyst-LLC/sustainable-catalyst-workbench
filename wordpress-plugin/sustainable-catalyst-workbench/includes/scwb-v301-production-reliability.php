<?php
/**
 * Workbench v3.0.1 — Production Activation and Interface Reliability.
 */
if (!defined('ABSPATH')) {
    exit;
}

final class SCWB_V301_Production_Reliability {
    const VERSION = '3.0.1';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_shortcode'), 1001);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
        add_action('admin_notices', array(__CLASS__, 'admin_notice'));
    }

    public static function studio_catalog() {
        return array(
            'connected' => array('label' => 'Connected Environment', 'shortcode' => 'sc_workbench_connected_environment', 'description' => 'One auditable project environment connecting Workbench, Lab, Site Intelligence, Decision Studio, Research Librarian, the Knowledge Library, and offline operation.'),
            'unified' => array('label' => 'Unified Project Hub', 'shortcode' => 'sc_workbench_unified', 'description' => 'Shared projects, studio registry, health, handoffs, packages, and reset safeguards.'),
            'projects' => array('label' => 'Persistent Projects', 'shortcode' => 'sc_workbench_persistent_workspace', 'description' => 'Create, switch, autosave, version, export, and optionally synchronize private Workbench projects.'),
            'teams' => array('label' => 'Team Workspace', 'shortcode' => 'sc_workbench_team_workspace', 'description' => 'Private organizations, authenticated teams, role-based access, shared project spaces, invitations, collaborative revisions, activity, and portable exports.'),
            'guided' => array('label' => 'Guided Projects', 'shortcode' => 'sc_workbench_guided_projects', 'description' => 'Workflow templates, structured intake, requirements, milestones, validation gates, starter evidence, team bindings, and portable project scaffolds.'),
            'data' => array('label' => 'Data Pipelines', 'shortcode' => 'sc_workbench_data_pipelines', 'description' => 'Live-source registries, connector health, dataset manifests, reproducible transformations, validation, freshness, caching, offline snapshots, provenance, and portable packages.'),
            'evaluation' => array('label' => 'Evaluation Lab', 'shortcode' => 'sc_workbench_evaluation_lab', 'description' => 'Benchmark catalogs, experiment matrices, statistical summaries, candidate comparisons, regression detection, reproducibility audits, provisional leaderboards, and human-controlled evaluation gates.'),
            'library' => array('label' => 'Library & Articles', 'shortcode' => 'sc_workbench_library_integration', 'description' => 'Article links, formulas, calculator embeds, citations, Research Librarian routes, and draft return.'),
            'handoffs' => array('label' => 'Platform Handoffs', 'shortcode' => 'sc_workbench_platform_handoffs', 'description' => 'Shared evidence, cross-application packets, compatibility reports, receipts, links, and portable bundles.'),
            'reviews' => array('label' => 'Collaboration & Sign-Off', 'shortcode' => 'sc_workbench_collaboration_review', 'description' => 'Review queues, record comments, requested changes, revision comparison, traceability, immutable snapshots, and technical sign-off.'),
            'research' => array('label' => 'Research Lab', 'shortcode' => 'sc_workbench_lab_canvas', 'description' => 'Canvas, notebook, documentation, and project records.'),
            'embedded' => array('label' => 'Embedded Devices', 'shortcode' => 'sc_workbench_embedded_device_studio', 'description' => 'Raspberry Pi, TinyML, sensors, calibration, and device logs.'),
            'devices' => array('label' => 'Device Orchestration', 'shortcode' => 'sc_workbench_device_orchestration', 'description' => 'Device inventory, consent, capability discovery, calibration, instrument sessions, experiment runs, simulation, logs, and recovery.'),
            'electronics' => array('label' => 'Electronics & FPGA', 'shortcode' => 'sc_workbench_fpga_studio', 'description' => 'HDL, constraints, schematics, BOMs, PCB planning, and validation.'),
            'robotics' => array('label' => 'Robotics & Controls', 'shortcode' => 'sc_workbench_robotics_studio', 'description' => 'Kinematics, PID, actuators, state machines, and HIL records.'),
            'instrumentation' => array('label' => 'Instrumentation', 'shortcode' => 'sc_workbench_instrumentation_studio', 'description' => 'Acquisition planning, signals, spectra, calibration, and uncertainty.'),
            'simulation' => array('label' => 'Simulation & Digital Twins', 'shortcode' => 'sc_workbench_simulation_studio', 'description' => 'Dynamic models, scenarios, Monte Carlo analysis, and validation.'),
            'intelligence' => array('label' => 'Computational Intelligence', 'shortcode' => 'sc_workbench_computational_intelligence', 'description' => 'Dataset profiling, predictive evaluation, forecasting, leakage and drift audits, subgroup checks, model cards, and reproducibility.'),
            'laboratories' => array('label' => 'Domain Laboratories', 'shortcode' => 'sc_workbench_domain_laboratory', 'description' => 'Shared domain profiles, calculations, experiments, validation, notebooks, reports, reproducibility, and Lab synchronization.'),
            'offline' => array('label' => 'Offline & Installable', 'shortcode' => 'sc_workbench_offline_installable', 'description' => 'Local installation, offline storage, loopback service, runner management, synchronization, updates, and recovery.'),
            'hardening' => array('label' => 'Production Hardening', 'shortcode' => 'sc_workbench_production_hardening', 'description' => 'Accessibility, performance, security, compatibility, migration stress, failure recovery, onboarding, extension contracts, and public-release gates.'),
            'runtime' => array('label' => 'Multi-Language Runtime', 'shortcode' => 'sc_workbench_multilanguage_runtime', 'description' => 'Engineering runtimes, equivalence checks, and reproducibility.'),
            'visualization' => array('label' => 'Visualization & Dashboards', 'shortcode' => 'sc_workbench_scientific_visualization', 'description' => 'Scientific plots, dashboards, overlays, state views, and exports.'),
            'experiments' => array('label' => 'Experiment Automation', 'shortcode' => 'sc_workbench_experiment_automation', 'description' => 'Protocols, workflows, schedules, checkpoints, and run audits.'),
            'documentation' => array('label' => 'Documentation & Dossiers', 'shortcode' => 'sc_workbench_documentation_dossier', 'description' => 'Technical reports, traceability, evidence, revisions, and release readiness.'),
            'recovery' => array('label' => 'Migration, Storage & Recovery', 'shortcode' => 'sc_workbench_migration_recovery', 'description' => 'Legacy project migration, browser-storage health, backup, restore, cleanup, and rollback.'),
        );
    }

    public static function register_assets() {
        $base = dirname(SCWB_V301_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v301.css';
        $js = $base . '/assets/js/sc-workbench-v301.js';

        wp_register_style(
            'scwb-v301',
            plugins_url('assets/css/sc-workbench-v301.css', SCWB_V301_PLUGIN_FILE),
            array('scwb-primary-repair'),
            file_exists($css) ? (string) filemtime($css) : self::VERSION
        );
        wp_register_script(
            'scwb-v301',
            plugins_url('assets/js/sc-workbench-v301.js', SCWB_V301_PLUGIN_FILE),
            array('scwb-primary-repair'),
            file_exists($js) ? (string) filemtime($js) : self::VERSION,
            true
        );
    }

    public static function register_shortcode() {
        if (!shortcode_exists('sc_workbench_diagnostics')) {
            add_shortcode('sc_workbench_diagnostics', array(__CLASS__, 'render_diagnostics'));
        }
    }

    public static function availability() {
        $report = array();
        foreach (self::studio_catalog() as $key => $studio) {
            $report[$key] = array(
                'key' => $key,
                'label' => $studio['label'],
                'shortcode' => $studio['shortcode'],
                'available' => shortcode_exists($studio['shortcode']),
            );
        }
        return $report;
    }

    public static function render_diagnostics($atts = array()) {
        wp_enqueue_style('scwb-primary-repair');
        wp_enqueue_style('scwb-v301');
        wp_enqueue_script('scwb-primary-repair');
        wp_enqueue_script('scwb-v301');

        $availability = self::availability();
        $available_count = count(array_filter($availability, static function($item) { return $item['available']; }));
        $total_count = count($availability);

        ob_start();
        ?>
        <section class="scwb-v301-diagnostics" data-scwb-v301-diagnostics>
            <header class="scwb-v301-diagnostics__header">
                <div>
                    <p class="scwb-v301-diagnostics__eyebrow">Workbench production diagnostics</p>
                    <h3>Activation and interface status</h3>
                </div>
                <span class="scwb-v301-diagnostics__score <?php echo $available_count === $total_count ? 'is-ok' : 'is-review'; ?>">
                    <?php echo esc_html($available_count . '/' . $total_count . ' studios registered'); ?>
                </span>
            </header>
            <div class="scwb-v301-diagnostics__grid">
                <?php foreach ($availability as $item) : ?>
                    <div class="scwb-v301-diagnostics__item <?php echo $item['available'] ? 'is-ok' : 'is-missing'; ?>">
                        <strong><?php echo esc_html($item['label']); ?></strong>
                        <code>[<?php echo esc_html($item['shortcode']); ?>]</code>
                        <span><?php echo $item['available'] ? 'Registered' : 'Unavailable'; ?></span>
                    </div>
                <?php endforeach; ?>
            </div>
            <p class="scwb-v301-diagnostics__runtime" data-scwb-v301-runtime-status aria-live="polite">Browser activation check pending.</p>
        </section>
        <?php
        return ob_get_clean();
    }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/production-status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'rest_status'),
            'permission_callback' => '__return_true',
        ));
    }

    public static function rest_status() {
        $availability = self::availability();
        $missing = array_values(array_map(
            static function($item) { return $item['shortcode']; },
            array_filter($availability, static function($item) { return !$item['available']; })
        ));

        return rest_ensure_response(array(
            'ok' => empty($missing) && shortcode_exists('sc_workbench'),
            'schema' => 'sc-workbench-production-status/1.0',
            'version' => self::VERSION,
            'primaryShortcodeRegistered' => shortcode_exists('sc_workbench'),
            'studios' => array_values($availability),
            'missingShortcodes' => $missing,
            'expectedStudioCount' => count($availability),
            'registeredStudioCount' => count($availability) - count($missing),
        ));
    }

    public static function admin_notice() {
        if (!current_user_can('manage_options')) {
            return;
        }
        $availability = self::availability();
        $missing = array_filter($availability, static function($item) { return !$item['available']; });
        if (!$missing && shortcode_exists('sc_workbench')) {
            return;
        }
        $labels = array_map(static function($item) { return $item['label']; }, $missing);
        echo '<div class="notice notice-warning"><p><strong>Workbench v3.0.1 production diagnostics:</strong> ';
        if (!shortcode_exists('sc_workbench')) {
            echo 'the canonical <code>[sc_workbench]</code> shortcode is not registered. ';
        }
        if ($labels) {
            echo 'Unavailable studios: ' . esc_html(implode(', ', $labels)) . '. ';
        }
        echo 'Reinstall the complete v3.0.1 plugin and clear all cache layers.</p></div>';
    }
}

SCWB_V301_Production_Reliability::boot();
