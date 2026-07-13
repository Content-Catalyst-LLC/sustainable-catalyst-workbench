<?php
/**
 * Sustainable Catalyst Prototyping Workbench v2.7.0.
 * Scientific Visualization and Engineering Dashboard Studio.
 */
if (!defined('ABSPATH')) { exit; }

if (!class_exists('SCWB_V270_Visualization_Dashboard')) {
final class SCWB_V270_Visualization_Dashboard {
    const VERSION = '2.7.0';
    const HANDLE = 'scwb-v270';
    private static $assets_loaded = false;

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_shortcodes'));
        add_filter('do_shortcode_tag', array(__CLASS__, 'append_suite'), 20, 4);
    }

    public static function register_shortcodes() {
        $shortcodes = array(
            'sc_workbench_scientific_visualization' => 'visualization',
            'sc_workbench_engineering_dashboard' => 'dashboard',
            'sc_workbench_interactive_chart_studio' => 'interactive',
            'sc_workbench_validation_overlay' => 'validation',
            'sc_workbench_system_state_view' => 'state',
            'sc_workbench_visual_export_accessibility' => 'export',
        );
        foreach ($shortcodes as $tag => $panel) {
            add_shortcode($tag, function ($atts = array()) use ($panel) {
                return SCWB_V270_Visualization_Dashboard::render_panel($panel, $atts);
            });
        }
    }

    public static function append_suite($output, $tag, $attr, $match) {
        $parents = array('sc_workbench_simulation_studio', 'sc_workbench_instrumentation_studio', 'sc_workbench_multilanguage_runtime');
        if (!in_array($tag, $parents, true) || false !== strpos($output, 'data-scwb-v270-suite')) { return $output; }
        $project = isset($attr['project']) ? $attr['project'] : 'default';
        return $output . self::render_suite_launcher($project);
    }

    private static function enqueue_assets() {
        if (self::$assets_loaded) { return; }
        self::$assets_loaded = true;
        $plugin_file = defined('SCWB_V270_PLUGIN_FILE') ? SCWB_V270_PLUGIN_FILE : dirname(__DIR__) . '/sustainable-catalyst-workbench.php';
        $base_url = plugin_dir_url($plugin_file);
        wp_enqueue_style(self::HANDLE, $base_url . 'assets/css/sc-workbench-v270.css', array(), self::VERSION);
        wp_enqueue_script(self::HANDLE, $base_url . 'assets/js/sc-workbench-v270.js', array(), self::VERSION, true);
        wp_localize_script(self::HANDLE, 'SCWBV270', array(
            'version' => self::VERSION,
            'runnerDefaultUrl' => 'http://127.0.0.1:8787',
            'storagePrefix' => 'scwb-v270:',
        ));
    }

    private static function titles() {
        return array(
            'visualization' => __('Scientific Visualization Studio', 'sustainable-catalyst-workbench'),
            'dashboard' => __('Engineering Dashboard Studio', 'sustainable-catalyst-workbench'),
            'interactive' => __('Interactive Parameter and Chart Studio', 'sustainable-catalyst-workbench'),
            'validation' => __('Validation Overlay and Uncertainty Studio', 'sustainable-catalyst-workbench'),
            'state' => __('Engineering System-State View', 'sustainable-catalyst-workbench'),
            'export' => __('Visual Export and Accessibility Studio', 'sustainable-catalyst-workbench'),
        );
    }

    public static function render_panel($panel, $atts = array()) {
        self::enqueue_assets();
        $titles = self::titles();
        $atts = shortcode_atts(array(
            'title' => isset($titles[$panel]) ? $titles[$panel] : __('Scientific Visualization Studio', 'sustainable-catalyst-workbench'),
            'project' => 'default',
            'display' => 'full',
        ), $atts);
        $project = sanitize_key($atts['project']) ?: 'default';
        $id = wp_unique_id('scwb-v270-');
        ob_start(); ?>
        <section id="<?php echo esc_attr($id); ?>" class="scwb-v270 scwb-v270--<?php echo esc_attr($panel); ?>" data-scwb-v270-panel="<?php echo esc_attr($panel); ?>" data-scwb-v270-project="<?php echo esc_attr($project); ?>">
            <header class="scwb-v270__header">
                <div>
                    <p class="scwb-v270__eyebrow"><?php esc_html_e('Sustainable Catalyst Prototyping Workbench · v2.7.0', 'sustainable-catalyst-workbench'); ?></p>
                    <h2><?php echo esc_html($atts['title']); ?></h2>
                </div>
                <span class="scwb-v270__status" data-scwb-v270-status><?php esc_html_e('Browser-local visualization', 'sustainable-catalyst-workbench'); ?></span>
            </header>
            <?php self::render_body($panel); ?>
            <p class="scwb-v270__boundary"><?php esc_html_e('Scientific and engineering support only. Verify source data, units, sampling, transformations, axis scales, thresholds, uncertainty assumptions, visual encodings, accessible descriptions, and exported figures before using a visualization as evidence or in safety-critical work.', 'sustainable-catalyst-workbench'); ?></p>
        </section>
        <?php return ob_get_clean();
    }

    private static function field($label, $name, $type = 'text', $value = '', $placeholder = '', $wide = false, $attributes = '') { ?>
        <label class="scwb-v270__field<?php echo $wide ? ' scwb-v270__field--wide' : ''; ?>">
            <span><?php echo esc_html($label); ?></span>
            <?php if ('textarea' === $type) : ?>
                <textarea data-scwb-v270-field="<?php echo esc_attr($name); ?>" placeholder="<?php echo esc_attr($placeholder); ?>" <?php echo $attributes; ?>><?php echo esc_textarea($value); ?></textarea>
            <?php else : ?>
                <input type="<?php echo esc_attr($type); ?>" data-scwb-v270-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>" placeholder="<?php echo esc_attr($placeholder); ?>" <?php echo $attributes; ?>>
            <?php endif; ?>
        </label>
    <?php }

    private static function select($label, $name, $options, $wide = false) { ?>
        <label class="scwb-v270__field<?php echo $wide ? ' scwb-v270__field--wide' : ''; ?>">
            <span><?php echo esc_html($label); ?></span>
            <select data-scwb-v270-field="<?php echo esc_attr($name); ?>">
                <?php foreach ($options as $value => $text) : ?><option value="<?php echo esc_attr($value); ?>"><?php echo esc_html($text); ?></option><?php endforeach; ?>
            </select>
        </label>
    <?php }

    private static function actions($primary = 'Render visualization', $connect = false) { ?>
        <div class="scwb-v270__actions">
            <button type="button" class="scwb-v270__button scwb-v270__button--primary" data-scwb-v270-action="analyze"><?php echo esc_html($primary); ?></button>
            <?php if ($connect) : ?><button type="button" class="scwb-v270__button" data-scwb-v270-action="connect"><?php esc_html_e('Connect local runner', 'sustainable-catalyst-workbench'); ?></button><?php endif; ?>
            <button type="button" class="scwb-v270__button" data-scwb-v270-action="save"><?php esc_html_e('Save locally', 'sustainable-catalyst-workbench'); ?></button>
            <button type="button" class="scwb-v270__button" data-scwb-v270-action="export-json"><?php esc_html_e('Export JSON', 'sustainable-catalyst-workbench'); ?></button>
            <button type="button" class="scwb-v270__button" data-scwb-v270-action="export-csv"><?php esc_html_e('Export CSV', 'sustainable-catalyst-workbench'); ?></button>
            <button type="button" class="scwb-v270__button" data-scwb-v270-action="export-svg"><?php esc_html_e('Export SVG', 'sustainable-catalyst-workbench'); ?></button>
            <button type="button" class="scwb-v270__button" data-scwb-v270-action="export-png"><?php esc_html_e('Export PNG', 'sustainable-catalyst-workbench'); ?></button>
        </div>
        <div class="scwb-v270__workspace">
            <div class="scwb-v270__chart" data-scwb-v270-chart role="img" aria-label="Visualization preview"><p><?php esc_html_e('Enter data and render a visualization.', 'sustainable-catalyst-workbench'); ?></p></div>
            <div class="scwb-v270__results" data-scwb-v270-results aria-live="polite"><p><?php esc_html_e('A structured analysis record will appear here.', 'sustainable-catalyst-workbench'); ?></p></div>
        </div>
    <?php }

    private static function render_body($panel) {
        if ('visualization' === $panel) { ?>
            <div class="scwb-v270__grid">
                <?php self::field('Figure title', 'title', 'text', 'Sensor response over time'); ?>
                <?php self::select('Visualization type', 'chart_type', array('line' => 'Time-series line', 'scatter' => 'Scatter', 'bar' => 'Bar', 'histogram' => 'Histogram', 'spectrum' => 'Frequency spectrum', 'spatial' => 'Spatial x/y')); ?>
                <?php self::field('X-axis label', 'x_label', 'text', 'Time (s)'); ?>
                <?php self::field('Y-axis label', 'y_label', 'text', 'Signal'); ?>
                <?php self::field('Units', 'units', 'text', 'V'); ?>
                <?php self::field('Histogram bins / spectrum limit', 'bins', 'number', '12', '', false, 'min="2" max="100"'); ?>
                <?php self::field('CSV data', 'data', 'textarea', "x,y\n0,0.10\n1,0.45\n2,0.88\n3,1.12\n4,1.03\n5,0.79", 'Header row followed by numeric data', true); ?>
            </div>
            <?php self::actions('Render scientific figure', true);
        } elseif ('dashboard' === $panel) { ?>
            <div class="scwb-v270__grid">
                <?php self::field('Dashboard title', 'title', 'text', 'Prototype health dashboard'); ?>
                <?php self::select('Layout density', 'density', array('comfortable' => 'Comfortable', 'compact' => 'Compact')); ?>
                <?php self::field('Metrics JSON', 'metrics', 'textarea', '[{"key":"temperature","label":"Temperature","value":42.4,"units":"°C","warning_high":55,"critical_high":70,"target":40},{"key":"voltage","label":"Supply voltage","value":4.94,"units":"V","warning_low":4.75,"warning_high":5.25,"critical_low":4.5,"critical_high":5.5,"target":5},{"key":"latency","label":"Control latency","value":18,"units":"ms","warning_high":25,"critical_high":50,"target":15}]', 'Array of metric records', true); ?>
                <?php self::field('Recent trend values', 'trend', 'textarea', '40,41,42,44,43,42.4', 'Comma-separated values for a sparkline', true); ?>
            </div>
            <?php self::actions('Build engineering dashboard');
        } elseif ('interactive' === $panel) { ?>
            <div class="scwb-v270__grid">
                <?php self::field('Figure title', 'title', 'text', 'Interactive system response'); ?>
                <?php self::select('Model', 'model', array('first_order' => 'First-order response', 'sine' => 'Sine wave', 'linear' => 'Linear', 'quadratic' => 'Quadratic')); ?>
                <?php self::field('Parameter A', 'parameter_a', 'range', '1', '', false, 'min="-10" max="10" step="0.1"'); ?>
                <?php self::field('Parameter B', 'parameter_b', 'range', '2', '', false, 'min="-10" max="10" step="0.1"'); ?>
                <?php self::field('Parameter C', 'parameter_c', 'range', '0', '', false, 'min="-10" max="10" step="0.1"'); ?>
                <?php self::field('X minimum', 'x_min', 'number', '0'); ?>
                <?php self::field('X maximum', 'x_max', 'number', '10'); ?>
                <?php self::field('Samples', 'samples', 'number', '101', '', false, 'min="10" max="1000"'); ?>
            </div>
            <?php self::actions('Update parameterized chart');
        } elseif ('validation' === $panel) { ?>
            <div class="scwb-v270__grid">
                <?php self::field('Figure title', 'title', 'text', 'Observed vs modeled response'); ?>
                <?php self::field('Sigma multiplier', 'sigma_multiplier', 'number', '1.96', '', false, 'min="0.1" max="10" step="0.01"'); ?>
                <?php self::field('Acceptance RMSE', 'rmse_limit', 'number', '0.2', '', false, 'min="0" step="0.001"'); ?>
                <?php self::field('CSV data', 'data', 'textarea', "x,observed,predicted,uncertainty\n0,0.10,0.08,0.05\n1,0.45,0.42,0.05\n2,0.88,0.84,0.06\n3,1.12,1.08,0.07\n4,1.03,1.00,0.06\n5,0.79,0.82,0.05", 'x, observed, predicted, uncertainty', true); ?>
            </div>
            <?php self::actions('Render validation overlay');
        } elseif ('state' === $panel) { ?>
            <div class="scwb-v270__grid">
                <?php self::field('System title', 'title', 'text', 'Embedded monitoring system'); ?>
                <?php self::field('Nodes JSON', 'nodes', 'textarea', '[{"id":"sensor","label":"Sensor","state":"normal","value":42.4,"units":"°C"},{"id":"controller","label":"Controller","state":"normal"},{"id":"actuator","label":"Actuator","state":"warning","value":78,"units":"%"},{"id":"gateway","label":"Gateway","state":"normal"}]', 'Node records', true); ?>
                <?php self::field('Edges JSON', 'edges', 'textarea', '[{"source":"sensor","target":"controller","relation":"measures"},{"source":"controller","target":"actuator","relation":"commands"},{"source":"controller","target":"gateway","relation":"publishes"}]', 'Directed edge records', true); ?>
            </div>
            <?php self::actions('Render system-state view');
        } else { ?>
            <div class="scwb-v270__grid">
                <?php self::field('Runner URL', 'runner_url', 'url', 'http://127.0.0.1:8787'); ?>
                <?php self::field('One-time pairing code', 'pairing_code', 'text', '', 'Six digits'); ?>
                <?php self::field('Figure title', 'title', 'text', 'Engineering figure'); ?>
                <?php self::select('Chart type', 'chart_type', array('line' => 'Line', 'scatter' => 'Scatter', 'bar' => 'Bar', 'histogram' => 'Histogram', 'spectrum' => 'Spectrum', 'state' => 'System state')); ?>
                <?php self::field('X-axis label', 'x_label', 'text', 'Time'); ?>
                <?php self::field('Y-axis label', 'y_label', 'text', 'Measurement'); ?>
                <?php self::field('Units', 'units', 'text', ''); ?>
                <?php self::field('Values', 'values', 'textarea', '0.10,0.45,0.88,1.12,1.03,0.79', 'Comma-separated values', true); ?>
            </div>
            <?php self::actions('Generate accessible figure record', true);
        }
    }

    public static function render_suite_launcher($project = 'default') {
        self::enqueue_assets();
        ob_start(); ?>
        <aside class="scwb-v270__suite" data-scwb-v270-suite>
            <p><strong><?php esc_html_e('Scientific Visualization and Engineering Dashboard Studio', 'sustainable-catalyst-workbench'); ?></strong></p>
            <p><?php esc_html_e('Turn simulation, instrumentation, runtime, and validation records into auditable scientific figures, dashboards, uncertainty overlays, system-state views, and accessible exports.', 'sustainable-catalyst-workbench'); ?></p>
            <code>[sc_workbench_scientific_visualization project="<?php echo esc_attr(sanitize_key($project) ?: 'default'); ?>"]</code>
        </aside>
        <?php return ob_get_clean();
    }
}
SCWB_V270_Visualization_Dashboard::boot();
}
