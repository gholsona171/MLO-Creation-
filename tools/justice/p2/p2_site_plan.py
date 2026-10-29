"""Justice Center phase 2: the site's height functions (pure Python, Blender + p1_maps + the gates), from plan/p2_site.json
(p2_site.py). One function per surface, so the drawn ground, its collision and every prop seated on it agree."""
import json, math
from pathlib import Path
J = Path(r'C:\Users\anton\Documents\Codex\JusticeCenter')
S = json.load(open(J / 'plan/p2_site.json'))
G, SLAB = S['G'], S['slab']
KERB_UP = 0.15                                          # the lawn's outer edge stands this far over the slab (a granite kerb)
def _seg_d(p, a, b):
    ax, ay = a; bx, by = b; px, py = p; ex, ey = bx - ax, by - ay; l2 = ex * ex + ey * ey
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((px - ax) * ex + (py - ay) * ey) / l2))
    return math.hypot(px - ax - t * ex, py - ay - t * ey)
def _line_d(p, pts): return min(_seg_d(p, a, b) for a, b in zip(pts, pts[1:]))
INNER = [tuple(p) for p in S['inner']]; OUTER = [tuple(p) for p in S['outer']]
def lawn_z(u, v):
    """the lawn and the walk: 28.8 along the building side (podium / Jail I), KERB_UP over the slab at the kerb; in between by the
    two distances (a smooth, even fall towards Davis Ave / Macdonald / Innocence)."""
    di = _line_d((u, v), INNER); do = _line_d((u, v), OUTER)
    t = di / (di + do) if di + do > 1e-9 else 0.0
    t = t * t * (3 - 2 * t) * 0.35 + t * 0.65                  # a little easing at both ends (no crease at the podium)
    return G + (SLAB + KERB_UP - G) * t
def _inside(poly, u, v):
    c = False; n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a[1] > v) != (b[1] > v) and u < (b[0] - a[0]) * (v - a[1]) / (b[1] - a[1]) + a[0]: c = not c
    return c
def on_podium(u, v): return any(a <= u <= b and c <= v <= d for a, b, c, d in S['podium'])
def on_lawn(u, v): return any(_inside(p, u, v) for p in S['lawn'] + S['walk'])
def ground_uv(u, v, slab_z):
    """the top of OUR ground at a lot point (slab_z: jc_frame.slab_z for the world point)."""
    if on_podium(u, v): return G
    if on_lawn(u, v): return lawn_z(u, v)
    return slab_z
