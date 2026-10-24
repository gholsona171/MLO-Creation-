# Tools

All PowerShell tools load CodeWalker.Core.dll and read the game archives directly (read-only). Paths at the top of each script:
GTA V install and the CodeWalker folder — change them for another PC.

| Tool | What it does | Example |
|---|---|---|
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
