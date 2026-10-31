"""Area 3 B1 garage dressing (Antonio 2026-10-30: "garage ... looks basic"), as numbers - a working police motor pool, Rockstar props
(the fire station's / Rockstar garages' set) plus painted markings and services. Every lane stays clear: jc3_drive_sweep.py sweeps the
patrol car's route against all of this, jc3_footprint.py checks the floor props.
  dress()   -> [(room, model, u, v, base z, heading)]     floor / wall / ceiling props (WALL: hung, not floor props)
  signs()   -> [(room, (u, v, z), face, w, h, lines, name, bg, fg, hang)]   hang = ceiling z for a hanging sign, else None
  decals()  -> [(kind, u, v, length, width, up (deg, lot frame), text)]      painted on the floor (decal shader): bay numbers, arrows,
               oil stains, the wash-bay drain
  boxes()   -> [(lo, hi, material)]                       hazard bands on the columns, pipes and conduit on the walls, a supply duct
  lamps()   -> [(u, v, z, energy, falloff, size, colour)]  warm task lights over the workshop"""
import math
import jc3_pgarage as G, jc3_police as P
ZB, CEIL = G.ZB, G.CEIL_B - 0.02                                          # B1 floor, the ceiling plate's underside
C = G.CLEAR                                                               # the linings' faces (11.15, 44.05, -58.55, -8.25)
WALL = {'prop_fire_exting_2a', 'prop_cctv_cam_06a', 'v_serv_firealarm', 'v_serv_emrglgt_off', 'prop_fire_hosebox_01'}
DEPTH = {'prop_fire_exting_2a': 0.01, 'v_serv_firealarm': 0.0, 'v_serv_emrglgt_off': 0.09, 'prop_shelves_01': 0.40, 'prop_shelves_02': 0.40,
         'prop_toolchest_05': 0.36, 'prop_toolchest_04': 0.38, 'prop_toolchest_03': 0.39, 'prop_tool_bench02': 1.03, 'prop_barier_conc_02a': 0.32,
         'prop_sacktruck_02a': 0.27, 'prop_tyre_rack_01': 0.14, 'prop_mp_barrier_02b': 0.43, 'prop_tool_box_06': 0.24,
         'prop_fire_hosebox_01': 0.05}
def on(face_u, face_v, axis, side, model, a, bottom):
    """a model's back on a face (no lining beyond: the faces given are the linings' / the columns' own), the room on `side`."""
    d = DEPTH.get(model, 0.02) + 0.01
    if axis == 'u': return ('pdeck', model, face_u + side * d, a, ZB + bottom, 90.0 if side > 0 else 270.0)
    return ('pdeck', model, a, face_v + side * d, ZB + bottom, 180.0 if side > 0 else 0.0)
def ceil_cam(u, v, h, room='pdeck', ceil=CEIL):
    return (room, 'prop_cctv_cam_06a', u, v, ceil - 0.39, h)
SE = (38.6, C[1], C[2] + 0.3, -40.4)                                      # the store corner: east of row 4, south of the loop's SE turn
def dress():
    L = []
    # the store corner (SE, clear of the loop): parts shelving on the east wall, a tool chest and box on the OUT lane's wall, drums,
    # cones, a barrier, a sack truck, a tyre stack
    L += [on(C[1], 0, 'u', -1, 'prop_shelves_01', v, 0.0) for v in (-41.8, -44.8)]
    wall_s = G.TRENCH[1] + 0.32                                           # the OUT lane's north wall: the footprint gate's B1 space edge
    L += [on(0, wall_s, 'v', 1, 'prop_toolchest_03', 39.4, 0.0), on(0, wall_s, 'v', 1, 'prop_tool_box_06', 40.3, 0.0)]
    L += [('pdeck', 'prop_barrel_02a', u, v, ZB, 0.0) for u, v in ((39.25, -45.5), (39.85, -45.5), (39.25, -44.9))]
    L += [('pdeck', 'prop_mp_cone_02', 41.1 + 0.42 * i, -47.0, ZB, 0.0) for i in range(3)]
    L += [('pdeck', 'prop_mp_barrier_02b', 40.6, -42.4, ZB, 90.0), ('pdeck', 'prop_sacktruck_02a', 39.3, -43.6, ZB, 90.0)]
    L += [('pdeck', 'imp_prop_impexp_tyre_01a', 42.6, -47.0, ZB + z, 0.0) for z in (0.0, 0.31, 0.62)]
    # the workshop is full (lifts, benches, chests, rack, engine): cones by the lifts
    L += [('pdeck', 'prop_mp_cone_02', 29.3, v, ZB, 0.0) for v in (-22.2, -14.6)]
    # the wash bay: wet-floor sign, mop bucket
    L += [('pdeck', 'v_serv_wetfloorsn', G.WASH[0] + 0.4, G.WASH[2] + 0.4, ZB, 45.0), ('pdeck', 'prop_tool_mopbucket', G.WASH[1] - 0.5, G.WASH[2] + 0.5, ZB, 0.0)]
    # fire extinguishers: the columns' aisle faces, the west and north walls; alarms, emergency lights
    L += [on(u + 0.25, 0, 'u', 1, 'prop_fire_exting_2a', v, 0.9) for u, v in ((33.4, -35.0), (33.4, -27.2))]
    L += [on(u - 0.25, 0, 'u', -1, 'prop_fire_exting_2a', v, 0.9) for u, v in ((28.35, -35.0), (28.35, -27.2))]
    L += [on(C[0], 0, 'u', 1, 'prop_fire_exting_2a', v, 0.9) for v in (-44.0, -24.0)] + [on(0, C[3], 'v', -1, 'prop_fire_exting_2a', u, 0.9) for u in (24.0, 28.0)]   # (36 sat in the NE turn's swing)
    L += [on(0, C[3], 'v', -1, 'v_serv_firealarm', 30.0, 1.4), on(C[0], 0, 'u', 1, 'v_serv_firealarm', -34.0, 1.4)]
    L += [on(0, C[3], 'v', -1, 'v_serv_emrglgt_off', u, 2.3) for u in (15.0, 35.0)] + [on(C[0], 0, 'u', 1, 'v_serv_emrglgt_off', v, 2.3) for v in (-30.0, -50.0)]
    # (Antonio 2026-10-31: break up the long parking hall) hose cabinets, more extinguishers, supply pallets in the south-west
    # recess (off the IN turn); no wall-hung tyre racks: the model also stands free in the workshop (one model, one kind)
    L += [on(C[0], 0, 'u', 1, 'prop_fire_hosebox_01', v, 0.8) for v in (-38.0, -28.0)]   # (-16: in the NW turn's swing) + [on(0, C[3], 'v', -1, 'prop_fire_hosebox_01', 20.0, 0.8)]
    L += [on(u - 0.27, 0, 'u', -1, 'prop_fire_exting_2a', -19.4, 0.9) for u in (22.35, 28.35)]
    L += [on(C[1], 0, 'u', -1, 'prop_fire_exting_2a', v, 0.9) for v in (-20.0, -30.0)]
    L += [('pdeck', 'prop_boxpile_06a', 13.0, -57.5, ZB, 0.0), ('pdeck', 'prop_boxpile_01a', 15.4, -57.6, ZB, 0.0)]
    # CCTV: the ramp feet, the corners, the workshop
    L += [ceil_cam(G.U_FOOT - 0.6, G.IN_C - 1.6, 120.0), ceil_cam(11.6, -8.7, 225.0), ceil_cam(43.6, -8.7, 135.0), ceil_cam(43.6, -47.3, 45.0),
          ceil_cam(11.6, -58.1, 315.0), ceil_cam(28.6, -22.2, 200.0)]
    return L
NAVY, WHITE, GREEN, RED, YEL, BLACK = (24, 38, 78), (255, 255, 255), (20, 110, 50), (170, 25, 25), (232, 190, 30), (20, 20, 20)
def signs():
    hz = CEIL - 0.42
    out = [('pdeck', (G.U_FOOT - 0.35, G.IN_C, hz), '-u', 1.8, 0.4, ['NO ENTRY'], 'JC gar NO ENTRY', RED, WHITE, CEIL),
           ('pdeck', (G.U_FOOT - 0.35, G.OUT_C, hz), '-u', 1.8, 0.4, ['EXIT'], 'JC gar EXIT', GREEN, WHITE, CEIL),
           ('pdeck', ((G.FUEL[0] + G.FUEL[1]) / 2, (G.FUEL[2] + G.FUEL[3]) / 2, hz), '+v', 1.4, 0.35, ['FUEL'], 'JC gar FUEL', YEL, BLACK, CEIL),
           ('pdeck', ((G.WASH[0] + G.WASH[1]) / 2, G.WASH[3] - 0.05, hz), '+v', 1.6, 0.35, ['WASH BAY'], 'JC gar WASH', NAVY, WHITE, CEIL),
           ('pdeck', (33.3, G.WORKSHOP[3] - 0.05, hz), '+v', 1.8, 0.35, ['FLEET WORKSHOP'], 'JC gar WORKSHOP', NAVY, WHITE, CEIL)]
    out += [('pdeck', (C[0], v, ZB + 2.0), '+u', 1.4, 0.4, ['ONE WAY'], 'JC gar ONE WAY', BLACK, WHITE, None) for v in (-36.0, -20.0)]
    out += [('pdeck', (u, C[3], ZB + 2.0), '-v', 1.4, 0.4, ['ONE WAY'], 'JC gar ONE WAY', BLACK, WHITE, None) for u in (22.0, 30.0)]
    out += [('pdeck', (C[0], -26.0, ZB + 2.0), '+u', 0.7, 0.7, ['5 MPH'], 'JC gar 5 MPH', WHITE, BLACK, None),
            ('pdeck', (P.STAIR_B[1] - 0.85, P.STAIR_B[2] - 0.15, ZB + 2.0), '-v', 1.6, 0.3, ['STAIRS - POLICE HQ'], 'JC gar STAIRS', NAVY, WHITE, None),
            ('pdeck', (C[1], -39.0, ZB + 2.0), '-u', 1.6, 0.3, ['PATROL PARKING'], 'JC gar PATROL', NAVY, WHITE, None)]
    # row letters (the columns' faces over their P numbers, the row-D wall, the east wall), POLICE VEHICLES ONLY, ONE WAY / 5 MPH
    # repeats, the first-aid and eyewash stations' signs
    out += [('pdeck', (22.35 - 0.25, -27.2, ZB + 2.3), '-u', 0.6, 0.35, ['ROW A'], 'JC gar ROW A', YEL, BLACK, None),
            ('pdeck', (28.35 - 0.25, -27.2, ZB + 2.3), '-u', 0.6, 0.35, ['ROW B'], 'JC gar ROW B', YEL, BLACK, None),
            ('pdeck', (33.4 + 0.25, -27.2, ZB + 2.3), '+u', 0.6, 0.35, ['ROW C'], 'JC gar ROW C', YEL, BLACK, None),
            ('pdeck', (31.0, G.TRENCH[1] + 0.1, ZB + 2.0), '+v', 0.8, 0.4, ['ROW D'], 'JC gar ROW D', YEL, BLACK, None),
            ('pdeck', (C[1], -25.0, ZB + 2.2), '-u', 0.8, 0.4, ['ROW E'], 'JC gar ROW E', YEL, BLACK, None)]
    out += [('pdeck', (C[0], -50.0, ZB + 2.0), '+u', 2.2, 0.35, ['POLICE VEHICLES ONLY'], 'JC gar POLICE ONLY', NAVY, WHITE, None),
            ('pdeck', (40.0, C[3], ZB + 2.0), '-v', 2.2, 0.35, ['POLICE VEHICLES ONLY'], 'JC gar POLICE ONLY', NAVY, WHITE, None)]
    out += [('pdeck', (C[1], v, ZB + 2.0), '-u', 1.4, 0.4, ['ONE WAY'], 'JC gar ONE WAY', BLACK, WHITE, None) for v in (-18.0, -32.0)]
    out += [('pdeck', (37.5, C[3], ZB + 2.0), '-v', 0.7, 0.7, ['5 MPH'], 'JC gar 5 MPH', WHITE, BLACK, None)]
    out += [('pdeck', (25.8, C[3], ZB + 1.95), '-v', 0.6, 0.18, ['FIRST AID'], 'JC gar FIRST AID', GREEN, WHITE, None),
            ('pdeck', (26.8, C[3], ZB + 1.75), '-v', 0.6, 0.18, ['EYE WASH'], 'JC gar EYE WASH', GREEN, WHITE, None)]
    return out
def decals():
    out = []
    for i, (u, v, h, row) in enumerate(G.bays()):                         # bay numbers at each bay's open end, reading from the aisle
        n = str(i + 1)
        if row < 0: out.append(('number', G.PARALLEL[0] + 0.45, v, 0.5, 0.35, 0.0, n))
        else:
            r = G.ROWS[row]
            if r[4] == 'u-': out.append(('number', r[0] + 0.45, v, 0.5, 0.35, 0.0, n))
            elif r[4] == 'u+': out.append(('number', r[1] - 0.45, v, 0.5, 0.35, 180.0, n))
            else: out.append(('number', u, r[3] - 0.45, 0.5, 0.35, 270.0, n))
    arrows = [(G.IN_X, v, 90.0) for v in (-40.0, -28.0, -18.0)] + [(u, G.NORTH_V, 0.0) for u in (22.0, 28.0)] + \
             [(G.EAST_U, v, 270.0) for v in (-18.0, -26.0)] + [(u, G.RET_V, 180.0) for u in (26.0,)] + \
             [(19.8, G.IN_C, 180.0), (20.6, G.OUT_C + 0.05, 0.0)]                                   # deck only: the ramps slope
    out += [('arrow', u, v, 1.8, 0.8, up, '') for u, v, up in arrows]
    out += [('oil', u + du, v, 0.9, 0.7, 30.0 * k, '') for k, (u, v, h, row) in enumerate(G.bays()) if row in (0, 1, 2) and k % 3 == 1 for du in (0.0,)]
    out += [('drain', (G.WASH[0] + G.WASH[1]) / 2, (G.WASH[2] + G.WASH[3]) / 2, 0.6, 0.6, 0.0, '')]
    return out
def wheel_stops():
    """a concrete wheel stop at the back of every bay (rows A-D; 1.6 x 0.15 x 0.10, collision): Rockstar has no wheel-stop prop, so
    these are our own blocks. 10 cm high: under the drive sweep's body band (0.15 m up), 0.55 m in front of the bay's back."""
    out = []
    for u, v, h, row in G.bays():
        if row < 0: continue
        r = G.ROWS[row]
        if r[4] == 'u-': out.append(((r[1] - 0.625, v - 0.8, ZB), (r[1] - 0.475, v + 0.8, ZB + 0.1)))
        elif r[4] == 'u+': out.append(((r[0] + 0.475, v - 0.8, ZB), (r[0] + 0.625, v + 0.8, ZB + 0.1)))
        else: out.append(((u - 0.8, r[2] + 0.475, ZB), (u + 0.8, r[2] + 0.625, ZB + 0.1)))
    return out
def boxes():
    """(lo, hi, material, collision)"""
    out = []
    for lo, hi in wheel_stops():
        out.append((lo, hi, 'conc', True)); out.append(((lo[0], lo[1], hi[2]), (hi[0], hi[1], hi[2] + 0.003), 'yellow_d', False))   # painted top
    for u in (25.8, 26.8):                                                # the first-aid and eyewash stations: small wall cabinets (no Rockstar prop),
        w, hgt, z0 = (0.45, 0.5, ZB + 1.25) if u == 25.8 else (0.35, 0.35, ZB + 1.1)   # on the north aisle's straight (not in the NE turn)
        out.append(((u - w / 2, C[3] - 0.15, z0), (u + w / 2, C[3] - 0.02, z0 + hgt), 'kit_white', False))
    for u, v in G.COLUMNS: out.append(((u - 0.27, v - 0.27, ZB), (u + 0.27, v + 0.27, ZB + 1.2), 'hazard', False))   # 2 cm proud (sweep: 1.2 cm)
    zp = CEIL - 0.28
    out += [((C[0] + 0.12, C[3] - 0.24, zp), (C[1] - 0.12, C[3] - 0.12, zp + 0.12), 'pipe_red', False),                 # the fire main, north wall
            ((C[0] + 0.12, C[3] - 0.42, zp + 0.02), (C[1] - 0.12, C[3] - 0.34, zp + 0.10), 'steel', False),             # a service pipe
            ((C[0] + 0.12, -48.5, zp + 0.04), (C[0] + 0.18, C[3] - 0.5, zp + 0.10), 'steel', False)]                    # conduit, west wall
    for u in (18.0, 32.0): out.append(((u - 0.03, C[3] - 0.18, ZB + 1.3), (u + 0.03, C[3] - 0.14, zp + 0.06), 'steel', False))   # drops to the panels (2 cm clear of their faces)
    for u in (18.0, 32.0): out.append(((u - 0.25, C[3] - 0.22, ZB + 0.8), (u + 0.25, C[3] - 0.02, ZB + 1.4), 'panel_grey', False))  # electrical panels
    out.append(((C[0] - 0.05, -16.85, CEIL - 0.32), (C[1] + 0.05, -16.35, CEIL - 0.08), 'steel', False))               # the supply duct (under the lamps)
    return out
WARM = (1.0, 0.82, 0.62)
def lamps():
    return [(u, v, CEIL, 0.9, 7.0, (1.2, 0.3), WARM) for u, v in ((31.0, -18.5), (35.0, -18.5), (33.0, -21.0), (40.6, -44.5), (14.0, -57.2), (26.0, -46.0))]
