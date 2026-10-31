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
import jc3_police_dress as JD, jc3_pgarage_dress as GD
WALL_HUNG = {'prop_fire_exting_2a'} | JD.WALL | GD.WALL          # hung on a wall / ceiling by design: not floor props (jc3_dress_check.py checks them)
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
import jc3_police as JPOL, jc3_pgarage as JGAR
POL1, POL2 = ('plobby', 'pdesk', 'pstaff1'), ('pstaff2', 'pint1', 'pobs1', 'pobs2', 'pint2')
def level(room):
    if room in ('galleria', 'tlobby', 'stair'): return 'L1'
    if room in POL1: return 'P1'
    if room in POL2: return 'P2'
    if room == 'pdeck': return 'B1'
    if room in ('pstair', 'pramp_in', 'pramp_out'): return '-'
    return room[-1]
def police_spaces(lev):
    """area 3: the named spaces of a police level (a prop must stay inside its space, partitions included): 0.11 in on a shared side,
    0.21 on the building's outer lines (0.31 at the lobby's colonnade glass / lining)."""
    outer = (JPOL.WI, JPOL.EI, JPOL.SG, JPOL.NI_LINK, JPOL.NI_FACE, JPOL.EG)
    def ins(r, t_out):
        out = list(r)
        for side, sgn in ((0, 1), (1, -1), (2, 1), (3, -1)):
            out[side] += sgn * (t_out if any(abs(r[side] - o) < 0.02 for o in outer) else 0.11)
        return out
    sp = {}
    if lev == 'P1':
        sp.update({k: [ins(r, 0.21) for r in rs] for k, rs in JPOL.SPACES1.items()})
        sp['plobby'] = [ins(r, 0.31) for r in JPOL.REGIONS['plobby']]; sp['pdesk'] = [ins(r, 0.21) for r in JPOL.REGIONS['pdesk']]
    if lev == 'P2':
        sp.update({k: [ins(r, 0.21) for r in rs] for k, rs in JPOL.SPACES2.items()}); sp.update({k: [ins(r, 0.21)] for k, r in JPOL.SUITES.items()})
    if lev == 'B1':
        sp['pdeck'] = inset_rects([list(r) for r in TK_rects()], 0.31)   # (boundary sides only: its pieces abut)
    return sp
def TK_rects():
    """B1's deck region (as jc3_pgarage_build.deck_region, without Blender)."""
    def minus(a, cuts):
        out = [a]
        for c in cuts:
            nxt = []
            for r in out:
                if c[0] >= r[1] or c[1] <= r[0] or c[2] >= r[3] or c[3] <= r[2]: nxt.append(r); continue
                if c[0] > r[0]: nxt.append((r[0], c[0], r[2], r[3]))
                if c[1] < r[1]: nxt.append((c[1], r[1], r[2], r[3]))
                u0, u1 = max(r[0], c[0]), min(r[1], c[1])
                if c[2] > r[2]: nxt.append((u0, u1, r[2], c[2]))
                if c[3] < r[3]: nxt.append((u0, u1, c[3], r[3]))
            out = nxt
        return out
    return minus(JGAR.B1, [(JGAR.U_FOOT, JGAR.B1[1], JGAR.B1[2], JGAR.TRENCH[1]), JPOL.STAIR_B])
def space_of(sp, u, v):
    for k, rs in sp.items():
        for r in rs:
            if r[0] - 0.12 <= u <= r[1] + 0.12 and r[2] - 0.12 <= v <= r[3] + 0.12: return k
    return None
PLANT = '--plant' in sys.argv
bad = 0; checked = 0
for lev in ('L1', 'A', 'B', 'P1', 'P2', 'B1'):
    rooms = {}
    if lev == 'L1': rooms['galleria'] = [[JP.UA0 + inset, JP.UA1, JP.VA0 + inset, JP.VA1 - inset], [JP.UB0 + inset, JP.UB1 - inset, JP.VB0 - inset, JP.VB1]]
    for k, zs in L['zones'].items():
        if k != 'galleria' and level(k) == lev and lev in ('L1', 'A', 'B'): rooms[k] = inset_rects(zs, 0.31 if k == 'tlobby' else 0.21)
    if lev in ('P1', 'P2', 'B1'): rooms = police_spaces(lev)
    zlev = JP.G if lev in ('L1', 'P1') else JPOL.P2 if lev == 'P2' else JGAR.ZB if lev == 'B1' else JT.FLOORS[lev]
    doors = ([['u', JP.UA1, s0, s1] for _, _, s0, s1, _, _ in JP.door_openings()] if lev == 'L1' else []) + \
            [[o['axis'], o['plane'], o['a0'], o['a1']] for o in L['openings'] if abs(o['z0'] - zlev) < 0.5]
    props = [[q['room'], q['model'], q['u'], q['v'], q['base'] - zlev, q['heading'], 1.0] for q in L['placed']
             if q['model'] not in WALL_HUNG and level(q['room']) == lev]
    if lev in ('P1', 'P2', 'B1'):                                          # area 3: each prop in the named space it stands in
        for q in props: q[0] = space_of(rooms, q[2], q[3]) or q[0]
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
