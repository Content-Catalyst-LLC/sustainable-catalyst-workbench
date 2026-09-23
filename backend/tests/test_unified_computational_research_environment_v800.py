from copy import deepcopy
from fastapi.testclient import TestClient
from app.main import app

c=TestClient(app)


def sample_env():
    spec={
      "environmentKey":"research-1","title":"Unified Research Environment","projectEntityId":"project:research-1","activeSurface":"notebook",
      "components":[
        {"componentKey":"notebook","componentType":"notebook-run","payload":{"notebookRunHash":"nb-1","cellRuns":[]},"role":"authoring"},
        {"componentKey":"visual","componentType":"visual-workspace","componentRef":"sc://workbench/visual/v1","contentHash":"a"*64,"role":"visualization"},
        {"componentKey":"package","componentType":"reproducible-package","componentRef":"sc://workbench/package/p1","contentHash":"b"*64,"role":"reproducibility"}
      ],
      "lineageRefs":["sc://workbench/execution/e1"]
    }
    r=c.post('/research-environment/build',json={"environment":spec}); assert r.status_code==200,r.text
    return r.json()


def test_manifest_and_status():
    m=c.get('/research-environment/manifest').json(); assert m['ok'] and m['version']=='8.3.0'
    assert m['schema']=='sc-workbench-unified-computational-research-environment/1.0'
    assert m['coreContracts']['unifiedResearchSession']=='sc.research.unified-research-scientific-investigation-runtime.v1'
    assert m['boundaries']['automaticExecutionAuthorized'] is False
    s=c.get('/v800/status').json(); assert s['ok'] and s['version']=='8.3.0' and s['v7SeriesIntegrated'] is True


def test_build_validate_and_tamper_detection():
    env=sample_env(); assert env['state']['componentCount']==3 and env['environmentRef'].startswith('sc://workbench/research-environment/')
    v=c.post('/research-environment/validate',json={"researchEnvironment":env}).json(); assert v['valid'] is True
    bad=deepcopy(env); bad['title']='tampered'
    v=c.post('/research-environment/validate',json={"researchEnvironment":bad}).json(); assert v['valid'] is False


def test_required_reference_must_be_hashed():
    spec={"environmentKey":"bad","title":"Bad","projectEntityId":"p","components":[{"componentKey":"d","componentType":"data-workspace","componentRef":"sc://data/x","required":True}]}
    r=c.post('/research-environment/build',json={"environment":spec}); assert r.status_code==422


def test_surface_and_session_plans_are_non_executing():
    env=sample_env()
    p=c.post('/research-environment/surface/plan',json={"researchEnvironment":env,"surface":"simulation","action":"prepare-run","requestPayload":{"simulationKind":"scalar-dynamic"}}).json()
    assert p['targetPath']=='/simulations/run' and p['executionPerformed'] is False and p['automaticDispatchAuthorized'] is False
    s=c.post('/research-environment/session/plan',json={"researchEnvironment":env,"action":"switch-surface","surface":"visual"}).json()
    assert s['requestedSurface']=='visual' and s['environmentPersistencePerformed'] is False


def test_snapshot_plan_targets_v712_package_runtime_without_building():
    env=sample_env()
    p=c.post('/research-environment/snapshot/plan',json={"researchEnvironment":env}).json()
    assert p['targetPath']=='/repro-package/build' and p['packageBuildPerformed'] is False and p['automaticReplayAuthorized'] is False
    assert p['preparedReproPackageRequest']['package']['packageKind']=='mixed'


def test_core_plan_is_two_phase():
    env=sample_env(); headers={'X-SC-Gateway-Service':'workbench','X-SC-Core-Version':'3.0'}
    first=c.post('/integration/core/research-environment/plan',json={"researchEnvironment":env,"coreProjectEntityId":"core-project-1"},headers=headers)
    assert first.status_code==200,first.text; a=first.json(); assert a['phase']=='prepare-session' and a['coreSessionIdMustComeFromCore'] is True
    assert a['coreRequests'][0]['path']=='/v1/research/unified-runtime/sessions' and a['automaticCoreDispatchAuthorized'] is False
    second=c.post('/integration/core/research-environment/plan',json={"researchEnvironment":env,"coreProjectEntityId":"core-project-1","coreSessionId":"core-session-1"},headers=headers)
    assert second.status_code==200,second.text; b=second.json(); assert b['phase']=='bind-environment'
    paths={x['path'] for x in b['coreRequests']}; assert '/v1/research/unified-runtime/product-bindings' in paths and '/v1/research/unified-runtime/object-bindings' in paths and '/v1/research/unified-runtime/visual-bindings' in paths and '/v1/research/unified-runtime/package-bindings' in paths


def test_capabilities_advertise_v800():
    caps=c.get('/capabilities').json(); assert caps['version']=='8.3.0'
    assert caps['coreIntegration']['unifiedComputationalResearchEnvironment'] is True
    assert 'unified-computational-research-environment' in caps['capabilities']
