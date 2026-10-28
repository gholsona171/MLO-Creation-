"""Justice Center gate (offline, on the BUILT resource): what you see is what you walk on, over the lot and 18 m round it (Tower City
work/tools/ground_check.py, playbook doc 02 "one ground" / doc 07).
  WALKED: every collision file the resource ships (resource/justice_center/stream/*.ybn: the emptied block files, the cut street files,
          the lot slab's) + every vanilla ybn round the lot the resource does not ship (src/ground_ref, the copy the rig loads: lr_ when it
          exists, else the base name) -> CodeWalker XML (tools/cw_xml.ps1) -> triangles (tools/ybnx.py, boxes as their hulls)
  DRAWN:  every vanilla HD model round the lot the way the game places it AFTER the build (tools/drawn_dump.py, minus every model the
          build swaps to jc_empty: work/maps report) + the lot slab (work/slab/tris_jc_lot.npy)
On a 0.5 m grid (+1.37 / +1.71 cm off the mesh lines) one ray down per cell finds the TOP up-facing face of each set between z 22 and 50
(one-sided, like the game). Per cell:
  MISMATCH  both hit, |drawn - walked| over TOL and under HEADROOM (higher than that is something you walk under: a wire, a crossarm)
  NOCOL     drawn ground, no collision under it
  HOLE      inside the lot: nothing drawn (you see through to below)
edge_crack: a NOCOL cell whose 4 rays 5 cm off it hit (the ray slipped down a shared edge, doc 07) - listed, not a defect.
obstacle: collision 0.15 m+ over the drawn ground within 1.2 m of a kept prop (a palm / birch trunk, a pole) - listed, not ground.
A cell outside the lot whose collision is exactly what Rockstar's untouched files give there (the same cast on the game's own files, no
file of ours) is printed apart as vanilla_ref (his drawn and walked meshes differ up to ~9 cm, and his collision has single-cell cracks).
--plant: the proof run (doc 07: prove a check on a known defect first): the slab's collision loses a 3 x 3 m square at lot (0, 20) and a
2 x 2 m patch at lot (20, 0) is lifted 0.2 m; the run must report NOCOL there and MISMATCH there, or the gate itself is broken.
Run: py -3 tools/ground_check.py [--no-dump] [--plant]  -> GROUND_CHECK_PASS / _FAIL, work/ground_check.json; exit 1 on any defect."""
import json, math, re, subprocess, sys, csv, numpy as np
from pathlib import Path
J = Path(r'C:\Users\anton\Documents\Codex\JusticeCenter'); W = J / 'work'; sys.path.insert(0, str(W)); sys.path.insert(0, str(W / 'tools'))
import jc_frame as F, ybnx
from shapely.geometry import Polygon, Point
from shapely import prepared
STREAM = J / 'resource/justice_center/stream'; XD = W / 'xml_ground'; XD.mkdir(exist_ok=True)
B = r'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\blender-4.5.14-windows-x64\blender.exe'
TOL = 0.05; HEADROOM = 2.2; STEP = 0.5; JX, JY = 0.0137, 0.0171; ZLO, ZHI = 22.0, 50.0; MARGIN = 18.0
PLANT = '--plant' in sys.argv
LOT = Polygon([p[:2] for p in F.lot_w()]); LOTP = prepared.prep(LOT)
def live_names(names):
    out = []
    for n in names:
        base = re.sub(r'^(hi@|ma@)?(lr_|hei_)?', '', n); pre = re.match(r'^(hi@|ma@)?', n).group(1) or ''
        fam = {p: pre + p + base for p in ('lr_', 'hei_', '')}
        pick = fam['lr_'] if fam['lr_'] in names else fam[''] if fam[''] in names else fam['hei_']
        if n == pick: out.append(n)
    return out
def walked(vanilla=False):
    """vanilla=True: the game's own files only (none of ours) - the reference a cell outside the lot is compared with"""
    shipped = [] if vanilla else sorted(STREAM.glob('*.ybn')); sn = {f.stem.lower() for f in shipped}
    refs = {f.stem.lower(): f for f in (J / 'src/ground_ref').glob('*.ybn')}
    keep = live_names(sorted(set(refs) | sn))
    files = [f for f in shipped if f.stem.lower() in keep or f.stem.lower().startswith('jc_')] + [refs[n] for n in keep if n not in sn and n in refs]
    ps = ','.join("'%s'" % f for f in files)
    r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', f"& '{W / 'tools/cw_xml.ps1'}' -OutDir '{XD}' -Files @({ps})"], capture_output=True, text=True)
    if r.returncode or r.stdout.count('ok ') != len(files): raise SystemExit('GROUND_CHECK: CodeWalker export failed - nothing was tested: ' + r.stdout[-500:] + r.stderr[-500:])
    T_, src = [], []
    for k, f in enumerate(files):
        t, m, kd, pr = ybnx.read(XD / (f.name + '.xml'))
        if PLANT and not vanilla and f.stem.lower() == 'jc_lot_col':
            c = t.mean(1); uv = np.array([F.L(x, y) for x, y in c[:, :2]])
            hole = (np.abs(uv[:, 0] - 0) < 1.5) & (np.abs(uv[:, 1] - 20) < 1.5)
            lift = (np.abs(uv[:, 0] - 20) < 1.0) & (np.abs(uv[:, 1] - 0) < 1.0)
            t = t.copy(); t[lift, :, 2] += 0.2; t = t[~hole]
            print('GROUND_CHECK --plant: slab collision', int(hole.sum()), 'triangles removed at lot (0, 20),', int(lift.sum()), 'lifted 0.2 m at lot (20, 0)')
        T_.append(t); src += [k] * len(t)
    return np.concatenate([t for t in T_ if len(t)]), np.array(src), [f.name for f in files]
def drawn(dump=True):
    out = XD / 'drawn_after.npz'; skip = XD / 'skip_after.json'
    rep = json.load(open(W / 'p1_maps_report.json'))
    names = set()
    for f in (W / 'maps').glob('*.ymap.xml'):
        src = J / 'src/ymap' / f.name
        if not src.exists(): continue                                            # our own (jc_lot)
        a = re.findall(r'<archetypeName>([^<]+)', src.read_text(encoding='utf-8')); b = re.findall(r'<archetypeName>([^<]+)', f.read_text(encoding='utf-8'))
        names |= {x.lower() for x, y in zip(a, b) if y == 'jc_empty' and x != 'jc_empty'}
    still = set()
    for f in (W / 'maps').glob('*.ymap.xml'):
        still |= {x.lower() for x in re.findall(r'<archetypeName>([^<]+)', f.read_text(encoding='utf-8'))}
    json.dump(sorted(n for n in names if n not in still), open(skip, 'w'))           # a model swapped everywhere it stands
    if dump:
        r = subprocess.run([B, '-b', '--python', str(W / 'tools/drawn_dump.py'), '--', str(out), '--dirs', str(J / 'src/native'), '--skip', str(skip), '--margin', str(MARGIN + 5)], capture_output=True, text=True)
        if 'DRAWN_DUMP' not in r.stdout: raise SystemExit('GROUND_CHECK: drawn_dump failed - nothing was tested: ' + r.stdout[-800:] + r.stderr[-800:])
    Z = np.load(out); V = Z['tris'].astype(np.float64); nm = list(Z['names'])
    S = np.load(W / 'slab/tris_jc_lot.npy').astype(np.float64)
    return np.concatenate([V, S]), np.concatenate([Z['mid'], np.full(len(S), len(nm))]), nm + ['jc_lot'], len(nm)
def cast(Tr, X0, Y0, NX, NY):
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
def _alone(Zc, j, i):
    n = [(j + a, i + b) for a, b in ((0, 1), (0, -1), (1, 0), (-1, 0))]
    return sum(1 for jj, ii in n if 0 <= jj < Zc.shape[0] and 0 <= ii < Zc.shape[1] and not np.isnan(Zc[jj, ii])) >= 2
def _edge(Zd, Zc, j, i):
    n = 0
    for a, b in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        jj, ii = j + a, i + b
        if 0 <= jj < Zd.shape[0] and 0 <= ii < Zd.shape[1] and not np.isnan(Zd[jj, ii]) and not np.isnan(Zc[jj, ii]) and abs(Zd[jj, ii] - Zc[jj, ii]) > TOL: n += 1
    return n < 2
def main():
    Cw, Csrc, files = walked(); Dw, Dmid, dnames, nvan = drawn('--no-dump' not in sys.argv)
    print('GROUND_CHECK triangles: walked', len(Cw), 'from', len(files), 'files; drawn', len(Dw), 'from', len(dnames), 'models', flush=True)
    xs = [p[0] for p in F.lot_w()]; ys = [p[1] for p in F.lot_w()]
    X0, Y0 = min(xs) - MARGIN, min(ys) - MARGIN; NX, NY = int((max(xs) - min(xs) + 2 * MARGIN) / STEP), int((max(ys) - min(ys) + 2 * MARGIN) / STEP)
    near = prepared.prep(LOT.buffer(MARGIN))
    Zd, Sd = cast(Dw, X0, Y0, NX, NY); Zc, Sc = cast(Cw, X0, Y0, NX, NY)
    Vw, _, _ = walked(vanilla=True); Zv, _ = cast(Vw, X0, Y0, NX, NY)          # Rockstar's own collision, untouched
    def same_as_vanilla(j, i):                                               # outside the lot: the cell walks exactly as it did before the build
        a, b = Zc[j, i], Zv[j, i]
        return (np.isnan(a) and np.isnan(b)) or (not np.isnan(a) and not np.isnan(b) and abs(a - b) < 0.002)
    rows = {'MISMATCH': [], 'NOCOL': [], 'HOLE': [], 'vanilla_ref': [], 'edge_crack': [], 'obstacle': []}; cells = 0
    lo3 = Cw.min(1); hi3 = Cw.max(1); upc = np.cross(Cw[:, 1] - Cw[:, 0], Cw[:, 2] - Cw[:, 0])[:, 2] > 0
    def zat(x, y):
        best = None
        for k in np.nonzero(upc & (lo3[:, 0] <= x) & (hi3[:, 0] >= x) & (lo3[:, 1] <= y) & (hi3[:, 1] >= y))[0]:
            (ax, ay, az), (bx, by, bz), (cx, cy, cz) = Cw[k]; d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(d) < 1e-12: continue
            l1 = ((by - cy) * (x - cx) + (cx - bx) * (y - cy)) / d; l2 = ((cy - ay) * (x - cx) + (ax - cx) * (y - cy)) / d
            if min(l1, l2, 1 - l1 - l2) >= -1e-6:
                z = l1 * az + l2 * bz + (1 - l1 - l2) * cz
                if ZLO < z < ZHI and (best is None or z > best): best = z
        return best
    def crack(Tr, x, y, zd):
        hits = [zat(x + dx, y + dy) for dx, dy in ((0.05, 0), (-0.05, 0), (0, 0.05), (0, -0.05))]
        return sum(1 for h in hits if h is not None and abs(h - zd) <= TOL) >= 3
    rows_ = list(csv.DictReader(open(J / 'plan/near_entities_wide.tsv'), delimiter='	')); ym = {r['ymap'] for r in rows_}
    KEPT = [(k[1], k[2]) for k in json.load(open(W / 'p1_maps_report.json'))['kept_band_lr']]       # props still standing: outside the lot + the band's
    PROPS = np.array([(float(r['x']), float(r['y'])) for r in rows_ if F.live_ymap(r['ymap'], ym) and r['archetype'].startswith('prop_')
                      and 'sc1_19' not in r['ymap'] and r['lodLevel'] in ('LODTYPES_DEPTH_HD', 'LODTYPES_DEPTH_ORPHANHD')
                      and not LOTP.contains(Point(float(r['x']), float(r['y'])))] + KEPT)
    def near_prop(x, y): return bool(len(PROPS)) and float(np.min(np.hypot(PROPS[:, 0] - x, PROPS[:, 1] - y))) < 1.2
    for j in range(NY):
        for i in range(NX):
            x, y = X0 + JX + i * STEP, Y0 + JY + j * STEP; zd, zc = Zd[j, i], Zc[j, i]
            if not near.contains(Point(x, y)): continue
            cells += 1; ins = LOTP.contains(Point(x, y)); u, v = F.L(x, y)
            if np.isnan(zd):
                if ins: rows['HOLE'].append((round(u, 2), round(v, 2), None if np.isnan(zc) else round(float(zc), 2), 'nothing drawn'))
                continue
            dn = dnames[Dmid[Sd[j, i]]]; cn = files[Csrc[Sc[j, i]]] if Sc[j, i] >= 0 else '-'
            if not ins and same_as_vanilla(j, i):                                # Rockstar's own drawn-vs-walked, unchanged by us
                if np.isnan(zc) or abs(float(zd - zc)) > TOL and float(zd - zc) <= HEADROOM: rows['vanilla_ref'].append((round(u, 2), round(v, 2), round(float(zd), 2), None if np.isnan(zc) else round(float(zd - zc), 3), dn + ' / ' + cn))
                continue
            if np.isnan(zc) and crack(Cw, x, y, zd):                         # a ray exactly on a shared edge slipped through (doc 07): 4 rays 5 cm off it hit
                rows['edge_crack'].append((round(u, 2), round(v, 2), round(float(zd), 2), dn)); continue
            if not np.isnan(zc) and float(zd - zc) < -0.15 and near_prop(x, y):   # collision 0.15 m+ over the ground at a standing prop: its trunk / pole (base flare)
                rows['obstacle'].append((round(u, 2), round(v, 2), round(float(zd), 2), round(float(zd - zc), 3), dn + ' / ' + cn)); continue
            if np.isnan(zc):
                rows['NOCOL'].append((round(u, 2), round(v, 2), round(float(zd), 2), dn + ' / under: nothing')); continue
            dz = float(zd - zc)
            if dz > HEADROOM: continue
            if abs(dz) <= TOL: continue
            ours = True                                                      # inside the lot, or a cell outside it that the build changed
            if _edge(Zd, Zc, j, i) and not ins: continue
            (rows['MISMATCH'] if ours else rows['vanilla_ref']).append((round(u, 2), round(v, 2), round(float(zd), 2), round(dz, 3), dn + ' / ' + cn))
    def clusters(r):
        cl = []
        for f in r:
            for c in cl:
                if any(abs(f[0] - p[0]) <= 0.75 and abs(f[1] - p[1]) <= 0.75 for p in c[-3:] + c[:1]): c.append(f); break
            else: cl.append([f])
        return sorted(cl, key=len, reverse=True)
    rep = {'cells': cells}
    for k, r in rows.items():
        cl = clusters(r); rep[k] = [{'n': len(c), 'u': [min(p[0] for p in c), max(p[0] for p in c)], 'v': [min(p[1] for p in c), max(p[1] for p in c)],
                                      'z': c[0][2], 'd': (max((p[3] for p in c if p[3] is not None), key=abs, default=None) if k in ('MISMATCH', 'vanilla_ref') else None), 'what': c[0][-1]} for c in cl]
        print(f'GROUND_CHECK {k:11s} cells {len(r):5d} clusters {len(cl):4d}', flush=True)
        for c in rep[k][:14]: print(f"    n {c['n']:4d}  u {c['u'][0]:7.1f} .. {c['u'][1]:7.1f}  v {c['v'][0]:7.1f} .. {c['v'][1]:7.1f}  z {c['z']}  {c['d']}  {c['what']}")
    json.dump(rep, open(W / ('ground_check_plant.json' if PLANT else 'ground_check.json'), 'w'), indent=1)
    bad = len(rows['MISMATCH']) + len(rows['NOCOL']) + len(rows['HOLE'])
    print('GROUND_CHECK cells tested', cells)
    if PLANT:
        hit_hole = any(abs(r[0]) < 1.6 and abs(r[1] - 20) < 1.6 for r in rows['NOCOL'])
        hit_lift = any(abs(r[0] - 20) < 1.1 and abs(r[1]) < 1.1 for r in rows['MISMATCH'])
        print('GROUND_CHECK_PLANT', 'PROVEN' if hit_hole and hit_lift else 'NOT PROVEN', '(planted hole found: %s, planted lift found: %s)' % (hit_hole, hit_lift))
        sys.exit(0 if hit_hole and hit_lift else 1)
    print('GROUND_CHECK_FAIL' if bad else 'GROUND_CHECK_PASS', bad); sys.exit(1 if bad else 0)
if __name__ == '__main__': main()
