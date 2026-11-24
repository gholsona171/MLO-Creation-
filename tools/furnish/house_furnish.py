"""The house's furniture (Antonio 2026-11-23, after walking it: things faced the wrong way, sat in beds, blocked doors, rooms bare):
every piece placed by rule instead of by eye, then proved by check().
  * Models: C9_HousingProps (our own pack, survey/c9hp_catalog.json from c9hp_catalog.py: exact size, origin at the bottom centre of
    the footprint, front -Y) plus vanilla pieces only where their footprint is known (the pool table: a square of its longest side).
  * wall(model, room, side, s, ...): the piece's BACK against that wall of the room (the wall's inner face: the outer walls' lining or
    the partition's face), centred at s along it, its FRONT into the room. Heading = which way the front faces: N wall -> 0 (front
    south), S -> 180, E -> 270, W -> 90 (GTA heading: anticlockwise from north; a -Y front turned by h points (sin h, -cos h)).
  * free(model, room, u, v, h): centred at (u, v).
  * Items mounted on a wall (art, mirrors, towel racks) carry z (height of their bottom); 'on' items (table lamps) sit on another piece.
check() fails the build when a piece: leaves its room, overlaps another piece, stands in a door's swing (1 m each side of every
doorway), stands in front of a window lower than its own top (full-height glass: only plants, lamps and seats up to 0.9 m), stands on
the stair or its void, or blocks a slider's door bay (1 m in front).
Run: py -3 house_furnish.py   -> FURNISH_PASS + ../review/house_furniture.png (both floors, every footprint and its front)"""
import json, math
from pathlib import Path
import house_plan as H

T = Path(__file__).resolve().parent
CAT = json.load(open(T.parent / 'survey' / 'c9hp_catalog.json'))
VANILLA = {'prop_pooltable_02': (2.9, 2.9, 0.95, 'v_coin_op')}          # (w, d, h, ytyp): footprint = a square of its longest side
EX, LN, PT = H.EXT_T, H.LIN, H.PART
FL = {0: H.F0 + .01, 1: H.F1 + .01}
CEIL = {0: H.F1 - H.SLAB - .03, 1: H.ROOF - H.SLAB - .03}
ITEMS = []


def size(m):
    if m in CAT: c = CAT[m]; return c['w'], c['d'], c['h']
    w, d, h, _ = VANILLA[m]; return w, d, h


def ytyp(m): return ('c9hp_' + CAT[m]['cat']) if m in CAT else VANILLA[m][3]


def room_of(name):
    for fl, rooms in ((0, H.GROUND), (1, H.UPPER)):
        if name in rooms: return fl, rooms[name]
    raise KeyError(name)


def face(fl, rect, side):
    """the inner face coordinate of that wall of the room: outer walls -> inside the lining; partitions -> half a partition in."""
    u0, u1, v0, v1 = rect
    if side == 'N': return v1 - (EX + LN if v1 == H.D else PT / 2)
    if side == 'S': return v0 + (EX + LN if v0 == 0 else PT / 2)
    if side == 'E': return u1 - (EX + LN if u1 == H.W else PT / 2)
    return u0 + (EX + LN if u0 == 0 else PT / 2)


HEAD = {'N': 0.0, 'S': 180.0, 'E': 270.0, 'W': 90.0}


def footprint(w, d, u, v, h):
    """axis-aligned footprint (u0, u1, v0, v1) of a w x d piece centred at (u, v) at a heading that is a multiple of 90."""
    q = round(h / 90) % 4; assert abs(h - 90 * round(h / 90)) < 1e-6, f'heading {h}: multiples of 90 only'
    a, b = (w, d) if q % 2 == 0 else (d, w)
    return (u - a / 2, u + a / 2, v - b / 2, v + b / 2)


def _add(m, room, u, v, h, z=0.0, kind='floor', on=None, gap=0.0):
    fl, rect = room_of(room); w, d, ht = size(m)
    ITEMS.append({'model': m, 'room': room, 'floor': fl, 'u': round(u, 4), 'v': round(v, 4), 'h': h, 'z': z, 'kind': kind, 'on': on,
                  'fp': footprint(w, d, u, v, h), 'top': z + ht})


def wall(m, room, side, s, z=0.0, kind='floor', out=0.0, on=None):
    """back to the `side` wall of `room`, centred at s along it; out = extra distance off the wall (a panel behind it)."""
    fl, rect = room_of(room); w, d, ht = size(m); f = face(fl, rect, side)
    off = (0.0 if CAT.get(m, {}).get('mount') == 'wall' else d / 2) + out
    if side == 'N': u, v = s, f - off
    elif side == 'S': u, v = s, f + off
    elif side == 'E': u, v = f - off, s
    else: u, v = f + off, s
    _add(m, room, u, v, HEAD[side], z, kind, on)


def free(m, room, u, v, h, z=0.0, kind='floor', on=None): _add(m, room, u, v, h, z, kind, on)


def ceiling(m, room, u, v): fl, _ = room_of(room); _add(m, room, u, v, 0.0, CEIL[fl] - FL[fl], 'ceiling')


# ================= GROUND =================
# garage: workbench + tool chests on the west wall, wire shelving on the north wall (laundry door at u 1..2 kept clear)
wall('c9hp_ws_workbench_wood', 'garage', 'W', 4.4); wall('c9hp_ws_toolchest_red', 'garage', 'W', 6.6)
wall('c9hp_ws_shelf_wire', 'garage', 'N', 5.6); wall('c9hp_ws_pegboard_wall', 'garage', 'W', 4.4, z=1.15, kind='wall')
# laundry: washer + dryer on the west wall, wall cupboard over them
wall('c9hp_washer_white', 'laundry', 'W', 9.45); wall('c9hp_dryer_white', 'laundry', 'W', 10.08)
wall('c9hp_cab_wall90_white', 'laundry', 'W', 9.77, z=1.45, kind='wall')
# powder room: vanity + mirror, toilet, towel rack, a small plant
wall('c9hp_vanity_60_white', 'powder', 'N', 4.75); wall('c9hp_mirror_rect', 'powder', 'N', 4.75, z=1.05, kind='wall')
wall('c9hp_toilet_white', 'powder', 'N', 5.95); wall('c9hp_towel_rack_white', 'powder', 'S', 5.0, z=0.95, kind='wall')
wall('c9hp_toilet_roll_holder', 'powder', 'E', 10.75, z=0.65, kind='wall')
# office: desk under the west window with its chair, two bookshelves on the east wall, a lounge chair, a rug, art
wall('c9hp_desk_oak', 'office', 'W', 14.5); free('c9hp_chair_office_black', 'office', 1.25, 14.5, 270.0)
wall('c9hp_lamp_desk_brass', 'office', 'W', 14.0, z=0.75, kind='on', on='c9hp_desk_oak')
wall('c9hp_bookshelf_walnut', 'office', 'E', 14.9); wall('c9hp_bookshelf_walnut', 'office', 'E', 15.85)
wall('c9hp_armchair_cognac', 'office', 'E', 17.15); free('c9hp_rug_c', 'office', 4.2, 14.5, 90.0, kind='rug')
wall('c9hp_wallart_b', 'office', 'S', 4.0, z=1.35, kind='wall'); free('c9hp_plant_fiddle', 'office', 0.6, 17.35, 0.0)
# kitchen: the cupboard run on the west wall (fridge, cupboards, sink, dishwasher, 36" range with the microwave hood over it,
# cupboard), wall cupboards over the counter, the island with three counter stools, pendants; dining at the south end
RUN = [('c9hp_fridge_french_steel', None), ('c9hp_cab_base90_white', 'c9hp_cab_wall90_white'), ('c9hp_cab_sinkbase90_white', None),
       ('c9hp_dishwasher_steel', None), ('c9hp_range_36_pro_steel', 'c9hp_microwave_otr_steel'), ('c9hp_cab_drawers60_white', 'c9hp_cab_wall60_white')]
s = 12.62
for m, over in RUN:
    w = size(m)[0]; wall(m, 'kitchen', 'W', s + w / 2)
    if over: wall(over, 'kitchen', 'W', s + w / 2, z=1.50 if 'microwave' not in over else 1.55, kind='wall')
    s += w
KITCHEN_RUN_END = s
free('c9hp_cab_island180_white', 'kitchen', 10.95, 15.0, 90.0)
for v in (14.4, 15.0, 15.6): free('c9hp_stool_counter_black', 'kitchen', 11.85, v, 270.0)
ceiling('c9hp_ceiling_pendant_globe_opal', 'kitchen', 10.95, 14.4); ceiling('c9hp_ceiling_pendant_globe_opal', 'kitchen', 10.95, 15.6)
free('c9hp_table_dining_oak', 'kitchen', 10.6, 8.6, 90.0)
for v in (8.15, 9.05): free('c9hp_chair_dining_oak', 'kitchen', 9.7, v, 90.0); free('c9hp_chair_dining_oak', 'kitchen', 11.5, v, 270.0)
free('c9hp_chair_dining_oak', 'kitchen', 10.6, 7.25, 180.0); free('c9hp_chair_dining_oak', 'kitchen', 10.6, 9.95, 0.0)
ceiling('c9hp_ceiling_pendant_linear_3', 'kitchen', 10.6, 8.6)
wall('c9hp_wallart_b', 'kitchen', 'W', 7.6, z=1.3, kind='wall')
# entry: console with a mirror over it, a tall plant by the glass, a bench
wall('c9hp_table_console_oak', 'entry', 'W', 4.4); wall('c9hp_mirror_round', 'entry', 'W', 4.4, z=1.05, kind='wall')
free('c9hp_plant_fiddle', 'entry', 8.65, 0.65, 0.0); wall('c9hp_bench_oak_grey', 'entry', 'E', 2.5, out=0.08)
# games room: the pool table, two bookshelves + art on the east wall, two armchairs by the window
free('prop_pooltable_02', 'games', 16.2, 3.05, 0.0)
wall('c9hp_bookshelf_oak', 'games', 'E', 1.4); wall('c9hp_bookshelf_oak', 'games', 'E', 2.35)
wall('c9hp_wallart_a', 'games', 'E', 4.3, z=1.2, kind='wall'); wall('c9hp_lamp_floor_tripod_wood', 'games', 'E', 5.4)
# hall: a plant at the foot of the stair
free('c9hp_plant_snake', 'hall', 13.6, 10.6, 0.0)
# lounge: the sectional facing the garden glass (its back to the stair), coffee table, rug, an armchair; a second sitting group by
# the east glass (sofa, two armchairs, glass table), lamps, art, plants
free('c9hp_sectional_grey', 'lounge', 16.5, 13.6, 180.0); free('c9hp_table_coffee_oak', 'lounge', 16.5, 15.3, 0.0)
free('c9hp_rug_a', 'lounge', 16.5, 14.9, 90.0, kind='rug'); free('c9hp_armchair_grey', 'lounge', 13.75, 15.3, 90.0)
wall('c9hp_sofa3_cream', 'lounge', 'E', 15.0); free('c9hp_table_coffee_glass', 'lounge', 23.55, 15.0, 90.0)
free('c9hp_armchair_cream', 'lounge', 22.15, 14.3, 90.0); free('c9hp_armchair_cream', 'lounge', 22.15, 15.7, 90.0)
free('c9hp_rug_b', 'lounge', 23.4, 15.0, 0.0, kind='rug')
wall('c9hp_wallart_b', 'lounge', 'S', 23.0, z=1.35, kind='wall'); wall('c9hp_table_console_walnut', 'lounge', 'S', 23.0)
free('c9hp_lamp_floor_arc_black', 'lounge', 19.3, 16.6, 90.0); free('c9hp_plant_fiddle', 'lounge', 13.6, 17.35, 0.0)
free('c9hp_plant_fiddle', 'lounge', 25.45, 12.4, 0.0)
# guest bedroom: queen bed on the north wall with nightstands + lamps + art, dresser under the east window, wardrobe, armchair
wall('c9hp_bed_queen_uphgrey', 'guest', 'N', 23.0)
for u in (21.75, 24.25):
    wall('c9hp_nightstand_white', 'guest', 'N', u); wall('c9hp_lamp_table_white', 'guest', 'N', u, z=0.55, kind='on', on='c9hp_nightstand_white')
wall('c9hp_wallart_c', 'guest', 'N', 23.0, z=1.35, kind='wall', out=0.0)
wall('c9hp_dresser_white', 'guest', 'E', 7.4); wall('c9hp_wardrobe_white', 'guest', 'S', 21.0)
free('c9hp_armchair_navy', 'guest', 25.2, 9.6, 270.0); free('c9hp_rug_a', 'guest', 23.0, 8.6, 90.0, kind='rug')
# guest bath: walk-in shower on the east wall, toilet, a 120 vanity with its mirror, towel rack, mat
wall('c9hp_shower_walkin_120', 'guestbath', 'E', 0.9); wall('c9hp_toilet_white', 'guestbath', 'E', 3.3)
wall('c9hp_vanity_120_white', 'guestbath', 'N', 21.25); wall('c9hp_mirror_rect', 'guestbath', 'N', 21.25, z=1.1, kind='wall')
wall('c9hp_towel_rack_white', 'guestbath', 'W', 2.5, z=0.95, kind='wall'); free('c9hp_bath_mat', 'guestbath', 24.3, 0.9, 90.0, kind='rug')
wall('c9hp_toilet_roll_holder', 'guestbath', 'E', 2.75, z=0.65, kind='wall')

# ================= UPPER =================
# bedroom 3: queen bed on the north wall, nightstands + lamps, art; wardrobe + dresser on the east wall; a black lounge chair
wall('c9hp_bed_queen_oak', 'bed3', 'N', 3.5)
for u in (2.2, 4.8):
    wall('c9hp_nightstand_oak', 'bed3', 'N', u); wall('c9hp_lamp_table_black', 'bed3', 'N', u, z=0.55, kind='on', on='c9hp_nightstand_oak')
wall('c9hp_wallart_a', 'bed3', 'N', 3.5, z=1.25, kind='wall')
wall('c9hp_wardrobe_oak', 'bed3', 'E', 3.6); wall('c9hp_dresser_oak', 'bed3', 'E', 5.3)
wall('c9hp_armchair_black', 'bed3', 'W', 7.6); free('c9hp_rug_c', 'bed3', 3.5, 5.6, 90.0, kind='rug')
# bedroom 2: king bed on the south wall, nightstands + lamps, art; two wardrobes on the east wall; lounge chair by the balcony glass
wall('c9hp_bed_king_uphgrey', 'bed2', 'S', 3.5)
for u in (2.0, 5.0):
    wall('c9hp_nightstand_walnut', 'bed2', 'S', u); wall('c9hp_lamp_table_sage', 'bed2', 'S', u, z=0.55, kind='on', on='c9hp_nightstand_walnut')
wall('c9hp_wallart_b', 'bed2', 'S', 3.5, z=1.35, kind='wall')
wall('c9hp_wardrobe_walnut', 'bed2', 'E', 13.3); wall('c9hp_wardrobe_walnut', 'bed2', 'E', 14.25)
free('c9hp_armchair_black', 'bed2', 1.2, 16.2, 180.0); free('c9hp_table_side_oak', 'bed2', 2.4, 16.5, 0.0)
free('c9hp_rug_a', 'bed2', 3.5, 13.4, 90.0, kind='rug')
# bath: shower-tub on the west wall, toilet, vanity + mirror on the east wall, towel rack
wall('c9hp_shower_tub_combo', 'bath', 'W', 1.06); wall('c9hp_toilet_white', 'bath', 'W', 3.2)
wall('c9hp_vanity_120_oak', 'bath', 'E', 2.4); wall('c9hp_mirror_rect', 'bath', 'E', 2.4, z=1.1, kind='wall')
wall('c9hp_towel_rack_grey', 'bath', 'S', 11.0, z=0.95, kind='wall'); free('c9hp_bath_mat', 'bath', 9.2, 2.3, 90.0, kind='rug')
# study / bedroom 4: desk under the window with its chair, bookshelves, a loveseat, art
wall('c9hp_desk_white', 'study', 'S', 17.0); free('c9hp_chair_office_grey', 'study', 17.0, 1.35, 0.0)
wall('c9hp_bookshelf_oak', 'study', 'W', 2.0); wall('c9hp_bookshelf_oak', 'study', 'W', 2.95)
wall('c9hp_loveseat_grey', 'study', 'E', 3.0); wall('c9hp_wallart_c', 'study', 'E', 3.0, z=1.4, kind='wall')
# landing: console + art + plant
wall('c9hp_table_console_oak', 'landing', 'S', 9.4); wall('c9hp_wallart_a', 'landing', 'S', 9.4, z=1.2, kind='wall')
free('c9hp_plant_fiddle', 'landing', 19.55, 6.5, 0.0)
# upper lounge: sofa on the west wall facing the TV console on the east wall, coffee table, rug, floor lamp
wall('c9hp_sofa3_navy', 'upperlounge', 'W', 15.0); wall('c9hp_tv_stand_oak', 'upperlounge', 'E', 15.0)
free('c9hp_table_coffee_walnut', 'upperlounge', 10.75, 15.0, 90.0); free('c9hp_rug_b', 'upperlounge', 10.9, 15.0, 90.0, kind='rug')
free('c9hp_lamp_floor_drum_white', 'upperlounge', 8.35, 17.35, 0.0)
# master: king bed against the oak headboard wall (u 14), nightstands + lamps, art over the bed; the sitting area in the SE corner
# (loveseat, glass table, armchair), the wine cabinet (built, house.py) on the south wall, floor lamp, plant
PANEL = 0.03
wall('c9hp_bed_king_oak', 'master', 'W', 15.0, out=PANEL)
for v in (13.45, 16.55):
    wall('c9hp_nightstand_walnut', 'master', 'W', v, out=PANEL); wall('c9hp_lamp_table_white', 'master', 'W', v, z=0.55, kind='on', on='c9hp_nightstand_walnut', out=PANEL)
wall('c9hp_wallart_b', 'master', 'W', 15.0, z=1.35, kind='wall', out=PANEL)
wall('c9hp_loveseat_cognac', 'master', 'S', 24.3); free('c9hp_table_coffee_glass', 'master', 24.3, 13.95, 0.0)
free('c9hp_armchair_cognac', 'master', 24.3, 15.45, 0.0); free('c9hp_rug_c', 'master', 18.2, 15.0, 0.0, kind='rug')
free('c9hp_lamp_floor_torchiere', 'master', 14.3, 12.5, 0.0); free('c9hp_plant_snake', 'master', 14.3, 17.5, 0.0)
# walk-in closet: four wardrobes facing each other across the aisle, a bench, a floor mirror
for u in (21.0, 21.97, 24.03, 25.0):
    wall('c9hp_wardrobe_white', 'closet', 'N', u); wall('c9hp_wardrobe_white', 'closet', 'S', u)
free('c9hp_bench_white_navy', 'closet', 23.0, 9.0, 90.0); wall('c9hp_mirror_floor_oak', 'closet', 'W', 9.0)
# master bath: walk-in shower, clawfoot tub, toilet, a 120 vanity with its mirror, towel rack, mat, plant
wall('c9hp_shower_walkin_120', 'masterbath', 'E', 0.9); wall('c9hp_bathtub_clawfoot_black', 'masterbath', 'S', 22.0)
wall('c9hp_toilet_white', 'masterbath', 'E', 3.6); wall('c9hp_toilet_roll_holder', 'masterbath', 'E', 3.05, z=0.65, kind='wall')
wall('c9hp_vanity_120_charcoal', 'masterbath', 'W', 3.0); wall('c9hp_mirror_rect', 'masterbath', 'W', 3.0, z=1.1, kind='wall')
wall('c9hp_towel_rack_grey', 'masterbath', 'N', 21.0, z=0.95, kind='wall'); free('c9hp_bath_mat', 'masterbath', 22.0, 1.55, 0.0, kind='rug')
free('c9hp_plant_snake', 'masterbath', 20.35, 5.5, 0.0)

# ================= second pass (Antonio: "too much empty space inside of each and every single room") =================
free('c9hp_lamp_floor_drum_black', 'office', 7.5, 12.6, 0.0)
free('c9hp_bench_white_navy', 'guest', 23.0, 9.45, 0.0); free('c9hp_plant_fiddle', 'guest', 20.4, 11.6, 0.0)
free('c9hp_lamp_floor_torchiere', 'guest', 25.5, 5.5, 0.0)
wall('c9hp_bathtub_alcove', 'guestbath', 'S', 21.6); free('c9hp_plant_snake', 'guestbath', 20.3, 3.7, 0.0)
free('c9hp_table_side_oak', 'lounge', 18.2, 13.2, 0.0); free('c9hp_plant_snake', 'lounge', 19.6, 12.45, 0.0)
wall('c9hp_chair_accent_teal', 'games', 'S', 18.4); wall('c9hp_chair_accent_teal', 'games', 'S', 19.2)
free('c9hp_bench_oak_grey', 'bed3', 3.5, 6.5, 0.0); wall('c9hp_desk_white', 'bed3', 'S', 3.8)
free('c9hp_chair_office_black', 'bed3', 3.8, 1.35, 0.0); free('c9hp_plant_fiddle', 'bed3', 0.6, 8.55, 0.0)
wall('c9hp_wallart_c', 'bed3', 'E', 5.3, z=1.25, kind='wall')
free('c9hp_bench_oak_grey', 'bed2', 3.5, 11.55, 180.0); wall('c9hp_tallchest_oak', 'bed2', 'W', 17.2)
free('c9hp_plant_fiddle', 'bed2', 7.5, 17.3, 0.0); free('c9hp_lamp_floor_tripod_wood', 'bed2', 0.6, 9.6, 0.0)
free('c9hp_bench_oak_grey', 'master', 16.55, 15.0, 90.0); wall('c9hp_dresser_walnut', 'master', 'S', 17.0)
wall('c9hp_wallart_c', 'master', 'S', 17.0, z=1.3, kind='wall'); free('c9hp_plant_fiddle', 'master', 19.6, 17.3, 0.0)
free('c9hp_rug_b', 'study', 17.0, 3.0, 0.0, kind='rug'); free('c9hp_lamp_floor_drum_black', 'study', 13.4, 4.6, 0.0)
free('c9hp_plant_snake', 'study', 19.6, 5.5, 0.0); wall('c9hp_table_side_oak', 'study', 'E', 1.6)
free('c9hp_plant_fiddle', 'upperlounge', 13.6, 12.5, 0.0); wall('c9hp_table_side_oak', 'upperlounge', 'W', 16.4)
wall('c9hp_wallart_c', 'upperlounge', 'S', 13.25, z=1.3, kind='wall')
free('c9hp_plant_snake', 'bath', 8.3, 5.6, 0.0); free('c9hp_stool_vanity_oak', 'masterbath', 20.9, 3.0, 0.0)

# ---- built pieces (house.py) that furniture must keep clear of: (floor, u0, u1, v0, v1, top above the floor)
WINE = (20.2, 22.2)                                     # the wine cabinet on the master's south wall (v 12)
BUILT = [(1, WINE[0], WINE[1], 12 + PT / 2, 12 + PT / 2 + .45, 2.1)]


def doors():
    """(floor, rect) of every doorway's swing zone: the opening's width, 1 m deep on both sides."""
    out = []
    for ax, at, d0, d1, fl, leaf in H.DOORS_IN:
        out.append((fl, (at - 1.0, at + 1.0, d0, d1) if ax == 'u' else (d0, d1, at - 1.0, at + 1.0)))
    for f, a, b, z0, z1, kind in H.OPEN_G + H.OPEN_U:
        fl = 0 if (f, a, b, z0, z1, kind) in H.OPEN_G else 1
        if kind == 'door' and f == 'S': out.append((fl, (a, b, 0, 1.25)))
        if kind == 'slider' and f == 'N': out.append((fl, (b - 1.6, b, H.D - 1.25, H.D)))
    return out


def windows():
    """(floor, rect 0.7 m deep in front of the opening, sill height above the floor) of every glass opening."""
    out = []
    for lst, fl in ((H.OPEN_G, 0), (H.OPEN_U, 1)):
        for f, a, b, z0, z1, kind in lst:
            if kind not in ('glass', 'slider'): continue
            r = {'S': (a, b, 0, .95), 'N': (a, b, H.D - .95, H.D), 'E': (H.W - .95, H.W, a, b), 'W': (0, .95, a, b)}[f]
            out.append((fl, r, z0))
    return out


def inter(a, b, eps=1e-3): return a[0] < b[1] - eps and b[0] < a[1] - eps and a[2] < b[3] - eps and b[2] < a[3] - eps


LOW_OK = ('plant', 'lamp_floor', 'armchair', 'sofa', 'loveseat', 'sectional', 'table_coffee', 'table_side', 'rug', 'bench', 'desk', 'chair', 'stool')


def check():
    errs = []
    for it in ITEMS:
        fl, rect = room_of(it['room'])
        lim = (face(fl, rect, 'W') - .005, face(fl, rect, 'E') + .005, face(fl, rect, 'S') - .005, face(fl, rect, 'N') + .005)
        u0, u1, v0, v1 = it['fp']
        if it['kind'] != 'ceiling' and not (lim[0] <= u0 and u1 <= lim[1] and lim[2] <= v0 and v1 <= lim[3]):
            errs.append(f"{it['model']} in {it['room']} leaves the room: {tuple(round(x, 2) for x in it['fp'])} vs {tuple(round(x, 2) for x in lim)}")
    solid = [it for it in ITEMS if it['kind'] in ('floor',)]
    for i, a in enumerate(solid):
        for b in solid[i + 1:]:
            if a['floor'] == b['floor'] and inter(a['fp'], b['fp']): errs.append(f"{a['model']} ({a['room']}) overlaps {b['model']} ({b['room']})")
        for fl, u0, u1, v0, v1, top in BUILT:
            if a['floor'] == fl and inter(a['fp'], (u0, u1, v0, v1)): errs.append(f"{a['model']} overlaps a built piece")
        for fl, r in doors():
            if a['floor'] == fl and inter(a['fp'], r): errs.append(f"{a['model']} ({a['room']}) blocks a doorway {tuple(round(x, 2) for x in r)}")
        for fl, r, sill in windows():
            if a['floor'] == fl and inter(a['fp'], r) and a['top'] > sill + .02:
                low = any(k in a['model'] for k in LOW_OK) and (a['top'] <= .95 or 'plant' in a['model'] or 'lamp_floor' in a['model'])
                if not (sill < .1 and low): errs.append(f"{a['model']} ({a['room']}) stands in front of a window (sill {sill}, top {a['top']:.2f})")
        if a['floor'] in (0, 1):
            u0, u1, v0, v1 = H.STAIR_HOLE
            if inter(a['fp'], (u0 - .3, u1 + .3, v0 - .1, v1 + .1)): errs.append(f"{a['model']} ({a['room']}) is on the stair / its void")
    walls = [it for it in ITEMS if it['kind'] == 'wall']
    for i, a in enumerate(walls):                                              # wall pieces: not into each other (same wall, same height)
        for b in walls[i + 1:]:
            if a['floor'] == b['floor'] and inter(a['fp'], b['fp']) and a['z'] < b['top'] and b['z'] < a['top']:
                errs.append(f"wall pieces {a['model']} and {b['model']} overlap")
        for s in solid:                                                        # and above the furniture under them
            if a['floor'] == s['floor'] and inter(a['fp'], s['fp']) and a['z'] < s['top'] - .01:
                errs.append(f"{a['model']} ({a['room']}) hangs into {s['model']} (bottom {a['z']}, its top {s['top']:.2f})")
    for it in ITEMS:
        if it['kind'] == 'on':
            base = [s for s in solid if s['model'] == it['on'] and s['floor'] == it['floor'] and inter(it['fp'], s['fp'])]
            if not base: errs.append(f"{it['model']} ({it['room']}) is not on a {it['on']}")
            elif abs(it['z'] - base[0]['top']) > .03: errs.append(f"{it['model']} floats / sinks: z {it['z']} on a top at {base[0]['top']:.3f}")
    return errs


def props():
    """the MLO entities: (model, local position, heading, ytyp) for house.py."""
    return [{'room': 1, 'model': it['model'], 'pos': (it['u'], it['v'], FL[it['floor']] + it['z']), 'heading': it['h']} for it in ITEMS]


def colliders():
    """backup collision boxes in the MLO's own ybn for every standing piece (the pack's embedded collision is unproven in game):
    (lo, hi) local. Seats and beds to their seat / mattress height, showers: their glass panel only, rugs / wall pieces: none."""
    out = []
    for it in ITEMS:
        if it['kind'] != 'floor' or 'plant' in it['model'] or 'lamp' in it['model']: continue
        u0, u1, v0, v1 = it['fp']; z = FL[it['floor']]
        m = it['model']
        if 'shower_walkin' in m:                                               # the fixed panel: local x -0.585..0.115 at y -0.44 (front)
            h = math.radians(it['h']); pts = [(x, -.44 + dy) for x in (-.585, .115) for dy in (-.01, .01)]
            P = [(it['u'] + x * math.cos(h) - y * math.sin(h), it['v'] + x * math.sin(h) + y * math.cos(h)) for x, y in pts]
            out.append(((min(p[0] for p in P), min(p[1] for p in P), z + .07), (max(p[0] for p in P), max(p[1] for p in P), z + 1.94))); continue
        top = it['top']
        if any(k in m for k in ('sofa', 'loveseat', 'sectional', 'armchair', 'bed_', 'bench', 'chair', 'stool')): top = min(top, .45)
        out.append(((u0, v0, z), (u1, v1, z + top)))
    return out


if __name__ == '__main__':
    errs = check()
    from PIL import Image, ImageDraw, ImageFont
    S, PAD = 46, 40
    sheet = Image.new('RGB', (int(2 * H.W * S + 3 * PAD), int(H.D * S + 2 * PAD + 40)), 'white'); d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(r'C:\Windows\Fonts\segoeui.ttf', 11)
    for fl, rooms in ((0, H.GROUND), (1, H.UPPER)):
        ox = PAD + fl * (H.W * S + PAD)
        P = lambda u, v: (ox + u * S, PAD + 30 + (H.D - v) * S)
        d.text((ox, 8), ('Ground' if fl == 0 else 'Upper') + ' floor (furniture check)', font=ImageFont.truetype(r'C:\Windows\Fonts\segoeuib.ttf', 20), fill='black')
        for n, (u0, u1, v0, v1) in rooms.items():
            d.rectangle([P(u0, v1), P(u1, v0)], outline=(60, 60, 60), width=3); d.text(P(u0 + .15, v1 - .1), n, font=f, fill=(120, 120, 120))
        for fl2, r in doors():
            if fl2 == fl: d.rectangle([P(r[0], r[3]), P(r[1], r[2])], outline=(60, 170, 80), width=1)
        u0, u1, v0, v1 = H.STAIR_HOLE; d.rectangle([P(u0, v1), P(u1, v0)], fill=(225, 215, 190))
        for it in ITEMS:
            if it['floor'] != fl or it['kind'] == 'ceiling': continue
            u0, u1, v0, v1 = it['fp']
            col = {'rug': (235, 225, 245), 'wall': (250, 210, 120), 'on': (255, 240, 160)}.get(it['kind'], (205, 220, 240))
            d.rectangle([P(u0, v1), P(u1, v0)], fill=col if it['kind'] == 'rug' else None, outline=col if it['kind'] == 'rug' else (40, 70, 150), width=2)
            h = math.radians(it['h']); fx, fy = math.sin(h), -math.cos(h)                  # the front
            if it['kind'] == 'floor':
                a = P(it['u'], it['v']); b = P(it['u'] + fx * .35, it['v'] + fy * .35); d.line([a, b], fill=(200, 40, 40), width=3)
            d.text(P(u0 + .03, (v0 + v1) / 2), it['model'][5:][:14], font=f, fill=(20, 20, 20))
    out = T.parent / 'review' / 'house_furniture.png'; sheet.save(out)
    for e in errs: print('FURNISH_ERR', e)
    print('FURNISH_PASS' if not errs else 'FURNISH_FAIL', len(ITEMS), 'pieces,', len(errs), 'problems ->', out)
