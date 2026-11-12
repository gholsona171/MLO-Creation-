"""Area 5 drawing helpers (Blender, called from jc3_tower_build): the BrunX-look finishes and fittings from jc5_court's numbers.
  walls          a room's walls: the core lining in its upper finish (marble / plaster), recorded for jc_shell, and the room's band set
                 (skirting, mahogany wainscot, the cap rail, a mahogany cornice and crown) laid as ONE shell round every wall of the
                 room - linings and partitions alike - by shells() once the floor's built-ins have claimed their wall space.
                 (2026-11-11: per-wall banded linings + free partitions crossed at T-junctions and z-fought; rebuilt as the shell.)
  placard        gold-on-black lettering in a mahogany frame (our artwork, jc5_art.py), the BrunX placard style.
  tray_ceiling   a rectangular room's ceiling with a dropped mahogany-edged soffit round a raised centre.
Every material here is textured (bx_* open textures, Rockstar's or TK's textured kit): no flat paint."""
import subprocess
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
import tc_kit as TK
import jc3_tower as JT, jc5_court as C
import jc3_tower_build as TB
import jc_shell as SH
OPS = TB.OPS
PLAC = {}
SHELL = {}                                                                # room -> its shell (floor, region, height, bands, holes)
DEPTHS = (C.SKIRT_P, C.PANEL_P, C.CAP_P, C.CORNICE[1], C.CORNICE[2])
def walls(room, region, others, F, top, holes, wainscot, upper='plaster', cap='bx_nero', ext_t=0.2, cornice=True, panel='bx_mahog'):
    """the walls of `room` from F to top: the core lining in `upper` (holes = 3D boxes: doors, window bays: see deep_bays) and the
    room's bands (z over the floor, depth off the core) for shells()."""
    SH.record(room, TB._grid_lining(region, others, ext_t, 0.1), F, top)
    TB.lining(room, region, others, F, top, upper, holes, ext_t=ext_t, int_t=0.1)
    H = top - F; w = wainscot
    bands = [(panel, 0.0, C.SKIRT_H, C.SKIRT_P), (panel, C.SKIRT_H, w, C.PANEL_P), (cap, w, w + C.CAP_H, C.CAP_P)]
    if cornice: bands += [(panel, H - C.CORNICE[0], H - 0.12, C.CORNICE[1]), (panel, H - 0.12, H, C.CORNICE[2])]
    SHELL[room] = {'F': F, 'region': region, 'H': H, 'bands': bands, 'holes': list(holes), 'built': False}
def partition(room, ax, at, a0, a1, F, top, holes, upper):
    """a 0.2 wall inside a room (centre line at `at`, from a0 to a1 along it: from core face to core face), in the upper finish; the
    room's shell gives it its bands on both faces and round its ends."""
    box3 = (at - 0.1, at + 0.1, a0, a1) if ax == 'u' else (a0, a1, at - 0.1, at + 0.1)
    SH.record(room, [box3], F, top)
    for c in TB.box_minus((*box3, F, top), holes): TK.box(room, (c[0], c[2], c[4]), (c[1], c[3], c[5]), upper)
def shell_depth(room, z0, z1):
    """how far the room's shell stands off its walls between z0 .. z1 (absolute): wall pieces stand off that much (or claim the space)."""
    sh = SHELL.get(room)
    if not sh: return 0.0
    return max([d for m, a, b, d in sh['bands'] if sh['F'] + a < z1 and sh['F'] + b > z0] or [0.0])
def shells():
    """lay the shell of every room whose walls() ran and whose shell is not laid yet."""
    for room, sh in SHELL.items():
        if sh['built']: continue
        bands = sh['bands']
        SH.build({room: (sh['F'], sh['region'], sh['H'])}, sh['holes'],
                 lambda r, u, v, ax, sd, F, H, b=bands: [(m, F + z0, F + z1, d) for m, z0, z1, d in b], DEPTHS)
        sh['built'] = True
def deep_bays(F, depth=0.45):
    """the window bays of the floor at F as 3D boxes: through the outer lining (+ 1 cm) and 0.45 m into the room (the shell too)."""
    out = []
    for fid, (ax, plane, o) in JT.FACE_LINE.items():
        lo, hi = sorted((plane + o * (JT.OL + 0.01), plane - o * depth))
        for a0, a1, z0, z1 in JT.bays(fid, F):
            out.append((lo, hi, a0, a1, z0, z1) if ax == 'u' else (a0, a1, lo, hi, z0, z1))
    return out
def placard(room, key, lines, c, face, w=1.1, h=0.42, frame=0.035):
    """lettering panel 2.2 cm proud of a mahogany frame board on the wall at c (centre: on the core wall's face); face = the side it
    reads from."""
    d = TK.OUT / 'tex' / 'jc5_art'
    if key not in PLAC:
        subprocess.run([TK.PYPIL, str(Path(__file__).resolve().parent.parent / 'interior' / 'jc5_art.py'), str(d), f'{key}=' + '|'.join(lines)], check=True)
        im = bpy.data.images.load(str(d / f'placard_{key}.png')); px = np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], 4); bpy.data.images.remove(im)
        px[:, :, 3] = 1.0; m = TK.tex_mat(f'JC5 placard {key}', px, False, 1.0, 0.25); m['preserve_authored_uv'] = True; TK.KEEP.add(m.name); PLAC[key] = m
    cu, cv, cz = c; s = 1 if face[0] == '+' else -1; ax = face[1]
    W2, H2 = w / 2 + frame, h / 2 + frame
    k, n = (0, cu) if ax == 'u' else (1, cv); along = cv if ax == 'u' else cu
    on_wall = any(abs(r[2 * k + (1 if s > 0 else 0)] - n) < 0.003 and r[2 * (1 - k)] <= along <= r[2 * (1 - k) + 1] for r in SH.CORE.get(room, []))
    fb = 0.03 + (shell_depth(room, cz - H2, cz + H2) if on_wall else 0.0)   # the frame board: 3 cm clear of the room's shell on a wall
    if ax == 'u': lo, hi = (min(cu, cu + s * fb), cv - W2, cz - H2), (max(cu, cu + s * fb), cv + W2, cz + H2)
    else: lo, hi = (cu - W2, min(cv, cv + s * fb), cz - H2), (cu + W2, max(cv, cv + s * fb), cz + H2)
    TK.box(room, lo, hi, 'bx_mahog', col=False); SH.keep_clear(room, lo, hi)
    e = (fb + 0.022) * s                                                   # the lettering 2.2 cm proud of the frame board (the sweep: > 1.2 cm)
    if ax == 'u': L, R = (cu + e, cv - s * w / 2), (cu + e, cv + s * w / 2)
    else: L, R = (cu + s * w / 2, cv + e), (cu - s * w / 2, cv + e)
    pts = [(*L, cz - h / 2), (*R, cz - h / 2), (*R, cz + h / 2), (*L, cz + h / 2)]
    me = bpy.data.meshes.new('placard'); me.from_pydata([Vector(p) for p in pts], [], [(0, 1, 2, 3)]); me.materials.append(PLAC[key])
    uv = me.uv_layers.new(name='UVMap 0')
    for li, q in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))): uv.data[li].uv = q
    o = bpy.data.objects.new('placard', me); TK.coll().objects.link(o); TK.PARTS[room].append(o)
    TK.SIGNS.append({'name': 'placard ' + key, 'room': room, 'lines': list(lines), 'face': face, 'pts': [[round(float(x), 4) for x in p] for p in pts], 'w': float(w), 'h': float(h)})
def tray_ceiling(room, rect, top, inset, drop, mat='plaster', edge='bx_mahog', walls=(0.0, 0.0, 0.0, 0.0)):
    """ceiling slab over rect at top (underside) with a soffit ring hanging `drop` below it between the wall linings (walls = their
    thickness on the u0 / u1 / v0 / v1 sides: the ring stands on their faces, never inside them) and the raised centre `inset` in from
    rect, a mahogany fascia on its inner edge and downlights in the soffit."""
    u0, u1, v0, v1 = rect; TK.box(room, (u0, v0, top), (u1, v1, top + 0.2), mat, col=False)
    inner = (u0 + inset, u1 - inset, v0 + inset, v1 - inset)
    w0, w1, w2, w3 = walls; u0, u1, v0, v1 = u0 + w0, u1 - w1, v0 + w2, v1 - w3
    for a, b, c, d in TK.rects_minus(u0, u1, v0, v1, [inner]): TK.box(room, (a, c, top - drop), (b, d, top), mat, col=False)
    f = 0.08; iu0, iu1, iv0, iv1 = inner
    for a, b, c, d in ((iu0, iu1, iv0, iv0 + f), (iu0, iu1, iv1 - f, iv1), (iu0, iu0 + f, iv0 + f, iv1 - f), (iu1 - f, iu1, iv0 + f, iv1 - f)):
        TK.box(room, (a, c, top - drop - 0.08), (b, d, top - drop + 0.02), edge, col=False)
    for a, b, c, d in TK.rects_minus(u0, u1, v0, v1, [inner]):
        n = max(1, int(max(b - a, d - c) // 2.6))
        for i in range(n):
            t = (i + 0.5) / n; x, y = (a + (b - a) * t, (c + d) / 2) if b - a > d - c else ((a + b) / 2, c + (d - c) * t)
            TK.lamp(room, x, y, top - drop, energy=0.35, falloff=5.0, size=(0.16, 0.16))
def chandelier(room, u, v, ceil, scale=1.0):
    """our chandelier hung at the ceiling (pivot = the rod's top) with its light."""
    OPS.setdefault('hung', []).append((room, 'jc_courts_chandelier', u, v, ceil, 0.0, scale))
    TK.lamp(room, u, v, ceil - 1.0 * scale, energy=1.1, falloff=10.0, size=(0.5, 0.5))
def pilaster(room, axis, plane, a, s, F, top, w=0.5, p=0.10, inset='bx_wallmarble', zin=(2.45, 4.6)):
    """a mahogany pilaster on the core wall face `plane` (s = +1 / -1: the room side), centred at a, full height, with a cream inset
    panel; the shell's bands stop on its sides."""
    lo = [0, 0, F]; hi = [0, 0, top]; k = 0 if axis == 'u' else 1
    lo[k], hi[k] = sorted((plane, plane + s * p)); lo[1 - k], hi[1 - k] = a - w / 2, a + w / 2; SH.keep_clear(room, lo, hi)
    if axis == 'u':
        TK.box(room, (min(plane, plane + s * p), a - w / 2, F), (max(plane, plane + s * p), a + w / 2, top), 'bx_mahog')
        if zin: TK.box(room, (min(plane + s * p, plane + s * (p + 0.02)), a - w / 2 + 0.08, F + zin[0]), (max(plane + s * p, plane + s * (p + 0.02)), a + w / 2 - 0.08, F + zin[1]), inset, col=False)
    else:
        TK.box(room, (a - w / 2, min(plane, plane + s * p), F), (a + w / 2, max(plane, plane + s * p), top), 'bx_mahog')
        if zin: TK.box(room, (a - w / 2 + 0.08, min(plane + s * p, plane + s * (p + 0.02)), F + zin[0]), (a + w / 2 - 0.08, max(plane + s * p, plane + s * (p + 0.02)), F + zin[1]), inset, col=False)
def sconce(room, axis, plane, a, s, z):
    TK.lamp(room, *((plane + s * 0.12, a) if axis == 'u' else (a, plane + s * 0.12)), z, energy=0.45, falloff=5.0, size=(0.18, 0.18), mount=(None, axis))
def bookcase(room, axis, plane, a0, a1, s, F, h=2.6, d=0.40):
    """a built-in mahogany bookcase run on a wall (back, plinth, top, uprights, 4 shelves per bay - no two boxes overlap - books from
    Rockstar's stacks), standing on the core wall face `plane`: the shell's bands stop on its sides."""
    def bx(n0, n1, b0, b1, z0, z1, m, col=True):
        lo = (min(plane + s * n0, plane + s * n1)); hi = (max(plane + s * n0, plane + s * n1))
        if axis == 'u': TK.box(room, (lo, b0, z0), (hi, b1, z1), m, col)
        else: TK.box(room, (b0, lo, z0), (b1, hi, z1), m, col)
    n_lo, n_hi = sorted((plane, plane + s * d))
    SH.keep_clear(room, *(((n_lo, a0, F), (n_hi, a1, F + h)) if axis == 'u' else ((a0, n_lo, F), (a1, n_hi, F + h))))
    bx(0.0, 0.02, a0, a1, F, F + h, 'bx_mahog')                                          # back
    bx(0.02, d, a0, a1, F, F + 0.12, 'bx_mahog'); bx(0.02, d, a0, a1, F + h - 0.06, F + h, 'bx_mahog')      # plinth, top
    n = max(1, int((a1 - a0) // 0.95)); xs = [a0 + (a1 - a0) * i / n for i in range(n + 1)]
    ups = [(max(a0, x - 0.02), min(a1, x + 0.02)) for x in xs]
    for u0, u1 in ups: bx(0.02, d, u0, u1, F + 0.12, F + h - 0.06, 'bx_mahog')
    shelves = [F + 0.12 + k * (h - 0.18) / 5 for k in range(1, 5)]
    for (_, b0), (b1, _) in zip(ups, ups[1:]):                                           # shelves between the uprights, set 1 cm back
        for z in shelves: bx(0.02, d - 0.015, b0, b1, z - 0.025, z, 'bx_mahog', False)
    hd = (90.0 if s > 0 else 270.0) if axis == 'u' else (180.0 if s > 0 else 0.0)                # books face the room
    for z in [F + 0.12] + shelves:
        for i in range(n):
            for j, m in enumerate(('vw_prop_book_stack_03a', 'vw_prop_book_stack_03b')):
                c = xs[i] + (xs[i + 1] - xs[i]) * (0.3 + 0.4 * j); off = 0.20
                OPS['props'].append((room, m, *((plane + s * off, c) if axis == 'u' else (c, plane + s * off)), z, hd))
