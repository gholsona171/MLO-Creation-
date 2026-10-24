# 03 · Props and furnishing

## The rule
Furnish with **real GTA props**, dense and specific, the way Rockstar dresses its own interiors (Diamond penthouse, Agency office,
executive apartments, casino): furniture plus cash, bottles, bags, magazines, remotes, food, art. Kit boxes only where no prop exists
(pools, showers, counters, signs). A room of boxes "feels AI generated" — that was the verdict on the first pass.

Before dressing a room, look at how Rockstar dressed the matching vanilla room: export its ytyp and list the props (Tower City
`survey/replica/*.ytyp.xml`), or visit it in game.

## Finding props
- `tools/prop_catalogue.ps1` → `prop_catalogue.json`: ~8 300 furniture / clutter / cash archetypes with exact bounds and their ytyp.
- `tools/find_arch_ytyp.ps1 -Names @('a','b')` → `arch_ytyp.json`: the ytyp + bounds of the props you chose (needed for the MLO's
  dependency list). Pass names as a PowerShell array; a comma string is read as one name.
- Good families: `apa_mp_h_*` / `ex_mp_h_*` (apartment and executive sets), `v_res_*` (houses), `v_corp_*` (offices), `v_club_*`,
  `ch_prop_ch_*` (casino), `sf_prop_sf_*` (Agency), `bkr_prop_*` / `ex_cash_pile_*` (cash), `vw_prop_*` (Diamond).

## Placement: pivots and facing (the two mistakes that made props float or sink)
- **Pivot height.** Many Rockstar props pivot at MID-height (bbMin.z < 0), e.g. the casino reception desk (±0.62), chests of drawers,
  safes, hampers. Placing their origin on the floor sinks half of them; then anything placed "on top" floats.
  Place every prop at `floor + base_height + max(0, -bbMin.z)`. Our build does this automatically.
- **Facing.** A prop's front is its **-Y** side. In a lot frame with headings: 0 faces -v (back to the north wall), 90 faces +u (back to
  the west wall), 180 faces +v, 270 faces -u.
- **Not every prop faces -Y.** Some (e.g. `sf_prop_sf_monitor_s_02a`) have their screen on +Y. Check one shot from each side
  before trusting a heading on a new prop.
- **Pivot in plan.** Beds pivot at the headboard (y from -L to 0); sofas and corner sofas pivot at a corner; check `bbMin/bbMax`
  before assuming centred.
- Run `tools/footprint_check.py` before every build: props through walls, overlapping each other, or blocking a doorway (±0.8 m).
  Chairs tucked a few cm under a table are fine.

## What looked wrong, and the fix
| Problem | Cause | Fix |
|---|---|---|
| Half-sunk furniture, floating monitor/phone | mid-height pivots | the pivot rule above |
| Reception desk "not proper" | our extra monitor faced the visitors and a wall wreath (`apa_mp_h_acc_vase_flowers_04`) stood on the counter | `ch_chint01_reception_desk` already has built-in screens facing the staff: add nothing but a phone, files and a real vase (`ex_mp_h_acc_vase_flowers_02`) |
| Benches facing the wall, people sitting on them backwards | a prop's 'front' is not always its +Y (prop_bench_01a seats toward its -Y) | before placing a seat in rows, look at ONE from the side in game; the sit spot and the prop must agree |
| Screen washed white in a bright room, still white after leaving | a dark-tuned timecycle (V_Metro_station) raises exposure; strong lights on pale stone blow out, and eye adaptation carries it outside | lit public rooms take a neutral timecycle (INT_mall); keep light energy moderate |
| White glow on pale floors inside shop / restaurant units | INT_smshop (the 24/7 preset) adds bloom 0.45, a haze fog and sky light at 0.5 (INT_mall: no bloom, natural ambient 0) | give shop units INT_mall too; compare presets by dumping timecycle_mods*.xml from update.rpf (survey/scan_tcmods2.ps1 pattern) |
| Black panels where mirrors should be; then a grey "glass" mirror with no reflection | a mirror needs Rockstar's mirror shader AND a mirror portal | see doc 02, Mirrors |
| Sinks with pipes showing over the counter | wall-hung basins (`prop_sink_05`) set on a counter | cut a hole in the counter top, drop in an inset basin (`v_res_mbsink`), add a faucet |
| Dirty orange "stone" | the kit's `onyx` texture | marble walls/floors, black granite (`nero`) tops |
| Bare poles for floor lamps | some `apa_mp_h_lit_floorlamp_*` draw only the pole out of their room | use `apa_mp_h_lit_floorlamp_17` |
| Blue casino stall doors in an office | `ch_prop_ch_toilet_door_flat` | `sf_prop_sf_door_bth_01a` |
| Arcade posters in a penthouse | `ch_prop_ch_wallart_*` are game posters | `h4_prop_office_painting_*`, `ex_office_swag_paintings*`, `ch_prop_vault_painting_*`, `v_res_picture_frame` |
| Paintings floating, an empty frame, overlapping canvases | `ex_office_swag_paintings*` are leaning stacks of loot, not wall art; wall art placed 8 cm off the wall | single canvases (`ch_prop_vault_painting_*`, `h4_prop_office_painting_*`; back plane at y +0.01) placed 1.2 cm from the wall face |
| A "counter" with a toilet in the kitchen | `v_res_m_sinkunit` is Michael's bathroom sink unit (with the toilet) | build the counter in the kit, inset `prop_ff_sink_01` + faucet, appliances on the top |
| Office chair facing the wall | heading convention: a chair's front is -Y like every prop | chair heading = facing the desk |
| Reception desk without collision | interior-only pieces (`ch_chint01_*`) carry no prop collision | build counters in the kit (collision) and dress them with props |
| Whole-kitchen props (`apa_mp_h_kit_kitchen_01_a`) | shell pieces: draw as floating frames outside their apartment | counters built in the kit + real appliances on top |

## Interior-only archetypes
Props that live only in a vanilla interior's ytyp (apartment fireplaces, executive vanities) **can't be spawned by script** before
their interior loads (`RequestModel` fails), but they work inside our MLO once their ytyp is in the dependency list. To show them,
visit the vanilla interior (e.g. `RequestIpl('apa_v_mp_h_01_a')`, Eclipse Towers -786.87, 315.76, 217.64).

## Proven pieces
- Parking: `prop_wall_light_05a` is the fitting Rockstar's own carpark uses (pivot at its top: hang it at the ceiling or on a
  rod); `prop_park_ticket_01` pay station, `prop_bollard_04`, `prop_fire_hosereel` (pivot mid-height), `prop_cctv_cam_01a`.
  Rockstar's carpark shader recipe (`hei_dt1_11_garage`): floor `normal_spec_detail` bumpiness 1 / spec 1 / falloff 120,
  walls falloff 120 / fresnel .95, ceilings and columns bumpiness .4 / spec .4 / falloff 190, markings `normal_spec_decal`.
- Real fire: `apa_mp_h_01_living_fire` (+ `apa_mp_h_01_living_firegls1` glass) from the high-life apartment; `prop_beach_fire`
  (logs + live flames; works indoors).
- Inset basin: `v_res_mbsink` (0.82 × 0.42 × 0.16, pivot mid-height).
- Big TVs: the largest vanilla screen is the casino penthouse cinema TV (`vw_prop_vw_cinema_tv_01`, 3.1 m ≈ 140 in);
  `prop_tv_flat_01` ≈ 97 in. Anything bigger is a custom prop (doc 04).
- Gun lockers `bkr_prop_gunlocker_01a`, racks `prop_cs_gunrack`, rifle crates `ba_prop_battle_crates_rifles_*`.

## Lessons from review 2 (2026-10-22)
- Never hang art in an opening: check the wall actually exists at the painting's u/v (an open-plan opening has no wall).
- A coffee table holds what sits on it: when you remove a table, remove or move everything placed at its top height. Trays
  (`apa_mp_h_acc_tray_01`, 0.44 m with its vases) belong ON a table (z 0.45), never on the floor.
- Monitors / screens face the person who uses them: check the chair side before choosing the heading.
- Stall doors: `sf_prop_sf_door_bth_01a` is 1.30 m wide (bounds) - it never fits a 1.10 m stall gap. Leave stalls open or size
  the gap from the door's true bounds.

## Furnishing many units fast (Tower City upper floors, 2026-10-23)
- Place props by the CENTRE of their bounding box, not their pivot: pivots of sofas, bookcases, exam lights, guitar cases are
  off-centre (apa_mpa2_living_books y -3.06..-0.13). centre = where you want it; pivot = centre - R(heading) * bbox centre.
- Mirrored layouts (two sides of a mall, u = -a): heading h becomes 360 - h, and compute the pivot from the FINAL heading (the
  model itself is never mirrored, so an off-centre pivot must be re-derived, not reflected).
- `apa_mp_h_*_books` / `apa_mpa*_living_books` are the books of an apartment's built-in shelves (no carcass, long in y): build kit
  bookcases and fill them with `vw_prop_book_stack_03a/03b` (upright rows), `02a`/`01a` (lying stacks).
- `apa_props_skinned` (apartment treadmill / cross-trainer) are skinned models: avoid as MLO entities. Gym kit that is plain:
  `prop_muscle_bench_01..06`, `prop_weight_bench_02`, `prop_weight_rack_01/02`, `prop_exer_bike_01`, `prop_punch_bag_l` (pivot at
  its top: hang it, add a chain), `prop_beach_punchbag`, `prop_yoga_mat_01..03`.
- Useful shop sets: barber `v_serv_bs_barbchair*`, salon `v_ilev_hd_chair`, optician `prop_sglasses_stand_*` + `prop_disp_cabinet_01`,
  dental stand-ins `v_med_examlight` + `v_med_cor_lightbox` + `v_serv_bs_barbchair3`, news `prop_news_disp_0*a` + `v_res_j_magrack`,
  music `sf_prop_sf_piano_01a`, `sf_prop_sf_guitars_rack_01a`, `prop_el_guitar_0*` (pivot mid: hang on the wall), phones
  `prop_phone_ing*` / `prop_player_phone_01` (stand upright on a table), glass office fronts `v_corp_go_glass2` (scale XY to fit).
- Tool: Tower City `work/upper_check.py` runs `tools/footprint_check.py` on a build's layout (unit rects + doorways exported by the
  build); `work/upper_gap_check.py` is the light-gap audit for those floors.
