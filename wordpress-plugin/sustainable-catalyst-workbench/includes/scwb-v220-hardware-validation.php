<?php
/**
 * Sustainable Catalyst Prototyping Workbench v2.2.0.
 * FPGA, Electronics Design, and Hardware Validation Studio.
 */

if (!defined('ABSPATH')) {
    exit;
}

if (!class_exists('SCWB_V220_Hardware_Validation')) {
    final class SCWB_V220_Hardware_Validation {
        const VERSION = '2.2.0';
        const HANDLE = 'scwb-v220';
        private static $assets_loaded = false;

        public static function boot() {
            add_action('init', array(__CLASS__, 'register_shortcodes'));
            add_filter('do_shortcode_tag', array(__CLASS__, 'append_suite'), 14, 4);
        }

        public static function register_shortcodes() {
            $shortcodes = array(
                'sc_workbench_fpga_studio' => 'fpga',
                'sc_workbench_electronics_design' => 'electronics',
                'sc_workbench_schematic_editor' => 'schematic',
                'sc_workbench_bom_validation' => 'bom',
                'sc_workbench_pcb_studio' => 'pcb',
                'sc_workbench_hardware_validation' => 'validation',
            );
            foreach ($shortcodes as $tag => $panel) {
                add_shortcode($tag, function ($atts = array()) use ($panel) {
                    return SCWB_V220_Hardware_Validation::render_panel($panel, $atts);
                });
            }
        }

        public static function append_suite($output, $tag, $attr, $match) {
            if ('sc_workbench_hardware_studio' !== $tag || false !== strpos($output, 'data-scwb-v220-suite')) {
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
            $plugin_file = defined('SCWB_V220_PLUGIN_FILE') ? SCWB_V220_PLUGIN_FILE : dirname(__DIR__) . '/sustainable-catalyst-workbench.php';
            $base_url = plugin_dir_url($plugin_file);
            wp_enqueue_style(self::HANDLE, $base_url . 'assets/css/sc-workbench-v220.css', array(), self::VERSION);
            wp_enqueue_script(self::HANDLE, $base_url . 'assets/js/sc-workbench-v220.js', array(), self::VERSION, true);
            wp_localize_script(self::HANDLE, 'SCWBV220', array(
                'version' => self::VERSION,
                'runnerDefaultUrl' => 'http://127.0.0.1:8787',
                'storagePrefix' => 'scwb-v220:',
                'v210StoragePrefix' => 'scwb-v210:',
                'labels' => array(
                    'saved' => __('Saved locally', 'sustainable-catalyst-workbench'),
                    'ready' => __('Ready', 'sustainable-catalyst-workbench'),
                    'invalid' => __('Review required', 'sustainable-catalyst-workbench'),
                ),
            ));
        }

        private static function titles() {
            return array(
                'fpga' => __('FPGA Studio', 'sustainable-catalyst-workbench'),
                'electronics' => __('Electronics Design Studio', 'sustainable-catalyst-workbench'),
                'schematic' => __('Schematic and Netlist Studio', 'sustainable-catalyst-workbench'),
                'bom' => __('BOM Validation Studio', 'sustainable-catalyst-workbench'),
                'pcb' => __('PCB Planning and Design-Rule Studio', 'sustainable-catalyst-workbench'),
                'validation' => __('Hardware Validation Studio', 'sustainable-catalyst-workbench'),
            );
        }

        public static function render_panel($panel, $atts = array()) {
            self::enqueue_assets();
            $titles = self::titles();
            $atts = shortcode_atts(array(
                'title' => isset($titles[$panel]) ? $titles[$panel] : __('Hardware Validation Studio', 'sustainable-catalyst-workbench'),
                'project' => 'default',
                'display' => 'full',
            ), $atts, 'sc_workbench_' . str_replace('-', '_', $panel));
            $project = sanitize_key($atts['project']);
            if (!$project) {
                $project = 'default';
            }
            $id = wp_unique_id('scwb-v220-');
            ob_start();
            ?>
            <section id="<?php echo esc_attr($id); ?>" class="scwb-v220 scwb-v220--<?php echo esc_attr($panel); ?> scwb-v220--<?php echo esc_attr(sanitize_key($atts['display'])); ?>" data-scwb-v220-panel="<?php echo esc_attr($panel); ?>" data-scwb-v220-project="<?php echo esc_attr($project); ?>">
                <header class="scwb-v220__header">
                    <div>
                        <p class="scwb-v220__eyebrow"><?php esc_html_e('Sustainable Catalyst Prototyping Workbench · v2.2.0', 'sustainable-catalyst-workbench'); ?></p>
                        <h2><?php echo esc_html($atts['title']); ?></h2>
                    </div>
                    <span class="scwb-v220__status" data-scwb-v220-status><?php esc_html_e('Browser-local', 'sustainable-catalyst-workbench'); ?></span>
                </header>
                <?php self::render_body($panel); ?>
                <p class="scwb-v220__boundary"><?php esc_html_e('Engineering support only. Verify component ratings, electrical clearances, grounding, thermal behavior, constraints, timing, fabrication rules, standards, and safety on the actual target hardware with qualified review.', 'sustainable-catalyst-workbench'); ?></p>
            </section>
            <?php
            return ob_get_clean();
        }

        private static function render_suite_launcher($project) {
            self::enqueue_assets();
            $modules = array(
                'fpga_studio' => array(__('FPGA Studio', 'sustainable-catalyst-workbench'), __('Create HDL, constraints, clocks, simulations, and implementation review records.', 'sustainable-catalyst-workbench')),
                'electronics_design' => array(__('Electronics Design', 'sustainable-catalyst-workbench'), __('Frame rails, interfaces, protection, decoupling, and component requirements.', 'sustainable-catalyst-workbench')),
                'schematic_editor' => array(__('Schematic and Netlist', 'sustainable-catalyst-workbench'), __('Build a structured connection model and export a reviewable netlist.', 'sustainable-catalyst-workbench')),
                'bom_validation' => array(__('BOM Validation', 'sustainable-catalyst-workbench'), __('Check quantities, lifecycle, substitutions, cost, and sourcing assumptions.', 'sustainable-catalyst-workbench')),
                'pcb_studio' => array(__('PCB Planning', 'sustainable-catalyst-workbench'), __('Define stackup, board outline, placement classes, and preliminary design rules.', 'sustainable-catalyst-workbench')),
                'hardware_validation' => array(__('Hardware Validation', 'sustainable-catalyst-workbench'), __('Create test plans, acceptance limits, measurements, deviations, and evidence.', 'sustainable-catalyst-workbench')),
            );
            ob_start();
            ?>
            <section class="scwb-v220 scwb-v220__suite" data-scwb-v220-suite data-scwb-v220-project="<?php echo esc_attr(sanitize_key($project)); ?>">
                <header class="scwb-v220__header">
                    <div><p class="scwb-v220__eyebrow"><?php esc_html_e('Workbench v2.2.0 expansion', 'sustainable-catalyst-workbench'); ?></p><h2><?php esc_html_e('FPGA, Electronics Design, and Hardware Validation Studio', 'sustainable-catalyst-workbench'); ?></h2></div>
                    <span class="scwb-v220__status"><?php esc_html_e('Engineering layer active', 'sustainable-catalyst-workbench'); ?></span>
                </header>
                <div class="scwb-v220__module-grid">
                    <?php foreach ($modules as $shortcode => $content) : ?>
                        <article class="scwb-v220__module-card"><h3><?php echo esc_html($content[0]); ?></h3><p><?php echo esc_html($content[1]); ?></p><code>[sc_workbench_<?php echo esc_html($shortcode); ?> project="<?php echo esc_html(sanitize_key($project)); ?>"]</code></article>
                    <?php endforeach; ?>
                </div>
            </section>
            <?php
            return ob_get_clean();
        }

        private static function render_body($panel) {
            switch ($panel) {
                case 'fpga': self::render_fpga(); break;
                case 'electronics': self::render_electronics(); break;
                case 'schematic': self::render_schematic(); break;
                case 'bom': self::render_bom(); break;
                case 'pcb': self::render_pcb(); break;
                case 'validation': self::render_validation(); break;
            }
        }

        private static function field($label, $name, $type = 'text', $placeholder = '', $value = '') {
            ?>
            <label class="scwb-v220__field"><span><?php echo esc_html($label); ?></span>
                <?php if ('textarea' === $type) : ?>
                    <textarea data-scwb-v220-field="<?php echo esc_attr($name); ?>" placeholder="<?php echo esc_attr($placeholder); ?>"><?php echo esc_textarea($value); ?></textarea>
                <?php else : ?>
                    <input type="<?php echo esc_attr($type); ?>" data-scwb-v220-field="<?php echo esc_attr($name); ?>" placeholder="<?php echo esc_attr($placeholder); ?>" value="<?php echo esc_attr($value); ?>">
                <?php endif; ?>
            </label>
            <?php
        }

        private static function select($label, $name, $options) {
            ?>
            <label class="scwb-v220__field"><span><?php echo esc_html($label); ?></span><select data-scwb-v220-field="<?php echo esc_attr($name); ?>">
                <?php foreach ($options as $value => $text) : ?><option value="<?php echo esc_attr($value); ?>"><?php echo esc_html($text); ?></option><?php endforeach; ?>
            </select></label>
            <?php
        }

        private static function button($label, $action, $secondary = false) {
            ?><button type="button" class="scwb-v220__button<?php echo $secondary ? ' scwb-v220__button--secondary' : ''; ?>" data-scwb-v220-action="<?php echo esc_attr($action); ?>"><?php echo esc_html($label); ?></button><?php
        }

        private static function render_fpga() {
            $sample = "module heartbeat #(parameter COUNT_MAX = 24_000_000) (\n  input  wire clk,\n  input  wire reset_n,\n  output reg  led\n);\n  reg [24:0] counter;\n  always @(posedge clk) begin\n    if (!reset_n) begin counter <= 0; led <= 0; end\n    else if (counter == COUNT_MAX - 1) begin counter <= 0; led <= ~led; end\n    else counter <= counter + 1'b1;\n  end\nendmodule";
            ?>
            <div class="scwb-v220__grid scwb-v220__grid--4">
                <?php self::field(__('Project name', 'sustainable-catalyst-workbench'), 'fpga-project', 'text', '', 'heartbeat-controller'); ?>
                <?php self::select(__('HDL', 'sustainable-catalyst-workbench'), 'fpga-language', array('verilog' => 'Verilog', 'systemverilog' => 'SystemVerilog', 'vhdl' => 'VHDL')); ?>
                <?php self::select(__('Board profile', 'sustainable-catalyst-workbench'), 'fpga-board', array('icebreaker' => 'iCEBreaker / iCE40UP5K', 'ulx3s' => 'ULX3S / ECP5', 'arty-a7' => 'Digilent Arty A7', 'generic' => __('Generic FPGA', 'sustainable-catalyst-workbench'))); ?>
                <?php self::field(__('Clock frequency (MHz)', 'sustainable-catalyst-workbench'), 'fpga-clock', 'number', '', '12'); ?>
            </div>
            <?php self::field(__('Top-level HDL', 'sustainable-catalyst-workbench'), 'fpga-source', 'textarea', 'Enter synthesizable HDL.', $sample); ?>
            <?php self::field(__('Pin and timing constraints', 'sustainable-catalyst-workbench'), 'fpga-constraints', 'textarea', 'One signal per line: signal,pin,io-standard,clock-mhz', "clk,35,LVCMOS33,12\nreset_n,10,LVCMOS33,\nled,11,LVCMOS33,"); ?>
            <?php self::field(__('Implementation report', 'sustainable-catalyst-workbench'), 'fpga-report', 'textarea', 'Paste Yosys, nextpnr, Vivado, Quartus, Verilator, or GHDL output for review.'); ?>
            <div class="scwb-v220__actions">
                <?php self::button(__('Generate FPGA project', 'sustainable-catalyst-workbench'), 'fpga-generate'); ?>
                <?php self::button(__('Analyze implementation report', 'sustainable-catalyst-workbench'), 'fpga-analyze'); ?>
                <?php self::button(__('Discover local FPGA tools', 'sustainable-catalyst-workbench'), 'fpga-discover', true); ?>
                <?php self::button(__('Download project bundle', 'sustainable-catalyst-workbench'), 'fpga-download', true); ?>
            </div>
            <div class="scwb-v220__metrics" data-scwb-v220-fpga-metrics></div>
            <div class="scwb-v220__grid scwb-v220__grid--2 scwb-v220__outputs"><pre class="scwb-v220__terminal" data-scwb-v220-fpga-source><?php esc_html_e('Generated HDL and constraints will appear here.', 'sustainable-catalyst-workbench'); ?></pre><pre class="scwb-v220__terminal" data-scwb-v220-fpga-output><?php esc_html_e('No implementation report has been analyzed.', 'sustainable-catalyst-workbench'); ?></pre></div>
            <?php
        }

        private static function render_electronics() {
            ?>
            <div class="scwb-v220__grid scwb-v220__grid--4">
                <?php self::field(__('Design name', 'sustainable-catalyst-workbench'), 'elec-name', 'text', '', 'environmental-sensor-node'); ?>
                <?php self::field(__('Input supply (V)', 'sustainable-catalyst-workbench'), 'elec-vin', 'number', '', '5'); ?>
                <?php self::field(__('Logic rail (V)', 'sustainable-catalyst-workbench'), 'elec-vlogic', 'number', '', '3.3'); ?>
                <?php self::field(__('Estimated load (mA)', 'sustainable-catalyst-workbench'), 'elec-current', 'number', '', '180'); ?>
            </div>
            <?php self::field(__('Functional blocks', 'sustainable-catalyst-workbench'), 'elec-blocks', 'textarea', 'One block per line: reference,type,description', "J1,power-input,USB-C 5 V input\nU1,regulator,3.3 V regulator\nU2,controller,RP2040 microcontroller\nU3,sensor,BME280 environmental sensor\nJ2,debug,SWD header"); ?>
            <?php self::field(__('Interfaces and constraints', 'sustainable-catalyst-workbench'), 'elec-interfaces', 'textarea', 'Document bus voltage, pull-ups, bandwidth, protection, isolation, and environment.', "I2C at 3.3 V; 4.7 kΩ pull-ups\nUSB input requires over-current and ESD review\nOutdoor enclosure; condensation risk\nTarget operating range: -10 °C to 50 °C"); ?>
            <div class="scwb-v220__actions"><?php self::button(__('Review architecture', 'sustainable-catalyst-workbench'), 'elec-review'); ?><?php self::button(__('Download architecture record', 'sustainable-catalyst-workbench'), 'elec-download', true); ?></div>
            <div class="scwb-v220__metrics" data-scwb-v220-elec-metrics></div>
            <pre class="scwb-v220__terminal" data-scwb-v220-elec-output><?php esc_html_e('Architecture review has not run.', 'sustainable-catalyst-workbench'); ?></pre>
            <?php
        }

        private static function render_schematic() {
            ?>
            <?php self::field(__('Component records', 'sustainable-catalyst-workbench'), 'sch-components', 'textarea', 'reference,value,footprint,pins', "J1,USB-C receptacle,USB-C-16P,VBUS|GND|D+|D-\nU1,3.3V regulator,SOT-23-5,VIN|GND|EN|VOUT\nU2,RP2040,QFN-56,IO0|IO1|3V3|GND\nC1,10uF,0603,1|2\nC2,100nF,0402,1|2"); ?>
            <?php self::field(__('Connection records', 'sustainable-catalyst-workbench'), 'sch-nets', 'textarea', 'net,endpoint,endpoint...', "VIN5V,J1.VBUS,U1.VIN,C1.1\nGND,J1.GND,U1.GND,U2.GND,C1.2,C2.2\nVCC3V3,U1.VOUT,U2.3V3,C2.1\nUSB_DP,J1.D+,U2.IO0\nUSB_DM,J1.D-,U2.IO1"); ?>
            <div class="scwb-v220__actions"><?php self::button(__('Validate schematic model', 'sustainable-catalyst-workbench'), 'sch-validate'); ?><?php self::button(__('Download netlist', 'sustainable-catalyst-workbench'), 'sch-netlist', true); ?><?php self::button(__('Download review record', 'sustainable-catalyst-workbench'), 'sch-download', true); ?></div>
            <div class="scwb-v220__metrics" data-scwb-v220-sch-metrics></div>
            <pre class="scwb-v220__terminal" data-scwb-v220-sch-output><?php esc_html_e('The structured schematic has not been validated.', 'sustainable-catalyst-workbench'); ?></pre>
            <?php
        }

        private static function render_bom() {
            $sample = "reference,manufacturer_part,description,quantity,unit_cost,status,substitute\nU1,AP2112K-3.3,3.3 V regulator,1,0.42,active,TLV75533\nU2,RP2040,Microcontroller,1,1.10,active,\nC1,GRM188R60J106ME47,10 uF capacitor,1,0.08,active,CL10A106MQ8NNNC\nC2,C0402C104K8RACTU,100 nF capacitor,4,0.03,active,GRM155R71C104KA88\nJ1,USB4105-GF-A,USB-C receptacle,1,0.76,active,TYPE-C-31-M-12";
            ?>
            <?php self::field(__('Bill of materials CSV', 'sustainable-catalyst-workbench'), 'bom-csv', 'textarea', 'Paste BOM CSV.', $sample); ?>
            <div class="scwb-v220__grid scwb-v220__grid--3">
                <?php self::field(__('Budget ceiling', 'sustainable-catalyst-workbench'), 'bom-budget', 'number', '', '12'); ?>
                <?php self::select(__('Currency', 'sustainable-catalyst-workbench'), 'bom-currency', array('USD' => 'USD', 'EUR' => 'EUR', 'GBP' => 'GBP')); ?>
                <?php self::select(__('Lifecycle policy', 'sustainable-catalyst-workbench'), 'bom-policy', array('strict' => __('Strict: active parts only', 'sustainable-catalyst-workbench'), 'review' => __('Review NRND and unknown', 'sustainable-catalyst-workbench'), 'prototype' => __('Prototype flexibility', 'sustainable-catalyst-workbench'))); ?>
            </div>
            <div class="scwb-v220__actions"><?php self::button(__('Validate BOM', 'sustainable-catalyst-workbench'), 'bom-validate'); ?><?php self::button(__('Export validated BOM', 'sustainable-catalyst-workbench'), 'bom-export', true); ?><?php self::button(__('Download sourcing record', 'sustainable-catalyst-workbench'), 'bom-download', true); ?></div>
            <div class="scwb-v220__metrics" data-scwb-v220-bom-metrics></div>
            <pre class="scwb-v220__terminal" data-scwb-v220-bom-output><?php esc_html_e('No BOM validation has run.', 'sustainable-catalyst-workbench'); ?></pre>
            <?php
        }

        private static function render_pcb() {
            ?>
            <div class="scwb-v220__grid scwb-v220__grid--4">
                <?php self::field(__('Board width (mm)', 'sustainable-catalyst-workbench'), 'pcb-width', 'number', '', '50'); ?>
                <?php self::field(__('Board height (mm)', 'sustainable-catalyst-workbench'), 'pcb-height', 'number', '', '35'); ?>
                <?php self::select(__('Copper layers', 'sustainable-catalyst-workbench'), 'pcb-layers', array('2' => '2', '4' => '4', '6' => '6')); ?>
                <?php self::field(__('Minimum track / space (mm)', 'sustainable-catalyst-workbench'), 'pcb-track', 'number', '', '0.15'); ?>
            </div>
            <div class="scwb-v220__grid scwb-v220__grid--3">
                <?php self::field(__('Minimum via drill (mm)', 'sustainable-catalyst-workbench'), 'pcb-via', 'number', '', '0.30'); ?>
                <?php self::field(__('Edge clearance (mm)', 'sustainable-catalyst-workbench'), 'pcb-edge', 'number', '', '0.25'); ?>
                <?php self::select(__('Environment', 'sustainable-catalyst-workbench'), 'pcb-environment', array('indoor' => __('Indoor controlled', 'sustainable-catalyst-workbench'), 'industrial' => __('Industrial', 'sustainable-catalyst-workbench'), 'outdoor' => __('Outdoor / field', 'sustainable-catalyst-workbench'))); ?>
            </div>
            <?php self::field(__('Placement records', 'sustainable-catalyst-workbench'), 'pcb-placement', 'textarea', 'reference,x_mm,y_mm,rotation,side,class', "J1,4,17.5,90,top,connector\nU1,14,17.5,0,top,power\nU2,28,17.5,0,top,controller\nC1,12,14,0,top,decoupling\nC2,25,14,0,top,decoupling"); ?>
            <div class="scwb-v220__actions"><?php self::button(__('Run preliminary DRC', 'sustainable-catalyst-workbench'), 'pcb-drc'); ?><?php self::button(__('Download board plan', 'sustainable-catalyst-workbench'), 'pcb-download', true); ?></div>
            <div class="scwb-v220__metrics" data-scwb-v220-pcb-metrics></div>
            <pre class="scwb-v220__terminal" data-scwb-v220-pcb-output><?php esc_html_e('Preliminary board checks have not run.', 'sustainable-catalyst-workbench'); ?></pre>
            <?php
        }

        private static function render_validation() {
            ?>
            <div class="scwb-v220__grid scwb-v220__grid--3">
                <?php self::field(__('Device under test', 'sustainable-catalyst-workbench'), 'val-device', 'text', '', 'environmental-sensor-node-rev-a'); ?>
                <?php self::field(__('Revision', 'sustainable-catalyst-workbench'), 'val-revision', 'text', '', 'A'); ?>
                <?php self::select(__('Test stage', 'sustainable-catalyst-workbench'), 'val-stage', array('bring-up' => __('Bring-up', 'sustainable-catalyst-workbench'), 'verification' => __('Design verification', 'sustainable-catalyst-workbench'), 'environmental' => __('Environmental test', 'sustainable-catalyst-workbench'), 'production' => __('Production test', 'sustainable-catalyst-workbench'))); ?>
            </div>
            <?php self::field(__('Test definitions', 'sustainable-catalyst-workbench'), 'val-tests', 'textarea', 'id,measurement,minimum,maximum,unit,method', "PWR-01,3V3 rail,3.20,3.40,V,DMM at TP3\nCUR-01,idle current,0,220,mA,USB power analyzer\nCLK-01,system clock,11.99,12.01,MHz,oscilloscope at CLK test point\nSNS-01,temperature error,-0.5,0.5,°C,reference chamber comparison"); ?>
            <?php self::field(__('Measured results', 'sustainable-catalyst-workbench'), 'val-results', 'textarea', 'id,value,note,evidence', "PWR-01,3.31,stable after 10 minutes,scope-capture-001\nCUR-01,172,normal acquisition mode,power-log-001\nCLK-01,12.0002,clean waveform,scope-capture-002\nSNS-01,0.21,after calibration,calibration-record-004"); ?>
            <div class="scwb-v220__actions"><?php self::button(__('Evaluate test plan', 'sustainable-catalyst-workbench'), 'val-evaluate'); ?><?php self::button(__('Download validation dossier', 'sustainable-catalyst-workbench'), 'val-download', true); ?><?php self::button(__('Export results CSV', 'sustainable-catalyst-workbench'), 'val-csv', true); ?></div>
            <div class="scwb-v220__metrics" data-scwb-v220-val-metrics></div>
            <pre class="scwb-v220__terminal" data-scwb-v220-val-output><?php esc_html_e('No hardware validation has been evaluated.', 'sustainable-catalyst-workbench'); ?></pre>
            <?php
        }
    }

    SCWB_V220_Hardware_Validation::boot();
}
