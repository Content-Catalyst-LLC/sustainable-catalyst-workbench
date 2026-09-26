from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def test_v810_identity_router_compose():
    assert 'APP_VERSION = "9.7.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text()
    assert 'version="9.7.0"' in main
    assert 'from app.v810 import router as v810_router' in main and 'app.include_router(v810_router)' in main
    compose=(ROOT/'compose.yml').read_text()
    assert 'sustainable-catalyst-workbench:9.7.0' in compose and "d.get('version')=='9.7.0'" in compose
    assert './data:/data' in compose and 'SCWB_RESEARCH_ENVIRONMENT_STORE' in compose


def test_v810_persistence_contract_and_boundaries():
    src=(ROOT/'backend/app/v810.py').read_text()
    for literal in ('/research-environment/persistence/save','/research-environment/persistence/{environment_key}','/research-environment/checkpoints/create','/research-environment/recovery/plan','/research-environment/recovery/apply','/v810/status','sc-workbench-research-environment-persistence-recovery/1.0'):
        assert literal in src
    for forbidden in ('subprocess.run(', 'os.system(', 'eval(', 'exec('):
        assert forbidden not in src
    for boundary in ('destructiveHistoryRewriteAuthorized','recoveryCreatesNewRevision','automaticScientificExecutionAuthorized','automaticNotebookReplayAuthorized','automaticWorkflowExecutionAuthorized'):
        assert boundary in src


def test_v810_capabilities_docs_env():
    cap=(ROOT/'backend/app/v640.py').read_text()
    for flag in ('researchEnvironmentPersistenceRecovery','researchEnvironmentRevisionHistory','researchEnvironmentCheckpoints','researchEnvironmentRecovery'):
        assert flag in cap
    assert (ROOT/'RELEASE_NOTES_8.1.0_RESEARCH_ENVIRONMENT_PERSISTENCE_RECOVERY.md').exists()
    assert (ROOT/'V810_RESEARCH_ENVIRONMENT_PERSISTENCE_RECOVERY_MAP.md').exists()
    assert (ROOT/'workbench-v8.1.0.env.example').exists()


def test_v810_wordpress():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 9.7.0' in main and "define('SCWB_VERSION', '9.7.0')" in main and 'SCWB_DIR' not in main
    assert 'includes/scwb-v810-research-environment-persistence-recovery.php' in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v810-research-environment-persistence-recovery.php').read_text()
    assert '/v810/status' in inc and 'sc_workbench_research_persistence_status' in inc and '/research-persistence/status' in inc
