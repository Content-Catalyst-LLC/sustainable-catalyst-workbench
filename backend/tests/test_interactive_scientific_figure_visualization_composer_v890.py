from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)


def _seed(monkeypatch, tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE', str(tmp_path / 'store'))
    project = 'project-v890'
    envkey = 'env-v890'
    env = c.post('/research-environment/build', json={'environment': {'environmentKey': envkey, 'title': 'Figure Environment', 'projectEntityId': project, 'components': []}}).json()
    assert c.post('/research-environment/persistence/save', json={'researchEnvironment': env, 'expectedCurrentRevision': 0, 'reason': 'v890-seed'}).status_code == 200
    ws = c.post('/research-projects/build', json={'project': {'projectKey': project, 'title': 'Figure Project', 'activeEnvironmentKey': envkey, 'activeEnvironmentRevision': 1}}).json()
    assert c.post('/research-projects/save', json={'workspace': ws, 'expectedProjectRevision': 0, 'reason': 'v890-seed'}).status_code == 200
    jobs = []
    for bracket, label in [([0, 3], 'Run A'), ([1, 4], 'Run B'), ([0, 5], 'Run C')]:
        r = c.post('/execution-console/jobs/prepare', json={
            'projectKey': project,
            'runtimeKind': 'solver',
            'label': label,
            'tags': ['figure'],
            'request': {'problemKind': 'root', 'problem': {'expression': 'x**2-4', 'variable': 'x', 'bracket': bracket}, 'solverKey': 'root.brentq'},
        })
        assert r.status_code == 200, r.text
        jid = r.json()['jobId']
        run = c.post(f'/execution-console/jobs/{jid}/run', json={'expectedJobRevision': 1, 'reason': 'v890-seed'})
        assert run.status_code == 200, run.text
        jobs.append(jid)
    return project, jobs


def _metric(catalog, scope='result'):
    key = 'resultMetrics' if scope == 'result' else 'requestMetrics'
    candidates = [x for x in catalog[key] if x['presentCount'] >= 2]
    assert candidates, catalog
    return candidates[0]['metric']


def test_manifest_status_capabilities():
    m = c.get('/figure-composer/manifest').json()
    assert m['ok'] and m['version'] == '9.0.0'
    assert m['capabilities']['multiPanelFigureComposition'] and m['capabilities']['provenanceManifest']
    assert m['boundaries']['automaticScientificEncodingSelectionAuthorized'] is False
    s = c.get('/v890/status').json()
    assert s['multiPanelFigureComposition'] and s['automaticScientificEncodingSelection'] is False
    caps = c.get('/capabilities').json()
    assert caps['version'] == '9.0.0'
    for key in ('interactiveScientificFigureComposer', 'scientificFigureMultiPanelComposition', 'scientificFigureMetricDataBinding', 'scientificFigureProvenanceManifest', 'scientificFigureLinkedSelection', 'scientificFigureExportPlanning', 'scientificFigureCorePlanning'):
        assert caps['coreIntegration'][key] is True


def test_source_catalog_and_multi_panel_composition(monkeypatch, tmp_path):
    project, jobs = _seed(monkeypatch, tmp_path)
    cat = c.get(f'/figure-composer/source-catalog/{project}')
    assert cat.status_code == 200, cat.text
    catalog = cat.json()
    assert catalog['completedJobCount'] == 3 and catalog['resultMetrics']
    result_metric = _metric(catalog, 'result')
    request_metric = _metric(catalog, 'request')
    payload = {
        'projectKey': project,
        'jobIds': jobs,
        'title': 'Solver comparison figure',
        'caption': 'Explicitly composed from completed Workbench runs.',
        'columns': 2,
        'theme': 'publication',
        'linkedSelectionJobIds': [jobs[1]],
        'panels': [
            {'panelId': 'a', 'title': 'Result metric', 'mark': 'bar', 'metricScope': 'result', 'yMetrics': [result_metric], 'yLabel': 'Result'},
            {'panelId': 'b', 'title': 'Request metric', 'mark': 'line', 'metricScope': 'request', 'yMetrics': [request_metric], 'showLegend': False},
        ],
    }
    r = c.post('/figure-composer/compose', json=payload)
    assert r.status_code == 200, r.text
    b = r.json()
    assert b['version'] == '9.0.0' and b['layout']['panelCount'] == 2 and len(b['panels']) == 2
    assert b['panels'][0]['mark'] == 'bar' and b['panels'][0]['scientificEncodingWasExplicitlyRequested'] is True
    assert b['linkedSelection']['jobIds'] == [jobs[1]] and b['linkedSelection']['selectionIsViewStateOnly'] is True
    assert len(b['provenance']['jobs']) == 3 and b['provenance']['sourceHashesPreserved'] is True
    assert b['exportPlan']['json']['available'] is True and b['exportPlan']['svg']['available'] is True
    assert b['boundaries']['automaticScientificEncodingSelectionPerformed'] is False
    assert b['boundaries']['automaticWinnerSelectionPerformed'] is False
    assert b['figureHash']


def test_scatter_requires_explicit_x_metric(monkeypatch, tmp_path):
    project, jobs = _seed(monkeypatch, tmp_path)
    catalog = c.get(f'/figure-composer/source-catalog/{project}').json()
    metric = _metric(catalog, 'result')
    bad = c.post('/figure-composer/compose', json={
        'projectKey': project,
        'jobIds': jobs[:2],
        'panels': [{'panelId': 'scatter', 'mark': 'scatter', 'metricScope': 'result', 'yMetrics': [metric]}],
    })
    assert bad.status_code == 422


def test_unknown_metric_rejected_without_coercion(monkeypatch, tmp_path):
    project, jobs = _seed(monkeypatch, tmp_path)
    bad = c.post('/figure-composer/compose', json={
        'projectKey': project,
        'jobIds': jobs[:2],
        'panels': [{'panelId': 'bad', 'mark': 'bar', 'metricScope': 'result', 'yMetrics': ['result.this_metric_does_not_exist']}],
    })
    assert bad.status_code == 422


def test_core_plan_is_two_phase_and_visual_view_only(monkeypatch, tmp_path):
    project, jobs = _seed(monkeypatch, tmp_path)
    catalog = c.get(f'/figure-composer/source-catalog/{project}').json()
    metric = _metric(catalog, 'result')
    r = c.post('/integration/core/figure-composer/plan', json={
        'projectKey': project,
        'jobIds': jobs[:2],
        'coreSessionId': 'core-v890',
        'title': 'Core-bound figure',
        'panels': [{'panelId': 'a', 'mark': 'point', 'metricScope': 'result', 'yMetrics': [metric]}],
    })
    assert r.status_code == 200, r.text
    b = r.json()
    assert b['version'] == '9.0.0' and b['figureBindingIsAnalyticalViewOnly'] is True
    assert b['automaticCoreDispatchAuthorized'] is False and b['automaticScientificEncodingSelectionAuthorized'] is False
    assert any(x.get('phase') == 'scientific-figure-bind' for x in b['coreRequests'])
