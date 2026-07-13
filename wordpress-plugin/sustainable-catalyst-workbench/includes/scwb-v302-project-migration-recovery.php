<?php
/**
 * Workbench v3.0.2 — Project Migration, Storage, and Recovery.
 */
if (!defined('ABSPATH')) {
    exit;
}

final class SCWB_V302_Project_Migration_Recovery {
    const VERSION = '3.0.2';

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 40);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V302_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v302.css';
        $js = $base . '/assets/js/sc-workbench-v302.js';
        wp_register_style('scwb-v302', plugins_url('assets/css/sc-workbench-v302.css', SCWB_V302_PLUGIN_FILE), array(), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v302', plugins_url('assets/js/sc-workbench-v302.js', SCWB_V302_PLUGIN_FILE), array(), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_migration_recovery' => 'overview',
            'sc_workbench_migration_center' => 'migration',
            'sc_workbench_storage_health_v302' => 'health',
            'sc_workbench_backup_restore' => 'backup',
            'sc_workbench_restore_center' => 'restore',
            'sc_workbench_orphan_cleanup' => 'cleanup',
            'sc_workbench_rollback_center' => 'rollback',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, static function($atts = array()) use ($panel) {
                    return SCWB_V302_Project_Migration_Recovery::render($panel, $atts);
                });
            }
        }
    }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/recovery-status', array(
            'methods' => 'GET',
            'permission_callback' => '__return_true',
            'callback' => static function() {
                return rest_ensure_response(array(
                    'ok' => true,
                    'version' => self::VERSION,
                    'schema' => 'sc-workbench-recovery-status/2.0',
                    'shortcodes' => array(
                        'sc_workbench_migration_recovery',
                        'sc_workbench_migration_center',
                        'sc_workbench_storage_health_v302',
                        'sc_workbench_backup_restore',
                        'sc_workbench_restore_center',
                        'sc_workbench_orphan_cleanup',
                        'sc_workbench_rollback_center',
                    ),
                    'storage' => 'browser-local',
                    'destructiveActionsRequireBackup' => true,
                ));
            },
        ));
    }

    private static function enqueue_assets() {
        self::register_assets();
        wp_enqueue_style('scwb-v302');
        wp_enqueue_script('scwb-v302');
    }

    public static function render($panel, $atts = array()) {
        self::enqueue_assets();
        $atts = shortcode_atts(array(
            'project' => 'default',
            'title' => 'Project Migration, Storage, and Recovery',
            'display' => 'full',
        ), $atts, 'sc_workbench_migration_recovery');
        $project = sanitize_key($atts['project']) ?: 'default';
        $display = sanitize_key($atts['display']);
        if (!in_array($display, array('inline', 'compact', 'full', 'drawer'), true)) {
            $display = 'full';
        }
        $instance = 'scwb-v302-' . wp_generate_uuid4();
        ob_start();
        ?>
        <section
            id="<?php echo esc_attr($instance); ?>"
            class="scwb-v302 scwb-v302--<?php echo esc_attr($display); ?>"
            data-scwb-v302
            data-scwb-v302-project="<?php echo esc_attr($project); ?>"
            data-scwb-v302-panel="<?php echo esc_attr($panel); ?>"
            data-scwb-v302-version="3.0.2"
        >
            <header class="scwb-v302__header">
                <div>
                    <p class="scwb-v302__eyebrow">Sustainable Catalyst Workbench · v3.0.2</p>
                    <h2><?php echo esc_html($atts['title']); ?></h2>
                    <p>Detect legacy browser projects, preview non-destructive migrations, inspect storage health, create signed backups, validate restores, plan rollback, and clean orphaned records with explicit safeguards.</p>
                </div>
                <span class="scwb-v302__status" data-scwb-v302-status>Recovery safeguards active</span>
            </header>

            <nav class="scwb-v302__nav" aria-label="Migration and recovery tools">
                <?php
                $tabs = array(
                    'overview' => 'Overview',
                    'migration' => 'Migration',
                    'health' => 'Storage health',
                    'backup' => 'Backup',
                    'restore' => 'Restore',
                    'cleanup' => 'Cleanup',
                    'rollback' => 'Rollback',
                );
                foreach ($tabs as $key => $label) :
                ?>
                    <button type="button" class="scwb-v302__tab<?php echo $key === $panel ? ' is-active' : ''; ?>" data-scwb-v302-tab="<?php echo esc_attr($key); ?>"><?php echo esc_html($label); ?></button>
                <?php endforeach; ?>
            </nav>

            <div class="scwb-v302__body">
                <section class="scwb-v302__panel<?php echo 'overview' === $panel ? ' is-active' : ''; ?>" data-scwb-v302-view="overview">
                    <div class="scwb-v302__cards">
                        <article><strong>Discover</strong><span>Inventory Workbench v1.x, v2.x, v3.x, unknown, and canonical browser-storage records.</span></article>
                        <article><strong>Preview</strong><span>Build a migration map and canonical v3 project manifest without modifying browser storage.</span></article>
                        <article><strong>Protect</strong><span>Create content-hashed backups and rollback points before every destructive operation.</span></article>
                        <article><strong>Recover</strong><span>Validate imported packages, resolve conflicts, restore safely, and audit the final workspace.</span></article>
                    </div>
                    <div class="scwb-v302__actions">
                        <button type="button" class="scwb-v302__button scwb-v302__button--primary" data-scwb-v302-action="scan">Scan browser storage</button>
                        <button type="button" class="scwb-v302__button" data-scwb-v302-action="backup">Create complete backup</button>
                        <button type="button" class="scwb-v302__button" data-scwb-v302-action="health">Audit workspace</button>
                    </div>
                </section>

                <section class="scwb-v302__panel<?php echo 'migration' === $panel ? ' is-active' : ''; ?>" data-scwb-v302-view="migration">
                    <?php self::field('Source version', 'source_version', 'text', 'auto-detect'); ?>
                    <?php self::field('Target project ID', 'target_project', 'text', $project); ?>
                    <label class="scwb-v302__check"><input type="checkbox" data-scwb-v302-field="preserve_unknown" checked> Preserve unknown Workbench-like keys in a legacy studio</label>
                    <div class="scwb-v302__actions">
                        <button type="button" class="scwb-v302__button" data-scwb-v302-action="scan">Discover legacy records</button>
                        <button type="button" class="scwb-v302__button scwb-v302__button--primary" data-scwb-v302-action="migration-preview">Preview migration</button>
                        <button type="button" class="scwb-v302__button" data-scwb-v302-action="migration-apply">Apply migration</button>
                    </div>
                </section>

                <section class="scwb-v302__panel<?php echo 'health' === $panel ? ' is-active' : ''; ?>" data-scwb-v302-view="health">
                    <?php self::field('Estimated browser quota in bytes', 'quota_bytes', 'number', '5242880'); ?>
                    <div class="scwb-v302__actions">
                        <button type="button" class="scwb-v302__button scwb-v302__button--primary" data-scwb-v302-action="health">Audit browser storage</button>
                        <button type="button" class="scwb-v302__button" data-scwb-v302-action="export-report">Export audit</button>
                    </div>
                </section>

                <section class="scwb-v302__panel<?php echo 'backup' === $panel ? ' is-active' : ''; ?>" data-scwb-v302-view="backup">
                    <?php self::field('Backup label', 'backup_label', 'text', 'Workbench recovery backup'); ?>
                    <?php self::field('Previous backup hash', 'previous_backup_hash', 'text', ''); ?>
                    <div class="scwb-v302__actions">
                        <button type="button" class="scwb-v302__button scwb-v302__button--primary" data-scwb-v302-action="backup">Create and download backup</button>
                        <button type="button" class="scwb-v302__button" data-scwb-v302-action="copy-backup-hash">Copy latest backup hash</button>
                    </div>
                </section>

                <section class="scwb-v302__panel<?php echo 'restore' === $panel ? ' is-active' : ''; ?>" data-scwb-v302-view="restore">
                    <label class="scwb-v302__field scwb-v302__field--wide"><span>Backup file</span><input type="file" accept="application/json,.json" data-scwb-v302-file></label>
                    <?php self::field('Conflict strategy: skip, overwrite, or rename', 'restore_strategy', 'text', 'skip'); ?>
                    <label class="scwb-v302__check"><input type="checkbox" data-scwb-v302-field="backup_before_restore" checked> Create rollback backup before restore</label>
                    <div class="scwb-v302__actions">
                        <button type="button" class="scwb-v302__button" data-scwb-v302-action="restore-validate">Validate restore</button>
                        <button type="button" class="scwb-v302__button scwb-v302__button--primary" data-scwb-v302-action="restore-apply">Apply restore</button>
                    </div>
                </section>

                <section class="scwb-v302__panel<?php echo 'cleanup' === $panel ? ' is-active' : ''; ?>" data-scwb-v302-view="cleanup">
                    <?php self::field('Cleanup scope: selected, duplicates, orphans, stale, or all-candidates', 'cleanup_scope', 'text', 'orphans'); ?>
                    <?php self::field('Selected keys, one per line', 'cleanup_keys', 'textarea', ''); ?>
                    <label class="scwb-v302__check"><input type="checkbox" data-scwb-v302-field="cleanup_backup"> I downloaded a current backup</label>
                    <?php self::field('Type CLEAN WORKSPACE', 'cleanup_confirmation', 'text', ''); ?>
                    <div class="scwb-v302__actions">
                        <button type="button" class="scwb-v302__button" data-scwb-v302-action="cleanup-plan">Create cleanup plan</button>
                        <button type="button" class="scwb-v302__button scwb-v302__button--danger" data-scwb-v302-action="cleanup-apply">Execute approved cleanup</button>
                    </div>
                </section>

                <section class="scwb-v302__panel<?php echo 'rollback' === $panel ? ' is-active' : ''; ?>" data-scwb-v302-view="rollback">
                    <?php self::field('Rollback backup JSON', 'rollback_backup', 'textarea', ''); ?>
                    <label class="scwb-v302__check"><input type="checkbox" data-scwb-v302-field="rollback_backup_confirmed"> I downloaded a backup of the current state</label>
                    <?php self::field('Type ROLLBACK WORKBENCH', 'rollback_confirmation', 'text', ''); ?>
                    <div class="scwb-v302__actions">
                        <button type="button" class="scwb-v302__button" data-scwb-v302-action="rollback-plan">Create rollback plan</button>
                        <button type="button" class="scwb-v302__button scwb-v302__button--danger" data-scwb-v302-action="rollback-apply">Execute approved rollback</button>
                    </div>
                </section>

                <div class="scwb-v302__workspace">
                    <div class="scwb-v302__summary" data-scwb-v302-summary aria-live="polite">No storage operation has run.</div>
                    <pre class="scwb-v302__result" data-scwb-v302-result>{}</pre>
                </div>
            </div>

            <p class="scwb-v302__boundary"><strong>Recovery boundary:</strong> all migrations, restores, rollbacks, cleanup, and reset operations occur in the current browser profile. Download and verify a backup before changing storage. Imported records remain subject to studio-level validation, source review, and professional boundaries.</p>
        </section>
        <?php
        return ob_get_clean();
    }

    private static function field($label, $name, $type = 'text', $value = '') {
        $wide = 'textarea' === $type;
        ?>
        <label class="scwb-v302__field<?php echo $wide ? ' scwb-v302__field--wide' : ''; ?>">
            <span><?php echo esc_html($label); ?></span>
            <?php if ('textarea' === $type) : ?>
                <textarea data-scwb-v302-field="<?php echo esc_attr($name); ?>"><?php echo esc_textarea($value); ?></textarea>
            <?php else : ?>
                <input type="<?php echo esc_attr($type); ?>" value="<?php echo esc_attr($value); ?>" data-scwb-v302-field="<?php echo esc_attr($name); ?>">
            <?php endif; ?>
        </label>
        <?php
    }
}

SCWB_V302_Project_Migration_Recovery::boot();
