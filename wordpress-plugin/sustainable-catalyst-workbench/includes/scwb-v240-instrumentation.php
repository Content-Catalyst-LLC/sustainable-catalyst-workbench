<?php
/**
 * Sustainable Catalyst Prototyping Workbench v2.4.0.
 * Instrumentation, Data Acquisition, and Signal Analysis Studio.
 */
if (!defined('ABSPATH')) { exit; }

if (!class_exists('SCWB_V240_Instrumentation')) {
final class SCWB_V240_Instrumentation {
    const VERSION = '2.4.0';
    const HANDLE = 'scwb-v240';
    private static $assets_loaded = false;

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_shortcodes'));
        add_filter('do_shortcode_tag', array(__CLASS__, 'append_suite'), 17, 4);
    }

    public static function register_shortcodes() {
        $shortcodes = array(
            'sc_workbench_instrumentation_studio' => 'instrumentation',
            'sc_workbench_data_acquisition' => 'acquisition',
            'sc_workbench_signal_analysis' => 'signal',
            'sc_workbench_frequency_analysis' => 'frequency',
            'sc_workbench_calibration_uncertainty' => 'calibration',
            'sc_workbench_measurement_validation' => 'validation',
        );
        foreach ($shortcodes as $tag => $panel) {
            add_shortcode($tag, function ($atts = array()) use ($panel) {
                return SCWB_V240_Instrumentation::render_panel($panel, $atts);
            });
        }
    }

    public static function append_suite($output, $tag, $attr, $match) {
        $parents = array('sc_workbench_hardware_studio', 'sc_workbench_robotics_studio');
        if (!in_array($tag, $parents, true) || false !== strpos($output, 'data-scwb-v240-suite')) {
            return $output;
        }
        $project = isset($attr['project']) ? $attr['project'] : 'default';
        return $output . self::render_suite_launcher($project);
    }

    private static function enqueue_assets() {
        if (self::$assets_loaded) { return; }
        self::$assets_loaded = true;
        $plugin_file = defined('SCWB_V240_PLUGIN_FILE') ? SCWB_V240_PLUGIN_FILE : dirname(__DIR__) . '/sustainable-catalyst-workbench.php';
        $base_url = plugin_dir_url($plugin_file);
        wp_enqueue_style(self::HANDLE, $base_url . 'assets/css/sc-workbench-v240.css', array(), self::VERSION);
        wp_enqueue_script(self::HANDLE, $base_url . 'assets/js/sc-workbench-v240.js', array(), self::VERSION, true);
        wp_localize_script(self::HANDLE, 'SCWBV240', array(
            'version' => self::VERSION,
            'runnerDefaultUrl' => 'http://127.0.0.1:8787',
            'storagePrefix' => 'scwb-v240:',
            'labels' => array(
                'saved' => __('Saved locally', 'sustainable-catalyst-workbench'),
                'ready' => __('Ready', 'sustainable-catalyst-workbench'),
                'invalid' => __('Review required', 'sustainable-catalyst-workbench'),
            ),
        ));
    }

    private static function titles() {
        return array(
            'instrumentation' => __('Instrumentation Studio', 'sustainable-catalyst-workbench'),
            'acquisition' => __('Data Acquisition Planning Studio', 'sustainable-catalyst-workbench'),
            'signal' => __('Time-Domain Signal Analysis Studio', 'sustainable-catalyst-workbench'),
            'frequency' => __('Frequency-Domain and Spectrum Studio', 'sustainable-catalyst-workbench'),
            'calibration' => __('Calibration and Measurement Uncertainty Studio', 'sustainable-catalyst-workbench'),
            'validation' => __('Measurement Campaign Validation Studio', 'sustainable-catalyst-workbench'),
        );
    }

    public static function render_panel($panel, $atts = array()) {
        self::enqueue_assets();
        $titles = self::titles();
        $atts = shortcode_atts(array(
            'title' => isset($titles[$panel]) ? $titles[$panel] : __('Instrumentation Studio', 'sustainable-catalyst-workbench'),
            'project' => 'default',
            'display' => 'full',
        ), $atts);
        $project = sanitize_key($atts['project']) ?: 'default';
        $id = wp_unique_id('scwb-v240-');
        ob_start(); ?>
        <section id="<?php echo esc_attr($id); ?>" class="scwb-v240 scwb-v240--<?php echo esc_attr($panel); ?>" data-scwb-v240-panel="<?php echo esc_attr($panel); ?>" data-scwb-v240-project="<?php echo esc_attr($project); ?>">
            <header class="scwb-v240__header">
                <div>
                    <p class="scwb-v240__eyebrow"><?php esc_html_e('Sustainable Catalyst Prototyping Workbench · v2.4.0', 'sustainable-catalyst-workbench'); ?></p>
                    <h2><?php echo esc_html($atts['title']); ?></h2>
                </div>
                <span class="scwb-v240__status" data-scwb-v240-status><?php esc_html_e('Browser-local', 'sustainable-catalyst-workbench'); ?></span>
            </header>
            <?php self::render_body($panel); ?>
            <p class="scwb-v240__boundary"><?php esc_html_e('Research and prototyping support only. Verify instrument ratings, isolation, grounding, probes, wiring, sampling assumptions, calibration traceability, uncertainty budgets, environmental limits, and all safety-critical measurements against the actual equipment and applicable standards.', 'sustainable-catalyst-workbench'); ?></p>
        </section>
        <?php return ob_get_clean();
    }

    private static function field($label, $name, $type = 'text', $value = '', $placeholder = '', $wide = false) { ?>
        <label class="scwb-v240__field<?php echo $wide ? ' scwb-v240__field--wide' : ''; ?>">
            <span><?php echo esc_html($label); ?></span>
            <?php if ('textarea' === $type) : ?>
                <textarea data-scwb-v240-field="<?php echo esc_attr($name); ?>" placeholder="<?php echo esc_attr($placeholder); ?>"><?php echo esc_textarea($value); ?></textarea>
            <?php else : ?>
                <input type="<?php echo esc_attr($type); ?>" data-scwb-v240-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>" placeholder="<?php echo esc_attr($placeholder); ?>">
            <?php endif; ?>
        </label>
    <?php }

    private static function select($label, $name, $options, $wide = false) { ?>
        <label class="scwb-v240__field<?php echo $wide ? ' scwb-v240__field--wide' : ''; ?>">
            <span><?php echo esc_html($label); ?></span>
            <select data-scwb-v240-field="<?php echo esc_attr($name); ?>">
                <?php foreach ($options as $value => $text) : ?>
                    <option value="<?php echo esc_attr($value); ?>"><?php echo esc_html($text); ?></option>
                <?php endforeach; ?>
            </select>
        </label>
    <?php }

    private static function actions($primary = 'Analyze') { ?>
        <div class="scwb-v240__actions">
            <button type="button" class="scwb-v240__button scwb-v240__button--primary" data-scwb-v240-action="analyze"><?php echo esc_html($primary); ?></button>
            <button type="button" class="scwb-v240__button" data-scwb-v240-action="save"><?php esc_html_e('Save locally', 'sustainable-catalyst-workbench'); ?></button>
            <button type="button" class="scwb-v240__button" data-scwb-v240-action="export"><?php esc_html_e('Export JSON', 'sustainable-catalyst-workbench'); ?></button>
        </div>
        <div class="scwb-v240__results" data-scwb-v240-results aria-live="polite"><p><?php esc_html_e('Enter the measurement or acquisition parameters, then run the analysis.', 'sustainable-catalyst-workbench'); ?></p></div>
    <?php }

    private static function render_body($panel) {
        if ('instrumentation' === $panel) { ?>
            <div class="scwb-v240__grid">
                <?php self::field('Instrument or sensor name', 'instrument_name', 'text', 'Pressure transducer'); ?>
                <?php self::select('Instrument type', 'instrument_type', array('voltage' => 'Voltage / analog sensor', 'current' => 'Current-loop sensor', 'temperature' => 'Temperature sensor', 'pressure' => 'Pressure sensor', 'accelerometer' => 'Accelerometer', 'other' => 'Other')); ?>
                <?php self::field('Engineering units', 'units', 'text', 'kPa'); ?>
                <?php self::field('Range minimum', 'range_min', 'number', '0'); ?>
                <?php self::field('Range maximum', 'range_max', 'number', '500'); ?>
                <?php self::field('Accuracy (% full scale)', 'accuracy_percent', 'number', '0.5'); ?>
                <?php self::field('ADC resolution (bits)', 'resolution_bits', 'number', '12'); ?>
                <?php self::field('Instrument bandwidth (Hz)', 'bandwidth_hz', 'number', '20'); ?>
                <?php self::field('Expected signal minimum', 'expected_min', 'number', '50'); ?>
                <?php self::field('Expected signal maximum', 'expected_max', 'number', '300'); ?>
                <?php self::field('Input / output interface', 'interface', 'text', '0–5 V'); ?>
                <?php self::select('Isolation required', 'isolation_required', array('no' => 'No / not yet determined', 'yes' => 'Yes')); ?>
            </div>
            <?php self::actions('Review instrumentation');
        } elseif ('acquisition' === $panel) { ?>
            <div class="scwb-v240__grid">
                <?php self::field('Acquisition name', 'acquisition_name', 'text', 'Vibration test run'); ?>
                <?php self::field('Channel count', 'channels', 'number', '4'); ?>
                <?php self::field('Sample rate per channel (Hz)', 'sample_rate', 'number', '2000'); ?>
                <?php self::field('Duration (seconds)', 'duration', 'number', '60'); ?>
                <?php self::field('ADC bit depth', 'bit_depth', 'number', '16'); ?>
                <?php self::field('Storage overhead (%)', 'overhead_percent', 'number', '15'); ?>
                <?php self::field('Expected maximum signal frequency (Hz)', 'expected_max_frequency', 'number', '500'); ?>
                <?php self::field('Buffer duration (seconds)', 'buffer_seconds', 'number', '2'); ?>
                <?php self::select('Channel sampling', 'sampling_mode', array('simultaneous' => 'Simultaneous', 'multiplexed' => 'Multiplexed / scanned')); ?>
                <?php self::select('Timestamp source', 'timestamp_source', array('hardware' => 'Hardware clock', 'system' => 'System clock', 'external' => 'External reference / PPS')); ?>
                <?php self::field('Anti-alias filter cutoff (Hz)', 'filter_cutoff', 'number', '800'); ?>
                <?php self::field('Available storage (MB)', 'available_storage_mb', 'number', '1024'); ?>
            </div>
            <?php self::actions('Plan acquisition');
        } elseif ('signal' === $panel) { ?>
            <div class="scwb-v240__grid">
                <?php self::field('Sample rate (Hz)', 'sample_rate', 'number', '100'); ?>
                <?php self::field('Moving-average window (samples)', 'filter_window', 'number', '5'); ?>
                <?php self::select('Detrending', 'detrend', array('mean' => 'Remove mean', 'linear' => 'Remove linear trend', 'none' => 'None')); ?>
                <?php self::field('Engineering units', 'units', 'text', 'V'); ?>
                <?php self::field('Time/value samples (CSV)', 'signal_csv', 'textarea', "time,value\n0.00,0.02\n0.01,0.61\n0.02,0.95\n0.03,0.58\n0.04,-0.01\n0.05,-0.62\n0.06,-0.98\n0.07,-0.57\n0.08,0.01", 'Paste time,value or one numeric value per line', true); ?>
            </div>
            <?php self::actions('Analyze signal');
        } elseif ('frequency' === $panel) { ?>
            <div class="scwb-v240__grid">
                <?php self::field('Sample rate (Hz)', 'sample_rate', 'number', '1000'); ?>
                <?php self::select('Window function', 'window', array('hann' => 'Hann', 'hamming' => 'Hamming', 'rectangular' => 'Rectangular')); ?>
                <?php self::field('Expected maximum frequency (Hz)', 'expected_max_frequency', 'number', '300'); ?>
                <?php self::field('Maximum FFT/DFT samples', 'max_samples', 'number', '1024'); ?>
                <?php self::field('Signal samples', 'frequency_samples', 'textarea', "0\n0.3090\n0.5878\n0.8090\n0.9511\n1\n0.9511\n0.8090\n0.5878\n0.3090\n0\n-0.3090\n-0.5878\n-0.8090\n-0.9511\n-1", 'Paste one numeric sample per line or a CSV value column', true); ?>
            </div>
            <?php self::actions('Compute spectrum');
        } elseif ('calibration' === $panel) { ?>
            <div class="scwb-v240__grid">
                <?php self::field('Calibration points (reference,observed)', 'calibration_csv', 'textarea', "reference,observed\n0,0.02\n25,24.91\n50,49.88\n75,74.96\n100,99.81", 'reference,observed', true); ?>
                <?php self::field('Uncertainty components (name,value,distribution)', 'uncertainty_csv', 'textarea', "reference standard,0.05,standard\nrepeatability,0.08,standard\nresolution,0.10,uniform\ntemperature effect,0.06,uniform", 'name,value,standard|uniform|triangular', true); ?>
                <?php self::field('Coverage factor k', 'coverage_factor', 'number', '2'); ?>
                <?php self::field('Calibration units', 'units', 'text', '°C'); ?>
                <?php self::select('Regression direction', 'regression_direction', array('observed_to_reference' => 'Correct observed → reference', 'reference_to_observed' => 'Model reference → observed')); ?>
                <?php self::field('Acceptance RMSE', 'acceptance_rmse', 'number', '0.25'); ?>
            </div>
            <?php self::actions('Fit calibration');
        } elseif ('validation' === $panel) { ?>
            <div class="scwb-v240__grid">
                <?php self::field('Expected sample rate (Hz)', 'expected_rate', 'number', '10'); ?>
                <?php self::field('Sample-rate tolerance (%)', 'rate_tolerance_percent', 'number', '2'); ?>
                <?php self::field('Maximum timing jitter (%)', 'max_jitter_percent', 'number', '10'); ?>
                <?php self::field('Minimum sample count', 'min_samples', 'number', '8'); ?>
                <?php self::field('Timestamped multi-channel data', 'measurement_csv', 'textarea', "time,temperature,pressure\n0.0,21.1,100.2\n0.1,21.2,100.1\n0.2,21.2,100.3\n0.3,21.3,100.2\n0.4,21.3,100.4\n0.5,21.4,100.3\n0.6,21.4,100.5\n0.7,21.5,100.4", 'time,channel_1,channel_2,...', true); ?>
                <?php self::field('Campaign notes', 'campaign_notes', 'textarea', '', 'Instrument IDs, environmental conditions, operator, reference clock, anomalies', true); ?>
            </div>
            <?php self::actions('Validate measurements');
        }
    }

    public static function render_suite_launcher($project = 'default') {
        self::enqueue_assets();
        $project = sanitize_key($project) ?: 'default';
        $modules = array(
            array('Instrumentation', 'Range, resolution, bandwidth, accuracy, interface, and isolation review.', '[sc_workbench_instrumentation_studio project="' . $project . '"]'),
            array('Data Acquisition', 'Sampling, Nyquist, throughput, buffering, storage, and timing planning.', '[sc_workbench_data_acquisition project="' . $project . '"]'),
            array('Signal Analysis', 'Time-domain statistics, drift, filtering, noise estimates, and previews.', '[sc_workbench_signal_analysis project="' . $project . '"]'),
            array('Frequency Analysis', 'Windowed spectrum, dominant frequencies, frequency resolution, and aliasing checks.', '[sc_workbench_frequency_analysis project="' . $project . '"]'),
            array('Calibration and Uncertainty', 'Linear calibration, residuals, uncertainty budgets, and expanded uncertainty.', '[sc_workbench_calibration_uncertainty project="' . $project . '"]'),
            array('Measurement Validation', 'Timestamp integrity, sample-rate accuracy, jitter, completeness, and channel statistics.', '[sc_workbench_measurement_validation project="' . $project . '"]'),
        );
        ob_start(); ?>
        <section class="scwb-v240 scwb-v240__suite" data-scwb-v240-suite data-scwb-v240-project="<?php echo esc_attr($project); ?>">
            <header class="scwb-v240__header"><div><p class="scwb-v240__eyebrow"><?php esc_html_e('Workbench v2.4.0', 'sustainable-catalyst-workbench'); ?></p><h2><?php esc_html_e('Instrumentation and Signal Analysis Modules', 'sustainable-catalyst-workbench'); ?></h2></div></header>
            <div class="scwb-v240__module-grid">
                <?php foreach ($modules as $module) : ?>
                    <article class="scwb-v240__module-card"><h3><?php echo esc_html($module[0]); ?></h3><p><?php echo esc_html($module[1]); ?></p><code><?php echo esc_html($module[2]); ?></code></article>
                <?php endforeach; ?>
            </div>
        </section>
        <?php return ob_get_clean();
    }
}
SCWB_V240_Instrumentation::boot();
}
