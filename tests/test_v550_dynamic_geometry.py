import math

import pytest

from backend.app.v550 import (
    ConstructionInput,
    ConstraintSpec,
    LocusInput,
    ObjectSpec,
    PointSpec,
    TransformInput,
    construction_object,
    locus_object,
    status_record,
    transform_object,
)


def _point(result, pid):
    return next(p for p in result['points'] if p['id'] == pid)


def test_status_reports_dynamic_geometry_capabilities_and_security_boundary():
    status = status_record()
    assert status['ok'] is True
    assert status['version'] == '5.5.0'
    assert 'draggable-points' in status['capabilities']
    assert 'affine-transformations' in status['capabilities']
    assert 'expression-linked-loci' in status['capabilities']
    assert status['arbitraryCodeExecutionAuthorized'] is False
    assert status['pythonEvalAuthorized'] is False
    assert status['remoteShellAuthorized'] is False


def test_horizontal_constraint_projects_points_and_polygon_measurement_updates():
    payload = ConstructionInput(
        points=[
            PointSpec(id='A', x=-2, y=-1),
            PointSpec(id='B', x=2, y=1),
            PointSpec(id='C', x=0, y=3),
        ],
        objects=[ObjectSpec(id='tri', type='polygon', pointIds=['A', 'B', 'C'], label='ABC')],
        constraints=[ConstraintSpec(type='horizontal', pointIds=['A', 'B'])],
    )
    result = construction_object(payload)['result']
    a, b = _point(result, 'A'), _point(result, 'B')
    assert a['y'] == pytest.approx(b['y'])
    assert result['solver']['converged'] is True
    assert result['measurements'][0]['area'] == pytest.approx(6.0)
    assert len(result['geometryObjectHash']) == 64


def test_fixed_distance_and_midpoint_constraints_are_bounded_and_deterministic():
    payload = ConstructionInput(
        points=[
            PointSpec(id='A', x=0, y=0, fixed=True),
            PointSpec(id='B', x=7, y=0),
            PointSpec(id='M', x=1, y=4),
        ],
        objects=[ObjectSpec(id='ab', type='segment', pointIds=['A', 'B'])],
        constraints=[
            ConstraintSpec(type='distance', pointIds=['A', 'B'], value=4),
            ConstraintSpec(type='midpoint', pointIds=['M', 'A', 'B']),
        ],
        iterations=20,
    )
    result = construction_object(payload)['result']
    a, b, m = _point(result, 'A'), _point(result, 'B'), _point(result, 'M')
    assert math.hypot(b['x'] - a['x'], b['y'] - a['y']) == pytest.approx(4.0)
    assert m['x'] == pytest.approx((a['x'] + b['x']) / 2)
    assert m['y'] == pytest.approx((a['y'] + b['y']) / 2)


def test_circle_equation_and_measurements_follow_center_and_through_point():
    payload = ConstructionInput(
        points=[PointSpec(id='O', x=1, y=-2), PointSpec(id='P', x=4, y=2)],
        objects=[ObjectSpec(id='c1', type='circle', centerId='O', throughId='P', label='c')],
    )
    result = construction_object(payload)['result']
    measurement = result['measurements'][0]
    assert measurement['radius'] == pytest.approx(5.0)
    assert measurement['area'] == pytest.approx(math.pi * 25)
    assert '²' in measurement['equation']


def test_conic_families_are_sampled_without_arbitrary_execution():
    payload = ConstructionInput(
        points=[PointSpec(id='O', x=0, y=0)],
        objects=[
            ObjectSpec(id='e', type='ellipse', centerId='O', radiusX=3, radiusY=2, rotationDegrees=20),
            ObjectSpec(id='p', type='parabola', centerId='O', radiusX=3, radiusY=1),
            ObjectSpec(id='h', type='hyperbola', centerId='O', radiusX=2, radiusY=1),
        ],
    )
    result = construction_object(payload)['result']
    by_id = {o['id']: o for o in result['objects']}
    assert len(by_id['e']['sampledPoints']) == 181
    assert len(by_id['p']['sampledPoints']) == 161
    assert len(by_id['h']['sampledPoints']) > 180


def test_affine_transform_reports_matrix_determinant_and_transforms_selected_points():
    payload = TransformInput(
        points=[PointSpec(id='A', x=2, y=1), PointSpec(id='B', x=-1, y=3)],
        pointIds=['A'],
        matrix=[[0, -1], [1, 0]],
        translation=[0, 0],
        origin=[0, 0],
    )
    result = transform_object(payload)['result']
    a, b = _point(result, 'A'), _point(result, 'B')
    assert (a['x'], a['y']) == pytest.approx((-1, 2))
    assert (b['x'], b['y']) == pytest.approx((-1, 3))
    assert result['determinant'] == pytest.approx(1)
    assert result['orientationPreserved'] is True


def test_reflection_transform_marks_orientation_reversal():
    payload = TransformInput(
        points=[PointSpec(id='A', x=2, y=1)],
        matrix=[[1, 0], [0, -1]],
    )
    result = transform_object(payload)['result']
    assert result['determinant'] == pytest.approx(-1)
    assert result['orientationPreserved'] is False
    assert result['areaScale'] == pytest.approx(1)


def test_expression_linked_locus_uses_restricted_parser_and_returns_canonical_object():
    payload = LocusInput(xExpression='3*cos(t)', yExpression='2*sin(t)', samples=61)
    result = locus_object(payload)['result']
    assert result['finitePointCount'] == 61
    assert len(result['points']) == 61
    assert result['parameter'] == 't'
    assert len(result['geometryObjectHash']) == 64


def test_locus_rejects_unapproved_function_call():
    with pytest.raises(Exception):
        locus_object(LocusInput(xExpression='__import__(1)', yExpression='t', samples=31))


def test_construction_rejects_unknown_point_references():
    with pytest.raises(ValueError):
        ConstructionInput(
            points=[PointSpec(id='A', x=0, y=0)],
            objects=[ObjectSpec(id='bad', type='segment', pointIds=['A', 'Z'])],
        )
