"""Justice Center survey: gathers the scans into survey/site.json (lot frame, files, entities, AI, LOD chain).
Lot frame: origin = courts tower centre (335.87, -1640.11), heading 50 deg: u = (cos50, sin50) towards Innocence Blvd,
v = (-sin50, cos50) towards Davis Ave. Inputs: measure.json, near_entities.tsv, block_files.tsv, site_scan.txt,
scenarios.tsv (all written by the scripts in survey/scripts)."""
import csv, json, math, collections, re
S = r'C:\Users\anton\Documents\Codex\JusticeCenter\survey'
OX, OY, HD = 335.87, -1640.11, 50.0
H = math.radians(HD)


def uv(x, y):
    dx, dy = x - OX, y - OY
    return round(dx * math.cos(H) + dy * math.sin(H), 1), round(-dx * math.sin(H) + dy * math.cos(H), 1)


def wxy(u, v):
    return round(OX + u * math.cos(H) - v * math.sin(H), 2), round(OY + u * math.sin(H) + v * math.cos(H), 2)


def inblock(u, v):
    return -52 <= u <= 68 and -74 <= v <= 121


M = json.load(open(S + r'\measure.json'))
# kerb outline of the sc1_19 ground in the lot frame (read off lotframe_height.png, 1 m)
BLOCK_UV = [(-49, -71), (62, -71), (66, -60), (66, 70), (62, 82), (45, 89), (-5, 112), (-30, 121), (-45, 119), (-49, 112)]
PARTS = {
    'courts_tower': dict(uv=[(-24.2, -24.2), (24.2, -24.2), (24.2, 24.2), (-24.2, 24.2)], z_podium=31.5, z_roof=91.7, z_top=97.5,
                         model='sc1_19_courts', note='48.3 m square shaft on a podium deck (z 31.5, about 60 x 60 m); penthouse 36 x 26 m to z 97.5'),
    'city_hall_low_block': dict(uv=[(35, 35), (66, 35), (66, 70), (35, 70)], z_roof=38.8, model='sc1_19_city_hall',
                                note='low 2-storey block, roof z 38.8-39.5 (ground about 28.3)'),
    'plaza_and_monument': dict(centre_uv=(-1, 62), radius_m=28, z=(29.5, 31.5),
                               model='sc1_19_ground, sc1_19_ground_dtl, sc1_19_detail_1..5', note='radial paved plaza, star monument at its centre'),
    'library': dict(uv=[(-48, 83), (-18, 83), (-18, 113), (-48, 113)], z_roof=34.1, model='sc1_19_library'),
    'davis_sheriff_station': dict(uv=[(33, -30), (66, -30), (66, 22), (33, 22)], z_roof=35.9,
                                  model='sc1_19_sheriff, sc1_19_lspd_ban, sc1_19_props_sheriff_heli_shdw',
                                  note='its staff lot runs on to u 32..66, v -71..-30'),
    'multi_storey_car_park': dict(uv=[(-40, -71), (28, -71), (28, -28), (-40, -28)], z_top=47.3,
                                  model='sc1_19_carpk, crprk_det, crprk_lights, stairdetails_*, cp_fence_*', note='5 decks, drive from Roy Lowenstein Blvd'),
    'sw_strip': dict(uv=[(-49, -30), (-28, -30), (-28, 80), (-49, 80)], z=(26.1, 30.4), note='planted strip and sunken beds along Macdonald St'),
}
for p in PARTS.values():
    if 'uv' in p:
        p['world'] = [wxy(*q) for q in p['uv']]
    if 'centre_uv' in p:
        p['centre_world'] = wxy(*p['centre_uv'])


def kind(n):
    if n.startswith('sc1_19'):
        return 'block model'
    if any(k in n for k in ('palm', 'tree', 'bush', 'plant', 'fern', 'weed', 'aloe', 'cat_tail', 'ivy')):
        return 'vegetation'
    if 'light' in n:
        return 'lights'
    if any(k in n for k in ('bench', 'bin', 'bollard', 'cone', 'ticket', 'barrier')):
        return 'street furniture'
    if n.startswith(('sc1_rd', 'sc1_lod', 'sc1_props')) or n.isdigit():
        return 'road / LOD'
    return 'other props'


def where(u, v):
    for n, p in PARTS.items():
        if 'uv' in p:
            us = [q[0] for q in p['uv']]
            vs = [q[1] for q in p['uv']]
            if min(us) <= u <= max(us) and min(vs) <= v <= max(vs):
                return n
    if (u + 1) ** 2 + (v - 62) ** 2 < 32 ** 2:
        return 'plaza_and_monument'
    return 'other ground'


inb = []
for r in csv.DictReader(open(S + r'\near_entities.tsv', encoding='utf-8-sig'), delimiter='\t'):
    u, v = uv(float(r['x']), float(r['y']))
    if inblock(u, v) and r['ymap'].startswith('lr_'):
        n = r['archetype']
        inb.append(dict(ymap=r['ymap'], name=n, ytyp=r['ytyp'], x=float(r['x']), y=float(r['y']), z=float(r['z']), u=u, v=v,
                        lod=r['lodLevel'].replace('LODTYPES_DEPTH_', ''), lodDist=float(r['lodDist']), kind=kind(n), area=where(u, v)))
files = [l.split('\t') for l in open(S + r'\block_files.tsv', encoding='utf-8').read().splitlines()]
log = open(S + r'\site_scan.txt', encoding='utf-8').read().splitlines()
occ = [l for l in log if l.startswith(('BOXOCC', 'OCCMODEL')) and l.split('\t')[1].startswith('lr_')]
dist = [l for l in log if l.startswith('DISTLIGHTS')]
ybn = [l.split('\t') for l in log if l.startswith('YBN')]
cars, nodes, seen = [], [], set()
for l in log:
    if l.startswith('CARGEN') and l.split('\t')[1].startswith('lr_'):
        m = re.search(r'X:([-\d.]+) Y:([-\d.]+) Z:([-\d.]+) model=(\S+) flags=(\d+)', l)
        x, y = float(m.group(1)), float(m.group(2))
        u, v = uv(x, y)
        if inblock(u, v):
            cars.append(dict(x=x, y=y, z=float(m.group(3)), u=u, v=v, model=m.group(4), flags=int(m.group(5)), area=where(u, v)))
    if l.startswith('NODE'):
        f = l.split('\t')
        x, y, z = map(float, f[2].split(','))
        u, v = uv(x, y)
        k = (round(x), round(y), round(z))
        if -46 <= u <= 63 and -68 <= v <= 116 and k not in seen:
            seen.add(k)
            nodes.append(dict(ynd=f[1], x=x, y=y, z=z, u=u, v=v, ped='ped=True' in f[3], area=where(u, v)))
sc = []
for r in csv.DictReader(open(S + r'\scenarios.tsv', encoding='utf-8-sig'), delimiter='\t'):
    u, v = uv(float(r['x']), float(r['y']))
    if -46 <= u <= 63 and -68 <= v <= 116:
        sc.append(dict(ymt=r['ymt'], x=float(r['x']), y=float(r['y']), z=float(r['z']), u=u, v=v, type=r['type'], area=where(u, v)))
blk = dict(M['block'])
blk.pop('hull', None)
out = dict(
    frame=dict(origin_world=[OX, OY], heading_deg=HD, u_axis='towards Innocence Blvd (NE)', v_axis='towards Davis Ave (NW)',
               world_from_lot='x = %.2f + u*cos50 - v*sin50 ; y = %.2f + u*sin50 + v*cos50' % (OX, OY)),
    streets=dict(NW='Davis Ave (the slanted kerb, v about +85..+121)', NE='Innocence Blvd (u about +66)',
                 SE='Roy Lowenstein Blvd (v about -71)', SW='Macdonald St (u about -49)'),
    zone_names=['DAVIS (north half)', 'RANCHO (south half)'],
    block=dict(kerb_outline_uv=BLOCK_UV, kerb_outline_world=[wxy(*q) for q in BLOCK_UV], min_area_box=blk,
               sidewalk_z=[27.6, 28.6], ground_z_p05_p50_p95=M['block_z_p05_p50_p95']),
    parts=PARTS,
    live_ymaps='the lr_ (Lowriders) copies are active in game (IsIplActive on the rig, 2026-10-28); base sc1_19* and hei_sc1_19* hold the same entities and are off',
    files=dict(all=[dict(name=f[0], rank=int(f[1]), path=f[2]) for f in files],
               collision_overlapping_box=[dict(name=y[1], box=y[2], path=y[3]) for y in ybn],
               occluders_live=occ, distant_lights=dist),
    entities_in_block_live=dict(count=len(inb), by_kind=dict(collections.Counter(e['kind'] for e in inb)),
                                by_area=dict(collections.Counter(e['area'] for e in inb)), list=inb),
    cargens_in_block=cars, path_nodes_in_block=nodes, scenarios_in_block=sc,
    interiors='none: GetInteriorAtCoords = 0 at the tower, the city-hall block and the sheriff station; no MLO entity in any sc1_19 ymap',
)
json.dump(out, open(S + r'\site.json', 'w'), indent=1)
print('entities', len(inb), out['entities_in_block_live']['by_kind'])
print('by area', out['entities_in_block_live']['by_area'])
print('cargens', len(cars), collections.Counter(c['area'] for c in cars))
print('nodes', len(nodes), collections.Counter((n['area'], n['ped']) for n in nodes))
print('scen', len(sc), collections.Counter((s['area'], s['type']) for s in sc).most_common(40))
