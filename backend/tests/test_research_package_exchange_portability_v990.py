import base64
import io
import json
import zipfile

from fastapi.testclient import TestClient
from app.main import app

c=TestClient(app)


def seed_project(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    p='p990'; env='env-'+p
    e=c.post('/research-environment/build',json={'environment':{'environmentKey':env,'title':'Portable research environment','projectEntityId':p,'components':[]}}); assert e.status_code==200,e.text
    s=c.post('/research-environment/persistence/save',json={'researchEnvironment':e.json(),'expectedCurrentRevision':0,'reason':'v990-test'}); assert s.status_code==200,s.text
    b=c.post('/research-projects/build',json={'project':{'projectKey':p,'title':'Portable research project','researchQuestion':'Can this research state be exchanged reproducibly?','objectives':['package research state'],'activeEnvironmentKey':env,'activeEnvironmentRevision':1}}); assert b.status_code==200,b.text
    sp=c.post('/research-projects/save',json={'workspace':b.json(),'expectedProjectRevision':0,'reason':'v990-test'}); assert sp.status_code==200,sp.text
    return p


def seed_meta(p):
    payload={'projectKey':p,'analysisKey':'meta-portable','title':'Portable meta-analysis','effectMeasure':'generic','studies':[
        {'studyKey':'s1','effectValue':0.2,'standardError':0.1},
        {'studyKey':'s2','effectValue':0.4,'standardError':0.12},
    ],'models':['fixed-effect'],'createdBy':'tester'}
    r=c.post('/cross-study-meta/meta-analyses',json=payload); assert r.status_code==200,r.text
    return r.json()


def build_package(p,analysis_hash=None):
    selections=[]
    if analysis_hash:
        selections=[{'objectType':'cross-study-meta-analysis','objectHash':analysis_hash,'label':'Pooled effect'}]
    r=c.post('/research-package-exchange/packages',json={'projectKey':p,'packageKey':'portable-1','title':'Portable package','description':'Exchange test','selections':selections,'includeProjectWorkspace':True,'createdBy':'tester'})
    assert r.status_code==200,r.text
    return r.json()


def test_manifest_and_status():
    m=c.get('/research-package-exchange/manifest').json(); assert m['ok'] and m['version']=='9.11.0'
    assert m['capabilities']['realZipArchiveExport'] and m['capabilities']['nonMutatingImportValidation']
    assert m['boundaries']['automaticNativeObjectOverwrite'] is False
    s=c.get('/v990/status').json(); assert s['researchPackageExchangePortability'] and s['nativeStoreMutationOnStage'] is False


def test_build_package_download_and_integrity(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); a=seed_meta(p); pkg=build_package(p,a['analysisHash'])
    assert pkg['ok'] and pkg['objectCount']==2 and len(pkg['packageHash'])==64 and len(pkg['archiveSha256'])==64
    d=c.get(pkg['archiveDownloadPath']); assert d.status_code==200 and d.headers['content-type'].startswith('application/zip')
    assert len(d.content)>100
    with zipfile.ZipFile(io.BytesIO(d.content)) as zf:
        names=set(zf.namelist()); assert 'manifest.json' in names and any(x.startswith('objects/') for x in names)
        manifest=json.loads(zf.read('manifest.json')); assert manifest['packageHash']==pkg['packageHash'] and len(manifest['objectFiles'])==2


def test_deterministic_package_hash_and_idempotence(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); a=seed_meta(p); x=build_package(p,a['analysisHash']); y=build_package(p,a['analysisHash'])
    assert x['packageHash']==y['packageHash'] and y['idempotent'] is True


def test_validate_exported_archive(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); a=seed_meta(p); pkg=build_package(p,a['analysisHash']); raw=c.get(pkg['archiveDownloadPath']).content
    r=c.post('/research-package-exchange/import/validate',json={'archiveBase64':base64.b64encode(raw).decode()}); assert r.status_code==200,r.text
    v=r.json(); assert v['ok'] and v['compatible'] and v['packageHashValid'] and v['packageHash']==pkg['packageHash'] and all(x['sha256Valid'] and x['payloadHashValid'] for x in v['integrityChecks'])


def test_corrupted_archive_is_reported(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); pkg=build_package(p); raw=c.get(pkg['archiveDownloadPath']).content
    src=zipfile.ZipFile(io.BytesIO(raw)); out=io.BytesIO()
    with src, zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            data=src.read(info.filename)
            if info.filename.startswith('objects/'):
                data=b'{"tampered":true}'
            dst.writestr(info.filename,data)
    r=c.post('/research-package-exchange/import/validate',json={'archiveBase64':base64.b64encode(out.getvalue()).decode()}); assert r.status_code==200,r.text
    v=r.json(); assert v['ok'] is False and any('mismatch' in e for e in v['errors'])


def test_stage_requires_explicit_confirmation(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); pkg=build_package(p); raw=c.get(pkg['archiveDownloadPath']).content; b64=base64.b64encode(raw).decode()
    r=c.post('/research-package-exchange/import/stage',json={'archiveBase64':b64,'targetProjectKey':p,'confirmStage':False}); assert r.status_code==409
    r=c.post('/research-package-exchange/import/stage',json={'archiveBase64':b64,'targetProjectKey':p,'confirmStage':True,'stagedBy':'tester'}); assert r.status_code==200,r.text
    d=r.json(); assert d['activationState']=='staged-only' and d['boundaries']['nativeResearchStoresMutated'] is False and d['boundaries']['importedObjectsActivated'] is False
    ls=c.get(f'/research-package-exchange/imports/{p}').json(); assert ls['stagingCount']==1


def test_stage_is_idempotent(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); pkg=build_package(p); raw=c.get(pkg['archiveDownloadPath']).content; body={'archiveBase64':base64.b64encode(raw).decode(),'targetProjectKey':p,'confirmStage':True}
    a=c.post('/research-package-exchange/import/stage',json=body).json(); b=c.post('/research-package-exchange/import/stage',json=body).json(); assert a['stagingHash']==b['stagingHash'] and b['idempotent'] is True


def test_source_catalog_and_package_listing(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); build_package(p)
    cat=c.get(f'/research-package-exchange/source-catalog/{p}').json(); assert cat['ok'] and cat['portablePackageCount']==1 and 'crossStudyMetaAnalyses' in cat['catalogs']
    ls=c.get(f'/research-package-exchange/packages/{p}').json(); assert ls['packageCount']==1


def test_core_plan_is_plan_only(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); pkg=build_package(p)
    r=c.post('/integration/core/research-package-exchange/plan',json={'projectKey':p,'packageHash':pkg['packageHash'],'createdBy':'tester'}); assert r.status_code==200,r.text
    d=r.json(); assert d['bindingPlan']['objectType']=='workbench.portable-research-package' and d['boundaries']['automaticCoreDispatch'] is False and d['boundaries']['governedCoreObjectCreated'] is False


def test_unsafe_zip_path_rejected():
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as zf:
        zf.writestr('../escape.json','{}'); zf.writestr('manifest.json','{}')
    r=c.post('/research-package-exchange/import/validate',json={'archiveBase64':base64.b64encode(buf.getvalue()).decode()}); assert r.status_code==409


def test_capability_flags():
    caps=c.get('/capabilities').json(); assert caps['version']=='9.11.0'
    for k in ('researchPackageExchangePortability','researchPackageContentAddressedExport','researchPackageZipArchiveExport','researchPackageIntegrityVerification','researchPackageDependencyInventory','researchPackageCompatibilityAssessment','researchPackageImportStaging','researchPackageCorePlanning'):
        assert caps['coreIntegration'][k] is True
