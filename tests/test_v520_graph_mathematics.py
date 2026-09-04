import math
import pytest
from pydantic import ValidationError

from backend.app.v520 import (
    GraphInput, AnalysisInput, VectorFieldInput, SurfaceInput,
    status_record, graph, analyze, vector_field, surface,
)


def test_v520_status_and_boundary():
    s=status_record()
    assert s['version']=='5.2.0'
    for cap in ['cartesian-functions','parametric-curves','polar-curves','implicit-equations','vector-fields','3d-surfaces']:
        assert cap in s['capabilities']
    assert s['arbitraryCodeExecutionAuthorized'] is False
    assert s['pythonEvalAuthorized'] is False
    assert s['remoteShellAuthorized'] is False


def test_cartesian_graph_and_live_parameter():
    r=graph(GraphInput(mode='cartesian', expression='a*x^2', parameters={'a':2}, xMin=-2,xMax=2,yMin=-1,yMax=9,samples=25))['result']
    pts=[p for p in r['series'][0]['points'] if p]
    assert r['version']=='5.2.0' and r['kind']=='cartesian'
    assert pts[0]['y']==8.0 and pts[-1]['y']==8.0
    assert len(r['graphObjectHash'])==64


def test_derivative_and_integral_overlay():
    r=graph(GraphInput(expression='x^2',xMin=-3,xMax=3,yMin=-1,yMax=10,samples=31,derivativeOverlay=True,integralLower=0,integralUpper=3))['result']
    assert len(r['series'])==2
    assert r['series'][1]['role']=='derivative'
    assert r['series'][1]['expression']=='2*x'
    assert r['integralOverlay']['exactText']=='9'


def test_parametric_circle_and_polar_curve():
    p=graph(GraphInput(mode='parametric',expression='cos(t)',expressionY='sin(t)',xMin=-2,xMax=2,yMin=-2,yMax=2,tMin=0,tMax=2*math.pi,samples=33))['result']
    pts=[x for x in p['series'][0]['points'] if x]
    assert abs(pts[0]['x']-1)<1e-9 and abs(pts[0]['y'])<1e-9
    q=graph(GraphInput(mode='polar',expression='2',xMin=-3,xMax=3,yMin=-3,yMax=3,tMin=0,tMax=2*math.pi,samples=33))['result']
    qpts=[x for x in q['series'][0]['points'] if x]
    assert abs(qpts[0]['x']-2)<1e-9


def test_implicit_circle_returns_contour_segments():
    r=graph(GraphInput(mode='implicit',expression='x^2+y^2=4',xMin=-3,xMax=3,yMin=-3,yMax=3,gridSize=31,samples=31))['result']
    assert r['series'][0]['role']=='implicit'
    assert len(r['series'][0]['segments'])>20


def test_roots_extrema_and_intersections():
    r=analyze(AnalysisInput(expression='x^3-3*x',comparisonExpression='0',xMin=-3,xMax=3,analyses=['roots','extrema','intersections']))['result']['analysis']
    roots=[round(x['x'],5) for x in r['roots']]
    assert roots==[-1.73205,0.0,1.73205]
    assert len(r['extrema'])==2
    assert {x['classification'] for x in r['extrema']}=={'minimum','maximum'}
    assert len(r['intersections'])==3


def test_vector_field_is_bounded_and_normalized():
    r=vector_field(VectorFieldInput(uExpression='-y',vExpression='x',gridSize=7))['result']
    assert len(r['arrows'])<=49
    nonzero=next(a for a in r['arrows'] if a['magnitude']>0)
    assert abs(math.hypot(nonzero['u'],nonzero['v'])-1)<1e-9


def test_surface_grid_and_range():
    r=surface(SurfaceInput(expression='x^2+y^2',xMin=-1,xMax=1,yMin=-1,yMax=1,gridSize=9))['result']
    assert len(r['x'])==9 and len(r['y'])==9 and len(r['z'])==9
    assert r['zRange']['min']==0.0
    assert r['zRange']['max']==2.0


def test_graph_limits_reject_unbounded_payloads():
    with pytest.raises(ValidationError):
        GraphInput(expression='x',samples=5000)
    with pytest.raises(ValidationError):
        SurfaceInput(expression='x+y',gridSize=100)


def test_restricted_parser_boundary_applies_to_graphs():
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        graph(GraphInput(expression="__import__('os')",xMin=-1,xMax=1,yMin=-1,yMax=1,samples=25))
