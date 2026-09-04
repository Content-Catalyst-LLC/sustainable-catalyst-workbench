<?php
/** Workbench v5.1.0 — Universal Mathematics & CAS Engine Foundation. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V510_Mathematics {
    const VERSION = '5.1.0';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 60);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V510_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v510.css';
        $js = $base . '/assets/js/sc-workbench-v510.js';
        wp_register_style('scwb-v510', plugins_url('assets/css/sc-workbench-v510.css', SCWB_V510_PLUGIN_FILE), array(), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v510', plugins_url('assets/js/sc-workbench-v510.js', SCWB_V510_PLUGIN_FILE), array(), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_mathematics' => 'workspace',
            'sc_workbench_cas' => 'algebra',
            'sc_workbench_equation_solver' => 'solve',
            'sc_workbench_calculus' => 'calculus',
            'sc_workbench_math_objects' => 'objects',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, function($atts) use ($panel) {
                    $atts = shortcode_atts(array(
                        'project' => 'default',
                        'display' => 'full',
                        'title' => 'Universal Mathematics',
                        'backend' => '',
                    ), $atts);
                    return SCWB_V510_Mathematics::render($atts, $panel);
                });
            }
        }
    }

    public static function backend_url($override = '') {
        $candidate = trim((string) $override);
        if (!$candidate && defined('SCWB_WORKBENCH_BACKEND_URL')) {
            $candidate = trim((string) SCWB_WORKBENCH_BACKEND_URL);
        }
        if (function_exists('apply_filters')) {
            $candidate = (string) apply_filters('scwb_workbench_backend_url', $candidate);
        }
        return rtrim($candidate, '/');
    }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/mathematics-status', array(
            'methods' => 'GET',
            'callback' => array(__CLASS__, 'status'),
            'permission_callback' => '__return_true',
        ));
    }

    public static function status() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-mathematics-interface-status/1.0',
            'version' => self::VERSION,
            'engine' => 'SymPy CAS through Workbench Python backend',
            'backendConfigured' => '' !== self::backend_url(),
            'capabilities' => array('exact arithmetic','simplify','expand','factor','numeric evaluation','equation solving','systems','differentiation','integration','limits','series','substitution','canonical math objects'),
            'arbitraryCodeExecutionAuthorized' => false,
            'pythonEvalAuthorized' => false,
            'remoteShellAuthorized' => false,
        ));
    }

    private static function enqueue_assets($backend = '') {
        self::register_assets();
        wp_enqueue_style('scwb-v510');
        wp_enqueue_script('scwb-v510');
        wp_localize_script('scwb-v510', 'SCWBV510Config', array(
            'version' => self::VERSION,
            'backendUrl' => self::backend_url($backend),
        ));
    }

    private static function field($label, $name, $value = '', $type = 'text', $wide = false) {
        ?><label class="scwb-v510__field<?php echo $wide ? ' is-wide' : ''; ?>"><span><?php echo esc_html($label); ?></span><?php
        if ('textarea' === $type) { ?><textarea data-scwb-v510-field="<?php echo esc_attr($name); ?>"><?php echo esc_textarea($value); ?></textarea><?php }
        else { ?><input type="<?php echo esc_attr($type); ?>" data-scwb-v510-field="<?php echo esc_attr($name); ?>" value="<?php echo esc_attr($value); ?>"><?php }
        ?></label><?php
    }

    public static function render($atts, $panel = 'workspace') {
        self::enqueue_assets(isset($atts['backend']) ? $atts['backend'] : '');
        $project = sanitize_key($atts['project']) ?: 'default';
        $instance = 'scwb-v510-' . wp_generate_uuid4();
        $tabs = array('workspace'=>'Overview','algebra'=>'Algebra / CAS','solve'=>'Solve','calculus'=>'Calculus','objects'=>'Math Objects');
        ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v510" data-scwb-v510 data-panel="<?php echo esc_attr($panel); ?>" data-project="<?php echo esc_attr($project); ?>" data-version="5.1.0">
            <header class="scwb-v510__header">
                <div><p class="scwb-v510__eyebrow">Sustainable Catalyst Workbench · Mathematics Engine v5.1.0</p><h2><?php echo esc_html($atts['title']); ?></h2><p>Exact symbolic mathematics, equation solving, calculus, arbitrary-precision evaluation, and reusable canonical math objects powered by the Workbench Python compute service.</p></div>
                <span class="scwb-v510__status" data-scwb-v510-status>Checking CAS backend…</span>
            </header>
            <nav class="scwb-v510__tabs" role="tablist" aria-label="Mathematics tools"><?php foreach ($tabs as $key=>$label): ?><button type="button" role="tab" data-scwb-v510-tab="<?php echo esc_attr($key); ?>" class="<?php echo $key===$panel?'is-active':''; ?>" aria-selected="<?php echo $key===$panel?'true':'false'; ?>"><?php echo esc_html($label); ?></button><?php endforeach; ?></nav>
            <div class="scwb-v510__views">
                <section class="scwb-v510__view<?php echo 'workspace'===$panel?' is-active':''; ?>" data-scwb-v510-view="workspace" <?php echo 'workspace'===$panel?'':'hidden'; ?>>
                    <h3>Universal mathematics foundation</h3><p>This first gap-closing build makes one mathematical object usable across exact algebra, numeric evaluation, solving, and calculus. Interactive linked graphing is available in the v5.2 Graph Mathematics studio.</p>
                    <div class="scwb-v510__cards"><article><strong>Exact</strong><span>Preserve fractions, radicals, constants, and symbolic forms.</span></article><article><strong>Compute</strong><span>Simplify, expand, factor, solve, differentiate, integrate, limit, and series.</span></article><article><strong>Reusable</strong><span>Every result carries LaTeX, free symbols, precision, operation provenance, and a content hash.</span></article></div>
                </section>
                <section class="scwb-v510__view<?php echo 'algebra'===$panel?' is-active':''; ?>" data-scwb-v510-view="algebra" <?php echo 'algebra'===$panel?'':'hidden'; ?>>
                    <h3>Algebra / CAS</h3><div class="scwb-v510__grid"><?php self::field('Expression','expression','x^2 + 4*x - 12','textarea',true); self::field('Precision','precision','15','number'); ?></div>
                    <div class="scwb-v510__actions"><button data-scwb-v510-action="simplify">Simplify</button><button data-scwb-v510-action="expand">Expand</button><button data-scwb-v510-action="factor">Factor</button><button data-scwb-v510-action="evaluate">Evaluate</button></div>
                </section>
                <section class="scwb-v510__view<?php echo 'solve'===$panel?' is-active':''; ?>" data-scwb-v510-view="solve" <?php echo 'solve'===$panel?'':'hidden'; ?>>
                    <h3>Equation solver</h3><div class="scwb-v510__grid"><?php self::field('Equations — one per line','equations','x^2 + 4*x - 12 = 0','textarea',true); self::field('Variables — comma separated','variables','x'); ?></div>
                    <div class="scwb-v510__actions"><button data-scwb-v510-action="solve">Solve exactly</button></div>
                </section>
                <section class="scwb-v510__view<?php echo 'calculus'===$panel?' is-active':''; ?>" data-scwb-v510-view="calculus" <?php echo 'calculus'===$panel?'':'hidden'; ?>>
                    <h3>Calculus</h3><div class="scwb-v510__grid"><?php self::field('Expression','calculus_expression','sin(x)*exp(x)','textarea',true); self::field('Variable','variable','x'); self::field('Order','order','1','number'); self::field('Lower bound (optional)','lower',''); self::field('Upper bound (optional)','upper',''); self::field('Point','point','0'); self::field('Series order','series_order','6','number'); ?></div>
                    <div class="scwb-v510__actions"><button data-scwb-v510-action="differentiate">Differentiate</button><button data-scwb-v510-action="integrate">Integrate</button><button data-scwb-v510-action="limit">Limit</button><button data-scwb-v510-action="series">Series</button></div>
                </section>
                <section class="scwb-v510__view<?php echo 'objects'===$panel?' is-active':''; ?>" data-scwb-v510-view="objects" <?php echo 'objects'===$panel?'':'hidden'; ?>>
                    <h3>Canonical math object</h3><p>Parse an expression or equation without changing it, producing the portable object contract future graph, table, matrix, and Lab handoffs will share.</p><div class="scwb-v510__grid"><?php self::field('Expression or equation','object_expression','a*x^2 + b*x + c = 0','textarea',true); ?></div><div class="scwb-v510__actions"><button data-scwb-v510-action="parse">Build math object</button></div>
                </section>
            </div>
            <aside class="scwb-v510__output"><header><strong>Mathematics result</strong><span data-scwb-v510-message aria-live="polite">Ready.</span></header><div class="scwb-v510__result" data-scwb-v510-result><div><small>Exact</small><code data-scwb-v510-exact>—</code></div><div><small>Decimal</small><code data-scwb-v510-decimal>—</code></div><div><small>LaTeX</small><code data-scwb-v510-latex>—</code></div></div><details><summary>Structured math object</summary><pre data-scwb-v510-output>{}</pre></details></aside>
            <footer class="scwb-v510__boundary"><strong>Execution boundary</strong><span>Mathematical expressions are parsed through a restricted allow-list. Python eval/exec, imports, filesystem access, remote shell access, and arbitrary code execution are not authorized.</span></footer>
        </section><?php return ob_get_clean();
    }
}
SCWB_V510_Mathematics::boot();
