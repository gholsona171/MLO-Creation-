"""The shipped mlo-data file's phase 3 part (playbook 08: street door, seats, zones, interactions), generated from the build tables,
never by hand: work/p3/out/mlo-data/jc_courts.json (world coordinates + GTA headings; interior found with GetInteriorAtCoords).
Seats are marked tested: false until the rig sit test. Run: py -3 jc3_mlo_data.py"""
import json, math, sys
from pathlib import Path
P3 = Path(__file__).resolve().parent; sys.path[:0] = [str(P3), str(P3.parent)]
import jc3_plan as JP, jc3_police as JPOL, jc_frame as F
L = json.load(open(P3 / 'out/jc3_layout.json'))
def W(u, v, z): x, y = F.W(u, v); return [round(x, 3), round(y, 3), round(z, 3)]
def H(h): return round((h + F.HDEG) % 360.0, 2)
def joaat(n):
    h = 0
    for c in n.lower().encode():
        h = (h + c) & 0xffffffff; h = (h + (h << 10)) & 0xffffffff; h ^= h >> 6
    h = (h + (h << 3)) & 0xffffffff; h ^= h >> 11; return (h + (h << 15)) & 0xffffffff
assert joaat('prop_hw1_03_gardoor_01') == 0x76B3CC32, 'joaat is wrong (Jail I sally port roll-up hash)'
ROLLUPS = {d['name'] for d in L['rollups']}
doors, inner = [], []                                                      # street doors: every door on a portal to outside (limbo); all east-facing
for d in L['doors']:                                                       # (galleria entries, police front pair, the two garage roll-ups)
    u, v, z = d['pos']; e = {'name': d['name'], 'model': d['model'], 'hash': '0x%08X' % joaat(d['model']), 'pos': W(u, v, z), 'heading': H(d['heading']),
                             'rooms': d['rooms']}
    if 'limbo' not in d['rooms']: inner.append(e); continue
    zf = z - 3.28 / 2 if d['name'] in ROLLUPS else {'galleria': JP.G, 'plobby': JPOL.P1}[d['rooms'][0]]   # stand on the floor (a roll-up's pivot is its centre)
    e.update({'street': True, 'stand_outside': W(u + 1.5, v, zf), 'stand_inside': W(u - 1.5, v, zf)})
    if d['name'] in ROLLUPS: e['lock'] = 'garage door: the buyer adds it to the server door-lock config (it does not open for a car by itself)'
    doors.append(e)
seats = [{'pos': W(*s[:3]), 'heading': H(s[3]), 'scenario': 'PROP_HUMAN_SEAT_BENCH', 'model': JP.BENCH, 'tested': False} for s in L['seats']]
zones = {k: [{'min': W(r[0], r[2], r[4]), 'max': W(r[1], r[3], r[5]), 'lot_box': r} for r in rs] for k, rs in L['zones'].items()}
ia = [{'kind': 'security_desk', 'pos': W(JP.DESK['u'][0] - 0.95, 0.0, JP.G), 'heading': H(270.0)},
      {'kind': 'exit_lane_guard', 'pos': W(JP.PODIUM['u'][0] - 0.6, sum(JP.PODIUM['v']) / 2, JP.G), 'heading': H(270.0)}]
for i, (bv, dv) in enumerate(JP.LANES):
    ia += [{'kind': 'xray_belt', 'lane': i + 1, 'load': W(JP.SCREEN_U + 1.9, bv, JP.G), 'collect': W(JP.SCREEN_U - 1.9, bv, JP.G)},
           {'kind': 'metal_detector', 'lane': i + 1, 'in': W(JP.SCREEN_U + 1.0, dv, JP.G), 'out': W(JP.SCREEN_U - 1.0, dv, JP.G)}]
out = {'mlo': L['mlo'], 'origin': L['origin'], 'heading': L['heading'], 'note': 'phase 3 courts + Police HQ (jc_courts): world coordinates, GTA headings; street_doors = every door to outside',
       'street_doors': doors, 'interior_doors': inner, 'seats': seats, 'zones': zones, 'interactions': ia, 'floors': {'galleria': JP.G}}
d = P3 / 'out/mlo-data'; d.mkdir(parents=True, exist_ok=True); json.dump(out, open(d / 'jc_courts.json', 'w'), indent=1)
print('JC3_MLO_DATA', len(doors), 'street doors', len(inner), 'interior doors', len(seats), 'seats', len(ia), 'interactions')
