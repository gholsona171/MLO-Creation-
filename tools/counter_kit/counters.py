#!/usr/bin/env python3
"""
c9_dj counter kit (Antonio, Oct 25 2026: "actual restaurant bar counters ... full size ones like they are, then custom versions where
it's cut so I can attach them together myself"). Built from ROCKSTAR's own counters: their geometry, shaders and textures, cut into
modules that snap edge to edge (shared/barsnap.lua), plus full-size copies of interior-only counters (those cannot be spawned by a
script in GTA: their archetypes live in an interior's ytyp; our copies can, with our own collision).

    python prop/build/counters.py --export   # once: the Rockstar drawables + textures from the game (Windows, CodeWalker) -> out/rsx/
    python prop/build/counters.py            # everything (counters_out.py writes the files)

Module frame (every module of a SET shares it): the run goes along +X, the PATRON side is -Y (GTA's front), the staff side +Y; the
BACK edge of the top (staff side) is y = 0 before the pivot shift, the top's front edge y = -D; z = 0 is the floor, the top is at H.
Pivot: the centre of the module's footprint on the floor (a corner: the centre of its D x D square). Joints: the point on the floor
under the back edge of each open face, and the out-heading of that face (barsnap). The sets: counters_sets.py.
Collision is built by the SAME recipe as the drawable: each profile box of a set is a little mesh run through the same cuts, turns
and mitres, then boxed (so a corner's collision follows its two legs). MIT, our own code. The Rockstar files it reads stay in out/rsx/.
"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rsx

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, 'out')
RSX = os.path.join(OUT, 'rsx')                 # x/<name>.ydr.xml + tex/<name>.dds (from the game, never committed)
PREFIX = 'c9dj_ctr_'


# ── the run of a set ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def source(name):
    return rsx.read(os.path.join(RSX, 'x', name + '.ydr.xml'))


def run_frame(s, m=None):
    """the set's source, straightened and turned into the module frame (run along +X, patron -Y, back edge y = 0, floor z = 0).
    Returns (model, the 4x4 transform used) so collision and copies can follow the same move."""
    m = m or source(s['src'])
    R = rsx.rot_z(s['rot'])
    t1 = np.array([-s['x0'], 0.0, 0.0])
    m1 = rsx.transform(rsx.transform(m, R), None, t1)
    sec = rsx.section_points(rsx.section(m1, 0, s['probe']))
    top = sec[sec[:, 2] > sec[:, 2].max() - 0.08]
    zmin = min(g.pos[:, 2].min() for g in m1.geos)
    t2 = np.array([0.0, -top[:, 1].max(), -zmin])
    M = np.eye(4); M[:3, :3] = R; M[:3, 3] = t1 + t2
    return rsx.transform(m1, None, t2), M


def box_mesh(boxes, x0, x1):
    """collision boxes (y0, y1, z0, z1) as a model whose geometry i is box i, spanning x0..x1 (cut like the drawable)"""
    geos = []
    for i, (y0, y1, z0, z1) in enumerate(boxes):
        P = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], float)
        T = np.array([[0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5], [0, 4, 5], [0, 5, 1], [2, 3, 7], [2, 7, 6], [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]])
        geos.append(rsx.Geo(i, ['Position'], {'Position': P}, T))
    return rsx.Model('boxes', 'boxes', geos, {})


def auto_boxes(m, cell=0.05, band=(0.10, 0.60), slab=0.06):
    """collision for a full-size copy whose drawable came without any (an interior's own piece): a 5 cm grid over the footprint;
    a cell with an upward surface above 0.6 m gets the top (a slab `slab` thick under that surface); a cell where anything of the
    drawable passes through the knee band (the front panel, a pedestal, a cabinet) is solid from the floor to its top. Runs of
    equal cells are merged into boxes. Floor at z = 0."""
    P = [(g.pos, g.tris) for g in m.geos]
    allp = np.vstack([p for p, _ in P])
    x0, y0 = allp[:, 0].min(), allp[:, 1].min()
    nx = int(np.ceil((allp[:, 0].max() - x0) / cell)) + 1
    ny = int(np.ceil((allp[:, 1].max() - y0) / cell)) + 1
    top = np.full((nx, ny), -1.0)
    body = np.zeros((nx, ny), bool)
    for pos, tris in P:
        for t in tris:
            a, b, c = pos[t]
            n = np.cross(b - a, c - a)
            ln = np.linalg.norm(n)
            if ln < 1e-12: continue
            k = max(2, int(np.ceil(max(np.linalg.norm(b - a), np.linalg.norm(c - a), np.linalg.norm(c - b)) / (cell / 2))))
            u, v = np.meshgrid(np.arange(k + 1), np.arange(k + 1))
            keep = (u + v) <= k
            u, v = u[keep] / k, v[keep] / k
            S = a[None] + u[:, None] * (b - a)[None] + v[:, None] * (c - a)[None]
            ix = np.clip(((S[:, 0] - x0) / cell).astype(int), 0, nx - 1)
            iy = np.clip(((S[:, 1] - y0) / cell).astype(int), 0, ny - 1)
            if abs(n[2]) / ln > 0.7:
                np.maximum.at(top, (ix, iy), S[:, 2])
            inb = (S[:, 2] > band[0]) & (S[:, 2] < band[1])
            body[ix[inb], iy[inb]] = True
    kind = np.zeros((nx, ny), int)           # 0 none, 1 slab, 2 solid
    kind[top >= 0.6] = 1
    kind[(top >= 0.6) & body] = 2
    q = np.round(top / 0.06) * 0.06            # tops within ~6 cm merge (the box takes the highest)
    boxes, used = [], np.zeros((nx, ny), bool)
    for i in range(nx):
        for j in range(ny):
            if used[i, j] or kind[i, j] == 0: continue
            same = lambda a, b: not used[a, b] and kind[a, b] == kind[i, j] and q[a, b] == q[i, j]
            j2 = j
            while j2 + 1 < ny and same(i, j2 + 1): j2 += 1
            i2 = i
            while i2 + 1 < nx and all(same(i2 + 1, jj) for jj in range(j, j2 + 1)): i2 += 1
            used[i:i2 + 1, j:j2 + 1] = True
            zt = float(top[i:i2 + 1, j:j2 + 1].max())
            z0 = 0.0 if kind[i, j] == 2 else zt - slab
            boxes.append(((x0 + i * cell, y0 + j * cell, z0), (x0 + (i2 + 1) * cell, y0 + (j2 + 1) * cell, zt)))
    lo, hi = allp.min(0), allp.max(0)                  # never past the drawable (the grid overshoots by up to a cell)
    return [((max(a[0], lo[0]), max(a[1], lo[1]), a[2]), (min(b[0], hi[0]), min(b[1], hi[1]), b[2])) for a, b in boxes]


def aabbs(m):
    return [(tuple(g.pos.min(0)), tuple(g.pos.max(0))) for g in m.geos if len(g.tris)]


# ── recipes (each works on the drawable AND on the box mesh) ─────────────────────────────────────────────────────────────────
_CANON = None      # the set's joint outline (segments in y, z): set by build_set while a set is built


def weld(m, x, canon, reach=0.008):
    """every vertex ON the cut plane x moved onto the nearest point of the set's canonical joint outline (when within `reach`): a
    rounded trim's facets cross a cut at slightly different spots along the run (up to 4 mm on the nightclub bars' trims), so every
    joint face is pulled onto ONE outline and any two faces meet exactly"""
    a, b = canon[:, 0, 1:], canon[:, 1, 1:]
    ab = b - a
    L2 = np.maximum((ab ** 2).sum(1), 1e-12)
    corners = np.vstack([a, b])
    for g in m.geos:
        P = g.data['Position']
        on = np.where(np.abs(P[:, 0] - x) < 1e-5)[0]
        for i in on:
            p = P[i, 1:]
            dv = np.linalg.norm(corners - p, axis=1)
            k = int(np.argmin(dv))
            if dv[k] <= 0.006:                     # onto the outline's own vertex (a facet corner)
                P[i, 1:] = corners[k]
                continue
            t = np.clip(((p - a) * ab).sum(1) / L2, 0, 1)
            q = a + t[:, None] * ab
            d = np.linalg.norm(q - p, axis=1)
            k = int(np.argmin(d))
            if d[k] <= reach: P[i, 1:] = q[k]
    return m


def slab(m, x0, x1, lo=True, hi=True):
    """the stretch x0..x1 of the run, moved to start at x = 0 (its cut faces welded onto the set's joint outline)"""
    out = rsx.transform(rsx.box_clip(m, (x0, None, None), (x1, None, None)), None, (-x0, 0, 0))
    if _CANON is not None and m.shaders_xml != 'boxes':
        if lo: weld(out, 0.0, _CANON)
        if hi: weld(out, x1 - x0, _CANON)
    return out


def extras(run, s, kind, L):
    """pieces copied from elsewhere on the run into a module (a steel table's legs, a waterfall end panel): s['extras'] =
    [(kinds, (x0, y0, z0), (x1, y1, z1), lambda L, D: (dx, dy))]: that box of the run, moved by (dx, dy). Drawables only."""
    if run.shaders_xml == 'boxes': return []
    out = []
    for kinds, lo, hi, at in s.get('extras', ()):
        if kind in kinds:
            dx, dy = at(L, s['D'])
            out.append(rsx.transform(rsx.box_clip(run, lo, hi), None, (dx, dy, 0)))
    return out


def straight(run, a, L):
    return slab(run, a, a + L)


def corner_out(run, a, D):
    """outside corner (turns towards the staff side; the patron is outside the L): two slices mitred on the diagonal"""
    A = rsx.clip(slab(run, a, a + D), (1, 1, 0), 0.0)                                         # keeps x + y <= 0
    B = rsx.transform(rsx.transform(slab(run, a, a + D), None, (-D, 0, 0)), rsx.rot_z(90))    # runs +Y, front faces +X
    B = rsx.clip(B, (-1, -1, 0), 0.0)                                                         # keeps x + y >= 0
    return rsx.merge([p for p in (A, B) if p.geos], 'oc')


def corner_in(run, a, D):
    """inside corner (turns towards the patron side; the patron is inside the L)"""
    A = rsx.clip(slab(run, a, a + D), (1, -1, 0), D)                                          # keeps x - y <= D
    B = rsx.transform(rsx.transform(slab(run, a, a + D), rsx.rot_z(-90)), None, (D, 0, 0))    # runs -Y, front faces -X, back edge x = D
    B = rsx.clip(B, (-1, 1, 0), -D)                                                           # keeps x - y >= D
    return rsx.merge([p for p in (A, B) if p.geos], 'ic')


def end_band(run, a, e, D, w):
    """a LEFT end made from the run itself (where Rockstar's end is open against a wall): a stretch e long, closed at x = 0 by the
    run's own profile turned to face -X (its front band, w deep: the top's edge + the front panel), picture-frame mitred"""
    A = slab(run, a, a + e)
    B = rsx.transform(rsx.transform(slab(run, a, a + D), rsx.rot_z(-90)), None, (D, 0, 0))
    B = rsx.box_clip(B, (None, None, None), (w, None, None))
    A1 = rsx.box_clip(A, (w, None, None), (None, None, None))
    A2 = rsx.box_clip(A, (None, None, None), (w, None, None))
    lo, hi = (None, None, None), (None, -D / 2, None)
    parts = [A1,
             rsx.clip(rsx.box_clip(A2, (None,) * 3, (None, -D / 2, None)), (-1, 1, 0), -D),      # front corner: A keeps x >= y + D
             rsx.clip(rsx.box_clip(A2, (None, -D / 2, None), (None,) * 3), (-1, -1, 0), 0.0),     # back corner: A keeps x >= -y
             rsx.clip(rsx.box_clip(B, (None,) * 3, (None, -D / 2, None)), (1, -1, 0), D),         # B keeps x <= y + D
             rsx.clip(rsx.box_clip(B, (None, -D / 2, None), (None,) * 3), (1, 1, 0), 0.0)]        # B keeps x <= -y
    return rsx.merge([p for p in parts if p.geos], 'el')


def make_end(run, s, end, left):
    """an end piece: ('band', a, e, w) | ('native', a, b): the source's own closed end (at a for a left end, at b for a right one) |
    ('compose', e, [(x0, x1, at), ...]): stretches of the run put together (only the face at the joint is welded)"""
    if end[0] == 'band': return end_band(run, end[1], end[2], s['D'], end[3])
    if end[0] == 'native': return slab(run, end[1], end[2], lo=not left, hi=left)
    if end[0] == 'pedestal':                      # ('pedestal', frame, a, b, (x0, x1) of its solid block): Rockstar's own closed
        _, fr, a, b, blk = end                    # block end from another part of the source (the run butts into its side panel)
        if run.shaders_xml == 'boxes':
            e = b - a
            solid = box_mesh([(-s['D'], 0.0, 0.0, s['H_body'])], blk[0], blk[1])
            return rsx.merge([slab(run, 0.0, e), solid], 'end')
        other, _ = run_frame(dict(s, **fr))
        return slab(other, a, b, lo=False, hi=True)
    e, parts = end[1], []
    for x0, x1, at in end[2]:
        p = slab(run, x0, x1, lo=(at == 0.0 and not left), hi=(abs(at + x1 - x0 - e) < 1e-6 and left))
        parts.append(rsx.transform(p, None, (at, 0, 0)))
    return rsx.merge([p for p in parts if p.geos], 'end')


def end_len(end):
    return {'band': lambda: end[2], 'native': lambda: end[2] - end[1], 'compose': lambda: end[1], 'pedestal': lambda: end[3] - end[2]}[end[0]]()


def build_piece(run, s, kind, L):
    D = s['D']
    if kind == 'straight': m = straight(run, s['straights'][L], L)
    elif kind == 'oc': m = corner_out(run, s['corner'], D)
    elif kind == 'ic': m = corner_in(run, s['corner'], D)
    elif kind == 'el': m = make_end(run, s, s['end'], True)
    elif 'end_r' in s: m = make_end(run, s, s['end_r'], False)
    else: m = rsx.mirror_x(make_end(run, s, s['end'], True), end_len(s['end']) / 2)
    ex = extras(run, s, kind, L)
    return rsx.merge([m] + ex, kind) if ex else m


def pieces(s):
    """[(suffix, kind, L)] of a set"""
    out = [('s%03d' % round(L * 100), 'straight', L) for L in sorted(s['straights'])]
    out += [('oc', 'oc', s['D']), ('ic', 'ic', s['D']), ('el', 'el', end_len(s['end'])), ('er', 'er', end_len(s.get('end_r', s['end'])))]
    return out


def pivot_and_joints(kind, L, D):
    """(the pivot in the module frame, joints relative to the pivot as (x, y, out-heading, hand)): hand 1 = a RIGHT face (looking
    out of it, the back edge is on the left), -1 = a LEFT face; only a left face and a right face can meet"""
    if kind == 'straight': p, j = (L / 2, -D / 2), [(0, 0, 90.0, -1), (L, 0, 270.0, 1)]
    elif kind == 'oc': p, j = (D / 2, -D / 2), [(0, 0, 90.0, -1), (0, 0, 0.0, 1)]
    elif kind == 'ic': p, j = (D / 2, -D / 2), [(0, 0, 90.0, -1), (D, -D, 180.0, 1)]
    elif kind == 'el': p, j = (L / 2, -D / 2), [(L, 0, 270.0, 1)]
    else: p, j = (L / 2, -D / 2), [(0, 0, 90.0, -1)]
    return p, [(round(x - p[0], 4), round(y - p[1], 4), h, t) for x, y, h, t in j]


# ── the joint check ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def faces(m, kind, L, D, inset=0.0):
    """each open face of a module, moved so it lies on x = 0 of a run going +X: [('left' | 'right', outline segments)] (a corner's
    other leg touches that plane along the mitre's edge only: joint_report leaves that line out)"""
    out = []
    if kind in ('straight', 'er', 'oc', 'ic'): out.append(('left', rsx.section(m, 0, inset)))
    if kind in ('straight', 'el'): out.append(('right', rsx.section(m, 0, L - inset)))
    if kind == 'oc':
        out.append(('right', rsx.section(rsx.transform(m, rsx.rot_z(-90)), 0, -inset)))
    if kind == 'ic':
        out.append(('right', rsx.section(rsx.transform(rsx.transform(m, rsx.rot_z(90)), None, (-D, -D, 0)), 0, -inset)))
    return out


def joint_report(mods, s):
    """the worst gap (metres) between each module's open faces and the straight's: 0 = the same outline (seamless)"""
    D = s['D']
    L0 = min(s['straights'])
    ref = mods['s%03d' % round(L0 * 100)]['frame']
    refs = {'left': rsx.section(ref, 0, 0.0), 'right': rsx.section(ref, 0, L0)}
    rep = {}
    for k, v in mods.items():
        skip = (1, 0.0 if v['kind'] == 'oc' else -D, 0.012) if v['kind'] in ('oc', 'ic') else None   # the mitre's own edge
        fs = faces(v['frame'], v['kind'], v['L'], D)
        rf = refs
        if v['kind'] in ('el', 'er') and s['end'][0] == 'pedestal':      # the run butts into the block: only the top must match
            zc = s['H_body']
            top = lambda S: S[(S[:, 0, 2] >= zc) & (S[:, 1, 2] >= zc)]
            fs = [(side, top(sec)) for side, sec in fs]
            rf = {k: top(v2) for k, v2 in refs.items()}
        gaps = [rsx.section_gap(sec, rf[side], 0, skip=skip) for side, sec in fs]
        rep[k] = round(max(gaps), 4) if gaps else 0.0
    return rep


def build_set(key, s):
    """{suffix: {frame (module frame model), model (pivot frame), boxes (pivot frame), kind, L, joints, pivot}}"""
    global _CANON
    run, M = run_frame(s)
    _CANON = None
    _CANON = rsx.section(run, 0, s.get('canon', s['probe']))
    zmax = max(g.pos[:, 2].max() for g in run.geos)
    lo = min(g.pos[:, 0].min() for g in run.geos) - 1
    hi = max(g.pos[:, 0].max() for g in run.geos) + 1
    bm = box_mesh(s['boxes'], lo, hi)
    out = {}
    for suf, kind, L in pieces(s):
        frame = build_piece(run, s, kind, L)
        bx = build_piece(bm, s, kind, L)
        p, joints = pivot_and_joints(kind, L, s['D'])
        sh = (-p[0], -p[1], 0.0)
        out[suf] = dict(frame=frame, model=rsx.transform(frame, None, sh), boxes=aabbs(rsx.transform(bx, None, sh)), kind=kind, L=L,
                        joints=joints, pivot=p, H=round(float(zmax), 4))
    return out
