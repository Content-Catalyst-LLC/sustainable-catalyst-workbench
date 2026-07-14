<?php
/** Workbench v4.3.0 — Live Data Connectors and Reproducible Dataset Pipelines. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V430_Data_Pipelines {
    const VERSION = '4.3.0';
    const EXPECTED_STUDIOS = 25;

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_records'), 4);
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 49);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_records() {
        $common = array('public' => false, 'show_ui' => false, 'show_in_rest' => false, 'exclude_from_search' => true, 'supports' => array('title', 'author', 'custom-fields'));
        register_post_type('scwb_data_source', array_merge($common, array('label' => 'Workbench Data Sources')));
        register_post_type('scwb_dataset', array_merge($common, array('label' => 'Workbench Datasets')));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V430_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v430.css';
        $js = $base . '/assets/js/sc-workbench-v430.js';
        wp_register_style('scwb-v430', plugins_url('assets/css/sc-workbench-v430.css', SCWB_V430_PLUGIN_FILE), array('scwb-v420'), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v430', plugins_url('assets/js/sc-workbench-v430.js', SCWB_V430_PLUGIN_FILE), array('scwb-v420'), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_data_pipelines' => 'workspace',
            'sc_workbench_source_registry' => 'sources',
            'sc_workbench_connector_health' => 'health',
            'sc_workbench_dataset_manifest' => 'manifest',
            'sc_workbench_pipeline_builder' => 'pipeline',
            'sc_workbench_dataset_validation' => 'validation',
            'sc_workbench_freshness_cache' => 'freshness',
            'sc_workbench_refresh_planner' => 'refresh',
            'sc_workbench_offline_dataset_snapshot' => 'snapshot',
            'sc_workbench_data_provenance' => 'provenance',
            'sc_workbench_reproducible_dataset_package' => 'package',
        );
        foreach ($map as $tag => $panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, function($atts = array()) use ($panel) {
                    $atts = shortcode_atts(array('project' => 'default', 'dataset' => 'default', 'source' => 'default', 'display' => 'full', 'title' => 'Live Data Connectors and Dataset Pipelines'), $atts);
                    return SCWB_V430_Data_Pipelines::render($atts, $panel);
                });
            }
        }
    }

    private static function can_persist() { return is_user_logged_in() && current_user_can('edit_posts'); }
    public static function permission_persist() { return self::can_persist(); }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1', '/data-pipeline-status', array('methods' => 'GET', 'callback' => array(__CLASS__, 'status'), 'permission_callback' => '__return_true'));
        register_rest_route('scwb/v1', '/data-sources', array('methods' => array('GET', 'POST'), 'callback' => array(__CLASS__, 'sources'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
        register_rest_route('scwb/v1', '/datasets', array('methods' => array('GET', 'POST'), 'callback' => array(__CLASS__, 'datasets'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
        register_rest_route('scwb/v1', '/connector-health-records', array('methods' => 'POST', 'callback' => array(__CLASS__, 'connector_health'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
        register_rest_route('scwb/v1', '/dataset-pipeline-plans', array('methods' => 'POST', 'callback' => array(__CLASS__, 'pipeline_plan'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
        register_rest_route('scwb/v1', '/dataset-snapshots', array('methods' => 'POST', 'callback' => array(__CLASS__, 'snapshot_plan'), 'permission_callback' => array(__CLASS__, 'permission_persist')));
    }

    public static function status() {
        return array(
            'ok' => true,
            'version' => self::VERSION,
            'expectedStudioCount' => self::EXPECTED_STUDIOS,
            'authenticated' => is_user_logged_in(),
            'canPersistPrivateDataRecords' => self::can_persist(),
            'privateByDefault' => true,
            'browserFallback' => true,
            'offlineSnapshots' => true,
            'paidExternalDatabaseRequired' => false,
            'automaticNetworkFetchAuthorized' => false,
            'automaticCredentialStorageAuthorized' => false,
            'automaticCloudUploadAuthorized' => false,
            'automaticPublicationAuthorized' => false,
            'automaticDeletionAuthorized' => false,
        );
    }

    private static function list_records($type) {
        if (!function_exists('get_posts')) { return array(); }
        $posts = get_posts(array('post_type' => $type, 'post_status' => array('private', 'draft'), 'numberposts' => 100, 'orderby' => 'modified', 'order' => 'DESC'));
        $records = array();
        foreach ($posts as $post) { $records[] = array('id' => (int) $post->ID, 'title' => $post->post_title, 'status' => $post->post_status, 'modified' => $post->post_modified_gmt); }
        return $records;
    }

    private static function collection_response($type, $request) {
        $method = is_object($request) && method_exists($request, 'get_method') ? $request->get_method() : 'GET';
        if ('POST' !== strtoupper($method)) { return rest_ensure_response(array('ok' => true, 'records' => self::list_records($type))); }
        if (!function_exists('wp_insert_post')) { return rest_ensure_response(array('ok' => false, 'message' => 'Private WordPress persistence is unavailable.')); }
        $params = is_object($request) && method_exists($request, 'get_json_params') ? (array) $request->get_json_params() : array();
        $title = isset($params['title']) ? sanitize_text_field($params['title']) : 'Workbench data record';
        $post_id = wp_insert_post(array('post_type' => $type, 'post_status' => 'private', 'post_title' => $title, 'post_author' => get_current_user_id()), true);
        if (is_wp_error($post_id)) { return rest_ensure_response(array('ok' => false, 'message' => $post_id->get_error_message())); }
        if (function_exists('update_post_meta')) { update_post_meta($post_id, '_scwb_v430_record', wp_json_encode($params)); }
        return rest_ensure_response(array('ok' => true, 'id' => (int) $post_id, 'private' => true, 'automaticPublicationAuthorized' => false));
    }

    public static function sources($request = null) { return self::collection_response('scwb_data_source', $request); }
    public static function datasets($request = null) { return self::collection_response('scwb_dataset', $request); }
    public static function connector_health() { return rest_ensure_response(array('ok' => true, 'automaticNetworkFetchAuthorized' => false, 'requiresExplicitExecution' => true)); }
    public static function pipeline_plan() { return rest_ensure_response(array('ok' => true, 'automaticExecutionAuthorized' => false, 'automaticOverwriteAuthorized' => false)); }
    public static function snapshot_plan() { return rest_ensure_response(array('ok' => true, 'requiresExplicitImport' => true, 'automaticCloudUploadAuthorized' => false)); }

    private static function enqueue_assets() { self::register_assets(); wp_enqueue_style('scwb-v430'); wp_enqueue_script('scwb-v430'); }

    private static function field($label, $name, $value = '', $type = 'text', $wide = false) {
        echo '<label class="scwb-v430__field' . ($wide ? ' scwb-v430__field--wide' : '') . '"><span>' . esc_html($label) . '</span>';
        if ('textarea' === $type) { echo '<textarea data-scwb-v430-field="' . esc_attr($name) . '">' . esc_textarea($value) . '</textarea>'; }
        else { echo '<input type="' . esc_attr($type) . '" data-scwb-v430-field="' . esc_attr($name) . '" value="' . esc_attr($value) . '">'; }
        echo '</label>';
    }

    private static function actions($primary) {
        echo '<div class="scwb-v430__actions"><button type="button" class="scwb-v430__button scwb-v430__button--primary" data-scwb-v430-action="build">' . esc_html($primary) . '</button><button type="button" class="scwb-v430__button" data-scwb-v430-action="save-local">Save browser record</button><button type="button" class="scwb-v430__button" data-scwb-v430-action="export">Export JSON</button></div><div class="scwb-v430__result" aria-live="polite"><p data-scwb-v430-summary>Ready to prepare a reproducible data record.</p><pre data-scwb-v430-output>{}</pre></div>';
    }

    private static function render_panel($panel, $dataset, $source) {
        echo '<div class="scwb-v430__grid">';
        if ('workspace' === $panel) {
            echo '<article class="scwb-v430__card"><strong>Register sources</strong><span>Preserve connector type, host allowlists, licensing, citations, refresh cadence, and stable source hashes.</span></article>';
            echo '<article class="scwb-v430__card"><strong>Build reproducible pipelines</strong><span>Plan transformations, dependencies, schemas, validation, freshness, and outputs without silently changing data.</span></article>';
            echo '<article class="scwb-v430__card"><strong>Work offline</strong><span>Create content-addressed dataset snapshots and portable packages for local analysis and later synchronization.</span></article>';
            echo '<article class="scwb-v430__card"><strong>Keep humans in control</strong><span>Network retrieval, credentials, overwrites, publication, cloud upload, and deletion require explicit external action.</span></article>';
            self::field('Dataset title', 'title', 'Reproducible Workbench Dataset'); self::field('Dataset ID', 'datasetId', $dataset); self::field('Source IDs JSON', 'sourceIds', '["' . $source . '"]', 'textarea', true); self::field('Columns JSON', 'columns', '[{"name":"value","type":"number","unit":""}]', 'textarea', true); self::field('Pipeline steps JSON', 'steps', '[{"stepId":"select-fields","operation":"select","params":{"fields":["value"]},"dependsOn":[]}]', 'textarea', true); self::actions('Build data workspace');
        } elseif ('sources' === $panel) {
            self::field('Source title', 'title', 'Public data source'); self::field('Source ID', 'sourceId', $source); self::field('Connector type', 'connectorType', 'https-json'); self::field('HTTPS URL', 'url', 'https://example.org/data.json'); self::field('Allowed hosts JSON', 'allowedHosts', '["example.org"]', 'textarea', true); self::field('License', 'license', 'unknown'); self::field('Citation', 'citation', '', 'textarea', true); self::actions('Normalize source');
        } elseif ('health' === $panel) {
            self::field('Source ID', 'sourceId', $source); self::field('HTTP status', 'statusCode', '200', 'number'); self::field('Latency milliseconds', 'latencyMs', '250', 'number'); self::field('Records received', 'recordsReceived', '0', 'number'); self::field('Error', 'error', '', 'textarea', true); self::actions('Build health record');
        } elseif ('manifest' === $panel) {
            self::field('Dataset title', 'title', 'Workbench dataset'); self::field('Dataset ID', 'datasetId', $dataset); self::field('Source IDs JSON', 'sourceIds', '["' . $source . '"]', 'textarea', true); self::field('Columns JSON', 'columns', '[]', 'textarea', true); self::field('Row count', 'rowCount', '0', 'number'); self::field('License', 'license', 'unknown'); self::actions('Build manifest');
        } elseif ('pipeline' === $panel) {
            self::field('Pipeline ID', 'pipelineId', $dataset . '-pipeline'); self::field('Dataset ID', 'datasetId', $dataset); self::field('Language', 'language', 'declarative'); self::field('Steps JSON', 'steps', '[]', 'textarea', true); self::actions('Build pipeline plan');
        } elseif ('validation' === $panel) {
            self::field('Records JSON', 'records', '[]', 'textarea', true); self::field('Schema fields JSON', 'schemaFields', '[]', 'textarea', true); self::field('Primary key', 'primaryKey', ''); self::actions('Validate dataset');
        } elseif ('freshness' === $panel) {
            self::field('Source ID', 'sourceId', $source); self::field('Observed at', 'observedAt', gmdate('c')); self::field('Maximum age seconds', 'maxAgeSeconds', '86400', 'number'); self::field('Cache TTL seconds', 'ttlSeconds', '3600', 'number'); self::field('ETag', 'etag', ''); self::actions('Build freshness and cache plan');
        } elseif ('refresh' === $panel) {
            self::field('Source IDs JSON', 'sourceIds', '["' . $source . '"]', 'textarea', true); self::field('Dependencies JSON', 'dependencies', '{}', 'textarea', true); self::actions('Build refresh plan');
        } elseif ('snapshot' === $panel) {
            self::field('Dataset manifest JSON', 'manifest', '{}', 'textarea', true); self::field('Records JSON', 'records', '[]', 'textarea', true); self::actions('Build offline snapshot');
        } elseif ('provenance' === $panel) {
            self::field('Dataset ID', 'datasetId', $dataset); self::field('Source records JSON', 'sourceRecords', '[]', 'textarea', true); self::field('Transformation records JSON', 'transformationRecords', '[]', 'textarea', true); self::field('Validation records JSON', 'validationRecords', '[]', 'textarea', true); self::field('Output records JSON', 'outputRecords', '[]', 'textarea', true); self::actions('Build provenance');
        } else {
            self::field('Manifest JSON', 'manifest', '{}', 'textarea', true); self::field('Pipeline JSON', 'pipeline', '{}', 'textarea', true); self::field('Provenance JSON', 'provenance', '{}', 'textarea', true); self::field('Validation JSON', 'validation', '{}', 'textarea', true); self::field('Snapshots JSON', 'snapshots', '[]', 'textarea', true); self::actions('Build reproducible package');
        }
        echo '</div>';
    }

    public static function render($atts, $panel = 'workspace') {
        self::enqueue_assets();
        $project = sanitize_key($atts['project']); $dataset = sanitize_key($atts['dataset']); $source = sanitize_key($atts['source']);
        $display = in_array($atts['display'], array('full', 'compact'), true) ? $atts['display'] : 'full';
        $authenticated = self::can_persist(); $instance = 'scwb-v430-' . wp_generate_uuid4();
        ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v430 scwb-v430--<?php echo esc_attr($display); ?>" data-scwb-v430 data-scwb-v430-panel="<?php echo esc_attr($panel); ?>" data-scwb-project="<?php echo esc_attr($project); ?>" data-scwb-dataset="<?php echo esc_attr($dataset); ?>" data-scwb-source="<?php echo esc_attr($source); ?>" data-scwb-authenticated="<?php echo $authenticated ? 'true' : 'false'; ?>">
            <header class="scwb-v430__header"><div><p class="scwb-v430__eyebrow">Sustainable Catalyst Workbench · v4.3.0</p><h2><?php echo esc_html($atts['title']); ?></h2><p>Source registries, connector health, dataset manifests, reproducible transformations, validation, freshness, caching, offline snapshots, provenance, and portable data packages.</p></div><span class="scwb-v430__status <?php echo $authenticated ? 'is-online' : 'is-local'; ?>"><?php echo $authenticated ? 'Private WordPress storage available' : 'Browser-local planning'; ?></span></header>
            <?php self::render_panel($panel, $dataset, $source); ?>
            <?php if (!$authenticated) : ?><div class="scwb-v430__notice" role="status"><strong>Local-first mode.</strong><span>Sign in with an authorized WordPress account to preserve private source and dataset records on this site.</span></div><?php endif; ?>
            <p class="scwb-v430__boundary"><strong>Data boundary:</strong> connector records and pipeline plans do not automatically fetch network data, store credentials, overwrite datasets, upload to cloud services, publish records, delete source material, or certify data quality.</p>
        </section>
        <?php return ob_get_clean();
    }
}
SCWB_V430_Data_Pipelines::boot();
