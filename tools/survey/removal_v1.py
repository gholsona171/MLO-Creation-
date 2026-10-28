"""Justice Center v1 removal list -> survey/removal_v1.json + a summary print. The complex takes the WHOLE sc1_19 block, so every
vanilla piece inside the kerb goes: the courts tower, the low block, the library, the Davis sheriff station, the car park, the plaza,
the monument, their LODs, collision, occluders, LOD lights, car generators, path nodes and scenario points.
Kept: the street ymaps' props in the sidewalk band (within KEEP_BAND m of the kerb: street lights, signs, signals), the streets,
their collision. Inputs: site.json, lights_box.tsv, block_files.tsv (all from the survey scripts)."""
import csv, json, math, os, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SV = os.path.join(ROOT, 'survey')
site = json.load(open(os.path.join(SV, 'site.json')))
K = site['block']['kerb_outline_uv']; OX, OY = site['frame']['origin_world']; H = math.radians(site['frame']['heading_deg'])
KEEP_BAND = 4.0


def uv(x, y):
    dx, dy = x - OX, y - OY
    return dx * math.cos(H) + dy * math.sin(H), -dx * math.sin(H) + dy * math.cos(H)


def inside(p, poly):
    c = False; x, y = p
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i - 1], poly[i]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c


def edge_dist(p, poly):
    best = 1e9
    for i in range(len(poly)):
        a, b = poly[i - 1], poly[i]; ex, ey = b[0] - a[0], b[1] - a[1]; L = ex * ex + ey * ey
        t = max(0, min(1, ((p[0] - a[0]) * ex + (p[1] - a[1]) * ey) / L))
        best = min(best, math.hypot(p[0] - a[0] - t * ex, p[1] - a[1] - t * ey))
    return best


ents = site['entities_in_block_live']['list']
block_ents = [e for e in ents if e['ymap'].startswith('lr_sc1_19') and inside((e['u'], e['v']), K)]
road_in = [e for e in ents if not e['ymap'].startswith('lr_sc1_19') and inside((e['u'], e['v']), K)]
road_go = [e for e in road_in if e['lod'] in ('HD', 'ORPHANHD') and edge_dist((e['u'], e['v']), K) > KEEP_BAND]
road_keep = [e for e in road_in if e not in road_go]
lights = collections.Counter()
for r in csv.DictReader(open(os.path.join(SV, 'lights_box.tsv')), delimiter='\t'):
    if inside(uv(float(r['x']), float(r['y'])), K): lights[r['ymap']] += 1
files = [l.split('\t') for l in open(os.path.join(SV, 'block_files.tsv'), encoding='utf-8').read().splitlines()]
out = dict(
    rule='No patchwork: every item goes from the build source (cut rules + metadata writers); nothing is covered over or hand-edited.',
    ymaps_edit=sorted({f[0] for f in files if f[0].endswith('.ymap')} | {'lr_sc1_rd.ymap', 'lr_sc1_rd_strm_3.ymap', 'lr_sc1_lod.ymap', 'lr_sc1_occl_00.ymap', 'lr_sc1_occl_01.ymap', 'lr_sc1_occl_03.ymap',
                                                                          'hei_sc1_rd.ymap', 'hei_sc1_rd_strm_3.ymap', 'hei_sc1_lod.ymap', 'hei_sc1_occl_00.ymap', 'hei_sc1_occl_01.ymap', 'hei_sc1_occl_03.ymap',
                                                                          'sc1_rd.ymap', 'sc1_rd_strm_3.ymap', 'sc1_lod.ymap', 'sc1_occl_00.ymap', 'sc1_occl_01.ymap', 'sc1_occl_03.ymap'}),
    entities_block=dict(count=len(block_ents), by_kind=dict(collections.Counter(e['kind'] for e in block_ents)),
                        by_area=dict(collections.Counter(e['area'] for e in block_ents)), hd_models=sorted({e['name'] for e in block_ents if e['kind'] == 'block model'}),
                        lods=sorted({(e['name'], e['lod']) for e in block_ents if e['lod'] in ('LOD', 'SLOD1', 'SLOD2')})),
    entities_road_ymaps_inside=dict(remove=len(road_go), keep_sidewalk_band=len(road_keep), remove_names=dict(collections.Counter(e['name'] for e in road_go)),
                                    keep_names=dict(collections.Counter(e['name'] for e in road_keep))),
    lod_rule='swap a LOD / SLOD1 / SLOD2 to the empty model only when every descendant is gone (all sc1_19 ones: yes, incl. SLOD2 sc1_lod_19 in lr_sc1_lod if it has no other children - check); road-ymap prop-combo LODs with kept children are cut by the kerb outline (l0_cut_lod), never swapped whole. New LOD chain for the complex: see fit_v1.md.',
    collision_empty=['sc1_19_0.ybn', 'hi@sc1_19_0.ybn', 'hi@sc1_19_1.ybn', 'hi@sc1_19_2.ybn', 'hi@sc1_19_3.ybn', 'hi@sc1_19_4.ybn', 'hi@sc1_19_5.ybn', 'ma@sc1_19_0.ybn'],
    collision_cut_by_kerb=['street ybns reaching inside the kerb (lr_sc1_rd_1/4/10/13/14, hi@lr_sc1_rd_0/1/7/8, ma@lr_sc1_rd_0/1 and the hei_ / base twins): only faces inside the kerb minus the sidewalk band'],
    occluders=['lr_sc1_occl_03: 3 tower boxes, 5 sheriff boxes; occlude models over the block in lr_sc1_occl_00 / 01 / 03 (cut by overlap, l0_occl.ps1)'],
    distant_lod_lights_inside_kerb=dict(lights), live_light_set='vw_ (vw_distlodlights_small028 + medium019 and the vw_lodlights twins)',
    car_generators=len(site['cargens_in_block']), path_nodes=len(site['path_nodes_in_block']), scenario_points=len(site['scenarios_in_block']),
    ai_note='car gens (lr_sc1_rd_strm_3) and scenario points (davis.ymt / rancho.ymt) only switched off in script (area_clear.lua pattern) or by scnpatch - one sp_manifest override per server; path nodes: block the car-park / sheriff-drive nodes (SetRoadsInAngledArea off) + navmesh blocking objects inside the new footprints',
)
json.dump(out, open(os.path.join(SV, 'removal_v1.json'), 'w'), indent=1, default=list)
print('block entities', len(block_ents), out['entities_block']['by_kind'])
print('road-ymap entities inside the kerb: remove', len(road_go), 'keep (sidewalk band)', len(road_keep))
print('LODs', out['entities_block']['lods'])
print('lights', dict(lights))
