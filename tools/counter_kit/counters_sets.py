"""
c9_dj counter kit: the SETS (modular styles cut from one Rockstar counter each) and the full-size COPIES. Numbers measured from the
Rockstar drawables (sections at several points of each run; prop/build/counters.py --report prints them again):

  rot     degrees the source turns (incl. the straightening: Rockstar's bkr bar is 0.28 deg off square) so its run goes +X, patron -Y
  x0      where the clean stretch of the run starts after turning (the module frame's x = 0)
  probe   an x (module frame) where the profile is plain (back edge + floor measured there)
  D       depth of the top (front edge to back edge); every module of the set is this deep
  straights  { length: x where that slice starts }   corner: x of the D-long slice the corners are mitred from
  end     ('band', a, e, w): a left end made from the run (Rockstar's is open: it stood against a wall), e long, closed by the run's own
          front band w deep turned to face out | ('native', a, b): Rockstar's own closed left end (x = a) cut at b; end_r the right one
          | ('compose', e, [(x0, x1, at), ...]): stretches of the run put together (the island's waterfall end)
          | ('pedestal', frame, a, b, block x0..x1): Rockstar's closed block end from another part of the source, in its own frame
  H_body  (pedestal ends) the height where the top slab starts: only the top is checked across a pedestal joint
  extras  [(kinds, lo, hi, f(L, D) -> (dx, dy))]: that box of the run copied into those modules, moved (a steel table's legs)
  group   the shop category (default 'Bar counters')
  short   the set's name in the shop rows (label = '<short>: <piece>', at most 40 characters)
  boxes   collision, (y0, y1, z0, z1) in the module frame (top slab, body, skirt ...): cut / turned / mitred with the drawable
  mat     collision material index (Rockstar's own where its bounds had one)
  joint_tol  the joint check's limit (default 1.5 mm; the edgy / glam trims are faceted so that two cuts differ by up to 3.7 mm
          where the trim meets the body's top, after the weld: not a visible gap)
  palette {texture: row}: a *_tnt palette's row copied into row 0 (script-spawned objects have tint 0)
  price   per metre of counter (a corner counts as D, an end its length), rounded to 25
"""

SETS = {
    # Clubhouse 1 bar (bkr_bar_bar01): dark wood top, grey wood front panel 0.31 m under the top's front edge, a low shelf box at the
    # back. Its ends are Rockstar's own pedestal (the end of the bar's short leg: a full-depth block under the top); the run butts
    # into the pedestal's side panel and only the top continues across the joint. (A front-band end showed the back box's mitre cut
    # as an open slanted face in game, rig 2026-10-25.)
    'bkrw': dict(short='Clubhouse grey bar', joint_tol=0.0025, src='bkr_bar_bar01', label='Clubhouse bar (grey wood)', rot=-90.278, x0=-1.20, probe=1.0, D=1.0186,
                 straights={1.0: 0.30, 2.0: 0.50}, corner=1.55, H_body=0.968,
                 end=('pedestal', dict(rot=0.0, x0=-1.022, probe=0.15), 0.0, 0.32, (0.0, 0.295)),
                 boxes=[(-1.0186, 0.0, 0.970, 1.026), (-0.705, -0.097, 0.0, 0.970)], mat=72, per_m=1400,
                 txd_from=['bkr_biker_dlc_int_01txd']),
    # Clubhouse 2 bar (bkr_int02_recareabar): dark marble top, cream panelled front, one wall under the top
    'bkrc': dict(short='Clubhouse cream bar', src='bkr_int02_recareabar', label='Clubhouse bar (cream)', rot=179.937, x0=-0.50, probe=1.0, D=1.0167,
                 straights={1.0: 0.55, 2.0: 0.05}, corner=0.60, end=('band', 0.20, 0.50, 0.40),
                 boxes=[(-1.0167, 0.0, 0.978, 1.034), (-0.700, -0.636, 0.0, 0.978)], mat=72, per_m=1300,
                 txd_from=['bkr_biker_dlc_int_02_txd']),
    # Nightclub bars (ba_*_lower_bar, After Hours): an island bar, top 10 cm thick, flared skirt, brackets every 1.31 m
    'trad': dict(short='Nightclub trad bar', src='ba_trad_lower_bar', label='Nightclub bar (traditional)', rot=0.0, x0=-2.748, probe=2.748, D=1.0264,
                 straights={1.0: 0.874, 2.0: 0.374}, corner=1.60, end=('native', 0.0, 0.75), end_r=('native', 4.746, 5.496),
                 boxes=[(-1.0264, 0.0, 0.950, 1.046), (-0.700, -0.284, 0.0, 0.711), (-0.823, -0.162, 0.711, 0.950)], mat=0, per_m=1600,
                 txd_from=['ba_int01_shell_txd']),
    'edgy': dict(short='Nightclub edgy bar', joint_tol=0.004, src='ba_edgy_lower_bar', label='Nightclub bar (edgy)', rot=0.0, x0=-2.748, probe=2.748, D=1.0264,
                 straights={1.0: 0.874, 2.0: 0.374}, corner=1.60, end=('native', 0.0, 0.75), end_r=('native', 4.746, 5.496),
                 boxes=[(-1.0264, 0.0, 0.949, 1.045), (-0.700, -0.284, 0.0, 0.710), (-0.823, -0.162, 0.710, 0.949)], mat=0, per_m=1600,
                 txd_from=['ba_int01_shell_txd']),
    'glam': dict(short='Nightclub glam bar', joint_tol=0.004, src='ba_glam_lower_bar', label='Nightclub bar (glam)', rot=0.0, x0=-2.748, probe=2.748, D=1.0264,
                 straights={1.0: 0.874, 2.0: 0.374}, corner=1.60, end=('native', 0.0, 0.75), end_r=('native', 4.746, 5.496),
                 boxes=[(-1.0264, 0.0, 0.949, 1.045), (-0.700, -0.284, 0.0, 0.710), (-0.823, -0.162, 0.710, 0.949)], mat=0, per_m=1700,
                 txd_from=['ba_int01_shell_txd']),
    # ── restaurant / kitchen ──────────────────────────────────────────────────────────────────────────────────────────────────
    # Fast-food cupboard counter (prop_ff_counter_01): steel top with a back upstand, cupboard doors. Cut only where the doors are
    # plain (run x 0.12-0.62 and 1.10-1.60; the handles and the door seam sit between), so every joint face is the same
    'ffsv': dict(short='Steel cupboard counter', src='prop_ff_counter_01', label='Steel cupboard counter', group='Restaurant counters', rot=0.0, x0=-0.859, probe=0.45,
                 D=0.802, straights={1.0: 0.12, 1.48: 0.12}, corner=0.40, end=('native', 0.0, 0.30), end_r=('native', 1.42, 1.718),
                 boxes=[(-0.802, 0.0, 0.857, 0.912), (-0.034, 0.0, 0.912, 0.987), (-0.792, -0.013, 0.0, 0.857)], mat=0, per_m=1300,
                 txd_from=[]),
    # Stainless prep table (prop_ff_counter_02): steel top with a front lip and back upstand, two shelves, square legs. Each straight
    # carries a pair of legs at its right end; the ends are Rockstar's own table ends (legs + closed shelf ends); corners get a leg at
    # their outer corner
    'ffst': dict(short='Steel prep table', src='prop_ff_counter_02', label='Stainless prep table', group='Kitchen counters', rot=0.0, x0=-1.244, probe=1.2,
                 D=0.802, straights={1.0: 0.70, 2.0: 0.20}, corner=0.70, end=('native', 0.0, 0.20), end_r=('native', 2.283, 2.483),
                 extras=[(('straight',), (2.394, -0.778, 0.0), (2.450, -0.722, 0.887), lambda L, D: (L - 0.089 - 2.394, 0.0)),
                         (('straight',), (2.394, -0.074, 0.0), (2.450, -0.019, 0.887), lambda L, D: (L - 0.089 - 2.394, 0.0)),
                         (('oc',), (2.394, -0.778, 0.0), (2.450, -0.722, 0.887), lambda L, D: (D - 0.089 - 2.394, 0.0)),   # outer corner
                         (('ic',), (2.394, -0.074, 0.0), (2.450, -0.019, 0.887), lambda L, D: (D - 0.089 - 2.394, 0.0))],  # outer (back)
                 boxes=[(-0.802, 0.0, 0.856, 0.912), (-0.034, 0.0, 0.912, 0.986), (-0.757, -0.038, 0.141, 0.164),
                        (-0.757, -0.038, 0.471, 0.493)], mat=0, per_m=1200, txd_from=[]),
    # Granite kitchen island (sf_int1_island_unit, the Agency): black granite top on a drawer cabinet (drawers on the staff side);
    # the left end is Rockstar's waterfall panel, the right end the cabinet's own end
    'gran': dict(short='Granite counter', src='sf_int1_island_unit', label='Granite kitchen counter', group='Kitchen counters', rot=-90.0, x0=-1.9, probe=2.8,
                 D=1.0, straights={1.0: 2.30, 1.5: 2.00}, corner=2.20, end=('compose', 0.35, [(0.0, 0.05, 0.0), (2.20, 2.50, 0.05)]),
                 end_r=('native', 3.50, 3.80), boxes=[(-1.0, 0.0, 0.900, 0.946), (-0.970, 0.0, 0.0, 0.900)], mat=0, per_m=1500,
                 txd_from=['sf_int1_sec_txd']),
}

# shop categories, in the order the shop lists them (each set / copy / vanilla row names one in `group`; sets default to the first)
GROUPS = ['Bar counters', 'Restaurant counters', 'Kitchen counters', 'Display counters', 'Checkout and reception']

# full-size copies of interior-only counters (Rockstar's archetypes live in an interior's ytyp: a script cannot spawn them). The copy
# is the whole Rockstar drawable, moved so the floor is z = 0; collision = Rockstar's own where the drawable had it, else
# counters.auto_boxes. `ends` = the set its open end takes modules from ('max' = the far end of that set's run: a right face)
COPIES = {
    'bkrw_full': dict(src='bkr_bar_bar01', label='Clubhouse L-bar (grey wood)', group='Bar counters', price=5200, ends=('bkrw', ['max']),
                      desc='The whole Clubhouse bar as Rockstar built it: an L, 4.3 x 2.4 m. Its long side ends open: Clubhouse grey bar pieces snap on there.'),
    'bkrc_full': dict(src='bkr_int02_recareabar', label='Clubhouse L-bar (cream)', group='Bar counters', price=4400, ends=('bkrc', ['max']),
                      desc='The cream Clubhouse bar with its flip-up end, 3.0 x 2.3 m. Its long side ends open: Clubhouse cream bar pieces snap on there.'),
    'bkrb_full': dict(src='bkr_bar_bar002', label='Clubhouse L-bar (curved, brick)', group='Bar counters', price=5200,
                      desc='The second Clubhouse bar: a curved dark top on grey wood and brick, 4.3 x 2.4 m.'),
    'bkrl_full': dict(src='bkr_int_02_bar_wood', label='Clubhouse L-bar (leather and wood)', group='Bar counters', price=5000,
                      palette={'int_02_bar_wood_pal': 2},      # tint row 2 = tan leather (row 0 is Rockstar's cyan placeholder)
                      desc='Wood bar with a padded leather front and a brass foot rail, an L of 3.1 x 2.4 m.'),
    'trad_full': dict(src='ba_trad_lower_bar', label='Nightclub bar (traditional), 5.5 m', group='Bar counters', price=8000,
                      desc='The whole After Hours bar: 5.5 m, served from both sides, grey stone top on reclaimed wood.'),
    'edgy_full': dict(src='ba_edgy_lower_bar', label='Nightclub bar (edgy), 5.5 m', group='Bar counters', price=8000,
                      desc='The whole After Hours bar in the edgy finish: black quilted front, granite top, served from both sides.'),
    'glam_full': dict(src='ba_glam_lower_bar', label='Nightclub bar (glam), 5.5 m', group='Bar counters', price=8500,
                      desc='The whole After Hours bar in the glam finish: purple sparkle front, gold top, served from both sides.'),
    'gran_full': dict(src='sf_int1_island_unit', label='Granite kitchen island, 3.8 m', group='Kitchen counters', price=5500,
                      desc='The Agency kitchen island: black granite on a drawer cabinet, a waterfall end, room to sit at the open half.'),
    'till_full': dict(src='v_53_shop_till', label='Store checkout counter', group='Checkout and reception', price=3800,
                      desc='The 24/7 checkout: the till counter with the cigarette shelves, 3.6 x 2.2 m.'),
    'shop_full': dict(src='vw_vwint01_shop_counter', label='Gift shop counter (casino)', group='Checkout and reception', price=4200,
                      desc='The Diamond casino gift shop counter: black stone top on dark panels, 3.2 x 3.2 m.'),
    'recep_full': dict(src='ch_chint01_reception_desk', label='Hotel reception desk (casino)', group='Checkout and reception', price=6000,
                       desc='The Diamond casino hotel desk, 4 m: two built-in screens and keyboards on the staff side.'),
    'lobby_full': dict(src='hei_heist_lobby_desk', label='Lobby front desk', group='Checkout and reception', price=5500,
                       desc='A long L-shaped front desk with a wood top and a white front, 5.9 x 2.6 m (the police station lobby).'),
    'office_full': dict(src='ex_receptiondesk01x', label='Office reception desk', group='Checkout and reception', price=3800,
                        desc='The executive office reception desk: a white panelled front with a raised ledge, 3.6 m.'),
}

# spawnable Rockstar counters added to the shop (no copy needed: the game's own prop with its own collision). The 1.9.0 'Counters'
# rows (fast-food counters, steel tables, coolers, display cases) stay as they were, only moved into these categories.
VANILLA = [
    dict(id='ctr_jewel_l', label='Jewellery display counter (L)', model='p_new_j_counter_01', price=4800, group='Display counters',
         desc='The Vangelico L-shaped glass display counter, 3.7 x 2.5 m.'),
    dict(id='ctr_glass_case_tall', label='Glass display case (narrow)', model='prop_venice_counter_02', price=1600, group='Display counters',
         desc='A narrow glass-fronted display case at counter height.'),
    dict(id='ctr_glass_case_square', label='Glass display case (square)', model='prop_venice_counter_03', price=1600, group='Display counters',
         desc='A square glass display case, 0.9 x 0.9 m, to show things off from every side.'),
    dict(id='ctr_glass_case_long', label='Glass display case (long)', model='prop_venice_counter_04', price=2400, group='Display counters',
         desc='A long glass display counter, 1.9 m, for a shop front.'),
    dict(id='ctr_steel_table_one_shelf', label='Stainless prep table (one shelf)', model='prop_ff_counter_03', price=2400, group='Kitchen counters',
         desc='Long stainless work top on legs with one low shelf.'),
]

# the 1.9.0 'Counters' rows, by id -> their category now
RECATEGORISE = {
    'ff_service_counter': 'Restaurant counters', 'drawer_back_counter': 'Restaurant counters',
    'steel_prep_table': 'Kitchen counters', 'steel_sink_table': 'Kitchen counters', 'steel_work_table': 'Kitchen counters',
    'folding_work_table': 'Kitchen counters', 'wood_workbench': 'Kitchen counters', 'steel_service_cart': 'Kitchen counters',
    'bar_wash_sink': 'Bar counters', 'backbar_cooler': 'Bar counters', 'backbar_cooler_long': 'Bar counters',
    'display_counter': 'Display counters', 'display_counter_low': 'Display counters', 'glass_case_counter': 'Display counters',
}
