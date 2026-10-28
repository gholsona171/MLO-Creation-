# 12 · Surveying a new lot (Justice Center, 2026-10-28)

The survey phase before any modelling: find the vanilla block, list every file that draws, collides, occludes, lights or
populates it, measure it, photograph it, and propose the fit. Worked example: `Documents\Codex\JusticeCenter\survey\`
(site.md / site.json / fit.md / plan_v0.png). Tools: `tools/survey/` (all read-only on the game).

## Steps
1. **Find the block by model name**, not by memory: `find_names.ps1 -Rx 'cityhall|court'` lists archetypes + files. Rockstar's
   names are a strong hint but not the in-game sign (Davis: the tower is `sc1_19_courts`; the model `sc1_19_city_hall` carries a
   PUBLIC LIBRARY sign). The block prefix (`sc1_19`) is the file family.
2. **Every file of the family, every prefix**: `block_files.ps1 -Rx '^(hei_|lr_|m\d+_\d+_|ma@|hi@)*sc1_19'` -> block_files.tsv +
   every entity of its ymaps (position, lod level, lodDist, parentIndex).
3. **Which copy is live: ask the game.** `IsIplActive(name)` on the rig for each prefix variant. In South LS the live ymaps are the
   **`lr_` (Lowriders, mplowrider)** copies; `hei_` and base are off. A path rank alone would have picked the wrong copy.
   Edit all same-named variants in the removal anyway (another server's IPL state may differ).
4. **Everything around it**: `site_scan.ps1` (entities within R with archetype bounds, box occluders + occlude models, LOD /
   distant lights, car generators, every ybn whose bounds reach the box, path nodes) and `scenarios.ps1` (scenario points with
   type names). Also check the active LOD-light set the same way (`vw_` on the rig).
5. **Measure from the collision**: extract the block ybns (`towercity/extract_by_name.ps1`), export XML (`ybn_xml.ps1`), then
   `ybn_heightmap.py` rasterises every triangle + box primitive (box = 4 alternate corners + their reflections through the centre)
   into a top-surface height map. `site_measure.py` gives min-area rectangles: the grid heading (Davis: 50.0 deg) and exact
   footprints (tower 48.3 m square, roof z 91.7). `lot_frame_map.py` resamples it into the lot frame with a 10 m grid: the drawing
   everything else is planned on.
6. **Street names**: `GetStreetNameAtCoord` / `GetNameOfZone` at points round the block on the rig.
7. **Shots**: `survey_shots.sh <dir> "name x y z tx ty tz fov" ...` (front, both sides, rear, aerial) and `topdown_calib.sh`, which
   also writes the world -> screen calibration of the top-down (`GetScreenCoordFromWorldCoord` on a 50 m grid while the camera is
   live). `plan_v0.py` draws the proposal on that calibrated shot.
8. **Write site.md / site.json / fit.md** and the open questions; no modelling until the fit is approved.

## Rig manners (Antonio may be playing on client 1)
- `tc_release.sh` unfreezes the ped where the shot camera left it - in the air over the lot. `survey_shots.sh` saves the ped's
  position and heading first and puts him back after `tc_release.sh` (trap on EXIT), so a camera run never strands the player.
- Keep a run to one batch of cameras (about 1 minute). If the server is down, `tc_restart.sh` brings it up (about 4 minutes).

## Traps found
- `Rank()` in the extract scripts reads `patchday2ng` as patchday 2 (rank 102 > dlc_patch 60). Harmless when names differ
  (`lr_` vs `hei_`), but never trust the rank to tell which IPL is on.
- `YbnFile` XML vertices are relative to each child's `GeometryCenter`; add it (and the `CompositeTransform`) before use.
- Scenario `MyPoint.Type` is null without the scenario type table loaded: read `TypeId` -> region `LookUps.TypeNames` hash and
  match against hashed known names (`scenarios.ps1`); unknown ones stay hex.
- CodeWalker's ymap `LODLights` comes back empty when the lodlights ymap is loaded alone (its positions live in the distant-lights
  parent). Count the `distlodlights` ymap; the `lodlights` twin has the same lights.
