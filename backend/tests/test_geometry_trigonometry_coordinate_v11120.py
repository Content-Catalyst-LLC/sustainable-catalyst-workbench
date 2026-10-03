from fastapi.testclient import TestClient
import math
from app.main import app

client=TestClient(app)

def test_status():
    d=client.get("/v11120/status").json()
    assert d["version"]=="11.12.0"
    assert d["capabilities"]["triangleGeometry"] is True
    assert d["capabilities"]["coordinateTransforms"] is True

def test_distance_midpoint():
    d=client.post("/calculation-engine/v1/geometry",json={
        "operation":"distance","pointA":[0,0],"pointB":[3,4]
    }).json()
    assert d["result"]["distance"]==5.0
    m=client.post("/calculation-engine/v1/geometry",json={
        "operation":"midpoint","pointA":[0,0],"pointB":[4,6]
    }).json()
    assert m["result"]["midpoint"]==[2.0,3.0]

def test_line_intersection():
    d=client.post("/calculation-engine/v1/geometry",json={
        "operation":"line-intersection",
        "lineA":[[0,0],[2,2]],
        "lineB":[[0,2],[2,0]]
    }).json()
    p=d["result"]["intersections"][0]
    assert p["approximate"]==[1.0,1.0]

def test_circle_properties():
    d=client.post("/calculation-engine/v1/geometry",json={
        "operation":"circle-properties","center":[0,0],"radius":2
    }).json()
    assert d["result"]["areaExact"]=="4*pi"
    assert abs(d["result"]["circumferenceApproximate"]-4*math.pi)<1e-12

def test_triangle_properties():
    d=client.post("/calculation-engine/v1/geometry",json={
        "operation":"triangle-properties",
        "pointA":[0,0],"pointB":[3,0],"pointC":[0,4]
    }).json()
    assert abs(d["result"]["areaApproximate"]-6.0)<1e-12
    assert d["result"]["isRight"] is True

def test_vector_angle_projection():
    d=client.post("/calculation-engine/v1/geometry",json={
        "operation":"vector-angle","vectorA":[1,0],"vectorB":[0,1]
    }).json()
    assert abs(d["result"]["angleDegrees"]-90.0)<1e-12
    p=client.post("/calculation-engine/v1/geometry",json={
        "operation":"vector-projection","vectorA":[2,2],"vectorB":[1,0]
    }).json()
    assert p["result"]["projection"]==[2.0,0.0]
    assert p["verification"]["residualOrthogonalToTarget"] is True

def test_right_triangle():
    d=client.post("/calculation-engine/v1/geometry",json={
        "operation":"trig-solve-right-triangle","sideA":3,"sideB":4
    }).json()
    assert abs(d["result"]["hypotenuse"]-5.0)<1e-12
    assert abs(d["result"]["area"]-6.0)<1e-12

def test_coordinate_rotation():
    d=client.post("/calculation-engine/v1/geometry",json={
        "operation":"coordinate-transform","points":[[1,0]],
        "transform":"rotate","angle":90,"angleUnit":"degrees"
    }).json()
    x,y=d["result"]["points"][0]
    assert abs(x)<1e-12 and abs(y-1)<1e-12

def test_calculation_object():
    payload={
      "calculationObjectRequest":{
        "calculation":{"operation":"evaluate","expression":"1"},
        "requestedResultType":"numeric"
      },
      "geometry":{
        "operation":"distance","pointA":[0,0],"pointB":[3,4]
      }
    }
    d=client.post("/calculation-engine/v1/geometry/calculation-object",json=payload).json()
    assert d["ok"] is True
    assert d["extensions"]["geometry"]["engine"]=="sympy-geometry-numpy"
    assert d["executionPlan"]["geometry"]["operation"]=="distance"
    assert d["provenance"]["geometryResultHash"]
