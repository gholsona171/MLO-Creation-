"""Offline hole grid (2026-10-23, ground-fix pass): hole_grid.py's check run on the BUILT FILES instead of the game, so a collision
fix can be proven before it is deployed. Every collision the resource ships near the garage is read back from the compiled files
(CodeWalker XML via cw_xml.ps1): the static ybn (vanilla cut by site_col.py, the MLO's own jy_shop8_mlo.ybn at the MLO origin) and
the embedded bounds of our placed drawables (lot quadrants, yard walls, gate, exterior skin, road sign) at their ymap positions.
The same 0.5 m grid as hole_grid.py (same origin / step) gets one vertical ray per cell through every layer to the LOWEST
triangle hit between z 30 and 60, and the same hole / pit / floating rules + the asphalt edge step are applied.
Limits: triangles only (box / sphere / capsule primitives are props - not ground), doors and props are not loaded (a roll-up door
reads 'floating' in game and 'hole' here when nothing is under it - both are failures), vanilla collision the resource does not ship
is absent (the scan box is the site, every vanilla file there ships).
Run: py -3 hole_grid_offline.py [stream dir] [--compare]   -> ../site/hole_grid_offline.json/.npy; --compare prints the cells where
the in-game scan (../site/hole_grid.npy) and this one disagree on hole / not hole (run it on the deployed build to trust it)."""
import json, math, re, subprocess, sys, xml.etree.ElementTree as ET, numpy as np
from pathlib import Path
T = Path(__file__).resolve().parent; M = T.parent; sys.path.insert(0, str(T))
import lot_plan as L
STREAM = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else M / 'resource' / 'rocky_shop8_junkyard' / 'stream'
XMLD = M / 'site' / 'xml_offline'
PIT, FLOAT, STEP_MAX = 0.6, 1.2, 0.06
REF = json.load(open(M / 'site' / 'hole_grid.json'))                    # the in-game scan: same origin / step / size
X0, Y0 = REF['origin']; STEP = REF['step']; NY, NX = np.load(M / 'site' / 'hole_grid.npy').shape
MLO_ORIGIN = (2356.35, 3139.65, 49.20)                                  # move_shop.py O_DST, heading 0
JX, JY = 0.0137, 0.0171                                                 # hole_grid.py's ray offset (off the 0.5 m mesh lines: a ray
                                                                         # exactly on a shared edge slips through, in game and here)


def export(files, xmld=None):
    xmld = xmld or XMLD; ps = ','.join("'%s'" % str(f) for f in files)
    r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
                        f"& '{T / 'cw_xml.ps1'}' -OutDir '{xmld}' -Files @({ps})"], capture_output=True, text=True)
    if r.returncode: raise SystemExit('CodeWalker export failed: ' + r.stdout[-400:] + r.stderr[-400:])


def mat4(txt):
    v = [float(a) for a in txt.split()]; return np.array(v).reshape(4, 4)     # CodeWalker: row-vector matrix, translation in row 4


def tris_of(bounds_el, place):
    """every triangle (3 x 3 world points) of a Bounds element tree; place(points) maps file space to world."""
    out = []
    def walk(b, parent):
        m = parent
        ct = b.find('CompositeTransform')
        if ct is not None: m = mat4(ct.text) @ parent
        kids = b.find('Children')
        if kids is not None:
            for c in kids: walk(c, m)
        vs = b.find('Vertices')
        if vs is None or not (vs.text or '').strip(): return
        gc = b.find('GeometryCenter'); g = np.array([float(gc.get(k)) for k in 'xyz']) if gc is not None else np.zeros(3)
        V = np.array([[float(a) for a in ln.split(',')] for ln in vs.text.strip().splitlines()]) + g
        V = np.c_[V, np.ones(len(V))] @ m; V = place(V[:, :3])
        idx = [(int(t.get('v1')), int(t.get('v2')), int(t.get('v3'))) for t in b.iter('Triangle')]
        if idx: out.append(V[np.array(idx)])
    walk(bounds_el, np.eye(4))
    return np.concatenate(out) if out else np.zeros((0, 3, 3))


def placements():
    """drawable name -> list of (position, heading deg) from our ymaps (stored quaternion = conjugate of the heading)."""
    P = {}
    for f in (M / 'site' / 'xml' / 'jy_site.ymap.xml', M / 'xml' / 'jy_shop8_ext.ymap.xml'):
        for e in ET.parse(f).getroot().iter('Item'):
            a = e.findtext('archetypeName'); p = e.find('position'); q = e.find('rotation')
            if a is None or p is None: continue
            h = -2 * math.degrees(math.atan2(float(q.get('z')), float(q.get('w'))))
            P.setdefault(a.lower(), []).append((np.array([float(p.get(k)) for k in 'xyz']), h))
    return P


def load_all():
    files = sorted(STREAM.glob('*.ybn')) + [f for f in sorted(STREAM.glob('*.ydr'))]
    P = placements(); files = [f for f in files if f.suffix == '.ybn' or f.stem.lower() in P]
    export(files); allt = []
    for f in files:
        root = ET.parse(XMLD / (f.name + '.xml')).getroot()
        b = root if root.tag == 'Bounds' else root.find('.//Bounds')
        if b is None: continue
        if f.suffix == '.ybn':
            off = np.array(MLO_ORIGIN) if f.stem.lower() == 'jy_shop8_mlo' else np.zeros(3)
            allt.append(tris_of(b, lambda V, o=off: V + o))
        else:
            for pos, h in P[f.stem.lower()]:
                c, s = math.cos(math.radians(h)), math.sin(math.radians(h)); R = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])
                allt.append(tris_of(b, lambda V, pos=pos, R=R: V @ R + pos))
    return np.concatenate(allt)


def cast(Tr, x0=None, y0=None, nx=None, ny=None, step=None):
    """lowest up-facing hit per cell of the grid (default: the in-game scan's grid); -999 = nothing between z 30 and 60."""
    X0, Y0, NX, NY, STEP = (x0 if x0 is not None else globals()['X0']), (y0 if y0 is not None else globals()['Y0']), nx or globals()['NX'], ny or globals()['NY'], step or globals()['STEP']
    Z = np.full((NY, NX), -999.0)
    up = np.cross(Tr[:, 1] - Tr[:, 0], Tr[:, 2] - Tr[:, 0])[:, 2] > 0     # one-sided: a ray down only hits a face turned UP (counter-
    Tr = Tr[up]                                                          # clockwise from above). Checked on the in-game scan: up-only
    lo = Tr.min(axis=1); hi = Tr.max(axis=1)                             # matched 76/78 holes and all but 235 of 74,212 heights to 0.1 m;
                                                                         # both sides read a slab's underside under every floor
    keep = (hi[:, 2] > 30) & (lo[:, 2] < 60) & (hi[:, 0] >= X0 - 1) & (lo[:, 0] <= X0 + NX * STEP + 1) & (hi[:, 1] >= Y0 - 1) & (lo[:, 1] <= Y0 + NY * STEP + 1)
    for t in Tr[keep]:
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = t
        d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(d) < 1e-12: continue                                       # vertical: a straight-down ray never lands on it
        i0, i1 = max(0, int(math.ceil((min(ax, bx, cx) - X0 - JX) / STEP))), min(NX - 1, int(math.floor((max(ax, bx, cx) - X0 - JX) / STEP)))
        j0, j1 = max(0, int(math.ceil((min(ay, by, cy) - Y0 - JY) / STEP))), min(NY - 1, int(math.floor((max(ay, by, cy) - Y0 - JY) / STEP)))
        if i1 < i0 or j1 < j0: continue
        px, py = np.meshgrid(X0 + JX + np.arange(i0, i1 + 1) * STEP, Y0 + JY + np.arange(j0, j1 + 1) * STEP)
        l1 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / d; l2 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / d; l3 = 1 - l1 - l2
        e = -1e-6; ins = (l1 >= e) & (l2 >= e) & (l3 >= e)
        if not ins.any(): continue
        z = l1 * az + l2 * bz + l3 * cz; ok = ins & (z > 30) & (z < 60)
        sub = Z[j0:j1 + 1, i0:i1 + 1]; cur = np.where(sub == -999.0, np.inf, sub)
        Z[j0:j1 + 1, i0:i1 + 1] = np.where(ok & (z < cur), z, sub)
    return Z


def flags_of(Z):
    """hole_grid.py's rules, unchanged."""
    flags = []
    for j in range(NY):
        for i in range(NX):
            z = Z[j, i]; x, y = X0 + i * STEP, Y0 + j * STEP
            if z == -999.0: flags.append((x, y, 'hole', None)); continue
            nb = [Z[jj, ii] for jj in (j - 1, j, j + 1) for ii in (i - 1, i, i + 1) if (jj, ii) != (j, i) and 0 <= jj < NY and 0 <= ii < NX]
            nb = [v for v in nb if v != -999.0]
            if len(nb) >= 5 and all(z < v - PIT for v in nb): flags.append((x, y, 'pit', round(float(z), 2))); continue
            win = Z[max(0, j - 4):j + 5, max(0, i - 4):i + 5]; win = win[win != -999.0]
            if len(win) and z > win.min() + FLOAT: flags.append((x, y, 'floating', round(float(z), 2)))
    def zat(x, y):
        i, j = int(round((x - X0) / STEP)), int(round((y - Y0) / STEP))
        return Z[j, i] if 0 <= j < NY and 0 <= i < NX and Z[j, i] != -999.0 else None
    edges = []
    for ax0, ax1, ay0, ay1 in L.ASPH_RECTS:
        for side, pts in (('W', [(ax0, y) for y in np.arange(ay0, ay1, 1.0)]), ('E', [(ax1, y) for y in np.arange(ay0, ay1, 1.0)]),
                          ('S', [(x, ay0) for x in np.arange(ax0, ax1, 1.0)]), ('N', [(x, ay1) for x in np.arange(ax0, ax1, 1.0)])):
            dx, dy = {'W': (-1, 0), 'E': (1, 0), 'S': (0, -1), 'N': (0, 1)}[side]
            for x, y in pts:
                if any(r[0] < x + dx * 0.75 < r[1] and r[2] < y + dy * 0.75 < r[3] for r in L.ASPH_RECTS): continue
                zi, zo = zat(x - dx * 0.25, y - dy * 0.25), zat(x + dx * 0.75, y + dy * 0.75)
                if zi is not None and zo is not None and abs(zi - zo) > STEP_MAX: edges.append((round(x, 1), round(y, 1), side, round(float(zi - zo), 2)))
    return flags, edges


def clusters_of(flags):
    cl = []
    for f in flags:
        for c in cl:
            if c['kind'] == f[2] and any(abs(f[0] - p[0]) <= 1.0 and abs(f[1] - p[1]) <= 1.0 for p in c['cells']): c['cells'].append(f[:2]); break
        else: cl.append({'kind': f[2], 'cells': [f[:2]], 'z': f[3]})
    for c in cl:
        xs = [p[0] for p in c['cells']]; ys = [p[1] for p in c['cells']]
        c['box'] = [min(xs), max(xs), min(ys), max(ys)]; c['n'] = len(c['cells']); del c['cells']
    return cl


def main():
    Tr = load_all(); print('OFFLINE triangles', len(Tr), flush=True)
    Z = cast(Tr); np.save(M / 'site' / 'hole_grid_offline.npy', Z)
    flags, edges = flags_of(Z); cl = clusters_of(flags)
    json.dump({'origin': [X0, Y0], 'step': STEP, 'stream': str(STREAM), 'clusters': cl, 'asphalt_edge_steps': edges},
              open(M / 'site' / 'hole_grid_offline.json', 'w'), indent=1)
    if '--compare' in sys.argv:
        G = np.load(M / 'site' / 'hole_grid.npy'); seen = ~np.isnan(G)
        gh, oh = (G == -999.0) & seen, (Z == -999.0) & seen
        print('COMPARE in-game holes', int(gh.sum()), 'offline holes', int(oh.sum()), 'both', int((gh & oh).sum()),
              'game only', int((gh & ~oh).sum()), 'offline only', int((oh & ~gh).sum()))
        both = seen & ~gh & ~oh; dz = np.abs(G[both] - Z[both])
        print('COMPARE lowest-hit z where both hit: median |dz| %.3f, cells over 0.1 m: %d of %d' % (np.median(dz), int((dz > 0.1).sum()), both.sum()))
    print('OFFLINE_ASPHALT_EDGE', len(edges))
    for e in edges[:40]: print('  ', e)
    print('OFFLINE_HOLE_GRID', len(flags), 'flagged cells in', len(cl), 'clusters')
    for c in sorted(cl, key=lambda c: -c['n']):
        b = c['box']; print(f"  {c['kind']:8s} {c['n']:5d} cells  x {b[0]:.1f}..{b[1]:.1f}  y {b[2]:.1f}..{b[3]:.1f}" + (f"  z {c['z']}" if c['z'] else ''))


if __name__ == '__main__': main()
