import os
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
DB='/tmp/scwb-v1310-test.sqlite3'

def setup_module():
    Path(DB).unlink(missing_ok=True)
    os.environ['SCWB_SESSION_SECRET']='v131-test-session-secret'
    os.environ['SCWB_DEEP_LINK_SECRET']='v131-test-link-secret'
    os.environ['SCWB_PROJECT_STORE_PATH']=DB
    os.environ['SCWB_STANDALONE_APP_URL']='https://workbench.example.test'
    os.environ['SCWB_PUBLIC_API_URL']='https://workbench-api.example.test'
    os.environ['SCWB_ALLOWED_ORIGINS']='https://workbench.example.test'

def teardown_module():
    for k in ['SCWB_SESSION_SECRET','SCWB_DEEP_LINK_SECRET','SCWB_PROJECT_STORE_PATH','SCWB_STANDALONE_APP_URL','SCWB_PUBLIC_API_URL','SCWB_ALLOWED_ORIGINS']: os.environ.pop(k,None)
    for p in [DB,DB+'-wal',DB+'-shm']: Path(p).unlink(missing_ok=True)

def token(): return client.post('/standalone/v1/auth/session/anonymous',json={'ttlSeconds':600,'clientLabel':'v1310'}).json()['token']

def test_status():
    d=client.get('/v1310/status').json(); assert d['version']=='13.1.0'; assert d['hardeningReady'] is True; assert d['wordpressRequired'] is False

def test_deployment_contract():
    d=client.get('/standalone/v1/interface/deployment-contract').json()['deployment']; assert d['frontendVersion']=='13.1.0'; assert d['backendVersion']=='13.1.0'; assert d['frontendVersionAsset']=='/version.json'

def test_hardening_readiness():
    d=client.get('/standalone/v1/interface/hardening-readiness').json(); assert d['hardeningReady'] is True; assert all(d['checks'].values())

def test_version_probe_auth():
    assert client.get('/standalone/v1/interface/version-probe').status_code in (401,403)
    d=client.get('/standalone/v1/interface/version-probe',headers={'Authorization':f'Bearer {token()}'}).json(); assert d['frontendExpectedVersion']=='13.1.0'; assert d['backendVersion']=='13.1.0'
