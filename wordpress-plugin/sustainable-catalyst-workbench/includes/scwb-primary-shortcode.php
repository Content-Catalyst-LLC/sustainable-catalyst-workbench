<?php
/** Workbench v2.8.1 primary shortcode repair. */
if (!defined('ABSPATH')) {
    exit;
}

final class SCWB_Primary_Shortcode_Repair {
    const VERSION = '2.9.0';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_shortcode'), 99);
        add_action('wp_enqueue_scripts', array(__CLASS__, 'register_assets'));
    }

    public static function register_assets() {
        wp_register_style(
            'scwb-primary-repair',
            plugins_url('../assets/css/scwb-primary-repair.css', __FILE__),
            array(),
            self::VERSION
        );
        wp_register_script(
            'scwb-primary-repair',
            plugins_url('../assets/js/scwb-primary-repair.js', __FILE__),
            array(),
            self::VERSION,
            true
        );
    }

    public static function register_shortcode() {
        if (!shortcode_exists('sc_workbench')) {
            add_shortcode('sc_workbench', array(__CLASS__, 'render'));
        }
    }

    private static function studios() {
        return array(
            'research' => array(
                'label' => 'Research Lab',
                'shortcode' => 'sc_workbench_lab_canvas',
                'description' => 'Canvas, notebook, documentation, and project records.',
            ),
            'embedded' => array(
                'label' => 'Embedded Devices',
                'shortcode' => 'sc_workbench_embedded_device_studio',
                'description' => 'Raspberry Pi, TinyML, sensors, calibration, and device logs.',
            ),
            'electronics' => array(
                'label' => 'Electronics & FPGA',
                'shortcode' => 'sc_workbench_fpga_studio',
                'description' => 'HDL, constraints, schematics, BOMs, PCB planning, and validation.',
            ),
            'robotics' => array(
                'label' => 'Robotics & Controls',
                'shortcode' => 'sc_workbench_robotics_studio',
                'description' => 'Kinematics, PID, actuators, state machines, and HIL records.',
            ),
            'instrumentation' => array(
                'label' => 'Instrumentation',
                'shortcode' => 'sc_workbench_instrumentation_studio',
                'description' => 'Acquisition planning, signals, spectra, calibration, and uncertainty.',
            ),
            'simulation' => array(
                'label' => 'Simulation & Digital Twins',
                'shortcode' => 'sc_workbench_simulation_studio',
                'description' => 'Dynamic models, scenarios, Monte Carlo analysis, and validation.',
            ),
            'runtime' => array(
                'label' => 'Multi-Language Runtime',
                'shortcode' => 'sc_workbench_multilanguage_runtime',
                'description' => 'Engineering runtimes, equivalence checks, and reproducibility.',
            ),
            'visualization' => array(
                'label' => 'Visualization & Dashboards',
                'shortcode' => 'sc_workbench_scientific_visualization',
                'description' => 'Scientific plots, dashboards, overlays, state views, and exports.',
            ),
            'experiments' => array(
                'label' => 'Experiment Automation',
                'shortcode' => 'sc_workbench_experiment_automation',
                'description' => 'Protocols, workflows, schedules, checkpoints, and run audits.',
            ),
            'documentation' => array(
                'label' => 'Documentation & Dossiers',
                'shortcode' => 'sc_workbench_documentation_dossier',
                'description' => 'Technical reports, traceability, evidence, revisions, and release readiness.',
            ),
        );
    }

    public static function render($atts = array()) {
        $atts = shortcode_atts(
            array(
                'topic' => 'workbench',
                'title' => 'Sustainable Catalyst Workbench',
                'display' => 'full',
                'project' => 'default',
                'studio' => 'research',
            ),
            $atts,
            'sc_workbench'
        );

        $display = sanitize_key($atts['display']);
        if (!in_array($display, array('inline', 'compact', 'full', 'drawer'), true)) {
            $display = 'full';
        }

        $project = sanitize_key($atts['project']);
        if (!$project) {
            $project = 'default';
        }

        $studios = self::studios();
        $initial = sanitize_key($atts['studio']);
        if (!isset($studios[$initial])) {
            $initial = 'research';
        }

        wp_enqueue_style('scwb-primary-repair');
        wp_enqueue_script('scwb-primary-repair');

        $available = array();
        foreach ($studios as $key => $studio) {
            if (shortcode_exists($studio['shortcode'])) {
                $available[$key] = $studio;
            }
        }

        if (!$available) {
            return '<div class="scwb-primary scwb-primary--error"><strong>Workbench modules are unavailable.</strong> Confirm that the Sustainable Catalyst Prototyping Workbench plugin is active.</div>';
        }

        if (!isset($available[$initial])) {
            $initial = array_key_first($available);
        }

        $instance = 'scwb-primary-' . wp_generate_uuid4();

        ob_start();
        ?>
        <section
            id="<?php echo esc_attr($instance); ?>"
            class="scwb-primary scwb-primary--<?php echo esc_attr($display); ?>"
            data-scwb-primary
            data-scwb-initial="<?php echo esc_attr($initial); ?>"
        >
            <header class="scwb-primary__header">
                <div>
                    <p class="scwb-primary__eyebrow">Sustainable Catalyst Workbench v2.9.0</p>
                    <h2><?php echo esc_html($atts['title']); ?></h2>
                    <p>
                        Select a studio to open its working interface. Calculations and records remain
                        separated by project while sharing the same Workbench environment.
                    </p>
                </div>
                <span class="scwb-primary__status">Unified Workbench selector</span>
            </header>

            <div class="scwb-primary__layout">
                <nav class="scwb-primary__nav" aria-label="Workbench studios" role="tablist">
                    <?php foreach ($available as $key => $studio) : ?>
                        <button
                            type="button"
                            class="scwb-primary__tab<?php echo $key === $initial ? ' is-active' : ''; ?>"
                            role="tab"
                            aria-selected="<?php echo $key === $initial ? 'true' : 'false'; ?>"
                            aria-controls="<?php echo esc_attr($instance . '-panel-' . $key); ?>"
                            data-scwb-primary-tab="<?php echo esc_attr($key); ?>"
                        >
                            <strong><?php echo esc_html($studio['label']); ?></strong>
                            <span><?php echo esc_html($studio['description']); ?></span>
                        </button>
                    <?php endforeach; ?>
                </nav>

                <div class="scwb-primary__workspace">
                    <?php foreach ($available as $key => $studio) : ?>
                        <section
                            id="<?php echo esc_attr($instance . '-panel-' . $key); ?>"
                            class="scwb-primary__panel<?php echo $key === $initial ? ' is-active' : ''; ?>"
                            role="tabpanel"
                            data-scwb-primary-panel="<?php echo esc_attr($key); ?>"
                            <?php echo $key === $initial ? '' : 'hidden'; ?>
                        >
                            <?php
                            echo do_shortcode(
                                sprintf(
                                    '[%s project="%s"]',
                                    esc_attr($studio['shortcode']),
                                    esc_attr($project)
                                )
                            );
                            ?>
                        </section>
                    <?php endforeach; ?>
                </div>
            </div>
        </section>
        <?php
        return ob_get_clean();
    }
}

SCWB_Primary_Shortcode_Repair::boot();
