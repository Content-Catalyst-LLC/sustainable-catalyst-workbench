<?php
/**
 * Sustainable Catalyst Prototyping Workbench v2.8.0.
 * Experiment Automation and Reproducible Workflow Studio.
 */
if (!defined('ABSPATH')) { exit; }

if (!class_exists('SCWB_V280_Experiment_Automation')) {
final class SCWB_V280_Experiment_Automation {
    const VERSION = '2.8.0';
    const HANDLE = 'scwb-v280';
    private static $assets_loaded = false;

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_shortcodes'));
        add_filter('do_shortcode_tag', array(__CLASS__, 'append_suite'), 20, 4);
    }

    public static function register_shortcodes() {
        $shortcodes = array(
            'sc_workbench_experiment_automation' => 'automation',
            'sc_workbench_protocol_builder' => 'protocol',
            'sc_workbench_workflow_pipeline' => 'workflow',
            'sc_workbench_experiment_scheduler' => 'scheduler',
            'sc_workbench_version_checkpoint' => 'versioning',
            'sc_workbench_reproducibility_audit' => 'reproducibility',
        );
        foreach ($shortcodes as $tag => $panel) {
            add_shortcode($tag, function ($atts = array()) use ($panel) {
                return SCWB_V280_Experiment_Automation::render_panel($panel, $atts);
            });
        }
    }

    public static function append_suite($output, $tag, $attr, $match) {
        $parents = array('sc_workbench_scientific_visualization', 'sc_workbench_simulation_studio', 'sc_workbench_instrumentation_studio');
        if (!in_array($tag, $parents, true) || false !== strpos($output, 'data-scwb-v280-suite')) { return $output; }
        $project = isset($attr['project']) ? $attr['project'] : 'default';
        return $output . self::render_suite_launcher($project);
    }

    private static function enqueue_assets() {
        if (self::$assets_loaded) { return; }
        self::$assets_loaded = true;
        $plugin_file = defined('SCWB_V280_PLUGIN_FILE') ? SCWB_V280_PLUGIN_FILE : dirname(__DIR__) . '/sustainable-catalyst-workbench.php';
        $base_url = plugin_dir_url($plugin_file);
        wp_enqueue_style(self::HANDLE, $base_url . 'assets/css/sc-workbench-v280.css', array(), self::VERSION);
        wp_enqueue_script(self::HANDLE, $base_url . 'assets/js/sc-workbench-v280.js', array(), self::VERSION, true);
        wp_localize_script(self::HANDLE, 'SCWBV280', array(
            'version' => self::VERSION,
            'runnerDefaultUrl' => 'http://127.0.0.1:8787',
            'storagePrefix' => 'scwb-v280:',
        ));
    }

    private static function titles() {
        return array(
            'automation' => __('Experiment Automation Studio', 'sustainable-catalyst-workbench'),
            'protocol' => __('Structured Protocol Builder', 'sustainable-catalyst-workbench'),
            'workflow' => __('Reproducible Workflow Pipeline Studio', 'sustainable-catalyst-workbench'),
            'scheduler' => __('Experiment Schedule and Local Task Planner', 'sustainable-catalyst-workbench'),
            'versioning' => __('Dataset, Configuration, and Checkpoint Studio', 'sustainable-catalyst-workbench'),
            'reproducibility' => __('Reproducibility and Deviation Audit Studio', 'sustainable-catalyst-workbench'),
        );
    }

    public static function render_panel($panel, $atts = array()) {
        self::enqueue_assets();
        $titles = self::titles();
        $atts = shortcode_atts(array(
            'title' => isset($titles[$panel]) ? $titles[$panel] : __('Experiment Automation Studio', 'sustainable-catalyst-workbench'),
            'project' => 'default',
            'display' => 'full',
        ), $atts);
        $project = sanitize_key($atts['project']) ?: 'default';
        $id = wp_unique_id('scwb-v280-');
        ob_start(); ?>
        <section id="<?php echo esc_attr($id); ?>" class="scwb-v280 scwb-v280--<?php echo esc_attr($panel); ?>" data-scwb-v280-panel="<?php echo esc_attr($panel); ?>" data-scwb-v280-project="<?php echo esc_attr($project); ?>">
            <header class="scwb-v280__header">
                <div>
                    <p class="scwb-v280__eyebrow"><?php esc_html_e('Sustainable Catalyst Prototyping Workbench · v2.8.0', 'sustainable-catalyst-workbench'); ?></p>
                    <h2><?php echo esc_html($atts['title']); ?></h2>
                </div>
                <span class="scwb-v280__status" data-scwb-v280-status><?php esc_html_e('Browser-local workflow record', 'sustainable-catalyst-workbench'); ?></span>
            </header>
            <?php self::render_body($panel); ?>
            <p class="scwb-v280__boundary"><?php esc_html_e('Automation support does not replace laboratory supervision, equipment interlocks, operating procedures, human review, or applicable safety and quality systems. Validate protocols, dependencies, schedules, code, instruments, checkpoints, data lineage, and failure handling before unattended or consequential use.', 'sustainable-catalyst-workbench'); ?></p>
        </section>
        <?php return ob_get_clean();
    }

    private static function field($label, $name, $type = 'text', $value = '', $placeholder = '', $wide = false) { ?>
        <label class="scwb-v280__field<?php echo $wide ? ' scwb-v280__field--wide' : ''; ?>">
            <span><?php echo esc_html($label); ?></span>
            <?php if ('textarea' === $type) : ?>
                <textarea data-scwb-v280-field="<?php echo esc_attr($name); ?>" placeholder="<?php echo esc_attr($placeholder); ?>"><?php echo esc_textarea($value); ?></textarea>
            <?php else : ?>
                <input type="<?php echo esc_attr($type); ?>" data-scwb-v280-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>" placeholder="<?php echo esc_attr($placeholder); ?>">
            <?php endif; ?>
        </label>
    <?php }

    private static function select($label, $name, $options, $wide = false) { ?>
        <label class="scwb-v280__field<?php echo $wide ? ' scwb-v280__field--wide' : ''; ?>">
            <span><?php echo esc_html($label); ?></span>
            <select data-scwb-v280-field="<?php echo esc_attr($name); ?>">
                <?php foreach ($options as $value => $text) : ?><option value="<?php echo esc_attr($value); ?>"><?php echo esc_html($text); ?></option><?php endforeach; ?>
            </select>
        </label>
    <?php }

    private static function actions($primary = 'Evaluate workflow', $connect = false) { ?>
        <div class="scwb-v280__actions">
            <button type="button" class="scwb-v280__button scwb-v280__button--primary" data-scwb-v280-action="analyze"><?php echo esc_html($primary); ?></button>
            <?php if ($connect) : ?><button type="button" class="scwb-v280__button" data-scwb-v280-action="connect"><?php esc_html_e('Connect local runner', 'sustainable-catalyst-workbench'); ?></button><?php endif; ?>
            <button type="button" class="scwb-v280__button" data-scwb-v280-action="save"><?php esc_html_e('Save locally', 'sustainable-catalyst-workbench'); ?></button>
            <button type="button" class="scwb-v280__button" data-scwb-v280-action="export-json"><?php esc_html_e('Export record', 'sustainable-catalyst-workbench'); ?></button>
            <button type="button" class="scwb-v280__button" data-scwb-v280-action="export-bundle"><?php esc_html_e('Export bundle', 'sustainable-catalyst-workbench'); ?></button>
        </div>
        <div class="scwb-v280__workspace">
            <div class="scwb-v280__summary" data-scwb-v280-summary aria-live="polite"></div>
            <pre class="scwb-v280__result" data-scwb-v280-result>{}</pre>
        </div>
    <?php }

    private static function render_body($panel) {
        echo '<div class="scwb-v280__body"><div class="scwb-v280__form">';
        if ('automation' === $panel) {
            self::field('Experiment title', 'title', 'text', 'Automated sensor characterization');
            self::field('Objective', 'objective', 'textarea', 'Acquire repeated measurements, validate quality gates, analyze results, and produce a reproducible record.', '', true);
            self::field('Pipeline tasks (JSON)', 'tasks', 'textarea', '[{"id":"acquire","title":"Acquire data","duration":10,"dependencies":[],"resource":"instrument"},{"id":"validate","title":"Validate data","duration":5,"dependencies":["acquire"],"resource":"compute"},{"id":"analyze","title":"Analyze","duration":15,"dependencies":["validate"],"resource":"compute"}]', 'Array of task records', true);
            self::field('Checkpoint rules (JSON)', 'rules', 'textarea', '[{"key":"sample_count","operator":"gte","lower":100,"severity":"critical"},{"key":"missing_fraction","operator":"lte","upper":0.01,"severity":"critical"}]', '', true);
            self::field('Observed checkpoint values (JSON)', 'observed', 'textarea', '{"sample_count":120,"missing_fraction":0}', '', true);
            self::field('Runner URL', 'runner_url', 'url', 'http://127.0.0.1:8787');
            self::field('Pairing code', 'pairing_code', 'text', '', 'Six-digit code');
            self::actions('Build automation record', true);
        } elseif ('protocol' === $panel) {
            self::field('Protocol title', 'title', 'text', 'Sensor calibration protocol');
            self::field('Objective', 'objective', 'textarea', 'Establish a traceable calibration response across the operating range.', '', true);
            self::field('Materials, one per line', 'materials', 'textarea', "Reference source\nSensor under test\nAcquisition interface", '', true);
            self::field('Hazards and controls, one per line', 'hazards', 'textarea', "Electrical energy — isolate before rewiring\nThermal exposure — verify safe surface temperature", '', true);
            self::field('Protocol steps (JSON)', 'steps', 'textarea', '[{"id":"prepare","title":"Prepare apparatus","procedure":"Inspect and connect apparatus","duration":10,"dependencies":[],"outputs":["setup-photo"],"checkpoint":"Connections verified"},{"id":"measure","title":"Acquire references","procedure":"Collect repeated values","duration":30,"dependencies":["prepare"],"outputs":["calibration.csv"],"checkpoint":"Coverage and repeat count verified"}]', '', true);
            self::actions('Validate protocol');
        } elseif ('workflow' === $panel) {
            self::field('Workflow title', 'title', 'text', 'Acquisition and analysis pipeline');
            self::field('Workflow tasks (JSON)', 'tasks', 'textarea', '[{"id":"capture","title":"Capture","duration":20,"dependencies":[],"resource":"daq","retry":1},{"id":"clean","title":"Clean","duration":8,"dependencies":["capture"],"resource":"compute","retry":1},{"id":"model","title":"Model","duration":18,"dependencies":["clean"],"resource":"compute","retry":0},{"id":"report","title":"Report","duration":6,"dependencies":["model"],"resource":"compute","retry":0}]', '', true);
            self::actions('Plan workflow');
        } elseif ('scheduler' === $panel) {
            self::field('Schedule window (minutes)', 'window', 'number', '1440');
            self::field('Scheduled tasks (JSON)', 'schedule', 'textarea', '[{"id":"sample","start":0,"duration":2,"resource":"sensor","repeatEvery":60,"occurrences":12},{"id":"daily-export","start":720,"duration":10,"resource":"compute","occurrences":1}]', '', true);
            self::field('Runner URL', 'runner_url', 'url', 'http://127.0.0.1:8787');
            self::field('Pairing code', 'pairing_code', 'text', '', 'Six-digit code');
            self::actions('Evaluate schedule', true);
        } elseif ('versioning' === $panel) {
            self::field('Project ID', 'project_id', 'text', 'default');
            self::field('Dataset record (JSON)', 'dataset', 'textarea', '{"file":"measurements.csv","rows":120,"columns":["time","value"]}', '', true);
            self::field('Configuration (JSON)', 'configuration', 'textarea', '{"sample_rate_hz":10,"gain":2,"filter":"moving_average_5"}', '', true);
            self::field('Code revision', 'code_revision', 'text', 'git:main');
            self::field('Environment (JSON)', 'environment', 'textarea', '{"python":"3.12","platform":"local-runner"}', '', true);
            self::field('Checkpoint rules (JSON)', 'rules', 'textarea', '[{"key":"rows","operator":"gte","lower":100,"severity":"critical"},{"key":"status","operator":"equal","expected":"validated","severity":"critical"}]', '', true);
            self::field('Observed values (JSON)', 'observed', 'textarea', '{"rows":120,"status":"validated"}', '', true);
            self::actions('Create version manifest');
        } else {
            self::field('Run IDs, one per line', 'run_ids', 'textarea', "run-001\nrun-002\nrun-003", '', true);
            self::field('Dataset hashes, one per line', 'dataset_hashes', 'textarea', "dataset-a\ndataset-a\ndataset-a", '', true);
            self::field('Configuration hashes, one per line', 'configuration_hashes', 'textarea', "config-a\nconfig-a\nconfig-a", '', true);
            self::field('Code revisions, one per line', 'code_revisions', 'textarea', "abc123\nabc123\nabc123", '', true);
            self::field('Metrics (JSON)', 'metrics', 'textarea', '[{"key":"rmse","values":[1,1.002,0.999],"absoluteTolerance":0.01,"relativeTolerance":0.01}]', '', true);
            self::field('Deviations, one per line', 'deviations', 'textarea', '', 'Leave blank when none were recorded', true);
            self::actions('Compare reproducibility');
        }
        echo '</div></div>';
    }

    public static function render_suite_launcher($project) {
        self::enqueue_assets();
        ob_start(); ?>
        <aside class="scwb-v280__launcher" data-scwb-v280-suite>
            <p class="scwb-v280__eyebrow"><?php esc_html_e('Workbench v2.8.0 workflow layer', 'sustainable-catalyst-workbench'); ?></p>
            <h3><?php esc_html_e('Automate and reproduce this project', 'sustainable-catalyst-workbench'); ?></h3>
            <p><?php esc_html_e('Turn measurements, simulations, and visualizations into structured protocols, dependency-aware workflows, checkpoints, version manifests, deviation records, and reproducible experiment bundles.', 'sustainable-catalyst-workbench'); ?></p>
            <code>[sc_workbench_experiment_automation project="<?php echo esc_attr(sanitize_key($project) ?: 'default'); ?>"]</code>
        </aside>
        <?php return ob_get_clean();
    }
}
SCWB_V280_Experiment_Automation::boot();
}
