"""Justice Center phase 2: the building shells (run inside Blender by p2_build.py). Everything comes from p2_plan: per face the stone
is the face rect minus openings minus covered rects (tc_kit.rects_minus), DEPTH m deep; each opening kind is built here:
  win / ribbon / punch : one glass pane in the opening's back plane + (shell floors) a dark box BACK m deep behind it (backing panel,
                         floor edge, ceiling strip, sides) so the dark glass never shows sky; mullions in front of the glass; a lit
                         window quad 4 cm in front of the backing in the building's _emi model when p2_plan.lit() picks the bay
  arcade               : the colonnade bay: open to the street, the lobby glass ARC_BACK m back (+ its backing box), granite soffit,
                         pier bodies between the bays, a granite floor at G, a downlight in the soffit (emissive, night)
  slot                 : Jail I's slot louvre: a sloped stone sill (the stepped frame), two dark blades, a dark box, NO glass
  vent                 : a black louvre band (blades every 0.15 m over a dark box)
  curtain              : the atrium's glass wall: one clear pane per bay, steel mullions + floor transoms, no backing
  garage               : a vehicle bay door opening (the door itself is phase 3): the bay room behind it (floor, walls, ceiling)
Fins (thin granite ribs, frame piers) stand proud of the stone. Roofs: Rockstar's roof recipe, inset where a parapet stands."""
import math
import tc_kit as TK
import p2_plan as PL
from p2_kit import fbox, fquad, quad, fdir, col_box, col_mesh, box_minus
GLASS = {'tower': 'glass_dark', 'police': 'glass_bronze', 'jail1': 'glass_bronze', 'jail2': 'glass_dark', 'atrium': 'glass_atrium'}
STONE = {'tower': 'granite', 'police': 'granite', 'jail1': 'granite', 'jail2': 'cream', 'atrium': 'granite'}
STATS = {}
def winbox(key, emi, face, s0, s1, z0, z1, D, glass, lit, mull=0.0, back=PL.BACK, see_out=False):
    """glass at d = -D, the dark box behind it (unless the floor is an MLO room: see_out), mullions every `mull` m."""
    fquad(key, face, [(s0, -D, z0), (s1, -D, z0), (s1, -D, z1), (s0, -D, z1)], glass, toward_d=1, name='glass')
    if mull:
        n = max(1, round((s1 - s0) / mull))
        for i in range(1, n):
            x = s0 + (s1 - s0) * i / n; fbox(key, face, x - 0.035, x + 0.035, -D + 0.006, -D + 0.07, z0, z1, 'metal')
    if see_out: return
    b = -D - back
    fquad(key, face, [(s0, b, z0), (s1, b, z0), (s1, b, z1), (s0, b, z1)], 'back', toward_d=1, name='back')
    fquad(key, face, [(s0, -D, z0), (s1, -D, z0), (s1, b, z0), (s0, b, z0)], 'back', toward=(0, 0, 1), name='back_f')
    fquad(key, face, [(s0, -D, z1), (s1, -D, z1), (s1, b, z1), (s0, b, z1)], 'back', toward=(0, 0, -1), name='back_c')
    fquad(key, face, [(s0, -D, z0), (s0, b, z0), (s0, b, z1), (s0, -D, z1)], 'back', toward=fdir(face, ds=1), name='back_s')
    fquad(key, face, [(s1, -D, z0), (s1, b, z0), (s1, b, z1), (s1, -D, z1)], 'back', toward=fdir(face, ds=-1), name='back_s')
    if lit:
        m = min(0.12, (s1 - s0) * 0.05); e = b + 0.04
        fquad(emi, face, [(s0 + m, e, z0 + 0.05), (s1 - m, e, z0 + 0.05), (s1 - m, e, z1 - 0.05), (s0 + m, e, z1 - 0.05)], 'win_emis', toward_d=1, name='emis')
        STATS['lit'] = STATS.get('lit', 0) + 1
def louvre(key, face, s0, s1, z0, z1, D, pitch, depth=0.5):
    """dark louvre blades every `pitch` m over a dark box (no glass)."""
    z = z0 + pitch / 2
    while z < z1 - 0.02:
        fbox(key, face, s0, s1, -D + 0.04, -D + 0.16, z - 0.018, z + 0.018, 'metal'); z += pitch
    b = -D - depth
    fquad(key, face, [(s0, b, z0), (s1, b, z0), (s1, b, z1), (s0, b, z1)], 'back', toward_d=1, name='lv_back')
    fquad(key, face, [(s0, -D, z0), (s1, -D, z0), (s1, b, z0), (s0, b, z0)], 'back', toward=(0, 0, 1), name='lv_f')
    fquad(key, face, [(s0, -D, z1), (s1, -D, z1), (s1, b, z1), (s0, b, z1)], 'back', toward=(0, 0, -1), name='lv_c')
    fquad(key, face, [(s0, -D, z0), (s0, b, z0), (s0, b, z1), (s0, -D, z1)], 'back', toward=fdir(face, ds=1), name='lv_s')
    fquad(key, face, [(s1, -D, z0), (s1, b, z0), (s1, b, z1), (s1, -D, z1)], 'back', toward=fdir(face, ds=-1), name='lv_s')
def building(k, emi):
    b = PL.B[k]; D = b['depth']; stone = STONE[k]; glass = GLASS[k]; see = PL.SEE_OUT[k]
    for face in PL.face_list(k):
        f, at, ax, s0, s1, o = face
        ops = PL.openings(k, face); cov = PL.covered(k, face)
        zbase = PL.SLAB - 0.35
        holes = [(a0, a1, zbase if kind in ('arcade', 'garage') else z0 - (0.25 if kind == 'slot' else 0.0), z1 + (0.25 if kind == 'garage' else 0.0)) for kind, a0, a1, z0, z1 in ops] + list(cov)
        holes += [(r[0][0], r[-1][1], zbase, PL.G) for r in PL.arcade_runs(k, face)]       # the colonnade floor runs under its piers
        for a0, a1, c0, c1 in TK.rects_minus(s0, s1, zbase, b['top'], holes): fbox(k, face, a0, a1, -D, 0.0, c0, c1, stone)
        arc = []
        for kind, a0, a1, z0, z1 in ops:
            lvl = PL.floor_of(k, z0); lit = (lvl not in see) and PL.lit(k, f, round(a0, 1), round(z0, 1))
            if kind in ('win', 'ribbon', 'punch'):
                winbox(k, emi, face, a0, a1, z0, z1, D, glass, lit, mull={'win': 1.6, 'ribbon': 1.5, 'punch': 0.0}[kind], see_out=lvl in see)
            elif kind == 'curtain':
                winbox(k, emi, face, a0, a1, z0, z1, D / 2, glass, False, see_out=True)
                first = not any(o_[0] == 'curtain' and abs(o_[2] - a0) < 1e-6 for o_ in ops); last = not any(o_[0] == 'curtain' and abs(o_[1] - a1) < 1e-6 for o_ in ops)
                if not last: fbox(k, face, a1 - 0.06, a1 + 0.06, -D, 0.05, z0, z1, 'metal')                    # mullion on the bay joint
                for lz in b['levels'][1:]: fbox(k, face, a0 + (0.0 if first else 0.06), a1 - (0.0 if last else 0.06), -D, 0.03, lz - 0.06, lz + 0.06, 'metal')   # transoms
            elif kind == 'slot':
                sill = z0 - 0.25
                for s_ in (a0, a1): pass
                V = [PL.P(face, a0, 0.0, sill), PL.P(face, a1, 0.0, sill), PL.P(face, a1, -D, z0), PL.P(face, a0, -D, z0), PL.P(face, a0, -D, sill), PL.P(face, a1, -D, sill)]
                TK.mesh(k, V, [(0, 1, 2, 3)] if _up(V[0], V[1], V[2]) else [(3, 2, 1, 0)], stone, False, 'sill')
                TK.mesh(k, V, [_wind(V, (0, 3, 4), fdir(face, ds=-1)), _wind(V, (1, 2, 5), fdir(face, ds=1))], stone, False, 'sill_end')
                louvre(k, face, a0, a1, z0, z1, D, 0.17)
            elif kind == 'vent':
                louvre(k, face, a0, a1, z0, z1, D, 0.15, 0.35)
            elif kind == 'arcade': arc.append((a0, a1, z0, z1))
            elif kind == 'garage': garage(k, face, a0, a1, z0, z1, D)
        if arc: arcade(k, emi, face, arc, D, glass, 1 in see)
        for a0, a1, z0, z1, pr in PL.fins(k, face): fbox(k, face, a0, a1, 0.0, pr, z0, z1, stone)
    roof(k)
    hull(k)
def _up(a, b, c):
    n = ((b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1]), (b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2]), (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
    return n[2] > 0
def _wind(V, idx, toward):
    a, b, c = (V[i] for i in idx)
    n = ((b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1]), (b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2]), (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
    return idx if sum(x * y for x, y in zip(n, toward)) > 0 else idx[::-1]
def arcade(k, emi, face, bays, D, glass, see_out):
    """the colonnade, per continuous run: one granite floor (G), one soffit, one glass wall ARC_BACK m back (+ its backing box), free
    standing piers PIER_DEPTH deep between the bays (a walk runs behind them), closed ends, a downlight per bay."""
    A = PL.ARC_BACK; PD = PL.PIER_DEPTH
    for run in PL.arcade_runs(k, face):
        r0, r1, z0, z1 = run[0][0], run[-1][1], run[0][2], run[0][3]
        fbox(k, face, r0, r1, -A, -D, z1, z1 + 0.45, STONE[k])                                       # soffit
        fbox(k, face, r0, r1, -A, 0.0, PL.G - 0.5, PL.G, 'granite')                                  # floor
        col_box(PL.P(face, r0, -A, PL.G - 0.5), PL.P(face, r1, 0.05, PL.G), 'stone')                 # 5 cm past the face: no seam with the ground outside
        winbox(k, emi, face, r0, r1, z0, z1, A, glass, False, mull=1.65, see_out=see_out)
        if z1 - z0 > 4:                                                                              # transom, between the mullions
            n = max(1, round((r1 - r0) / 1.65)); xs = [r0] + [r0 + (r1 - r0) * i / n for i in range(1, n)] + [r1]
            for i_, (x0, x1) in enumerate(zip(xs, xs[1:])):
                fbox(k, face, x0 + (0.035 if i_ else 0.0), x1 - (0.035 if i_ < n - 1 else 0.0), -A + 0.006, -A + 0.07, z0 + 3.0, z0 + 3.12, 'metal')
        for a0, a1, _, _ in run:
            c = (a0 + a1) / 2; zc = z1 - 0.06
            fquad(emi, face, [(c - 0.35, -A / 2 - 0.35, zc), (c + 0.35, -A / 2 - 0.35, zc), (c + 0.35, -A / 2 + 0.35, zc), (c - 0.35, -A / 2 + 0.35, zc)], 'soffit_emis', toward=(0, 0, -1), name='downlight')
        for (_, p1, _, _), (q0, _, _, _) in zip(run, run[1:]):                                       # the piers between the bays
            fbox(k, face, p1, q0, -PD, -D, PL.G, z1, STONE[k])
            col_box(PL.P(face, p1, -PD, PL.G - 0.5), PL.P(face, q0, 0.0, z1 + 0.45), 'stone')
        fbox(k, face, r0 - 0.5, r0, -A, -D, PL.G - 0.5, z1 + 0.45, STONE[k])                         # the run's closed ends
        fbox(k, face, r1, r1 + 0.5, -A, -D, PL.G - 0.5, z1 + 0.45, STONE[k])
def garage(k, face, a0, a1, z0, z1, D):
    """a vehicle bay behind its door opening: floor (flush with the street + 5 cm), walls, ceiling; collision for all of it."""
    gd = next(g for g in PL.GARAGES.values() if g['face'] == (k, face[0]))
    u0, u1, v0, v1 = gd['room']; t = 0.3; zc = gd['ceil']
    f, at, ax, *_ , o = face
    if ax == 'u':
        if o < 0: u0 = at + D
        else: u1 = at - D
    else:
        if o < 0: v0 = at + D
        else: v1 = at - D
    p_, q_ = PL.P(face, a0, -D, z0 - 0.3), PL.P(face, a1, 0.0, z0)                                    # the threshold: the floor under the door
    pieces = [((u0, v0, z0 - 0.3), (u1, v1, z0)), (tuple(map(min, p_, q_)), tuple(map(max, p_, q_))), ((u0, v0, zc), (u1, v1, zc + t))]
    if ax == 'u':
        far = u1 if o < 0 else u0
        pieces += [((u0, v0, z0), (u1, v0 + t, zc)), ((u0, v1 - t, z0), (u1, v1, zc)), ((far - t if o < 0 else far, v0 + t, z0), (far if o < 0 else far + t, v1 - t, zc))]
    else:
        far = v1 if o < 0 else v0
        pieces += [((u0, v0, z0), (u0 + t, v1, zc)), ((u1 - t, v0, z0), (u1, v1, zc)), ((u0 + t, far - t if o < 0 else far, z0), (u1 - t, far if o < 0 else far + t, zc))]
    for lo, hi in pieces: TK.box(k, lo, hi, 'conc', col=False); col_box(lo, hi, 'concrete')
    fbox(k, face, a0, a1, -D, 0.0, z1, z1 + 0.25, 'metal')                                          # the door head (steel)
def inset(k, r):
    """rect r of building k, pulled in by the stone depth on every face that is exposed at its roof (where a parapet stands)."""
    b = PL.B[k]; u0, u1, v0, v1 = r; lo = [u0, v0]; hi = [u1, v1]
    for face in PL.face_list(k):
        f, at, ax, s0, s1, o = face
        mid = ((s0 + s1) / 2)
        if PL.exposed_at(k, face, mid, b['roof'] + 0.2) and ((ax == 'u' and u0 - 0.01 <= at <= u1 + 0.01) or (ax == 'v' and v0 - 0.01 <= at <= v1 + 0.01)):
            i = 0 if ax == 'u' else 1
            if o > 0: hi[i] = min(hi[i], at - b['depth'])
            else: lo[i] = max(lo[i], at + b['depth'])
    return lo, hi
def atrium_pieces(t=None):
    """the atrium's L as rects that stop `t` (its stone depth) short of every outer side (internal splits of the L stay):
    the galleria floor, the glass roof and its beams all lie inside the parapet stone / the placeholder core walls."""
    t = PL.B['atrium']['depth'] if t is None else t; R = PL.rects('atrium'); out = []
    for i, (u0, u1, v0, v1) in enumerate(R):
        strips = []
        for ax, at, a0, a1, o in (('v', v1, u0, u1, 1), ('v', v0, u0, u1, -1), ('u', u1, v0, v1, 1), ('u', u0, v0, v1, -1)):
            segs = [(a0, a1)]
            for j, (p0, p1, q0, q1) in enumerate(R):
                if j == i: continue
                lo_, hi_ = (p0, p1) if ax == 'u' else (q0, q1); b0, b1 = (q0, q1) if ax == 'u' else (p0, p1)
                if (o > 0 and abs(lo_ - at) < 1e-6) or (o < 0 and abs(hi_ - at) < 1e-6):
                    segs = [x for s0, s1 in segs for x in ((s0, min(s1, b0)), (max(s0, b1), s1)) if x[1] - x[0] > 1e-6]
            for s0, s1 in segs:
                strips.append((at - t, at, s0, s1) if (ax == 'u' and o > 0) else (at, at + t, s0, s1) if ax == 'u' else (s0, s1, at - t, at) if o > 0 else (s0, s1, at, at + t))
        out += TK.rects_minus(u0, u1, v0, v1, strips)
    return out
def roof(k):
    b = PL.B[k]
    if k == 'atrium':
        for u0, u1, v0, v1 in atrium_pieces(): atrium_roof([u0, v0], [u1, v1], b['roof'])
        return
    for r in PL.rects(k):
        lo, hi = inset(k, r)
        TK.box(k, (lo[0], lo[1], b['roof'] - 0.4), (hi[0], hi[1], b['roof']), 'roof', col=False)
def atrium_roof(lo, hi, z):
    """the galleria's glass roof: one pane per 3 x 3 m bay over a steel grid (0.25 x 0.5 m beams)."""
    nu = max(1, round((hi[0] - lo[0]) / 3.0)); nv = max(1, round((hi[1] - lo[1]) / 3.0))
    us = [lo[0] + (hi[0] - lo[0]) * i / nu for i in range(nu + 1)]; vs = [lo[1] + (hi[1] - lo[1]) * i / nv for i in range(nv + 1)]
    for u0, u1 in zip(us, us[1:]):
        for v0, v1 in zip(vs, vs[1:]): quad('atrium', [(u0, v0, z), (u1, v0, z), (u1, v1, z), (u0, v1, z)], 'glass_atrium', (0, 0, 1), 'roofglass')
    for u in us[1:-1]: TK.box('atrium', (u - 0.125, lo[1], z - 0.5), (u + 0.125, hi[1], z - 0.035), 'metal', col=False)
    for v in vs[1:-1]:
        for u0, u1 in zip([lo[0]] + [u + 0.125 for u in us[1:-1]], [u - 0.125 for u in us[1:-1]] + [hi[0]]):
            TK.box('atrium', (u0, v - 0.125, z - 0.45), (u1, v + 0.125, z - 0.035), 'metal', col=False)
def hull(k):
    voids = PL.arcade_voids(k) + PL.mlo_voids(k)
    for gd in PL.GARAGES.values():
        if gd['face'][0] == k: u0, u1, v0, v1 = gd['room']; voids.append((u0 - 0.6, u1 + 0.6, v0 - 0.01, v1 + 0.01, PL.G - 1.5, gd['ceil'] + 0.3))
    for h in PL.hull(k):
        for c in box_minus(h, voids): col_box((c[0], c[2], c[4]), (c[1], c[3], c[5]), 'glass' if k == 'atrium' and c[5] <= PL.B[k]['roof'] + 0.01 else 'stone')
def bridges(key, emi):
    """the enclosed skybridges: stone bands top and bottom, a dark ribbon window on both long sides, ends run into the buildings."""
    for n, (u0, u1, v0, v1, z0, z1) in PL.BRIDGES.items():
        along_v = (v1 - v0) > (u1 - u0); e = PL.BRIDGE_DEPTH
        if along_v: v0e, v1e, u0e, u1e = v0 - e, v1 + e, u0, u1
        else: u0e, u1e, v0e, v1e = u0 - e, u1 + e, v0, v1
        TK.box(key, (u0e, v0e, z0), (u1e, v1e, z0 + 0.8), 'granite', col=False)
        TK.box(key, (u0e, v0e, z1 - 0.8), (u1e, v1e, z1), 'granite', col=False)
        col_box((u0e, v0e, z0), (u1e, v1e, z1), 'stone')
        sides = [('E', u1, 'u', v0, v1, 1), ('W', u0, 'u', v0, v1, -1)] if along_v else [('N', v1, 'v', u0, u1, 1), ('S', v0, 'v', u0, u1, -1)]
        for face in sides:
            f, at, ax, s0, s1, o = face; D = 0.2
            se0, se1 = (v0e, v1e) if along_v else (u0e, u1e)
            for a, b_ in ((se0, s0), (s1, se1)): fbox(key, face, a, b_, -(u1 - u0 if along_v else v1 - v0) / 2, 0.0, z0 + 0.8, z1 - 0.8, 'granite')   # ends inside the buildings
            fbox(key, face, s0, s1, -D, 0.0, z0 + 0.8, z0 + 0.95, 'granite'); fbox(key, face, s0, s1, -D, 0.0, z1 - 0.95, z1 - 0.8, 'granite')
            winbox(key, emi, face, s0, s1, z0 + 0.95, z1 - 0.95, D, 'glass_dark', PL.lit(n, f), mull=1.5, back=0.9)
