"""The shipped mlo-data file for Jail I (playbook 08: street door, seats, zones, interactions), generated from the build tables, never by
hand: out/mlo-data/jc_jail.json (world coordinates + GTA headings; find the interior with GetInteriorAtCoords). Seats carry tested: false
until the rig sit test writes them true (jj_probe.py sit -> out/probe_sit.json). Run: py -3 jj_mlo_data.py"""
import json, math, sys
from pathlib import Path
JL = Path(__file__).resolve().parent; sys.path[:0] = [str(JL), str(JL.parent)]
OD = __import__('os').environ.get('JJ_OUT', 'out')                # the output folder (build_jail.sh builds into out_next, then swaps)
import jj_plan as J, jj_fit as JF, jc_frame as F
L = json.load(open(JL / OD / 'jj_layout.json'))
def W(u, v, z): x, y = F.W(u, v); return [round(x, 3), round(y, 3), round(z, 3)]
def joaat(s):
    h = 0
    for c in s.lower().encode():
        h = (h + c) & 0xFFFFFFFF; h = (h + (h << 10)) & 0xFFFFFFFF; h ^= h >> 6
    h = (h + (h << 3)) & 0xFFFFFFFF; h ^= h >> 11; return (h + (h << 15)) & 0xFFFFFFFF
def H(h): return round((h + F.HDEG) % 360.0, 2)
tested = {}
pj = JL / OD / 'probe_sit.json'
if pj.exists():
    for r in json.load(open(pj)).get('seats', []):                  # a result counts only for the seat it tested (same spot, same build numbers)
        i = r['i']
        if i < len(L['seats']) and all(abs(a - b) < 0.011 for a, b in zip(r['seat'], L['seats'][i][:3])): tested[i] = r.get('ok', False)
s0, s1 = J.SALLY['s']; dv = (s0 + s1) / 2
street = {'name': 'sally_port_rollup', 'model': J.ROLLUP[0], 'kind': 'vehicle roll-up (garage door, attribute 5) in Jail I west face, Macdonald St',
          'pos': W(J.JBOX[0] + 0.275, dv, J.SALLY_Z + J.ROLLUP[2] / 2), 'heading': H(90.0), 'width': J.ROLLUP[1], 'height': J.ROLLUP[2],
          'drive_from_street': W(J.JBOX[0] - 8.0, dv, J.SALLY_Z), 'drive_stop_inside': W(J.DRIVE_STOP - 2.5, dv, J.SALLY_Z), 'drive_heading_in': H(270.0),
          'model_hash': joaat(J.ROLLUP[0]), 'model_hash_signed': joaat(J.ROLLUP[0]) - (1 << 32) if joaat(J.ROLLUP[0]) >= 1 << 31 else joaat(J.ROLLUP[0]),
          'lock_config_required': True,
          'note': ('ADD THIS DOOR TO YOUR DOOR-LOCK CONFIG (ox_doorlock or similar: model, coords, heading above; a garage door). The game opens '
                   'the roll-up by itself only for a car ARRIVING from the street; a car reversing out from inside needs the lock system to '
                   'open and hold it, or it cannot leave. Antonio 2026-10-29: "client add locks".')}
doors = [{'name': d['name'], 'model': d['model'], 'pos': W(*d['pos']), 'heading': H(d['heading']), 'rooms': d['rooms']} for d in L['doors']]
seats = [{'i': i, 'pos': W(s[0], s[1], s[2]), 'heading': H(s[3]), 'room': s[4], 'scenario': s[5], 'what': s[6], 'tested': tested.get(i, False)} for i, s in enumerate(L['seats'])]
zones = {k: [{'min': W(r[0], r[2], r[4]), 'max': W(r[1], r[3], r[5]), 'lot_box': r} for r in rs] for k, rs in L['zones'].items()}
ia = [{'kind': 'booking_counter', 'staff': W(-21.45, 9.0, J.G), 'prisoner': W(-18.8, 9.0, J.G), 'heading_staff': H(90.0)},
      {'kind': 'officer_station_cctv', 'pos': W(-23.8, 1.6, J.G), 'heading': H(0.0)},
      {'kind': 'mugshot', 'stand': W(JF.PHOTO['u'], 0.75, J.G), 'camera': W(JF.PHOTO['u'], JF.PHOTO['cam_v'] + 0.4, J.G)},
      {'kind': 'fingerprints', 'pos': W(sum(JF.PRINTS[:2]) / 2, 1.2, J.G), 'heading': H(180.0)},
      {'kind': 'property_counter', 'pos': W(-29.2, 6.8, J.G), 'heading': H(180.0)},
      {'kind': 'cell_block_officer', 'pos': W(-20.5, 23.1, J.L2), 'heading': H(180.0)}]
for k in range(J.CELLS_HOLD): ia.append({'kind': 'holding_cell', 'number': k + 1, 'inside': W(-12.5, k * J.HOLD_P + 1.5, J.G), 'door': f'hold{k + 1}'})
for side in ('w', 'e'):
    for tier, z in ((1, J.L2), (2, J.TIER2)):
        for k in range(J.BLOCK_CELLS):
            u = (J.B_IN[0] + 1.6) if side == 'w' else (J.B_IN[1] - 1.6)
            ia.append({'kind': 'cell', 'id': f'{side.upper()}{tier}{k + 1:02d}', 'inside': W(u, J.cell_v0(k) + 1.2, z), 'door': f'cell_{side}{tier}{k + 1:02d}'})
out = {'mlo': L['mlo'], 'origin': L['origin'], 'heading': L['heading'], 'note': 'Justice Center area 4, Jail I (Corrections Center); world coordinates, GTA headings',
       'street_doors': [street], 'doors': doors, 'seats': seats, 'zones': zones, 'interactions': ia,
       'floors': {'B1_tunnel': J.B1, 'sally_port': J.SALLY_Z, 'L1': J.G, 'L2_cell_block': J.L2, 'L3_upper_tier': J.TIER2},
       'prisoner_route': 'sally port -> airlock -> booking -> holding -> secure corridor -> secure stair down -> B1 tunnel -> courts tower secure lift (B1 stop) -> L3 / L5 holding -> defendant door',
       'secure_lift_b1': {'cab': W(J.CAB_C, (J.SEC_CAB[2] + J.SEC_CAB[3]) / 2, J.B1), 'landing': W(J.CAB_C, J.CAB_EP + 1.2, J.B1), 'bank': 'secure (courts tower, jc_courts lifts.json)'}}
d = JL / OD / 'mlo-data'; d.mkdir(parents=True, exist_ok=True); json.dump(out, open(d / 'jc_jail.json', 'w'), indent=1)
print('JJ_MLO_DATA', len(doors), 'doors', len(seats), 'seats', len(ia), 'interactions')
