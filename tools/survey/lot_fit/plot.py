"""Block Boyz site survey drawings (north up, world metres):
  ../topdown_area.png   the whole box: ground height, the 30.0 shoreline, water, roads (collision + path nodes), houses, poles,
                        bushes / trees, wrecks and boats, car generators, the three placements, the client's junction
  ../topdown_P1.png     the client's strip close up with P1 / P2 and every entity that would go
  ../heightmap_2m.npz   the ground (low) and top surfaces on the 2 m grid
Reads placements.json (evaluate.py) and the building outline from ../../tools/concept_v3.py (read only)."""
import sys, os, json, math; sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'tools'))
import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
import common as C
import concept_v3 as CV
low, top, (x0, x1, y0, y1, c) = C.heights(); M = np.load(os.path.join(C.D, 'masks.npz'))
ny, nx = low.shape
l2 = np.nanmean(low.reshape(ny // 2, 2, nx // 2, 2), axis=(1, 3)); t2 = np.nanmax(top.reshape(ny // 2, 2, nx // 2, 2), axis=(1, 3))
np.savez_compressed(os.path.join(C.D, 'heightmap_2m.npz'), ground=l2, top=t2, box=np.array([x0, x1, y0, y1, 2.0]),
                    note='ground = lowest walkable collision surface (mean of 1 m cells), top = highest; NaN = no collision')
PL = json.load(open(os.path.join(C.D, 'placements.json')))['placements']
ENTS = C.entities(); R, SEGS = C.nodes()
COL = {'P1': '#d62728', 'P2': '#ff7f0e', 'P3': '#9467bd'}


def W(p, o, h):
    cc, s = math.cos(h), math.sin(h); return (o[0] + cc * p[0] - s * p[1], o[1] + s * p[0] + cc * p[1])


def base(ax, lim):
    X0, X1, Y0, Y1 = lim
    im = ax.imshow(np.clip(low, 24, 46), origin='lower', extent=(x0, x1, y0, y1), cmap='terrain', vmin=18, vmax=46, interpolation='nearest')
    xs, ys = np.arange(x0 + .5, x1), np.arange(y0 + .5, y1)
    cs = ax.contour(xs, ys, low, levels=np.arange(32, 46, 2), colors='k', linewidths=.3, alpha=.4); ax.clabel(cs, fontsize=6, fmt='%d')
    ax.contourf(xs, ys, M['water'].astype(float), levels=[.5, 1.5], colors=['#3a7bd5'], alpha=.45)
    ax.contour(xs, ys, low, levels=[C.WATER_Z], colors='#0033cc', linewidths=1.6)
    ax.contourf(xs, ys, M['road'].astype(float), levels=[.5, 1.5], colors=['#444444'], alpha=.75)
    for a, b, ped, f0, st in SEGS:
        if not ped: ax.plot([a[0], b[0]], [a[1], b[1]], color='w', lw=.6, ls='--')
    for e in ENTS:
        if not (X0 - 20 < e['x'] < X1 + 20 and Y0 - 20 < e['y'] < Y1 + 20): continue
        a = e['arch']
        if C.is_house(a): ax.add_patch(Polygon(C.corners(e), fc='#8b0000', ec='k', alpha=.6, lw=.6))
        elif a.startswith(('prop_telegraph', 'prop_telegwall')): ax.plot(e['x'], e['y'], marker='^', color='#b00000', ms=5, mec='k', mew=.4)
        elif any(t in a for t in ('rowboat', 'byard', 'carwreck', 'trukwreck')): ax.plot(e['x'], e['y'], 's', color='#00bcd4', ms=5, mec='k', mew=.4)
        elif any(t in a for t in ('bush', 'tree', 'palm')): ax.plot(e['x'], e['y'], '.', color='#1b5e20', ms=3)
        elif 'fnc' in a or 'fence' in a:
            p = C.corners(e); ax.plot([p[0][0], p[1][0]], [p[0][1], p[1][1]], color='#795548', lw=1)
    for l in open(os.path.join(C.D, 'site_scan.txt')):
        if l.startswith('CARGEN'):
            v = [float(t) for t in __import__('re').findall(r'[XY]:(-?[\d.]+)', l)]; ax.plot(v[0], v[1], 'P', color='y', ms=6, mec='k', mew=.4)
    ax.add_patch(Rectangle((1275, 3600), 50, 75, fill=False, ec='k', ls=':', lw=1.2))
    ax.text(1277, 3677, "client's junction\n(street query)", fontsize=7)
    return im


def placement(ax, P, full):
    o, h = (P['site_json']['x'], P['site_json']['y']), math.radians(P['site_json']['heading']); col = COL[P['id']]
    ax.add_patch(Polygon(P['corners'], fill=False, ec=col, lw=2.2, ls='-' if P['id'] != 'P2' else '--'))
    if full:
        ax.add_patch(Polygon([W(p, o, h) for p in CV.grown(*CV.OVERHANG)], fc=col, alpha=.25, ec=col, lw=.8))
        ax.add_patch(Polygon([W(p, o, h) for p in CV.outline()], fc=col, alpha=.45, ec='k', lw=.8))
        for p in (CV.ARCH[0], CV.ARCH[-1]): q = W(p, o, h); ax.plot(q[0], q[1], 'o', color=col, mec='k', ms=5)
        a = W((32, -6), o, h); b = W((32, -22), o, h)
        ax.annotate('', xy=b, xytext=a, arrowprops=dict(arrowstyle='->', color=col, lw=1.6))
    cx, cy = P['centre']; ax.text(cx, cy, f"{P['id']}\n{P['size_m'][0]:.0f} x {P['size_m'][1]:.0f} m", color=col, fontsize=9, ha='center',
                                  va='center', weight='bold', bbox=dict(fc='w', alpha=.6, lw=0))


def legend(ax):
    from matplotlib.lines import Line2D
    h = [Line2D([], [], color='#0033cc', lw=1.6, label='shoreline (ground = water 30.0)'), Line2D([], [], color='#444444', lw=5, label='road collision'),
         Line2D([], [], color='w', ls='--', lw=1, label='vehicle path nodes'), Line2D([], [], marker='^', color='#b00000', ls='', label='power pole'),
         Line2D([], [], marker='s', color='#00bcd4', ls='', label='boat / wreck'), Line2D([], [], marker='.', color='#1b5e20', ls='', label='bush / tree'),
         Line2D([], [], marker='P', color='y', ls='', label='car generator'), Line2D([], [], color='#8b0000', lw=5, label='house / shed'),
         Line2D([], [], color='#795548', lw=1, label='fence')] + \
        [Line2D([], [], color=COL[k], lw=2, label=f'{k} site (arrow = glass front, dots = arch legs)') for k in COL]
    ax.legend(handles=h, loc='lower left', fontsize=7, framealpha=.85)


for name, lim, full in (('topdown_area.png', (1000, 1500, 3400, 3900), True), ('topdown_P1.png', (1120, 1360, 3480, 3720), True)):
    fig, ax = plt.subplots(figsize=(15, 15)); im = base(ax, lim)
    for P in PL: placement(ax, P, full and (P['id'] != 'P2'))
    if name == 'topdown_P1.png':
        P1 = next(p for p in PL if p['id'] == 'P1')
        for e in P1['entities']:
            if e['inside'] and e['kind'] not in ('ground / decal mesh', 'wire span'): ax.plot(e['x'], e['y'], 'x', color='k', ms=4, mew=.8)
    ax.set_xlim(lim[0], lim[1]); ax.set_ylim(lim[2], lim[3])
    st = 50 if lim[1] - lim[0] > 300 else 20
    ax.set_xticks(range(lim[0], lim[1] + 1, st)); ax.set_yticks(range(lim[2], lim[3] + 1, st)); ax.grid(alpha=.25); ax.tick_params(labelsize=7)
    ax.set_title('Block Boyz site survey, west Sandy Shores (north up, world metres). Colour = ground height (m)'
                 + ('; x = vanilla entities inside P1' if name == 'topdown_P1.png' else ''), fontsize=10)
    legend(ax); plt.colorbar(im, ax=ax, shrink=.5, label='ground z (m)')
    plt.savefig(os.path.join(C.D, name), dpi=90, bbox_inches='tight'); plt.close(fig); print('wrote', name)
