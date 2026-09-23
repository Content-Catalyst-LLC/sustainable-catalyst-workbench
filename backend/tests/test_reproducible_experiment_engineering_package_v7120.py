from copy import deepcopy
from fastapi.testclient import TestClient
from app.main import app
from app.v510 import content_hash

c = TestClient(app)


def package_spec():
    notebook = {"schema":"sc-workbench-notebook-run/1.0","notebookRunHash":"nb-hash","cells":[{"cellId":"a","resultHash":"r1"}]}
    vv = {"schema":"sc-workbench-vv-report/1.0","reportHash":"vv-hash","overallStatus":"pass"}
    return {
        "packageKey":"study-001","title":"Experiment Package","projectEntityId":"project:demo","packageKind":"mixed",
        "components":[
            {"componentKey":"notebook","componentType":"notebook-run","componentRef":"sc://workbench/notebook/nb-1","payload":notebook},
            {"componentKey":"validation","componentType":"validation-report","componentRef":"sc://workbench/validation/vv-1","payload":vv},
            {"componentKey":"external-data","componentType":"dataset","componentRef":"sc://dataset/1","contentHash":"a"*64,"required":True}
        ],
        "environments":[{"environmentKey":"workbench","environmentType":"workbench","environmentRef":"sc://workbench/runtime/8.8.0","versionRef":"8.8.0"}],
        "lineageRefs":["sc://execution/1"],"assumptions":["Declared inputs are complete."],"limitations":["Package pass does not certify scientific validity."]
    }


def test_manifest_status():
    m=c.get('/repro-package/manifest').json(); assert m['ok'] and m['version']=='8.8.0' and m['coreContract']=='sc.research.reproducible-package.v1'
    s=c.get('/v7120/status').json(); assert s['ok'] and s['v7SeriesComplete'] is True and s['automaticReplayAuthorized'] is False


def test_build_validate_and_tamper():
    r=c.post('/repro-package/build',json={'package':package_spec()}); assert r.status_code==200,r.text; p=r.json()
    assert p['integrityManifest']['allRequiredComponentsHashed'] is True and p['boundaries']['reproducibilityCertified'] is False
    v=c.post('/repro-package/validate',json={'reproduciblePackage':p}).json(); assert v['valid'] is True
    bad=deepcopy(p); nb=next(x for x in bad['components'] if x['componentKey']=='notebook'); nb['payload']['cells'][0]['resultHash']='tampered'
    assert c.post('/repro-package/validate',json={'reproduciblePackage':bad}).json()['valid'] is False


def test_reference_only_required_component_must_have_hash():
    s=package_spec(); s['components'][2].pop('contentHash')
    assert c.post('/repro-package/build',json={'package':s}).status_code==422


def test_assemble_replay_and_export_plans_are_nonexecuting():
    payload={"packageKey":"assembled","title":"Assembled","projectEntityId":"project:demo","dataWorkspace":{"workspaceRef":"sc://workbench/data/1","value":1},"notebookRun":{"notebookRunRef":"sc://workbench/notebook/1","notebookRunHash":"n1"},"visualWorkspace":{"visualWorkspaceRef":"sc://workbench/visual/1","visualWorkspaceHash":"v1"}}
    r=c.post('/repro-package/assemble',json=payload); assert r.status_code==200,r.text; p=r.json(); assert len(p['components'])==3
    replay=c.post('/repro-package/replay/plan',json={'reproduciblePackage':p,'mode':'replay'}).json(); assert replay['replayPerformed'] is False and replay['automaticExecutionReplayAuthorized'] is False
    export=c.post('/repro-package/export/plan',json={'reproduciblePackage':p}).json(); assert export['archiveWritePerformed'] is False and export['fileCount']>=4


def test_core_plan_is_two_phase_and_reuses_existing_contract():
    p=c.post('/repro-package/build',json={'package':package_spec()}).json()
    headers={'X-Request-ID':'v7120','X-SC-Gateway-Service':'workbench','X-SC-Core-Version':'3.0'}
    first=c.post('/integration/core/repro-package/plan',json={'reproduciblePackage':p,'coreProjectEntityId':'core-project-1'},headers=headers); assert first.status_code==200,first.text; a=first.json()
    assert a['coreContract']=='sc.research.reproducible-package.v1' and a['corePackageIdMustComeFromCore'] is True and a['automaticCoreDispatchAuthorized'] is False
    second=c.post('/integration/core/repro-package/plan',json={'reproduciblePackage':p,'coreProjectEntityId':'core-project-1','corePackageId':'core-package-1'},headers=headers); assert second.status_code==200,second.text; b=second.json()
    paths=[x['path'] for x in b['coreRequests']]
    assert any(x.endswith('/components') for x in paths) and any(x.endswith('/replay-plans') for x in paths) and any(x.endswith('/snapshots') for x in paths)
    assert b['automaticCoreDispatchAuthorized'] is False and b['automaticReplayAuthorized'] is False


def test_embedded_hash_mismatch_rejected():
    s=package_spec(); s['components'][0]['contentHash']='0'*64
    assert c.post('/repro-package/build',json={'package':s}).status_code==422
