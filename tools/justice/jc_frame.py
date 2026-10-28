"""Justice Center: the lot frame and the block outlines every build script shares (pure python, no Blender).
Lot frame (survey/site.md): origin (335.87, -1640.11), heading 50 deg; u towards Innocence Blvd (NE), v towards Davis Ave (NW).
KERB_UV: the survey's kerb outline (lot frame). LOT_UV (plan/lot_poly.json, written by lot_outline.py): the line where the block's
own ground meets Rockstar's sidewalk - everything inside it is cleared, everything outside it (sidewalk, kerb, street) is kept."""
import json, math
from pathlib import Path
J = Path(r'C:\Users\anton\Documents\Codex\JusticeCenter')
OX, OY, HDEG = 335.87, -1640.11, 50.0
H = math.radians(HDEG); C, S = math.cos(H), math.sin(H)
def W(u, v): return (OX + u * C - v * S, OY + u * S + v * C)
def L(x, y):
    dx, dy = x - OX, y - OY; return (dx * C + dy * S, -dx * S + dy * C)
_site = json.load(open(J / 'survey/site.json'))
KERB_UV = [tuple(p) for p in _site['block']['kerb_outline_uv']]
KERB_W = [W(u, v) for u, v in KERB_UV]
def inside(poly, x, y):
    c = False; n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]: c = not c
    return c
def edge_dist(poly, x, y):
    best = 1e9
    for i in range(len(poly)):
        a, b = poly[i - 1], poly[i]; ex, ey = b[0] - a[0], b[1] - a[1]; l2 = ex * ex + ey * ey
        t = max(0.0, min(1.0, ((x - a[0]) * ex + (y - a[1]) * ey) / l2))
        best = min(best, math.hypot(x - a[0] - t * ex, y - a[1] - t * ey))
    return best
def lot_w():
    """the clearing outline, world xy (plan/lot_poly.json, lot_outline.py)"""
    return [tuple(p) for p in json.load(open(J / 'plan/lot_poly.json'))['world']]
def in_lot(x, y): return inside(LOT_W_CACHE(), x, y)
_lc = []
def LOT_W_CACHE():
    if not _lc: _lc.append(lot_w())
    return _lc[0]
def live_ymap(y, names):
    """the copy the rig loads (survey: lr_ on, hei_ / base off): lr_ when it exists, else the base name, hei_ only when neither does"""
    b = y[3:] if y.startswith('lr_') else y[4:] if y.startswith('hei_') else y
    if y.startswith('lr_'): return True
    if y.startswith('hei_'): return ('lr_' + b) not in names and b not in names
    return ('lr_' + b) not in names
def edge_pts(step=1.0):
    """the lot outline with its heights (Rockstar's sidewalk edge), every edge split into pieces <= step m (straight in plan and
    height, so every extra point lies on his edge line): [(x, y, z), ...] counter-clockwise"""
    P = [tuple(p) for p in json.load(open(J / 'plan/lot_poly.json'))['world']]; out = []
    for i, a in enumerate(P):
        b = P[(i + 1) % len(P)]; n = max(1, math.ceil(math.dist(a[:2], b[:2]) / step))
        for k in range(n): t = k / n; out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t))
    return out
_E = []
def slab_z(x, y):
    """the lot slab's height at (x, y): inverse-distance (d^-3) mean of the edge heights (Tower City l0_slab rule; the slab and every
    rule that seats something on it use this one function)"""
    import numpy as np
    if not _E: _E.append(np.array(edge_pts(1.0)))
    E = _E[0]; d = np.sqrt((E[:, 0] - x) ** 2 + (E[:, 1] - y) ** 2) + 0.05; w = d ** -3
    return float((w * E[:, 2]).sum() / w.sum())
