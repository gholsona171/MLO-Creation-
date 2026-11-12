"""Area 3 Police HQ dressing, the staff floors (2026-10-31 redesign; helpers and the public side in jc3_police_dress.py). Every room
furnished for what it is (jc3_redesign_plan.ROOMS), Rockstar's props throughout; kit2() = the pod screens (no Rockstar prop). The wet rooms (showers, toilet stalls,
counters, urinals) are jc3_police_wet.py. Coordinates checked against each room's faces, its doors' swing zones (0.8 m each side) and the other props
(jc3_footprint.py / jc3_dress_check.py are the gates)."""
import jc3_police as P
from jc3_police_dress import (W, desk, ceiling, services, cam, local, BOARDS, BENCH, OCH, LCH, EXC, FCAB, TCAB, LCAB, LOCK, SIDE, TOP)
P1, P2, COR = P.P1, P.P2, P.COR
PODS2 = [(13.5, -33.6), (13.5, -38.3), (13.5, -43.0), (16.6, -33.6), (16.6, -38.3), (16.6, -43.0), (19.85, -43.3)]   # detectives (west)
PODS2E = [(27.0, -38.4), (29.95, -38.4)]                                # (the doors' lanes: u 24 .. 25.2 and 31.6 .. 32.8)                                   # detectives (east)
LEVELS = {'prop_shelves_01': (0.08, 0.74, 1.31, 1.86), 'v_ind_cf_shelf': (0.09, 0.74, 1.31, 1.86)}   # shelf tops (measured: up-facing vertices)
EVID = ('v_res_filebox01', 'prop_cs_cardbox_01', 'hei_prop_heist_box', 'v_20_evidence01', 'prop_cs_package_01', 'prop_paper_box_01')
ARMS = ('prop_box_guncase_01a', 'prop_box_ammo04a', 'prop_box_ammo02a', 'prop_gun_case_02', 'prop_box_guncase_02a', 'prop_ld_ammo_pack_03')   # (the crate never on the bottom shelf: slots 0/2/4 there)
def stock(room, shelf, u, v, h, items):
    """every level of a shelving unit filled: three slots along it (x -0.85 / 0 / +0.85 in the unit's frame), items cycling per slot."""
    from jc3_police_dress import local
    out = []
    for li, z in enumerate(LEVELS[shelf]):
        for si, x in enumerate((-0.85, 0.0, 0.85)):
            m = items[(li * 3 + si * 2) % len(items)]; out.append((room, m, *local(u, v, h, x, 0.0), z, (h + 7.0 * ((li + si) % 3)) % 360))
    return out
def pod(room, cu, cv):
    """two workstations back to back across the 1.2 m screen (kit2): users north and south, each desk's cables ending at the screen."""
    return desk(room, cu, cv + 0.56, 0.0) + desk(room, cu, cv - 0.56, 180.0)
def staff1():
    L, S = [], 'pstaff1'
    # the staff corridor: notices, extinguishers, water cooler, clock, fire alarm, cameras
    L += [W(S, BOARDS[1], 'u', COR[0], 1, -20.5, 1.25), W(S, BOARDS[2], 'u', COR[1], -1, -27.0, 1.25), W(S, BOARDS[3], 'u', COR[1], -1, -38.5, 1.25)]
    L += [W(S, BOARDS[4], 'u', COR[1], -1, -31.0, 1.25)]
    L += [W(S, 'prop_fire_exting_2a', 'u', COR[0], 1, -12.5, 0.5), W(S, 'prop_fire_exting_2a', 'u', COR[1], -1, -42.0, 0.5), W(S, 'prop_watercooler', 'u', COR[1], -1, -22.6)]
    L += [W(S, 'prop_game_clock_02', 'u', COR[0], 1, -31.9, 2.05), W(S, 'v_serv_firealarm', 'u', COR[0], 1, -45.0, 1.4)]
    L += [cam(S, 23.0, -10.4, 23.0, -40.0), cam(S, 23.0, -47.2, 23.0, -20.0)]
    # break room: kitchen run (sink, counters with coffee machine / microwave / kettle / toaster, fridge), table + four chairs, sofa under the TV, vending
    L += [W(S, 'prop_ff_sink_02', 'v', P.NI_LINK, -1, 11.6), W(S, SIDE, 'v', P.NI_LINK, -1, 13.2), W(S, SIDE, 'v', P.NI_LINK, -1, 14.25), W(S, 'v_res_tt_fridge', 'v', P.NI_LINK, -1, 15.4)]
    L += [(S, 'prop_coffee_mac_01', 13.0, -7.95, 0.88, 0.0), (S, 'prop_kettle', 13.55, -7.9, 0.88, 0.0), (S, 'prop_micro_01', 14.25, -7.95, 0.88, 0.0), (S, 'prop_toaster_01', 14.6, -8.2, 0.88, 0.0)]
    L += [(S, 'prop_table_04', 13.3, -10.4, 0.0, 0.0)] + [(S, 'prop_chair_02', u, v, 0.0, h) for u in (12.85, 13.75) for v, h in ((-11.35, 180.0), (-9.45, 0.0))]
    L += [(S, 'v_res_mmug', 13.0, -10.3, 0.8, 0.0), (S, 'prop_food_cb_donuts', 13.5, -10.5, 0.8, 20.0)]
    L += [W(S, 'v_med_p_sofa', 'v', P.G_BREAK, 1, 15.9), W(S, 'prop_tv_flat_01', 'v', P.G_BREAK, 1, 15.9, 1.15)]
    L += [W(S, 'prop_vend_soda_02', 'u', 17.5, -1, -9.2), W(S, 'prop_vend_coffe_01', 'u', 17.5, -1, -10.4), W(S, 'prop_bin_11b', 'u', 17.5, -1, -11.4)]
    L += [(S, 'prop_plant_int_01b', 11.35, -12.75, 0.0, 0.0)]
    # briefing / roll call (2026-11-01, Antonio: "desks, not a bunch of chairs"): the navy feature wall (art) between flags, the lectern
    # table, three rows of three desks facing it with two officers each, papers and folders on every desk, whiteboard, projector, clock
    L += [W(S, 'v_20_office_flag01', 'v', P.G_BREAK, -1, 12.4), W(S, 'v_20_office_flag01', 'v', P.G_BREAK, -1, 18.7)]
    L += [(S, 'v_corp_conftable2', 16.3, -15.3, 0.0, 0.0), (S, 'prop_laptop_01a', 16.7, -15.3, 0.82, 180.0), (S, 'v_res_paperfolders', 15.4, -15.4, 0.93, 0.0),
          (S, 'p_amb_clipboard_01', 17.5, -15.5, 0.82, 0.0)]
    for dv in (-17.3, -19.15, -21.0):
        for du in (13.0, 16.1, 19.2):
            L += [(S, 'v_ind_dc_desk03', du, dv, 0.0, 180.0)] + [(S, 'prop_off_chair_04', du + x, dv - 0.95, 0.0, 180.0) for x in (-0.6, 0.6)]
            k = int(du * 3 + dv) % 3
            L += [(S, ('v_res_paperfolders', 'prop_cd_folder_pile1', 'v_res_binder')[k], du - 0.6, dv - 0.1, 0.8 + (0.11 if k == 0 else 0.0), 175.0),
                  (S, 'p_amb_clipboard_01' if k != 1 else 'v_20_copfile01', du + 0.6, dv - 0.1, 0.8, 190.0), (S, 'v_res_mmug', du + 0.15, dv + 0.2, 0.8, 0.0)]
    L += [W(S, 'v_med_cor_whiteboard', 'u', COR[0], -1, -19.6, 1.15), W(S, 'prop_game_clock_02', 'v', P.G_FIT, 1, 16.3, 2.05), ceiling(S, 'v_res_mountedprojector', 16.3, -18.4, 180.0)]
    # fitness: weight bench, squat rack, muscle bench, two weight racks, exercise bike, yoga mats, a notice board
    L += [(S, 'prop_weight_bench_02', 13.5, -24.5, 0.0, 0.0), (S, 'prop_weight_squat', 17.0, -24.1, 0.0, 0.0), (S, 'prop_muscle_bench_02', 19.9, -24.6, 0.0, 0.0)]
    L += [W(S, 'prop_weight_rack_01', 'v', P.G_BRIEF, 1, 15.5), W(S, 'prop_weight_rack_02', 'v', P.G_BRIEF, 1, 18.9), (S, 'prop_exer_bike_01', 11.6, -25.6, 0.0, 90.0)]
    L += [(S, 'v_res_fa_yogamat002', 20.8, -23.0, 0.0, 90.0), (S, 'v_res_fa_yogamat002', 21.1, -23.0, 0.0, 90.0), W(S, BOARDS[0], 'v', P.G_FIT, -1, 18.5, 1.25)]
    # men's locker room: two locker runs (north, south), a long bench, a short bench, coat hooks on the stair wall
    L += [W(S, LOCK, 'v', P.G_BRIEF, -1, 11.25 + 0.8 * i) for i in range(8)] + [W(S, LOCK, 'v', P.G_BRIEF, -1, u) for u in (17.65, 18.45, 19.25, 20.05)]
    L += [W(S, LOCK, 'v', P.G_MEN, 1, 11.25 + 0.8 * i) for i in range(5)]
    L += [(S, 'v_res_fh_benchlong', 14.0, -28.9, 0.0, 0.0), (S, 'hei_heist_stn_benchshort', 19.6, -28.4, 0.0, 0.0)]
    L += [W(S, 'prop_coathook_01', 'v', -30.0, 1, u, 1.65) for u in (19.0, 20.0, 21.0)]
    # men's showers / WC: jc3_police_wet.l1_showers()
    # women's locker room: lockers on the west wall, bench, coat hooks (its counter, stalls and showers: jc3_police_wet.l1_showers())
    L += [W(S, LOCK, 'u', P.WI, 1, v) for v in (-36.3, -37.1, -37.9, -38.7, -39.5)] + [(S, 'v_res_fh_benchlong', 14.0, -37.8, 0.0, 0.0)]
    L += [W(S, 'prop_coathook_01', 'v', P.G_LOCK, 1, u, 1.65) for u in (11.6, 12.6, 13.6)]
    # evidence intake: the pass-through evidence lockers, the intake desk with bags, a packing bench, boxes
    L += [W(S, FCAB, 'v', P.G_LOCK, -1, 16.6 + 0.6 * i) for i in range(6)]
    L += desk(S, 19.0, -41.7, 180.0, end=[('v_20_evidence01', 0.0, 0.0, 90.0)])
    L += [W(S, 'prop_tool_bench01', 'u', COR[0], -1, -40.9), (S, 'v_20_evidence01', 21.5, -40.9, 0.86, 90.0), (S, 'v_res_filebox01', 16.6, -44.0, 0.0, 0.0)]
    # evidence cage (mesh walls: the build): three shelving runs stocked on every level with boxes and bagged evidence, crates, a camera
    L += [W(S, 'v_ind_cf_shelf', 'u', 16.0, 1, -46.7), W(S, 'v_med_cor_shelfrack', 'u', COR[0], -1, -46.2)]
    L += stock(S, 'v_ind_cf_shelf', *W(S, 'v_ind_cf_shelf', 'u', 16.0, 1, -46.7)[2:4], 90.0, EVID)
    L += [(S, 'prop_cardbordbox_03a', 20.6, -48.3, 0.0, 0.0), (S, 'prop_box_wood05a', 17.8, -45.4, 0.0, 0.0), (S, 'v_serv_plas_boxgt2', 17.1, -47.0, 0.0, 0.0)]
    L += [cam(S, 16.4, -48.6, 20.0, -45.0)]
    # evidence store: four runs of open shelving, every level stocked, crates
    for v in (-41.2, -43.4, -45.6, -47.8): L += [(S, 'prop_shelves_01', 12.9, v, 0.0, 0.0)] + stock(S, 'prop_shelves_01', 12.9, v, 0.0, EVID)
    L += [(S, 'prop_cardbordbox_03a', 15.2, -47.9, 0.0, 0.0), (S, 'prop_cardbordbox_03a', 15.25, -44.6, 0.0, 0.0), cam(S, 15.6, -40.5, 12.0, -46.0)]
    # armory (the cage behind the mesh line G_AG: everything below is behind mesh): gun lockers (east wall), four shelving runs of gun
    # cases and ammunition, wall gun racks and the patch (art) on the south
    # wall, the cleaning tables, ammo crates, a flag
    L += [W(S, LOCK, 'u', P.U_FOOT, -1, v) for v in (-55.8, -55.0, -54.2, -53.4, -52.6, -51.8)]
    for u in (11.6, 13.6):
        for v in (-51.95, -54.95): L += [(S, 'prop_shelves_01', u, v, 0.0, 90.0)] + stock(S, 'prop_shelves_01', u, v, 90.0, ARMS)
    L += [W(S, 'prop_cs_gunrack', 'v', P.SG, 1, u, 1.2) for u in (14.8, 16.4)] + [W(S, 'prop_box_guncase_03a', 'v', P.SG, 1, u, 0.0) for u in (14.8, 16.4)]
    L += [(S, SIDE, 17.4, -52.8, 0.0, 0.0), (S, SIDE, 18.42, -52.8, 0.0, 0.0), (S, 'prop_gun_case_01', 17.9, -52.95, 0.88, 0.0),
          (S, 'prop_box_ammo01a', 17.2, -52.6, 0.88, 20.0), (S, 'prop_box_ammo02a', 17.5, -52.55, 0.88, 0.0), (S, 'prop_box_ammo07a', 18.7, -52.6, 0.88, 0.0),
          (S, 'prop_ld_ammo_pack_01', 18.3, -52.5, 0.88, 30.0), (S, 'prop_ld_ammo_pack_02', 18.5, -52.75, 0.88, 0.0)]
    L += [W(S, 'prop_box_ammo03a', 'v', P.SG, 1, 19.3), (S, 'prop_box_ammo04a', 19.3, -55.75, 0.44, 0.0), (S, 'v_20_flag01', 20.15, -55.6, 0.0, 0.0)]
    L += [(S, 'ex_prop_exec_guncase', 19.9, -51.0, 0.0, 270.0), cam(S, 11.0, -56.2, 16.0, -52.0)]
    # the issue vestibule (outside the cage): the issue desk with the sign-out sheet, a notice
    L += [(S, SIDE, 15.0, -49.75, 0.0, 0.0), (S, 'p_amb_clipboard_01', 14.8, -49.75, 0.88, 0.0), (S, 'prop_cs_walkie_talkie', 15.3, -49.7, 0.88 + 0.13, 90.0)]
    # report writing: six desks in two rows, printer table, copier, a notice board, clock, plant
    for u in (26.2, 28.8, 31.4): L += desk(S, u, -32.4, 180.0) + desk(S, u, -38.0, 0.0)
    L += [W(S, SIDE, 'v', -41.3, 1, 26.0), (S, 'prop_printer_02', 26.0, -40.85, 0.88, 180.0), W(S, 'prop_copier_01', 'u', P.LOB_W, -1, -35.2)]
    L += [W(S, BOARDS[2], 'v', P.DESK_S, -1, 28.5, 1.3), W(S, 'prop_game_clock_02', 'u', P.LOB_W, -1, -39.5, 2.05), (S, 'prop_plant_int_02a', 32.1, -40.6, 0.0, 0.0)]
    # patrol equipment: charging / kit shelving, radios on a table, lockers, a bench, vest hooks, cones and kit bags
    L += [W(S, 'v_corp_cabshelves01', 'v', -41.3, -1, u) for u in (26.6, 29.4)] + [W(S, SIDE, 'u', P.LOB_W, -1, -42.4)]
    L += [(S, 'prop_cs_walkie_talkie', 32.05, v, 0.88 + 0.13, 90.0) for v in (-42.7, -42.5, -42.3, -42.1)]
    L += [W(S, LOCK, 'v', P.TRENCH_N, 1, 25.2 + 0.8 * i) for i in range(8)] + [(S, 'v_res_fh_benchlong', 28.0, -44.6, 0.0, 0.0)]
    L += [W(S, 'prop_coathook_01', 'u', COR[1], 1, v, 1.65) for v in (-43.0, -42.2)]
    L += [(S, 'prop_mp_cone_02', 31.6, -44.0, 0.0, 0.0), (S, 'prop_mp_cone_02', 31.6, -43.6, 0.0, 0.0), (S, 'v_ind_rc_workbag', 27.0, -45.6, 0.0, 20.0), (S, 'prop_big_bag_01', 29.5, -45.7, 0.0, 0.0)]
    # roll call corridor: a locker run, a bench, a notice board and the shift whiteboard, a camera
    L += [W(S, LOCK, 'v', P.GAR_N, -1, 34.4 + 0.8 * i) for i in range(10)] + [(S, 'v_res_fh_benchlong', 38.0, -46.2, 0.0, 0.0)]
    L += [W(S, BOARDS[1], 'v', P.TRENCH_N, 1, 36.0, 1.25), W(S, 'v_med_cor_whiteboard', 'v', P.TRENCH_N, 1, 42.5, 1.15), cam(S, 44.2, -45.0, 36.0, -46.0)]
    L += services(S, P.SPACES1)
    return L
def staff2():
    L, S = [], 'pstaff2'
    # the commander's office: his desk under the badge plaque between flags, guest chairs, the meeting table, bookshelf with awards, safe, TV, plant
    L += desk(S, 14.0, -9.6, 0.0, chair=EXC) + [(S, 'v_corp_lazychair', 13.4, -11.0, 0.0, 180.0), (S, 'v_corp_lazychair', 14.6, -11.0, 0.0, 180.0)]
    L += [W(S, 'v_20_office_flag01', 'v', P.NI_LINK, -1, 12.6), W(S, 'v_20_office_flag01', 'v', P.NI_LINK, -1, 15.4)]
    L += [(S, 'v_corp_conftable3', 13.8, -15.3, 0.0, 0.0)] + [(S, LCH, u, v, 0.0, h) for u in (12.6, 13.8, 15.0) for v, h in ((-16.5, 180.0), (-14.1, 0.0))]
    L += [(S, 'v_res_paperfolders', 13.3, -15.35, 0.93, 0.0), (S, 'v_res_mmug', 14.4, -15.2, 0.82, 0.0)]
    L += [W(S, 'v_res_tre_smallbookshelf', 'u', 17.5, -1, -9.0), (S, 'ex_prop_exec_award_gold', 17.2, -8.7, 0.93, 270.0), (S, 'ex_prop_exec_award_diamond', 17.2, -9.3, 0.93, 270.0)]
    L += [W(S, 'm23_2_prop_m32_safe_01a', 'u', 17.5, -1, -16.8), W(S, 'v_med_cor_flatscreentv', 'v', P.G_CAPT, 1, 13.8, 1.25)]
    L += [(S, 'prop_plant_int_02a', 11.35, -8.1, 0.0, 0.0), W(S, 'prop_coathook_01', 'u', 17.5, -1, -13.4, 1.65)]
    # the executive assistant: reception desk facing the corridor door, waiting chairs, filing cabinets, plant
    L += desk(S, 19.4, -15.6, 90.0) + [W(S, 'v_corp_bk_chair1', 'u', COR[0], -1, v) for v in (-9.8, -10.9)] + [W(S, FCAB, 'v', P.NI_LINK, -1, u) for u in (18.3, 18.9, 19.5)]
    L += [(S, 'prop_plant_int_01b', 21.3, -17.1, 0.0, 0.0)]
    # command conference: two tables end to end, leather chairs round them, TV, credenza, flags, plant (the patch: art())
    L += [(S, 'v_corp_conftable2', 14.92, -22.3, 0.0, 0.0), (S, 'v_corp_conftable2', 18.56, -22.3, 0.0, 0.0)]
    L += [(S, LCH, u, v, 0.0, h) for u in (13.7, 15.0, 16.3, 17.6, 18.9, 20.1) for v, h in ((-23.55, 180.0), (-21.05, 0.0))] + [(S, LCH, 12.45, -22.3, 0.0, 90.0)]
    L += [(S, 'v_res_paperfolders', 15.6, -22.4, 0.93, 0.0), (S, 'prop_laptop_01a', 17.0, -22.1, 0.82, 200.0), (S, 'p_amb_coffeecup_01', 18.2, -22.5, 0.82, 0.0)]
    L += [W(S, 'v_med_cor_flatscreentv', 'v', P.G_BRIEF, 1, 16.3, 1.25), W(S, SIDE, 'v', P.G_CAPT, -1, 16.3), W(S, 'v_20_office_flag01', 'v', P.G_CAPT, -1, 14.6),
          W(S, 'v_20_office_flag01', 'v', P.G_CAPT, -1, 18.0), (S, 'prop_plant_int_01b', 21.3, -18.5, 0.0, 0.0)]
    # the detective lieutenant: desk facing the case whiteboard, cabinets, a visitor's chair, plant
    L += desk(S, 14.5, -28.0, 180.0) + [W(S, 'v_med_cor_whiteboard', 'v', P.G_BRIEF, -1, 14.5, 1.0)] + [W(S, TCAB, 'v', P.G_MEN, 1, u) for u in (11.4, 12.0)]
    L += [(S, 'v_corp_lazychair', 16.6, -27.6, 0.0, 225.0), (S, 'prop_plant_int_02a', 17.6, -30.5, 0.0, 0.0)]
    # interview prep: a table against the stair wall, two chairs, the case board
    L += [W(S, SIDE, 'v', P.STAIR_B[3], 1, 20.15), (S, OCH, 19.2, -29.35, 0.0, 90.0), (S, OCH, 21.1, -29.35, 0.0, 270.0), (S, 'v_20_copfile02', 20.1, -29.35, 0.882, 10.0)]
    L += [W(S, BOARDS[2], 'v', P.G_BRIEF, -1, 20.2, 1.25)]
    # detectives (west): desk pods with screens (kit2), case boards, filing cabinets, copier, water cooler
    for cu, cv in PODS2: L += pod(S, cu, cv)
    L += [W(S, BOARDS[0], 'v', P.G_MEN, -1, 12.2, 1.25), W(S, BOARDS[4], 'v', P.G_MEN, -1, 16.0, 1.25)]
    L += [W(S, 'v_med_cor_whiteboard', 'u', COR[0], -1, -43.4, 1.15), W(S, 'v_med_cor_pinboard', 'u', COR[0], -1, -41.3, 1.0)]   # case boards
    L += [W(S, FCAB, 'v', P.G_EVID, 1, u) for u in (13.35, 13.95, 18.35, 18.95)] + [W(S, 'prop_copier_01', 'u', COR[0], -1, -46.6), W(S, 'prop_watercooler', 'u', COR[0], -1, -36.6)]
    # the L2 corridor: notices, extinguishers, clock, bin, plant, cameras
    L += [W(S, BOARDS[3], 'u', COR[1], -1, -22.0, 1.25), W(S, BOARDS[1], 'u', COR[0], 1, -45.0, 1.25)]
    L += [W(S, 'prop_fire_exting_2a', 'u', COR[0], 1, -20.0, 0.5), W(S, 'prop_fire_exting_2a', 'u', COR[1], -1, -52.0, 0.5), W(S, 'prop_game_clock_02', 'u', COR[0], 1, -31.9, 2.05)]
    L += [W(S, 'prop_bin_11b', 'u', COR[1], -1, -53.0), (S, 'prop_plant_int_01b', 23.0, -55.85, 0.0, 0.0), cam(S, 23.0, -56.0, 23.0, -30.0), cam(S, 23.0, -7.7, 23.0, -30.0)]
    # IT / servers: a run of server racks, the network rack, a desk, a cabinet, a camera
    L += [W(S, 'xm_base_cia_server_01', 'v', P.NI_LINK, -1, u) for u in (26.0, 26.9, 27.8, 28.7)] + [W(S, 'v_corp_servercln', 'v', P.NI_LINK, -1, u) for u in (29.6, 30.5)]
    L += [W(S, 'v_serv_tvrack', 'u', P.LOB_W, -1, -9.0)] + desk(S, 28.0, -11.4, 0.0) + [W(S, LCAB, 'v', -13.0, 1, 25.4), cam(S, 24.4, -12.6, 29.0, -9.0)]
    # training: tables in two rows facing the screen wall, chairs, projector, whiteboard, plant (the patch: art())
    for tu in (27.0, 30.0):
        for tv in (-21.3, -16.3):
            L += [(S, 'v_corp_conftable2', tu, tv, 0.0, 90.0)] + [(S, 'prop_off_chair_04', tu - 1.15, tv + dv, 0.0, 90.0) for dv in (-1.2, 0.0, 1.2)]
    L += [W(S, 'prop_tv_flat_01', 'u', P.LOB_W, -1, -19.0, 0.95), ceiling(S, 'v_res_mountedprojector', 28.5, -18.8, 90.0), W(S, 'v_med_cor_whiteboard', 'v', -13.0, -1, 28.4, 1.0)]
    L += [(S, 'prop_plant_int_02a', 24.6, -23.4, 0.0, 0.0)]
    # internal affairs: two desks, locked cabinets
    L += desk(S, 26.6, -24.75, 180.0) + desk(S, 26.6, -28.9, 0.0) + [W(S, TCAB, 'u', 28.4, -1, v) for v in (-26.2, -26.8)] + [W(S, 'v_corp_filecabdark01', 'u', 28.4, -1, -27.65)]
    # crime analysis: the monitor wall, an analyst desk, map boards
    L += [W(S, 'prop_tv_flat_01', 'u', P.LOB_W, -1, v, 1.05) for v in (-25.8, -28.25)] + desk(S, 31.0, -27.5, 90.0) + [W(S, 'v_47_map02', 'u', 28.4, 1, -27.0, 0.95)]
    # the L2 restrooms: jc3_police_wet.l2_restrooms()
    # detectives (east): two pods, boards, a cabinet
    for cu, cv in PODS2E: L += pod(S, cu, cv)
    L += [W(S, BOARDS[1], 'v', -35.5, -1, 27.0, 1.25), W(S, BOARDS[3], 'v', -35.5, -1, 29.95, 1.25), W(S, TCAB, 'v', -41.3, 1, 31.9)]
    # records (as built in pass 2h, approved): the counter desk inside the door, back-to-back shelving runs and a run on the east wall, a
    # sorting table, filing cabinets along the north-east and south walls
    L += desk(S, 25.62, -44.0, 270.0)
    for v in (-46.0, -48.5, -51.0, -53.5):
        L += [(S, 'v_corp_cabshelves01', 27.7, v, 0.0, 270.0), (S, 'v_corp_cabshelves01', 28.34, v, 0.0, 90.0)]
        if v != -46.0: L += [W(S, 'v_corp_cabshelves01', 'u', P.LOB_W, -1, v)]            # (-46: the quartermaster's door, v -46.6 .. -45.2)
    L += [(S, 'v_corp_conftable2', 30.35, -50.0, 0.0, 90.0), (S, 'v_res_filebox01', 30.35, -49.2, 0.82, 0.0), (S, 'v_res_filebox01', 30.35, -50.6, 0.82, 10.0),
          (S, 'v_med_cor_fileboxa', 30.15, -51.3, 0.82, 0.0), (S, 'v_res_paperfolders', 30.5, -48.6, 0.93, 90.0)]
    L += [W(S, TCAB, 'u', P.LOB_W, -1, v) for v in (-42.2, -42.8, -43.4)]
    L += [W(S, TCAB, 'v', P.SG, 1, u) for u in (25.0, 25.6, 26.2, 26.8)] + [W(S, LCAB, 'v', P.SG, 1, u) for u in (29.6, 31.0)]
    L += [(S, 'v_corp_boxpapr1fd', u, -56.05, 0.89, 0.0) for u in (29.3, 31.3)]
    # the east corridor, the patrol lieutenant, the sergeants
    L += [W(S, BOARDS[0], 'u', P.LOB_W, 1, -35.0, 1.25), W(S, 'prop_fire_exting_2a', 'u', P.LOB_W, 1, -42.5, 0.5)]
    L += desk(S, 38.5, -35.0, 180.0, chair=EXC) + [W(S, 'v_med_cor_whiteboard', 'v', P.LOBBY_S, -1, 38.5, 1.0)] + [W(S, TCAB, 'v', P.G_EB, 1, u) for u in (36.0, 36.6)]
    L += [(S, 'v_corp_lazychair', 37.9, -33.7, 0.0, 0.0), (S, 'v_corp_lazychair', 39.1, -33.7, 0.0, 0.0), W(S, 'v_20_office_flag01', 'v', P.LOBBY_S, -1, 36.8),
          W(S, 'v_20_office_flag01', 'v', P.LOBBY_S, -1, 40.2), (S, 'prop_plant_int_02a', 41.2, -39.3, 0.0, 0.0)]
    L += desk(S, 36.6, -43.3, 0.0) + desk(S, 39.6, -43.3, 0.0) + desk(S, 38.0, -41.0, 180.0) + [W(S, BOARDS[2], 'v', P.GAR_N, 1, 41.2, 1.25)]
    # the quartermaster store: four runs of shelving with boxes, folded uniforms and caps on top, crates along the south wall
    for v in (-47.2, -49.6, -52.0, -54.4):
        for u in (36.2, 39.6, 43.0):
            L += [(S, 'prop_shelves_01', u, v, 0.0, 0.0), (S, 'prop_cardbordbox_02a', u - 0.7, v, 1.9, 0.0)]
            L += [(S, 'prop_ld_jeans_02', u + 0.6, v, 1.9, 90.0)] if (u + v) % 2 < 1 else [(S, 'prop_ld_hat_01', u + 0.6, v, 1.9, 0.0)]
    L += [W(S, 'v_serv_plas_boxg4', 'v', P.SG, 1, 37.0), (S, 'prop_cardbordbox_04a', 34.0, -55.6, 0.0, 0.0)]
    # the interview suites (kept as approved): table, chairs, case file, the observers' chairs, cameras
    for room, u in (('pint1', 12.4), ('pint2', 20.2)):
        L += [(room, SIDE, u, -52.8, 0.0, 0.0), (room, OCH, u, -53.8, 0.0, 180.0), (room, OCH, u, -51.8, 0.0, 0.0),
              (room, 'v_20_copfile02', u - 0.15, -52.8, 0.882, 10.0), (room, 'v_res_mmug', u + 0.25, -52.6, 0.88, 0.0)]
    L += [('pobs1', OCH, 15.6, -52.8, 0.0, 270.0), ('pobs2', OCH, 17.1, -52.8, 0.0, 90.0)]
    L += [ceiling(r, 'prop_cctv_cam_06a', u, -49.4, h) for r, u, h in (('pint1', 13.8, 135.0), ('pint2', 18.8, 225.0))]
    L += services(S, P.SPACES2)
    return L
def kit2():
    """the pod screens (grey panel, 4 cm x 1.2 m), with collision."""
    out = []
    for cu, cv in PODS2 + PODS2E: out.append(('pstaff2', (cu - 1.25, cv - 0.02, P2), (cu + 1.25, cv + 0.02, P2 + 1.2), 'panel_grey', True))
    return out
