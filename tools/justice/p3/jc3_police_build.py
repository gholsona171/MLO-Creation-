"""Area 3 build (Blender, called by jc3_build.py): the Police HQ's L1 + L2 as REDESIGNED 2026-10-31 (jc3_police / jc3_redesign_plan:
dense rooms off narrow corridors, the public and secure sides apart), the stair B1 - L1 - L2 and the interview suites (both kept as
approved), with jc3_tower_build's helpers. prepare() registers every door before a wall is drawn (walls take their holes from
JT.OPENINGS); build() draws the rooms and returns the regions.
  walls     each MLO room's LINING (TB.lining) + 0.2 partitions between its named spaces (space_walls), doors cut out; the lobby in
            Pacific Standard's granite, offices in the bank's plaster, the L1 staff side in Mission Row's block
  floors    per space by its finish: travertine (public), carpet (offices), floorboards (command), speckled vinyl (L1 staff), concrete
            (secure), tile (wet)
  finishes  the approved board (P.TRIMS: skirting, navy wainscot + gold rail, wood panelling in command, white tile in the wet rooms,
            hazard skirting on the secure side, brick accent walls) as solid shells round the recorded walls (jc_shell)
  counters  the front desk window in the lobby's west wall and the property / records windows onto the hall: bullet-resistant
            glass, ledges both sides, a portal through each pane
  insignia  our own Cleveland Division of Police art (jc3_insignia.py -> PNG): wall panels, the lobby + B1 floor seals (decals), the
            patch on the front transom
Every face textured: Rockstar's materials (jc3_build.rs) and our tinted / painted ones for the navy, gold, skirting and tile. No patchwork:
the old trim pass (boards laid on wall faces after the fact) was removed whole on 2026-11-11 and the finishes rebuilt from the walls."""
import subprocess
from pathlib import Path
import numpy as np
import tc_kit as TK
import jc3_tower as JT, jc3_police as P, jc3_police_dress as D
import jc3_tower_build as TB
import jc_shell as PF
DF = JT.DF                                                                # the playbook door tool (casings)
OPS = TB.OPS
GLASS = (JT.GLASS_L, JT.GLASS_R)
ROOM_H = 2.6                                                              # L1 / L2 rooms' clear height (ceiling slab over it, the next floor's slab over that)
INTO = {'P_desk': -1, 'P_staff': -1, 'P_stairL1': 1, 'P_stairL2': 1, 'P_stairB1': -1, 'P_int1': 1, 'P_obs1': 1, 'P_obs2': 1, 'P_int2': 1}
WALL_MAT = {'plobby': 'plaster', 'pdesk': 'plaster', 'pstaff1': 'block', 'pstaff2': 'plaster'}
FLOOR = {'lobby': 'marble', 'public': 'marble', 'office': 'plank', 'command': 'plank', 'staff': 'speckle', 'secure': 'conc', 'wet': 'tilefloor'}
def door_name(room, name): return 'P_in_' + room + '_' + name.replace(' ', '_')
def prepare():
    """the police doors into JT's lists (TB.build_rooms collects OPS['doors'] / portals from them)."""
    JT.double_door('P_front', 'plobby', 'limbo', 'u', P.EG, P.FRONT[0], P.P1, 1, models=GLASS)
    JT.double_door('P_link', 'plobby', 'galleria', 'v', P.NI_LINK, P.LINK[0], P.P1, 1, models=GLASS)
    for name, frm, to, z, ax, plane, a0, kind in P.PORTAL_DOORS:
        if kind == 'single': JT.single_door(name, frm, to, ax, plane, a0, z, INTO[name])
    for room, name, z, ax, plane, a0 in P.INNER_DOORS:
        JT.single_door(door_name(room, name), room, None, ax, plane, a0, z, 1, model=P.DOOR_MODEL.get((room, name), JT.GEN))
def _inreg(region, x, y): return any(r[0] - 1e-6 <= x <= r[1] + 1e-6 and r[2] - 1e-6 <= y <= r[3] + 1e-6 for r in region)
def space_walls(room, spaces, opens, F, region, others, ext_t, holes, mat_of):
    """0.2 partitions between a room's named spaces, centred on their shared edges, doors cut out (open pairs meet without one). Each
    runs the whole shared edge, less the room's own lining cells (TB._grid_lining: the same cells TB.lining draws), so it meets a lining
    face flush and never overlaps it. Where two partitions meet inside the room (an end with the room all round it) they stop 0.1 short of
    each other's line; an L or a cross leaves the 0.2 square at the joint uncovered, so one of them runs through it (no slit in a corner)."""
    seg, names, done = [], list(spaces), set()
    def interior(ax, pa, c):
        pts = [(pa + du, c + dv) for du in (-0.15, 0.15) for dv in (-0.15, 0.15)]
        return all(_inreg(region, *((x, y) if ax == 'u' else (y, x))) for x, y in pts)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if (a, b) in opens or (b, a) in opens: continue
            for ra in spaces[a]:
                for rb in spaces[b]:
                    for ax, pa, pb in (('u', ra[1], rb[0]), ('u', ra[0], rb[1]), ('v', ra[3], rb[2]), ('v', ra[2], rb[3])):
                        if abs(pa - pb) > 1e-6: continue
                        lo, hi = ((max(ra[2], rb[2]), min(ra[3], rb[3])) if ax == 'u' else (max(ra[0], rb[0]), min(ra[1], rb[1])))
                        key = (ax, round(pa, 3), round(lo, 3))
                        if hi - lo < 0.05 or key in done: continue
                        done.add(key)
                        j0, j1 = interior(ax, pa, lo), interior(ax, pa, hi)
                        seg.append([ax, pa, lo, hi, 0.1 if j0 else 0.0, 0.1 if j1 else 0.0, j0, j1, mat_of(a, b)])
    def box_of(s): return (s[1] - 0.1, s[1] + 0.1, s[2] + s[4], s[3] - s[5]) if s[0] == 'u' else (s[2] + s[4], s[3] - s[5], s[1] - 0.1, s[1] + 0.1)
    claimed = []
    for s in seg:                                                         # the joints nobody covers: this partition runs through
        for k, c in ((0, s[2]), (1, s[3])):
            if not s[6 + k]: continue
            sq = (s[1], c) if s[0] == 'u' else (c, s[1])
            cover = [box_of(q) for q in seg if q is not s] + claimed
            if any(b[0] - 1e-4 <= sq[0] <= b[1] + 1e-4 and b[2] - 1e-4 <= sq[1] <= b[3] + 1e-4 for b in cover): continue
            s[4 + k] = -0.1; claimed.append(box_of(s))
    cells = TB._grid_lining(region, others, ext_t, 0.1)
    for s in seg:
        for u0, u1, v0, v1 in TK.rects_minus(*box_of(s), cells):
            if min(u1 - u0, v1 - v0) < 0.005: continue
            PF.record(room, [(u0, u1, v0, v1)], F, F + ROOM_H)
            for c in TB.box_minus((u0, u1, v0, v1, F, F + ROOM_H), holes): TK.box(room, (c[0], c[2], c[4]), (c[1], c[3], c[5]), s[8])
def mesh_walls(room, spaces, pairs, F, region, others, ext_t):
    """steel mesh walls (Rockstar's Mission Row armoury mesh, normal_cutout) on the shared edges of the `pairs` of spaces, in place of a
    block partition: 5 cm posts at the ends and every <= 1.4 m, a bottom and a top rail, the mesh between them both ways (two one-sided
    quads), one collision slab per run. A door on the line hangs in a steel frame on its fitted opening (6 cm jambs, a head over the leaf)."""
    import bpy
    from mathutils import Vector
    def interior(ax, pa, c):
        return all(_inreg(region, *((pa + du, c + dv) if ax == 'u' else (c + dv, pa + du))) for du in (-0.15, 0.15) for dv in (-0.15, 0.15))
    def end_t(ax, pa, c):
        if interior(ax, pa, c): return 0.1
        x, y = (pa, c) if ax == 'u' else (c, pa)
        for r, t in others:
            if r[0] - 1e-6 <= x <= r[1] + 1e-6 and r[2] - 1e-6 <= y <= r[3] + 1e-6: return t
        return ext_t
    def bx(ax, pa, t, a0, a1, z0, z1, mat, col=True):
        if ax == 'u': TK.box(room, (pa - t, a0, z0), (pa + t, a1, z1), mat, col)
        else: TK.box(room, (a0, pa - t, z0), (a1, pa + t, z1), mat, col)
    def quad(ax, pa, a0, a1, z0, z1, s):
        P_ = [(pa, a0, z0), (pa, a1, z0), (pa, a1, z1), (pa, a0, z1)] if ax == 'u' else [(a0, pa, z0), (a1, pa, z0), (a1, pa, z1), (a0, pa, z1)]
        if (ax == 'u') == (s < 0): P_ = P_[::-1]                           # wound to face +s along the wall's normal axis
        me = bpy.data.meshes.new('mesh'); me.from_pydata([Vector(p) for p in P_], [], [(0, 1, 2, 3)]); me.materials.append(TK.MAT['metmesh'])
        me.uv_layers.new(name='UVMap 0'); me.update(); o = bpy.data.objects.new('mesh', me); TK.coll().objects.link(o); TK.PARTS[room].append(o)
    done = set()
    for a, b in pairs:
        for ra in spaces[a]:
            for rb in spaces[b]:
                for ax, pa, pb in (('u', ra[1], rb[0]), ('u', ra[0], rb[1]), ('v', ra[3], rb[2]), ('v', ra[2], rb[3])):
                    if abs(pa - pb) > 1e-6: continue
                    lo, hi = ((max(ra[2], rb[2]), min(ra[3], rb[3])) if ax == 'u' else (max(ra[0], rb[0]), min(ra[1], rb[1])))
                    if hi - lo < 0.05 or (ax, round(pa, 3), round(lo, 3)) in done: continue
                    done.add((ax, round(pa, 3), round(lo, 3)))
                    s0, s1 = lo + end_t(ax, pa, lo - 1e-3), hi - end_t(ax, pa, hi + 1e-3)
                    doors = sorted((o['a0'], o['a1'], o['z1']) for o in JT.OPENINGS if o['axis'] == ax and abs(o['plane'] - pa) < 1e-6
                                   and abs(o['z0'] - F) < 0.5 and o['a0'] >= s0 - 1e-6 and o['a1'] <= s1 + 1e-6)
                    spans, cur = [], s0
                    for d0, d1, dz in doors:                                  # a steel frame on the fitted opening (jambs on the leaf's bbox)
                        bx(ax, pa, 0.06, d0 - 0.06, d0, F, F + ROOM_H, 'steel'); bx(ax, pa, 0.06, d1, d1 + 0.06, F, F + ROOM_H, 'steel')
                        bx(ax, pa, 0.06, d0, d1, dz, F + ROOM_H, 'steel'); spans.append((cur, d0 - 0.06)); cur = d1 + 0.06
                    spans.append((cur, s1))
                    for m0, m1 in spans:
                        if m1 - m0 < 0.1: continue
                        n = max(1, int(-(-(m1 - m0) // 1.4))); xs = [m0 + (m1 - m0) * i / n for i in range(n + 1)]
                        for i, x in enumerate(xs):                            # posts (the end posts inside the run)
                            p0 = x if i == 0 else (x - 0.05 if i == n else x - 0.025); bx(ax, pa, 0.025, p0, p0 + 0.05, F, F + ROOM_H, 'steel', col=False)
                        for i in range(n):                                    # rails and mesh between the posts (never through them)
                            q0 = xs[i] + (0.05 if i == 0 else 0.025); q1 = xs[i + 1] - (0.05 if i == n - 1 else 0.025)
                            bx(ax, pa, 0.02, q0, q1, F, F + 0.08, 'steel', col=False); bx(ax, pa, 0.02, q0, q1, F + ROOM_H - 0.06, F + ROOM_H, 'steel', col=False)
                            for sd in (1, -1): quad(ax, pa + sd * 0.001, q0, q1, F + 0.08, F + ROOM_H - 0.06, sd)
                        if ax == 'u': TK.colbox(room, (pa - 0.02, m0, F), (pa + 0.02, m1, F + ROOM_H))
                        else: TK.colbox(room, (m0, pa - 0.02, F), (m1, pa + 0.02, F + ROOM_H))
def lining(room, region, others, z0, z1, mat, holes, ext_t):
    PF.record(room, TB._grid_lining(region, others, ext_t, 0.1), z0, z1); TB.lining(room, region, others, z0, z1, mat, holes, ext_t=ext_t, int_t=0.1)
def floors(room, spaces, F, staff_mat='speckle'):
    for k, rs in spaces.items():
        f = P.FINISH_OF.get(room, {}).get(k, P.FINISH_DEFAULT[room]); m = FLOOR[f] if f != 'staff' else staff_mat
        TB.slab(room, rs, F - 0.4, F, m)
def _shut(room, a0, a1):
    """a west bay stretch (a0 .. a1 along v) that belongs to a windowless secure room (P.WINDOWLESS): lined solid inside."""
    if room not in P.WINDOWLESS: return False
    names = P.WINDOWLESS[room]
    if names is None: return True
    sp = {'pstaff1': P.SPACES1, 'pstaff2': P.SPACES2}[room]
    return any(abs(r[0] - P.WI) < 0.02 and min(a1, r[3]) - max(a0, r[2]) > 0.05 for n in names for r in sp[n])
def _west(room, F, region):
    """the west face's window bays inside this room's region: holes through its outer lining + one limbo portal per region rect. The bays
    of windowless secure rooms get the portal but no hole (2026-11-01: the facade keeps its glazing, the room reads windowless)."""
    plane = P.WI + P.OL; bs = P.west_bays(F); holes = []
    for r in region:
        if abs(r[0] - P.WI) > 0.02: continue
        ins = [(max(a0, r[2]), min(a1, r[3]), z0, z1) for a0, a1, z0, z1 in bs if min(a1, r[3]) - max(a0, r[2]) > 0.05]
        holes += [(P.WI - 0.01, plane + 0.01, a0, a1, z0, z1) for a0, a1, z0, z1 in ins if not _shut(room, a0, a1)]
        if ins: OPS['portals'].append({'from': room, 'to': 'limbo', 'kind': f'{room} W windows', 'P': ('u', plane, min(i[0] for i in ins), max(i[1] for i in ins), ins[0][2], ins[0][3], -1)})
    return holes
RAIL_H, RAIL_OFF, RAIL_W, RAIL_T = 0.9, 0.06, 0.04, 0.05                # handrail: 0.9 m over the nosing line, its face 6 cm off the wall
def _handrail(room, wall, side, base, d, zb):
    """a wall handrail along one flight (lane along v): a 4 x 5 cm steel bar from the bottom riser to the top riser (the stretch the
    lane walls run beside: the mid wall ends at both landings) on the nosing line + RAIL_H, its inner face RAIL_OFF off the wall face
    `wall` (the lane on `side` of it), and three brackets into the wall."""
    run = (P.RISERS - 1) * P.GO; foot = base - d * P.GO; top = base + d * run
    z = lambda a: zb + (a - foot) * d / P.GO * P.RISE + RAIL_H
    c0, c1 = sorted((wall + side * RAIL_OFF, wall + side * (RAIL_OFF + RAIL_W)))
    cs = [(c, a, z(a) + dz) for dz in (-RAIL_T / 2, RAIL_T / 2) for c, a in ((c0, base), (c1, base), (c1, top), (c0, top))]
    TK.mesh(room, cs, [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], 'steel', False, 'stair_handrail')
    b0, b1 = sorted((wall, wall + side * RAIL_OFF))
    for t in (0.12, 0.5, 0.88):
        a = base + d * run * t; TK.box(room, (b0, a - 0.015, z(a) - RAIL_T / 2 - 0.06), (b1, a + 0.015, z(a) - RAIL_T / 2), 'steel', col=False)
def _stair(holes, zb1):
    """the police stair (rebuilt 2026-11-11, Antonio at postal 446: "the landing is missing and the flights don't connect"): one room
    from B1 (zb1) to L2, two lanes along v split by a block wall, a south landing on every floor and a north half landing between,
    each flight running from one landing's edge to the other's (P.SB_NLAND starts at the top riser), a wall handrail on both sides
    of every flight, and a steel balustrade on L2 where the west lane drops to the flight below (L2 is the top floor)."""
    room = 'pstair'; S = P.STAIR_B; z0, z1 = zb1, P.P2 + ROOM_H; reg = [S]
    TB.lining(room, reg, [], z0, z1, 'block', holes, ext_t=0.15, int_t=0.15)
    TB.slab(room, reg, z0 - 0.4, z0, 'speckle'); TB.slab(room, reg, z1, z1 + 0.2, 'ceiltile', col=False)
    (w0, w1), (e0, e1) = P.SB_LANES
    for zf in (zb1, P.P1):
        for base, d, zb, zt, lane in P.flights(zf):
            TK.stair(room, 'v', base, d, zb, zt, lane, 'speckle', 'steel', fill_to=None, depth=0.45)
            _handrail(room, lane[0], 1, base, d, zb); _handrail(room, lane[1], -1, base, d, zb)
        zh = zf + P.RISERS * P.RISE
        TK.box(room, (S[0] + 0.15, P.SB_NLAND[0], zh - 0.3), (S[1] - 0.15, P.SB_NLAND[1], zh), 'speckle')   # the north half landing
    for zl in (P.P1, P.P2):
        TK.box(room, (S[0] + 0.15, P.SB_SLAND[0], zl - 0.3), (S[1] - 0.15, P.SB_SLAND[1], zl), 'speckle')    # the south landings L1 / L2
    TK.box(room, (P.SB_MIDW[0], P.SB_SLAND[1], z0), (P.SB_MIDW[1], P.SB_NLAND[0], z1), 'block')               # the wall between the lanes
    g = P.SB_SLAND[1]                                                                                          # L2: the west lane's edge
    TK.box(room, (w0, g, P.P2), (w1, g + 0.02, P.P2 + 0.95), 'steel')                                          # the balustrade panel
    TK.box(room, (w0, g - 0.01, P.P2 + 0.95), (w1, g + 0.05, P.P2 + 1.0), 'steel', col=False)                 # its top rail
    for zl in (zb1, P.P1, P.P2): TK.lamp(room, (S[0] + S[1]) / 2, sum(P.SB_SLAND) / 2, zl + ROOM_H, energy=0.6, falloff=6.0, size=(0.9, 0.3))
    return reg
WIN = {}                                                                  # room -> its window / mirror cuts (the wall finishes keep clear)
def _suites(holes):
    """the L2 interview suites (kept as approved): four rooms, the mirror walls (mirror entity + mirror portal on the interview side,
    dark glass + a room-to-room portal on the observation side), the observation rooms dim."""
    F = P.P2; R = {}
    for k, r in P.SUITES.items():
        R[k] = [r]; oth = [(q, 0.1) for kk, q in P.SUITES.items() if kk != k] + [((P.WI, P.LOB_W, -48.93, P.NI_LINK), 0.1), ((P.COR[0], P.COR[1], P.SG, P.NI_LINK), 0.1)]
        cut = holes + _west(k, F, R[k])
        for intr, obs, ax, plane, side in P.MIRROR:
            if k in (intr, obs): cut = cut + [(plane - 0.2, plane + 0.2, P.MIRROR_SPAN[0], P.MIRROR_SPAN[1], P.MIRROR_SPAN[2], P.MIRROR_SPAN[3])]
        WIN[k] = cut
        TB.slab(k, R[k], F - 0.4, F, 'carpet'); TB.slab(k, R[k], F + ROOM_H, F + ROOM_H + 0.2, 'ceiltile', col=False)
        lining(k, R[k], oth, F, F + ROOM_H, 'plaster', cut, P.OL)
        if k.startswith('pint'): TB.lights_grid(k, R[k], F + ROOM_H, 2.4)
        else: TK.lamp(k, (r[0] + r[1]) / 2, (r[2] + r[3]) / 2, F + ROOM_H, energy=0.15, falloff=4.0, size=(0.6, 0.3))
    v0, v1, z0, z1 = P.MIRROR_SPAN
    for intr, obs, ax, plane, side in P.MIRROR:                          # side: the interview room's side of the wall plane (-1: u < plane)
        TK.box(obs, (plane - 0.01, v0, z0), (plane + 0.01, v1, z1), 'obsglass', col=True)                   # the dark glass (collision)
        um = plane + side * 0.115                                         # the mirror panel: 1.5 cm off the interview face of the wall
        TK.prop(intr, P.MIRROR_PROP[0], um, (v0 + v1) / 2, (z0 + z1) / 2, P.mirror_heading(side),                           # its -Y face into the interview room
                scale=((v1 - v0) / P.MIRROR_PROP[1], (z1 - z0) / P.MIRROR_PROP[2]))
        OPS['portals'].append({'from': intr, 'to': 'limbo', 'kind': f'{intr} mirror', 'P': ('u', um, v0, v1, z0, z1, -side), 'flags': 4})
        OPS['portals'].append({'from': obs, 'to': intr, 'kind': f'{obs} glass', 'P': ('u', plane - side * 0.1, v0, v1, z0, z1, side)})
        for a, b, c, d in ((v0 - 0.04, v1 + 0.04, z0 - 0.04, z0), (v0 - 0.04, v1 + 0.04, z1, z1 + 0.04), (v0 - 0.04, v0, z0, z1), (v1, v1 + 0.04, z0, z1)):
            for s_, rm in ((side, intr), (-side, obs)):                   # a steel frame round the opening on both faces
                f0, f1 = sorted((plane + s_ * 0.1, plane + s_ * 0.13))
                TK.box(rm, (f0, a, c), (f1, b, d), 'steel', col=False)
    return R
def export_mirror(out):
    """jc_courts_mirror: a 1 x 1 m panel in the XZ plane facing -Y, centred on its origin, shader mirror_default.sps with white diffuse +
    spec and specularIntensityMult 1 (Rockstar's vw_vwint02_pent_mbt_mirror material; Tower City's tc_prop_mirror, proven in game). Its own
    drawable + archetype: a mirror never reflects the entity holding the surface. Returns its bounds for the ytyp."""
    import bpy
    from mathutils import Vector
    m = TK.create_shader('mirror_default.sps'); m.name = 'JC mirror'; m['preserve_authored_uv'] = True
    w = np.ones((8, 8, 4), np.float32)
    for s_ in ('DiffuseSampler', 'SpecSampler'):
        nd = m.node_tree.nodes.get(s_)
        if nd: nd.image = TK.dds(f'jc_mirror_{s_[:4].lower()}', w, out / 'tex', s_ != 'DiffuseSampler', 'B8G8R8A8_UNORM'); nd.texture_properties.embedded = True
    q = m.node_tree.nodes.get('specularIntensityMult')
    if q: q.set_float(1.0)
    me = bpy.data.meshes.new('mirror_panel'); me.from_pydata([Vector(v) for v in [(-0.5, 0, -0.5), (0.5, 0, -0.5), (0.5, 0, 0.5), (-0.5, 0, 0.5)]], [], [(0, 1, 2, 3)])
    me.materials.append(m); uv = me.uv_layers.new(name='UVMap 0')
    for i, c in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]): uv.data[i].uv = c
    me.update(); assert me.polygons[0].normal.y < -0.99, 'the mirror panel must face -Y'
    o = bpy.data.objects.new('mirror_panel', me); TK.coll().objects.link(o)
    root, lo, hi = TK.K.new_drawable(P.MIRROR_PROP[0], [o], uv=0.5, keep_uv=TK.KEEP); TK._export(root, out)
    return {'bb_lo': [round(v, 4) for v in lo], 'bb_hi': [round(v, 4) for v in hi]}
def _bx(room, axis, n0, n1, a0, a1, z0, z1, mat, col=True):
    """a box given across a wall (n: the wall's normal axis) and along it (the wall finishes keep clear of it)."""
    lo, hi = ((n0, a0, z0), (n1, a1, z1)) if axis == 'u' else ((a0, n0, z0), (a1, n1, z1))
    TK.box(room, lo, hi, mat, col); PF.keep_clear(room, lo, hi)
def counter_cut(axis, plane, a0, a1):
    return (plane - 0.2, plane + 0.2, a0, a1, P.P1 + 0.95, P.P1 + 2.3) if axis == 'u' else (a0, a1, plane - 0.2, plane + 0.2, P.P1 + 0.95, P.P1 + 2.3)
def counter(name, axis, plane, a0, a1):
    """a service window in the wall plane between the public side (plobby, the + side) and pdesk (the - side): the staff counter, its top,
    the public ledge (all wood: the board's warm counter), the pane (collision) and a portal through it."""
    F = P.P1
    _bx('plobby', axis, plane + 0.1, plane + 0.35, a0, a1, F, F + 0.95, 'panel')                  # the public face of the counter (raised wood panels)
    _bx('plobby', axis, plane, plane + 0.35, a0, a1, F + 0.95, F + 1.05, 'plank')                 # the public ledge (wood)
    _bx('pdesk', axis, plane - 0.75, plane - 0.1, a0, a1, F, F + 0.95, 'panel')                   # the staff counter (wood)
    _bx('pdesk', axis, plane - 0.8, plane, a0, a1, F + 0.95, F + 1.05, 'plank')                   # its top (wood)
    _bx('pdesk', axis, plane - 0.03, plane + 0.03, a0, a1, F + 1.05, F + 2.3, 'railglass', col=True)   # the bullet-resistant pane
    OPS['portals'].append({'from': 'plobby', 'to': 'pdesk', 'kind': f'police {name} counter glass', 'P': (axis, plane, a0, a1, F + 1.05, F + 2.3, -1)})
# ---------------- insignia (our own art: jc3_insignia.py) ----------------
INS = {}
def _ins_png(name):
    d = TK.OUT / 'tex' / 'insignia'
    if not INS: subprocess.run([TK.PYPIL, str(Path(__file__).with_name('jc3_insignia.py')), str(d)], check=True); INS['dir'] = d
    return d / f'{name}.png'
def _px(name, opaque):
    import bpy
    im = bpy.data.images.load(str(_ins_png(name))); px = np.array(im.pixels[:], np.float32).reshape(im.size[1], im.size[0], 4)   # bottom-first rows
    bpy.data.images.remove(im)
    if opaque: px[:, :, 3] = 1.0
    return px
def _quad(room, key, pts):
    import bpy
    from mathutils import Vector
    me = bpy.data.meshes.new(key); me.from_pydata([Vector(p) for p in pts], [], [(0, 1, 2, 3)]); me.materials.append(TK.MAT[key])
    uv = me.uv_layers.new(name='UVMap 0')
    for li, q in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))): uv.data[li].uv = q
    o = bpy.data.objects.new(key, me); TK.coll().objects.link(o); TK.PARTS[room].append(o)
def art_panel(room, name, axis, face, side, a, zc, w, h, off=0.065, decal=False):
    """an insignia panel (PNG `name`) w x h centred at a / zc on the wall face `face` (axis u: the plane u = face), readable from the
    `side` (+1: the larger coordinate), `off` in front of the face (clear of the trim bands at 0.035 / 0.048)."""
    key = 'JC3 art ' + name + ('_d' if decal else '')
    if key not in TK.MAT:
        m = TK.tex_mat(key, _px(name, not decal), False, 2.0, 0.15, 'decal.sps' if decal else None); m['preserve_authored_uv'] = True
        TK.KEEP.add(m.name); TK.MAT[key] = m
    s = 1 if side > 0 else -1; n = face + s * off
    if axis == 'u': L, R = (n, a - s * w / 2), (n, a + s * w / 2)                                 # the reader's left / right edge
    else: L, R = (a + s * w / 2, n), (a - s * w / 2, n)
    _quad(room, key, [(*L, zc - h / 2), (*R, zc - h / 2), (*R, zc + h / 2), (*L, zc + h / 2)])
def insignia():
    import jc3_pgarage_build as GB
    for room, name, axis, face, side, a, zc, w, h, off, decal in D.art(): art_panel(room, name, axis, face, side, a, zc, w, h, off, decal)
    for room, name, u, v, size, up, z in D.floor_art(): GB.floor_decal(room, u, v, size, size, up, _px(name, False), f'JC3 floor {name} {room}', z)
# ---------------- door casings (the playbook door tool's casing round every fitted opening) ----------------
MESH_DOORS = {'P_in_pstaff1_cage', 'P_in_pstaff1_arm', 'P_in_pstaff1_armory_gate'}   # (their steel frames are the mesh walls')
def door_casings(R):
    """a navy casing round every police door opening on each face that a police room owns: the wall's faces found from the solids beside
    the jamb, the room from the floor region in front of the face. The roll-ups, the mesh-wall doors and faces onto other buildings are
    left out."""
    import jc3_pgarage as G
    police = {k: v for k, v in R.items() if k in P.KEYS}
    floor = lambda k: P.P1 if k in ('plobby', 'pdesk', 'pstaff1') else (G.ZB if k == 'pdeck' else P.P2)
    for o in JT.OPENINGS:
        if not o['name'].startswith('P_') or o['name'] in MESH_DOORS: continue
        ax, pa, a0, a1, z0 = o['axis'], o['plane'], o['a0'], o['a1'], o['z0']
        k = 0 if ax == 'u' else 1                                        # the strip: only the wall the door stands in, solids <= 0.6 thick across
        strip = [b for b in TK.SOLIDS if (b[0][2] <= z0 + 1.0 <= b[1][2]) and b[1][k] - b[0][k] <= 0.6 and   # its plane (2026-11-11: the
                 ((ax == 'u' and b[0][1] < a0 - 0.005 and b[1][1] > a0 - 0.04 and b[0][0] < pa + 0.6 and b[1][0] > pa - 0.6) or
                  (ax == 'v' and b[0][0] < a0 - 0.005 and b[1][0] > a0 - 0.04 and b[0][1] < pa + 0.6 and b[1][1] > pa - 0.6))]
        # stair's south lining, a wall ACROSS the stair doors' wall, put their casings 2 m out in the shaft: the "diagonal blue rail")
        if not strip: continue
        n0 = min(b[0][k] for b in strip); n1 = max(b[1][k] for b in strip)
        for side, face in ((-1, n0), (1, n1)):
            pt = [0.0, 0.0]; pt[k] = face + side * 0.3; pt[1 - k] = (a0 + a1) / 2
            room = next((r for r, rs in police.items() if _inreg(rs, *pt) and abs(floor(r) - z0) < 1.0 and r not in ('pstair',)), None)
            if room is None and _inreg(police.get('pstair', []), *pt): room = 'pstair'
            if room is None: continue
            for n_0, n_1, b0, b1, c0, c1 in DF.casing(o, face, side):
                lo, hi = [0, 0, c0], [0, 0, c1]; lo[k], hi[k] = n_0, n_1; lo[1 - k], hi[1 - k] = b0, b1
                TK.box(room, tuple(lo), tuple(hi), 'navy', col=False); PF.keep_clear(room, lo, hi)
# ---------------- the rooms ----------------
def build(zb1):
    R = {}; holes = TB.opening_boxes(); WIN.clear()
    LOBBY, NE, SOUTH, HALL, REST = P.REGIONS['plobby']; DESK = P.REGIONS['pdesk'][0]
    staff1 = [(r, 0.1) for rs in P.SPACES1.values() for r in rs]
    # the east colonnade glass: bays north of LOBBY_S open the lobby (full height), the rest the south block (L1) and the L2 east wing
    face = next(f for f in TB.PL.face_list('police') if f[0] == 'E')
    bays = [b for run in TB.PL.arcade_runs('police', face) for b in run]
    gl = [(P.EG - 0.5, P.EG + 0.1, a0, a1, z0, z1) for a0, a1, z0, z1 in bays]
    north = [b for b in bays if b[0] > P.LOBBY_S]; south = [b for b in bays if b[1] < P.LOBBY_S]
    OPS['portals'].append({'from': 'plobby', 'to': 'limbo', 'kind': 'police lobby E glass', 'P': ('u', P.EG - 0.3, min(b[0] for b in north), max(b[1] for b in north), P.P1, north[0][3], 1)})
    OPS['portals'].append({'from': 'plobby', 'to': 'limbo', 'kind': 'police south block E glass', 'P': ('u', P.EG - 0.3, min(b[0] for b in south), max(b[1] for b in south), P.P1, P.P1 + ROOM_H, 1)})
    OPS['portals'].append({'from': 'pstaff2', 'to': 'limbo', 'kind': 'police L2 east wing E glass', 'P': ('u', P.EG - P.OL, min(b[0] for b in south), max(b[1] for b in south), P.P2, P.P2 + ROOM_H, 1)})
    nb = [(a0, a1, z0, z1) for F in (P.P1, P.P2) for a0, a1, z0, z1 in P.north_bays(F)]
    nh = [(a0, a1, P.NI_FACE - 0.5, P.NI_FACE + 0.1, z0, z1) for a0, a1, z0, z1 in nb]
    for a0, a1, z0, z1 in nb: OPS['portals'].append({'from': 'plobby', 'to': 'limbo', 'kind': 'police lobby N window', 'P': ('v', P.NI_FACE - 0.3, a0, a1, z0, z1, 1)})
    cuts = [counter_cut(ax, plane, a0, a1) for _, ax, plane, a0, a1 in P.COUNTERS]
    # the front pair in phase 2's frame (sized POLICE_FRONT_W x 2.4 m round the old pair): the door tool's fillers close it to the leaves
    fo = {'a0': TB.PL.POLICE_FRONT, 'a1': TB.PL.POLICE_FRONT + TB.PL.POLICE_FRONT_W, 'z0': P.P1, 'z1': P.P1 + 2.4}
    ff = JT.pair_fit(TB.PL.POLICE_FRONT, P.P1)
    for a0, a1, z0, z1 in DF.fillers(fo, ff['a0'], ff['a1'], ff['z1']): TK.box('plobby', (P.EG - 0.05, a0, z0), (P.EG + 0.05, a1, z1), 'steel', col=False)   # (no collision: a 10 cm slit's filler, under phase 2's head)
    # ---------------- plobby: the lobby (double height), the public south block, the hall, the public restrooms ----------------
    room = 'plobby'; R[room] = [LOBBY, NE, SOUTH, HALL, REST]; F = P.P1
    oth = [(DESK, 0.1)] + staff1 + [(P.STAIR_B, 0.15)]
    floors(room, P.SPACES_LOBBY, F)
    TB.slab(room, [LOBBY, NE], P.CEIL - 0.2, P.CEIL, 'plaster', col=False); TB.slab(room, [HALL], F + ROOM_H, F + ROOM_H + 0.2, 'plaster', col=False)
    TB.slab(room, [SOUTH, REST], F + ROOM_H, F + ROOM_H + 0.2, 'ceiltile', col=False)
    lining(room, [LOBBY, NE], [(SOUTH, 0.0), (HALL, 0.0), (REST, 0.0)] + oth, F, F + ROOM_H, 'granite', holes + gl + nh + cuts, 0.3)
    lining(room, [SOUTH, HALL, REST], [(LOBBY, 0.0), (NE, 0.0)] + oth, F, F + ROOM_H, 'plaster', holes + gl + cuts, 0.3)
    up = [(r, 0.1) for rs in P.SPACES2.values() for r in rs] + [(HALL, 0.1)]
    lining(room, [LOBBY, NE], up, F + ROOM_H, P.CEIL - 0.2, 'granite', holes + gl + nh, 0.3)
    space_walls(room, P.SPACES_LOBBY, P.OPEN_LOBBY, F, R[room], oth, 0.3, holes, lambda a, b: 'granite' if 'lobby' in (a, b) else 'plaster')
    TB.lights_grid(room, [LOBBY, NE], P.CEIL - 0.2, 5.0); TB.lights_grid(room, [HALL], F + ROOM_H, 4.0)
    for k in ('public corridor', 'victim room A', 'victim room B', 'press room', "men's restroom", "women's restroom"):
        TB.lights_grid(room, P.SPACES_LOBBY[k], F + ROOM_H, 3.0)
    # ---------------- pdesk: front desk, dispatch, watch commander, copy, the property / records windows ----------------
    room = 'pdesk'; R[room] = [DESK]
    oth = [(LOBBY, 0.1), (HALL, 0.1)] + staff1
    floors(room, P.SPACES_DESK, F); TB.slab(room, R[room], F + ROOM_H, F + ROOM_H + 0.2, 'ceiltile', col=False)
    lining(room, R[room], oth, F, F + ROOM_H, 'plaster', holes + cuts, 0.2)
    space_walls(room, P.SPACES_DESK, P.OPEN_DESK, F, R[room], oth, 0.2, holes, lambda a, b: 'plaster')
    for rs in P.SPACES_DESK.values(): TB.lights_grid(room, rs, F + ROOM_H, 3.0)
    for name, ax, plane, a0, a1 in P.COUNTERS: counter(name, ax, plane, a0, a1)
    # ---------------- the stair, the interview suites (kept as approved) ----------------
    R['pstair'] = _stair(holes, zb1)
    R.update(_suites(holes))
    # ---------------- the staff sides ----------------
    for room, F, base, spaces, opens, staff_floor in (('pstaff1', P.P1, P.STAFF1, P.SPACES1, P.OPEN1, 'speckle'), ('pstaff2', P.P2, P.STAFF2, P.SPACES2, P.OPEN2, 'carpet')):
        cut = [P.STAIR_B, DESK] if room == 'pstaff1' else [P.STAIR_B] + list(P.SUITES.values())
        reg = []
        for r in base: reg += TK.rects_minus(*r, cut)
        R[room] = reg
        if room == 'pstaff1': oth = [(P.STAIR_B, 0.15), (DESK, 0.1), (HALL, 0.1), (REST, 0.1), (LOBBY, 0.1), (SOUTH, 0.1)]
        else: oth = [(P.STAIR_B, 0.15), (LOBBY, 0.1), (NE, 0.1)] + [(q, 0.1) for q in P.SUITES.values()]
        win = _west(room, F, reg); extra = gl if room == 'pstaff2' else []; WIN[room] = win + extra
        floors(room, spaces, F, staff_floor); TB.slab(room, reg, F + ROOM_H, F + ROOM_H + 0.2, 'ceiltile', col=False)
        lining(room, reg, oth, F, F + ROOM_H, WALL_MAT[room], holes + win + extra, P.OL)
        mesh = P.MESH1 if room == 'pstaff1' else set()
        space_walls(room, spaces, set(opens) | mesh, F, reg, oth, P.OL, holes, lambda a, b, m=WALL_MAT[room]: m)
        if mesh: mesh_walls(room, spaces, mesh, F, reg, oth, P.OL)
        for rs in spaces.values(): TB.lights_grid(room, rs, F + ROOM_H, 3.2)
    # ---------------- kit (no Rockstar prop for these), props, signs, insignia, door casings, the wall finishes ----------------
    for room, lo, hi, mat, col in D.kit(): TK.box(room, lo, hi, mat, col=col); PF.keep_clear(room, lo, hi)
    for room, m, u, v, z, h in D.dress(): OPS['props'].append((room, m, u, v, z, h))
    for room, c, face, w, h_, lines, name, bg, fg in D.signs(): TK.sign(room, c, face, w, h_, lines, name, bg=bg, fg=fg, emis=False, scale=1.0)
    insignia()
    door_casings(R)
    wins = gl + nh + cuts + [h for c in WIN.values() for h in c]
    PF.build({'plobby': (P.P1, R['plobby'], ROOM_H), 'pdesk': (P.P1, R['pdesk'], ROOM_H), 'pstaff1': (P.P1, R['pstaff1'], ROOM_H),
              'pstaff2': (P.P2, R['pstaff2'], ROOM_H), **{k: (P.P2, R[k], ROOM_H) for k in P.SUITES}}, holes + wins, P.shell_bands, P.SHELL_DEPTHS)
    return R
