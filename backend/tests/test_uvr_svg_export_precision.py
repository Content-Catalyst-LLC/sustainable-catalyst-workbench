"""Pure export tests plus real route authentication/owner-isolation checks."""
import copy
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from app.graph_svg import render_svg, display_y_range

CASES = json.loads((Path(__file__).resolve().parents[2] / 'tests/fixtures/uvr-display-range.json').read_text())

def response(values):
    return {'ok': True, 'render': {'graph': {'id': 'g', 'projectId': 'p', 'title': '<script>& test',
            'graphObjectHash': 'graph-hash', 'researchSessionId': 's'},
            'renderHash': 'render-hash', 'renderer': 'standalone-svg-view-renderer/1.0',
            'views': [{'series': [{'x': list(range(len(values))), 'y': values}]}]}}

def coordinates(svg):
    root = ET.fromstring(svg)
    return [[tuple(map(float, p.split(','))) for p in line.attrib['points'].split()]
            for line in root.findall('{http://www.w3.org/2000/svg}polyline')]

@pytest.mark.parametrize('case', CASES, ids=lambda c: c['name'])
def test_display_and_export(case):
    payload = response(case['values'])
    before = copy.deepcopy(payload)
    result = render_svg(payload, 'p', 'g')
    assert payload == before
    assert result == render_svg(payload, 'p', 'g')
    ys = [p[1] for p in coordinates(result['svg'])[0]]
    assert all(math.isfinite(y) for y in ys)
    assert len(ys) == len(case['values'])
    assert (max(ys)-min(ys) < 1e-8) if case['flat'] else (max(ys)-min(ys) > 300)
    assert hashlib.sha256(result['svg'].encode()).hexdigest() == result['svgSha256']
    manifest = json.dumps(result['provenance'], sort_keys=True, separators=(',', ':'))
    assert hashlib.sha256(manifest.encode()).hexdigest() == result['provenanceSha256']
    assert result['provenance']['graphObjectHash'] == 'graph-hash'
    assert result['provenance']['renderHash'] == 'render-hash'
    assert result['provenance']['scientificVerification'] == 'not-asserted'
    assert '<script>' not in result['svg']

@pytest.mark.parametrize('field', ['projectId', 'id', 'graphObjectHash'])
def test_rejects_invalid_identity(field):
    payload = response([1, 1])
    payload['render']['graph'][field] = ''
    with pytest.raises(ValueError): render_svg(payload, 'p', 'g')

@pytest.mark.parametrize('bad', [float('nan'), float('inf'), None, True, '1'])
def test_rejects_invalid_samples(bad):
    with pytest.raises(ValueError): render_svg(response([1, bad]), 'p', 'g')

def test_series_separation():
    payload = response([1, 1])
    payload['render']['views'][0]['series'].append({'points': [[0, 2], [1, 2]]})
    lines = coordinates(render_svg(payload, 'p', 'g')['svg'])
    assert len(lines) == 2
    assert lines[0][0][1] != lines[1][0][1]

def test_route_auth_ownership_integrity(tmp_path, monkeypatch):
    # Small app, real endpoint and auth/store; no full legacy release app or production DB.
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.v1210 import router as auth_router
    from app.v1220 import router as project_router
    from app.v1350 import router as graph_router
    monkeypatch.setenv('SCWB_SESSION_SECRET', 'uvr-local-test-secret-only')
    monkeypatch.setenv('SCWB_PROJECT_STORE_PATH', str(tmp_path / 'graphs.sqlite3'))
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(project_router)
    app.include_router(graph_router)
    client = TestClient(app)
    def headers():
        token = client.post('/standalone/v1/auth/session/anonymous', json={}).json()['token']
        return {'Authorization': f'Bearer {token}'}
    owner, other = headers(), headers()
    project = client.post('/standalone/v1/projects', headers=owner, json={'name': 'Test'}).json()['project']
    graph = client.post('/standalone/v1/graph-studio/graphs', headers=owner, json={
        'projectId': project['id'], 'series': [{'expression': 'sin(x)**2 + cos(x)**2',
        'includeRoots': False, 'includeCriticalPoints': False}], 'samples': 401}).json()['graph']
    url = f"/standalone/v1/graph-studio/graphs/{graph['id']}"
    assert client.get(url+'/export.svg').status_code == 401
    assert client.get(url+'/export.svg', headers={'Authorization': 'Bearer invalid'}).status_code == 401
    assert client.get(url+'/export.svg', headers=other).status_code == 404
    before = client.get(url, headers=owner).json()
    exported = client.get(url+'/export.svg', headers=owner)
    assert exported.status_code == 200
    assert exported.headers['content-type'].startswith('image/svg+xml')
    assert exported.headers['cache-control'] == 'private, no-store'
    assert exported.headers['x-content-type-options'] == 'nosniff'
    assert 'sandbox' in exported.headers['content-security-policy']
    assert graph['id'] in exported.headers['content-disposition']
    assert exported.headers['x-sc-figure-sha256'] == hashlib.sha256(exported.content).hexdigest()
    assert max(y for _, y in coordinates(exported.text)[0])-min(y for _, y in coordinates(exported.text)[0]) < 1e-8
    assert client.get(url, headers=owner).json() == before
