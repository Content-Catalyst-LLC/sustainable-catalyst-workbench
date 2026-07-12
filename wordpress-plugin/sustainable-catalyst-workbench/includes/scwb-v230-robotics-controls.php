<?php
/**
 * Sustainable Catalyst Prototyping Workbench v2.3.0.
 * Robotics, Controls, and Mechatronics Studio.
 */
if (!defined('ABSPATH')) { exit; }

if (!class_exists('SCWB_V230_Robotics_Controls')) {
final class SCWB_V230_Robotics_Controls {
    const VERSION = '2.3.0';
    const HANDLE = 'scwb-v230';
    private static $assets_loaded = false;

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_shortcodes'));
        add_filter('do_shortcode_tag', array(__CLASS__, 'append_suite'), 16, 4);
    }

    public static function register_shortcodes() {
        $shortcodes = array(
            'sc_workbench_robotics_studio' => 'robotics',
            'sc_workbench_controls_studio' => 'controls',
            'sc_workbench_mechatronics_studio' => 'mechatronics',
            'sc_workbench_actuator_studio' => 'actuators',
            'sc_workbench_state_machine_studio' => 'state-machine',
            'sc_workbench_hil_validation' => 'hil',
        );
        foreach ($shortcodes as $tag => $panel) {
            add_shortcode($tag, function ($atts = array()) use ($panel) {
                return SCWB_V230_Robotics_Controls::render_panel($panel, $atts);
            });
        }
    }

    public static function append_suite($output, $tag, $attr, $match) {
        if (!in_array($tag, array('sc_workbench_hardware_studio', 'sc_workbench_embedded_device_studio'), true) || false !== strpos($output, 'data-scwb-v230-suite')) {
            return $output;
        }
        $project = isset($attr['project']) ? $attr['project'] : 'default';
        return $output . self::render_suite_launcher($project);
    }

    private static function enqueue_assets() {
        if (self::$assets_loaded) { return; }
        self::$assets_loaded = true;
        $plugin_file = defined('SCWB_V230_PLUGIN_FILE') ? SCWB_V230_PLUGIN_FILE : dirname(__DIR__) . '/sustainable-catalyst-workbench.php';
        $base_url = plugin_dir_url($plugin_file);
        wp_enqueue_style(self::HANDLE, $base_url . 'assets/css/sc-workbench-v230.css', array(), self::VERSION);
        wp_enqueue_script(self::HANDLE, $base_url . 'assets/js/sc-workbench-v230.js', array(), self::VERSION, true);
        wp_localize_script(self::HANDLE, 'SCWBV230', array(
            'version' => self::VERSION,
            'runnerDefaultUrl' => 'http://127.0.0.1:8787',
            'storagePrefix' => 'scwb-v230:',
            'labels' => array('saved' => __('Saved locally', 'sustainable-catalyst-workbench'), 'ready' => __('Ready', 'sustainable-catalyst-workbench'), 'invalid' => __('Review required', 'sustainable-catalyst-workbench')),
        ));
    }

    private static function titles() {
        return array(
            'robotics' => __('Robotics Studio', 'sustainable-catalyst-workbench'),
            'controls' => __('Controls and PID Studio', 'sustainable-catalyst-workbench'),
            'mechatronics' => __('Mechatronics Architecture Studio', 'sustainable-catalyst-workbench'),
            'actuators' => __('Actuator and Motor Sizing Studio', 'sustainable-catalyst-workbench'),
            'state-machine' => __('Robot State Machine Studio', 'sustainable-catalyst-workbench'),
            'hil' => __('Hardware-in-the-Loop and Telemetry Validation', 'sustainable-catalyst-workbench'),
        );
    }

    public static function render_panel($panel, $atts = array()) {
        self::enqueue_assets();
        $titles = self::titles();
        $atts = shortcode_atts(array('title' => $titles[$panel] ?? __('Robotics Studio', 'sustainable-catalyst-workbench'), 'project' => 'default', 'display' => 'full'), $atts);
        $project = sanitize_key($atts['project']) ?: 'default';
        $id = wp_unique_id('scwb-v230-');
        ob_start(); ?>
        <section id="<?php echo esc_attr($id); ?>" class="scwb-v230 scwb-v230--<?php echo esc_attr($panel); ?>" data-scwb-v230-panel="<?php echo esc_attr($panel); ?>" data-scwb-v230-project="<?php echo esc_attr($project); ?>">
            <header class="scwb-v230__header"><div><p class="scwb-v230__eyebrow"><?php esc_html_e('Sustainable Catalyst Prototyping Workbench · v2.3.0', 'sustainable-catalyst-workbench'); ?></p><h2><?php echo esc_html($atts['title']); ?></h2></div><span class="scwb-v230__status" data-scwb-v230-status><?php esc_html_e('Browser-local', 'sustainable-catalyst-workbench'); ?></span></header>
            <?php self::render_body($panel); ?>
            <p class="scwb-v230__boundary"><?php esc_html_e('Prototype and analytical support only. Verify loads, voltages, current limits, torque, speed, stopping behavior, fault handling, interlocks, mechanical clearances, control stability, and safe states on the actual system with qualified engineering review.', 'sustainable-catalyst-workbench'); ?></p>
        </section><?php return ob_get_clean();
    }

    private static function field($label, $name, $type = 'text', $value = '', $placeholder = '') { ?>
        <label class="scwb-v230__field"><span><?php echo esc_html($label); ?></span><?php if ('textarea' === $type) : ?><textarea data-scwb-v230-field="<?php echo esc_attr($name); ?>" placeholder="<?php echo esc_attr($placeholder); ?>"><?php echo esc_textarea($value); ?></textarea><?php else : ?><input type="<?php echo esc_attr($type); ?>" data-scwb-v230-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>" placeholder="<?php echo esc_attr($placeholder); ?>"><?php endif; ?></label><?php
    }
    private static function select($label, $name, $options) { ?><label class="scwb-v230__field"><span><?php echo esc_html($label); ?></span><select data-scwb-v230-field="<?php echo esc_attr($name); ?>"><?php foreach ($options as $value => $text) : ?><option value="<?php echo esc_attr($value); ?>"><?php echo esc_html($text); ?></option><?php endforeach; ?></select></label><?php }
    private static function actions($primary = 'Analyze') { ?><div class="scwb-v230__actions"><button type="button" class="scwb-v230__button scwb-v230__button--primary" data-scwb-v230-action="analyze"><?php echo esc_html($primary); ?></button><button type="button" class="scwb-v230__button" data-scwb-v230-action="save"><?php esc_html_e('Save locally', 'sustainable-catalyst-workbench'); ?></button><button type="button" class="scwb-v230__button" data-scwb-v230-action="export"><?php esc_html_e('Export JSON', 'sustainable-catalyst-workbench'); ?></button></div><div class="scwb-v230__results" data-scwb-v230-results aria-live="polite"><p>Enter project values and run the analysis.</p></div><?php }

    private static function render_body($panel) {
        switch ($panel) {
            case 'robotics': self::render_robotics(); break;
            case 'controls': self::render_controls(); break;
            case 'mechatronics': self::render_mechatronics(); break;
            case 'actuators': self::render_actuators(); break;
            case 'state-machine': self::render_state_machine(); break;
            case 'hil': self::render_hil(); break;
        }
    }

    private static function render_robotics() { ?><div class="scwb-v230__grid"><?php self::select('Drive model', 'drive_model', array('differential'=>'Differential drive','ackermann'=>'Ackermann steering','omnidirectional'=>'Omnidirectional')); self::field('Wheel diameter (mm)', 'wheel_diameter_mm', 'number', '100'); self::field('Track width / wheelbase (mm)', 'track_width_mm', 'number', '300'); self::field('Left wheel speed (RPM)', 'left_rpm', 'number', '60'); self::field('Right wheel speed (RPM)', 'right_rpm', 'number', '60'); self::field('Payload mass (kg)', 'payload_kg', 'number', '5'); ?></div><?php self::actions('Calculate motion'); }
    private static function render_controls() { ?><div class="scwb-v230__grid"><?php self::field('Proportional gain Kp', 'kp', 'number', '1.2'); self::field('Integral gain Ki', 'ki', 'number', '0.3'); self::field('Derivative gain Kd', 'kd', 'number', '0.05'); self::field('Plant gain', 'plant_gain', 'number', '1'); self::field('Plant time constant (s)', 'tau', 'number', '1'); self::field('Setpoint', 'setpoint', 'number', '1'); self::field('Simulation duration (s)', 'duration', 'number', '10'); self::field('Step interval (s)', 'dt', 'number', '0.02'); ?></div><?php self::actions('Simulate control loop'); }
    private static function render_mechatronics() { ?><div class="scwb-v230__grid"><?php self::field('System name', 'system_name', 'text', 'Mobile research robot'); self::field('Supply voltage (V)', 'supply_v', 'number', '12'); self::field('Continuous current budget (A)', 'current_budget_a', 'number', '5'); self::field('Controller', 'controller', 'text', 'Raspberry Pi + microcontroller'); self::field('Sensors, one per line', 'sensors', 'textarea', "encoder\nIMU\ndistance sensor"); self::field('Actuators, one per line', 'actuators', 'textarea', "left motor\nright motor"); self::field('Safety mechanisms, one per line', 'safety', 'textarea', "emergency stop\ncurrent limit\nwatchdog"); ?></div><?php self::actions('Review architecture'); }
    private static function render_actuators() { ?><div class="scwb-v230__grid"><?php self::select('Actuator type', 'actuator_type', array('dc-motor'=>'DC motor','stepper'=>'Stepper motor','servo'=>'Servo','linear'=>'Linear actuator')); self::field('Moving mass / load (kg)', 'mass_kg', 'number', '5'); self::field('Wheel or lever radius (m)', 'radius_m', 'number', '0.05'); self::field('Target acceleration (m/s²)', 'acceleration', 'number', '1'); self::field('Rolling/friction coefficient', 'friction', 'number', '0.05'); self::field('Safety factor', 'safety_factor', 'number', '2'); self::field('Target speed (RPM)', 'target_rpm', 'number', '120'); self::field('Supply voltage (V)', 'voltage', 'number', '12'); self::field('Assumed efficiency (0–1)', 'efficiency', 'number', '0.75'); ?></div><?php self::actions('Size actuator'); }
    private static function render_state_machine() { ?><div class="scwb-v230__grid"><?php self::field('Initial state', 'initial_state', 'text', 'IDLE'); self::field('States, one per line', 'states', 'textarea', "IDLE\nARMED\nMOVING\nFAULT\nSAFE_STOP"); self::field('Transitions: FROM,event,TO', 'transitions', 'textarea', "IDLE,start,ARMED\nARMED,go,MOVING\nMOVING,stop,IDLE\nMOVING,fault,FAULT\nFAULT,reset,SAFE_STOP\nSAFE_STOP,clear,IDLE"); self::field('Required safe states', 'safe_states', 'textarea', "IDLE\nSAFE_STOP"); ?></div><?php self::actions('Validate state machine'); }
    private static function render_hil() { ?><div class="scwb-v230__grid"><?php self::field('Telemetry CSV', 'telemetry_csv', 'textarea', "time,setpoint,measured,current,temp\n0,0,0,0.2,24\n1,1,0.65,1.3,26\n2,1,0.91,1.1,28\n3,1,0.99,1.0,29"); self::field('Measured-value tolerance', 'tolerance', 'number', '0.1'); self::field('Maximum current (A)', 'max_current', 'number', '2'); self::field('Maximum temperature (°C)', 'max_temp', 'number', '60'); self::field('Required sample count', 'min_samples', 'number', '4'); ?></div><?php self::actions('Evaluate telemetry'); }

    private static function render_suite_launcher($project) {
        self::enqueue_assets();
        $modules = array(
            'robotics_studio'=>array('Robotics Studio','Model drive kinematics, speed, turning rate, and payload context.'),
            'controls_studio'=>array('Controls Studio','Simulate a PID loop and inspect overshoot, settling, and steady-state error.'),
            'mechatronics_studio'=>array('Mechatronics Architecture','Review controllers, sensors, actuators, power, and safety layers.'),
            'actuator_studio'=>array('Actuator Sizing','Estimate torque, power, speed, current, and safety-factor requirements.'),
            'state_machine_studio'=>array('Robot State Machines','Validate state reachability, transitions, and safe-state coverage.'),
            'hil_validation'=>array('HIL and Telemetry','Evaluate measured response, current, temperature, and acceptance limits.'),
        );
        ob_start(); ?><section class="scwb-v230 scwb-v230__suite" data-scwb-v230-suite data-scwb-v230-project="<?php echo esc_attr(sanitize_key($project)); ?>"><header class="scwb-v230__header"><div><p class="scwb-v230__eyebrow">Workbench v2.3.0 expansion</p><h2>Robotics, Controls, and Mechatronics Studio</h2></div><span class="scwb-v230__status">Control layer active</span></header><div class="scwb-v230__module-grid"><?php foreach ($modules as $shortcode=>$content): ?><article class="scwb-v230__module-card"><h3><?php echo esc_html($content[0]); ?></h3><p><?php echo esc_html($content[1]); ?></p><code>[sc_workbench_<?php echo esc_html($shortcode); ?> project="<?php echo esc_html(sanitize_key($project)); ?>"]</code></article><?php endforeach; ?></div></section><?php return ob_get_clean();
    }
}
SCWB_V230_Robotics_Controls::boot();
}
