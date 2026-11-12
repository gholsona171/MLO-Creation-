"""Wall finish shells (Blender; used by the police HQ (jc3_police_build) and area 5 (jc3_tower_build)): skirting, wainscot, rails,
tile, cornices built as SOLID SHELLS round the walls, never as boards laid on wall faces or as per-wall bands.

Why (2026-11-11, Antonio on the police side: "walls not connected, weird lips, didn't texture everything properly"): boards laid on
faces after the fact skipped short faces, stopped dead at convex corners (lips), and per-wall banded linings / free partitions crossed
each other at T-junctions (coplanar faces: z-fighting). The shell is computed from the walls' footprints instead:
  core   every wall a room draws (lining strips, partitions) is recorded as a 2D footprint (record)
  grid   per floor rect of the room, the plan is cut on every core edge and every edge +- each band depth; each cell knows its square
         (Chebyshev) distance to the core and the wall it fronts (axis, side)
  bands  bands_at(room, u, v, axis, side, F, H) says which bands that wall carries [(material, z0, z1, depth)]; a cell gets a band where
         it is nearer the core than the band is deep: a band follows the wall round every convex corner (partition ends, returns) and
         meets itself in every concave one - one continuous shell, no ends showing, nothing overlapping
  holes  doors, windows (holes), and every solid box already standing in the shell's way (counters, casings, kit, built-ins,
         pilasters: TK.SOLIDS) plus keep_clear boxes (meshes) are cut out of the bands (3D), so a band stops on their sides
The cells never overlap in plan and one wall's bands never overlap in height: no two faces share a plane and a facing."""
import numpy as np
import tc_kit as TK
import jc3_tower_build as TB
CORE = {}                                                                # room -> [(u0, u1, v0, v1, z0, z1)] the walls' footprints
HOLES = {}                                                               # room -> extra 3D boxes the bands keep clear of (casings, kit, counters)
def record(room, rects, z0, z1):
    CORE.setdefault(room, []).extend((r[0], r[1], r[2], r[3], z0, z1) for r in rects if r[1] - r[0] > 1e-4 and r[3] - r[2] > 1e-4)
def keep_clear(room, lo, hi): HOLES.setdefault(room, []).append((lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
def _deep_holes(holes, d=0.08):
    """the openings as the bands see them: every hole box stretched across its wall by d both ways (a window's box is only the lining's
    depth; the bands stand in front of that)."""
    out = []
    for h in holes:
        if h[1] - h[0] <= h[3] - h[2]: out.append((h[0] - d, h[1] + d, *h[2:]))
        else: out.append((h[0], h[1], h[2] - d, h[3] + d, h[4], h[5]))
    return out
def build(rooms, holes, bands_at, depths):
    """rooms: room -> (floor z, region rects, shell height); bands_at: see above; depths: every band depth bands_at can return.
    Lays every room's shell; returns {room: boxes laid}."""
    laid = {}
    depths = sorted(set(depths)); D = max(depths)
    SOL = np.array([lo + hi for lo, hi in TK.SOLIDS], np.float64).reshape(-1, 6)     # what stands there before the shell
    for room, (F, region, H) in rooms.items():
        core = [c for c in CORE.get(room, []) if c[4] < F + 0.5 and c[5] > F + 1.0]
        if not core: continue
        C = np.array([c[:4] for c in core], np.float64)
        cut = _deep_holes(holes) + HOLES.get(room, [])
        n = 0
        for r in region:
            u0, u1, v0, v1 = r
            near = C[(C[:, 0] < u1 + D) & (C[:, 1] > u0 - D) & (C[:, 2] < v1 + D) & (C[:, 3] > v0 - D)]
            if not len(near): continue
            xs = sorted({u0, u1} | {x for c in near for e in (c[0], c[1]) for d in [0.0] + depths for x in (e - d, e + d) if u0 < x < u1})
            ys = sorted({v0, v1} | {y for c in near for e in (c[2], c[3]) for d in [0.0] + depths for y in (e - d, e + d) if v0 < y < v1})
            X0, X1 = np.array(xs[:-1]), np.array(xs[1:]); Y0, Y1 = np.array(ys[:-1]), np.array(ys[1:])
            cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2
            gu = np.maximum(np.maximum(near[None, :, 0] - X1[:, None], X0[:, None] - near[None, :, 1]), 0)       # [nx, nc]
            gv = np.maximum(np.maximum(near[None, :, 2] - Y1[:, None], Y0[:, None] - near[None, :, 3]), 0)       # [ny, nc]
            dist = np.maximum(gu[:, None, :], gv[None, :, :])                                                   # [nx, ny, nc]
            inside = ((near[None, None, :, 0] <= cx[:, None, None]) & (cx[:, None, None] <= near[None, None, :, 1]) &
                      (near[None, None, :, 2] <= cy[None, :, None]) & (cy[None, :, None] <= near[None, None, :, 3])).any(2)
            dmin = dist.min(2); best = dist.argmin(2)
            sig = {}
            for i in range(len(cx)):
                for j in range(len(cy)):
                    if inside[i, j] or dmin[i, j] >= D - 1e-6: continue
                    c = near[best[i, j]]                                                  # the wall this cell fronts: its axis and side
                    if c[0] - 1e-6 <= cx[i] <= c[1] + 1e-6: axis, side = 'v', (1 if cy[j] > c[3] else -1)
                    else: axis, side = 'u', (1 if cx[i] > c[1] else -1)
                    bands = tuple((m, z0, z1) for m, z0, z1, pr in bands_at(room, cx[i], cy[j], axis, side, F, H) if dmin[i, j] < pr - 1e-6 and z1 - z0 > 1e-3)
                    if bands: sig[(i, j)] = bands
            runs = []                                                                    # runs of like cells along u, then like runs merged along v
            for j in range(len(cy)):
                i = 0
                while i < len(cx):
                    b = sig.get((i, j))
                    if b is None: i += 1; continue
                    k = i
                    while k + 1 < len(cx) and sig.get((k + 1, j)) == b: k += 1
                    runs.append((i, k, j, b)); i = k + 1
            open_ = {}; rects = []
            for i, k, j, b in runs:
                key = (i, k, b); prev = open_.get(key)
                if prev is not None and prev[1] == j - 1: prev[1] = j
                else:
                    if prev is not None: rects.append((i, k, prev[0], prev[1], b))
                    open_[key] = [j, j]
            rects += [(i, k, j0, j1, b) for (i, k, b), (j0, j1) in open_.items()]
            for i, k, j0, j1, b in rects:
                for m, z0, z1 in b:
                    bb = (X0[i], X1[k], Y0[j0], Y1[j1], z0, z1)
                    hit = SOL[(SOL[:, 0] < bb[1] - 1e-4) & (SOL[:, 3] > bb[0] + 1e-4) & (SOL[:, 1] < bb[3] - 1e-4) & (SOL[:, 4] > bb[2] + 1e-4) &
                              (SOL[:, 2] < bb[5] - 1e-4) & (SOL[:, 5] > bb[4] + 1e-4)]
                    for q in TB.box_minus(bb, cut + [(h[0], h[3], h[1], h[4], h[2], h[5]) for h in hit]):
                        if min(q[1] - q[0], q[3] - q[2], q[5] - q[4]) < 0.002: continue
                        TK.box(room, (q[0], q[2], q[4]), (q[1], q[3], q[5]), m, col=False); n += 1
        laid[room] = n
    return laid
