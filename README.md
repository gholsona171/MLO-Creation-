# FiveM MLO Playbook

What we learned building custom MLOs (Cloud 9 nightclub, Tower City: mall, tower, casino, penthouse, head office and parking) for
ClevelandRP, written so the next build starts where this one finished. Every rule here was paid for with a broken build, a
crash or a correction. The `tools/` folder holds the scripts that do the work; each doc names the tool for its job.

This is the GitHub repo `gholsona171/MLO-Creation-`. Its working clone lives in `Documents\Codex\MLO-Creation` (not on the Desktop):
pull before reading, and commit + push every new lesson or tool the same day it is learned. Nothing in it contains keys, licence
files or server credentials. Keep it that way.

## Read in this order
1. [Pipeline](docs/01-pipeline.md): the build chain, the gates, deploying, the test rig.
2. [MLO structure](docs/02-mlo-structure.md): rooms, portals, collision, LODs, the rules the engine enforces silently.
3. [Props and furnishing](docs/03-props.md): real GTA props, pivots, facing, the catalogue, what looks wrong and why.
4. [Custom props](docs/04-custom-props.md): modelling our own (the 181-inch TV, the urinal, the faucet), render targets.
5. [Water and pools](docs/05-water-pools.md): water that looks right, and water you can swim in.
6. [Doors and lifts](docs/06-doors-lifts.md): native doors, sliding lift doors, DoorSystem quirks.
7. [Verification](docs/07-verification.md): screenshots, fly-through videos, frame review, what to check before saying done.
8. [Working agreements](docs/08-working-agreements.md): how Antonio wants the work done.
9. [Field notes](docs/09-field-notes.md): the short original lessons (LOD hiding, ymap gotchas, stairs, seating, doors, mirrors...).
10. [Shipping](docs/10-shipping.md): **every MLO ships with a conflict checker + a buyer README telling how to use it** (rule), the package checklist.
11. [Modular props](docs/11-modular-props.md): cutting Rockstar props (bars, counters) into modules that snap edge to edge, full-size copies of interior-only props, collision / tint traps found in game.
12. [Site survey](docs/12-site-survey.md): finding a vanilla block, its live (`lr_` / `hei_`) files, occluders, lights, AI, measuring it
    from its collision, rig shots that put the player back, and the fit proposal (Justice Center, Davis).

## Tools at a glance
See [tools/README.md](tools/README.md). The short list:

| Job | Tool |
|---|---|
| **Conflict checker shipped inside every MLO** (built from the package's own files) | `shipping/make_conflict_check.py` + `check_conflicts.ps1.in` |
| Every furniture / clutter / cash prop in the game, with sizes | `prop_catalogue.ps1` |
| Which ytyp holds a prop, and its bounds | `find_arch_ytyp.ps1` |
| Game drawable ↔ CodeWalker XML (read Rockstar's materials, import our own) | `ydr_xml.ps1` |
| Collision ↔ XML | `ybn_xml.ps1` |
| Find how Rockstar built something in collision (by material) | `vanilla_bounds_by_material.ps1` |
| Extract the game's water map | `water_xml.ps1` |
| Every vanilla garage door (roll-up, attribute 5) with sizes | `scan_garage_doors.ps1` |
| Custom prop build (TV with render target, urinal, faucet) | `custom_props/tc_props.py` + `props_meta.py` |
| Swimmable pool (water map cells on the 2 m grid + loader) | `pool_water.py`, `water.lua` |
| Check the city for stray water after shipping a water map | `water_diff.lua` |
| Prop footprint check: walls, doorways, overlaps (pivot-aware) | `footprint_check.py` |
| Every counter-like archetype in the game (size, interior or spawnable) | `counters_scan.ps1`, `arch_info.ps1` |
| Rockstar drawables cut / turned / mitred into snapping modules, own collision, preview renders | `counter_kit/` (doc 11) |
| Collision as one BVH child per room (physics-pool crash) | `merge_cols.py` |
| Survey a new lot: block files, live variant, occluders, lights, AI, collision height map, calibrated top-down (doc 12) | `survey/` |
| Video → frame contact sheets for review | `video_review.py` |
| Clear a whole vanilla block to one flat lot: outline from Rockstar's sidewalk edge, removals, LOD / SLOD cuts, collision, occluders, LOD lights, AI off, gates + rig probes (doc 02 / 07) | `justice/` (`build_p1.sh`) |
| Ground holes / steps and drawn-vs-collision, offline on the built files (before deploying) | `wow2easy_move/tools/hole_grid_offline.py`, `seen_vs_solid.py` (see 07) |

## Project tools (copies; the projects stay where they run from)
- `tools/towercity/`: level-0 vanilla removal (`l0_cut`, `l0_col`, `l0_maps`), `area_clear.lua` (AI traffic, navmesh and scenarios
  off inside the lots), `vanilla_off.lua`, the in-game probes (`vis_col_check`, `fly_check`), upper-floor checks, RPF extract and
  MLO export scripts.
- `tools/garage/`: ground checks from the junkyard garage: `hole_grid` (in game) and `hole_grid_offline`, `crack_check`,
  `seen_vs_solid`, `door_swing_check`, `ground_map`, `cw_xml` (CodeWalker XML export).

## Where the live projects are
- Tower City workspace: `C:\Users\anton\Documents\Codex\TowerCity` (build scripts in `work/`, surveys in `survey/`).
- Justice Center workspace (survey + phase 1 block clearing, 2026-10-28): `C:\Users\anton\Documents\Codex\JusticeCenter` (`survey/`, `work/`, `shots/`).
- Local test server (rig): `C:\C9Test` (rig scripts `t.sh`, `tc_restart.sh`, `tc_tviews.sh`, `tc_fly.sh`).
