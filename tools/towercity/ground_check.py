"""Tower City gate (offline, on the BUILT files): what you see is what you walk on, round both lots (Antonio 2026-10-24: knee-deep in
the lawn, waist-deep in the Power St sidewalk, a hole beside the portico steps). Adapted from wow2easy_move/tools/hole_grid_offline.py +
seen_vs_solid.py (playbook doc 07).
  WALKED: every exterior collision the resource ships (resource/tower_city/stream/*.ybn, world space: the cut vanilla files, the lot
          slabs, the exterior skins' and the paving's bounds; the MLO interior bounds are skipped) -> CodeWalker XML (cw_xml.ps1)
  DRAWN:  our exterior drawables (the builds' own tris_*.npy, world space) + every vanilla drawable we ship cut (work/cut, read back
          with tri_dump.py -> work/xml_ground/drawn_vanilla.json)
On a 0.5 m grid (+1.37 / +1.71 cm off the mesh lines) over both lots + 18 m round them, one ray down per cell finds the LOWEST
up-facing face of each set between z 25 and 50 (one-sided, like the game). Per cell:
  MISMATCH  both hit, drawn - walked over TOL (drawn higher: you sink in; lower: you float)
  NOCOL     drawn ground, no collision under it within 1.5 m (you fall / sink to whatever is lower)
  HOLE      collision but nothing drawn, inside our area (the lots + the exterior zones): you see through to below
Cells whose drawn AND walked faces are both Rockstar's untouched-in-place faces are printed apart (his own meshes differ up to ~8 cm).
Run: py -3 tools/ground_check.py [--no-dump]  -> SUMMARY lines, work/ground_check.json; exit 1 on any MISMATCH / NOCOL / HOLE.
Prove it first on a known defect (doc 07): it must flag the knee-deep lawn, the waist-deep sidewalk and the hole by the steps."""
import json, math, re, subprocess, sys, xml.etree.ElementTree as ET, numpy as np
from pathlib import Path
T = Path(r'C:\Users\anton\Documents\Codex\TowerCity'); W = T / 'work'; sys.path.insert(0, str(W))
import ext_plan as EP
STREAM = T / 'resource/tower_city/stream'; XD = W / 'xml_ground'; XD.mkdir(exist_ok=True)
B = r'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\blender-4.5.14-windows-x64\blender.exe'
TOL = 0.05; HEADROOM = 2.2; STEP = 0.5; JX, JY = 0.0137, 0.0171; ZLO = 25.0
PASSES = (50.0, 38.5)            # two looks: everything to z 50 (decks), and the street under the decks (to z 38.5)
SHIPPED = {f.name.lower() for f in STREAM.glob('*.ybn')}
SKIP_DRAWN = r'_fur\d|fur\d+$|^dt1_11_(dt1_planter|hge_r2|hge_r2_d)$'      # grass shells; planters / hedges kept whole (Rockstar's own drawn vs walked)
def _edge(Zd, Zc, j, i):
    """a mismatching cell with fewer than 2 of its 4 neighbours mismatching too: a few-cm lip, not a surface you stand on."""
    n = 0
    for a, b in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        jj, ii = j + a, i + b
        if 0 <= jj < Zd.shape[0] and 0 <= ii < Zd.shape[1] and not np.isnan(Zd[jj, ii]) and not np.isnan(Zc[jj, ii]) and abs(Zd[jj, ii] - Zc[jj, ii]) > TOL: n += 1
    return n < 2
def _alone(Zc, j, i):
    n = [(j + a, i + b) for a, b in ((0, 1), (0, -1), (1, 0), (-1, 0))]
    return sum(1 for jj, ii in n if 0 <= jj < Zc.shape[0] and 0 <= ii < Zc.shape[1] and not np.isnan(Zc[jj, ii])) >= 2
INTERIOR = {'tc_garage', 'tc_mall', 'tc_residences', 'tc_tower', 'tc_under'}
OURS = ['work/extfix/tris_tc_ext_fix.npy', 'work/l3/tris_tc_tower_ext.npy', 'work/l2/tris_tc_mall_ext.npy', 'work/l1/tris_tc_ug_ext.npy',
        'work/gar/tris_tc_garage_ext.npy', 'work/slab/tris_tc_lot_east.npy', 'work/slab/tris_tc_lot_west.npy']
def mat4(txt): return np.array([float(a) for a in txt.split()]).reshape(4, 4)
def tris_of(b):
    out = []
    def walk(b, m):
        ct = b.find('CompositeTransform')
        if ct is not None: m = mat4(ct.text) @ m
        kids = b.find('Children')
        if kids is not None:
            for c in kids: walk(c, m)
        vs = b.find('Vertices')
        if vs is None or not (vs.text or '').strip(): return
        gc = b.find('GeometryCenter'); g = np.array([float(gc.get(k)) for k in 'xyz']) if gc is not None else np.zeros(3)
        V = np.array([[float(a) for a in ln.split(',')] for ln in vs.text.strip().splitlines()]) + g
        V = (np.c_[V, np.ones(len(V))] @ m)[:, :3]
        idx = [(int(t.get('v1')), int(t.get('v2')), int(t.get('v3'))) for t in b.iter('Triangle')]
        if idx: out.append(V[np.array(idx)])
    walk(b, np.eye(4)); return np.concatenate(out) if out else np.zeros((0, 3, 3))
def walked():
    """the shipped exterior ybns + every vanilla ybn round the lots the resource does NOT ship (src/ground_ref, ybn_near_lots.ps1)."""
    files = [f for f in sorted(STREAM.glob('*.ybn')) if f.stem.lower() not in INTERIOR]
    shipped = {f.name.lower() for f in files}
    files += [f for f in sorted((T / 'src/ground_ref').glob('*.ybn')) if f.name.lower() not in shipped]
    ps = ','.join("'%s'" % f for f in files)
    r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', f"& '{W / 'tools/cw_xml.ps1'}' -OutDir '{XD}' -Files @({ps})"],
                       capture_output=True, text=True)
    if r.returncode or r.stdout.count('ok ') != len(files): raise SystemExit('GROUND_CHECK: CodeWalker export failed - nothing was tested: ' + r.stdout[-500:] + r.stderr[-500:])
    T_, src = [], []
    for k, f in enumerate(files):
        x = ET.parse(XD / (f.name + '.xml')).getroot(); b = x if x.tag == 'Bounds' else x.find('.//Bounds')
        t = tris_of(b) if b is not None else np.zeros((0, 3, 3)); T_.append(t); src += [k] * len(t)
    return np.concatenate([t for t in T_ if len(t)]), np.array(src), [f.name for f in files]
def drawn(dump=True):
    """vanilla as the game draws it round the lots (drawn_dump.py: cut models, untouched models, placed) + our exterior drawables."""
    out = W / 'xml_ground/drawn_vanilla.npz'
    if dump:
        r = subprocess.run([B, '-b', '--python', str(W / 'tools/drawn_dump.py'), '--', str(out)], capture_output=True, text=True)
        if 'DRAWN_DUMP' not in r.stdout: raise SystemExit('GROUND_CHECK: drawn_dump failed - nothing was tested: ' + r.stdout[-800:] + r.stderr[-800:])
    Z = np.load(out); V = Z['tris'].astype(np.float64); names = list(Z['names']) + [Path(p).stem.replace('tris_', '') for p in OURS]
    O = [np.load(T / p).astype(np.float64) for p in OURS]
    mid = np.concatenate([Z['mid']] + [np.full(len(o), len(Z['names']) + k) for k, o in enumerate(O)])
    return np.concatenate([V] + O), mid, names, len(Z['names'])
def cast(Tr, X0, Y0, NX, NY, ZHI=50.0):
    """TOP-most up-facing face per cell between ZLO and ZHI (what you see from above and stand on); -> z, triangle index."""
    Z = np.full((NY, NX), np.nan); SRC = np.full((NY, NX), -1, np.int64)
    up = np.cross(Tr[:, 1] - Tr[:, 0], Tr[:, 2] - Tr[:, 0])[:, 2] > 0
    ids = np.nonzero(up)[0]; lo = Tr.min(1); hi = Tr.max(1)
    keep = ids[(hi[ids, 2] > ZLO) & (lo[ids, 2] < ZHI) & (hi[ids, 0] >= X0) & (lo[ids, 0] <= X0 + NX * STEP) & (hi[ids, 1] >= Y0) & (lo[ids, 1] <= Y0 + NY * STEP)]
    for k in keep:
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = Tr[k]
        d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(d) < 1e-12: continue
        i0, i1 = max(0, math.ceil((min(ax, bx, cx) - X0 - JX) / STEP)), min(NX - 1, math.floor((max(ax, bx, cx) - X0 - JX) / STEP))
        j0, j1 = max(0, math.ceil((min(ay, by, cy) - Y0 - JY) / STEP)), min(NY - 1, math.floor((max(ay, by, cy) - Y0 - JY) / STEP))
        if i1 < i0 or j1 < j0: continue
        px, py = np.meshgrid(X0 + JX + np.arange(i0, i1 + 1) * STEP, Y0 + JY + np.arange(j0, j1 + 1) * STEP)
        l1 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / d; l2 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / d; l3 = 1 - l1 - l2
        ins = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
        if not ins.any(): continue
        z = l1 * az + l2 * bz + l3 * cz; ok = ins & (z > ZLO) & (z < ZHI)
        sub = Z[j0:j1 + 1, i0:i1 + 1]; better = ok & ~(z <= np.nan_to_num(sub, nan=-np.inf))
        Z[j0:j1 + 1, i0:i1 + 1] = np.where(better, z, sub); s = SRC[j0:j1 + 1, i0:i1 + 1]; SRC[j0:j1 + 1, i0:i1 + 1] = np.where(better, k, s)
    return Z, SRC
def ours_area():
    P = list(json.load(open(T / 'plan/lot_polys.json')).values()) + json.load(open(T / 'plan/ext_cuts.json'))['occl']
    return P
def inside(poly, x, y):
    c = False; n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]: c = not c
    return c
def main():
    Cw, Csrc, files = walked(); Dw, Dmid, dnames, nvan = drawn('--no-dump' not in sys.argv)
    print('GROUND_CHECK triangles: walked', len(Cw), 'from', len(files), 'files; drawn', len(Dw), 'from', len(dnames), 'models', flush=True)
    HOLES = [q for v in json.load(open(T / 'plan/slab_holes.json')).values() for q in v]       # the buildings' own footprints (their floors)
    LOTS = list(json.load(open(T / 'plan/lot_polys.json')).values()); AREA = ours_area()
    import tower_plan as TP
    su = (TP.PORT[0] - TP.PIER_W - 0.6, TP.PORT[1] + TP.PIER_W + 0.6); land = TP.PV[0] - 2.0 - 1.2
    COLUMNS = [(tuple(m['centre'][:2]) if False else (m['centre'][0] + m['shift'][0], m['centre'][1] + m['shift'][1]), 1.4)
               for m in json.load(open(T / 'plan/ext_cuts.json'))['move']]
    STEPS = [[EP.W(u, v) for u, v in EP.rect(su[0], su[1], land - 6 * 0.27 - 0.3, TP.PV[0])]]   # the portico steps + landing (l3_build)
    xs = [p[0] for q in LOTS for p in q]; ys = [p[1] for q in LOTS for p in q]
    X0, Y0 = min(xs) - 18, min(ys) - 18; NX, NY = int((max(xs) - min(xs) + 36) / STEP), int((max(ys) - min(ys) + 36) / STEP)
    near = lambda x, y, r: any(inside(q, x, y) for q in AREA) or any(min(math.dist((x, y), p) for p in q) < r for q in LOTS)
    rows = {'MISMATCH': [], 'NOCOL': [], 'HOLE': [], 'vanilla_ref': []}
    for ZHI in PASSES:
        Zd, Sd = cast(Dw, X0, Y0, NX, NY, ZHI); Zc, Sc = cast(Cw, X0, Y0, NX, NY, ZHI)
        for j in range(NY):
            for i in range(NX):
                x, y = X0 + JX + i * STEP, Y0 + JY + j * STEP; zd, zc = Zd[j, i], Zc[j, i]
                if np.isnan(zd) and np.isnan(zc):
                    if any(inside(q, x, y) for q in AREA) and not any(inside(q, x, y) for q in HOLES):
                        u, v = EP.L(x, y); rows['HOLE'].append((round(u, 2), round(v, 2), None, 'nothing drawn, nothing to stand on'))
                    continue
                if not near(x, y, 18.0) or any(inside(q, x, y) for q in HOLES): continue
                u, v = EP.L(x, y); van = Sd[j, i] >= 0 and Dmid[Sd[j, i]] < nvan
                if not np.isnan(zd) and re.search(SKIP_DRAWN, dnames[Dmid[Sd[j, i]]]): continue   # grass fur shells, kept planters / hedges: his own
                if any(inside(q, x, y) for q in STEPS): continue                                  # stairs: tread drawn, ramp walked (by design)
                if any(math.dist((x, y), c) <= r for c, r in COLUMNS): continue                   # inside a solid column (the moved deck pier)
                ours_cell = any(inside(q, x, y) for q in AREA)
                dn = dnames[Dmid[Sd[j, i]]] if Sd[j, i] >= 0 else '-'; cn = files[Csrc[Sc[j, i]]] if Sc[j, i] >= 0 else '-'
                if not np.isnan(zd) and np.isnan(zc) and _alone(Zc, j, i): continue           # a 0.5 m cell at a mesh's edge only
                if not np.isnan(zd) and np.isnan(zc): rows['NOCOL'].append((round(u, 2), round(v, 2), round(float(zd), 2), dn + ' / under: ' + (cn if not np.isnan(zc) else 'nothing'))); continue
                if np.isnan(zd):
                    if any(inside(q, x, y) for q in AREA): rows['HOLE'].append((round(u, 2), round(v, 2), round(float(zc), 2), cn))
                    continue
                dz = float(zd - zc)
                if dz > HEADROOM: continue          # drawn well over the walked ground: something you walk UNDER (a cornice, a deck), not ground
                mine = ours_cell or not van or cn.lower().startswith('tc_')
                if abs(dz) > TOL and _edge(Zd, Zc, j, i): continue           # a sliver at an overhang's edge (a coping lip, a ledge's nose)
                if abs(dz) > TOL: (rows['MISMATCH'] if mine else rows['vanilla_ref']).append((round(u, 2), round(v, 2), round(float(zd), 2), round(dz, 3), dn + ' / ' + cn))
    def clusters(r):
        cl = []
        for f in r:
            for c in cl:
                if any(abs(f[0] - p[0]) <= 0.75 and abs(f[1] - p[1]) <= 0.75 for p in c[-3:] + c[:1]): c.append(f); break
            else: cl.append([f])
        return sorted(cl, key=len, reverse=True)
    rep = {}
    for k, r in rows.items():
        cl = clusters(r); rep[k] = [{'n': len(c), 'u': [min(p[0] for p in c), max(p[0] for p in c)], 'v': [min(p[1] for p in c), max(p[1] for p in c)],
                                      'z': c[0][2], 'd': (max((p[3] for p in c), key=abs) if k in ('MISMATCH', 'vanilla_ref') else None), 'what': c[0][-1]} for c in cl]
        for c, cc in zip(rep[k], cl): c['cells'] = [list(p[:3]) for p in cc[:4]]
        print(f'GROUND_CHECK {k:11s} cells {len(r):5d} clusters {len(cl):4d}', flush=True)
        for c in rep[k][:14]: print(f"    n {c['n']:4d}  u {c['u'][0]:7.1f} .. {c['u'][1]:7.1f}  v {c['v'][0]:7.1f} .. {c['v'][1]:7.1f}  z {c['z']}  {c['d']}  {c['what']}")
    json.dump(rep, open(W / 'ground_check.json', 'w'), indent=1)
    AL = json.load(open(T / 'plan/ground_check_allow.json'))['allow']; allowed = 0
    for k in ('MISMATCH', 'NOCOL', 'HOLE'):
        keep = [r for r in rows[k] if not any(a['u'][0] <= r[0] <= a['u'][1] and a['v'][0] <= r[1] <= a['v'][1] for a in AL)]
        allowed += len(rows[k]) - len(keep); rows[k] = keep
    print('GROUND_CHECK allowed (reviewed, plan/ground_check_allow.json):', allowed, 'cells')
    bad = len(rows['MISMATCH']) + len(rows['NOCOL']) + len(rows['HOLE'])
    print('GROUND_CHECK_FAIL' if bad else 'GROUND_CHECK_PASS', bad); sys.exit(1 if bad else 0)
if __name__ == '__main__': main()
