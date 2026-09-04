import math
import pytest
from pydantic import ValidationError
from fastapi import HTTPException

from backend.app.v540 import (
    MultiGraphInput, RegionSpec, SeriesSpec, TableInput,
    status_record, multi_graph, table,
)


def test_v540_status_and_boundaries():
    status = status_record()
    assert status['version'] == '5.4.0'
    for cap in [
        'multi-expression-stack', 'per-series-domain-restrictions', 'piecewise-by-domain',
        'pairwise-intersections', 'tangent-lines', 'normal-lines',
        'discontinuity-analysis', 'vertical-asymptotes', 'inequality-regions', 'value-tables',
    ]:
        assert cap in status['capabilities']
    assert status['arbitraryCodeExecutionAuthorized'] is False
    assert status['pythonEvalAuthorized'] is False
    assert status['remoteShellAuthorized'] is False


def test_multi_series_analysis_and_intersections():
    payload = MultiGraphInput(
        series=[
            SeriesSpec(expression='x^3-3*x', label='f'),
            SeriesSpec(expression='0', label='axis'),
        ],
        xMin=-3, xMax=3, yMin=-4, yMax=4, samples=121,
        analyses=['roots', 'extrema', 'intersections'],
    )
    result = multi_graph(payload)['result']
    assert result['version'] == '5.4.0'
    assert result['kind'] == 'advanced-cartesian'
    assert len(result['series']) == 2
    roots = result['analysis']['series'][0]['roots']
    assert [round(item['x'], 5) for item in roots] == [-1.73205, 0.0, 1.73205]
    assert len(result['analysis']['series'][0]['extrema']) == 2
    assert len(result['analysis']['intersections']) == 1
    assert len(result['analysis']['intersections'][0]['points']) == 3
    assert len(result['graphObjectHash']) == 64


def test_domain_restrictions_enable_piecewise_graphs():
    result = multi_graph(MultiGraphInput(
        series=[
            SeriesSpec(expression='x^2', label='left', domainMin=-2, domainMax=0),
            SeriesSpec(expression='2*x+1', label='right', domainMin=0, domainMax=2),
        ],
        xMin=-2, xMax=2, yMin=-2, yMax=5, samples=25,
        analyses=['intersections'],
    ))['result']
    first = result['series'][0]['points']
    second = result['series'][1]['points']
    assert any(p is None for p in first)
    assert any(p is None for p in second)
    assert result['piecewiseByDomainRestriction'] is True
    assert result['series'][0]['domain'] == {'min': -2.0, 'max': 0.0}


def test_derivative_tangent_and_normal_construction():
    result = multi_graph(MultiGraphInput(
        series=[SeriesSpec(expression='x^2', label='f', derivativeOrder=1)],
        xMin=-3, xMax=3, yMin=-2, yMax=10, samples=51,
        analyses=['roots', 'extrema'], tangentAt=1, includeNormal=True,
    ))['result']
    assert result['series'][0]['derivative']['expression'] == '2*x'
    tangent, normal = result['constructions']
    assert tangent['role'] == 'tangent' and abs(tangent['slope'] - 2) < 1e-9
    assert normal['role'] == 'normal' and abs(normal['slope'] + .5) < 1e-9


def test_asymptote_and_discontinuity_analysis():
    result = multi_graph(MultiGraphInput(
        series=[SeriesSpec(expression='1/(x-2)', label='f')],
        xMin=-4, xMax=6, yMin=-10, yMax=10, samples=121,
        analyses=['asymptotes', 'discontinuities'],
    ))['result']
    analysis = result['analysis']['series'][0]
    assert any(abs(item['x'] - 2) < 1e-7 for item in analysis['discontinuities'])
    assert any(item.get('axis') == 'vertical' and abs(item['x'] - 2) < 1e-7 for item in analysis['asymptotes'])
    assert any(item.get('axis') == 'horizontal' and abs(item['y']) < 1e-9 for item in analysis['asymptotes'])


def test_inequality_region_and_value_table():
    series = [SeriesSpec(expression='x^2-4', label='f')]
    result = multi_graph(MultiGraphInput(
        series=series, xMin=-4, xMax=4, yMin=-5, yMax=12, samples=401,
        analyses=['roots'], region=RegionSpec(expression='x^2-4', comparator='lte', level=0),
    ))['result']
    intervals = result['region']['intervals']
    assert len(intervals) == 1
    assert intervals[0]['xMin'] <= -1.95 and intervals[0]['xMax'] >= 1.95
    t = table(TableInput(series=series, xMin=-2, xMax=2, rows=5))['result']
    assert len(t['rows']) == 5
    assert t['rows'][2]['x'] == 0.0 and t['rows'][2]['values'][0] == -4.0


def test_live_parameters_and_series_limits():
    result = multi_graph(MultiGraphInput(
        series=[SeriesSpec(expression='a*sin(b*x)+c', label='f')],
        parameters={'a': 2, 'b': 1, 'c': 1},
        xMin=0, xMax=math.pi/2, yMin=-1, yMax=4, samples=25,
        analyses=[],
    ))['result']
    points = [p for p in result['series'][0]['points'] if p]
    assert abs(points[0]['y'] - 1) < 1e-9
    assert abs(points[-1]['y'] - 3) < 1e-8
    with pytest.raises(ValidationError):
        MultiGraphInput(series=[SeriesSpec(expression='x') for _ in range(9)])


def test_restricted_parser_boundary_is_preserved():
    with pytest.raises(HTTPException):
        multi_graph(MultiGraphInput(
            series=[SeriesSpec(expression="__import__('os')")],
            xMin=-1, xMax=1, yMin=-1, yMax=1, samples=25,
        ))
