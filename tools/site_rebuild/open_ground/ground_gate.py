"""The site's ground gate, offline on the BUILT files (the playbook's hole_grid_offline / seen_vs_solid / crack_check ideas, doc 07):
everything is read back from the assembled stream folder through CodeWalker XML, never from our own tables.
Collision = every static collision file the game loads here: our edited copy where the resource ships one, Rockstar's otherwise.
Drawn = our ground tiles (bb_ground_*, at their ymap positions) and the vanilla ground models we lowered (terrain.py).
On a 0.5 m grid over the site (rays off the grid lines):
  COL_HOLE       no collision under a cell, also for a second ray 4 cm off it   -> must be 0 (a lone ray that slips down the exact
                 seam between two of Rockstar's collision files is not a hole: the game's collision margin closes it)
  COL_GRADE      collision off the planned grade by more than 6 cm (the collision is a 2 m grid of plane pieces, the grade a smooth
                 field: round the arch feet's cones they part by up to ~5 cm)  -> must be 0
  PAD_FLAT       under the club + apron, collision off PAD_Z by more than 5 mm -> must be 0
  PAD_HIGH       under the club + apron, collision higher than the floor top - 5 cm (natural ground through the floor) -> 0
  DRAWN_FLOAT    our ground more than 8 cm over the collision, or more than 3 cm under it (it is lifted 2 cm) -> must be 0
  TERRAIN_SHOWS  a lowered vanilla ground face above our ground (0.3 m inside the outline) -> must be 0
  EDGE_STEP      along the outline, collision just inside vs just outside differs by more than 0.15 m -> must be 0
Run: py -3 ground_gate.py      prints GROUND_GATE_PASS (+ counts) or GROUND_GATE_FAIL with the worst cells; ../site/ground_gate.json"""
import json, re, sys
import numpy as np
from pathlib import Path
T = Path(__file__).resolve().parent; sys.path.insert(0, str(T))
import ground_scan as GS, grade as GR, site_plan as SP
import shapely
from shapely.geometry import Polygon
M = T.parent; ST = M / 'resource' / 'blockboyz_truckclub' / 'stream'; XG = M / 'site' / 'xml_gate'
STEP = 0.5
TOL = dict(grade=0.06, pad=0.05, pad_flat=0.005, drawn_hi=0.08, drawn_lo=-0.03, edge=0.15)


def ydr_tris(xml_path, origin):
    """the high-LOD triangles of a drawable's CodeWalker XML, moved to its (identity-rotated) placement."""
    s = Path(xml_path).read_text(encoding='utf-8'); hi = s.split('<DrawableModelsMedium')[0]
    out = []
    for g in re.finditer(r'<VertexBuffer>.*?<Data2?>(.*?)</Data2?>.*?<IndexBuffer>\s*<Data>(.*?)</Data>', hi, re.S):
        V = np.array([[float(q) for q in ln.split()[:3]] for ln in g.group(1).strip().splitlines()]) + np.array(origin)
        I = np.array([int(q) for q in g.group(2).split()]).reshape(-1, 3); out.append(V[I])
    return np.concatenate(out) if out else np.zeros((0, 3, 3))


def main():
    XG.mkdir(parents=True, exist_ok=True)
    for f in XG.glob('*'): f.unlink()
    van = sorted((M / 'vanilla').glob('*.ybn')); edited = [ST / f.name for f in van if (ST / f.name).exists()]
    assert edited, 'no edited collision in the stream (run assemble.py)'
    models = [l.split('\t') for l in (M / 'vanilla' / 'models.tsv').read_text().splitlines()]
    terr = [(ST / f'{a}.ydr', (float(x), float(y), float(z))) for a, k, x, y, z in models if k == 'terrain' and (ST / f'{a}.ydr').exists()]
    gi = json.load(open(M / 'site' / 'ground' / 'ground_info.json'))
    tiles = [(ST / f'{n}.ydr', v['origin']) for n, v in gi.items()]
    GS.export(edited + [p for p, _ in terr] + [p for p, _ in tiles], XG)
    col = [GS.tris_of(GS.bounds_of((XG if (ST / f.name).exists() else M / 'site' / 'xml_vanilla') / (f.name + '.xml'))) for f in van]
    col = np.concatenate(col)
    xs = [p[0] for p in SP.SITE]; ys = [p[1] for p in SP.SITE]
    x0, y0 = np.floor(min(xs)) - 2, np.floor(min(ys)) - 2; nx, ny = int((max(xs) - x0 + 2) / STEP), int((max(ys) - y0 + 2) / STEP)
    low = GS.cast(col, x0, y0, nx, ny, STEP); low2 = GS.cast(col, x0 + 0.031, y0 + 0.027, nx, ny, STEP); top = GS.cast(col, x0, y0, nx, ny, STEP, lowest=False)
    drawn = GS.cast(np.concatenate([ydr_tris(XG / (p.name + '.xml'), o) for p, o in tiles]), x0, y0, nx, ny, STEP)
    tz = GS.cast(np.concatenate([ydr_tris(XG / (p.name + '.xml'), o) for p, o in terr]), x0, y0, nx, ny, STEP, lowest=False)
    cx = x0 + STEP / 2 + GS.JX + np.arange(nx) * STEP; cy = y0 + STEP / 2 + GS.JY + np.arange(ny) * STEP
    X, Y = np.meshgrid(cx, cy); S = Polygon(SP.SITE)
    on = shapely.contains_xy(S, X, Y); deep = shapely.contains_xy(S.buffer(-0.3), X, Y)
    pad = np.zeros_like(on)
    for p in SP.derived()['pad']: pad |= shapely.contains_xy(Polygon(p), X, Y)
    G = np.vectorize(GR.grade_z)(X, Y)
    wall = Polygon([SP.W(p)[:2] for p in __import__('concept_v3').outline(192)]).buffer(-0.6)
    under_club = shapely.contains_xy(wall, X, Y)
    fails = {}
    def flag(name, mask, val):
        idx = np.argwhere(mask)
        fails[name] = {'cells': int(mask.sum()), 'worst': [[round(float(X[j, i]), 2), round(float(Y[j, i]), 2), round(float(val[j, i]), 3)]
                                                          for j, i in idx[np.argsort(-np.abs(val[mask]))][:5]] if mask.any() else []}
    flag('COL_HOLE', on & np.isnan(low) & np.isnan(low2), np.zeros_like(X))
    seams = int((on & (np.isnan(low) ^ np.isnan(low2))).sum())
    flag('COL_GRADE', deep & ~np.isnan(low) & (np.abs(low - G) > TOL['grade']), low - G)
    flag('PAD_FLAT', pad & ~np.isnan(low) & (np.abs(low - SP.PAD_Z) > TOL['pad_flat']), low - SP.PAD_Z)
    flag('PAD_HIGH', pad & ~np.isnan(top) & (top > SP.FLOOR_TOP - TOL['pad']), top - SP.FLOOR_TOP)
    dd = drawn - low
    flag('DRAWN_FLOAT', deep & ~under_club & (np.isnan(drawn) | (dd > TOL['drawn_hi']) | (dd < TOL['drawn_lo'])), np.nan_to_num(dd, nan=-9))
    flag('TERRAIN_SHOWS', deep & ~np.isnan(tz) & ~np.isnan(drawn) & (tz > drawn - 0.005), tz - drawn)
    # the outline: collision 0.25 m inside vs 0.25 m outside, every 0.5 m
    bd = S.exterior; steps = []
    for d in np.arange(0, bd.length, STEP):
        p = bd.interpolate(d); q = bd.interpolate(min(d + 0.05, bd.length)); t = np.array([q.x - p.x, q.y - p.y]); t /= np.linalg.norm(t) + 1e-12
        n_in = np.array([-t[1], t[0]])                                       # (counter-clockwise outline: left = inside)
        a = np.array([p.x, p.y]) + n_in * 0.25; b = np.array([p.x, p.y]) - n_in * 0.25
        ia, ja = int((a[0] - x0) / STEP), int((a[1] - y0) / STEP); ib, jb = int((b[0] - x0) / STEP), int((b[1] - y0) / STEP)
        za, zb = low[ja, ia], low[jb, ib]
        if not (np.isnan(za) or np.isnan(zb)) and abs(za - zb) > TOL['edge']: steps.append([round(p.x, 2), round(p.y, 2), round(float(za - zb), 3)])
    fails['EDGE_STEP'] = {'cells': len(steps), 'worst': sorted(steps, key=lambda s: -abs(s[2]))[:5]}
    stats = {'cells_on_site': int(on.sum()), 'pad_collision_top_max': round(float(np.nanmax(np.where(pad, top, np.nan))), 3),
             'floor_top': SP.FLOOR_TOP, 'seam_rays': seams, 'drawn_minus_col_median': round(float(np.nanmedian(np.where(deep & ~under_club, dd, np.nan))), 3)}
    json.dump({'fails': fails, 'stats': stats}, open(M / 'site' / 'ground_gate.json', 'w'), indent=1)
    bad = {k: v for k, v in fails.items() if v['cells']}
    print(('GROUND_GATE_FAIL ' if bad else 'GROUND_GATE_PASS ') + json.dumps({'stats': stats, 'fails': bad or {k: 0 for k in fails}}))
    if bad: sys.exit(1)


if __name__ == '__main__': main()
