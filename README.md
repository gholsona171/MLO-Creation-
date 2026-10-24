# FiveM MLO Playbook

What we learned building custom MLOs (Cloud 9 nightclub, Tower City: mall, tower, casino, penthouse, head office and parking) for
ClevelandRP, written so the next build starts where this one finished. Every rule here was paid for with a broken build, a
crash or a correction. The `tools/` folder holds the scripts that do the work; each doc names the tool for its job.

This folder is meant to become a GitHub repo. Nothing in it contains keys, licence files or server credentials. Keep it that way.

## Read in this order
1. [Pipeline](docs/01-pipeline.md): the build chain, the gates, deploying, the test rig.
2. [MLO structure](docs/02-mlo-structure.md): rooms, portals, collision, LODs, the rules the engine enforces silently.
3. [Props and furnishing](docs/03-props.md): real GTA props, pivots, facing, the catalogue, what looks wrong and why.
4. [Custom props](docs/04-custom-props.md): modelling our own (the 181-inch TV, the urinal, the faucet), render targets.
5. [Water and pools](docs/05-water-pools.md): water that looks right, and water you can swim in.
6. [Doors and lifts](docs/06-doors-lifts.md): native doors, sliding lift doors, DoorSystem quirks.
7. [Verification](docs/07-verification.md): screenshots, fly-through videos, frame review, what to check before saying done.
8. [Working agreements](docs/08-working-agreements.md): how Antonio wants the work done.

## Tools at a glance
See [tools/README.md](tools/README.md). The short list:

| Job | Tool |
|---|---|
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
| Collision as one BVH child per room (physics-pool crash) | `merge_cols.py` |
| Video → frame contact sheets for review | `video_review.py` |
| Ground holes / steps and drawn-vs-collision, offline on the built files (before deploying) | `wow2easy_move/tools/hole_grid_offline.py`, `seen_vs_solid.py` (see 07) |

## Where the live projects are
- Tower City workspace: `C:\Users\anton\Documents\Codex\TowerCity` (build scripts in `work/`, surveys in `survey/`).
- Local test server (rig): `C:\C9Test` (rig scripts `t.sh`, `tc_restart.sh`, `tc_tviews.sh`, `tc_fly.sh`).
