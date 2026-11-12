"""Area 3 Police HQ dressing for the 2026-10-31 REDESIGN (jc3_redesign_plan.ROOMS: every room's purpose and prop list), rewritten from
scratch (the 2g / 2h dressing is gone with its layout). Rockstar's own props: Mission Row's set (v_policehub / hei_heist_police_dlc,
survey/mlo_scan.tsv) first, then Rockstar office, gym, kitchen, washroom and storage pieces; kit only where Rockstar has no prop (the
honor wall island, the press lectern, shower / WC stall partitions, the detectives' pod screens: kit()).
  dress()      -> [(room, model, u, v, base z (absolute), heading)]   floor, desk-top, wall-hung and ceiling props
  signs()      -> [(room, (u, v, z), face, w, h, lines, name, bg, fg)]  door plates, window / desk signs, stair floor marks
  art()        -> [(room, png, axis, face, side, a, z, w, h, off, decal)]  the Cleveland insignia panels (jc3_insignia.py PNGs)
  floor_art()  -> [(room, png, u, v, size, up deg, z)]                   the floor seals (decals)
  kit()        -> [(room, lo, hi, material, collision)]
  WALL / CEILING / FLAT / FRONT: what the gates need (jc3_dress_check, jc3_footprint)
Facing: a prop's front is -y unless FRONT says '+y' (measured from vertex normals: survey/vanilla, 2026-10-31 for the new pieces).
Heading: 0 faces -v, 90 +u, 180 +v, 270 -u. A wall item stands off its wall face by the trim bands there (P.trim_proud) + 1 cm.
L1 public + front of house here; the staff floors in jc3_police_dress2.py."""
import json, math
from pathlib import Path
import jc3_police as P
import jc_desk as JD
A = {k.lower(): v for k, v in json.load(open(Path(__file__).with_name('survey') / 'arch_ytyp.json', encoding='utf-8-sig')).items()}
def bb(m):
    f = lambda s: [float(x[2:]) for x in s.split()]; a = A[m.lower()]; return f(a['bbMin']), f(a['bbMax'])
P1, P2, H = P.P1, P.P2, 2.6
FRONT = {'v_20_notbrd01': '+y', 'v_20_notbrd002': '+y', 'v_20_notbrd003': '+y', 'v_20_notbrd004': '+y', 'v_20_notbrd005': '+y',
         'v_med_wallpicture1': '+y', 'v_med_wallpicture2': '+y'}
BOARDS = ('v_20_notbrd01', 'v_20_notbrd002', 'v_20_notbrd003', 'v_20_notbrd004', 'v_20_notbrd005')
WALL = set(BOARDS) | {'v_med_cor_whiteboard', 'v_med_cor_pinboard', 'prop_game_clock_02', 'v_ret_gc_clock', 'prop_fire_exting_2a', 'v_serv_firealarm',
        'prop_coathook_01', 'prop_cctv_cam_06a', 'v_med_smokealarm', 'v_serv_metro_ceilingvent', 'v_med_wallpicture1', 'v_med_wallpicture2',
        'v_med_cor_flatscreentv', 'prop_cs_gunrack', 'prop_tv_flat_01', 'v_47_map02', 'hei_prop_hei_muster_01', 'prop_towel_rail_02',
        'prop_shower_rack_01', 'v_res_mountedprojector', 'prop_handdry_01', 'prop_sink_02', 'v_73_p_ap_banosink_aa001'}
CEILING = {'prop_cctv_cam_06a', 'v_med_smokealarm', 'v_serv_metro_ceilingvent', 'v_res_mountedprojector'}
FLAT = {'apa_mp_h_01_acc_rug'}                                             # lies on the floor under furniture: not a footprint
BENCH, OCH, LCH, EXC = 'v_ilev_ph_bench', 'prop_off_chair_05', 'v_ilev_leath_chr', 'ex_prop_offchair_exec_01'
CONSOLE, CONSOLE_TOP = 'v_ind_dc_desk03', 0.80                         # the dispatch consoles: a plain 2.5 x 1.08 desk (no built-in screens)
FCAB, TCAB, LCAB, LOCK, SIDE = 'v_corp_filecabtall', 'v_corp_tallcabdark01', 'v_corp_lowcabdark01', 'v_ind_rc_locker', 'v_corp_sidetable'
CHAIRS = (OCH, 'prop_off_chair_04', 'prop_off_chair_03', 'v_corp_offchair')
TOP = JD.TOP                                                               # v_corp_officedesk's top (0.90: jc_desk)
NAVY, WHITE, GOLD = (24, 38, 78), (255, 255, 255), (201, 162, 39)
def _seed(u, v): return int(abs(u * 7.31 + v * 13.17) * 10) % 97
def floor_of(room): return P1 if room in ('plobby', 'pdesk', 'pstaff1') else P2
def ceil_of(room, u, v):
    if room == 'plobby' and any(r[0] <= u <= r[1] and r[2] <= v <= r[3] for r in (P.LOBBY, P.NE)): return P.CEIL - 0.2
    return floor_of(room) + H
def thick(room, axis, line, a):
    """the lining / partition thickness on the room's side of the wall line `line` at a (along it)."""
    outer = {('u', P.WI): 0.2, ('u', P.EI): 0.2, ('v', P.SG): 0.2, ('v', P.TRENCH_N): 0.2, ('u', P.U_FOOT): 0.2,
             ('v', P.NI_LINK): 0.3 if room == 'plobby' else 0.2, ('v', P.NI_FACE): 0.3 if room == 'plobby' else 0.2, ('u', P.EG): 0.3 if room == 'plobby' else 0.2}
    for (ax, l), t in outer.items():
        if ax == axis and abs(l - line) < 0.02: return t
    S = P.STAIR_B
    if axis == 'u' and min(abs(line - S[0]), abs(line - S[1])) < 0.02 and S[2] <= a <= S[3]: return 0.15
    if axis == 'v' and min(abs(line - S[2]), abs(line - S[3])) < 0.02 and S[0] <= a <= S[1]: return 0.15
    return 0.1
def face_of(room, axis, line, side, a): return line + side * thick(room, axis, line, a)
def W(room, model, axis, line, side, a, bottom=0.0):
    """a model with its back against the wall line `line` (the room on the `side`: +1 = the larger coordinate), centred at a along
    it, its bottom `bottom` m over the floor, off the face by the trim bands there + 1 cm."""
    lo, hi = bb(model); front = FRONT.get(model, '-y'); depth = hi[1] if front == '-y' else -lo[1]
    face = face_of(room, axis, line, side, a)
    pu, pv = (face + side * 0.15, a) if axis == 'u' else (a, face + side * 0.15)
    d = face + side * (P.trim_proud(room, pu, pv, bottom, bottom + hi[2] - lo[2], axis, side) + depth + 0.01)
    if axis == 'u': h = (90.0 if side > 0 else 270.0) if front == '-y' else (270.0 if side > 0 else 90.0)
    else: h = (180.0 if side > 0 else 0.0) if front == '-y' else (0.0 if side > 0 else 180.0)
    u, v = (d, a) if axis == 'u' else (a, d)
    return (room, model, u, v, bottom, h)
def local(u, v, h, x, y):
    t = math.radians(h); return u + x * math.cos(t) - y * math.sin(t), v + x * math.sin(t) + y * math.cos(t)
def look(u, v, tu, tv):
    """the heading that turns a model's front (-y) from (u, v) toward (tu, tv)."""
    return math.degrees(math.atan2(tu - u, -(tv - v))) % 360.0
PAPERS = (('v_res_paperfolders', 0.18, 90.0), ('prop_cd_folder_pile1', 0.05, 90.0), ('v_ret_gc_trays', 0.2, 0.0), ('v_res_binder', 0.2, 0.0))
def desk(room, u, v, h=0.0, chair=None, extra=True, end=None):
    """an office workstation (jc_desk.workstation: v_corp_officedesk carries its own screens, keyboard, tower and cables; the chair at
    local +y 1.2 of (u, v, h) faces them) with clutter that varies desk to desk on its one clear end; end: [(model, y, dz, dh)] there
    instead of the clutter."""
    s = _seed(u, v); ch = chair or CHAIRS[s % len(CHAIRS)]
    if end is None:
        end = []
        if extra:
            m, y, dh = PAPERS[s % 4]
            end.append((m, y, 0.0, dh) if s % 3 != 1 else ('v_corp_cd_desklamp', 0.26, 0.0, 90.0))
            if s % 6 == 3: end.append(('prop_food_cb_donuts', -0.36, 0.0, 0.0))
            elif s % 2: end.append(('v_res_mmug' if s % 4 == 1 else 'v_ret_gc_mug03', -0.38, 0.0, 0.0))
    return JD.workstation(room, u, v, h, ch, items=end)
def console(room, u, v, h):
    """a dispatch console: a plain desk (CONSOLE), two positions (chairs at x -0.62 / +0.62 on its +y side), two screens per position
    angled in toward the chair, keyboard, mouse, radio, phone - everything inside its position's 1.25 m."""
    out = [(room, CONSOLE, u, v, 0.0, h)]
    put = lambda m, x, y, dh=180.0: out.append((room, m, *local(u, v, h, x, y), CONSOLE_TOP, (h + dh) % 360))
    for x in (-0.62, 0.62):
        out.append((room, OCH, *local(u, v, h, x, 1.05), 0.0, h))
        put('prop_monitor_01a', x - 0.25, -0.28, 170.0); put('prop_monitor_01a', x + 0.25, -0.28, 190.0)
        put('prop_keyboard_01b', x, 0.2); put('prop_mouse_01a', x + 0.34, 0.22); put('prop_police_radio_main', x - 0.45, 0.12)
        put('prop_off_phone_01', x + 0.42, -0.02)
    return out
def ceiling(room, model, u, v, h=0.0):
    """a ceiling-mounted model: its top 1 cm under the ceiling."""
    lo, hi = bb(model); return (room, model, u, v, ceil_of(room, u, v) - floor_of(room) - 0.01 - (hi[2] - lo[2]) - max(lo[2], 0.0), h)
def services(room, spaces, skip=()):
    """a smoke alarm (and a vent in rooms of 12 m2 or more) in every space, off its centre (the light sits on the centre)."""
    out = []
    for k, rs in spaces.items():
        if k in skip: continue
        r = max(rs, key=lambda q: (q[1] - q[0]) * (q[3] - q[2])); cu, cv = (r[0] + r[1]) / 2, (r[2] + r[3]) / 2
        du = 0.8 if r[1] - r[0] > 2.2 else 0.0; dv = 0.0 if du else 0.8
        out.append(ceiling(room, 'v_med_smokealarm', cu + du, cv + dv))
        if (r[1] - r[0]) * (r[3] - r[2]) >= 12.0: out.append(ceiling(room, 'v_serv_metro_ceilingvent', cu - du, cv - dv))
    return out
def cam(room, u, v, tu, tv): return ceiling(room, 'prop_cctv_cam_06a', u, v, look(u, v, tu, tv))
# ---------------- L1 public (plobby) ----------------
def public():
    L, R = [], 'plobby'
    # the lobby: bench banks south and north of the seal, the Wall of Honor island (kit) with flags, the flags by the front desk window,
    # notices, vending, plants in the NE window pocket, bins, cameras
    for cu, cv in ((38.5, -28.2), (39.2, -13.0)):
        L += [(R, BENCH, cu, cv - 0.5, 0.0, 0.0), (R, BENCH, cu, cv + 0.5, 0.0, 180.0)]
    L += [(R, 'ch_prop_ch_planter_01', 36.15, -28.2, 0.0, 0.0), (R, 'ch_prop_ch_planter_01', 40.85, -28.2, 0.0, 0.0), (R, 'ch_prop_ch_planter_01', 36.85, -13.0, 0.0, 0.0)]
    L += [(R, 'v_20_flag01', ISLAND[0] - 0.45, sum(ISLAND[2:]) / 2, 0.0, 180.0), (R, 'v_20_flag02', ISLAND[1] + 0.45, sum(ISLAND[2:]) / 2, 0.0, 180.0)]
    L += [(R, m, 33.3, v, 0.0, 90.0) for m, v in (('v_20_flag01', -18.6), ('v_20_flag02', -18.0), ('v_20_flag03', -17.4))]
    L += [W(R, BOARDS[0], 'u', P.LOB_W, 1, -28.6, 1.25), W(R, BOARDS[3], 'u', P.LOB_W, 1, -12.0, 1.25)]
    L += [W(R, 'prop_watercooler', 'u', P.LOB_W, 1, -26.6), W(R, 'prop_recyclebin_02a', 'u', P.LOB_W, 1, -25.9)]
    L += [W(R, 'prop_vend_coffe_01', 'u', P.LOB_W, 1, -15.2), W(R, 'prop_vend_soda_02', 'u', P.LOB_W, 1, -14.2)]
    L += [W(R, 'prop_fire_exting_2a', 'u', P.LOB_W, 1, -30.0, 0.5), W(R, 'v_serv_firealarm', 'u', P.LOB_W, 1, -29.6, 1.4)]
    L += [W(R, 'prop_game_clock_02', 'u', P.LOB_W, 1, -16.5, 2.6)]
    L += [(R, 'prop_plant_int_01b', 39.9, -9.95, 0.0, 0.0), (R, 'prop_plant_int_01b', 41.2, -9.95, 0.0, 0.0)]
    L += [(R, 'prop_bin_11b', 41.35, -30.4, 0.0, 0.0), (R, 'prop_bin_11b', 36.0, -9.75, 0.0, 0.0)]
    L += [cam(R, 41.5, -30.5, 37.0, -20.0), cam(R, 41.5, -9.7, 37.0, -20.0), cam(R, 33.3, -30.5, 38.0, -20.0)]
    L += [ceiling(R, 'v_med_smokealarm', 37.5, v) for v in (-27.0, -18.5, -11.5)]
    # the public corridor (to the victim rooms and the press room): notices, a picture, the water cooler at its end, an extinguisher, a camera
    L += [W(R, BOARDS[1], 'u', P.LOB_W, 1, -36.4, 1.25), W(R, BOARDS[2], 'u', P.LOB_W, 1, -40.6, 1.25), W(R, 'v_med_wallpicture2', 'u', P.LOB_W, 1, -33.4, 1.35)]
    L += [W(R, 'prop_watercooler', 'v', P.GAR_N, 1, 33.6), W(R, 'prop_fire_exting_2a', 'u', P.LOB_W, 1, -43.4, 0.5), cam(R, 33.6, -31.6, 33.6, -44.0)]
    # victim rooms A / B: sofa against one wall, a coffee table on a rug, two easy chairs facing it, side table with tissues, floor lamp, plant
    for wall_v, s in ((P.LOBBY_S, -1), (P.G_EB, 1)):                       # the sofa's wall line, and the way into the room from it
        mid = 38.5; f = face_of(R, 'v', wall_v, s, mid); hc = 180.0 if s < 0 else 0.0
        L += [W(R, 'v_med_p_sofa', 'v', wall_v, s, mid), W(R, 'v_med_wallpicture1', 'v', wall_v, s, mid, 1.35)]
        L += [(R, 'apa_mp_h_01_acc_rug', mid, f + s * 1.75, 0.0, 0.0), (R, 'v_med_p_coffeetable', mid, f + s * 1.85, 0.0, 0.0),
              (R, 'v_res_tissues', mid + 0.3, f + s * 1.75, 0.40, 0.0), (R, 'v_res_mmug', mid - 0.3, f + s * 1.95, 0.40, 0.0)]
        L += [(R, 'v_med_p_easychair', mid - 1.2, f + s * 3.25, 0.0, hc), (R, 'v_med_p_easychair', mid + 1.2, f + s * 3.25, 0.0, hc)]
        L += [(R, 'v_med_p_sidetable', 36.45, f + s * 0.5, 0.0, 0.0), (R, 'v_res_tissues', 36.45, f + s * 0.5, 0.62, 30.0),
              (R, 'v_med_p_floorlamp', 40.55, f + s * 0.6, 0.0, 0.0), (R, 'prop_plant_int_02a', 41.2, f + s * 3.6, 0.0, 0.0)]
    # the press room: the podium wall (badge + lettering: art()), the lectern (kit) between two flags, chairs in two rows, the TV camera
    L += [(R, 'v_20_flag01', 36.2, -43.75, 0.0, 0.0), (R, 'v_20_flag03', 40.3, -43.75, 0.0, 0.0)]
    L += [(R, 'prop_off_chair_04', u, v, 0.0, 0.0) for v in (-41.9, -41.0) for u in (36.6, 37.8, 39.0)]   # (the door's lane: u < 35.9)
    L += [(R, 'prop_tv_cam_02', 40.9, -41.0, 0.0, 210.0), W(R, 'prop_game_clock_02', 'v', P.G_EB, -1, 38.25, 2.05)]
    # the hall: a bench facing the property / records windows, notices, planters beside the galleria link, an extinguisher
    L += [W(R, BENCH, 'v', P.NI_LINK, -1, 26.2), W(R, BOARDS[4], 'v', P.NI_LINK, -1, 30.6, 1.25), W(R, 'v_med_wallpicture2', 'v', P.NI_LINK, -1, 23.4, 1.35)]
    L += [(R, 'ch_prop_ch_planter_01', 17.95, -8.1, 0.0, 0.0), (R, 'ch_prop_ch_planter_01', 22.05, -8.1, 0.0, 0.0)]
    L += [W(R, 'prop_fire_exting_2a', 'v', P.NI_LINK, -1, 28.4, 0.5), W(R, 'prop_bin_11b', 'v', P.NI_LINK, -1, 32.1), cam(R, 18.0, -7.8, 30.0, -9.0)]
    # the public restrooms: jc3_police_wet.l1_public()
    L += services(R, P.SPACES_LOBBY, skip=('lobby',))
    return L
# ---------------- L1 front of house (pdesk) ----------------
def front():
    L, R = [], 'pdesk'
    # the front desk: two clerk stations at the counter, the feature wall behind them (art), low cabinets under it, a clock
    for v in (-23.4, -20.6):
        L += [(R, OCH, 31.25, v, 0.0, 90.0), (R, 'prop_monitor_w_large', 32.3, v, 1.05, 270.0), (R, 'prop_keyboard_01b', 31.95, v, 1.05, 270.0),
              (R, 'prop_mouse_01a', 31.95, v - 0.38, 1.05, 270.0)]
    L += [(R, 'prop_police_radio_main', 32.35, -22.0, 1.05, 270.0), (R, 'v_ret_gc_phone', 32.25, -24.2, 1.10, 280.0), (R, 'v_ret_gc_trays', 32.3, -19.8, 1.15, 270.0),
          (R, 'p_amb_clipboard_01', 32.4, -21.4, 1.24, 260.0)]
    L += [W(R, LCAB, 'u', 28.0, 1, v) for v in (-23.0, -20.9)] + [(R, 'prop_printer_02', 28.45, -23.0, 0.89, 90.0), (R, 'v_res_paperfolders', 28.4, -20.6, 1.0, 90.0)]
    L += [W(R, 'prop_game_clock_02', 'v', -17.9, -1, 30.4, 1.9), W(R, 'v_serv_firealarm', 'v', -17.9, -1, 28.9, 1.4)]
    # dispatch: two consoles (four positions) facing the CCTV wall, the city map, a cabinet
    L += console(R, 24.835, -23.9, 270.0) + console(R, 24.835, -21.3, 270.0)
    L += [W(R, 'prop_tv_flat_01', 'u', P.DESK_W, 1, -23.9, 1.05), W(R, 'prop_tv_flat_01', 'u', P.DESK_W, 1, -21.3, 1.05)]
    L += [W(R, 'v_47_map02', 'v', -26.0, 1, 24.95, 0.95), W(R, TCAB, 'u', 28.0, -1, -19.2)]   # (2j: no rack in front of the consoles)
    # the watch commander: his desk facing the door, the CCTV monitor, the roster whiteboard, a rack, lockers, a visitor's chair
    L += desk(R, 29.6, -27.55, 180.0, chair=EXC, end=[('prop_cctv_mon_02', 0.05, 0.0, 0.0)])
    L += [W(R, 'v_med_cor_whiteboard', 'v', P.DESK_S, 1, 27.2, 1.0), W(R, 'v_serv_tvrack', 'u', P.LOB_W, -1, -28.0)]
    L += [W(R, LOCK, 'u', P.DESK_W, 1, v) for v in (-29.25, -28.45, -27.65)] + [(R, 'v_corp_lazychair', 31.6, -26.75, 0.0, 225.0)]
    # copy and supply: copier, mail slots, shelving with paper boxes, shredder, a side table with a printer
    L += [W(R, 'prop_copier_01', 'u', P.LOB_W, -1, -15.9), W(R, 'v_corp_postboxa', 'u', P.DESK_W, 1, -15.6), W(R, 'v_corp_offshelfdark', 'v', P.HALL_S, -1, 28.5)]
    L += [(R, 'prop_paper_box_01', 27.2, -14.5, 0.0, 10.0), (R, 'prop_paper_box_02', 27.2, -14.5, 0.36, 350.0), (R, 'prop_paper_box_03', 29.8, -14.4, 0.0, 0.0)]
    L += [W(R, 'prop_shredder_01', 'v', -17.9, 1, 29.6), W(R, SIDE, 'v', -17.9, 1, 30.95), (R, 'prop_printer_01', 30.95, -17.15, 0.88, 0.0)]
    # the property window: clerk, shelving for bagged property, boxes; the records window: clerk, forms cabinets, ticket printer
    for c0, c1, sh in ((24.6, 27.8, 'property'), (29.2, 32.4, 'records')):
        cu = (c0 + c1) / 2
        L += [(R, OCH, cu, -11.45, 0.0, 180.0), (R, 'prop_monitor_01a', cu - 0.6, -10.35, 1.05, 0.0), (R, 'prop_keyboard_01a', cu - 0.6, -10.7, 1.05, 0.0)]
        if sh == 'property':
            L += [W(R, 'v_corp_cabshelves01', 'u', 28.4, -1, -12.05), (R, 'v_20_evidence01', cu + 0.7, -10.4, 1.05, 10.0), (R, 'prop_cs_cardbox_01', 24.6, -12.9, 0.0, 0.0)]
        else:
            L += [W(R, FCAB, 'u', P.LOB_W, -1, v) for v in (-12.9, -12.3)] + [(R, 'prop_printer_02', cu + 0.8, -10.4, 1.05, 0.0), (R, 'v_ret_gc_folder1', cu + 0.2, -10.35, 1.05, 0.0)]
    L += [cam(R, 24.4, -29.6, 30.0, -27.0), cam(R, 32.4, -17.5, 30.0, -22.0)]
    L += services(R, P.SPACES_DESK)
    return L
def dress():
    import jc3_police_dress2 as D2, jc3_police_wet as WET
    L = public() + front() + D2.staff1() + D2.staff2() + WET.props()
    return [(r, m, u, v, floor_of(r) + z, h) for r, m, u, v, z, h in L]
# ---------------- signs ----------------
PLATE = {   # inner door: (plate text, the approach side of its wall: +1 = the larger coordinate)
    ('pstaff1', 'break'): ('BREAK ROOM', -1), ('pstaff1', 'brief'): ('BRIEFING', 1), ('pstaff1', 'fitness'): ('FITNESS', 1), ('pstaff1', 'men'): ("MEN'S LOCKERS", 1),
    ('pstaff1', 'men showers'): ('SHOWERS', 1), ('pstaff1', 'women'): ("WOMEN'S LOCKERS", 1), ('pstaff1', 'evid'): ('EVIDENCE', 1), ('pstaff1', 'cage'): ('EVIDENCE CAGE', 1),
    ('pstaff1', 'shelving'): ('EVIDENCE STORE', 1), ('pstaff1', 'arm'): ('ARMORY', 1), ('pstaff1', 'armory gate'): ('WEAPONS CAGE', 1), ('pstaff1', 'report'): ('REPORT WRITING', -1), ('pstaff1', 'equip'): ('PATROL EQUIPMENT', -1),
    ('pstaff1', 'rollcall'): ('ROLL CALL', -1), ('pdesk', 'front'): ('FRONT DESK', -1), ('pdesk', 'watch'): ('WATCH COMMANDER', 1), ('pdesk', 'copy'): ('COPY / SUPPLY', -1),
    ('pdesk', 'property'): ('PROPERTY', -1), ('pdesk', 'records'): ('RECORDS', -1), ('plobby', 'victim a'): ('INTERVIEW A', -1), ('plobby', 'victim b'): ('INTERVIEW B', -1),
    ('plobby', 'press'): ('PRESS ROOM', -1), ('plobby', 'men wc'): ('MEN', 1), ('plobby', 'women wc'): ('WOMEN', 1),
    ('pstaff2', 'commander'): ('COMMANDER', 1), ('pstaff2', 'assistant'): ('COMMAND OFFICE', 1), ('pstaff2', 'conf'): ('CONFERENCE', 1), ('pstaff2', 'prep'): ('INTERVIEW PREP', 1),
    ('pstaff2', 'lieutenant'): ('DET. LIEUTENANT', 1), ('pstaff2', 'detectives'): ('DETECTIVE BUREAU', 1), ('pstaff2', 'it'): ('IT / SERVERS', -1), ('pstaff2', 'training'): ('TRAINING', -1),
    ('pstaff2', 'ia'): ('INTERNAL AFFAIRS', -1), ('pstaff2', 'analysis'): ('CRIME ANALYSIS', 1), ('pstaff2', 'men wc'): ('MEN', -1), ('pstaff2', 'women wc'): ('WOMEN', -1),
    ('pstaff2', 'detectives e'): ('DETECTIVES', -1), ('pstaff2', 'records'): ('RECORDS', -1), ('pstaff2', 'east wing'): ('PATROL SUPERVISORS', -1),
    ('pstaff2', 'patrol lt'): ('PATROL LIEUTENANT', -1), ('pstaff2', 'sergeants'): ('SERGEANTS', -1), ('pstaff2', 'quartermaster'): ('QUARTERMASTER', -1)}
def _edge(room, ax, plane, a0):
    """the stretch of wall (lo, hi along it) that holds the door: the shared edge of the two spaces it joins."""
    sp = {'plobby': P.SPACES_LOBBY, 'pdesk': P.SPACES_DESK, 'pstaff1': P.SPACES1, 'pstaff2': P.SPACES2}[room]; best = None
    for rs in sp.values():
        for r in rs:
            for x in ((r[0], r[1]) if ax == 'u' else (r[2], r[3])):
                if abs(x - plane) > 1e-6: continue
                lo, hi = (r[2], r[3]) if ax == 'u' else (r[0], r[1])
                if lo - 1e-6 <= a0 and a0 + 1.4 <= hi + 1e-6: best = (lo, hi) if best is None else (max(best[0], lo), min(best[1], hi))
    return best
MESH_PLATES = {('pstaff1', 'cage'), ('pstaff1', 'arm'), ('pstaff1', 'armory gate')}   # doors in mesh walls
def _wall_spans(room, ax, plane, s):
    """(a0, a1, z0, z1) of every prop standing against the wall `plane` on side s (within 0.8 m of it): a plate never goes behind one
    (2026-11-11, Antonio: the quartermaster's cabinets covered its plate)."""
    out = []
    for r, m, u, v, z, h in dress():
        if r != room or m.lower() not in A: continue
        lo, hi = bb(m); t = math.radians(h); c, sn = math.cos(t), math.sin(t)
        pts = [(u + x * c - y * sn, v + x * sn + y * c) for x in (lo[0], hi[0]) for y in (lo[1], hi[1])]
        n_ = [p[0] if ax == 'u' else p[1] for p in pts]; a_ = [p[1] if ax == 'u' else p[0] for p in pts]
        near = min(n_) - plane if s > 0 else plane - max(n_)
        if -0.05 <= near <= 0.8: out.append((min(a_), max(a_), z + max(0.0, -lo[2]) + lo[2], z + max(0.0, -lo[2]) + hi[2]))
    return out
def _clear(spans, c0, c1, z0, z1):
    return not any(a0 < c1 + 0.05 and a1 > c0 - 0.05 and b0 < z1 and b1 > z0 for a0, a1, b0, b1 in spans)
def signs():
    out = []
    for room, name, z, ax, plane, a0 in P.INNER_DOORS:                    # a name plate beside each door on its approach side (or over it)
        text, s = PLATE[(room, name)]; lo, hi = _edge(room, ax, plane, a0); a1 = a0 + 1.4
        w = min(0.9, 0.12 + 0.055 * len(text)); zz = z + 1.6; sp = _wall_spans(room, ax, plane, s)
        ok = lambda c: lo + 0.15 <= c - w / 2 and c + w / 2 <= hi - 0.15 and _clear(sp, c - w / 2, c + w / 2, zz - 0.07, zz + 0.07)
        c = next((c for c in (a1 + 0.12 + w / 2, a0 - 0.12 - w / 2) if ok(c)), None)
        if c is None: c = (a0 + a1) / 2; zz = z + 2.49                     # neither side is clear: over the door head
        f = plane + s * 0.1
        if (room, name) in MESH_PLATES: c = (a0 + a1) / 2; zz = z + 2.45; f = plane + s * 0.06      # on the steel door head (a mesh wall)
        out.append((room, (f, c, zz) if ax == 'u' else (c, f, zz), ('+' if s > 0 else '-') + ax, w, 0.14, [text], 'JC plate ' + ''.join(ch for ch in text if ch.isalnum() or ch == ' '), NAVY, WHITE))
    for name, a0 in (('INTERVIEW 1', 11.6), ('OBSERVATION 1', 14.35), ('OBSERVATION 2', 16.45), ('INTERVIEW 2', 19.5)):
        out.append(('pstaff2', (a0 + 0.7, -48.93 + 0.1, P2 + 2.5), '+v', 0.9, 0.14, [name], f'JC plate {name}', NAVY, WHITE))
    out += [('pstaff1', (P.COR[0] + 0.15, -33.75, P1 + 1.6), '+u', 0.5, 0.14, ['STAIRS'], 'JC plate STAIRS', NAVY, WHITE),
            ('pstaff2', (P.COR[0] + 0.15, -33.75, P2 + 1.6), '+u', 0.5, 0.14, ['STAIRS'], 'JC plate STAIRS', NAVY, WHITE),
            ('plobby', (23.0, P.HALL_N + 0.1, P1 + 2.5), '+v', 1.3, 0.16, ['POLICE - STAFF ONLY'], 'JC plate STAFF ONLY', NAVY, WHITE),
            ('plobby', (26.2, P.HALL_N + 0.1, P1 + 2.45), '+v', 1.4, 0.2, ['PROPERTY'], 'JC sign PROPERTY', NAVY, GOLD),
            ('plobby', (30.8, P.HALL_N + 0.1, P1 + 2.45), '+v', 1.4, 0.2, ['RECORDS'], 'JC sign RECORDS', NAVY, GOLD),
            ('plobby', (P.LOB_W + 0.1, -22.0, P1 + 2.55), '+u', 2.2, 0.3, ['FRONT DESK'], 'JC lobby FRONT DESK', NAVY, GOLD)]
    S = P.STAIR_B
    for lv, z in (('L1', P1), ('L2', P2)): out.append(('pstair', (S[1] - 0.15, -33.0, z + 1.7), '-u', 0.4, 0.4, [lv], f'JC floor {lv}', (230, 190, 30), (20, 20, 20)))
    out.append(('pstair', (S[0] + 1.0, S[2] + 0.15, 25.6 + 1.7), '+v', 0.4, 0.4, ['B1'], 'JC floor B1', (230, 190, 30), (20, 20, 20)))
    return out
# ---------------- the Cleveland insignia (jc3_redesign_plan.INSIGNIA, the 12 spots) ----------------
LECTERN = (37.95, 38.55, -43.6, -43.1)
ISLAND = (36.0, 38.8, -17.3, -17.0)                                        # the Wall of Honor (u0, u1, v0, v1), 2.4 m high
def art():
    import jc3_pgarage as G
    return [('plobby', 'panel_lobbyband', 'u', P.LOB_W + 0.1, 1, -22.0, P1 + 4.2, 4.4, 0.7, 0.1, False),            # on the navy band (kit)
            ('pdesk', 'panel_frontdesk', 'u', face_of('pdesk', 'u', 28.0, 1, -22.0), 1, -21.95, P1 + 1.75, 3.2, 1.2, 0.065, False),
            ('plobby', 'insignia_patch', 'u', P.EG, -1, -24.53, P1 + 3.15, 0.9, 0.9, 0.03, True),                    # the transom: from inside
            ('plobby', 'insignia_patch', 'u', P.EG, 1, -24.53, P1 + 3.15, 0.9, 0.9, -0.045, True),                   # ... and from the plaza
            ('pstaff1', 'panel_rollcall', 'v', P.G_BREAK - 0.1, -1, 16.3, P1 + 1.75, 3.6, 1.4, 0.065, False),
            ('plobby', 'panel_press', 'v', P.GAR_N + 0.1, 1, 38.25, P1 + 1.75, 3.6, 1.4, 0.065, False),
            ('plobby', 'insignia_badge', 'v', LECTERN[3], 1, sum(LECTERN[:2]) / 2, P1 + 0.75, 0.36, 0.36, 0.01, True),
            ('plobby', 'panel_honor', 'v', ISLAND[3], 1, 37.4, P1 + 1.5, 2.4, 1.2, 0.065, False),
            ('plobby', 'panel_honor', 'v', ISLAND[2], -1, 37.4, P1 + 1.5, 2.4, 1.2, 0.065, False),
            ('pstaff2', 'panel_plaque', 'v', P.NI_LINK - 0.2, -1, 14.0, P2 + 1.8, 0.9, 0.9, 0.065, False),
            ('pstaff2', 'panel_patchpanel', 'u', P.COR[0] - 0.1, -1, -20.4, P2 + 1.7, 1.2, 1.2, 0.065, False),
            ('pstaff2', 'panel_patchpanel', 'u', P.LOB_W - 0.1, -1, -15.5, P2 + 1.7, 1.2, 1.2, 0.065, False),
            ('pstaff1', 'panel_patchpanel', 'v', P.SG + 0.2, 1, 18.6, P1 + 1.75, 1.2, 1.2, 0.065, False),            # the armory's south wall
            ('pdeck', 'panel_fleet', 'u', G.U_FOOT - 0.1, -1, sum(G.DIV) / 2, G.ZB + 1.45, 1.1, 1.4, 0.065, False)]
def floor_art():
    import jc3_pgarage as G
    return [('plobby', 'insignia_seal', 37.45, -21.5, 2.6, 180.0, P1 + 0.004), ('pdeck', 'insignia_seal', 19.25, -37.0, 1.6, 270.0, G.ZB + 0.005)]
# ---------------- kit (no Rockstar prop) ----------------
def kit():
    import jc3_police_dress2 as D2
    u0, u1, v0, v1 = ISLAND; a0, a1, b0, b1 = LECTERN
    out = [('plobby', (P.LOB_W + 0.1, -26.5, P1 + 3.6), (P.LOB_W + 0.135, -17.5, P1 + 4.8), 'navy', False),           # the feature band over the counter
           ('plobby', (u0, v0, P1), (u1, v1, P1 + 2.4), 'brick', True), ('plobby', (u0 - 0.01, v0 - 0.01, P1 + 2.4), (u1 + 0.01, v1 + 0.01, P1 + 2.43), 'gold', False),
           ('plobby', (a0, b0, P1), (a1, b1, P1 + 1.1), 'panel', True), ('plobby', (a0 - 0.05, b0 - 0.05, P1 + 1.1), (a1 + 0.05, b1 + 0.05, P1 + 1.13), 'granite', False)]
    import jc3_police_wet as WET
    return out + D2.kit2() + WET.kit()

