<?php
/**
 * Sustainable Catalyst Workbench v2.0.0 foundation.
 *
 * Loaded by the existing Workbench plugin after the upgrade script patches
 * sustainable-catalyst-workbench.php. This file intentionally uses the existing
 * plugin identity and browser-local project model.
 */

if (!defined('ABSPATH')) {
    exit;
}

if (!class_exists('SCWB_V200_Foundation')) {
    final class SCWB_V200_Foundation {
        const VERSION = '2.0.0';
        const HANDLE = 'scwb-v200';

        private static $assets_loaded = false;

        public static function boot() {
            add_action('init', array(__CLASS__, 'register_shortcodes'));
            add_filter('do_shortcode_tag', array(__CLASS__, 'append_runner_to_code_studio'), 10, 4);
        }

        public static function register_shortcodes() {
            $shortcodes = array(
                'sc_workbench_lab_canvas' => 'canvas',
                'sc_workbench_notebook' => 'notebook',
                'sc_workbench_documentation_studio' => 'documentation',
                'sc_workbench_hardware_studio' => 'hardware',
                'sc_workbench_arduino' => 'arduino',
                'sc_workbench_schematic' => 'schematic',
                'sc_workbench_bom' => 'bom',
                'sc_workbench_pcb' => 'pcb',
                'sc_workbench_assembly' => 'assembly',
                'sc_workbench_fpga' => 'fpga',
                'sc_workbench_local_runner' => 'runner',
            );

            foreach ($shortcodes as $tag => $panel) {
                add_shortcode($tag, function ($atts = array()) use ($panel) {
                    return SCWB_V200_Foundation::render_panel($panel, $atts);
                });
            }
        }

        public static function append_runner_to_code_studio($output, $tag, $attr, $m) {
            if ('sc_workbench_code_studio' !== $tag || false !== strpos($output, 'data-scwb-v200-runner')) {
                return $output;
            }

            return $output . self::render_panel('runner', array(
                'title' => __('Local Go Runner', 'sustainable-catalyst-workbench'),
                'project' => isset($attr['project']) ? $attr['project'] : 'default',
                'display' => 'embedded',
            ));
        }

        private static function enqueue_assets() {
            if (self::$assets_loaded) {
                return;
            }
            self::$assets_loaded = true;

            $plugin_file = defined('SCWB_V200_PLUGIN_FILE') ? SCWB_V200_PLUGIN_FILE : dirname(__DIR__) . '/sustainable-catalyst-workbench.php';
            $base_url = plugin_dir_url($plugin_file);

            wp_enqueue_style(
                self::HANDLE,
                $base_url . 'assets/css/sc-workbench-v200.css',
                array(),
                self::VERSION
            );
            wp_enqueue_script(
                self::HANDLE,
                $base_url . 'assets/js/sc-workbench-v200.js',
                array(),
                self::VERSION,
                true
            );
            wp_localize_script(self::HANDLE, 'SCWBV200', array(
                'version' => self::VERSION,
                'runnerDefaultUrl' => 'http://127.0.0.1:8787',
                'storagePrefix' => 'scwb-v200:',
                'labels' => array(
                    'saved' => __('Saved locally', 'sustainable-catalyst-workbench'),
                    'downloaded' => __('Download created', 'sustainable-catalyst-workbench'),
                    'runnerOffline' => __('Local runner unavailable', 'sustainable-catalyst-workbench'),
                ),
            ));
        }

        private static function title_for($panel) {
            $titles = array(
                'canvas' => __('Research Lab Canvas', 'sustainable-catalyst-workbench'),
                'notebook' => __('Research and Lab Notebook', 'sustainable-catalyst-workbench'),
                'documentation' => __('Technical Documentation Studio', 'sustainable-catalyst-workbench'),
                'hardware' => __('Hardware Studio', 'sustainable-catalyst-workbench'),
                'arduino' => __('Arduino Studio', 'sustainable-catalyst-workbench'),
                'schematic' => __('Schematic Generator', 'sustainable-catalyst-workbench'),
                'bom' => __('Bill of Materials', 'sustainable-catalyst-workbench'),
                'pcb' => __('Conceptual PCB Generator', 'sustainable-catalyst-workbench'),
                'assembly' => __('Assembly Translator', 'sustainable-catalyst-workbench'),
                'fpga' => __('FPGA Studio', 'sustainable-catalyst-workbench'),
                'runner' => __('Local Go Runner', 'sustainable-catalyst-workbench'),
            );
            return isset($titles[$panel]) ? $titles[$panel] : __('Workbench Studio', 'sustainable-catalyst-workbench');
        }

        public static function render_panel($panel, $atts = array()) {
            self::enqueue_assets();

            $atts = shortcode_atts(array(
                'title' => self::title_for($panel),
                'project' => 'default',
                'display' => 'full',
            ), $atts, 'sc_workbench_' . $panel);

            $id = wp_unique_id('scwb-v200-');
            $project = sanitize_key($atts['project']);
            if (!$project) {
                $project = 'default';
            }

            ob_start();
            ?>
            <section
                id="<?php echo esc_attr($id); ?>"
                class="scwb-v200 scwb-v200--<?php echo esc_attr($panel); ?> scwb-v200--<?php echo esc_attr(sanitize_key($atts['display'])); ?>"
                data-scwb-v200-panel="<?php echo esc_attr($panel); ?>"
                data-scwb-v200-project="<?php echo esc_attr($project); ?>"
            >
                <header class="scwb-v200__header">
                    <div>
                        <p class="scwb-v200__eyebrow"><?php esc_html_e('Sustainable Catalyst Prototyping Workbench · v2.0.0', 'sustainable-catalyst-workbench'); ?></p>
                        <h2><?php echo esc_html($atts['title']); ?></h2>
                    </div>
                    <span class="scwb-v200__status" data-scwb-v200-status><?php esc_html_e('Browser-local', 'sustainable-catalyst-workbench'); ?></span>
                </header>
                <?php self::render_panel_body($panel); ?>
                <p class="scwb-v200__boundary">
                    <?php esc_html_e('Research and prototyping support only. Validate code, calculations, schematics, component choices, constraints, and generated documentation before professional or safety-critical use.', 'sustainable-catalyst-workbench'); ?>
                </p>
            </section>
            <?php
            return ob_get_clean();
        }

        private static function field($label, $name, $type = 'text', $placeholder = '') {
            ?>
            <label class="scwb-v200__field">
                <span><?php echo esc_html($label); ?></span>
                <?php if ('textarea' === $type) : ?>
                    <textarea data-scwb-field="<?php echo esc_attr($name); ?>" placeholder="<?php echo esc_attr($placeholder); ?>"></textarea>
                <?php else : ?>
                    <input type="<?php echo esc_attr($type); ?>" data-scwb-field="<?php echo esc_attr($name); ?>" placeholder="<?php echo esc_attr($placeholder); ?>">
                <?php endif; ?>
            </label>
            <?php
        }

        private static function button($label, $action, $secondary = false) {
            ?>
            <button class="scwb-v200__button<?php echo $secondary ? ' scwb-v200__button--secondary' : ''; ?>" type="button" data-scwb-action="<?php echo esc_attr($action); ?>">
                <?php echo esc_html($label); ?>
            </button>
            <?php
        }

        private static function render_panel_body($panel) {
            switch ($panel) {
                case 'canvas':
                    self::render_canvas();
                    break;
                case 'notebook':
                    self::render_notebook();
                    break;
                case 'documentation':
                    self::render_documentation();
                    break;
                case 'hardware':
                    self::render_hardware();
                    break;
                case 'arduino':
                    self::render_arduino();
                    break;
                case 'schematic':
                    self::render_schematic();
                    break;
                case 'bom':
                    self::render_bom();
                    break;
                case 'pcb':
                    self::render_pcb();
                    break;
                case 'assembly':
                    self::render_assembly();
                    break;
                case 'fpga':
                    self::render_fpga();
                    break;
                case 'runner':
                    self::render_runner();
                    break;
            }
        }

        private static function render_canvas() {
            ?>
            <div class="scwb-v200__toolbar" role="toolbar" aria-label="Canvas controls">
                <label><?php esc_html_e('Tool', 'sustainable-catalyst-workbench'); ?>
                    <select data-scwb-canvas-tool>
                        <option value="pen"><?php esc_html_e('Pen', 'sustainable-catalyst-workbench'); ?></option>
                        <option value="line"><?php esc_html_e('Line', 'sustainable-catalyst-workbench'); ?></option>
                        <option value="eraser"><?php esc_html_e('Eraser', 'sustainable-catalyst-workbench'); ?></option>
                    </select>
                </label>
                <label><?php esc_html_e('Width', 'sustainable-catalyst-workbench'); ?><input type="range" min="1" max="18" value="3" data-scwb-canvas-width></label>
                <?php self::button(__('Undo', 'sustainable-catalyst-workbench'), 'canvas-undo', true); ?>
                <?php self::button(__('Clear', 'sustainable-catalyst-workbench'), 'canvas-clear', true); ?>
                <?php self::button(__('Download PNG', 'sustainable-catalyst-workbench'), 'canvas-download'); ?>
            </div>
            <div class="scwb-v200__canvas-wrap">
                <canvas width="1200" height="720" data-scwb-canvas aria-label="Research drawing canvas"></canvas>
            </div>
            <?php
        }

        private static function render_notebook() {
            ?>
            <div class="scwb-v200__grid scwb-v200__grid--2">
                <?php self::field(__('Entry title', 'sustainable-catalyst-workbench'), 'notebook-title', 'text', __('Experiment, observation, or calculation', 'sustainable-catalyst-workbench')); ?>
                <label class="scwb-v200__field"><span><?php esc_html_e('Entry type', 'sustainable-catalyst-workbench'); ?></span>
                    <select data-scwb-field="notebook-type">
                        <option value="observation"><?php esc_html_e('Observation', 'sustainable-catalyst-workbench'); ?></option>
                        <option value="hypothesis"><?php esc_html_e('Hypothesis', 'sustainable-catalyst-workbench'); ?></option>
                        <option value="method"><?php esc_html_e('Method', 'sustainable-catalyst-workbench'); ?></option>
                        <option value="measurement"><?php esc_html_e('Measurement', 'sustainable-catalyst-workbench'); ?></option>
                        <option value="result"><?php esc_html_e('Result', 'sustainable-catalyst-workbench'); ?></option>
                        <option value="review"><?php esc_html_e('Review note', 'sustainable-catalyst-workbench'); ?></option>
                    </select>
                </label>
            </div>
            <?php self::field(__('Notebook entry', 'sustainable-catalyst-workbench'), 'notebook-body', 'textarea', __('Record context, method, units, uncertainty, sources, and interpretation.', 'sustainable-catalyst-workbench')); ?>
            <div class="scwb-v200__actions">
                <?php self::button(__('Save entry', 'sustainable-catalyst-workbench'), 'notebook-save'); ?>
                <?php self::button(__('Export notebook', 'sustainable-catalyst-workbench'), 'notebook-export', true); ?>
            </div>
            <div class="scwb-v200__records" data-scwb-notebook-records></div>
            <?php
        }

        private static function render_documentation() {
            ?>
            <div class="scwb-v200__grid scwb-v200__grid--2">
                <?php self::field(__('Project title', 'sustainable-catalyst-workbench'), 'doc-title', 'text', __('Technical project record', 'sustainable-catalyst-workbench')); ?>
                <?php self::field(__('Version / revision', 'sustainable-catalyst-workbench'), 'doc-version', 'text', '0.1.0'); ?>
            </div>
            <?php self::field(__('Purpose and scope', 'sustainable-catalyst-workbench'), 'doc-purpose', 'textarea', __('State the problem, audience, operating boundary, and intended use.', 'sustainable-catalyst-workbench')); ?>
            <?php self::field(__('Methods and architecture', 'sustainable-catalyst-workbench'), 'doc-methods', 'textarea', __('Describe models, code, hardware, data, interfaces, and assumptions.', 'sustainable-catalyst-workbench')); ?>
            <?php self::field(__('Validation and limitations', 'sustainable-catalyst-workbench'), 'doc-validation', 'textarea', __('Document tests, evidence, uncertainty, unresolved issues, and review requirements.', 'sustainable-catalyst-workbench')); ?>
            <div class="scwb-v200__actions">
                <?php self::button(__('Generate Markdown', 'sustainable-catalyst-workbench'), 'documentation-generate'); ?>
                <?php self::button(__('Download Markdown', 'sustainable-catalyst-workbench'), 'documentation-download', true); ?>
            </div>
            <pre class="scwb-v200__output" data-scwb-documentation-output aria-live="polite"></pre>
            <?php
        }

        private static function render_hardware() {
            ?>
            <div class="scwb-v200__module-grid">
                <?php
                $modules = array(
                    'arduino' => array(__('Arduino Studio', 'sustainable-catalyst-workbench'), __('Sketch scaffold, board assumptions, pins, sensors, and serial output.', 'sustainable-catalyst-workbench')),
                    'schematic' => array(__('Schematic Generator', 'sustainable-catalyst-workbench'), __('Conceptual signal and power connections with synchronized components.', 'sustainable-catalyst-workbench')),
                    'bom' => array(__('Bill of Materials', 'sustainable-catalyst-workbench'), __('Editable component quantities, references, notes, and export.', 'sustainable-catalyst-workbench')),
                    'pcb' => array(__('Conceptual PCB', 'sustainable-catalyst-workbench'), __('Board outline and placement concept; not manufacturing routing.', 'sustainable-catalyst-workbench')),
                    'assembly' => array(__('Assembly Translator', 'sustainable-catalyst-workbench'), __('Educational instruction mapping and architecture notes.', 'sustainable-catalyst-workbench')),
                    'fpga' => array(__('FPGA Studio', 'sustainable-catalyst-workbench'), __('Verilog and constraint scaffolding with explicit synthesis boundaries.', 'sustainable-catalyst-workbench')),
                );
                foreach ($modules as $key => $item) : ?>
                    <article class="scwb-v200__module">
                        <p class="scwb-v200__module-id"><?php echo esc_html(strtoupper($key)); ?></p>
                        <h3><?php echo esc_html($item[0]); ?></h3>
                        <p><?php echo esc_html($item[1]); ?></p>
                        <button type="button" class="scwb-v200__text-button" data-scwb-open-module="<?php echo esc_attr($key); ?>"><?php esc_html_e('Open panel', 'sustainable-catalyst-workbench'); ?></button>
                    </article>
                <?php endforeach; ?>
            </div>
            <?php
        }

        private static function render_arduino() {
            ?>
            <div class="scwb-v200__grid scwb-v200__grid--3">
                <?php self::field(__('Board', 'sustainable-catalyst-workbench'), 'arduino-board', 'text', 'Arduino Uno R4 WiFi'); ?>
                <?php self::field(__('Sensor / module', 'sustainable-catalyst-workbench'), 'arduino-sensor', 'text', 'BME280'); ?>
                <?php self::field(__('Data pin', 'sustainable-catalyst-workbench'), 'arduino-pin', 'text', 'A0'); ?>
            </div>
            <?php self::field(__('Prototype purpose', 'sustainable-catalyst-workbench'), 'arduino-purpose', 'textarea', __('Describe the measurement, actuation, sampling interval, units, and calibration expectation.', 'sustainable-catalyst-workbench')); ?>
            <div class="scwb-v200__actions">
                <?php self::button(__('Generate sketch', 'sustainable-catalyst-workbench'), 'arduino-generate'); ?>
                <?php self::button(__('Download .ino', 'sustainable-catalyst-workbench'), 'arduino-download', true); ?>
            </div>
            <pre class="scwb-v200__output" data-scwb-arduino-output></pre>
            <?php
        }

        private static function render_schematic() {
            ?>
            <div class="scwb-v200__grid scwb-v200__grid--3">
                <?php self::field(__('Controller', 'sustainable-catalyst-workbench'), 'schematic-controller', 'text', 'Arduino Uno R4 WiFi'); ?>
                <?php self::field(__('Input device', 'sustainable-catalyst-workbench'), 'schematic-input', 'text', 'BME280 sensor'); ?>
                <?php self::field(__('Output / interface', 'sustainable-catalyst-workbench'), 'schematic-output', 'text', 'USB serial'); ?>
            </div>
            <div class="scwb-v200__actions">
                <?php self::button(__('Generate concept', 'sustainable-catalyst-workbench'), 'schematic-generate'); ?>
                <?php self::button(__('Download SVG', 'sustainable-catalyst-workbench'), 'schematic-download', true); ?>
            </div>
            <div class="scwb-v200__diagram" data-scwb-schematic-output></div>
            <?php
        }

        private static function render_bom() {
            ?>
            <div class="scwb-v200__actions">
                <?php self::button(__('Add component', 'sustainable-catalyst-workbench'), 'bom-add'); ?>
                <?php self::button(__('Download CSV', 'sustainable-catalyst-workbench'), 'bom-download', true); ?>
            </div>
            <div class="scwb-v200__table-wrap">
                <table class="scwb-v200__table">
                    <thead><tr><th><?php esc_html_e('Ref', 'sustainable-catalyst-workbench'); ?></th><th><?php esc_html_e('Component', 'sustainable-catalyst-workbench'); ?></th><th><?php esc_html_e('Qty', 'sustainable-catalyst-workbench'); ?></th><th><?php esc_html_e('Specification / note', 'sustainable-catalyst-workbench'); ?></th><th></th></tr></thead>
                    <tbody data-scwb-bom-body></tbody>
                </table>
            </div>
            <?php
        }

        private static function render_pcb() {
            ?>
            <div class="scwb-v200__grid scwb-v200__grid--3">
                <?php self::field(__('Board width (mm)', 'sustainable-catalyst-workbench'), 'pcb-width', 'number', '80'); ?>
                <?php self::field(__('Board height (mm)', 'sustainable-catalyst-workbench'), 'pcb-height', 'number', '50'); ?>
                <?php self::field(__('Placement concept', 'sustainable-catalyst-workbench'), 'pcb-layout', 'text', 'controller, sensor, power, headers'); ?>
            </div>
            <div class="scwb-v200__actions">
                <?php self::button(__('Generate placement concept', 'sustainable-catalyst-workbench'), 'pcb-generate'); ?>
                <?php self::button(__('Download SVG', 'sustainable-catalyst-workbench'), 'pcb-download', true); ?>
            </div>
            <div class="scwb-v200__diagram" data-scwb-pcb-output></div>
            <?php
        }

        private static function render_assembly() {
            ?>
            <div class="scwb-v200__grid scwb-v200__grid--2">
                <label class="scwb-v200__field"><span><?php esc_html_e('Target', 'sustainable-catalyst-workbench'); ?></span>
                    <select data-scwb-field="assembly-target"><option value="x86-64">x86-64</option><option value="arm64">ARM64</option><option value="risc-v">RISC-V</option></select>
                </label>
                <?php self::field(__('Operation', 'sustainable-catalyst-workbench'), 'assembly-operation', 'text', 'sum an integer array'); ?>
            </div>
            <div class="scwb-v200__actions"><?php self::button(__('Generate educational scaffold', 'sustainable-catalyst-workbench'), 'assembly-generate'); ?></div>
            <pre class="scwb-v200__output" data-scwb-assembly-output></pre>
            <?php
        }

        private static function render_fpga() {
            ?>
            <div class="scwb-v200__grid scwb-v200__grid--3">
                <?php self::field(__('Board / family', 'sustainable-catalyst-workbench'), 'fpga-board', 'text', 'generic iCE40'); ?>
                <?php self::field(__('Module name', 'sustainable-catalyst-workbench'), 'fpga-module', 'text', 'sensor_pulse'); ?>
                <?php self::field(__('Clock frequency (MHz)', 'sustainable-catalyst-workbench'), 'fpga-clock', 'number', '12'); ?>
            </div>
            <?php self::field(__('Logic behavior', 'sustainable-catalyst-workbench'), 'fpga-behavior', 'textarea', __('Describe inputs, outputs, reset behavior, timing assumptions, and test expectations.', 'sustainable-catalyst-workbench')); ?>
            <div class="scwb-v200__actions">
                <?php self::button(__('Generate project scaffold', 'sustainable-catalyst-workbench'), 'fpga-generate'); ?>
                <?php self::button(__('Download Verilog', 'sustainable-catalyst-workbench'), 'fpga-download', true); ?>
            </div>
            <pre class="scwb-v200__output" data-scwb-fpga-output></pre>
            <?php
        }

        private static function render_runner() {
            ?>
            <div data-scwb-v200-runner>
                <div class="scwb-v200__grid scwb-v200__grid--3">
                    <?php self::field(__('Runner URL', 'sustainable-catalyst-workbench'), 'runner-url', 'url', 'http://127.0.0.1:8787'); ?>
                    <?php self::field(__('Pairing code', 'sustainable-catalyst-workbench'), 'runner-code', 'text', '000000'); ?>
                    <label class="scwb-v200__field"><span><?php esc_html_e('Native execution', 'sustainable-catalyst-workbench'); ?></span><label class="scwb-v200__check"><input type="checkbox" data-scwb-field="runner-consent"> <?php esc_html_e('I understand local code runs with my user permissions.', 'sustainable-catalyst-workbench'); ?></label></label>
                </div>
                <div class="scwb-v200__actions">
                    <?php self::button(__('Check runner', 'sustainable-catalyst-workbench'), 'runner-health', true); ?>
                    <?php self::button(__('Pair', 'sustainable-catalyst-workbench'), 'runner-pair'); ?>
                    <?php self::button(__('Discover runtimes', 'sustainable-catalyst-workbench'), 'runner-runtimes', true); ?>
                </div>
                <pre class="scwb-v200__output scwb-v200__output--terminal" data-scwb-runner-output aria-live="polite">Local runner is optional. Start workbench-runner on this computer, then pair this browser.</pre>
            </div>
            <?php
        }
    }

    SCWB_V200_Foundation::boot();
}
