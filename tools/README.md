# Tools

All PowerShell tools load CodeWalker.Core.dll and read the game archives directly (read-only). Paths at the top of each script:
GTA V install and the CodeWalker folder — change them for another PC.

| Tool | What it does | Example |
|---|---|---|
| `shipping/make_conflict_check.py` | **Required for every shipped MLO.** Writes `<res>/tools/check_conflicts.ps1` from the build's own stream files (+ area family regex, IPL refs); our folders skipped. Run in the assemble step; prove on a planted conflict (docs/10) | `py -3 shipping/make_conflict_check.py --stream res/stream --res my_mlo --name "My MLO" --area "Strawberry Ave, x 100 y -1500"` |
| `prop_catalogue.ps1` | Catalogues every furniture / clutter / cash / fixture archetype in the game with exact bounds and ytyp → `prop_catalogue.json` | `powershell -File prop_catalogue.ps1` |
| `find_arch_ytyp.ps1` | The ytyp + bounds of named props, merged into `arch_ytyp.json` (the MLO's dependency list comes from it) | `powershell -Command "& '.\find_arch_ytyp.ps1' -Names @('v_res_mbsink','prop_beach_fire')"` |
| `ydr_xml.ps1` | Game drawable → CodeWalker XML + textures (read Rockstar's shaders); XML → ydr (import our own) | `-Mode export -Name prop_tv_flat_01 -Out tv` / `-Mode import -In x.ydr.xml -Out x.ydr` |
| `ybn_xml.ps1` | Collision file ↔ XML | `-Mode export -In a.ybn -Out a.xml` |
| `vanilla_bounds_by_material.ps1` | Finds collision polygons of a material in an area (how we found Rockstar's pool water surfaces) and exports one file | edit the area box + material index |
| `water_xml.ps1` | Extracts the game's water maps | `powershell -File water_xml.ps1` |
| `scan_garage_doors.ps1` | Every garage-door archetype (special attribute 5) with bounds, flags and ytyp | `powershell -File scan_garage_doors.ps1 > garage_doors.tsv` |
| `pool_water.py` | Vanilla water map + a pool's 2 m swim cells (inside a raised deck) → `tc_water.xml` | `py -3 pool_water.py` |
| `water.lua` | Client: `LoadWaterFromPath` the map, reload after Cayo, `ResetWater` on stop | ship in the resource |
| `water_diff.lua` | City-wide stray-water check: vanilla vs our water map on a grid, lists every difference | run in a client (rig `t.sh`) |
| `custom_props/tc_props.py` | Blender build of our own props: the render-target TV, the urinal, the faucet (CW XML) | `blender -b --python tc_props.py` |
| `custom_props/props_meta.py` | Render-target texture patch, CodeWalker import, ytyp compile, survey update | `py -3 props_meta.py` |
| `footprint_check.py` | Props through walls / overlapping / in doorways, pivot-aware | `py -3 footprint_check.py props.json arch_ytyp.json` |
| `video_review.py` | Walkthrough video → labelled frame contact sheets for review | `py -3 video_review.py walk.mp4 review 3 2` |
| `merge_cols.py` | Blender: join an MLO's collision into one mesh per room before the composite (one BVH child per room: phInstGta pool) | `from merge_cols import merge_cols` in the build |
| `tc_tviews.sh` | Rig: screenshots from a scripted camera in a lot frame | `OX=.. OY=.. bash tc_tviews.sh tag "name u v z tu tv tz"` |
| `tc_fly.sh` | Rig: fly-through video along waypoints | `bash tc_fly.sh out.mp4 1.6 "u v z" "u v z" ...` |

The project-specific build (rooms, partitions, layout tables) lives in the Tower City workspace (`work/tower_crown.py`, `work/tc_kit.py`).

### Clearing a block's edges and its ground (Tower City exterior review, 2026-10-24) - in `towercity/`
| Tool | What it does | Example |
|---|---|---|
| `extract_by_name.ps1` | Extracts game files by FILE NAME (best-ranked copy: patchday > dlc_patch > dlcpacks > base), resources re-saved as standalone RSC7 (a raw ydr extract will not import) | `-Out src/native -Names dt1_rd1_r1_12.ydr,dt1_rd1_fwy02.ydr` |
| `arch_dict.ps1` | The ytyp, drawableDictionary and txd of named archetypes (which .ydd holds a LOD / SLOD1 model); hash-only names (`hash_d50b466a`) match by Jenkins hash | `-Names dt1_props_combo0109_slod,hash_d50b466a` |
| `face_dump.py` / `tri_dump.py` | Blender: every face centre / triangle of vanilla drawables in world space (+ material) - plan cuts from Rockstar's own geometry | `blender -b --python tri_dump.py -- src/native out.json name ...` |
| `col_near.py` | Blender: which collision objects of which ybn reach a lot-frame box (finds a pillar's / wall's collision) | `-- dir u0 u1 v0 v1 z0 z1 names...` |
| `ybn_in_zones.ps1` | Every downtown ybn with triangles in the clean-up zones (the files the collision cut must process) | `powershell -File ybn_in_zones.ps1` |
| `ext_plan.py` + `ext_rules.py` | Zone rules for vanilla models: cut (polygon + height band + material), clone (Rockstar's own edge across a gap), move (a pillar), entity removal, occluder zones; applied inside `l0_cut.py` / `l0_col.py` | `py -3 ext_plan.py` |
| `ext_build.py` / `ext_meta.py` | Our paving over removed drives (copied base-tarmac triangles + 12 mm), a removed block's footprint, a pit closed; bollards / benches as map entities | `blender -b --python ext_build.py` |
| `lot_ground.py` + `l0_slab.py` | The lot slab's edge sampled every 0.5 m on the ground outside it; the inside draped from it | `py -3 lot_ground.py` |
| `slab_edge_check.py` | Gate: slab edge vs the ground outside it, every metre (proven on the 1.18 m Alta St defect) | `py -3 slab_edge_check.py [slab dir]` |
| `l0_occl.ps1` | Every vanilla occluder over the lots / zones, by overlap (not centre), from every `*occl*` ymap | `-Report` to list |
| `l0_maps.py` | + the LOD rule: a LOD / SLOD1 whose every descendant is gone is swapped (the floating rooftop props) | assemble runs it |
| `build_l0.sh` | Rebuilds every level-0 output from source + gates, then assembles (`ASSEMBLE=0` level 0 only) | `bash build_l0.sh` |
| `l0_cut_lod.py` | District LOD cut by the lot outline + the move rules' `lod` entries (a moved vanilla piece moved in its LOD / SLOD1 too; those are never lot-cut) | `blender -b --python l0_cut_lod.py -- file.ydd name ...` |
| `pair_sheet.py` | Before / after pair sheet from two shot folders with the same camera names (fails on a missing frame) | `py -3 pair_sheet.py before/ after/ out.jpg i1_under i2_top` |
| `tc_ext_final.sh` | Rig cameras for the last exterior items, incl. the forced-LOD trio (normal / `OverrideLodscaleThisFrame` 0.08 / 0.04) | `bash tc_ext_final.sh <tag> [i1..i4]` |

### Mall interior gates (Tower City mall review, 2026-10-24) - in `towercity/`
Read the build outputs (`tris_*.npy` + `mats_*.npy` triangle kinds, layouts' portals / `gap_regions` / `windows` / `street_partitions` /
`mirrors`, `signs.json`, `anchors.json`, all written by `tc_kit.export_all`); each one was proven on the defect it was written for.
| Tool | What it does | Example |
|---|---|---|
| `mall_gap_check.py` | Blender: portal-aware light-gap audit - a face counts only where the game DRAWS it (own room, or a room reached through a portal / seen through its portal's rectangle); seam scan of every outer wall; windows straddling a wall; mirror reflections that would show black | `blender -b --python mall_gap_check.py [-- only=prom,avenue pass=2 dirs=150]`, `-- probe=room,x,y,z,dx,dy,dz` traces one ray |
| `sign_check.py` | Every sign vs every triangle and prop: CLIP / FRONT / VIEW / WALL / TEXT | `py -3 sign_check.py --list [--debug name]` |
| `hang_check.py` | Every hung / mounted fitting meets its support within 8 cm (lamps, pendants, chandeliers, hanging-sign rods, flag wires) | `py -3 hang_check.py --list` |
| `upper_gap_check.py` | Upper floors' light-gap audit; now reads the window list (piers and raised sills included) from the layout | `blender -b --python upper_gap_check.py` |

### Counter kit: Rockstar props cut into modules (C9 DJ, 2026-10-25) - in `counter_kit/` (doc 11)
| Tool | What it does | Example |
|---|---|---|
| `../counters_scan.ps1` | Every counter / desk / bar / till archetype with counter-like bounds: ytyp, interior or prop, txd, size | `powershell -File counters_scan.ps1 -Out C:	mp\counters.tsv` |
| `../arch_info.ps1` | Texture dictionary, flags, lodDist, physics dictionary of named archetypes | `-Names bkr_bar_bar01,ba_trad_lower_bar` |
| `rsx.py` | Rockstar ydr XML as arrays: plane cuts with every attribute interpolated, turn / mirror / merge, write back with box collision or the source's own bounds moved; outline sections + gap check | library |
| `rsxview.py` | numpy textured rasteriser for previews and seam checks (no game needed) | library |
| `counters.py` + `counters_sets.py` + `counters_out.py` | The module recipes (straight, mitred corners, band / pedestal / native / composed ends, copied legs), welded joint faces, collision through the same recipe, auto collision for interior pieces, joint check gate, ytd per style, shop rows, joint table | `py -3 counters_out.py --check` / `py -3 counters_out.py` |
| `cw.ps1` | CodeWalker on Windows: ydr / ytyp / ytd (from a folder of .dds) import, `tex` finds named textures anywhere in the game | `cw.ps1 tex a,b out_dir preferred_txd` |
| `tints.ps1` | The tint values Rockstar gives an archetype's MLO entities (palette rows) | `-Names bkr_int_02_bar_wood` |
| `assemble_preview.py` | Chains modules by their joints (the placer's maths) and renders the result | `py -3 assemble_preview.py bkrw out.png el,s200,oc,s100,er` |
| `rig/placeat.sh`, `aimplace.sh`, `tab.sh`, `buy.sh`, `store.sh`, `cam.sh` | Rig: buy / place / store furniture through the real tablet and laser, aiming the laser at an exact floor point | `FP=1 bash placeat.sh <id> <x> <y> <standx> <standy> <tag>` |

### Site survey (Justice Center, 2026-10-28) - in `survey/` (doc 12; paths at the top of each script point at the JusticeCenter workspace)
| Tool | What it does | Example |
|---|---|---|
| `find_names.ps1` | Archetypes + files whose names match a regex, with ytyp and bounds | `-Rx 'cityhall|court'` |
| `block_files.ps1` | Every file of a block family (any prefix: `lr_`, `hei_`, `hi@`, `ma@`) + every entity of its ymaps | `-Rx '^(hei_|lr_|ma@|hi@)*sc1_19'` |
| `site_scan.ps1` | Entities within R (+ bounds), occluders, LOD / distant lights, car gens, ybns by bounds, path nodes, scenarios in a box | `-X 330 -Y -1615 -R 170` |
| `scenarios.ps1` | Scenario points of named regions in a box, with type names | `-BX0 .. -BY1 ..` |
| `ybn_heightmap.py` | Top-surface height map of ybn XML (triangles + boxes), 0.5 m | `py -3 ybn_heightmap.py` |
| `site_measure.py` / `lot_frame_map.py` | Min-area rectangles (grid heading, footprints) / the map in the lot frame with a 10 m grid | `py -3 site_measure.py` |
| `site_json.py` / `plan_v0.py` | site.json from the scans / the fit proposal drawn on the calibrated top-down | `py -3 plan_v0.py` |
| `survey_shots.sh` | Rig cameras; saves and restores the player's position, `tc_release.sh` on exit | `bash survey_shots.sh out "front x y z tx ty tz 50"` |
| `topdown_calib.sh` | Top-down shot + world -> screen calibration grid | `bash topdown_calib.sh plan.png 335 -1620 900 18 29` |
| `real_osm.py` | OpenStreetMap Overpass JSON -> cleaned GeoJSON + local metres; prints every building's levels / height | `py -3 real_osm.py` |
| `fit_v1.py` | The real layout on a GTA block at ONE scale (rotation + translation, LP per rotation, largest feasible scale) | `py -3 fit_v1.py` |
| `design_v1.py` | Floors (real height x scale, real floor counts), interiors vs shell, entrances, sally port on the fitted outlines | `py -3 design_v1.py` |
| `real_layout.py` / `plan_v1.py` / `section_v1.py` | Real footprint plan (north up) / plan on the calibrated top-down / elevation + every floor | `py -3 plan_v1.py` |
| `removal_v1.py` / `lights_dump.ps1` | Everything inside the kerb to remove (entities, LODs, ybns, occluders, LOD lights, AI) / distant-light positions | `py -3 removal_v1.py` |
| `map_data_sheet.py` | Four panels: collision heights, traffic, scenarios, entities, with the plan outlines | `py -3 map_data_sheet.py` |
