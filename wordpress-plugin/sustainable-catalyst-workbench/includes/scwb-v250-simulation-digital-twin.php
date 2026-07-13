<?php
/**
 * Sustainable Catalyst Prototyping Workbench v2.5.0.
 * Simulation, Digital Twin, and Systems Modeling Studio.
 */
if (!defined('ABSPATH')) { exit; }

if (!class_exists('SCWB_V250_Simulation_Digital_Twin')) {
final class SCWB_V250_Simulation_Digital_Twin {
    const VERSION = '2.5.0';
    const HANDLE = 'scwb-v250';
    private static $assets_loaded = false;

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_shortcodes'));
        add_filter('do_shortcode_tag', array(__CLASS__, 'append_suite'), 18, 4);
    }

    public static function register_shortcodes() {
        $shortcodes = array(
            'sc_workbench_simulation_studio' => 'simulation',
            'sc_workbench_digital_twin' => 'digital_twin',
            'sc_workbench_systems_modeling' => 'systems',
            'sc_workbench_scenario_sweep' => 'scenario',
            'sc_workbench_monte_carlo' => 'monte_carlo',
            'sc_workbench_model_validation' => 'validation',
        );
        foreach ($shortcodes as $tag => $panel) {
            add_shortcode($tag, function ($atts = array()) use ($panel) {
                return SCWB_V250_Simulation_Digital_Twin::render_panel($panel, $atts);
            });
        }
    }

    public static function append_suite($output, $tag, $attr, $match) {
        $parents = array('sc_workbench_instrumentation_studio', 'sc_workbench_robotics_studio', 'sc_workbench_hardware_studio');
        if (!in_array($tag, $parents, true) || false !== strpos($output, 'data-scwb-v250-suite')) { return $output; }
        $project = isset($attr['project']) ? $attr['project'] : 'default';
        return $output . self::render_suite_launcher($project);
    }

    private static function enqueue_assets() {
        if (self::$assets_loaded) { return; }
        self::$assets_loaded = true;
        $plugin_file = defined('SCWB_V250_PLUGIN_FILE') ? SCWB_V250_PLUGIN_FILE : dirname(__DIR__) . '/sustainable-catalyst-workbench.php';
        $base_url = plugin_dir_url($plugin_file);
        wp_enqueue_style(self::HANDLE, $base_url . 'assets/css/sc-workbench-v250.css', array(), self::VERSION);
        wp_enqueue_script(self::HANDLE, $base_url . 'assets/js/sc-workbench-v250.js', array(), self::VERSION, true);
        wp_localize_script(self::HANDLE, 'SCWBV250', array(
            'version' => self::VERSION,
            'runnerDefaultUrl' => 'http://127.0.0.1:8787',
            'storagePrefix' => 'scwb-v250:',
        ));
    }

    private static function titles() {
        return array(
            'simulation' => __('Dynamic Simulation Studio', 'sustainable-catalyst-workbench'),
            'digital_twin' => __('Digital Twin Studio', 'sustainable-catalyst-workbench'),
            'systems' => __('Systems Modeling Studio', 'sustainable-catalyst-workbench'),
            'scenario' => __('Scenario Sweep and Sensitivity Studio', 'sustainable-catalyst-workbench'),
            'monte_carlo' => __('Monte Carlo and Uncertainty Studio', 'sustainable-catalyst-workbench'),
            'validation' => __('Model Validation and Twin Calibration Studio', 'sustainable-catalyst-workbench'),
        );
    }

    public static function render_panel($panel, $atts = array()) {
        self::enqueue_assets();
        $titles = self::titles();
        $atts = shortcode_atts(array(
            'title' => isset($titles[$panel]) ? $titles[$panel] : __('Simulation Studio', 'sustainable-catalyst-workbench'),
            'project' => 'default',
            'display' => 'full',
        ), $atts);
        $project = sanitize_key($atts['project']) ?: 'default';
        $id = wp_unique_id('scwb-v250-');
        ob_start(); ?>
        <section id="<?php echo esc_attr($id); ?>" class="scwb-v250 scwb-v250--<?php echo esc_attr($panel); ?>" data-scwb-v250-panel="<?php echo esc_attr($panel); ?>" data-scwb-v250-project="<?php echo esc_attr($project); ?>">
            <header class="scwb-v250__header">
                <div><p class="scwb-v250__eyebrow"><?php esc_html_e('Sustainable Catalyst Prototyping Workbench · v2.5.0', 'sustainable-catalyst-workbench'); ?></p><h2><?php echo esc_html($atts['title']); ?></h2></div>
                <span class="scwb-v250__status" data-scwb-v250-status><?php esc_html_e('Browser-local', 'sustainable-catalyst-workbench'); ?></span>
            </header>
            <?php self::render_body($panel); ?>
            <p class="scwb-v250__boundary"><?php esc_html_e('Research and prototyping support only. Treat models as explicit approximations. Verify equations, units, parameter ranges, numerical stability, calibration data, uncertainty assumptions, boundary conditions, and decision consequences against field evidence and qualified review.', 'sustainable-catalyst-workbench'); ?></p>
        </section>
        <?php return ob_get_clean();
    }

    private static function field($label, $name, $type = 'text', $value = '', $placeholder = '', $wide = false) { ?>
        <label class="scwb-v250__field<?php echo $wide ? ' scwb-v250__field--wide' : ''; ?>"><span><?php echo esc_html($label); ?></span>
            <?php if ('textarea' === $type) : ?><textarea data-scwb-v250-field="<?php echo esc_attr($name); ?>" placeholder="<?php echo esc_attr($placeholder); ?>"><?php echo esc_textarea($value); ?></textarea>
            <?php else : ?><input type="<?php echo esc_attr($type); ?>" data-scwb-v250-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>" placeholder="<?php echo esc_attr($placeholder); ?>"><?php endif; ?>
        </label>
    <?php }

    private static function select($label, $name, $options, $wide = false) { ?>
        <label class="scwb-v250__field<?php echo $wide ? ' scwb-v250__field--wide' : ''; ?>"><span><?php echo esc_html($label); ?></span><select data-scwb-v250-field="<?php echo esc_attr($name); ?>">
            <?php foreach ($options as $value => $text) : ?><option value="<?php echo esc_attr($value); ?>"><?php echo esc_html($text); ?></option><?php endforeach; ?>
        </select></label>
    <?php }

    private static function actions($primary = 'Run analysis') { ?>
        <div class="scwb-v250__actions">
            <button type="button" class="scwb-v250__button scwb-v250__button--primary" data-scwb-v250-action="analyze"><?php echo esc_html($primary); ?></button>
            <button type="button" class="scwb-v250__button" data-scwb-v250-action="save"><?php esc_html_e('Save locally', 'sustainable-catalyst-workbench'); ?></button>
            <button type="button" class="scwb-v250__button" data-scwb-v250-action="export"><?php esc_html_e('Export JSON', 'sustainable-catalyst-workbench'); ?></button>
        </div>
        <div class="scwb-v250__results" data-scwb-v250-results aria-live="polite"><p><?php esc_html_e('Enter model parameters, then run the analysis.', 'sustainable-catalyst-workbench'); ?></p></div>
    <?php }

    private static function render_body($panel) {
        if ('simulation' === $panel) { ?>
            <div class="scwb-v250__grid">
                <?php self::select('Dynamic model', 'model_type', array('first_order' => 'First-order process', 'logistic' => 'Logistic growth', 'damped' => 'Damped oscillator')); ?>
                <?php self::select('Numerical solver', 'solver', array('rk4' => 'Runge–Kutta 4', 'euler' => 'Explicit Euler')); ?>
                <?php self::field('Initial state x(0)', 'initial_state', 'number', '0'); ?>
                <?php self::field('Input / forcing u', 'input_value', 'number', '10'); ?>
                <?php self::field('Gain or growth rate', 'gain', 'number', '1.5'); ?>
                <?php self::field('Time constant / damping', 'time_constant', 'number', '4'); ?>
                <?php self::field('Capacity / natural frequency', 'capacity', 'number', '100'); ?>
                <?php self::field('Time step Δt', 'time_step', 'number', '0.1'); ?>
                <?php self::field('Duration', 'duration', 'number', '30'); ?>
                <?php self::field('Units', 'units', 'text', 'engineering units'); ?>
            </div>
            <?php self::actions('Run simulation');
        } elseif ('digital_twin' === $panel) { ?>
            <div class="scwb-v250__grid">
                <?php self::field('Twin name', 'twin_name', 'text', 'Thermal process twin'); ?>
                <?php self::field('Initial state', 'initial_state', 'number', '20'); ?>
                <?php self::field('Model gain', 'gain', 'number', '0.8'); ?>
                <?php self::field('Time constant', 'time_constant', 'number', '5'); ?>
                <?php self::field('Calibration search ± (%)', 'search_percent', 'number', '40'); ?>
                <?php self::field('Observed stream (time,input,observed)', 'twin_csv', 'textarea', "time,input,observed\n0,20,20.0\n1,30,21.5\n2,30,23.0\n3,30,24.2\n4,25,24.4\n5,25,24.5", 'time,input,observed', true); ?>
            </div>
            <?php self::actions('Evaluate twin');
        } elseif ('systems' === $panel) { ?>
            <div class="scwb-v250__grid">
                <?php self::field('State names', 'state_names', 'text', 'resource,demand'); ?>
                <?php self::field('System matrix A', 'matrix_a', 'textarea', "-0.20,-0.05\n0.08,-0.15", 'One matrix row per line', true); ?>
                <?php self::field('Initial state vector x₀', 'initial_vector', 'text', '100,40'); ?>
                <?php self::field('Constant input vector b', 'input_vector', 'text', '10,2'); ?>
                <?php self::field('Time step Δt', 'time_step', 'number', '0.1'); ?>
                <?php self::field('Duration', 'duration', 'number', '50'); ?>
                <?php self::select('Solver', 'solver', array('rk4' => 'Runge–Kutta 4', 'euler' => 'Explicit Euler')); ?>
            </div>
            <?php self::actions('Simulate system');
        } elseif ('scenario' === $panel) { ?>
            <div class="scwb-v250__grid">
                <?php self::select('Scenario model', 'scenario_model', array('first_order' => 'First-order final state', 'logistic' => 'Logistic final state', 'linear' => 'Linear outcome')); ?>
                <?php self::select('Swept parameter', 'parameter', array('gain' => 'Gain / growth rate', 'time_constant' => 'Time constant', 'input_value' => 'Input / forcing', 'capacity' => 'Capacity', 'coefficient' => 'Linear coefficient')); ?>
                <?php self::field('Minimum value', 'minimum', 'number', '0.5'); ?>
                <?php self::field('Maximum value', 'maximum', 'number', '2.5'); ?>
                <?php self::field('Steps', 'steps', 'number', '21'); ?>
                <?php self::field('Baseline input', 'input_value', 'number', '10'); ?>
                <?php self::field('Baseline gain', 'gain', 'number', '1.5'); ?>
                <?php self::field('Baseline time constant', 'time_constant', 'number', '4'); ?>
                <?php self::field('Capacity', 'capacity', 'number', '100'); ?>
                <?php self::field('Duration', 'duration', 'number', '30'); ?>
            </div>
            <?php self::actions('Run parameter sweep');
        } elseif ('monte_carlo' === $panel) { ?>
            <div class="scwb-v250__grid">
                <?php self::field('Simulation runs', 'runs', 'number', '5000'); ?>
                <?php self::field('Random seed', 'seed', 'number', '2026'); ?>
                <?php self::field('Output intercept', 'intercept', 'number', '5'); ?>
                <?php self::field('Decision threshold', 'threshold', 'number', '25'); ?>
                <?php self::field('Uncertain inputs (name,mean,std,min,max,distribution)', 'variables_csv', 'textarea', "name,mean,std,min,max,distribution\nefficiency,0.80,0.05,0.60,0.95,normal\nload,20,3,10,30,normal\ncost_factor,1.0,0.15,0.6,1.5,triangular", 'normal, uniform, or triangular', true); ?>
                <?php self::field('Linear coefficients (name,coefficient)', 'coefficients_csv', 'textarea', "name,coefficient\nefficiency,12\nload,0.8\ncost_factor,-4", 'name,coefficient', true); ?>
            </div>
            <?php self::actions('Run Monte Carlo');
        } elseif ('validation' === $panel) { ?>
            <div class="scwb-v250__grid">
                <?php self::field('Observed and predicted values', 'validation_csv', 'textarea', "observed,predicted\n10,9.7\n12,12.3\n15,14.6\n18,18.5\n20,19.8\n25,24.1", 'observed,predicted', true); ?>
                <?php self::field('Maximum RMSE', 'max_rmse', 'number', '1.5'); ?>
                <?php self::field('Maximum absolute bias', 'max_bias', 'number', '0.5'); ?>
                <?php self::field('Minimum R²', 'min_r2', 'number', '0.95'); ?>
                <?php self::field('Maximum MAPE (%)', 'max_mape', 'number', '10'); ?>
                <?php self::select('Calibration recommendation', 'calibration_mode', array('linear' => 'Fit linear correction', 'none' => 'Metrics only')); ?>
            </div>
            <?php self::actions('Validate model');
        }
    }

    public static function render_suite_launcher($project = 'default') {
        self::enqueue_assets();
        $project = sanitize_key($project) ?: 'default';
        $modules = array(
            array('Dynamic Simulation', 'First-order, logistic, and damped-system simulations with Euler or RK4 integration.', '[sc_workbench_simulation_studio project="' . $project . '"]'),
            array('Digital Twin', 'Compare measured streams to model behavior and calibrate a transparent first-order twin.', '[sc_workbench_digital_twin project="' . $project . '"]'),
            array('Systems Modeling', 'Simulate coupled linear state systems with explicit matrices, states, and forcing.', '[sc_workbench_systems_modeling project="' . $project . '"]'),
            array('Scenario Sweep', 'Run parameter sweeps and identify sensitivity, monotonicity, and outcome ranges.', '[sc_workbench_scenario_sweep project="' . $project . '"]'),
            array('Monte Carlo', 'Propagate parameter uncertainty through a transparent linear response model.', '[sc_workbench_monte_carlo project="' . $project . '"]'),
            array('Model Validation', 'Calculate residual metrics, acceptance checks, and linear correction records.', '[sc_workbench_model_validation project="' . $project . '"]'),
        );
        ob_start(); ?>
        <section class="scwb-v250 scwb-v250__suite" data-scwb-v250-suite data-scwb-v250-project="<?php echo esc_attr($project); ?>">
            <header class="scwb-v250__header"><div><p class="scwb-v250__eyebrow"><?php esc_html_e('Workbench v2.5.0', 'sustainable-catalyst-workbench'); ?></p><h2><?php esc_html_e('Simulation, Digital Twin, and Systems Modeling Modules', 'sustainable-catalyst-workbench'); ?></h2></div></header>
            <div class="scwb-v250__module-grid"><?php foreach ($modules as $module) : ?><article class="scwb-v250__module-card"><h3><?php echo esc_html($module[0]); ?></h3><p><?php echo esc_html($module[1]); ?></p><code><?php echo esc_html($module[2]); ?></code></article><?php endforeach; ?></div>
        </section>
        <?php return ob_get_clean();
    }
}
SCWB_V250_Simulation_Digital_Twin::boot();
}
