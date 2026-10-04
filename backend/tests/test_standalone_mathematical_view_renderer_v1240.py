import os
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)

def setup_module():
    os.environ["SCWB_SESSION_SECRET"]="v12.4-test-secret"
def teardown_module():
    os.environ.pop("SCWB_SESSION_SECRET",None)

def headers():
    d=client.post("/standalone/v1/auth/session/anonymous",json={"ttlSeconds":600}).json()
    return {"Authorization":f"Bearer {d['token']}"}

def test_status():
    d=client.get("/v1240/status").json()
    assert d["version"]=="12.4.0"
    assert d["rendererAuthority"]=="standalone-app"
    assert d["capabilities"]["standaloneSvgRenderer"] is True

def test_config():
    d=client.get("/standalone/v1/renderer/config",headers=headers()).json()
    assert d["renderer"]["renderer"]=="standalone-svg-view-renderer/1.0"
    assert "cartesian-function" in d["renderer"]["supportedKinds"]

def test_function_view_spec():
    d=client.post("/standalone/v1/renderer/view-spec",headers=headers(),json={
      "graphing":{
        "operation":"function-plot","expression":"x**2-1",
        "variable":"x","domain":[-2,2],"samples":101,
        "includeDerivative":True,"includeIntegral":False,
        "includeRoots":True,"includeCriticalPoints":True
      }
    }).json()
    result=d["viewSpec"]
    assert result["ok"] is True
    assert result["result"]["viewCount"]>=2
    kinds=[v["kind"] for v in result["result"]["views"]]
    assert "cartesian-function" in kinds
    assert "derivative" in kinds
    primary=result["result"]["views"][0]
    roots=[m["x"] for m in primary["markers"] if m["kind"]=="root"]
    assert any(abs(x+1)<1e-7 for x in roots)
    assert any(abs(x-1)<1e-7 for x in roots)

def test_linked_table():
    d=client.post("/standalone/v1/renderer/view-spec",headers=headers(),json={
      "graphing":{
        "operation":"linked-function-study","expression":"x",
        "variable":"x","domain":[-1,1],"samples":25
      }
    }).json()
    kinds=[v["kind"] for v in d["viewSpec"]["result"]["views"]]
    assert "linked-table" in kinds
