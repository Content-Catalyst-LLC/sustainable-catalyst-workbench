<?php
/** Workbench v4.0.2 — Project Graph, Synchronization, and Recovery Hardening. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V402_Graph_Sync_Recovery {
    const VERSION = '4.0.2';
    const EXPECTED_STUDIOS = 22;

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_records'), 4);
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 46);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_records() {
        $common = array('public' => false, 'show_ui' => false, 'show_in_rest' => false, 'exclude_from_search' => true, 'supports' => array('title', 'author', 'custom-fields'));
        register_post_type('scwb_sync_txn', array_merge($common, array('label' => 'Workbench Sync Transactions')));
        register_post_type('scwb_checkpoint', array_merge($common, array('label' => 'Workbench Recovery Checkpoints')));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V402_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v402.css';
        $js = $base . '/assets/js/sc-workbench-v402.js';
        wp_register_style('scwb-v402', plugins_url('assets/css/sc-workbench-v402.css', SCWB_V402_PLUGIN_FILE), array('scwb-v401'), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v402', plugins_url('assets/js/sc-workbench-v402.js', SCWB_V402_PLUGIN_FILE), array('scwb-v401'), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_graph_sync_recovery' => 'overview',
            'sc_workbench_project_graph_integrity' => 'graph',
            'sc_workbench_sync_reconciliation' => 'reconcile',
            'sc_workbench_sync_journal' => 'journal',
            'sc_workbench_recovery_checkpoint' => 'checkpoint',
            'sc_workbench_interrupted_sync_recovery' => 'recovery',
            'sc_workbench_sync_receipt_verification' => 'receipt',
            'sc_workbench_graph_sync_stress' => 'stress',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, function($atts) use ($panel) {
                    $atts = shortcode_atts(array('project' => 'default', 'display' => 'full', 'title' => 'Project Graph, Synchronization, and Recovery'), $atts);
                    return SCWB_V402_Graph_Sync_Recovery::render($atts, $panel);
                });
            }
        }
    }

    private static function can_manage() { return is_user_logged_in() && current_user_can('edit_posts'); }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/graph-sync-recovery-status', array('methods' => 'GET', 'callback' => array(__CLASS__, 'status'), 'permission_callback' => '__return_true'));
        register_rest_route('scwb/v1', '/project-graph-integrity', array('methods' => 'GET', 'callback' => array(__CLASS__, 'graph_status'), 'permission_callback' => '__return_true'));
        register_rest_route('scwb/v1', '/sync-transactions', array('methods' => 'GET', 'callback' => array(__CLASS__, 'sync_transactions'), 'permission_callback' => array(__CLASS__, 'can_manage')));
        register_rest_route('scwb/v1', '/recovery-checkpoints', array('methods' => 'GET', 'callback' => array(__CLASS__, 'checkpoint_status'), 'permission_callback' => array(__CLASS__, 'can_manage')));
        register_rest_route('scwb/v1', '/interrupted-sync-recovery', array('methods' => 'GET', 'callback' => array(__CLASS__, 'recovery_status'), 'permission_callback' => array(__CLASS__, 'can_manage')));
    }

    public static function status() {
        return rest_ensure_response(array(
            'ok' => true,
            'schema' => 'sc-workbench-project-graph-sync-recovery-status/1.0',
            'version' => self::VERSION,
            'milestone' => 'Project Graph, Synchronization, and Recovery Hardening',
            'expectedStudioCount' => self::EXPECTED_STUDIOS,
            'threeWayReconciliation' => true,
            'idempotentSyncJournals' => true,
            'contentAddressedCheckpoints' => true,
            'automaticExecutionAuthorized' => false,
            'automaticRollbackAuthorized' => false,
            'automaticDeletionAuthorized' => false,
        ));
    }

    public static function graph_status() { return rest_ensure_response(array('ok' => true, 'version' => self::VERSION, 'checks' => array('duplicate-nodes', 'duplicate-edges', 'dangling-edges', 'cycles', 'components', 'hashes'), 'automaticMutationAuthorized' => false)); }
    public static function sync_transactions() { return rest_ensure_response(array('ok' => true, 'version' => self::VERSION, 'private' => true, 'states' => array('prepared', 'applying', 'verifying', 'committed', 'rolled-back', 'aborted'))); }
    public static function checkpoint_status() { return rest_ensure_response(array('ok' => true, 'version' => self::VERSION, 'private' => true, 'contentAddressed' => true, 'automaticRestoreAuthorized' => false)); }
    public static function recovery_status() { return rest_ensure_response(array('ok' => true, 'version' => self::VERSION, 'backupRequired' => true, 'confirmation' => 'ROLLBACK CONNECTED PROJECT', 'automaticRollbackAuthorized' => false)); }

    private static function card($title, $text, $action, $button) {
        ?>
        <article class="scwb-v402__card">
            <h4><?php echo esc_html($title); ?></h4>
            <p><?php echo esc_html($text); ?></p>
            <button type="button" data-scwb-v402-action="<?php echo esc_attr($action); ?>"><?php echo esc_html($button); ?></button>
        </article>
        <?php
    }

    public static function render($atts, $panel = 'overview') {
        self::register_assets();
        wp_enqueue_style('scwb-v401');
        wp_enqueue_style('scwb-v402');
        wp_enqueue_script('scwb-v401');
        wp_enqueue_script('scwb-v402');
        wp_localize_script('scwb-v402', 'SCWBV402Config', array(
            'version' => self::VERSION,
            'restUrl' => esc_url_raw(rest_url('scwb/v1')),
            'nonce' => wp_create_nonce('wp_rest'),
            'expectedStudios' => self::EXPECTED_STUDIOS,
        ));
        $project = sanitize_key($atts['project']) ?: 'default';
        $display = sanitize_key($atts['display']) ?: 'full';
        ob_start();
        ?>
        <section class="scwb-v402 scwb-v402--<?php echo esc_attr($display); ?>" data-scwb-v402 data-panel="<?php echo esc_attr($panel); ?>" data-project="<?php echo esc_attr($project); ?>" data-version="4.0.2">
            <header class="scwb-v402__header">
                <div><p class="scwb-v402__eyebrow">Workbench v4.0.2 hardening patch</p><h3><?php echo esc_html($atts['title']); ?></h3><p>Audit connected graphs, preview three-way reconciliation, verify transaction receipts, and recover interrupted synchronization without automatic mutation.</p></div>
                <span class="scwb-v402__status">Human-controlled recovery</span>
            </header>
            <div class="scwb-v402__summary">
                <div><strong>Project</strong><span><?php echo esc_html($project); ?></span></div>
                <div><strong>Graph policy</strong><span>Content-hashed</span></div>
                <div><strong>Sync policy</strong><span>Idempotent journal</span></div>
                <div><strong>Rollback</strong><span>Verified backup required</span></div>
            </div>
            <div class="scwb-v402__grid">
                <?php self::card('Graph integrity', 'Detect duplicate identifiers, dangling edges, cycles, disconnected components, self-loops, and hash mismatches.', 'graph', 'Audit project graph'); ?>
                <?php self::card('Three-way reconciliation', 'Compare local, remote, and common-base records before choosing a conflict strategy.', 'reconcile', 'Preview reconciliation'); ?>
                <?php self::card('Transaction journal', 'Create ordered, content-hashed operations with stable idempotency keys and resumable phases.', 'journal', 'Build sync journal'); ?>
                <?php self::card('Recovery checkpoint', 'Build a content-addressed checkpoint with record hashes, graph hash, and a Merkle-style root.', 'checkpoint', 'Create checkpoint plan'); ?>
                <?php self::card('Interrupted-sync recovery', 'Determine whether to resume, re-verify, inspect, or plan an explicitly authorized rollback.', 'recovery', 'Build recovery plan'); ?>
                <?php self::card('Receipt verification', 'Verify transaction, journal, checkpoint, operation count, and target status before commit acceptance.', 'receipt', 'Verify receipt contract'); ?>
                <?php self::card('Stress evaluation', 'Evaluate graph size, synchronization duration, memory, density, and conflict-ratio budgets.', 'stress', 'Evaluate stress budget'); ?>
            </div>
            <pre class="scwb-v402__output" data-scwb-v402-output aria-live="polite">Select a hardening check. No project records will be changed.</pre>
        </section>
        <?php
        return ob_get_clean();
    }
}

SCWB_V402_Graph_Sync_Recovery::boot();
