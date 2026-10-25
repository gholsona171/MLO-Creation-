# 07 · Verification

Nothing is done until it has been seen on the rig.

1. **Rebuild → gates pass → deploy → `tc_restart.sh`.**
2. **Probe with Lua** (`t.sh cl 1 "..."`): the ped stands where expected, the interior/room id, door states, lift stops, water state.
3. **Targeted screenshots** of every changed spot (`tc_tviews.sh <tag> "name u v z tu tv tz" ...`); tile them 2×2 for review.
   Keep the camera inside the room: a camera inside a ceiling or wall shows grey.
4. **Walkthrough video** (`tc_fly.sh`) through every room at walking speed; send it compressed under 30 MB for phone viewing
   (ffmpeg scale 960, crf 28).
5. **Frame review**: cut a frame every 3 s and review contact sheets (`tools/video_review.py`); list everything wrong by room before
   reporting.
6. Test interactions for real: push doors, ride lifts with and without access, sit-test every seat, swim in pools.
7. Write the MLO data file (doors, lifts, spots, TVs, seats) and its README from the build tables, never by hand.

Pitfalls seen:
- A stopped background job kept running and took over the camera for two minutes of a recording.
- Deploying while the server runs crashed the client; always restart the rig after deploying.
- A dead harness ped silently ignores tasks; revive it before walking tests.

## Missing ceilings / faces (review 2)
- If a room shows sky through its ceiling, the build's face cullers removed it. Run the build with
  `TC_CULL_DEBUG=<drawable name part>` (e.g. `ph_wc`): both cullers print each removed horizontal face and the box that removed it.
- Rain heads: the drop rod must reach the ceiling (`rain()` now runs it to the room's ceiling height) - a short rod floats.

## Light-gap audit (tools/gap_check.py) - run after every build
- Rays from points inside every room (floor + 0.4, floor + 1.7, ceiling - 0.3, found by rays, so no point is ever outside or in the
  roof void), ~600 directions each; a ray that leaves the building without SEEING a face is a hole. Faces are one-sided in game: a
  face turned away from the ray does not count (an outward-only wall sheet is invisible from inside).
- Pass 2 scans every outer wall point by point (0.1 m along, 0.2 m up, straight out and +-25 deg): thin slits cannot hide there.
- Known openings (door holes the props fill) are listed apart; everything else is a gap. Points inside a solid you added (a column)
  report false gaps - check them in game.
- Typical finds (wow2easy junkyard, 2026-10-23): every outer corner of a sheet-metal shop leaked (inside sheets stop 15-25 cm
  short) -> wall-clad corner columns; a wall cut that started 1 cm under the floor removed a floor strip along the whole cut.

## The seam walk (what the client checks - do it first)
Corners and wall junctions at night; every line where a wall was removed, cut or extended (floor and ceiling); material and colour
where a new surface meets the original (same texture at another UV scale reads as a different floor); what a moved prop exposes;
signs crossing new openings; furniture in door swings; wires/poles left with nothing to hold.

## Site audit (tools/site_audit.sh) - in game, after every deploy, before any shots
Built from what the client found by eye on the junkyard garage (round 6, 2026-10-23); each check exists because a defect slipped through.
- **Openings, no locks:** every gate and door is walked through BOTH ways by the player ped with every lock script stopped. Ship
  without locks unless told otherwise. Failures found: a door seated on the average ground (its foot buried 0.3-0.6 m in sand on
  the high side) and the wall header cut to a fixed height below the door's top (jammed). Seat doors on the HIGH ground under their
  swing; cut the opening to the door's own top + 10 cm.
- **What's behind a door:** check the far side with in-game ray fans, not a list of entity centres - yard objects (containers 13 m
  long, wrecks) reach far from their origin. Never clear a client's yard to make room: move the door to a clear stretch.
- **Ground underfoot:** a ray grid over the new blacktop reading the collision MATERIAL. Anything that is not the lot's own material
  is a leftover: an old slab, porch pad, apron, dirt track, terrain. Removing faces from a drawable does NOT remove its collision -
  cut both, from the same rule.
- **Ground you see:** removed slabs leave gravel strips and concrete edges under porches and at doors - look under every roof
  overhang and at every door threshold.

## Wires, poles and lamps when buildings go (tools: wires.py, lodlights.py)
- A removed building leaves its utility feeds: transformer poles with service drops, spans ending in air, wall insulators.
  Every span end must sit on a standing pole or one of our insulators; a pole whose only job was feeding the removed building goes
  (with its spans) - a transformer pole beside the new building looked absurd, its drops hung to the ground.
- wires.py prints WIRES_SAG for any kept span whose lowest point is under 3 m above the ground (a re-hung SHORT span keeps its long
  sag and loops to the floor). Zero is the pass mark.
- Night: every light that belonged to a removed building, sign or board keeps glowing as a distant LOD light over nothing - move it
  to z -1000 in every distlodlights_* copy (base, apa_, hei_, vw_, m25_2_), keep lights that still have a lamp within 3 m. Check
  for another resource already shipping the same file (Tower City ships other indices - no clash here, but check).
- Hold the clock for night shots: a time-sync resource overrides one-off NetworkOverrideClockTime calls (shots came out at noon).

## Drive clearance (Tower City parking, 2026-10-23)
- Every drive path (bridge in, deck to deck, out of the doors) is a polyline in the plan module with a floor height function
  that knows the ramp, the bridge and the apron by position. `gar_gap_check.py` samples it every 0.5 m and casts a car's cross-
  section (rays 1.1 m each side at 0.5 / 1.3 / 2.35 m, rays up 2.1 m from both sides and the centre) against every exported
  triangle: zero hits or nothing deploys. A pure test checks the same paths for steps and grades over 1:7.
- Run it after the lot slab is rebuilt: the first run "hit" a stale slab ridge over the apron - the right finding (see 02).

## Probes must prove they ran (2026-10-23)
- From Python on Windows, `subprocess.run(['bash', ...])` starts **WSL's** bash (no distro installed), not Git Bash: every call to the
  rig failed, returned nothing, and the probes reported "0 problems". Call Git Bash by its full path
  (`C:\Program Files\Git\bin\bash.exe`), and make every rig call that gets no answer **raise** ("nothing was tested"), never pass.
- Before trusting any new check, run it once on a defect you already know is there (the junkyard's north-porch hole). If it does
  not flag it, the check is wrong, not the build.
- Surface probes (rays onto our own model faces) miss ground that another model draws (gravel, vanilla terrain, decals). Run the
  model-independent **hole grid** too (`wow2easy_move/tools/hole_grid.py`): a 0.5 m ray grid over the whole site through every
  layer to the lowest collision, flagging holes, pits, and "floating" cells (a roof / canopy with no ground under it), plus the
  step between laid asphalt and the ground beside it.
- Sweep floor heights are per build: adding the parking's floors (32.4 / 41.0) to the global "visible above this floor" list
  surfaced 52 hidden ceiling-top faces in the mall at the same height. Give each build its own extra floors (`LOT_FLOORS`).

## Offline ground checks before deploying (wow2easy_move/tools, 2026-10-23)
- **Shape-test rays are one-sided:** a ray going down only hits faces turned UP (counter-clockwise from above). Checked on the
  junkyard scan: an up-facing-only cast of the built files matched 76 of 78 in-game holes and all but 235 of 74,212 cell heights
  to 0.1 m (median 3 mm); a two-sided cast read every slab's underside. A floor face wound the wrong way is a hole.
- `hole_grid_offline.py [--compare]`: hole_grid.py's grid, rules and asphalt-edge check run on the BUILT files (CodeWalker XML of
  every shipped ybn + the embedded bounds of our placed drawables at their ymap positions, `cw_xml.ps1`). `--compare` prints how
  far it agrees with the last in-game scan - run it on the deployed build first to trust it, then on the rebuild. Props and doors
  are not loaded (they read 'hole' offline where the game reads 'floating').
- `seen_vs_solid.py`: the drawn ground (high-detail vertex / index buffers of the lot and terrain drawables) against the collision,
  cell by cell, on the blacktop and on the graded apron (0.06 m tolerance). Rockstar's own drawn and collision ground differ by up
  to ~8 cm - printed for reference only.
- `ground_map.py`: the site's ground from Rockstar's own collision (never edited) - the input for grading, not an in-game scan of
  a build that already has your changes in it.
- Offset grid rays off the mesh lines (hole_grid.py: +1.37 / +1.71 cm). A ray exactly on an edge two triangles share can slip
  through in game and offline. The lot's 0.5 m mesh read as rows of false holes on exact .0 / .5 coordinates.

## Buyer conflict check (before handing a map over)
Two resources shipping the same vanilla file name (a `.ymap` / `.ybn`) means only one copy loads: one side's edits silently vanish.
Before a sale, have the buyer run a name-pattern search over his `resources` folder for every vanilla file the map ships
(plus a text search of his scripts for the IPL / interior names the map replaces). Send it as plain text without `*` or `_`
(Discord turns them into italics and the command breaks): use `$PSItem` instead of `$_`, `\x5F` for `_` in the regex, print
each hit as a `CONFLICT ...` line and finish with `CHECK DONE` so an empty result can't be mistaken for a broken run.
Pattern hits are only candidates: the real clashes are hits with the SAME file name as one the map ships.
For a real clash, get his file, convert both to XML (CodeWalker MetaXml; names come back as `hash_XXXXXXXX`, compare by
Jenkins hash) and diff entities and car generators against vanilla. Fold his change into the map's build as a source rule
(Tower City: `plan/buyer_ymap_edits.json`, read by `l0_maps.py`), ship the merged file, and have him delete his copy.

## Door walk that can be trusted (Tower City top floors, 2026-10-24)
- Stop the server's door-lock scripts first (rcore_doorlock, any phone/heist script that locks doors).
- Walk through the LEAF's real middle: find the door object (GetClosestObjectOfType), take the centre of GetModelDimensions via
  GetOffsetFromEntityInWorldCoords and the normal from GetEntityForwardVector. Guessing the hinge side from the layout heading
  walks into the frame and reports false "blocked".
- Place the walker 1 m above the floor (SetEntityCoords at floor height can drop it through and kill it; a dead walker reports
  every door blocked), check IsEntityDead before each pass and resurrect.
- Pass = 1 m past the door line, both directions. Tool: C9Test/tc_topdoors.lua (generated from the layout's door props).
- Prop review shots: aim from the room's centre toward the prop, not along the prop's heading (wall-hung props face the wall's
  normal, but many props' heading points into the wall they stand against).

## Portal-aware gap check, signs, anchors (Tower City mall, 2026-10-24)
Antonio found an open strip in the promenade's ceiling, black patches in three mirrors, signs through walls and soffits, floating
chandeliers and a slit where a wall ended behind a window pane - all in a build whose plain gap check had passed. Four offline
checks now run on the built files (`tools/towercity/`), each proven first on the defect it was written for:
- **`mall_gap_check.py` (Blender) - what the game really DRAWS.** A ray from a point in room R sees a face only if it faces the
  ray, is not see-through glass / a decal (the build saves each triangle's kind: `mats_*.npy`) and belongs to a drawable drawn from
  there: R's own, or one of a room the ray entered through a portal (a portal to limbo draws the exterior models). Faces of other
  drawables are passed (that is the "sky strip": the face exists but is not drawn from this room). A ray that ends seeing nothing
  is a gap unless it left through a limbo portal. Pass 1: rooms on a 3 m grid, 150 directions. Pass 2: the seam scan along every
  outer wall (0.25 m x 11 heights, out / +-30 deg / down-and-out). Pass 0: no inner wall meets a street wall inside a window.
  Pass 3: mirrors (reflected rays from eye points must meet the mirror's own room before any portal). Proven: it flagged the
  promenade's clear-glass crown (1,621 gap cells) and 2,440 black reflected rays in the old mirrors.
  Points are kept only where the first face straight up and straight down is drawn from the room (a point above a vault's soffit
  or inside a soffit box is not in the room) - otherwise every check near a ceiling is noise.
- **`sign_check.py` - every sign against every triangle and prop.** CLIP (anything inside the panel's +-2.5 cm slab), FRONT
  (anything within 1.5 m in front), VIEW (straight-on 2.5 m view a third hidden, or two thirds of all directions), WALL (nothing
  behind it within 25 cm: it floats over an opening), TEXT (letters under 12 cm on a sign 1.5 m+ wide). The build records every
  panel (`signs.json`). First run: 64 of 500 signs failed - over door openings, through ceilings, across pilasters.
- **`hang_check.py` - nothing floats.** Every lamp, pendant, chandelier, hanging-sign rod and flag wire records its support point
  and direction (`anchors.json`); an 8 cm ray from each must meet a face turned toward it. Proven on the old chandeliers (rod tops
  9 m under the glass) and the light bars hung 25 cm off the court walls.
- A window bay must never straddle an inner wall: the build splits a bay with a stone pier where any wall (ground units,
  corridors, the tenant floors' partitions) meets the street wall (`l2_build.street_partitions`). Seventeen bays did
  (three on the ground floor, fourteen on the tenant floors, whose plan said it had avoided them).

## Exterior review from the street (Tower City, 2026-10-24)
- Before cutting a removed building's leftovers, photograph every viewpoint the owner named and keep the cameras in a script
  (`C9Test/tc_ext_after.sh <tag>`): the same cameras after the deploy make the before / after pairs.
- Hold the clock in a thread for a whole shot run (`NetworkOverrideClockTime` every frame): one call per shot drifted to night
  within a few shots (a time-sync resource).
- Probe collision you are about to change BEFORE the build and keep the output: the driveway pillar's rays (`C9Test/tc_pillar.lua`-style,
  horizontal rays per height at the old and the new spot) read 'none' at every height on the defect (its collision had been cut
  by the apron outline), so the same probe after the build proves the move.
- Height grids with material per cell (`GetShapeTestResultIncludingMaterial`, rays down every 1 m) show what lies under a piece you
  remove: the car-park pit under the San Andreas branch (z 15.9) only showed this way.
- **Sills and plinths follow the street, not the floor.** The mall's ground-floor sills were a fixed floor + 1.0 m; the street rises
  1.5 m round the block, so on the high side the sill sat at or under the sidewalk (from inside you looked down past it to the
  paving, the "light strip"; the sill top lay on the lot slab and the cross-drawable check flagged it once the slab was draped).
  Read the street's edge heights (Tower City `plan/lot_edge_dense.json`) and set sill = max(floor + 1.0, street + 0.45), plinth top
  = max(floor + 1.2, street + 0.3), per bay.
- **Close every front's ends.** A storefront row's pier rule skipped the two ENDS of the court's fronts (where they meet the hall's
  glass and the Eatery's front): a 25 cm slit from the floor up, and at the hall a 15 x 40 cm shaft from a shop out to the plaza.
  Found only by the portal-aware pass-1 rays; a jamb now closes each end back to the shop's skin and out to the outer wall.
- **Before / after for a fix that only exists in a build**: shoot "before" on the deployed build first; if a defect needs the old
  state back (a LOD you just replaced), take the new files OUT of the rig copy only, restart, shoot, then redeploy with assemble.sh
  (never move them back by hand). Pair sheets: `tools/towercity/pair_sheet.py <before_dir> <after_dir> <out.jpg> names...` (fails on
  a missing frame). Identify an unknown thing in a shot by casting a ray through its pixel from the scripted camera (camera
  basis from position + target + fov) and reading the hit point - `GetEntityModel` on a map building handle throws.
- A Sollumz RE-import of built drawables trips on the embedded sign textures' mip chains ("Mip 7 has invalid layer size") - checks
  must read the build's own exports (`tris_*.npy`), not re-import the ydr (Tower City's old `zfight_check.py`).
