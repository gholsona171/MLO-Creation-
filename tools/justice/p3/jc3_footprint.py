"""Phase 3 prop footprint gate, per level (L1 = galleria + tower lobby + stair foot; A = L3; B = L5): every placed prop inside its
room's usable floor (the region less its linings, inset only on the region's boundary), no two big props overlapping, nothing in a
doorway's swing zone (+-0.8 m at the line, playbook 03) - the playbook's footprint_check.py on our layout, doors of that level only.
Proof: --plant adds a bench across the galleria's ENTRY doorway; the check must flag it. Run: py -3 jc3_footprint.py [--plant]"""
import json, sys, subprocess
from pathlib import Path
P3 = Path(__file__).resolve().parent; sys.path.insert(0, str(P3)); import jc3_plan as JP, jc3_tower as JT
FC = r'C:\Users\anton\Documents\Codex\MLO-Creation\tools\footprint_check.py'
L = json.load(open(P3 / 'out/jc3_layout.json'))
inset = JP.FIN_P + 0.01
WALL_HUNG = {'prop_fire_exting_2a'}                     # hung on a wall face by design (back 1.2 cm off it): not floor props
def inset_rects(zs, t):
    """inset a room's region by its lining, only on the sides that are the region's boundary (pieces of one room abut, no wall)."""
    out = []
    for z in zs:
        r = [z[0], z[1], z[2], z[3]]
        def shared(side):
            for q in zs:
                if q is z: continue
                ov_v = min(q[3], z[3]) - max(q[2], z[2]); ov_u = min(q[1], z[1]) - max(q[0], z[0])
                if side == 0 and abs(q[1] - z[0]) < 1e-6 and ov_v > 0.05: return True
                if side == 1 and abs(q[0] - z[1]) < 1e-6 and ov_v > 0.05: return True
                if side == 2 and abs(q[3] - z[2]) < 1e-6 and ov_u > 0.05: return True
                if side == 3 and abs(q[2] - z[3]) < 1e-6 and ov_u > 0.05: return True
            return False
        for side, sgn in ((0, 1), (1, -1), (2, 1), (3, -1)):
            if shared(side): continue
            outer = abs(z[side] - (JT.IU0, JT.IU1, JT.IV0, JT.IV1)[side]) < 0.02          # on the tower's outer wall: the 0.2 lining
            r[side] += sgn * (t if (outer or t > 0.25) else 0.11)                           # else a 0.1 partition half (+1 cm)
        out.append(r)
    return out
def level(room): return 'L1' if room in ('galleria', 'tlobby', 'stair') else room[-1]
PLANT = '--plant' in sys.argv
bad = 0; checked = 0
for lev in ('L1', 'A', 'B'):
    rooms = {}
    if lev == 'L1': rooms['galleria'] = [[JP.UA0 + inset, JP.UA1, JP.VA0 + inset, JP.VA1 - inset], [JP.UB0 + inset, JP.UB1 - inset, JP.VB0 - inset, JP.VB1]]
    for k, zs in L['zones'].items():
        if k != 'galleria' and level(k) == lev: rooms[k] = inset_rects(zs, 0.31 if k == 'tlobby' else 0.21)
    zlev = JP.G if lev == 'L1' else JT.FLOORS[lev]
    doors = ([['u', JP.UA1, s0, s1] for _, _, s0, s1, _, _ in JP.door_openings()] if lev == 'L1' else []) + \
            [[o['axis'], o['plane'], o['a0'], o['a1']] for o in L['openings'] if abs(o['z0'] - zlev) < 0.5]
    props = [[q['room'], q['model'], q['u'], q['v'], q['base'] - zlev, q['heading'], 1.0] for q in L['placed']
             if q['model'] not in WALL_HUNG and level(q['room']) == lev]
    if PLANT and lev == 'L1': s0, s1 = JP.entrance_span('entry'); props.append(['galleria', JP.BENCH, JP.UA1 - 0.6, (s0 + s1) / 2, 0.0, 90.0, 1.0])
    pj = P3 / f'out/footprint_props_{lev}.json'; json.dump({'rooms': rooms, 'doors': doors, 'props': props}, open(pj, 'w'))
    r = subprocess.run([sys.executable, FC, str(pj), str(P3 / 'survey/arch_ytyp.json')], capture_output=True, text=True)
    lines = [l for l in r.stdout.strip().splitlines() if not (l.startswith('OVERLAP') and l.split()[2] == JP.ROPE and l.split()[3] == JP.ROPE)]
    found = [l for l in lines if l.split()[0] in ('WALL', 'OVERLAP', 'DOORWAY', 'NO')]
    for l in found: print(lev, l)
    if PLANT and lev == 'L1':
        assert any(l.startswith('DOORWAY') for l in found), 'PLANTED DOORWAY BENCH NOT FOUND: the footprint check is broken'
        print('JC3_FOOTPRINT_PLANT_FOUND'); sys.exit(0)
    bad += len(found); checked += len(props)
print('checked', checked, 'props,', bad, 'findings'); print('JC3_FOOTPRINT_PASS' if not bad else 'JC3_FOOTPRINT_FAIL')
