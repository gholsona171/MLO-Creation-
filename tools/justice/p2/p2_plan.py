"""Justice Center phase 2: the exterior shells, as numbers (pure Python: Blender, the LOD baker, the meta writers and the gates all
import this one module, so the drawings can't drift). Lot frame of work/jc_frame.py: u towards Innocence Blvd, v towards Davis Ave,
z = world z. Plan v1 (survey/fit_v1.md, survey/v1_outlines.json): the real OSM layout at 0.73, ground floors z 28.8.
A building = an axis-aligned box (u0, u1, v0, v1) with floor levels; its facade = per FACE a list of OPENINGS (kind, s0, s1, z0, z1)
in face coordinates (s = the lot coordinate along the face, z absolute) + COVERED rects (where a neighbour or a skybridge stands
against it: nothing is built there). The stone of a face is the face rect minus openings minus covered (tc_kit.rects_minus).
Faces: 'E' plane u = u1 (s = v), 'W' u = u0, 'N' plane v = v1 (s = u), 'S' v = v0. N / S faces own the corners (E / W faces stop
DEPTH short of them), so two faces never share a corner block.
Phase 3 hooks: SEE_OUT[building] = set of levels that get an MLO room behind the glass. Their bays then get NO backing box and the
hull leaves that floor band open (the MLO's own collision takes over); MLO_BUILT['atrium'] drops the atrium placeholder core."""
import math, hashlib
G = 28.8                                      # every ground floor
SLAB = 28.29                                  # the lot slab (jc_frame.slab_z: 28.24 - 28.43, 28.29 at every door)
SEE_OUT = {'tower': {1, 2, 3, 5}, 'police': {1, 2}, 'jail1': set(), 'jail2': set(), 'atrium': {1, 2, 3, 4}}   # police: area 3 (L1, L2)  # phase 3: the atrium galleria MLO (jc_courts)
MLO_BUILT = {'atrium': True, 'sallyport': True, 'police_in': True, 'police_out': True}   # police_in / _out: area 3's garage ramps (jc3_pgarage)     # sallyport: jc_jail's MLO brings the bay (jc-jail, jj_hooks.SALLY_BUILT)
BACK = 1.2                                    # the dark backing panel behind the glass of a shell bay
def levels(z0, heights):
    out = []; z = z0
    for h in heights: out.append(round(z, 4)); z += h
    return out, round(z, 4)
# ---------------- the buildings ----------------
TOWER_LOW = 3.6                               # L1..L7 (the lobby, the two courtroom floors, chambers): 18 risers of 0.20 per storey, so
                                              # the tower's stair works at Rockstar's 0.20 / 0.27 (phase 3: fix the levels, never the risers)
TOWER_FT = (122.2 - G - 7 * TOWER_LOW) / 19   # 3.5895: the shell floors above take the rest (roof stays 122.2)
JAIL1_L1 = 6.0                                # Antonio: Jail I's ground floor is double height (the sally port + booking)
B = {
 'tower':  dict(name='Courts Tower', box=(13.7, 50.6, 17.3, 56.3), floors=levels(G, [TOWER_LOW] * 7 + [TOWER_FT] * 19), depth=0.45, roof=122.2, parapet=1.3),
 'police': dict(name='Police HQ', box=(10.1, 45.1, -59.6, -7.2), floors=levels(G, [3.2] * 9), depth=0.45, roof=57.6, parapet=1.2),
 'jail1':  dict(name='Jail I', box=(-45.0, -8.5, -7.0, 63.6), floors=levels(G, [JAIL1_L1] + [(59.5 - G - JAIL1_L1) / 9] * 9), depth=0.55, roof=59.5, parapet=1.2),
 'jail2':  dict(name='Jail II', box=(-43.1, -4.8, -57.4, -24.5), floors=levels(G, [(57.7 - G) / 11] * 11), depth=0.3, roof=57.7, parapet=1.0),
 'atrium': dict(name='Atrium', box=None, rects=[(-8.5, 37.9, -7.2, 17.3), (-8.5, 13.7, 17.3, 49.6)], floors=levels(G, [3.575] * 4), depth=0.3, roof=43.1, parapet=0.8),
}
for k, b in B.items(): b['levels'], _ = b['floors']; b['top'] = b['roof'] + b['parapet']
# skybridges (Wikipedia: enclosed walkways Jail I - Jail II and police HQ - Jail II, positions estimated): (u0, u1, v0, v1, z0, z1)
BRIDGES = {'b_jail': (-28.0, -24.0, -24.5, -7.0, 34.8, 38.8), 'b_police': (-4.8, 10.1, -44.0, -40.0, 34.8, 38.8)}
BRIDGE_DEPTH = 0.6                             # each end runs this far into the building it joins (closes the hole in its face)
# ---------------- vehicle bays (Rockstar's dropped kerbs re-used: survey drawn_before profile, OUTSTANDING) ----------------
# sally port: Macdonald St dropped kerb at v 13..19 -> a door in Jail I's west face; police garage: Innocence Blvd drop at v -50..-46.
GARAGE_DOOR = ('prop_hw1_03_gardoor_01', 6.22, 4.37)              # vanilla roll-up (doc 06): opening = door + 10 cm
SALLY = dict(face=('jail1', 'W'), s=(12.84, 19.16), z0=SLAB + 0.05, z1=SLAB + 0.05 + 4.47, room=(-45.0, -26.0, 8.0, 24.0), ceil=34.3)
def _p3(name):
    """one of phase 3's plan modules (work/p3), loaded by path (its numbers decide the police HQ's doors and voids)."""
    import importlib, sys as _s
    from pathlib import Path
    p = str(Path(__file__).resolve().parent.parent / 'p3')
    if p not in _s.path: _s.path.insert(0, p)
    return importlib.import_module(name)
PGARAGE = dict(face=('police', 'E'), z0=SLAB + 0.05, ceil=31.6)          # area 3: the B1 garage's two roll-up doors (phase 3: jc3_pgarage reads these)
POLICE_ROLLUP = ('prop_gar_door_05', 3.38, 3.28)                           # Rockstar's 3.38 x 3.28 m roll-up: its top (31.62) stays under L2's floor (32.0)
POLICE_DOOR_C = {'in': -54.5, 'out': -49.6}                               # door / lane centres (v): IN south, OUT north, a 1.4 m pier between
def _pg(k):
    c = POLICE_DOOR_C[k]; w = POLICE_ROLLUP[1] + 0.1                          # the opening: the door + 10 cm (doc 06)
    return dict(PGARAGE, s=(c - w / 2, c + w / 2), z1=PGARAGE['z0'] + POLICE_ROLLUP[2], room=(30.0, 45.1, c - w / 2, c + w / 2))   # room = the opening (a wider one left hull strips)
GARAGES = {'sallyport': SALLY, 'police_in': _pg('in'), 'police_out': _pg('out')}   # room = (u0, u1, v0, v1) of the bay behind the door (to the face)
SLAB_HOLES = [B['police']['box']]                                         # p1's lot slab is cut here: area 3's B1 + ramps run below its height (28.3)
POLICE_FRONT = -25.88                                                      # area 3: the front pair in the east colonnade glass (a0 along v; bay -26.15 .. -22.91)
POLICE_FRONT_W = 2 * 1.30 + 2 * 0.05
# ---------------- faces ----------------
FACES = ('N', 'S', 'E', 'W')
def rects(k):
    b = B[k]; return b['rects'] if b.get('rects') else [b['box']]
def face_list(k):
    """[(face id, plane at, axis 'u'|'v', s0, s1, out sign)] for every outer face of building k (the atrium's L too)."""
    out = []
    for i, (u0, u1, v0, v1) in enumerate(rects(k)):
        d = B[k]['depth']
        for f, at, ax, s0, s1, o in (('N', v1, 'v', u0, u1, 1), ('S', v0, 'v', u0, u1, -1), ('E', u1, 'u', v0 + d, v1 - d, 1), ('W', u0, 'u', v0 + d, v1 - d, -1)):
            out.append((f'{f}{i}' if len(rects(k)) > 1 else f, at, ax, s0, s1, o))
    return out
def P(face, s, d, z):
    """face coordinates -> lot (u, v, z): s along the face, d out of it (+ = outside)."""
    _, at, ax, _, _, o = face
    return (at + o * d, s, z) if ax == 'u' else (s, at + o * d, z)
def overlap(a0, a1, b0, b1): return min(a1, b1) - max(a0, b0)
def covered(k, face):
    """rects (s0, s1, z0, z1) of this face that another building or a skybridge stands against (nothing is built there)."""
    _, at, ax, s0, s1, o = face; out = []
    for j in B:
        if j == k: continue
        for (u0, u1, v0, v1) in rects(j):
            lo, hi = (u0, u1) if ax == 'u' else (v0, v1); a0, a1 = (v0, v1) if ax == 'u' else (u0, u1)
            if (abs(lo - at) < 0.3 or abs(hi - at) < 0.3) and overlap(a0, a1, s0, s1) > 0.1:
                out.append((max(a0, s0), min(a1, s1), G - 1.0, B[j]['roof'] if B[j]['top'] < B[k]['top'] else B[k]['top'] + 1))
    for n, (u0, u1, v0, v1, z0, z1) in BRIDGES.items():
        lo, hi = (u0, u1) if ax == 'u' else (v0, v1); a0, a1 = (v0, v1) if ax == 'u' else (u0, u1)
        if (abs(lo - at) < 0.3 or abs(hi - at) < 0.3) and overlap(a0, a1, s0, s1) > 0.1: out.append((a0, a1, z0, z1))
    # the atrium's inner faces (between its two rects) are not faces at all
    if k == 'atrium':
        for (u0, u1, v0, v1) in rects(k):
            lo, hi = (u0, u1) if ax == 'u' else (v0, v1); a0, a1 = (v0, v1) if ax == 'u' else (u0, u1)
            if ((abs(lo - at) < 0.01 and o > 0) or (abs(hi - at) < 0.01 and o < 0)) and overlap(a0, a1, s0, s1) > 0.1:
                out.append((max(a0, s0), min(a1, s1), G - 1.0, B[k]['top'] + 1))
    return out
def corner_ext(k, face):
    """(e0, e1): how far an E / W face's stone runs on past its ends. N / S faces own the corners - but where the N / S face is covered
    at that corner (a neighbour stands against it), nobody built the 0.3 x 0.3 corner column (the atrium's SE corner against the police
    HQ: an open notch from the slab to the roof, found by the ground check). Then the E / W face takes the corner."""
    f, at, ax, s0, s1, o = face
    if ax != 'u': return (0.0, 0.0)
    i = int(f[1:]) if len(f) > 1 else 0; FL = face_list(k); d = B[k]['depth']; out = []
    for side, s_ in (('S', s0), ('N', s1)):
        pf = next(q for q in FL[4 * i:4 * i + 4] if q[0][0] == side)
        zs = (G + 0.5, (G + B[k]['roof']) / 2, B[k]['roof'] - 0.5, B[k]['top'] - 0.1)                  # covered over its whole height only
        own = exposed_at(k, face, min(max(s_, s0 + 1e-3), s1 - 1e-3), G + 0.5)                       # (and this face is built there)
        out.append(d if own and not any(exposed_at(k, pf, at - o * 0.01, z) for z in zs) else 0.0)
    return tuple(out)
def exposed_at(k, face, s, z):
    return not any(a <= s <= b and c <= z <= d for a, b, c, d in covered(k, face))
def grid(s0, s1, corner, bay, fin):
    """bay centres between two solid corner piers: an integer number of bays of about `bay` m, `fin` m stone between them.
    Returns [(a0, a1)] window spans."""
    inner = (s1 - s0) - 2 * corner; n = max(1, round((inner + fin) / (bay + fin))); w = (inner - (n - 1) * fin) / n
    return [(s0 + corner + i * (w + fin), s0 + corner + i * (w + fin) + w) for i in range(n)]
def lit(*key, rate=0.28):
    """deterministic night pattern: is this shell bay lit at night (Rockstar's *_emissive look)."""
    h = int(hashlib.md5(repr(key).encode()).hexdigest()[:8], 16); return (h % 1000) / 1000.0 < rate
# ---------------- the facades: openings per building and face ----------------
def openings(k, face):
    """[(kind, s0, s1, z0, z1)]. kinds: 'win' (glass + backing box), 'ribbon' (long glass band, mullions), 'arcade' (the open
    colonnade bay: glass wall ARC_BACK m behind), 'slot' (Jail I louvre slot, no glass), 'vent' (black louvre band), 'punch'
    (Jail II small window), 'curtain' (atrium glass wall), 'door' (an atrium entrance: the MLO's native leaves stand in it),
    'garage' (a vehicle bay door opening)."""
    b = B[k]; f, at, ax, s0, s1, o = face; L = b['levels']; out = []
    s0f, s1f = (s0 - b['depth'], s1 + b['depth']) if ax == 'u' else (s0, s1)     # the full face (corners included)
    def add(kind, a0, a1, z0, z1):
        if all(not (overlap(a0, a1, c0, c1) > 0 and overlap(z0, z1, d0, d1) > 0) for c0, c1, d0, d1 in covered(k, face)): out.append((kind, a0, a1, z0, z1))
    if k == 'tower':
        bays = grid(s0f, s1f, 4.0, 7.2, 0.7)
        for i, z in enumerate(L):
            lvl = i + 1
            for a0, a1 in bays:
                if lvl <= 2: continue
                if lvl == 26: add('win', a0, a1, z + 0.55, z + 3.05)                         # the mechanical floor: taller openings
                else: add('win', a0, a1, z + 0.95, z + 2.45)
        for a0, a1 in arcade_bays(k, face): add('arcade', a0, a1, G, L[2] - 0.95)
    elif k == 'police':
        bays = grid(s0f, s1f, 2.2, 3.6, 0.8)
        for i, z in enumerate(L):
            lvl = i + 1
            if lvl <= 2 and arcade_bays(k, face): continue
            if lvl == 3: add('ribbon', s0f + 2.2, s1f - 2.2, z + 0.9, z + 2.5); continue      # the bronze ribbon over the base
            for a0, a1 in bays: add('win', a0, a1, z + 0.85, z + 2.55)
        for a0, a1 in arcade_bays(k, face): add('arcade', a0, a1, G, L[2] - 0.6)
    elif k == 'jail1':
        bays = grid(s0f, s1f, 4.4, 5.4, 1.2)
        for i, z in enumerate(L):
            lvl = i + 1
            if lvl == 2: add('ribbon', s0f + 4.4, s1f - 4.4, z + 0.55, z + 1.25)                # the thin dark glass strip
            elif lvl == 3:
                for a0, a1 in bays: add('vent', a0 + 0.3, a1 - 0.3, z + 0.35, z + 2.35)        # the black ventilation louvre band
            elif lvl >= 4:
                for a0, a1 in bays: add('slot', a0 + 0.5, a1 - 0.5, z + 1.05, z + 1.55)        # the slot louvres (no glass)
        for a0, a1 in arcade_bays(k, face): add('arcade', a0, a1, G, L[1] - 0.5)
    elif k == 'jail2':
        for i, z in enumerate(L):
            lvl = i + 1
            if lvl <= 2:
                if lvl == 1: add('ribbon', s0f + 1.8, s1f - 1.8, z + 0.9, z + 2.1)
                continue
            n = int((s1f - s0f - 2.4) // 2.4); x0 = (s0f + s1f) / 2 - n * 1.2
            mid = (s0f + s1f) / 2
            for j in range(n):
                c = x0 + 1.2 + 2.4 * j
                if abs(c - mid) < 2.0: continue                                             # the central slot stack
                add('punch', c - 0.3, c + 0.3, z + 0.95, z + 1.75)
            add('vent', mid - 1.0, mid + 1.0, z + 1.2, z + 1.55)
    elif k == 'atrium':
        sp = 1.5; n = max(1, round((s1f - s0f - 1.2) / sp)); w = (s1f - s0f - 1.2) / n
        doors = ATRIUM_DOORS.get(f, {})
        dbays = {j for pair in doors.values() for j in pair}
        for j in range(n):
            a0, a1 = s0f + 0.6 + j * w, s0f + 0.6 + (j + 1) * w
            if any(overlap(a0, a1, c0, c1) > 0 for c0, c1 in ATRIUM_SOLID.get(f, ())): continue          # a site wall joins here: stone bay
            add('curtain', a0, a1, ATRIUM_DOOR_TOP + ATRIUM_DOOR_HEAD if j in dbays else G, b['roof'] - 0.6)   # over a door: glass from its head up
        for name, (j0, j1) in doors.items():                                                          # phase 3 entrances: native doors (MLO)
            add('door', s0f + 0.6 + j0 * w, s0f + 0.6 + (j1 + 1) * w, G, ATRIUM_DOOR_TOP)
    for gk, gd in GARAGES.items():
        if (k, face[0]) == gd['face']:
            out = [o_ for o_ in out if not (overlap(o_[1], o_[2], *gd['s']) > -0.6 and o_[3] < gd['z1'] + 0.3)]
            out.append(('garage', gd['s'][0], gd['s'][1], gd['z0'], gd['z1']))
    return out
# the galleria's entrances (phase 3, jc3_plan reads these): curtain bay pairs of the atrium's east face that become door openings for two
# native 1.30 m leaves (v_ilev_ph_door01 / 002, 2.30 high); the opening is the door's top + 10 cm (playbook 07), a steel head over it
# where a site wall runs into the atrium's curtain wall the bay it meets is stone, so the wall ends on solid granite (rig 2026-10-28:
# the secure yard's east wall stopped 15 cm in front of a pane, mid-bay, and read through the glass from the galleria). (s0, s1) of the
# wall per face; p2_site asserts every yard wall that reaches the atrium lies inside one of these.
ATRIUM_SOLID = {'S0': [(-4.8, -4.2)]}
ATRIUM_DOORS = {'E0': {'entry': (5, 6), 'exit': (9, 10)}}
ATRIUM_DOOR_TOP = G + 2.30 + 0.10
ATRIUM_DOOR_HEAD = 0.12
ARC_BACK = 3.0                                 # the colonnade's glass wall stands this far behind the face
def arcade_bays(k, face):
    """the open colonnade bays at street level (the real buildings stand on square granite piers): towers / police on their
    exposed public faces, Jail I on every exposed face. A bay is open only where the face is exposed from the ground up."""
    b = B[k]; f, at, ax, s0, s1, o = face
    s0f, s1f = (s0 - b['depth'], s1 + b['depth']) if ax == 'u' else (s0, s1)
    want = {'tower': ('E', 'N', 'S', 'W'), 'police': ('E', 'S'), 'jail1': ('W', 'N', 'S', 'E')}.get(k, ())
    if f not in want: return []
    if k == 'tower': bays = grid(s0f, s1f, 4.0, 7.2, 0.7); pier = 1.4
    elif k == 'police': bays = grid(s0f, s1f, 2.2, 3.6, 0.8); pier = 1.2
    else: bays = grid(s0f, s1f, 4.4, 5.4, 1.2); pier = 1.4
    out = []
    gar = [room_span(gd) for gd in GARAGES.values() if gd['face'] == (k, f)]
    for a0, a1 in bays:
        if any(overlap(a0, a1, g0 - 0.8, g1 + 0.8) > 0 for g0, g1 in gar): continue
        c0, c1 = a0 + (pier - (0.7 if k == 'tower' else 0.8 if k == 'police' else 1.2)) / 2, a1 - (pier - (0.7 if k == 'tower' else 0.8 if k == 'police' else 1.2)) / 2
        if exposed_at(k, face, (c0 + c1) / 2, G + 0.5) and exposed_at(k, face, c0 + 0.1, G + 0.5) and exposed_at(k, face, c1 - 0.1, G + 0.5): out.append((c0, c1))
    return out
def room_span(gd):
    """a vehicle bay's extent along its face (no colonnade bay may reach into it)."""
    u0, u1, v0, v1 = gd['room']; return (v0, v1) if gd['face'][1] in ('E', 'W') else (u0, u1)
def fins(k, face):
    """vertical ribs standing proud of the face: [(s0, s1, z0, z1, proud)]. Tower: thin granite fins between the bays + the
    corner edges; police: the frame grid's piers; Jail I: the stepped bay frames."""
    b = B[k]; f, at, ax, s0, s1, o = face; out = []
    s0f, s1f = (s0 - b['depth'], s1 + b['depth']) if ax == 'u' else (s0, s1)
    if k == 'tower': bays, fw, pr, zb = grid(s0f, s1f, 4.0, 7.2, 0.7), 0.35, 0.25, b['levels'][2] - 0.95
    elif k == 'police': bays, fw, pr, zb = grid(s0f, s1f, 2.2, 3.6, 0.8), 0.8, 0.3, b['levels'][3]
    elif k == 'jail1': bays, fw, pr, zb = grid(s0f, s1f, 4.4, 5.4, 1.2), 1.2, 0.4, b['levels'][3]
    else: return []
    for (a0, a1), (c0, c1) in zip(bays, bays[1:]):
        m = (a1 + c0) / 2
        segs = [(zb, b['top'])]
        for cs0, cs1, cz0, cz1 in covered(k, face):
            if cs0 - 0.1 <= m <= cs1 + 0.1: segs = [(max(z0, cz1), z1) for z0, z1 in segs if z1 > cz1]
        for z0, z1 in segs:
            if z1 - z0 > 0.5: out.append((m - fw / 2, m + fw / 2, z0, z1, pr))
    return out
# ---------------- the hull: collision on everything (no walking through walls, no climbing into the shell) ----------------
def hull(k):
    """collision boxes (u0, u1, v0, v1, z0, z1) in the lot frame: the building's mass from under the slab to the roof, its parapet
    ring to the parapet top, the colonnade bays cut back to their glass wall. Floors in SEE_OUT are left to the MLO (phase 3)."""
    b = B[k]; out = []; FL = face_list(k)
    for i, (u0, u1, v0, v1) in enumerate(rects(k)):
        out.append((u0, u1, v0, v1, G - 1.0, b['roof']))
        t = 0.3
        for face, r in zip(FL[4 * i:4 * i + 4], ((u0, u1, v1 - t, v1), (u0, u1, v0, v0 + t), (u1 - t, u1, v0 + t, v1 - t), (u0, u0 + t, v0 + t, v1 - t))):
            # the parapet ring only where a parapet is drawn: on a face exposed at the roof (not an inner split of an L, not against a
            # taller neighbour - an invisible 0.8 m ledge there, found by the ground check once the atrium's MLO floor was tested)
            ax = face[2]; a0, a1 = (r[2], r[3]) if ax == 'u' else (r[0], r[1]); e0, e1 = corner_ext(k, face); a0 -= e0; a1 += e1; n = max(1, int(round((a1 - a0) / 0.1))); run = None
            for j in range(n + 1):                                       # the exposed runs along the face, 0.1 m steps
                sj = a0 + (a1 - a0) * min(j + 0.5, n) / n if j < n else None
                if sj is not None and exposed_at(k, face, min(max(sj, face[3] + 1e-3), face[4] - 1e-3), b['roof'] + 0.2):   # (a corner: as the face's end)
                    run = [a0 + (a1 - a0) * j / n, a0 + (a1 - a0) * (j + 1) / n] if run is None else [run[0], a0 + (a1 - a0) * (j + 1) / n]
                elif run is not None:
                    out.append(((r[0], r[1], run[0], run[1]) if ax == 'u' else (run[0], run[1], r[2], r[3])) + (b['roof'], b['top'])); run = None
    return out
# The tower's interior volumes (phase 3: jc3_tower.py builds into exactly these; the hull keeps everything else, so the facade's
# stone, the strips behind the colonnade's end piers and the shell floors keep their collision). Lot rects + z bands.
TOWER_IN = dict(u0=13.7 + 0.45, u1=50.6 - 0.45, v0=17.3 + 0.45, v1=56.3 - 0.45, arc=3.0)
TOWER_COURT = (19.2, 31.2, 22.8, 41.2)                                  # each courtroom's plan, inner (no window): double height
TOWER_CORE = (35.0, 42.6, 29.0, 35.65)                                  # public lifts + the stair shaft, L1 .. L5 (+ headroom)
TOWER_SECLIFT = (31.2, 35.0, 22.8, 25.8)                                # the secure lift's shaft
TOWER_VEST = (22.5, 31.5)                                               # the galleria -> tower lobby doorway (u), through the tower's S face
def tower_voids():
    L = B['tower']['levels']; i = TOWER_IN; a = i['arc']; out = []
    out.append((i['u0'], 50.6 - a, 17.3 + a, 56.3 - a, L[0], L[2]))                      # L1 + L2: the lobby, inside the colonnade glass
    out.append((TOWER_VEST[0], TOWER_VEST[1], 17.3 - 0.01, 17.3 + a, L[0], L[2]))        # the vestibule from the galleria
    for f in (2, 4):                                                                      # the courtroom floors L3, L5 (see-out)
        out.append((i['u0'], i['u1'], i['v0'], i['v1'], L[f], L[f + 1]))
        c = TOWER_COURT; out.append((c[0], c[1], c[2], c[3], L[f + 1], L[f + 2]))         # the courtroom's upper half
    for c in (TOWER_CORE, TOWER_SECLIFT): out.append((c[0], c[1], c[2], c[3], L[0], L[5] + 0.0))
    return out
def jail_voids():
    """Jail I's MLO volumes (jc-jail's work/jail/jj_hooks.JAIL_VOIDS: the numbers live there; Jail I keeps every pane, louvre and
    backing box - no SEE_OUT band)."""
    import importlib.util
    from pathlib import Path
    p = Path(__file__).resolve().parent.parent / 'jail' / 'jj_hooks.py'
    if not p.exists(): return []
    spec = importlib.util.spec_from_file_location('jj_hooks', p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return [tuple(v) for v in m.JAIL_VOIDS]
def mlo_voids(k):
    """the floor bands handed to an MLO (SEE_OUT levels): cut out of the hull (the MLO brings its own walls / floors / collision).
    The tower hands over explicit volumes (tower_voids), not whole bands."""
    if k == 'tower' and SEE_OUT['tower']: return tower_voids()
    if k == 'jail1': return jail_voids()
    if k == 'police': return [tuple(v) for v in _p3('jc3_police').voids() + _p3('jc3_pgarage').voids()]   # area 3: the L1 / L2 rooms, B1
    b = B[k]; L = b['levels'] + [b['roof']]; out = []
    for lvl in sorted(SEE_OUT[k]):
        for (u0, u1, v0, v1) in rects(k): out.append((u0 - 0.01, u1 + 0.01, v0 - 0.01, v1 + 0.01, L[lvl - 1], L[lvl]))
    return out
PIER_DEPTH = 1.4                               # the colonnade's piers: square-ish, free standing; a 1.6 m walk runs behind them
def arcade_runs(k, face):
    """the colonnade bays grouped into continuous runs (bays closer than 3 m share one walk, one glass wall, one soffit):
    [[(a0, a1, z0, z1), ...], ...] (rig 2026-10-28: piers running back to the glass cut the colonnade into dead-end alcoves)."""
    bays = [(o_[1], o_[2], o_[3], o_[4]) for o_ in openings(k, face) if o_[0] == 'arcade']; runs = []
    for b in sorted(bays):
        if runs and b[0] - runs[-1][-1][1] < 3.0: runs[-1].append(b)
        else: runs.append([b])
    return runs
def arcade_voids(k):
    """the colonnade's walkable space per run (lot rects u0, u1, v0, v1, z0, z1): cut out of the hull (the piers get their own)."""
    out = []
    for face in face_list(k):
        for run in arcade_runs(k, face):
            p = P(face, run[0][0], -ARC_BACK, 0); q = P(face, run[-1][1], 0.0, 0)
            out.append((min(p[0], q[0]), max(p[0], q[0]), min(p[1], q[1]), max(p[1], q[1]), G - 1.0, run[0][3]))
    return out
def floor_of(k, z):
    L = B[k]['levels']; return max([1] + [i + 1 for i, lz in enumerate(L) if lz <= z + 1e-6])
# ---------------- what the LOD chain needs (one source with the HD facades) ----------------
def lit_bays(k):
    """the bays lit at night, exactly as the HD _emi model picks them: [(face, a0, a1, z0, z1)]."""
    out = []
    for face in face_list(k):
        f = face[0]
        for kind, a0, a1, z0, z1 in openings(k, face):
            if kind in ('win', 'ribbon', 'punch') and floor_of(k, z0) not in SEE_OUT[k] and lit(k, f, round(a0, 1), round(z0, 1)): out.append((face, a0, a1, z0, z1))
    return out
def massing(k):
    """the LOD boxes of building k: [(u0, u1, v0, v1, z0, z1)] (the face planes; parapet top)."""
    return [(r[0], r[1], r[2], r[3], SLAB - 0.3, B[k]['top']) for r in rects(k)]
def bridge_massing(): return [(u0, u1, v0, v1, z0, z1) for (u0, u1, v0, v1, z0, z1) in BRIDGES.values()]

def box_minus(h, voids):
    """an axis box (u0, u1, v0, v1, z0, z1) minus axis boxes: exact grid decomposition; kept cells merged into z-columns per (u, v)
    cell, then along u (no internal faces where nothing was cut: a split face inside a solid reads as ground to the checks)."""
    clip = [tuple(max(a, b) if i % 2 == 0 else min(a, b) for i, (a, b) in enumerate(zip(v, h))) for v in voids]
    clip = [c for c in clip if c[1] - c[0] > 1e-4 and c[3] - c[2] > 1e-4 and c[5] - c[4] > 1e-4]
    if not clip: return [h]
    cuts = [sorted({h[2 * a], h[2 * a + 1]} | {c[2 * a + i] for c in clip for i in (0, 1)}) for a in range(3)]
    def kept(u0, u1, v0, v1, z0, z1):
        m = ((u0 + u1) / 2, (v0 + v1) / 2, (z0 + z1) / 2)
        return not any(c[0] <= m[0] <= c[1] and c[2] <= m[1] <= c[3] and c[4] <= m[2] <= c[5] for c in clip)
    cols = {}
    for i, (u0, u1) in enumerate(zip(cuts[0], cuts[0][1:])):
        for j, (v0, v1) in enumerate(zip(cuts[1], cuts[1][1:])):
            runs = []; cur = None
            for z0, z1 in zip(cuts[2], cuts[2][1:]):
                if kept(u0, u1, v0, v1, z0, z1): cur = (cur[0], z1) if cur else (z0, z1)
                elif cur: runs.append(cur); cur = None
            if cur: runs.append(cur)
            cols[(i, j)] = runs
    out = []
    for j, (v0, v1) in enumerate(zip(cuts[1], cuts[1][1:])):
        open_ = {}                                                  # z-run -> start u
        for i, (u0, u1) in enumerate(zip(cuts[0], cuts[0][1:])):
            rs = set(cols[(i, j)])
            for r in list(open_):
                if r not in rs: out.append((open_.pop(r), u0, v0, v1, r[0], r[1]))
            for r in rs:
                if r not in open_: open_[r] = u0
        for r, s in open_.items(): out.append((s, cuts[0][-1], v0, v1, r[0], r[1]))
    return out
