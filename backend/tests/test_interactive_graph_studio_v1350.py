import os
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def setup_module():
    os.environ["SCWB_SESSION_SECRET"]="v135-local-session-secret"
    os.environ["SCWB_DEEP_LINK_SECRET"]="v135-local-link-secret"
    os.environ["SCWB_PROJECT_STORE_PATH"]="/tmp/scwb-v1350-test.sqlite3"
    try: os.remove("/tmp/scwb-v1350-test.sqlite3")
    except FileNotFoundError: pass

def token():
    return client.post("/standalone/v1/auth/session/anonymous",json={
        "ttlSeconds":3600,"clientLabel":"v135-test"
    }).json()["token"]

def test_status():
    d=client.get("/v1350/status").json()
    assert d["version"]=="13.5.0"
    assert d["graphStudioReady"] is True
    assert all(d["checks"].values())

def test_graph_lifecycle_and_render():
    h={"Authorization":f"Bearer {token()}"}
    p=client.post("/standalone/v1/projects",headers=h,json={
        "name":"Graph Project","description":"","metadata":{}
    }).json()["project"]
    rs=client.post("/standalone/v1/research-sessions",headers=h,json={
        "projectId":p["id"],"title":"Graph Session","purpose":"",
        "tags":[],"metadata":{}
    }).json()["researchSession"]
    g=client.post("/standalone/v1/graph-studio/graphs",headers=h,json={
        "projectId":p["id"],"researchSessionId":rs["id"],"title":"Functions",
        "graphType":"cartesian",
        "series":[
          {"expression":"sin(x)","label":"sin","variable":"x","visible":True,
           "includeRoots":True,"includeCriticalPoints":True,
           "includeDerivative":False,"includeIntegral":False},
          {"expression":"cos(x)","label":"cos","variable":"x","visible":True,
           "includeRoots":True,"includeCriticalPoints":True,
           "includeDerivative":False,"includeIntegral":False}
        ],
        "domain":[-3.14,3.14],"yDomain":[-2,2],"samples":101,
        "metadata":{"interfaceVersion":"13.5.0"}
    }).json()["graph"]
    assert g["projectId"]==p["id"]
    assert len(g["series"])==2

    listed=client.get(f"/standalone/v1/projects/{p['id']}/graphs",headers=h).json()
    assert listed["count"]==1

    a=client.post(f"/standalone/v1/graph-studio/graphs/{g['id']}/annotations",headers=h,json={
        "kind":"point","label":"Origin","x":0,"y":0,"metadata":{}
    }).json()["annotation"]
    assert a["graphId"]==g["id"]

    rendered=client.post(f"/standalone/v1/graph-studio/graphs/{g['id']}/render",headers=h).json()["render"]
    assert rendered["viewCount"]==2
    assert all(v["kind"]=="cartesian-function" for v in rendered["views"])
    assert rendered["viewSpecAuthority"]=="v11.16 backend"

    updated=client.patch(f"/standalone/v1/graph-studio/graphs/{g['id']}",headers=h,json={
        "title":"Updated Functions","samples":151
    }).json()["graph"]
    assert updated["title"]=="Updated Functions"
    assert updated["samples"]==151

def test_graph_owner_isolation():
    h1={"Authorization":f"Bearer {token()}"}
    h2={"Authorization":f"Bearer {token()}"}
    p=client.post("/standalone/v1/projects",headers=h1,json={
        "name":"Private Graph Project","description":"","metadata":{}
    }).json()["project"]
    g=client.post("/standalone/v1/graph-studio/graphs",headers=h1,json={
        "projectId":p["id"],"title":"Private","graphType":"cartesian",
        "series":[{"expression":"x**2"}],"domain":[-2,2],"yDomain":[-1,5],
        "samples":51,"metadata":{}
    }).json()["graph"]
    assert client.get(f"/standalone/v1/graph-studio/graphs/{g['id']}",headers=h2).status_code==404
