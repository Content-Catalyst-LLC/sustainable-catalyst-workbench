<?php
/** Workbench v5.0.0 — Sustainable Catalyst Integrated Research and Engineering Platform. */
if (!defined('ABSPATH')) { exit; }

final class SCWB_V500_Integrated_Platform {
    const VERSION = '5.0.0';
    const EXPECTED_STUDIOS = 28;

    public static function boot() {
        add_action('init', array(__CLASS__, 'register_records'), 4);
        add_action('init', array(__CLASS__, 'register_assets'), 5);
        add_action('init', array(__CLASS__, 'register_shortcodes'), 50);
        add_action('rest_api_init', array(__CLASS__, 'register_rest_routes'));
    }

    public static function register_records() {
        $common = array('public'=>false,'show_ui'=>false,'show_in_rest'=>false,'exclude_from_search'=>true,'supports'=>array('title','author','custom-fields'));
        register_post_type('scwb_platform_prj', array_merge($common, array('label'=>'Workbench Integrated Platform Projects')));
        register_post_type('scwb_platform_rel', array_merge($common, array('label'=>'Workbench Integrated Platform Releases')));
    }

    public static function register_assets() {
        $base = dirname(SCWB_V500_PLUGIN_FILE);
        $css = $base . '/assets/css/sc-workbench-v500.css';
        $js = $base . '/assets/js/sc-workbench-v500.js';
        wp_register_style('scwb-v500', plugins_url('assets/css/sc-workbench-v500.css', SCWB_V500_PLUGIN_FILE), array('scwb-v450'), file_exists($css) ? (string) filemtime($css) : self::VERSION);
        wp_register_script('scwb-v500', plugins_url('assets/js/sc-workbench-v500.js', SCWB_V500_PLUGIN_FILE), array('scwb-v450'), file_exists($js) ? (string) filemtime($js) : self::VERSION, true);
    }

    public static function register_shortcodes() {
        $map = array(
            'sc_workbench_integrated_platform'=>'workspace',
            'sc_workbench_platform_project'=>'project',
            'sc_workbench_surface_registry'=>'registry',
            'sc_workbench_platform_portfolio'=>'portfolio',
            'sc_workbench_platform_workflow'=>'workflow',
            'sc_workbench_platform_integrity'=>'integrity',
            'sc_workbench_platform_governance'=>'governance',
            'sc_workbench_platform_deployment'=>'deployment',
            'sc_workbench_platform_dossier'=>'dossier',
            'sc_workbench_platform_package'=>'package',
        );
        foreach ($map as $tag=>$panel) {
            if (!shortcode_exists($tag)) {
                add_shortcode($tag, function($atts=array()) use ($panel) {
                    $atts=shortcode_atts(array('project'=>'default','display'=>'full','title'=>'Integrated Research and Engineering Platform'),$atts);
                    return SCWB_V500_Integrated_Platform::render($atts,$panel);
                });
            }
        }
    }

    private static function can_persist() { return is_user_logged_in() && current_user_can('edit_posts'); }
    public static function permission_persist() { return self::can_persist(); }

    public static function register_rest_routes() {
        register_rest_route('scwb/v1','/integrated-platform-status',array('methods'=>'GET','callback'=>array(__CLASS__,'status'),'permission_callback'=>'__return_true'));
        register_rest_route('scwb/v1','/integrated-platform-projects',array('methods'=>array('GET','POST'),'callback'=>array(__CLASS__,'projects'),'permission_callback'=>array(__CLASS__,'permission_persist')));
        register_rest_route('scwb/v1','/integrated-platform-releases',array('methods'=>array('GET','POST'),'callback'=>array(__CLASS__,'releases'),'permission_callback'=>array(__CLASS__,'permission_persist')));
        register_rest_route('scwb/v1','/integrated-platform-governance',array('methods'=>'POST','callback'=>array(__CLASS__,'governance_plan'),'permission_callback'=>array(__CLASS__,'permission_persist')));
        register_rest_route('scwb/v1','/integrated-platform-deployment',array('methods'=>'POST','callback'=>array(__CLASS__,'deployment_plan'),'permission_callback'=>array(__CLASS__,'permission_persist')));
        register_rest_route('scwb/v1','/integrated-platform-packages',array('methods'=>'POST','callback'=>array(__CLASS__,'package_plan'),'permission_callback'=>array(__CLASS__,'permission_persist')));
    }

    public static function status() {
        return array(
            'ok'=>true,'version'=>self::VERSION,'expectedStudioCount'=>self::EXPECTED_STUDIOS,
            'integratedSurfaces'=>array('workbench','lab','site-intelligence','decision-studio','research-librarian','knowledge-library','wordpress','offline'),
            'browserLocalOperation'=>true,'privateWordPressStorage'=>true,'offlineOperation'=>true,'paidExternalServiceRequired'=>false,
            'automaticWorkflowExecutionAuthorized'=>false,'automaticPublicationAuthorized'=>false,'automaticCertificationAuthorized'=>false,
            'automaticDeviceExecutionAuthorized'=>false,'automaticDestructiveSynchronizationAuthorized'=>false,'automaticHighStakesDecisionAuthorized'=>false,
            'remoteShellAuthorized'=>false,'arbitraryCommandExecutionAuthorized'=>false,
        );
    }

    private static function list_records($type) {
        if (!function_exists('get_posts')) { return array(); }
        $posts=get_posts(array('post_type'=>$type,'post_status'=>array('private','draft'),'numberposts'=>100,'orderby'=>'modified','order'=>'DESC'));
        $records=array(); foreach($posts as $post){$records[]=array('id'=>(int)$post->ID,'title'=>$post->post_title,'status'=>$post->post_status,'modified'=>$post->post_modified_gmt);} return $records;
    }

    private static function collection_response($type,$request) {
        $method=is_object($request)&&method_exists($request,'get_method')?$request->get_method():'GET';
        if('POST'!==strtoupper($method)){return rest_ensure_response(array('ok'=>true,'records'=>self::list_records($type)));}
        if(!function_exists('wp_insert_post')){return rest_ensure_response(array('ok'=>false,'message'=>'Private WordPress persistence is unavailable.'));}
        $params=is_object($request)&&method_exists($request,'get_json_params')?(array)$request->get_json_params():array();
        $title=isset($params['title'])?sanitize_text_field($params['title']):'Integrated Workbench record';
        $post_id=wp_insert_post(array('post_type'=>$type,'post_status'=>'private','post_title'=>$title,'post_author'=>get_current_user_id()),true);
        if(is_wp_error($post_id)){return rest_ensure_response(array('ok'=>false,'message'=>$post_id->get_error_message()));}
        if(function_exists('update_post_meta')){update_post_meta($post_id,'_scwb_v500_record',wp_json_encode($params));}
        return rest_ensure_response(array('ok'=>true,'id'=>(int)$post_id,'private'=>true,'automaticPublicationAuthorized'=>false,'automaticExecutionAuthorized'=>false));
    }

    public static function projects($request=null){return self::collection_response('scwb_platform_prj',$request);}
    public static function releases($request=null){return self::collection_response('scwb_platform_rel',$request);}
    public static function governance_plan(){return rest_ensure_response(array('ok'=>true,'humanApprovalRequired'=>true,'automaticPublicationAuthorized'=>false,'automaticCertificationAuthorized'=>false));}
    public static function deployment_plan(){return rest_ensure_response(array('ok'=>true,'verifiedBackupRequired'=>true,'verifiedRollbackRequired'=>true,'automaticDeploymentAuthorized'=>false,'remoteShellAuthorized'=>false));}
    public static function package_plan(){return rest_ensure_response(array('ok'=>true,'privateByDefault'=>true,'explicitImportRequired'=>true,'automaticInstallationAuthorized'=>false));}

    private static function enqueue_assets(){self::register_assets();wp_enqueue_style('scwb-v500');wp_enqueue_script('scwb-v500');}
    private static function field($label,$name,$value='',$type='text',$wide=false){echo '<label class="scwb-v500__field'.($wide?' scwb-v500__field--wide':'').'"><span>'.esc_html($label).'</span>';if('textarea'===$type){echo '<textarea data-scwb-v500-field="'.esc_attr($name).'">'.esc_textarea($value).'</textarea>';}else{echo '<input type="'.esc_attr($type).'" data-scwb-v500-field="'.esc_attr($name).'" value="'.esc_attr($value).'">';}echo '</label>';}
    private static function actions($label){echo '<div class="scwb-v500__actions"><button type="button" class="scwb-v500__button scwb-v500__button--primary" data-scwb-v500-action="build">'.esc_html($label).'</button><button type="button" class="scwb-v500__button" data-scwb-v500-action="save-local">Save browser record</button><button type="button" class="scwb-v500__button" data-scwb-v500-action="export">Export JSON</button></div><div class="scwb-v500__result" aria-live="polite"><p data-scwb-v500-summary>Ready to prepare an integrated platform record.</p><pre data-scwb-v500-output>{}</pre></div>';}

    private static function render_panel($panel,$project){
        echo '<div class="scwb-v500__overview"><article><strong>One canonical project</strong><span>Connect requirements, evidence, data, calculations, experiments, workflows, reviews, evaluations, and release records.</span></article><article><strong>All platform surfaces</strong><span>Coordinate Workbench, Lab, Site Intelligence, Decision Studio, Research Librarian, Knowledge Library, WordPress, and offline nodes.</span></article><article><strong>Human-controlled release</strong><span>Require integrity, traceability, security, evaluation, professional review where applicable, backups, rollback, and named approval.</span></article></div>';
        echo '<div class="scwb-v500__form">';
        if('registry'===$panel){self::field('Surface records (JSON)','surfaces','[{"id":"workbench","state":"ready","version":"5.0.0"},{"id":"lab","state":"ready"},{"id":"site-intelligence","state":"degraded"},{"id":"decision-studio","state":"ready"},{"id":"research-librarian","state":"ready"},{"id":"knowledge-library","state":"ready"},{"id":"wordpress","state":"ready"},{"id":"offline","state":"ready"}]','textarea',true);self::actions('Build surface registry');}
        elseif('portfolio'===$panel){self::field('Projects (JSON)','projects','[]','textarea',true);self::actions('Build project portfolio');}
        elseif('workflow'===$panel){self::field('Workflow title','title','Integrated research workflow');self::field('Stages (JSON)','stages','[{"id":"frame","surface":"research-librarian","dependsOn":[]},{"id":"source","surface":"knowledge-library","dependsOn":["frame"]},{"id":"analyze","surface":"workbench","dependsOn":["source"]},{"id":"validate","surface":"lab","dependsOn":["analyze"],"approvalRequired":true}]','textarea',true);self::actions('Build integrated workflow');}
        elseif('integrity'===$panel){self::field('Integrated project (JSON)','project','{"schema":"sc-workbench-integrated-project/1.0","projectId":"'.$project.'"}','textarea',true);self::actions('Audit project integrity');}
        elseif('governance'===$panel){self::field('Project and evaluation record (JSON)','project','{"projectId":"'.$project.'","highStakes":false}','textarea',true);self::field('Named approver','approver','');self::actions('Evaluate governance gate');}
        elseif('deployment'===$panel){self::field('Deployment targets (JSON)','targets','["wordpress","offline"]','textarea',true);self::field('Project (JSON)','project','{"projectId":"'.$project.'"}','textarea',true);self::actions('Build deployment plan');}
        elseif('dossier'===$panel){self::field('Project (JSON)','project','{"projectId":"'.$project.'"}','textarea',true);self::field('Components (JSON)','components','{"registry":{},"workflows":[],"integrity":{},"governance":{},"deployment":{},"artifacts":[]}','textarea',true);self::actions('Build platform dossier');}
        elseif('package'===$panel){self::field('Project (JSON)','project','{"projectId":"'.$project.'"}','textarea',true);self::field('Dossier (JSON)','dossier','{}','textarea',true);self::field('Files (JSON)','files','{"README.md":"Integrated Workbench package"}','textarea',true);self::actions('Build portable platform package');}
        else{self::field('Project title','title','Integrated Sustainable Catalyst project');self::field('Domains (JSON)','domains','["sustainability","engineering","research"]','textarea',true);self::field('Surfaces (JSON)','surfaces','[{"id":"workbench"},{"id":"lab"},{"id":"site-intelligence"},{"id":"decision-studio"},{"id":"research-librarian"},{"id":"knowledge-library"},{"id":"wordpress"},{"id":"offline"}]','textarea',true);self::field('Requirements (JSON)','requirements','[{"id":"REQ-1","text":"Produce an auditable integrated result"}]','textarea',true);self::actions('Build integrated project');}
        echo '</div>';
    }

    public static function render($atts=array(),$panel='workspace'){
        self::enqueue_assets();$project=sanitize_key($atts['project'])?:'default';$instance='scwb-v500-'.wp_generate_uuid4();ob_start(); ?>
        <section id="<?php echo esc_attr($instance); ?>" class="scwb-v500" data-scwb-v500 data-panel="<?php echo esc_attr($panel); ?>" data-project="<?php echo esc_attr($project); ?>" data-version="5.0.0">
            <header class="scwb-v500__header"><div><p class="scwb-v500__eyebrow">Sustainable Catalyst Workbench v5.0.0</p><h3><?php echo esc_html($atts['title']); ?></h3><p>One connected, local-first and privately persistable environment for auditable research, scientific analysis, engineering development, evidence, review, and controlled release.</p></div><span class="scwb-v500__status">Integrated platform</span></header>
            <?php self::render_panel($panel,$project); ?>
            <footer class="scwb-v500__boundary"><strong>Human-control boundary</strong><span>No automatic workflow execution, publication, certification, device execution, destructive synchronization, high-stakes decision, remote shell, or arbitrary command execution is authorized.</span></footer>
        </section><?php return ob_get_clean();
    }
}
SCWB_V500_Integrated_Platform::boot();
