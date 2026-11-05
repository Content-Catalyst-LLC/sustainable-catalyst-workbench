import base64, hashlib, json
from pathlib import Path
import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app import scientific_figures as figures, v1210, v1220, v1340

def test_owned_persistent_source_handoff(tmp_path,monkeypatch):
    monkeypatch.setenv('SCWB_PROJECT_STORE_PATH',str(tmp_path/'workbench.db'))
    monkeypatch.setenv('SCWB_SESSION_SECRET','test-only-persistent-secret')
    monkeypatch.setenv('SCWB_LIBRARY_URL','http://library.test')
    monkeypatch.setenv('SCWB_LIBRARY_TOKEN','test-library-token')
    raw=json.dumps({'schema':'sc-lab-scientific-visualization/1.0','cells':[{'z':1}],
        'scientificContext':{'unit':'test','source':{'sha256':'a'*64,'citation':'Synthetic only'}}}).encode()
    digest=hashlib.sha256(raw).hexdigest()
    real_client=httpx.Client
    def upstream(request):
        assert request.headers['Authorization']=='Bearer test-library-token'
        return httpx.Response(200,content=raw)
    monkeypatch.setattr(figures.httpx,'Client',lambda **kw:real_client(transport=httpx.MockTransport(upstream),**kw))
    token=v1210.create_anonymous_session(v1210.AnonymousSessionRequest())['token']
    owner,_=v1220._owner('Bearer '+token)
    project=v1220.create_project(v1220.ProjectCreateRequest(name='Synthetic acceptance'),owner)
    session=v1340.create_research_session(v1340.ResearchSessionCreateRequest(projectId=project['id'],title='Source import',metadata={'workspaceProjectId':'ws-acceptance'}),owner)
    app=FastAPI();app.include_router(figures.router)
    with TestClient(app) as client:
        root='/standalone/v1/research-sessions/'+session['id']+'/scientific-figures'
        body={'artifactId':'artifact:sha256:'+digest,'workspaceProjectId':'ws-acceptance'}
        assert client.post(root,json=body).status_code==401
        headers={'Authorization':'Bearer '+token}
        assert client.post(root,json={**body,'workspaceProjectId':'other'},headers=headers).status_code==409
        assert client.post(root,json={**body,'artifactId':'artifact:sha256:'+'0'*64},headers=headers).status_code==409
        result=client.post(root,json=body,headers=headers)
        assert result.status_code==201,result.text
        target=root+'/'+result.json()['figure']['id']
        reopened=client.get(target,headers=headers).json()['figure']
        assert base64.b64decode(reopened['metadata']['contentBase64'])==raw
        other=v1210.create_anonymous_session(v1210.AnonymousSessionRequest())['token']
        assert client.get(target,headers={'Authorization':'Bearer '+other}).status_code==404
        assert client.get(target,headers=headers).json()['figure']==reopened
