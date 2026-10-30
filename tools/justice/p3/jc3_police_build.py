"""Area 3 build (Blender, called by jc3_build.py): the Police HQ's L1 + L2 rooms and its stair B1 - L1 - L2, from jc3_police's numbers,
with jc3_tower_build's helpers (lining by region, slabs, door openings, lights). prepare() registers the doors before any wall is drawn
(the walls take their holes from JT.OPENINGS); build() draws every room and returns the regions. The garage (B1 + the two ramps) is
jc3_pgarage_build.py. Rockstar's recipes as area 2: lobby = the tower lobby's granite / marble; offices = plaster, carpet, ceiling tile;
L1 staff = Mission Row's painted block + speckled floor. Interview suites: the mirror is its own entity (Rockstar's penthouse mirror, scaled)
+ a mirror portal (flags 4); the observation room sees the interview room through dark glass (a room-to-room portal)."""
import tc_kit as TK
import jc3_tower as JT, jc3_police as P
import jc3_tower_build as TB
OPS = TB.OPS
GLASS = (JT.GLASS_L, JT.GLASS_R)
ROOM_H = 2.6                                                              # L1 / L2 rooms' clear height (ceiling slab over it, the next floor's slab over that)
INTO = {'P_desk': -1, 'P_staff': -1, 'P_stairL1': 1, 'P_stairL2': 1, 'P_stairB1': -1, 'P_int1': 1, 'P_obs1': 1, 'P_obs2': 1, 'P_int2': 1}
def prepare():
    """the police doors into JT's lists (TB.build_rooms collects OPS['doors'] / portals from them)."""
    JT.double_door('P_front', 'plobby', 'limbo', 'u', P.EG, P.FRONT[0], P.P1, 1, models=GLASS)
    JT.double_door('P_link', 'plobby', 'galleria', 'v', P.NI_LINK, P.LINK[0], P.P1, 1, models=GLASS)
    for name, frm, to, z, ax, plane, a0, kind in P.PORTAL_DOORS:
        if kind == 'single': JT.single_door(name, frm, to, ax, plane, a0, z, INTO[name])
    for name, z, ax, plane, a0 in P.INNER_DOORS:
        JT.single_door('P_in_' + name, 'pstaff1' if z == P.P1 else 'pstaff2', None, ax, plane, a0, z, 1)
def _space_walls(spaces, open_pairs, F, room, mat, holes):
    """0.2 partitions between a staff side's named spaces, centred on their shared edges, doors cut out (open_pairs meet without one)."""
    done = set(); names = list(spaces)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if (a, b) in open_pairs or (b, a) in open_pairs: continue
            for ra in spaces[a]:
                for rb in spaces[b]:
                    for ax, pa, pb in (('u', ra[1], rb[0]), ('u', ra[0], rb[1]), ('v', ra[3], rb[2]), ('v', ra[2], rb[3])):
                        if abs(pa - pb) > 1e-6: continue
                        lo, hi = ((max(ra[2], rb[2]), min(ra[3], rb[3])) if ax == 'u' else (max(ra[0], rb[0]), min(ra[1], rb[1])))
                        if hi - lo < 0.05 or (ax, round(pa, 3), round(lo, 3)) in done: continue
                        done.add((ax, round(pa, 3), round(lo, 3)))
                        outer = (P.WI, P.EI, P.SG, P.NI_LINK, P.NI_FACE)          # stop at the room's lining (0.2 on the outer lines, 0.1 inside)
                        lo += 0.2 if any(abs(lo - o) < 0.02 for o in outer) else 0.1
                        hi -= 0.2 if any(abs(hi - o) < 0.02 for o in outer) else 0.1
                        box3 = (pa - 0.1, pa + 0.1, lo, hi, F, F + ROOM_H) if ax == 'u' else (lo, hi, pa - 0.1, pa + 0.1, F, F + ROOM_H)
                        for c in TB.box_minus(box3, holes): TK.box(room, (c[0], c[2], c[4]), (c[1], c[3], c[5]), mat)
def _west(room, F, region):
    """the west face's window bays inside this room's region: holes through its outer lining + one limbo portal per region rect."""
    plane = P.WI + P.OL; bs = P.west_bays(F); holes = []
    for r in region:
        if abs(r[0] - P.WI) > 0.02: continue
        ins = [(max(a0, r[2]), min(a1, r[3]), z0, z1) for a0, a1, z0, z1 in bs if min(a1, r[3]) - max(a0, r[2]) > 0.05]
        holes += [(P.WI - 0.01, plane + 0.01, a0, a1, z0, z1) for a0, a1, z0, z1 in ins]
        if ins: OPS['portals'].append({'from': room, 'to': 'limbo', 'kind': f'{room} W windows', 'P': ('u', plane, min(i[0] for i in ins), max(i[1] for i in ins), ins[0][2], ins[0][3], -1)})
    return holes
def _stair(holes, zb1):
    """the police stair: one room from B1 (zb1) to L2, lanes along v, the south landing of each floor, the north half landings."""
    room = 'pstair'; S = P.STAIR_B; z0, z1 = zb1, P.P2 + ROOM_H; reg = [S]
    TB.lining(room, reg, [], z0, z1, 'block', holes, ext_t=0.15, int_t=0.15)
    TB.slab(room, reg, z0 - 0.4, z0, 'speckle'); TB.slab(room, reg, z1, z1 + 0.2, 'ceiltile', col=False)
    for zf in (zb1, P.P1):
        for base, d, zb, zt, lane in P.flights(zf):
            TK.stair(room, 'v', base, d, zb, zt, lane, 'speckle', 'steel', fill_to=None, depth=0.45)
        zh = zf + P.RISERS * P.RISE
        TK.box(room, (S[0] + 0.15, P.SB_NLAND[0], zh - 0.3), (S[1] - 0.15, P.SB_NLAND[1], zh), 'speckle')   # the north half landing
    for zl in (P.P1, P.P2):
        TK.box(room, (S[0] + 0.15, P.SB_SLAND[0], zl - 0.3), (S[1] - 0.15, P.SB_SLAND[1], zl), 'speckle')    # the south landings L1 / L2
    TK.box(room, (P.SB_MIDW[0], P.SB_SLAND[1], z0), (P.SB_MIDW[1], P.SB_NLAND[0], z1), 'block')               # the wall between the lanes
    for zl in (zb1, P.P1, P.P2): TK.lamp(room, (S[0] + S[1]) / 2, sum(P.SB_SLAND) / 2, zl + ROOM_H, energy=0.6, falloff=6.0, size=(0.9, 0.3))
    return reg
def _suites(holes):
    """the L2 interview suites: four rooms, the mirror walls (mirror entity + mirror portal on the interview side, dark glass + a
    room-to-room portal on the observation side), the observation rooms dim."""
    F = P.P2; R = {}
    for k, r in P.SUITES.items():
        R[k] = [r]; oth = [(q, 0.1) for kk, q in P.SUITES.items() if kk != k] + [((P.WI, P.LOB_W, -48.93, P.NI_LINK), 0.1), ((P.COR[0], P.COR[1], P.SG, P.NI_LINK), 0.1)]
        cut = holes + _west(k, F, R[k])
        for intr, obs, ax, plane, side in P.MIRROR:
            if k in (intr, obs): cut = cut + [(plane - 0.2, plane + 0.2, P.MIRROR_SPAN[0], P.MIRROR_SPAN[1], P.MIRROR_SPAN[2], P.MIRROR_SPAN[3])]
        TB.slab(k, R[k], F - 0.4, F, 'carpet'); TB.slab(k, R[k], F + ROOM_H, F + ROOM_H + 0.2, 'ceiltile', col=False)
        TB.lining(k, R[k], oth, F, F + ROOM_H, 'plaster', cut, ext_t=P.OL, int_t=0.1)
        if k.startswith('pint'): TB.lights_grid(k, R[k], F + ROOM_H, 2.4)
        else: TK.lamp(k, (r[0] + r[1]) / 2, (r[2] + r[3]) / 2, F + ROOM_H, energy=0.15, falloff=4.0, size=(0.6, 0.3))
    v0, v1, z0, z1 = P.MIRROR_SPAN
    for intr, obs, ax, plane, side in P.MIRROR:                          # side: the interview room's side of the wall plane (-1: u < plane)
        TK.box(obs, (plane - 0.01, v0, z0), (plane + 0.01, v1, z1), 'obsglass', col=True)                   # the dark glass (collision)
        um = plane + side * 0.115                                         # the mirror panel: 1.5 cm off the interview face of the wall
        TK.prop(intr, P.MIRROR_PROP[0], um, (v0 + v1) / 2, (z0 + z1) / 2, 0.0 if side > 0 else 180.0,                  # its +x into the interview room
                scale=((v1 - v0) / P.MIRROR_PROP[1], (z1 - z0) / P.MIRROR_PROP[2]))
        OPS['portals'].append({'from': intr, 'to': 'limbo', 'kind': f'{intr} mirror', 'P': ('u', um, v0, v1, z0, z1, -side), 'flags': 4})
        OPS['portals'].append({'from': obs, 'to': intr, 'kind': f'{obs} glass', 'P': ('u', plane - side * 0.1, v0, v1, z0, z1, side)})
        for a, b, c, d in ((v0 - 0.04, v1 + 0.04, z0 - 0.04, z0), (v0 - 0.04, v1 + 0.04, z1, z1 + 0.04), (v0 - 0.04, v0, z0, z1), (v1, v1 + 0.04, z0, z1)):
            for s_, rm in ((side, intr), (-side, obs)):                   # a steel frame round the opening on both faces
                f0, f1 = sorted((plane + s_ * 0.1, plane + s_ * 0.13))
                TK.box(rm, (f0, a, c), (f1, b, d), 'steel', col=False)
    return R
def build(zb1):
    R = {}; holes = TB.opening_boxes()
    # ---------------- the public lobby ----------------
    room = 'plobby'; R1, NE, HALL = P.REGIONS['plobby']; R[room] = [R1, NE, HALL]
    c0, c1 = P.COUNTER; CUT = (P.LOB_W - 0.2, P.LOB_W + 0.2, c0, c1, P.P1 + 0.95, P.P1 + 2.3)   # the counter window through both linings
    staff = [(r, 0.1) for rs in P.SPACES1.values() for r in rs] + [(P.STAIR_B, 0.15)]
    oth_low = [((P.DESK_W, P.LOB_W, P.DESK_S, P.HALL_S), 0.1)] + staff
    gl = []                                                               # the east glass runs: holes + limbo portals (on the lining's room face)
    for run in TB.PL.arcade_runs('police', next(f for f in TB.PL.face_list('police') if f[0] == 'E')):
        a0, a1, z0, z1 = run[0][0], run[-1][1], run[0][2], run[0][3]
        gl.append((P.EG - 0.5, P.EG + 0.1, a0, a1, z0, z1))
        # one portal over the whole run on the lining's room face, the doorway included (two planes - this and the door's - let rays slip
        # between them at the doorway's edges; the front pair stands 0.3 m beyond it on its own portal)
        OPS['portals'].append({'from': room, 'to': 'limbo', 'kind': 'police lobby E glass', 'P': ('u', P.EG - 0.3, a0, a1, P.P1, z1, 1)})
    nb = [(a0, a1, z0, z1) for F in (P.P1, P.P2) for a0, a1, z0, z1 in P.north_bays(F)]
    nh = [(a0, a1, P.NI_FACE - 0.5, P.NI_FACE + 0.1, z0, z1) for a0, a1, z0, z1 in nb]
    for a0, a1, z0, z1 in nb: OPS['portals'].append({'from': room, 'to': 'limbo', 'kind': 'police lobby N window', 'P': ('v', P.NI_FACE - 0.3, a0, a1, z0, z1, 1)})
    TB.slab(room, R[room], P.P1 - 0.4, P.P1, 'marble')
    TB.slab(room, [R1, NE], P.CEIL - 0.2, P.CEIL, 'plaster', col=False); TB.slab(room, [HALL], P.P1 + ROOM_H, P.P1 + ROOM_H + 0.2, 'plaster', col=False)
    TB.lining(room, R[room], oth_low, P.P1, P.P1 + ROOM_H, 'granite', holes + gl + nh + [CUT], ext_t=0.3, int_t=0.1)
    up = [(r, 0.1) for rs in P.SPACES2.values() for r in rs] + [(HALL, 0.1)]
    TB.lining(room, [R1, NE], up, P.P1 + ROOM_H, P.CEIL - 0.2, 'granite', holes + gl + nh, ext_t=0.3, int_t=0.1)
    TB.lights_grid(room, [R1, NE], P.CEIL - 0.2, 5.0); TB.lights_grid(room, [HALL], P.P1 + ROOM_H, 4.0)
    OPS['portals'].append({'from': room, 'to': 'pdesk', 'kind': 'police counter glass', 'P': ('u', P.LOB_W, c0, c1, P.P1 + 1.05, P.P1 + 2.3, -1)})
    TK.box(room, (P.LOB_W + 0.1, c0, P.P1), (P.LOB_W + 0.35, c1, P.P1 + 0.95), 'granite')                     # the lobby side of the counter
    # ---------------- the desk office ----------------
    room = 'pdesk'; R[room] = P.REGIONS['pdesk']
    TB.slab(room, R[room], P.P1 - 0.4, P.P1, 'speckle'); TB.slab(room, R[room], P.P1 + ROOM_H, P.P1 + ROOM_H + 0.2, 'ceiltile', col=False)
    TB.lining(room, R[room], [((P.LOB_W, P.EG, P.GAR_N, -9.1), 0.1), (HALL, 0.1)] + staff, P.P1, P.P1 + ROOM_H, 'plaster', holes + [CUT])
    TK.box(room, (P.LOB_W - 0.75, c0, P.P1), (P.LOB_W - 0.1, c1, P.P1 + 0.95), 'panel')                       # the counter (desk side)
    TK.box(room, (P.LOB_W - 0.8, c0, P.P1 + 0.95), (P.LOB_W, c1, P.P1 + 1.05), 'granite')                     # its top (desk side of the wall plane)
    TK.box('plobby', (P.LOB_W, c0, P.P1 + 0.95), (P.LOB_W + 0.35, c1, P.P1 + 1.05), 'granite')                # the lobby's ledge (the lobby draws it)
    TK.box(room, (P.LOB_W - 0.03, c0, P.P1 + 1.05), (P.LOB_W + 0.03, c1, P.P1 + 2.3), 'railglass', col=True) # the bullet-resistant pane
    TB.lights_grid(room, R[room], P.P1 + ROOM_H, 3.2)
    # ---------------- the stair, the staff sides, the interview suites ----------------
    R['pstair'] = _stair(holes, zb1)
    R.update(_suites(holes))
    for room, F, base, spaces, opens, flo, wal in (('pstaff1', P.P1, P.STAFF1, P.SPACES1, P.OPEN1, 'speckle', 'block'),
                                                   ('pstaff2', P.P2, P.STAFF2, P.SPACES2, P.OPEN2, 'carpet', 'plaster')):
        cut = [P.STAIR_B, P.REGIONS['pdesk'][0]] if room == 'pstaff1' else [P.STAIR_B] + list(P.SUITES.values())
        reg = []
        for r in base: reg += TK.rects_minus(*r, cut)
        R[room] = reg
        if room == 'pstaff1': oth = [(P.STAIR_B, 0.15), (P.REGIONS['pdesk'][0], 0.1), (HALL, 0.1), (R1, 0.1)]
        else: oth = [(P.STAIR_B, 0.15), (R1, 0.1)] + [(q, 0.1) for q in P.SUITES.values()]
        win = _west(room, F, reg)
        TB.slab(room, reg, F - 0.4, F, flo); TB.slab(room, reg, F + ROOM_H, F + ROOM_H + 0.2, 'ceiltile', col=False)
        TB.lining(room, reg, oth, F, F + ROOM_H, wal, holes + win, ext_t=P.OL, int_t=0.1)
        _space_walls(spaces, opens, F, room, wal, holes)
        TB.lights_grid(room, reg, F + ROOM_H, 3.6)
    for room, m, u, v, z, h in P.furniture(): OPS['props'].append((room, m, u, v, z, h))
    return R
