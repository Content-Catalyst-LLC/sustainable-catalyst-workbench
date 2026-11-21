"""UVR-01.3 production candidate: pure Python SVG chart export.

Requires a trusted, authenticated Graph Studio render response. Ownership must
be enforced by the calling endpoint, never by values from the request body.
"""
import html
import math
import hashlib
import json


def _points(series):
    if isinstance(series.get('points'), list):
        raw = series['points']
        raw = [(p[0], p[1]) if isinstance(p, (list, tuple)) and len(p) == 2 else (p.get('x'), p.get('y')) if isinstance(p, dict) else (None, None) for p in raw]
    else:
        x, y = series.get('x'), series.get('y')
        if not isinstance(x, list) or not isinstance(y, list) or len(x) != len(y):
            raise ValueError('Series requires equal-length numeric x/y arrays')
        raw = list(zip(x, y))
    if len(raw) < 2:
        raise ValueError('Series must contain at least two points')
    if any(not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x)
           or not isinstance(y, (int, float)) or isinstance(y, bool) or not math.isfinite(y)
           for x, y in raw):
        raise ValueError('Series contains non-finite or non-numeric points')
    return raw


def display_y_range(minimum, maximum):
    """Match standalone-app/display-range.mjs; change display bounds only."""
    spread = maximum - minimum
    magnitude = max(abs(minimum), abs(maximum))
    if spread <= 32 * math.ulp(1.0) * magnitude:
        center = minimum + spread / 2
        span = max(1e-12, abs(center) * 0.2)
        return center - span / 2, center + span / 2
    return minimum, maximum


def render_svg(render_response, expected_project_id, expected_graph_id, caption='', width=900, height=550):
    if not isinstance(render_response, dict) or render_response.get('ok') is not True:
        raise ValueError('Successful authoritative render response required')
    r = render_response.get('render')
    if not isinstance(r, dict) or not isinstance(r.get('graph'), dict):
        raise ValueError('Missing graph')
    g = r['graph']
    if not expected_project_id or g.get('projectId') != expected_project_id:
        raise ValueError('Project mismatch')
    if not expected_graph_id or g.get('id') != expected_graph_id:
        raise ValueError('Graph mismatch')
    if not isinstance(g.get('graphObjectHash'), str) or not g['graphObjectHash']:
        raise ValueError('Missing graph-object hash')
    if not isinstance(r.get('renderHash'), str) or not r['renderHash']:
        raise ValueError('Missing render hash')
    if type(width) is not int or type(height) is not int or not (240 <= width <= 4000 and 180 <= height <= 4000):
        raise ValueError('Invalid dimensions')
    views = r.get('views')
    if not isinstance(views, list) or not views:
        raise ValueError('Missing views')
    datasets = [_points(series) for view in views if isinstance(view, dict) for series in view.get('series', [])]
    if not datasets or sum(map(len,datasets)) > 100000:
        raise ValueError('No valid series or too many points')
    coordinates = [point for dataset in datasets for point in dataset]
    minx, maxx = min(p[0] for p in coordinates), max(p[0] for p in coordinates)
    miny, maxy = min(p[1] for p in coordinates), max(p[1] for p in coordinates)
    if minx == maxx: minx, maxx = minx - 1, maxx + 1
    miny, maxy = display_y_range(miny, maxy)
    left, right, top, bottom = 74, 26, 75, 65
    pw, ph = width-left-right, height-top-bottom
    def sx(v): return left + (v-minx)/(maxx-minx)*pw
    def sy(v): return top + (maxy-v)/(maxy-miny)*ph
    colors = ('#b42318','#007a3d','#314b74','#74532d','#755494')
    lines = ''.join('<polyline fill="none" stroke="%s" stroke-width="2.5" points="%s"/>' %
                    (colors[i%len(colors)],' '.join('%.2f,%.2f' % (sx(x),sy(y)) for x,y in ds))
                    for i,ds in enumerate(datasets))
    title = html.escape(str(g.get('title') or 'Report figure'), quote=True)
    desc = html.escape(str(caption), quote=True)
    provenance = {'graphId':g['id'],'projectId':g['projectId'],'graphObjectHash':g['graphObjectHash'],
                  'renderHash':r['renderHash'],'renderer':r.get('renderer'), 'scientificVerification':'not-asserted'}
    manifest = json.dumps(provenance, sort_keys=True, separators=(',',':'))
    manifest_hash = hashlib.sha256(manifest.encode()).hexdigest()
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{title}">'
           f'<title>{title}</title><desc>{desc}</desc>'
           f'<metadata>provenance-sha256:{manifest_hash}</metadata>'
           f'<rect width="100%" height="100%" fill="#fff"/>'
           f'<text x="{left}" y="40" font-family="sans-serif" font-size="20">{title}</text>'
           f'<path d="M {left} {top} V {top+ph} H {left+pw}" fill="none" stroke="#555"/>{lines}'
           f'<text x="{left}" y="{height-20}" font-size="12" font-family="sans-serif">x: {minx:.4g} to {maxx:.4g}</text>'
           f'<text x="{width-right}" y="{height-20}" text-anchor="end" font-size="12" font-family="sans-serif">y: {miny:.4g} to {maxy:.4g}</text></svg>')
    return {'svg':svg, 'svgSha256':hashlib.sha256(svg.encode()).hexdigest(),
            'provenance':provenance, 'provenanceSha256':manifest_hash}
