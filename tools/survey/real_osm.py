"""Justice Center v1: the real complex from OpenStreetMap (survey/real/overpass_raw.json, Overpass API, ODbL).
Writes survey/real/justice_center.geojson (every building / building:part / plaza / artwork / street in the box, WGS84, with tags)
and survey/real/real_local.json (the same in local metres: x east, y north, origin = the Courts Tower centroid; equirectangular).
Prints every building with its tags so the Justice Center pieces can be named."""
import json, math, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RD = os.path.join(ROOT, 'survey', 'real')
raw = json.load(open(os.path.join(RD, 'overpass_raw.json'), encoding='utf-8'))
nodes = {e['id']: (e['lat'], e['lon']) for e in raw['elements'] if e['type'] == 'node' and 'lat' in e}
TOWER_WAY = 333533679                       # Courts Tower building:part (reference.md, OSM)
ways = {e['id']: e for e in raw['elements'] if e['type'] == 'way'}
rels = [e for e in raw['elements'] if e['type'] == 'relation']
art = [e for e in raw['elements'] if e['type'] == 'node' and e.get('tags', {}).get('tourism') == 'artwork']
t = ways[TOWER_WAY]
pts = [nodes[n] for n in t['nodes'] if n in nodes]
LAT0 = sum(p[0] for p in pts) / len(pts); LON0 = sum(p[1] for p in pts) / len(pts)
KX = 111320.0 * math.cos(math.radians(LAT0)); KY = 110574.0


def loc(lat, lon):
    return round((lon - LON0) * KX, 2), round((lat - LAT0) * KY, 2)


feats, local = [], {}
for w in ways.values():
    tg = w.get('tags', {})
    if not tg: continue
    kind = ('building' if 'building' in tg else 'part' if 'building:part' in tg else 'plaza' if tg.get('highway') == 'pedestrian' or 'area:highway' in tg
            else 'artwork' if tg.get('tourism') == 'artwork' else 'street' if 'highway' in tg else 'other')
    ll = [nodes[n] for n in w['nodes'] if n in nodes]
    if len(ll) < 2: continue
    closed = w['nodes'][0] == w['nodes'][-1]
    geom = {'type': 'Polygon', 'coordinates': [[[p[1], p[0]] for p in ll]]} if closed and kind != 'street' else {'type': 'LineString', 'coordinates': [[p[1], p[0]] for p in ll]}
    feats.append({'type': 'Feature', 'id': f'way/{w["id"]}', 'properties': dict(tg, _kind=kind), 'geometry': geom})
    local[f'way/{w["id"]}'] = dict(kind=kind, tags=tg, closed=closed, xy=[loc(*p) for p in ll])
for a in art:
    feats.append({'type': 'Feature', 'id': f'node/{a["id"]}', 'properties': dict(a['tags'], _kind='artwork'), 'geometry': {'type': 'Point', 'coordinates': [a['lon'], a['lat']]}})
    local[f'node/{a["id"]}'] = dict(kind='artwork', tags=a['tags'], xy=[loc(a['lat'], a['lon'])])
for r in rels:
    feats.append({'type': 'Feature', 'id': f'relation/{r["id"]}', 'properties': dict(r.get('tags', {}), _kind='relation', _members=[m['ref'] for m in r.get('members', [])]), 'geometry': None})
    local[f'relation/{r["id"]}'] = dict(kind='relation', tags=r.get('tags', {}), members=[(m['type'], m['ref'], m.get('role')) for m in r.get('members', [])])
json.dump({'type': 'FeatureCollection', 'source': 'OpenStreetMap contributors, ODbL; Overpass API ' + open(os.path.join(RD, 'overpass_source.txt')).read().strip(),
           'features': feats}, open(os.path.join(RD, 'justice_center.geojson'), 'w'), indent=1)
json.dump(dict(origin_latlon=[LAT0, LON0], m_per_deg=[KX, KY], note='x east, y north, metres, origin = Courts Tower (way 333533679) centroid',
               features=local), open(os.path.join(RD, 'real_local.json'), 'w'), indent=1)


def area(xy):
    return abs(sum(xy[i][0] * xy[i - 1][1] - xy[i - 1][0] * xy[i][1] for i in range(len(xy)))) / 2


for k, f in sorted(local.items(), key=lambda kv: kv[1]['kind']):
    if f['kind'] in ('building', 'part', 'plaza', 'artwork', 'relation'):
        xy = f.get('xy') or [(0, 0)]
        cx = sum(p[0] for p in xy) / len(xy); cy = sum(p[1] for p in xy) / len(xy)
        if abs(cx) > 260 or abs(cy) > 260: continue
        tg = {kk: vv for kk, vv in f['tags'].items() if kk in ('name', 'building', 'building:part', 'building:levels', 'height', 'min_height', 'building:min_level', 'addr:street', 'addr:housenumber', 'highway', 'tourism', 'artist_name', 'layer', 'building:colour', 'roof:shape', 'parking', 'amenity')}
        print(k, f['kind'], 'c=(%.0f,%.0f)' % (cx, cy), 'A=%.0f' % (area(xy) if f.get('closed') else 0), tg)
