<?php
/**
 * Sustainable Catalyst Prototyping Workbench v2.6.0.
 * Multi-Language Engineering Runtime Studio.
 */
if (!defined('ABSPATH')) { exit; }

if (!class_exists('SCWB_V260_Multilanguage_Runtime')) {
final class SCWB_V260_Multilanguage_Runtime {
    const VERSION = '2.6.0';
    const HANDLE = 'scwb-v260';
    private static $assets_loaded = false;

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_shortcodes'));
        add_filter('do_shortcode_tag', array(__CLASS__, 'append_suite'), 19, 4);
    }

    public static function register_shortcodes() {
        $shortcodes = array(
            'sc_workbench_multilanguage_runtime' => 'runtime',
            'sc_workbench_language_equivalence' => 'equivalence',
            'sc_workbench_numerical_benchmark' => 'benchmark',
            'sc_workbench_runtime_project_generator' => 'templates',
            'sc_workbench_reproducibility_validator' => 'reproducibility',
            'sc_workbench_execution_audit' => 'audit',
        );
        foreach ($shortcodes as $tag => $panel) {
            add_shortcode($tag, function ($atts = array()) use ($panel) {
                return SCWB_V260_Multilanguage_Runtime::render_panel($panel, $atts);
            });
        }
    }

    public static function append_suite($output, $tag, $attr, $match) {
        $parents = array('sc_workbench_simulation_studio', 'sc_workbench_code_studio');
        if (!in_array($tag, $parents, true) || false !== strpos($output, 'data-scwb-v260-suite')) { return $output; }
        $project = isset($attr['project']) ? $attr['project'] : 'default';
        return $output . self::render_suite_launcher($project);
    }

    private static function enqueue_assets() {
        if (self::$assets_loaded) { return; }
        self::$assets_loaded = true;
        $plugin_file = defined('SCWB_V260_PLUGIN_FILE') ? SCWB_V260_PLUGIN_FILE : dirname(__DIR__) . '/sustainable-catalyst-workbench.php';
        $base_url = plugin_dir_url($plugin_file);
        wp_enqueue_style(self::HANDLE, $base_url . 'assets/css/sc-workbench-v260.css', array(), self::VERSION);
        wp_enqueue_script(self::HANDLE, $base_url . 'assets/js/sc-workbench-v260.js', array(), self::VERSION, true);
        wp_localize_script(self::HANDLE, 'SCWBV260', array(
            'version' => self::VERSION,
            'runnerDefaultUrl' => 'http://127.0.0.1:8787',
            'storagePrefix' => 'scwb-v260:',
        ));
    }

    private static function titles() {
        return array(
            'runtime' => __('Multi-Language Engineering Runtime Studio', 'sustainable-catalyst-workbench'),
            'equivalence' => __('Language Equivalence and Result Validation Studio', 'sustainable-catalyst-workbench'),
            'benchmark' => __('Numerical Stability and Runtime Benchmark Studio', 'sustainable-catalyst-workbench'),
            'templates' => __('Multi-Language Project Generator', 'sustainable-catalyst-workbench'),
            'reproducibility' => __('Cross-Runtime Reproducibility Validator', 'sustainable-catalyst-workbench'),
            'audit' => __('Local Execution Safety and Audit Studio', 'sustainable-catalyst-workbench'),
        );
    }

    public static function render_panel($panel, $atts = array()) {
        self::enqueue_assets();
        $titles = self::titles();
        $atts = shortcode_atts(array(
            'title' => isset($titles[$panel]) ? $titles[$panel] : __('Multi-Language Runtime Studio', 'sustainable-catalyst-workbench'),
            'project' => 'default',
            'display' => 'full',
        ), $atts);
        $project = sanitize_key($atts['project']) ?: 'default';
        $id = wp_unique_id('scwb-v260-');
        ob_start(); ?>
        <section id="<?php echo esc_attr($id); ?>" class="scwb-v260 scwb-v260--<?php echo esc_attr($panel); ?>" data-scwb-v260-panel="<?php echo esc_attr($panel); ?>" data-scwb-v260-project="<?php echo esc_attr($project); ?>">
            <header class="scwb-v260__header">
                <div><p class="scwb-v260__eyebrow"><?php esc_html_e('Sustainable Catalyst Prototyping Workbench · v2.6.0', 'sustainable-catalyst-workbench'); ?></p><h2><?php echo esc_html($atts['title']); ?></h2></div>
                <span class="scwb-v260__status" data-scwb-v260-status><?php esc_html_e('Browser-local by default', 'sustainable-catalyst-workbench'); ?></span>
            </header>
            <?php self::render_body($panel); ?>
            <p class="scwb-v260__boundary"><?php esc_html_e('Engineering and research support only. Local execution requires explicit pairing and consent. Review source code, numerical methods, dependencies, compiler flags, runtime versions, units, tolerances, output parsing, and platform-specific behavior before relying on results.', 'sustainable-catalyst-workbench'); ?></p>
        </section>
        <?php return ob_get_clean();
    }

    private static function field($label, $name, $type = 'text', $value = '', $placeholder = '', $wide = false) { ?>
        <label class="scwb-v260__field<?php echo $wide ? ' scwb-v260__field--wide' : ''; ?>"><span><?php echo esc_html($label); ?></span>
            <?php if ('textarea' === $type) : ?><textarea data-scwb-v260-field="<?php echo esc_attr($name); ?>" placeholder="<?php echo esc_attr($placeholder); ?>"><?php echo esc_textarea($value); ?></textarea>
            <?php else : ?><input type="<?php echo esc_attr($type); ?>" data-scwb-v260-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>" placeholder="<?php echo esc_attr($placeholder); ?>"><?php endif; ?>
        </label>
    <?php }

    private static function select($label, $name, $options, $wide = false) { ?>
        <label class="scwb-v260__field<?php echo $wide ? ' scwb-v260__field--wide' : ''; ?>"><span><?php echo esc_html($label); ?></span><select data-scwb-v260-field="<?php echo esc_attr($name); ?>">
            <?php foreach ($options as $value => $text) : ?><option value="<?php echo esc_attr($value); ?>"><?php echo esc_html($text); ?></option><?php endforeach; ?>
        </select></label>
    <?php }

    private static function actions($primary = 'Run analysis', $extra = '') { ?>
        <div class="scwb-v260__actions">
            <button type="button" class="scwb-v260__button scwb-v260__button--primary" data-scwb-v260-action="analyze"><?php echo esc_html($primary); ?></button>
            <?php if ($extra) : ?><button type="button" class="scwb-v260__button" data-scwb-v260-action="<?php echo esc_attr($extra); ?>"><?php esc_html_e('Connect local runner', 'sustainable-catalyst-workbench'); ?></button><?php endif; ?>
            <button type="button" class="scwb-v260__button" data-scwb-v260-action="save"><?php esc_html_e('Save locally', 'sustainable-catalyst-workbench'); ?></button>
            <button type="button" class="scwb-v260__button" data-scwb-v260-action="export"><?php esc_html_e('Export JSON', 'sustainable-catalyst-workbench'); ?></button>
        </div>
        <div class="scwb-v260__results" data-scwb-v260-results aria-live="polite"><p><?php esc_html_e('Enter the project or validation inputs, then run the analysis.', 'sustainable-catalyst-workbench'); ?></p></div>
    <?php }

    private static function language_options() {
        return array('python' => 'Python', 'javascript' => 'JavaScript / Node.js', 'r' => 'R', 'sql' => 'SQL / SQLite', 'go' => 'Go', 'c' => 'C11', 'cpp' => 'C++17', 'rust' => 'Rust', 'haskell' => 'Haskell', 'assembly' => 'Assembly profile');
    }

    private static function render_body($panel) {
        if ('runtime' === $panel) { ?>
            <div class="scwb-v260__grid">
                <?php self::field('Runner URL', 'runner_url', 'url', 'http://127.0.0.1:8787'); ?>
                <?php self::field('One-time pairing code', 'pairing_code', 'text', '', 'Six digits'); ?>
                <?php self::select('Primary language', 'language', self::language_options()); ?>
                <?php self::select('Execution mode', 'execution_mode', array('discovery' => 'Discovery only', 'native' => 'Paired local execution')); ?>
                <?php self::field('Source filename', 'filename', 'text', 'main.py'); ?>
                <?php self::field('Maximum duration (seconds)', 'timeout_seconds', 'number', '8'); ?>
                <?php self::field('Source code', 'source', 'textarea', "print(sum(i*i for i in range(10)))", 'Trusted local source only', true); ?>
            </div>
            <?php self::actions('Inspect runtime plan', 'connect');
        } elseif ('equivalence' === $panel) { ?>
            <div class="scwb-v260__grid">
                <?php self::select('Engineering calculation', 'calculation', array('energy' => 'Energy: E = P × t', 'quadratic' => 'Quadratic roots', 'dot_product' => 'Vector dot product', 'linear_regression' => 'Linear regression')); ?>
                <?php self::field('Inputs (JSON)', 'inputs', 'textarea', '{"power_kw":2.5,"hours":8}', 'Calculation inputs', true); ?>
                <?php self::field('Runtime outputs (JSON)', 'outputs', 'textarea', '{"python":20,"javascript":20,"go":20}', 'Language-to-output mapping', true); ?>
                <?php self::field('Absolute tolerance', 'absolute_tolerance', 'number', '0.000001'); ?>
                <?php self::field('Relative tolerance', 'relative_tolerance', 'number', '0.000001'); ?>
            </div>
            <?php self::actions('Compare language results');
        } elseif ('benchmark' === $panel) { ?>
            <div class="scwb-v260__grid">
                <?php self::select('Benchmark', 'benchmark', array('cancellation' => 'Catastrophic cancellation', 'summation' => 'Naive vs Kahan summation', 'dot_product' => 'Dot-product accumulation')); ?>
                <?php self::field('Values (comma-separated)', 'values', 'textarea', '10000000000000000,1,-10000000000000000', 'Numeric values', true); ?>
                <?php self::field('Repeat count', 'repeats', 'number', '1000'); ?>
                <?php self::select('Precision target', 'precision', array('float64' => 'IEEE 754 float64', 'decimal' => 'Decimal reference')); ?>
            </div>
            <?php self::actions('Run numerical benchmark');
        } elseif ('templates' === $panel) { ?>
            <div class="scwb-v260__grid">
                <?php self::select('Language', 'language', self::language_options()); ?>
                <?php self::select('Project template', 'template', array('engineering_calculation' => 'Engineering calculation', 'csv_analysis' => 'CSV analysis', 'simulation_step' => 'Simulation time step', 'unit_test' => 'Calculation with tests')); ?>
                <?php self::field('Project name', 'project_name', 'engineering-runtime-example'); ?>
                <?php self::field('Calculation expression', 'expression', 'text', 'power_kw * hours'); ?>
                <?php self::field('Dependencies / notes', 'dependencies', 'textarea', '', 'One dependency or requirement per line', true); ?>
            </div>
            <?php self::actions('Generate project files');
        } elseif ('reproducibility' === $panel) { ?>
            <div class="scwb-v260__grid">
                <?php self::field('Execution records (JSON)', 'records', 'textarea', '[{"language":"python","runtime":"3.12","output":"20.000000","duration_ms":5},{"language":"go","runtime":"1.24","output":"20","duration_ms":18}]', 'Cross-runtime records', true); ?>
                <?php self::select('Output comparison', 'comparison_mode', array('numeric' => 'Numeric tolerance', 'exact' => 'Exact normalized text', 'json' => 'Canonical JSON')); ?>
                <?php self::field('Tolerance', 'tolerance', 'number', '0.000001'); ?>
                <?php self::field('Required languages', 'required_languages', 'text', 'python,go'); ?>
            </div>
            <?php self::actions('Validate reproducibility');
        } else { ?>
            <div class="scwb-v260__grid">
                <?php self::select('Language', 'language', self::language_options()); ?>
                <?php self::field('Source size (bytes)', 'source_bytes', 'number', '2048'); ?>
                <?php self::field('Requested timeout (seconds)', 'timeout_seconds', 'number', '8'); ?>
                <?php self::field('Expected output size (bytes)', 'output_bytes', 'number', '4096'); ?>
                <?php self::select('Filesystem mode', 'filesystem_mode', array('temporary' => 'Temporary isolated directory', 'project' => 'Project directory', 'unrestricted' => 'Unrestricted')); ?>
                <?php self::select('Network access', 'network_access', array('disabled' => 'Disabled', 'required' => 'Required')); ?>
                <?php self::select('Explicit consent', 'consent', array('yes' => 'Yes', 'no' => 'No')); ?>
            </div>
            <?php self::actions('Evaluate execution boundary');
        }
    }

    public static function render_suite_launcher($project = 'default') {
        self::enqueue_assets();
        ob_start(); ?>
        <aside class="scwb-v260__suite" data-scwb-v260-suite>
            <p><strong><?php esc_html_e('Multi-Language Engineering Runtime Studio', 'sustainable-catalyst-workbench'); ?></strong></p>
            <p><?php esc_html_e('Generate equivalent engineering calculations, inspect local runtimes, compare numerical behavior, and validate reproducibility across languages.', 'sustainable-catalyst-workbench'); ?></p>
            <code>[sc_workbench_multilanguage_runtime project="<?php echo esc_attr(sanitize_key($project) ?: 'default'); ?>"]</code>
        </aside>
        <?php return ob_get_clean();
    }
}
SCWB_V260_Multilanguage_Runtime::boot();
}
