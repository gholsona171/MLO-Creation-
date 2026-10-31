"""Area 3 Police HQ dressing (Antonio 2026-10-30: "headquarters look basic" - dress it like a working police HQ), as numbers. Rebuilt from
the room plan (jc3_police) with Rockstar's own police-station props: the set Mission Row uses (hei_heist_police_dlc / v_policehub, read
from survey/mlo_scan.tsv) plus Rockstar office pieces. Replaces jc3_police.furniture() (its patrol-room lockers stood 4 m inside the
public lobby after the colonnade moved GAR_N; jc3_dress_check.py now checks every prop against its own room).
  dress()  -> [(room, model, u, v, base z (absolute), heading)]   floor props, desk clutter, wall-hung and ceiling props
  signs()  -> [(room, (u, v, z), face, w, h, lines, name)]        door plates, floor numbers, POLICE lettering (tc_kit.sign panels)
  WALL     -> {model}  hung on a wall / ceiling (not floor props: jc3_footprint skips them, jc3_dress_check checks them)
Facing: FRONT[model] = the side the model shows ('-y' unless measured otherwise from its vertex normals: Mission Row's notice boards
face +y - placed like the whiteboard they would have hung backwards). A wall item's back sits 1 cm off the lining's face.
Heading: a prop's +y points to (-sin h, cos h) (jc3_police's convention)."""
import math
import jc3_police as P
WI, SG, NI, COR, LOB_W, P1, P2, H = P.WI, P.SG, P.NI_LINK, P.COR, P.LOB_W, P.P1, P.P2, 2.6
OUTER = {('u', WI), ('u', P.EI), ('v', SG), ('v', NI), ('v', P.NI_FACE), ('v', P.TRENCH_N)}   # outer lines: 0.2 m linings
FRONT = {'v_20_notbrd01': '+y', 'v_20_notbrd002': '+y', 'v_20_notbrd003': '+y', 'v_20_notbrd004': '+y', 'v_20_notbrd005': '+y'}
WALL = {'v_20_notbrd01', 'v_20_notbrd002', 'v_20_notbrd003', 'v_20_notbrd004', 'v_20_notbrd005', 'v_med_cor_whiteboard',
        'v_med_cor_pinboard', 'prop_game_clock_02', 'prop_fire_exting_2a', 'v_serv_firealarm', 'prop_coathook_01', 'v_20_lspd_sign',
        'prop_cctv_cam_06a', 'v_med_smokealarm', 'v_serv_metro_ceilingvent', 'v_serv_emrglgt_off', 'prop_wall_vent_02'}
CEILING = {'prop_cctv_cam_06a', 'v_med_smokealarm', 'v_serv_metro_ceilingvent'}
BENCH, DESK, OCH, BKC, LCH, EXC = 'v_ilev_ph_bench', 'v_corp_officedesk', 'prop_off_chair_05', 'v_corp_bk_chair1', 'v_ilev_leath_chr', 'ex_prop_offchair_exec_01'
SHELF, FCAB, LOCK, SIDE = 'v_corp_offshelfdark', 'v_corp_filecabtall', 'v_ind_rc_locker', 'v_corp_sidetable'
CHAIRS = (OCH, 'prop_off_chair_04', 'prop_off_chair_03', 'v_corp_offchair')        # desk chairs vary (Rockstar office set)
BOARDS = ('v_20_notbrd01', 'v_20_notbrd002', 'v_20_notbrd003', 'v_20_notbrd004', 'v_20_notbrd005')
TOP = 0.76                                                                 # v_corp_officedesk's top
def _seed(u, v): return int(abs(u * 7.31 + v * 13.17) * 10) % 97
def floor_of(room): return P1 if room in ('plobby', 'pdesk', 'pstaff1') else P2
def ceil_of(room, u=0.0, v=0.0):
    """the ceiling's underside: the lobby's tall hall under its 0.2 m ceiling slab (P.CEIL - 0.2), its low north hall and every other room
    at floor + 2.6."""
    if room == 'plobby' and not (17.5 <= u <= LOB_W and P.HALL_S <= v <= NI): return P.CEIL - 0.2
    return floor_of(room) + H
def wall(room, model, axis, line, side, a, bottom, depth=None):
    """a model with its back against the wall plane `axis` = line (+ the lining), the room on the `side` (+1: the larger coordinate),
    `a` along the wall, its bottom `bottom` m over the floor. depth: the model's back -> pivot distance (from its bounds, given by the
    caller that knows them; None = 0.02 for thin wall pieces)."""
    t = 0.2 if (axis, round(line, 2)) in {(x, round(y, 2)) for x, y in OUTER} else 0.1
    plane = line + side * t; front = FRONT.get(model, '-y')
    if axis == 'u': h = (90.0 if side > 0 else 270.0) if front == '-y' else (270.0 if side > 0 else 90.0)
    else: h = (180.0 if side > 0 else 0.0) if front == '-y' else (0.0 if side > 0 else 180.0)
    d = plane + side * ((depth if depth is not None else 0.02) + 0.01)
    u, v = (d, a) if axis == 'u' else (a, d)
    return (room, model, u, v, bottom, h)
DEPTH = {'v_20_notbrd01': 0.05, 'v_med_cor_whiteboard': 0.01, 'v_med_cor_pinboard': 0.0, 'prop_game_clock_02': 0.03, 'prop_fire_exting_2a': 0.01,
         'v_serv_firealarm': 0.0, 'prop_coathook_01': 0.06, 'v_20_lspd_sign': 0.01, 'v_serv_emrglgt_off': 0.09,
         FCAB: 0.30, 'v_corp_tallcabdark01': 0.30, 'v_corp_lowcabdark01': 0.30, 'v_corp_filecablow': 0.30, SHELF: 0.26, LOCK: 0.39,
         'prop_watercooler': 0.20, 'prop_vend_coffe_01': 0.32, 'prop_vend_soda_02': 0.47, 'prop_vend_water_01': 0.33, SIDE: 0.45,
         'v_res_tt_fridge': 0.45, 'prop_shredder_01': 0.19, 'v_corp_cabshelves01': 0.32, 'prop_copier_01': 0.52, 'v_med_p_sofa': 0.48,
         'prop_recyclebin_02a': 0.25, 'prop_bin_11b': 0.24, 'v_20_office_flag01': 0.16, BENCH: 0.45, 'prop_plant_int_01b': 0.46,
         'prop_plant_int_02a': 0.44, 'prop_tool_mopbucket': 0.25, 'prop_cabinet_01': 0.31, 'v_res_filebox01': 0.17}
for _b in BOARDS: DEPTH[_b] = 0.05
def W(room, model, axis, line, side, a, bottom=0.0): return wall(room, model, axis, line, side, a, bottom, DEPTH.get(model, 0.02))
def local(u, v, h, x, y):
    t = math.radians(h); return u + x * math.cos(t) - y * math.sin(t), v + x * math.sin(t) + y * math.cos(t)
def desk(room, u, v, h=0.0, chair=None, extra=True):
    """v_corp_officedesk (user side +y) with a chair, a monitor or two, keyboard + mouse, and clutter that varies desk to desk."""
    s = _seed(u, v); ch = chair or CHAIRS[s % len(CHAIRS)]
    out = [(room, DESK, u, v, 0.0, h), (room, ch, *local(u, v, h, 0.0, 1.15), 0.0, h)]
    put = lambda m, x, y, z=TOP, dh=180.0: out.append((room, m, *local(u, v, h, x, y), z, (h + dh) % 360))
    put('prop_monitor_w_large' if s % 3 == 0 else 'prop_monitor_01a', -0.05, -0.25)
    if s % 4 == 1: put('prop_monitor_01a', 0.55, -0.22, TOP, 200.0)
    put('prop_keyboard_01b' if s % 2 else 'prop_keyboard_01a', 0.0, 0.18); put('prop_mouse_01a', 0.38, 0.2)
    if not extra: return out
    put('v_res_mmug' if s % 2 else 'v_ret_gc_mug03', 0.75, 0.12)
    put(('v_res_paperfolders', 'prop_cd_folder_pile1', 'v_ret_gc_trays', 'v_res_binder')[s % 4], -0.85, -0.05, TOP + (0.11 if s % 4 == 0 else 0.0))
    put('v_ret_gc_phone', 0.95, -0.25, TOP + 0.05)
    if s % 3 != 1: put('v_corp_cd_desklamp', -1.0, -0.35)
    if s % 5 == 2: put('v_20_copfile01', -0.45, 0.2, TOP + 0.002, 170.0)
    if s % 5 == 4: put('prop_cs_walkie_talkie', 0.6, -0.05, TOP + 0.13, 90.0)
    if s % 6 == 3: put('prop_food_cb_donuts', 0.75, -0.3)
    return out
def ceiling(room, model, u, v, h=0.0):
    """a ceiling-mounted model: its top 1 cm under the ceiling."""
    hz = {'prop_cctv_cam_06a': 0.38, 'v_med_smokealarm': 0.13, 'v_serv_metro_ceilingvent': 0.02}[model]
    return (room, model, u, v, ceil_of(room, u, v) - floor_of(room) - hz - 0.01, h)
def dress():
    L = []
    # ---------------- L1 public lobby + hall (plobby): benches, planters, flags, notices on the west wall, the counter's monitors ----------------
    L += [W('plobby', BENCH, 'u', LOB_W, 1, v) for v in (-36.0, -32.0, -15.0)]
    for cu, cv in ((38.0, -34.5), (38.0, -14.5)):
        L += [('plobby', BENCH, cu, cv - 0.5, 0.0, 0.0), ('plobby', BENCH, cu, cv + 0.5, 0.0, 180.0)]
        L += [('plobby', 'ch_prop_ch_planter_01', cu + du, cv, 0.0, 0.0) for du in (-2.35, 2.35)]
    L += [('plobby', m, 33.3, v, 0.0, 90.0) for m, v in (('v_20_flag01', -18.6), ('v_20_flag02', -18.0), ('v_20_flag03', -17.4))]
    L += [('plobby', 'prop_bin_11b', 41.4, -38.0, 0.0, 0.0), ('plobby', 'prop_bin_11b', 41.4, -11.0, 0.0, 0.0)]
    L += [('plobby', 'ch_prop_ch_planter_01', 17.95, -8.1, 0.0, 0.0), ('plobby', 'ch_prop_ch_planter_01', 22.05, -8.1, 0.0, 0.0),
          ('plobby', BENCH, 27.5, -12.85, 0.0, 180.0)]
    L += [W('plobby', BOARDS[i], 'u', LOB_W, 1, v, 1.25) for i, v in enumerate((-41.0, -36.0, -32.0))]
    L += [W('plobby', 'prop_watercooler', 'u', LOB_W, 1, -28.3), W('plobby', 'prop_recyclebin_02a', 'u', LOB_W, 1, -27.4),
          W('plobby', 'prop_plant_int_01b', 'u', LOB_W, 1, -43.6), W('plobby', 'prop_vend_coffe_01', 'u', LOB_W, 1, -11.0)]
    L += [W('plobby', 'prop_game_clock_02', 'u', LOB_W, 1, -22.0, 3.35)]                   # over the FRONT DESK lettering
    L += [W('plobby', 'prop_fire_exting_2a', 'u', LOB_W, 1, -38.8, 0.9), W('plobby', 'prop_fire_exting_2a', 'v', P.HALL_S, 1, 26.0, 0.9)]
    L += [W('plobby', BOARDS[3], 'v', P.HALL_S, 1, 29.5, 1.25), W('plobby', 'v_serv_firealarm', 'v', P.HALL_S, 1, 24.6, 1.4)]
    L += [ceiling('plobby', 'prop_cctv_cam_06a', 41.6, -43.9, 45.0), ceiling('plobby', 'prop_cctv_cam_06a', 41.6, -9.6, 135.0),
          ceiling('plobby', 'prop_cctv_cam_06a', 18.0, -12.9, 225.0)]
    L += [ceiling('plobby', 'v_med_smokealarm', 37.5, v) for v in (-40.0, -26.0, -12.0)] + [ceiling('plobby', 'v_med_smokealarm', 25.0, -10.3)]
    # ---------------- L1 front desk office (pdesk): the clerk's counter, desks, radios, files, printer ----------------
    L += desk('pdesk', 28.5, -27.0, 0.0) + desk('pdesk', 28.5, -16.6, 180.0)
    L += [('pdesk', OCH, 31.3, -22.0, 0.0, 90.0), ('pdesk', 'prop_police_radio_main', 32.35, -20.2, 1.05, 270.0),
          ('pdesk', 'prop_monitor_w_large', 32.3, -23.3, 1.05, 270.0), ('pdesk', 'prop_keyboard_01b', 31.95, -22.2, 1.05, 270.0),
          ('pdesk', 'v_ret_gc_phone', 32.25, -24.0, 1.10, 280.0), ('pdesk', 'v_ret_gc_trays', 32.3, -21.0, 1.15, 270.0)]
    L += [W('pdesk', FCAB, 'u', P.DESK_W, 1, v) for v in (-29.3, -28.7, -28.1)]
    L += [W('pdesk', 'v_corp_tallcabdark01', 'u', P.DESK_W, 1, v) for v in (-15.0, -14.4)]
    L += [W('pdesk', SIDE, 'v', P.HALL_S, -1, 26.3), ('pdesk', 'prop_printer_02', 26.3, -14.1, 0.88, 180.0),
          W('pdesk', 'prop_shredder_01', 'v', P.HALL_S, -1, 27.6)]
    L += [W('pdesk', BOARDS[0], 'u', P.DESK_W, 1, -22.6, 1.25), W('pdesk', 'v_med_cor_pinboard', 'v', P.DESK_S, 1, 26.0, 1.0),
          W('pdesk', 'prop_game_clock_02', 'v', P.DESK_S, 1, 29.8, 2.05), W('pdesk', 'prop_fire_exting_2a', 'u', P.DESK_W, 1, -17.5, 0.9)]
    L += [ceiling('pdesk', 'v_med_smokealarm', 28.4, -22.0), ceiling('pdesk', 'prop_cctv_cam_06a', 24.4, -29.6, 315.0)]
    # ---------------- L1 staff side (pstaff1) ----------------
    S = 'pstaff1'
    # briefing room: rows of chairs facing the north wall, the briefing table, whiteboard + pinboard, flags, clock
    L += [(S, 'prop_off_chair_04', u, v, 0.0, 180.0) for v in (-22.0, -20.6, -19.2) for u in (12.6, 13.8, 15.0, 16.2, 17.4, 18.6, 19.8)]   # briefing rows
    L += [(S, 'v_corp_conftable2', 16.2, -15.0, 0.0, 0.0), (S, 'prop_laptop_01a', 16.6, -15.0, 0.82, 180.0), (S, 'v_res_paperfolders', 15.3, -15.1, 0.93, 0.0)]
    L += [W(S, 'v_med_cor_whiteboard', 'v', P.G_BREAK, -1, 16.2, 1.0), W(S, 'v_med_cor_pinboard', 'v', P.G_BREAK, -1, 12.4, 0.9)]
    L += [W(S, 'v_20_office_flag01', 'v', P.G_BREAK, -1, 14.85), W(S, 'v_20_office_flag01', 'v', P.G_BREAK, -1, 17.55)]
    L += [W(S, BOARDS[1], 'u', COR[0], -1, -16.0, 1.25), W(S, BOARDS[2], 'u', COR[0], -1, -24.6, 1.25),
          W(S, 'prop_game_clock_02', 'v', P.G_BRIEF, 1, 16.2, 2.05), W(S, 'prop_fire_exting_2a', 'u', COR[0], -1, -18.6, 0.9)]
    # locker room: lockers on the stair's west wall, benches, coat hooks, a notice board
    L += [(S, LOCK, 17.86, -35.4 + 0.8 * i, 0.0, 270.0) for i in range(7)]
    L += [(S, BENCH, 14.0, -33.0, 0.0, 90.0), (S, BENCH, 14.0, -37.2, 0.0, 90.0)]
    L += [W(S, 'prop_coathook_01', 'v', P.G_BRIEF, -1, u, 1.65) for u in (11.6, 12.5, 13.4)]
    L += [W(S, BOARDS[4], 'v', P.G_BRIEF, -1, 15.6, 1.25), W(S, 'v_serv_firealarm', 'v', P.G_LOCK, 1, 13.0, 1.4)]
    # evidence: shelving with boxes, cabinets, a booking desk, evidence bags on the table
    L += [(S, SHELF, 21.63, -42.6, 0.0, 270.0), (S, SHELF, 16.0, -44.5, 0.0, 90.0)]
    L += [W(S, FCAB, 'v', P.G_LOCK, -1, u) for u in (12.0, 12.6, 13.2)]
    L += [(S, 'v_res_filebox01', 16.0, v, z, 0.0) for v in (-42.6, -46.4) for z in (0.0, 0.36)]
    L += desk(S, 13.6, -46.6, 0.0, extra=False) + [(S, 'v_20_evidence01', 13.0, -46.7, TOP + 0.02, 0.0), (S, 'v_20_evidence01', 13.9, -46.5, TOP + 0.02, 30.0)]
    L += [W(S, 'v_med_cor_pinboard', 'v', P.G_EVID, 1, 18.5, 1.0)]
    # armory: lockers and cabinets
    L += [W(S, LOCK, 'u', P.U_FOOT, -1, v) for v in (-55.8, -55.0, -54.2, -53.4, -52.6, -51.8)]
    L += [W(S, 'prop_cabinet_01', 'v', SG, 1, u) for u in (12.0, 12.6, 13.2, 13.8)]
    L += [W(S, 'prop_fire_exting_2a', 'v', P.G_EVID, -1, 17.2, 0.9)]
    # break room: fridge, coffee, soda, a table with chairs, sofa, TV, notices
    L += [W(S, 'v_res_tt_fridge', 'u', 17.5, -1, -8.0), W(S, SIDE, 'u', 17.5, -1, -9.6), (S, 'prop_coffee_mac_01', 16.95, -9.6, 0.88, 270.0),
          W(S, 'prop_vend_soda_02', 'u', 17.5, -1, -11.4)]
    L += [(S, SIDE, 12.6, -9.2, 0.0, 0.0), (S, OCH, 12.6, -10.25, 0.0, 180.0), (S, OCH, 12.6, -8.15, 0.0, 0.0),
          (S, 'prop_food_cb_donuts', 12.5, -9.2, 0.88, 20.0), (S, 'v_res_mmug', 12.9, -9.0, 0.88, 0.0)]
    L += [W(S, BOARDS[0], 'v', NI, -1, 14.6, 1.3), W(S, 'prop_bin_11b', 'v', P.G_BREAK, 1, 16.9)]
    # report room: four writing desks, printer, copier, cabinets
    L += desk(S, 27.0, -38.0) + desk(S, 31.0, -38.0) + desk(S, 27.0, -33.4, 180.0) + desk(S, 31.0, -33.4, 180.0)
    L += [W(S, 'prop_copier_01', 'u', COR[1], 1, -40.6 + 0.4), W(S, 'v_corp_lowcabdark01', 'v', -41.3, 1, 31.6),
          W(S, BOARDS[2], 'v', P.DESK_S, -1, 28.5, 1.3), W(S, 'prop_game_clock_02', 'u', LOB_W, -1, -35.5, 2.05)]
    # kit store: shelving, the water cooler in the corridor
    L += [(S, SHELF, 28.4, v, 0.0, 0.0) for v in (-46.9, -44.0)] + [W(S, 'prop_tool_mopbucket', 'u', COR[1], 1, -42.2)]
    L += [W(S, 'prop_watercooler', 'u', COR[0], 1, -42.4), W(S, 'prop_fire_exting_2a', 'u', COR[1], -1, -28.0, 0.9),
          W(S, BOARDS[3], 'u', COR[1], -1, -23.5, 1.25), W(S, BOARDS[1], 'u', COR[0], 1, -25.5, 1.25)]
    # patrol room (3.2 m deep since GAR_N moved): lockers along its north wall, a bench in front, the shift board
    L += [W(S, LOCK, 'v', P.GAR_N, -1, 34.8 + 0.8 * i) for i in range(9)] + [(S, BENCH, 38.4, -46.6, 0.0, 0.0)]
    L += [W(S, 'v_med_cor_whiteboard', 'v', P.TRENCH_N, 1, 43.0, 1.0)]
    L += [ceiling(S, 'v_med_smokealarm', u, v) for u, v in ((16.2, -20.0), (14.5, -33.5), (16.0, -44.5), (16.0, -52.7), (14.0, -10.3), (28.5, -35.7), (38.7, -46.0))]
    L += [ceiling(S, 'prop_cctv_cam_06a', 23.0, -47.3, 0.0), ceiling(S, 'prop_cctv_cam_06a', 11.0, -56.2, 315.0)]
    # ---------------- L2 (pstaff2) ----------------
    S = 'pstaff2'
    # captain's office: executive desk, flags, shelves, a visitors' pair, plant, notices
    L += [(S, DESK, 16.0, -12.0, 0.0, 90.0), (S, EXC, 14.8, -12.0, 0.0, 90.0)]
    L += [(S, m, *local(16.0, -12.0, 90.0, x, y), TOP + dz, (90.0 + 180.0) % 360) for m, x, y, dz in
          (('prop_monitor_w_large', -0.4, -0.25, 0.0), ('prop_keyboard_01b', -0.4, 0.18, 0.0), ('v_corp_cd_desklamp', 0.95, -0.3, 0.0),
           ('v_ret_gc_phone', 0.7, 0.05, 0.05), ('prop_cd_folder_pile1', -1.0, 0.0, 0.0), ('v_res_mmug', 0.35, 0.2, 0.0))]
    L += [(S, 'v_corp_lazychair', 17.7, -12.8, 0.0, 270.0), (S, 'v_corp_lazychair', 17.7, -11.2, 0.0, 270.0)]
    L += [W(S, SHELF, 'v', NI, -1, 16.0), W(S, 'v_20_office_flag01', 'v', NI, -1, 12.0), W(S, 'v_20_office_flag01', 'v', NI, -1, 13.0)]
    L += [W(S, 'prop_plant_int_02a', 'v', P.G_CAPT, 1, 20.8), W(S, 'v_med_cor_pinboard', 'u', COR[0], -1, -10.0, 1.0),
          W(S, 'prop_game_clock_02', 'u', COR[0], -1, -16.5, 2.05)]
    # conference room
    L += [(S, 'v_corp_conftable2', 16.3, -22.3, 0.0, 0.0)] + [(S, LCH, u, v, 0.0, h) for u in (14.8, 16.3, 17.8) for v, h in ((-23.3, 180.0), (-21.3, 0.0))]
    L += [(S, LCH, 13.95, -22.3, 0.0, 90.0), (S, LCH, 18.65, -22.3, 0.0, 270.0)]
    L += [(S, 'v_res_paperfolders', 15.6, -22.4, 0.93, 0.0), (S, 'prop_laptop_01a', 17.0, -22.1, 0.82, 200.0), (S, 'v_res_mmug', 16.4, -22.6, 0.82, 0.0)]
    L += [W(S, 'v_med_cor_whiteboard', 'v', P.G_CAPT, -1, 16.3, 1.0), W(S, SIDE, 'v', P.G_BRIEF, 1, 16.3), (S, 'prop_tv_01', 16.3, -26.2, 0.88, 180.0),
          W(S, 'prop_plant_int_01b', 'v', P.G_BRIEF, 1, 20.9)]
    # open office (detectives): desks in pairs, cabinets, the copier, boards, water cooler
    for v in (-46.0, -40.5, -35.0, -29.5): L += desk(S, 14.0, v)
    for v in (-46.0, -40.5): L += desk(S, 19.0, v)
    L += [W(S, 'v_corp_tallcabdark01', 'v', P.G_BRIEF, -1, u) for u in (11.2, 11.8, 12.4)] + [W(S, 'prop_copier_01', 'u', COR[0], -1, -46.5)]
    L += [W(S, BOARDS[i], 'u', COR[0], -1, v, 1.25) for i, v in ((4, -44.0), (1, -28.4))]
    L += [W(S, 'v_med_cor_whiteboard', 'v', P.G_BRIEF, -1, 16.5, 1.0), W(S, 'prop_watercooler', 'u', COR[0], -1, -42.3),
          W(S, 'prop_plant_int_01b', 'u', COR[0], -1, -48.3), W(S, 'prop_game_clock_02', 'u', COR[0], -1, -37.2, 2.05)]
    # interview suites: table, chairs, the observers' chair, the case file
    for room, u in (('pint1', 12.4), ('pint2', 20.2)):
        L += [(room, SIDE, u, -52.8, 0.0, 0.0), (room, OCH, u, -53.8, 0.0, 180.0), (room, OCH, u, -51.8, 0.0, 0.0),
              (room, 'v_20_copfile02', u - 0.15, -52.8, 0.882, 10.0), (room, 'v_res_mmug', u + 0.25, -52.6, 0.88, 0.0)]
    L += [('pobs1', OCH, 15.6, -52.8, 0.0, 270.0), ('pobs2', OCH, 17.1, -52.8, 0.0, 90.0)]
    L += [ceiling(r, 'prop_cctv_cam_06a', u, -49.4, h) for r, u, h in (('pint1', 13.8, 135.0), ('pint2', 18.8, 225.0))]
    # records: shelving runs with boxes, cabinets, a desk
    L += [(S, SHELF, 28.4, v, 0.0, 0.0) for v in (-44.5, -48.0, -51.5, -55.0)]
    L += [(S, 'v_res_filebox01', 30.0, v, z, 90.0) for v in (-44.5, -48.0, -51.5) for z in (0.0, 0.36)]
    L += [W(S, 'v_corp_tallcabdark01', 'u', LOB_W, -1, v) for v in (-42.5, -43.1, -43.7)] + desk(S, 31.0, -53.0, 90.0, extra=False)
    # open office east: two rows of desks, cabinets, printer, boards
    for u in (26.5, 30.5):
        for v in (-34.0, -27.0, -20.0, -13.0): L += desk(S, u, v)
    L += [W(S, SIDE, 'u', LOB_W, -1, -9.0), ('pstaff2', 'prop_printer_01', 32.25, -9.0, 0.88, 270.0), W(S, 'prop_shredder_01', 'u', LOB_W, -1, -10.2)]
    L += [W(S, BOARDS[i], 'u', LOB_W, -1, v, 1.25) for i, v in ((0, -37.0), (2, -23.5), (3, -16.5))] + [W(S, 'v_med_cor_whiteboard', 'v', NI, -1, 28.5, 1.0)]
    L += [W(S, 'prop_plant_int_02a', 'u', COR[1], 1, -40.5), W(S, 'prop_vend_coffe_01', 'u', COR[1], 1, -8.2)]
    # L2 store
    L += [W(S, SHELF, 'v', SG, 1, u) for u in (35.5, 38.5, 41.5)] + [(S, 'v_res_filebox01', u, -55.3, z, 0.0) for u in (37.0, 40.0) for z in (0.0, 0.36)]
    # corridor: extinguishers, notices, bins
    L += [W(S, 'prop_fire_exting_2a', 'u', COR[0], 1, v, 0.9) for v in (-20.0, -52.0)] + [W(S, BOARDS[2], 'u', COR[1], -1, -46.0, 1.25)]
    L += [W(S, 'prop_bin_11b', 'u', COR[1], -1, -53.0)]
    L += [ceiling(S, 'v_med_smokealarm', u, v) for u, v in ((16.0, -12.5), (16.3, -22.3), (15.0, -38.0), (28.5, -24.0), (28.5, -48.0), (38.7, -50.5), (23.0, -30.0))]
    L += [ceiling(S, 'prop_cctv_cam_06a', 23.0, -56.2, 0.0), ceiling(S, 'prop_cctv_cam_06a', 23.0, -7.6, 180.0)]
    L += [ceiling(r, 'v_serv_metro_ceilingvent', u, v) for r, u, v in (('pdesk', 26.0, -19.0), ('pdesk', 31.0, -27.5), ('pstaff1', 19.0, -24.0),
          ('pstaff1', 12.0, -31.5), ('pstaff1', 29.0, -31.0), ('pstaff1', 23.0, -40.0), ('pstaff2', 13.0, -20.5), ('pstaff2', 17.0, -33.0),
          ('pstaff2', 28.5, -38.5), ('pstaff2', 28.5, -17.0), ('pstaff2', 23.0, -45.0), ('pstaff2', 19.5, -10.5))]
    return [(r, m, u, v, floor_of(r) + z, h) for r, m, u, v, z, h in L]
NAVY, WHITE = (24, 38, 78), (255, 255, 255)
PLATE = {'brief': 'BRIEFING', 'lock': 'LOCKER ROOM', 'evid': 'EVIDENCE', 'arm': 'ARMORY', 'break': 'BREAK ROOM', 'report': 'REPORT ROOM',
         'kit': 'KIT STORE', 'patrol': 'PATROL', 'capt': 'CAPTAIN', 'conf': 'CONFERENCE', 'office': 'DETECTIVES', 'records': 'RECORDS',
         'office e': 'OFFICE', 'l2store': 'STORE'}
def signs():
    """(room, (u, v, z), face, w, h, lines, name, bg, fg): door name plates on the approach side, floor marks in the stair, the lobby's
    POLICE lettering and FRONT DESK over the counter."""
    out = []
    side_of = {COR[0]: ('pstaff', 1), COR[1]: ('pstaff', -1), LOB_W: ('pstaff', -1), P.G_EVID: ('pstaff', 1), P.G_BREAK: ('pstaff', -1)}
    for name, z, axis, plane, a0 in P.INNER_DOORS:
        room = 'pstaff1' if z == P1 else 'pstaff2'; s = side_of[plane][1]; t = 0.1
        p = (plane + s * t, a0 + 1.4 + 0.35, z + 1.6) if axis == 'u' else (a0 + 1.4 + 0.35, plane + s * t, z + 1.6)
        out.append((room, p, ('+' if s > 0 else '-') + axis, 0.5, 0.14, [PLATE[name]], f'JC plate {PLATE[name]}', NAVY, WHITE))
    for name, a0 in (('INTERVIEW 1', 11.6), ('OBSERVATION 1', 14.35), ('OBSERVATION 2', 16.45), ('INTERVIEW 2', 19.5)):
        out.append(('pstaff2', (a0 + 0.7, -48.93 + 0.1, P2 + 2.5), '+v', 0.9, 0.14, [name], f'JC plate {name}', NAVY, WHITE))
    out += [('pstaff1', (COR[0] + 0.15, -33.75, P1 + 1.6), '+u', 0.5, 0.14, ['STAIRS'], 'JC plate STAIRS', NAVY, WHITE),   # the stair's wall: 0.15 lining
            ('pstaff2', (COR[0] + 0.15, -33.75, P2 + 1.6), '+u', 0.5, 0.14, ['STAIRS'], 'JC plate STAIRS', NAVY, WHITE),
            ('plobby', (23.0, P.HALL_S + 0.1, P1 + 2.6), '+v', 1.6, 0.22, ['POLICE - STAFF ONLY'], 'JC plate STAFF ONLY', NAVY, WHITE)]
    S = P.STAIR_B
    for lv, z in (('L1', P1), ('L2', P2)): out.append(('pstair', (S[1] - 0.15, -33.0, z + 1.7), '-u', 0.4, 0.4, [lv], f'JC floor {lv}', (230, 190, 30), (20, 20, 20)))
    out.append(('pstair', (S[0] + 1.0, S[2] + 0.15, 25.6 + 1.7), '+v', 0.4, 0.4, ['B1'], 'JC floor B1', (230, 190, 30), (20, 20, 20)))
    out += [('plobby', (LOB_W + 0.1, -22.0, P1 + 4.2), '+u', 4.2, 0.7, ['POLICE'], 'JC lobby POLICE', NAVY, WHITE),
            ('plobby', (LOB_W + 0.1, -22.0, P1 + 2.55), '+u', 2.2, 0.3, ['FRONT DESK'], 'JC lobby FRONT DESK', NAVY, WHITE)]
    return out
