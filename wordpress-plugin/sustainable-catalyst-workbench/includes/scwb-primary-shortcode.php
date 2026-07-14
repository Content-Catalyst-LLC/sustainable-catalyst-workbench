<?php
/** Canonical Workbench v4.1.0 primary shortcode and studio router. */
if (!defined('ABSPATH')) {
    exit;
}

final class SCWB_Primary_Shortcode_Repair {
    const VERSION = '4.1.0';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 4);
        add_action('init', array(__CLASS__, 'register_shortcode'), 1000);
        add_action('wp_loaded', array(__CLASS__, 'register_shortcode'), 1000);
    }

    public static function register_assets() {
        $plugin_file = defined('SCWB_V301_PLUGIN_FILE') ? SCWB_V301_PLUGIN_FILE : dirname(__DIR__) . '/sustainable-catalyst-workbench.php';
        $base = dirname($plugin_file);
        $css = $base . '/assets/css/scwb-primary-repair.css';
        $js = $base . '/assets/js/scwb-primary-repair.js';
        wp_register_style('scwb-primary-repair', plugins_url('assets/css/scwb-primary-repair.css', $plugin_file), array(), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-primary-repair', plugins_url('assets/js/scwb-primary-repair.js', $plugin_file), array(), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_shortcode() {
        // v3.0.1 deliberately owns the canonical public shortcode. This removes
        // stale add-on callbacks that previously left the page rendering an old
        // selector or the literal shortcode text.
        if (shortcode_exists('sc_workbench')) {
            remove_shortcode('sc_workbench');
        }
        add_shortcode('sc_workbench', array(__CLASS__, 'render'));
    }

    private static function studios() {
        if (class_exists('SCWB_V301_Production_Reliability')) {
            return SCWB_V301_Production_Reliability::studio_catalog();
        }
        return array();
    }

    private static function enqueue_assets() {
        self::register_assets();
        wp_enqueue_style('scwb-primary-repair');
        wp_enqueue_script('scwb-primary-repair');
        if (class_exists('SCWB_V301_Production_Reliability')) {
            SCWB_V301_Production_Reliability::register_assets();
            wp_enqueue_style('scwb-v301');
            wp_enqueue_script('scwb-v301');
        }
    }

    private static function render_studio($studio, $project, $key) {
        if (!shortcode_exists($studio['shortcode'])) {
            return sprintf(
                '<div class="scwb-primary__module-error" role="alert"><strong>%s is unavailable.</strong><p>The shortcode <code>[%s]</code> is not registered. Install the complete Workbench v4.1.0 plugin and clear all caches.</p></div>',
                esc_html($studio['label']),
                esc_html($studio['shortcode'])
            );
        }

        $source = sprintf('[%s project="%s" display="full"]', $studio['shortcode'], esc_attr($project));
        try {
            $output = do_shortcode($source);
        } catch (Throwable $error) {
            return sprintf(
                '<div class="scwb-primary__module-error" role="alert"><strong>%s failed to render.</strong><p>%s</p></div>',
                esc_html($studio['label']),
                esc_html($error->getMessage())
            );
        }

        if (!is_string($output) || '' === trim($output) || false !== strpos($output, '[' . $studio['shortcode'])) {
            return sprintf(
                '<div class="scwb-primary__module-error" role="alert"><strong>%s returned no usable interface.</strong><p>Verify the module file, shortcode registration, and asset loader for <code>[%s]</code>.</p></div>',
                esc_html($studio['label']),
                esc_html($studio['shortcode'])
            );
        }

        return '<div class="scwb-primary__module-mount" data-scwb-module-mount data-scwb-module-state="ready">' . $output . '</div>';
    }

    public static function render($atts = array()) {
        self::enqueue_assets();
        $atts = shortcode_atts(array(
            'topic' => 'workbench',
            'title' => 'Sustainable Catalyst Workbench',
            'display' => 'full',
            'project' => 'default',
            'studio' => 'unified',
            'remember' => 'true',
            'diagnostics' => 'true',
        ), $atts, 'sc_workbench');

        $display = sanitize_key($atts['display']);
        if (!in_array($display, array('inline', 'compact', 'full', 'drawer'), true)) {
            $display = 'full';
        }
        $project = sanitize_key($atts['project']) ?: 'default';
        $studios = self::studios();
        if (!$studios) {
            return '<div class="scwb-primary scwb-primary--error"><strong>Workbench registry is unavailable.</strong><p>Confirm that the complete v4.0.2 plugin is active.</p></div>';
        }

        $availability = array();
        foreach ($studios as $key => $studio) {
            $availability[$key] = shortcode_exists($studio['shortcode']);
        }
        $available_keys = array_keys(array_filter($availability));
        if (!$available_keys) {
            return '<div class="scwb-primary scwb-primary--error"><strong>Workbench modules are unavailable.</strong><p>Install the complete v4.0.2 plugin rather than a partial add-on.</p></div>';
        }

        $initial = sanitize_key($atts['studio']);
        if (!isset($studios[$initial]) || empty($availability[$initial])) {
            $initial = $available_keys[0];
        }

        $instance = 'scwb-primary-' . wp_generate_uuid4();
        $available_count = count($available_keys);
        $total_count = count($studios);
        $remember = filter_var($atts['remember'], FILTER_VALIDATE_BOOLEAN);
        $show_diagnostics = filter_var($atts['diagnostics'], FILTER_VALIDATE_BOOLEAN);

        ob_start();
        ?>
        <section
            id="<?php echo esc_attr($instance); ?>"
            class="scwb-primary scwb-primary--<?php echo esc_attr($display); ?> is-loading"
            data-scwb-primary
            data-scwb-initial="<?php echo esc_attr($initial); ?>"
            data-scwb-project="<?php echo esc_attr($project); ?>"
            data-scwb-remember="<?php echo $remember ? 'true' : 'false'; ?>"
            data-scwb-version="4.1.0"
            aria-busy="true"
        >
            <noscript><div class="scwb-primary__module-error"><strong>JavaScript is required for Workbench studio navigation.</strong></div></noscript>
            <header class="scwb-primary__header">
                <div>
                    <p class="scwb-primary__eyebrow">Sustainable Catalyst Workbench v4.1.0</p>
                    <h2><?php echo esc_html($atts['title']); ?></h2>
                    <p>Open a persistent project workspace, the unified hub, or a specialist studio. Projects can autosave locally and optionally synchronize to private WordPress records.</p>
                </div>
                <span class="scwb-primary__status <?php echo $available_count === $total_count ? 'is-ok' : 'is-review'; ?>" data-scwb-primary-status>
                    <?php echo esc_html($available_count . '/' . $total_count . ' studios available'); ?>
                </span>
            </header>

            <div class="scwb-primary__activation" data-scwb-activation role="status" aria-live="polite"><span class="scwb-primary__spinner" aria-hidden="true"></span><span>Activating Workbench studios…</span></div>

            <div class="scwb-primary__layout">
                <nav class="scwb-primary__nav" aria-label="Workbench studios" role="tablist" aria-orientation="vertical">
                    <?php foreach ($studios as $key => $studio) :
                        $available = !empty($availability[$key]);
                        $active = $available && $key === $initial;
                        $tab_id = $instance . '-tab-' . $key;
                        $panel_id = $instance . '-panel-' . $key;
                    ?>
                        <button
                            id="<?php echo esc_attr($tab_id); ?>"
                            type="button"
                            class="scwb-primary__tab<?php echo $active ? ' is-active' : ''; ?><?php echo !$available ? ' is-unavailable' : ''; ?>"
                            role="tab"
                            aria-selected="<?php echo $active ? 'true' : 'false'; ?>"
                            aria-controls="<?php echo esc_attr($panel_id); ?>"
                            tabindex="<?php echo $active ? '0' : '-1'; ?>"
                            data-scwb-primary-tab="<?php echo esc_attr($key); ?>"
                            <?php disabled(!$available); ?>
                        >
                            <span class="scwb-primary__tab-title"><strong><?php echo esc_html($studio['label']); ?></strong><em><?php echo $available ? 'Ready' : 'Unavailable'; ?></em></span>
                            <span><?php echo esc_html($studio['description']); ?></span>
                        </button>
                    <?php endforeach; ?>
                </nav>

                <div class="scwb-primary__workspace" data-scwb-primary-workspace>
                    <?php foreach ($studios as $key => $studio) :
                        $available = !empty($availability[$key]);
                        $active = $available && $key === $initial;
                        $tab_id = $instance . '-tab-' . $key;
                        $panel_id = $instance . '-panel-' . $key;
                    ?>
                        <section
                            id="<?php echo esc_attr($panel_id); ?>"
                            class="scwb-primary__panel<?php echo $active ? ' is-active' : ''; ?>"
                            role="tabpanel"
                            aria-labelledby="<?php echo esc_attr($tab_id); ?>"
                            tabindex="0"
                            data-scwb-primary-panel="<?php echo esc_attr($key); ?>"
                            data-scwb-studio-shortcode="<?php echo esc_attr($studio['shortcode']); ?>"
                            <?php echo $active ? '' : 'hidden'; ?>
                        >
                            <?php echo self::render_studio($studio, $project, $key); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
                        </section>
                    <?php endforeach; ?>
                </div>
            </div>

            <?php if ($show_diagnostics) : ?>
                <details class="scwb-primary__diagnostics">
                    <summary>Interface diagnostics</summary>
                    <div class="scwb-primary__diagnostics-grid">
                        <div><strong>Primary shortcode</strong><span>Registered by v4.0.2</span></div>
                        <div><strong>Browser router</strong><span data-scwb-primary-js-status>Initializing</span></div>
                        <div><strong>Project</strong><span><?php echo esc_html($project); ?></span></div>
                        <div><strong>Available studios</strong><span><?php echo esc_html($available_count . ' of ' . $total_count); ?></span></div>
                    </div>
                </details>
            <?php endif; ?>
        </section>
        <?php
        return ob_get_clean();
    }
}

SCWB_Primary_Shortcode_Repair::boot();
