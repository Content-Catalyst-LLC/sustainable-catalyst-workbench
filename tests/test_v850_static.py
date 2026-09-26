from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v850_identity_router_compose():
    assert 'APP_VERSION = "10.0.0"' in (ROOT/'backend/app/release.py').read_text()
    main=(ROOT/'backend/app/main.py').read_text(); assert 'version="10.0.0"' in main and 'from app.v850 import router as v850_router' in main
    compose=(ROOT/'compose.yml').read_text(); assert 'sustainable-catalyst-workbench:10.0.0' in compose and "d.get('version')=='10.0.0'" in compose and './data:/data' in compose

def test_v850_contract_routes_boundaries():
    src=(ROOT/'backend/app/v850.py').read_text()
    for literal in ('sc-workbench-research-timeline-run-history/1.0','/research-timeline/manifest','/research-timeline/{project_key}','/research-timeline/{project_key}/runs','/research-timeline/{project_key}/lineage','/research-timeline/compare','/integration/core/research-timeline/plan','/v850/status'):
        assert literal in src
    for boundary in ('timelineIsCompetingSourceOfTruth','filesystemMtimeUsedAsAuthoritativeChronology','automaticCausalInferenceAuthorized','automaticCoreDispatchAuthorized'):
        assert boundary in src

def test_v850_capabilities_docs():
    cap=(ROOT/'backend/app/v640.py').read_text()
    for flag in ('researchTimelineRunHistory','researchTimelineDerivedEvents','researchTimelineLineageGraph','researchTimelineComparison','researchTimelineCorePlanning'): assert flag in cap
    assert (ROOT/'RELEASE_NOTES_8.5.0_RESEARCH_TIMELINE_RUN_HISTORY.md').exists()
    assert (ROOT/'V850_RESEARCH_TIMELINE_RUN_HISTORY_MAP.md').exists()
    assert (ROOT/'workbench-v8.5.0.env.example').exists()

def test_v850_wordpress():
    main=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php').read_text()
    assert 'Version: 10.0.0' in main and "define('SCWB_VERSION', '10.0.0')" in main and 'SCWB_DIR' not in main
    assert 'includes/scwb-v850-research-timeline-run-history.php' in main
    inc=(ROOT/'wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v850-research-timeline-run-history.php').read_text()
    assert '/v850/status' in inc and 'sc_workbench_research_timeline_status' in inc and '/research-timeline/status' in inc
