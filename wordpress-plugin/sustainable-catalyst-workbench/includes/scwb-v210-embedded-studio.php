<?php
/**
 * Sustainable Catalyst Prototyping Workbench v2.1.0.
 * Raspberry Pi, TinyML, and Embedded Device Studio.
 */

if (!defined('ABSPATH')) {
    exit;
}

if (!class_exists('SCWB_V210_Embedded_Studio')) {
    final class SCWB_V210_Embedded_Studio {
        const VERSION = '2.1.0';
        const HANDLE = 'scwb-v210';

        private static $assets_loaded = false;

        public static function boot() {
            add_action('init', array(__CLASS__, 'register_shortcodes'));
            add_filter('do_shortcode_tag', array(__CLASS__, 'append_embedded_suite'), 12, 4);
        }

        public static function register_shortcodes() {
            $shortcodes = array(
                'sc_workbench_embedded_device_studio' => 'device',
                'sc_workbench_raspberry_pi' => 'raspberry-pi',
                'sc_workbench_tinyml' => 'tinyml',
                'sc_workbench_sensor_calibration' => 'calibration',
                'sc_workbench_device_logs' => 'logs',
                'sc_workbench_embedded_board_catalog' => 'boards',
            );

            foreach ($shortcodes as $tag => $panel) {
                add_shortcode($tag, function ($atts = array()) use ($panel) {
                    return SCWB_V210_Embedded_Studio::render_panel($panel, $atts);
                });
            }
        }

        public static function append_embedded_suite($output, $tag, $attr, $match) {
            if ('sc_workbench_hardware_studio' !== $tag || false !== strpos($output, 'data-scwb-v210-suite')) {
                return $output;
            }

            $project = isset($attr['project']) ? $attr['project'] : 'default';
            return $output . self::render_suite_launcher($project);
        }

        private static function enqueue_assets() {
            if (self::$assets_loaded) {
                return;
            }
            self::$assets_loaded = true;

            $plugin_file = defined('SCWB_V210_PLUGIN_FILE')
                ? SCWB_V210_PLUGIN_FILE
                : dirname(__DIR__) . '/sustainable-catalyst-workbench.php';
            $base_url = plugin_dir_url($plugin_file);

            wp_enqueue_style(
                self::HANDLE,
                $base_url . 'assets/css/sc-workbench-v210.css',
                array(),
                self::VERSION
            );
            wp_enqueue_script(
                self::HANDLE,
                $base_url . 'assets/js/sc-workbench-v210.js',
                array(),
                self::VERSION,
                true
            );
            wp_localize_script(self::HANDLE, 'SCWBV210', array(
                'version' => self::VERSION,
                'runnerDefaultUrl' => 'http://127.0.0.1:8787',
                'storagePrefix' => 'scwb-v210:',
                'v200StoragePrefix' => 'scwb-v200:',
                'labels' => array(
                    'saved' => __('Saved locally', 'sustainable-catalyst-workbench'),
                    'ready' => __('Ready', 'sustainable-catalyst-workbench'),
                    'runnerOffline' => __('Local runner unavailable', 'sustainable-catalyst-workbench'),
                ),
            ));
        }

        private static function titles() {
            return array(
                'device' => __('Embedded Device Studio', 'sustainable-catalyst-workbench'),
                'raspberry-pi' => __('Raspberry Pi Studio', 'sustainable-catalyst-workbench'),
                'tinyml' => __('TinyML Studio', 'sustainable-catalyst-workbench'),
                'calibration' => __('Sensor Calibration Studio', 'sustainable-catalyst-workbench'),
                'logs' => __('Device Observation Log', 'sustainable-catalyst-workbench'),
                'boards' => __('Embedded Board Catalog', 'sustainable-catalyst-workbench'),
            );
        }

        public static function render_panel($panel, $atts = array()) {
            self::enqueue_assets();
            $titles = self::titles();
            $atts = shortcode_atts(array(
                'title' => isset($titles[$panel]) ? $titles[$panel] : __('Embedded Studio', 'sustainable-catalyst-workbench'),
                'project' => 'default',
                'display' => 'full',
            ), $atts, 'sc_workbench_' . str_replace('-', '_', $panel));

            $project = sanitize_key($atts['project']);
            if (!$project) {
                $project = 'default';
            }
            $id = wp_unique_id('scwb-v210-');

            ob_start();
            ?>
            <section
                id="<?php echo esc_attr($id); ?>"
                class="scwb-v210 scwb-v210--<?php echo esc_attr($panel); ?> scwb-v210--<?php echo esc_attr(sanitize_key($atts['display'])); ?>"
                data-scwb-v210-panel="<?php echo esc_attr($panel); ?>"
                data-scwb-v210-project="<?php echo esc_attr($project); ?>"
            >
                <header class="scwb-v210__header">
                    <div>
                        <p class="scwb-v210__eyebrow"><?php esc_html_e('Sustainable Catalyst Prototyping Workbench · v2.1.0', 'sustainable-catalyst-workbench'); ?></p>
                        <h2><?php echo esc_html($atts['title']); ?></h2>
                    </div>
                    <span class="scwb-v210__status" data-scwb-v210-status><?php esc_html_e('Browser-local', 'sustainable-catalyst-workbench'); ?></span>
                </header>
                <?php self::render_body($panel); ?>
                <p class="scwb-v210__boundary">
                    <?php esc_html_e('Prototype and research support only. Confirm electrical limits, pin assignments, device permissions, calibration, model behavior, latency, memory use, environmental conditions, and safety requirements on the actual hardware.', 'sustainable-catalyst-workbench'); ?>
                </p>
            </section>
            <?php
            return ob_get_clean();
        }

        private static function render_suite_launcher($project) {
            self::enqueue_assets();
            ob_start();
            ?>
            <section class="scwb-v210 scwb-v210__suite" data-scwb-v210-suite data-scwb-v210-project="<?php echo esc_attr(sanitize_key($project)); ?>">
                <header class="scwb-v210__header">
                    <div>
                        <p class="scwb-v210__eyebrow"><?php esc_html_e('Workbench v2.1.0 expansion', 'sustainable-catalyst-workbench'); ?></p>
                        <h2><?php esc_html_e('Raspberry Pi, TinyML, and Embedded Device Studio', 'sustainable-catalyst-workbench'); ?></h2>
                    </div>
                    <span class="scwb-v210__status"><?php esc_html_e('Foundation active', 'sustainable-catalyst-workbench'); ?></span>
                </header>
                <div class="scwb-v210__module-grid">
                    <?php
                    $modules = array(
                        'embedded_device_studio' => array(__('Embedded Device Studio', 'sustainable-catalyst-workbench'), __('Discover local interfaces and create allowlisted device task plans.', 'sustainable-catalyst-workbench')),
                        'raspberry_pi' => array(__('Raspberry Pi Studio', 'sustainable-catalyst-workbench'), __('Generate service, sensor, and deployment scaffolds.', 'sustainable-catalyst-workbench')),
                        'tinyml' => array(__('TinyML Studio', 'sustainable-catalyst-workbench'), __('Prepare numerical datasets and validate compact baseline models.', 'sustainable-catalyst-workbench')),
                        'sensor_calibration' => array(__('Sensor Calibration', 'sustainable-catalyst-workbench'), __('Fit and document linear calibration relationships.', 'sustainable-catalyst-workbench')),
                        'device_logs' => array(__('Device Logs', 'sustainable-catalyst-workbench'), __('Record observations, measurements, and validation notes.', 'sustainable-catalyst-workbench')),
                        'embedded_board_catalog' => array(__('Board Catalog', 'sustainable-catalyst-workbench'), __('Compare supported board families and deployment profiles.', 'sustainable-catalyst-workbench')),
                    );
                    foreach ($modules as $shortcode => $content) :
                    ?>
                        <article class="scwb-v210__module-card">
                            <h3><?php echo esc_html($content[0]); ?></h3>
                            <p><?php echo esc_html($content[1]); ?></p>
                            <code>[sc_workbench_<?php echo esc_html($shortcode); ?> project="<?php echo esc_html(sanitize_key($project)); ?>"]</code>
                        </article>
                    <?php endforeach; ?>
                </div>
            </section>
            <?php
            return ob_get_clean();
        }

        private static function render_body($panel) {
            switch ($panel) {
                case 'device': self::render_device(); break;
                case 'raspberry-pi': self::render_raspberry_pi(); break;
                case 'tinyml': self::render_tinyml(); break;
                case 'calibration': self::render_calibration(); break;
                case 'logs': self::render_logs(); break;
                case 'boards': self::render_boards(); break;
            }
        }

        private static function field($label, $name, $type = 'text', $placeholder = '', $value = '') {
            ?>
            <label class="scwb-v210__field">
                <span><?php echo esc_html($label); ?></span>
                <?php if ('textarea' === $type) : ?>
                    <textarea data-scwb-v210-field="<?php echo esc_attr($name); ?>" placeholder="<?php echo esc_attr($placeholder); ?>"><?php echo esc_textarea($value); ?></textarea>
                <?php else : ?>
                    <input type="<?php echo esc_attr($type); ?>" data-scwb-v210-field="<?php echo esc_attr($name); ?>" placeholder="<?php echo esc_attr($placeholder); ?>" value="<?php echo esc_attr($value); ?>">
                <?php endif; ?>
            </label>
            <?php
        }

        private static function select($label, $name, $options) {
            ?>
            <label class="scwb-v210__field">
                <span><?php echo esc_html($label); ?></span>
                <select data-scwb-v210-field="<?php echo esc_attr($name); ?>">
                    <?php foreach ($options as $value => $text) : ?>
                        <option value="<?php echo esc_attr($value); ?>"><?php echo esc_html($text); ?></option>
                    <?php endforeach; ?>
                </select>
            </label>
            <?php
        }

        private static function button($label, $action, $secondary = false) {
            ?>
            <button type="button" class="scwb-v210__button<?php echo $secondary ? ' scwb-v210__button--secondary' : ''; ?>" data-scwb-v210-action="<?php echo esc_attr($action); ?>">
                <?php echo esc_html($label); ?>
            </button>
            <?php
        }

        private static function render_device() {
            ?>
            <div class="scwb-v210__grid scwb-v210__grid--2">
                <div class="scwb-v210__panel">
                    <h3><?php esc_html_e('Local runner connection', 'sustainable-catalyst-workbench'); ?></h3>
                    <?php self::field(__('Runner URL', 'sustainable-catalyst-workbench'), 'runner-url', 'url', '', 'http://127.0.0.1:8787'); ?>
                    <div class="scwb-v210__actions">
                        <?php self::button(__('Check runner', 'sustainable-catalyst-workbench'), 'device-health'); ?>
                        <?php self::button(__('Discover devices', 'sustainable-catalyst-workbench'), 'device-discover', true); ?>
                    </div>
                    <p class="scwb-v210__help"><?php esc_html_e('Pair once through the v2.0.0 Local Go Runner panel. v2.1.0 reuses that origin-bound browser token.', 'sustainable-catalyst-workbench'); ?></p>
                </div>
                <div class="scwb-v210__panel">
                    <h3><?php esc_html_e('Structured task plan', 'sustainable-catalyst-workbench'); ?></h3>
                    <?php self::select(__('Task', 'sustainable-catalyst-workbench'), 'device-task', array(
                        'raspberry-pi-info' => __('Read Raspberry Pi identity', 'sustainable-catalyst-workbench'),
                        'serial-list' => __('List serial interfaces', 'sustainable-catalyst-workbench'),
                        'i2c-list' => __('List I²C interfaces', 'sustainable-catalyst-workbench'),
                        'gpio-list' => __('List GPIO character devices', 'sustainable-catalyst-workbench'),
                        'arduino-board-list' => __('Ask Arduino CLI for connected boards', 'sustainable-catalyst-workbench'),
                    )); ?>
                    <label class="scwb-v210__check"><input type="checkbox" data-scwb-v210-field="device-consent"> <?php esc_html_e('I consent to this allowlisted local device task.', 'sustainable-catalyst-workbench'); ?></label>
                    <div class="scwb-v210__actions"><?php self::button(__('Run structured task', 'sustainable-catalyst-workbench'), 'device-task-run'); ?></div>
                </div>
            </div>
            <pre class="scwb-v210__terminal" data-scwb-v210-device-output><?php esc_html_e('Device discovery has not run.', 'sustainable-catalyst-workbench'); ?></pre>
            <?php
        }

        private static function render_raspberry_pi() {
            ?>
            <div class="scwb-v210__grid scwb-v210__grid--3">
                <?php self::field(__('Project name', 'sustainable-catalyst-workbench'), 'pi-project', 'text', '', 'environment-monitor'); ?>
                <?php self::select(__('Board profile', 'sustainable-catalyst-workbench'), 'pi-board', array(
                    'raspberry-pi-5' => 'Raspberry Pi 5',
                    'raspberry-pi-4' => 'Raspberry Pi 4 Model B',
                    'raspberry-pi-zero-2-w' => 'Raspberry Pi Zero 2 W',
                    'raspberry-pi-3' => 'Raspberry Pi 3 Model B+',
                )); ?>
                <?php self::select(__('Operating profile', 'sustainable-catalyst-workbench'), 'pi-os', array(
                    'raspios-bookworm-lite' => 'Raspberry Pi OS Lite (Bookworm)',
                    'raspios-bookworm' => 'Raspberry Pi OS Desktop (Bookworm)',
                    'ubuntu-server' => 'Ubuntu Server',
                )); ?>
                <?php self::select(__('Primary interface', 'sustainable-catalyst-workbench'), 'pi-interface', array(
                    'gpio' => 'GPIO', 'i2c' => 'I²C', 'spi' => 'SPI', 'serial' => 'Serial / UART', 'network' => 'Network / API', 'camera' => 'Camera',
                )); ?>
                <?php self::field(__('Sensor or peripheral', 'sustainable-catalyst-workbench'), 'pi-sensor', 'text', 'BME280, camera, Modbus meter', 'BME280 environmental sensor'); ?>
                <?php self::field(__('Sample interval (seconds)', 'sustainable-catalyst-workbench'), 'pi-interval', 'number', '', '10'); ?>
            </div>
            <?php self::field(__('Research objective and operating constraints', 'sustainable-catalyst-workbench'), 'pi-objective', 'textarea', 'Describe measurements, location, power, network, storage, and validation requirements.'); ?>
            <div class="scwb-v210__actions">
                <?php self::button(__('Generate project', 'sustainable-catalyst-workbench'), 'pi-generate'); ?>
                <?php self::button(__('Download project bundle', 'sustainable-catalyst-workbench'), 'pi-download', true); ?>
                <?php self::button(__('Download Python service', 'sustainable-catalyst-workbench'), 'pi-python', true); ?>
            </div>
            <div class="scwb-v210__grid scwb-v210__grid--2 scwb-v210__outputs">
                <pre class="scwb-v210__terminal" data-scwb-v210-pi-code><?php esc_html_e('Generate a project to create the Python acquisition service.', 'sustainable-catalyst-workbench'); ?></pre>
                <pre class="scwb-v210__terminal" data-scwb-v210-pi-manifest><?php esc_html_e('The project manifest will appear here.', 'sustainable-catalyst-workbench'); ?></pre>
            </div>
            <?php
        }

        private static function render_tinyml() {
            $sample = "temperature,humidity,vibration,label\n21.1,42.0,0.12,normal\n22.3,44.0,0.10,normal\n29.8,61.0,0.82,alert\n30.5,63.0,0.91,alert\n23.0,45.0,0.14,normal\n31.2,65.0,0.88,alert";
            ?>
            <div class="scwb-v210__grid scwb-v210__grid--3">
                <?php self::select(__('Task type', 'sustainable-catalyst-workbench'), 'tinyml-task', array('classification' => __('Classification', 'sustainable-catalyst-workbench'), 'regression' => __('Regression', 'sustainable-catalyst-workbench'))); ?>
                <?php self::field(__('Target column', 'sustainable-catalyst-workbench'), 'tinyml-target', 'text', '', 'label'); ?>
                <?php self::select(__('Quantization preview', 'sustainable-catalyst-workbench'), 'tinyml-quantization', array('int8' => 'INT8', 'float16' => 'Float16', 'none' => __('None', 'sustainable-catalyst-workbench'))); ?>
            </div>
            <?php self::field(__('Numerical CSV dataset', 'sustainable-catalyst-workbench'), 'tinyml-csv', 'textarea', 'Paste CSV with a header row.', $sample); ?>
            <div class="scwb-v210__actions">
                <?php self::button(__('Analyze and validate baseline', 'sustainable-catalyst-workbench'), 'tinyml-analyze'); ?>
                <?php self::button(__('Download model card', 'sustainable-catalyst-workbench'), 'tinyml-model-card', true); ?>
                <?php self::button(__('Download deployment scaffold', 'sustainable-catalyst-workbench'), 'tinyml-scaffold', true); ?>
                <?php self::button(__('Download project bundle', 'sustainable-catalyst-workbench'), 'tinyml-bundle', true); ?>
            </div>
            <div class="scwb-v210__metrics" data-scwb-v210-tinyml-metrics></div>
            <pre class="scwb-v210__terminal" data-scwb-v210-tinyml-output><?php esc_html_e('No dataset analysis has run.', 'sustainable-catalyst-workbench'); ?></pre>
            <?php
        }

        private static function render_calibration() {
            ?>
            <div class="scwb-v210__grid scwb-v210__grid--3">
                <?php self::field(__('Instrument or sensor', 'sustainable-catalyst-workbench'), 'cal-name', 'text', '', 'temperature-sensor-01'); ?>
                <?php self::field(__('Unit', 'sustainable-catalyst-workbench'), 'cal-unit', 'text', '', '°C'); ?>
                <?php self::field(__('Calibration date', 'sustainable-catalyst-workbench'), 'cal-date', 'date'); ?>
            </div>
            <?php self::field(__('Reference, measured pairs', 'sustainable-catalyst-workbench'), 'cal-pairs', 'textarea', 'One pair per line: reference,measured', "0,0.3\n10,10.4\n20,20.7\n30,30.8\n40,41.2"); ?>
            <div class="scwb-v210__actions">
                <?php self::button(__('Fit linear calibration', 'sustainable-catalyst-workbench'), 'cal-fit'); ?>
                <?php self::button(__('Download calibration record', 'sustainable-catalyst-workbench'), 'cal-download', true); ?>
            </div>
            <div class="scwb-v210__metrics" data-scwb-v210-cal-metrics></div>
            <pre class="scwb-v210__terminal" data-scwb-v210-cal-output><?php esc_html_e('Calibration has not been calculated.', 'sustainable-catalyst-workbench'); ?></pre>
            <?php
        }

        private static function render_logs() {
            ?>
            <div class="scwb-v210__grid scwb-v210__grid--4">
                <?php self::field(__('Device', 'sustainable-catalyst-workbench'), 'log-device', 'text', '', 'sensor-node-01'); ?>
                <?php self::field(__('Metric', 'sustainable-catalyst-workbench'), 'log-metric', 'text', '', 'temperature'); ?>
                <?php self::field(__('Value', 'sustainable-catalyst-workbench'), 'log-value', 'number', '', '22.4'); ?>
                <?php self::field(__('Unit', 'sustainable-catalyst-workbench'), 'log-unit', 'text', '', '°C'); ?>
            </div>
            <?php self::field(__('Observation or validation note', 'sustainable-catalyst-workbench'), 'log-note', 'textarea', 'Location, test state, anomaly, calibration condition, or environmental context.'); ?>
            <div class="scwb-v210__actions">
                <?php self::button(__('Add observation', 'sustainable-catalyst-workbench'), 'log-add'); ?>
                <?php self::button(__('Export CSV', 'sustainable-catalyst-workbench'), 'log-export', true); ?>
                <?php self::button(__('Clear log', 'sustainable-catalyst-workbench'), 'log-clear', true); ?>
            </div>
            <div class="scwb-v210__table-wrap">
                <table class="scwb-v210__table">
                    <thead><tr><th><?php esc_html_e('Time', 'sustainable-catalyst-workbench'); ?></th><th><?php esc_html_e('Device', 'sustainable-catalyst-workbench'); ?></th><th><?php esc_html_e('Metric', 'sustainable-catalyst-workbench'); ?></th><th><?php esc_html_e('Value', 'sustainable-catalyst-workbench'); ?></th><th><?php esc_html_e('Note', 'sustainable-catalyst-workbench'); ?></th><th></th></tr></thead>
                    <tbody data-scwb-v210-log-body></tbody>
                </table>
            </div>
            <?php
        }

        private static function render_boards() {
            ?>
            <div class="scwb-v210__filters">
                <?php self::select(__('Filter family', 'sustainable-catalyst-workbench'), 'board-family', array(
                    'all' => __('All families', 'sustainable-catalyst-workbench'),
                    'raspberry-pi' => 'Raspberry Pi',
                    'arduino' => 'Arduino',
                    'esp32' => 'ESP32 / Arduino-compatible',
                    'seeed' => 'Seeed Studio',
                    'adafruit' => 'Adafruit',
                    'st' => 'STMicroelectronics',
                    'fpga' => 'FPGA',
                )); ?>
            </div>
            <div class="scwb-v210__board-grid" data-scwb-v210-board-grid></div>
            <?php
        }
    }

    SCWB_V210_Embedded_Studio::boot();
}
