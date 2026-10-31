# Field notes

Lessons kept as working notes during the builds (Cloud 9, Tower City, the junkyard garage), one per section. The docs 01-08 hold the worked-out rules; these are the short originals.

## mlo-archetype-bounds

Geometry added to an existing drawable (extending a floor/landing, raising a shaft) does NOT update the archetype's
bbMin/bbMax/bsRadius in the ytyp. GTA culls the whole drawable by that stale box, so from some camera angles the area
outside the box vanishes and sky (blue/white) shows through. Cost a day of chasing portals/room flags on Cloud 9 (2026-10-10).

**Why:** visibility uses the ytyp archetype bounds, not the ydr's own bounds.
**How to apply:** run work/v19_bounds.py (re-derives every custom drawable archetype bbox from geometry) before every
TequiBuild compile of v_int_64.ytyp; for any MLO, recompute archetype bounds after editing a drawable. Also check portals
cover the full opening when an opening is widened, and that rooms use the same room flags as their neighbours.
Related: [[cloud9-mlo-project]], [[feedback-mlo-stairs]]

## gta-hide-vanilla-lods

Proven in game on the Cloud 9 lot (2026-10-11):
- Removing an HD entity from its ymap is not enough: its LOD parent (in the `<parent>` ymap) draws in its place.
- Setting that LOD entity's lodDist to 1 is ALSO wrong: the SLOD above it then draws (blurry billboard).
- Vanilla LOD archetypes live in drawable dictionaries (.ydd), so a same-named .ydr "empty stand-in" is ignored.
- What works: keep the LOD entity, its lodDist and hierarchy; set its archetypeName to our own empty archetype
  (tll22_empty: plain DRAWABLE, 1 cm quad buried 5 m) defined in a resource ytyp + `data_file 'DLC_ITYP_REQUEST'`.
- Edit every same-named ymap variant (base, hei_, apa_; patchday copies are overridden by name).
- Exterior lights inside a drawable do work; the Sollumz template light had light_fade_distance 60, which hid them
  from more than about 60 m away. Set the fade to 150 or more and add a corona for visible heads.
- Cutting decal/ground faces under a new slab: bisect along the footprint edges first, then delete the inside faces.
  Deleting only fully-inside faces leaves pale wedges; deleting whole crossing faces leaves gaps.
Related: [[cloud9-mlo-project]], [[mlo-archetype-bounds]]

## gta-ymap-entity-gotchas

Found on Tower City level 1 (2026-10-19). Two map-entity rules:

**Quaternions by entity type**
- MLO instance (CMloInstanceDef) in a ymap: the real rotation (0,0,sin(h/2),cos(h/2)).
- Plain CEntityDef in a ymap: the conjugate (0,0,-sin(h/2),cos(h/2)).
- Entity inside an MLO: also the conjugate.

**Where exterior archetypes live**
- An exterior entity's archetype must live in its own plain ytyp, loaded with DLC_ITYP_REQUEST.
- If it sits inside the MLO's ytyp (which _manifest.ymf flags INTERIOR_DATA), the ymap entity never draws. There is no error.
- CreateObject of the same model still works, which hides the problem.
- World-space collision (separate ybn) still works too, so raycasts look fine.

**Debug tell:** what you see at the spot is only the interior geometry, drawn through the portal.

Related: [[tower-city-mlo]], [[mlo-archetype-bounds]].

## mlo-copy-rockstar-materials

When a material or effect won't come out right in an MLO, look at how Rockstar (or other creators) did it and copy
that, instead of guessing shaders. Antonio asked for exactly this on 2026-10-11 after two failed glass attempts.

**Why:** guessing gave opaque white/green "glass" twice; reading apa_mp_h_01_living_glass2 fixed it first try.
**How to apply:** extract a vanilla model that has the effect (TequiBuild extract), import in Sollumz, dump each
material's shader filename, render bucket and parameters, then reuse them.
- Clear glass: `glass_normal_spec_reflect.sps`, render bucket ALPHA, alpha diffuse (dark tint, alpha ~.05 for clear,
  .16 is milky), flat normal/spec, dark EnvironmentSampler, reflectivePower ~12, falloff 400, fresnel .85.
  `glass.sps` in the opaque bucket renders solid.
- Metal (club handrail ba_trad_rails): normal_spec, specularIntensityMult .7-.9, falloff 30-60, specularFresnel .9;
  its texture is chrome, so for brass use a dark gold diffuse (~.34,.235,.085) with those values.
- Rockstar props reskinned beat hand-modelled furniture for chairs/stools; hand-model only shapes vanilla lacks.
- Colours sampled from reference photos are sRGB and already lit: convert to linear (and darken) before writing
  them into our DDS textures, or they render far too bright (tomato-red booths, 2026-10-11).
- Run work/v26_collision_audit.py after layout changes: stale 'Fitted furniture collision' meshes and leftover
  vanilla boxes caused invisible blockers and walk-through walls.
Related: [[cloud9-mlo-project]], [[gta-hide-vanilla-lods]]

## mlo-mirrors-separate

A working MLO mirror = its own entity (Tower City: tc_prop_mirror, mirror_default.sps) + a mirror portal (flags 260) on its plane.
Built into the room drawable it reflects nothing - the reflection skips the entity holding the surface. The phInstGta crash fix
(2026-10-23) merges COLLISION per room only; never merge mirrors or props into a room model to save entities.

**Why:** Antonio, 2026-10-23: "that didn't merge the mirrors back into the building, did it? ... that was the reason mirrors didn't
work ... make sure you write that lesson down."

**How to apply:** any merge / optimisation pass touches bounds only; after it, stand at one mirror in game and check the reflection.
Playbook doc 02 (Mirrors + collision merge). Related: [[reference-mlo-playbook]], [[tower-city-mlo]].

## fivem-scenario-override-crash

Cloud 9 MLO, 2026-10-11. Goal: no ambient peds in the club (except bartender), no cars parking on the rebuilt lot.

- CRASHED (GTA5_b3258.exe+C5E707, 11 s after the manifest loaded): eclipse.ymt re-saved through CodeWalker's
  scenario model after deleting points (TequiBuild scnedit).
- WORKS: TequiBuild `scnpatch` - byte-patch Rockstar's own eclipse.ymt in place (per listed point: uAvailableInMpSp=1,
  NoSpawn flag, z -150 m; xy untouched so the 2D accel grid and all indices stay valid), re-wrap with the original
  resource header. Loaded with stream/eclipse.ymt + sp_manifest.ymt (PSO, region renamed compcache:/cloud9_lot/eclipse)
  + `data_file 'SCENARIO_POINTS_OVERRIDE_PSO_FILE' 'sp_manifest.ymt'`. Flags alone did NOT stop a parked car; the z
  sink did. Proof it is live: DoesScenarioExistInArea false at patched points, true at the bartender (/peds census).
- Streaming eclipse.ymt without the manifest has no effect.

**Why:** the first attempt mixed doc + forum methods and shipped untested; the client log showed which stage died.
**How to apply:** read the CitizenFX log before guessing; edit vanilla meta in place when only fields change. Caveat for
servers: only ONE resource can override sp_manifest, and the manifest is tied to the game build it was taken from (3258).
Related: [[cloud9-mlo-project]], [[gta-hide-vanilla-lods]]

## fivem-two-clients-one-pc

Worked 2026-10-11 on the MLO Workshop test server ([[cloud9-mlo-project]]):
- server.cfg `sv_lan 1` (else the duplicate account is dropped). In LAN mode players.json shows NO identifiers for
  either player, so licence-based frameworks (Qbox) cannot tell them apart - unsolved.
- Client 1: normal Connect-Localhost.ps1. Client 2: shortcut `FiveM.exe -cl2 +connect 127.0.0.1:30120` opened via
  explorer.exe (shortcut saved as server\Connect Localhost cl2.lnk). Second process is FiveM_cl2_b3258_GTAProcess.
- Traps: `-cl2 fivem://connect/...` fails ("should be launched directly from the shell", no master process) and took
  client 1 down; first -cl2 run pops a "select GTA5.exe" dialog (own setting PathCL2 in CitizenFX.ini, now saved).
- Antonio watches the screen: long silent waits look like a hang and he interrupts. Launch with a quick command, then
  watch with a background loop and say what is happening.

## feedback-mlo-stairs

Stairs in any MLO must match Rockstar's own stairs exactly.

**Rockstar's numbers** (measured 2026-10-19 from v_64_back_stairs + its collision in v_rockclub.ybn):
- Every riser 0.20 m, every going 0.27 m.
- The visible treads have NO collision.
- Collision is ONE smooth ramp along the nosing line (slope 0.20/0.27).
- The ramp starts one going in front of the bottom riser, at the lower floor.
- It meets the upper floor exactly at the top riser.
- N risers = N-1 treads; the ramp is N goings long.

**Why:**
- Antonio walked them and said they felt off and must match regular GTA stairs exactly.
- Mine had two faults:
  - The ramp was squeezed over N-1 goings, which made it steeper than the steps.
  - One flight had 0.196 m risers, because its floor-to-floor wasn't a multiple of 0.20.
- Stepped box collision makes peds hop.

**How to apply:**
- Always build stairs with `tc_kit.stair()` / `stair_plan()` (Tower City workspace, work/tc_kit.py). Antonio asked for a reusable stair tool like the door tool.
- `stair_plan()` refuses a floor-to-floor that isn't a multiple of 0.20. Fix the levels, never the risers. Example: Tower City P2 moved to 18.4.
- Lay out the shaft from the tool's result (`top` / `foot` / `run`) before modelling walls.
- Verify in game with a walk that logs vertical jerk and ragdoll/climb/jump states, in both directions. On 2026-10-19 all flights showed jerk ≤0.06 m per 50 ms and none of those states.

Related: [[feedback-mlo-seating]], [[cloud9-mlo-project]], [[tower-city-mlo]].

## feedback-mlo-seating

Antonio actually uses the seating (peds and his player sit), so every chair/sofa in any MLO must be built and verified for sitting — apply to all future rooms, not just the hideout.

- Heights: sofa 0.42–0.45 m, chair 0.45–0.50 m, desk 0.74–0.80 m. Seat + back collision boxes, 0.3 m clear around.
- Sit point ≈0.20–0.25 m in front of the backrest, z = seat surface (cushion centre perches peds on the edge, feet into tables).
- 0.38–0.45 m seat-front to coffee table is fine once the point is right. Little clipping is OK, a lot is not.
- Working scenarios on custom props: PROP_HUMAN_SEAT_ARMCHAIR, PROP_HUMAN_SEAT_CHAIR. COMPUTER/BENCH/CHAIR_UPRIGHT/MP_PLAYER don't play without Rockstar props.
- Verify with tll_capture `/sit/...` photos and hand over world sit coordinates. Full notes in the workspace MLO-Building-Guide.md ([[cloud9-mlo-project]]).

**Why:** he plans to use the chairs and couches in RP; looks alone aren't acceptance.
**How to apply:** for every new seat, design to these numbers, then sit-test in game before showing comparisons.

## feedback-mlo-native-doors

Doors in MLOs must be real game doors with real collision that moves with them: no scripts, no spawned panels,
no push-back hacks. Antonio's servers use their own lock systems (Qbox / ox_doorlock style), which register doors by
model + coords through the game door system; a scripted door breaks that.

**Why:** said explicitly 2026-10-10 after I built a script-slid panel ("Do not use any script at all").
**How to apply:** door = custom ydr (skeleton + embedded bound composite, origin per type: hinge for swing, bottom corner
for sliding) placed as an MLO entity; archetype flags Dynamic (1<<17) + Enable Door Physics (1<<26) = 67239936 and
specialAttribute 7 normal / 8 sliding / 5 garage (FiveM docs part-8; template prop_facgate_07b for sliding).
CRITICAL: set the archetype's physicsDictionary to the model's own name (e.g. tll19_secret_door) - with it empty the
embedded bound never loads: no collision, door system ignores ratios, peds walk through (proven in game 2026-10-10).
Same for any custom prop meant to use embedded collision. Archetype flags as Rockstar doors: 604110848.
Sliding doors travel toward model +X (origin side): put the origin at the corner the door slides toward.
Do not ship doortuning.ymt (needs replace_level_meta gta5 - conflicts with other resources); default tuning applies.
Hollow static collision where a sliding door's pocket is. Auto-open on approach is expected unless a lock system locks it.
Related: [[cloud9-mlo-project]], [[mlo-archetype-bounds]]

## feedback-mlo-data-file

Every MLO I build must include `mlo-data/<name>-coords.json` + README inside the resource (listed in fxmanifest `files`), regenerated whenever furniture moves. Must contain the exact street entrance door (model, position, heading, stand-outside/inside points; verify by photographing from the street), interior doors, floor heights, zones, every tested sit point (z = seat surface, heading, working scenario), and interaction points (racks, terminals, laptops). Use `GetInteriorAtCoords`, never a hard-coded interior id.

**Why:** Antonio builds seed/sit scripts with other AI tools and has always hated that MLOs don't publish their entrance coordinates.
**How to apply:** add new seats/interactions to the generator as each room is built ([[cloud9-mlo-project]], [[feedback-mlo-seating]]). Cloud 9 generator: work/v14_mlo_data.py.

## feedback-real-props-not-kit

Antonio (2026-10-22, Tower City crown floors): "you were supposed to look at how the other ones are built and use a lot of
that accessories and money and miscellaneous things ... there's no personality. It feels AI generated. Even your tables
don't make sense ... a solid block. You should be utilizing real props from GTA 5."

**Why:** box-built furniture (slab beds, block tables with no legroom, bare "sofa" slabs) reads as placeholder; the
vanilla interiors (Diamond penthouse, Agency office, casino, high-life apartments) get their character from dense,
specific props: cash piles, bottles, bags, art, magazines, remotes, food.

**How to apply:** every room of every MLO: furniture = real props (apa_mp_h_* / ex_mp_h_* apartment & executive sets,
v_corp_* / v_res_* / v_club_*, ch_prop_ch_* casino, sf_prop_sf_* agency, prop_* vanilla), plus cash (ex_cash_pile_*,
bkr_prop_bkr_cashpile_*, bkr_prop_moneypack_*), bar stock (spiritsrow / winerow / prop_glass_stack_*), and clutter.
Kit geometry only for things with no vanilla prop (pools, showers, signs, pendants). Catalogue of 8 299 props with sizes:
`TowerCity/survey/prop_catalogue.json` (built by survey/prop_catalogue.ps1); chosen props must be surveyed into
arch_ytyp.json via find_arch_ytyp.ps1 before a build. Prop convention: front = -y; heading 0/90/180/270 puts the back
against the N/W/S/E wall. Check footprints against room rects, doorways and each other before building. Related:
[[tower-city-mlo]], [[feedback-no-patchwork]], [[feedback-mlo-seating]].

## feedback-self-qa-gaps-seams

Before any MLO / building change goes to Antonio, I hunt the defects he keeps finding, instead of waiting for him to point them out:
- light gaps: corners, wall junctions, where walls were cut/extended (run wow2easy_move/tools/gap_check.sh - rays from inside every
  room, one-sided faces like the game; plus a point-by-point scan of every outer wall);
- seams where old meets new: ceiling/floor joins over removed walls, strips that a cut took out of a floor;
- material/colour mismatches where my added surface meets the original (same texture at a different UV scale/vertex colour);
- things exposed by moves (ground under a moved prop, a sign cut by a new window, furniture blocking a door);
- leftover / dangling pieces (wires ending in air, poles with nothing on them, transformer poles that fed a removed building,
  short re-hung spans sagging to the ground, lamps/LOD lights glowing over removed buildings at night);
- ground: leftover slabs/gravel/concrete under porches and at thresholds, AND their collision (drawable faces removed != collision);
- openings: every gate/door walked both ways with no lock scripts (doors seated on high ground, header above the door top);
- the client's world stays as it is - never clear his yard/props to make my thing fit; move my thing.
Tools: wow2easy_move/tools/gap_check.sh (light gaps), site_audit.sh (openings / ground material / sag), wires.py WIRES_SAG.

**Why:** 2026-10-23, round 6 of the junkyard garage: "I'm checking corners and looking for gaps in walls and gaps in seams where
we've added things ... wire that into our checks ... learn from what I'm telling you so I don't have to give as many prompts."
He also wants each of his points played back in my own words first ("explanations of what I'm telling you, so I can confirm").

**How to apply:** after each build: gap check + an in-game seam walk (corner shots at night, floor/ceiling at every edit line),
fix what turns up, THEN send shots. Play back his list before building; ask only where it is genuinely his call. Related:
[[feedback-room-by-room-signoff]], [[feedback-no-patchwork]], [[reference-mlo-playbook]].

Also (2026-10-23): ship every map with NO locks - doors and gates are plain native doors that push / slide open; the buyer runs
their own lock system. Never register doors with a lock script or write lock config for a delivery.

## feedback-probes-prove-they-ran

Never report "0 problems" from a probe unless it demonstrably ran: every rig call that gets no answer must raise, and every new
check is first run on a defect known to exist (it must flag it) before its clean results mean anything. On this PC, Python's
subprocess `bash` is WSL's (no distro) - use `C:\Program Files\Git\bin\bash.exe`.

**Why:** 2026-10-23 the visible-surface probe reported 0 issues for Tower City and the Graveyard garage, but every call had
silently failed; Antonio knew of a fall-through hole at the garage's north porch door and caught it.

**How to apply:** fail loudly, test the test on a known defect, then run it. Related: [[feedback-self-qa-gaps-seams]],
[[reference-mlo-playbook]].

## feedback-reference-side-by-side

When building anything to match Antonio's reference photos, every stage ends with side-by-side images (our render from the same angle and scale as each matching photo), a self-listed set of differences, fixes, and only then the next stage; the side-by-sides are sent to him.

**Why:** 2026-10-15, Cloud Nine Cruiser van: the background builder reached stage 3 fast, but the high top was too tall and boxy, windows too low, rear overhang about 0.25 m too long. Its checks only tested my spec estimates (2.54 m height), not his photos. He asked: "why didn't we pass on instructions for the builder to do side-by-side comparison of my image as he builds?" Same expectation as the MLO work ([[feedback-room-by-room-signoff]]).

Side-by-sides alone weren't enough: by 03j he was still saying "not right" on the rear and side. From then on, the builder lines up a camera to each photo in Blender and checks with an overlay (the photo at 50% over the render, plus an edge difference). Every outline has to sit on the photo's outline.

**How to apply:** put the side-by-side rule in every builder / subagent brief and plan from the start; photo measurements win over spec numbers; when reviewing renders myself, compare against the photo views (side, rear, front 3/4, interior) before forwarding. Related: [[cloud9-mlo-project]].

## feedback-room-by-room-signoff

Standing order for the Cloud 9 MLO ([[cloud9-mlo-project]]): finish the current area all the way through (no half-done hand-backs), then deliver in-game vs design-photo side-by-sides and stop. Only start the next area after Antonio explicitly says it's good / moves me on. Order agreed 2026-10-10: hacker lounge (Photo 3) → Cloud 9 signage → main lounge (Photo 1) → office (Photo 2).

**Why:** he wants to judge each room himself against his reference photos and expects them copied exactly, not approximated.
**How to apply:** within an area, push through every gap autonomously ([[feedback-fewer-questions]]); at the end, send comparisons + a short list of what still differs, then wait.

## feedback-videos-not-pictures

Antonio (2026-10-22): "when everything is done, I prefer a fly-through video and maybe a quick little video of you swimming in
the water. I don't want pictures."

**Why:** he reviews by walking through the space himself; stills hide how rooms connect and how things behave.

**How to apply:** screenshots are fine for my own checking (and for option comparisons he explicitly asks to see), but the final
hand-off of a build is a fly-through video of every changed room, plus short clips of interactions (swimming, doors, lifts),
compressed under 30 MB for his phone. Related: [[feedback-test-on-screen]], [[reference-mlo-playbook]].

## feedback-cinematic-flythrough

Hand-off fly-throughs must be smooth and cinematic, paced by section: the yard/wall perimeter FAST, gates and garage doors SLOW
so they can be watched opening, the building's perimeter MODERATE, interiors steady. He likes the camera turns ("camera flips")
- keep sweeping/orbiting moves, eased in and out, no jerky corners.

**Why:** 2026-10-23, round 6: "the video wasn't very smooth ... perimeter of the gate can be kind of fast ... watching the gate
open and the garage door open can be slow ... building moderate ... I do like your camera flips ... make it cinematic."

**How to apply:** per-segment speeds with eased (smoothstep/spline) camera paths and look-at targets, the doors/gates actually
opening on camera (walk a ped through, no lock scripts), never a camera through a closed door or a prop. Related:
[[feedback-videos-not-pictures]].

## feedback-no-patchwork

Never patchwork. If a part has to be redone (a light, a mesh, a function, a page), remove everything built for it and rebuild it clean from its source; no fixes layered on top, no filler pieces covering mistakes. Only patch when Antonio explicitly says so. Pass this rule to every subagent/builder.

**Why:** 2026-10-15, Cloud Nine Cruiser van: repeated patch passes on the rear (lamps, corner filler, cap) left doubled tail lamps sticking out of the body, dark triangles and leftover geometry. He said: "Nothing should ever be patchwork, ever. That's in any project we do moving forward. Commit that to Claude MD or wherever, everywhere."

**How to apply:** written into ~/.claude/CLAUDE.md and C:\Users\anton\CLAUDE.md as well; include it in every builder brief and plan; when a fix touches previous work, delete that work first, then rebuild. Related: [[feedback-reference-side-by-side]].

## envi-restaurants-findings

On Oct 19 2026, envi-restaurants was scanned on the C9Test rig with the local tool c9_animscan, plus a check of envi's open files.

**Grill (verified in game, two passes, client 2 watching):**
- No animation and no hand prop.
- It is menu-driven under a top-down scripted camera, and the cook is hidden locally.
- Flow: Use Grill → Slot N → category → recipe → "click to remove".
- The patty prop swaps model in place at 0/12/30/48/60 s of a 60 s cook: raw → rare → cooked → overcooked → burnt.
- Quality goes into the item metadata. Each cook adds station dirt.

**Other stations (from envi's README / open config, NOT scanned in game):**
- Cutting board: knife in the left hand, ingredient in the right, progress bar, chopped pieces appear.
- Microwave: guess the time, rotating plate.
- Oven: tray props.
- Sink: hand washing with mp_arresting a_uncuff.
- Cleaning anims: timetable@floyd@clean_kitchen, lamar tagging spray, coc_packing.
- Eating and drinking anims come from the config.

**Custom animation files:** the only one is envi-cooking-props/stream/model@water.ycd.

**Why:** Antonio asked whether C9 DJ is "ahead of the curve". It is on animation: 1.8.0 Mech.STEPS gives every step a GTA animation and a tool. He stopped in-game testing here and wants C9 DJ's station UX made as simple and nice as envi's menus.

**How to apply:**
- Don't chase envi "flip animations": they don't exist.
- Copy envi's simplicity (slot menu, category → recipe, visible stage props, click to take off) and keep our animations.
- Test restaurant `envitest` (job pizzathis) is on the rig at the Legion Square plaza; see C:\C9Test\plan\venues-restore.txt.

Related: [[c9-local-test-rig]], [[venues-160-test-progress]].

**Rebuild status (2026-10-19):**
- Design: `scripts/c9_dj/docs/STATION-MENUS.md`. Takeover brief: `STATION-MENUS-HANDOFF.md`. Both are on cloud9 branch `claude/c9dj-station-menus` (7f52b756); the worktree is C:\C9Test\cloud9-menus.
- The design is NOT yet approved by Antonio, and no code has changed.
- Push it through C:\C9Test\cloud9-notes (the test copy's push URL is disabled).

## exterior-vertex-colours (Justice Center phase 2, 2026-10-28)

Exterior vertex colours must copy Rockstar's, never 1.0. In his exterior models colour 0 is R = natural ambient, **G = artificial
ambient** (night light "from inside"), B = a third term. Measured (Sollumz import, `color_srgb`, model means): sc1_19_courts
0.467 / 0.054 / 0.222, sc1_19_sheriff 0.581 / 0.132 / 0.368, hw1_26_build01 0.484 / 0.015 / 0.485 - G is about 0.05 on walls.
With 1.0 (tc_kit's exterior default) every wall glowed evenly at 23:00 while the vanilla neighbours went dark.

**How to apply:** write his values (or his model's per-vertex colours) with `color_srgb` on every exterior and LOD model; only
night-light (emissive) models keep 1.0. Check at 23:00 next to vanilla buildings. Details: docs/13 "Night: vertex colours".

## interior-rooms-area-2 (Justice Center phase 3 courts tower, 2026-10-29)

- **Door leaf heading:** `v_ilev_ph_gendoor005` / `v_ilev_ph_cellgate` leaves run along the model's **-x** from the hinge (glass
  `v_ilev_ph_door01` along +x). Put the hinge at the opening's far end and point the heading's +x along the wall, so the leaf lies back
  across the opening. The first build had every leaf turned 180 degrees, into the wall beside its opening: all doors-both-ways walks
  failed. Now a unit test checks it: each leaf's far end (hinge + 1.30 m) must lie inside its opening.
- **Walking lanes through doors:** a 0.7 m lane through the middle of each leaf, 1.5 m either side, must miss every fitting (pew
  ends, bars, benches). A 4-seat pew block had its end 0.13 m from a door leaf's lane and the walker stuck on it. This is a plan-time
  test now: prove it on the old pew end, then pass.
- **Door probe geometry:** the probe's start and end points must be inside the rooms. The corridor beside the holding cells is 1.3 m,
  so a 1.5 m stand point was inside the wall and the walker never moved ("past_line -1.87"). Use a depth that fits the narrower side.
  The pass mark is depth minus the arrival radius (0.6 m), not a fixed 1.0.
- **Preview renders of windowless rooms:** a scene saved by the build has no Blender lights (game lights are not Blender lights), so
  inner rooms render black apart from the emissive lamp panels. The renderer adds area lights on a 4 m grid under each room region's
  ceiling (from the layout's zones). This is preview only; nothing changes in the build.
- **Saved-scene renders:** Sollumz could not re-import the built ydr (sign texture mips). The build now saves its own scene
  (`out/jc3_scene.blend`) and the renderer opens it. Rebuilding wipes `out/`, so never rebuild while a render is reading it.
- **Room walls = linings by region:** each room's lining comes from its own region: 0.1 against another room (back-to-back 0.2
  partitions), 0.2 on outer walls, thicker in the lobby. The footprint gate insets each region only on its boundary sides, per level.
- **Archetype names lower case (BIG):** the meta compiler hashes archetype and asset names exactly as written. The game hashes the
  .ydr file name lower case. Rooms named `jc_courts_crtA` never matched `jc_courts_crta.ydr`: every L3 / L5 room was unregistered
  (`IsModelInCdimage` false) and drew as a white void showing the outside world, while all offline gates passed. Collision, the
  room probe, door walks and sit tests all passed too, because they do not need the drawable. Rules:
  - Lower-case every drawable / archetype name at the source; jc3_meta now asserts it (proven on a planted name).
  - The rig `models` probe stands in the MLO (its ytyp loads only near it) and requires `IsModelInCdimage` for every room drawable,
    with a planted unstreamed name that must read false.
  - Look at the rooms in game (first-person shots per room) before trusting walk and sit passes.
- **Assemble must ship every room:** an assemble line written for the first room (`cp ... jc_courts_galleria.ydr`) silently left the
  later rooms out. The stream gate now checks that every room drawable the ytyp places is in `stream/` (with a plant). A gate inside
  `a && b` under `set -e` does NOT stop the script: use `gate || { echo ...; exit 1; }`.
- **Elevator leaf `v_ilev_finelevdoor01`:** the leaf runs +x from its origin (bounds x -0.15 .. 1.45) and opens by sliding along its
  -x. Put the origin at the opening's edge with the leaf lying across the opening (tc_kit.lift_bank: left car c + 0.65 heading 180,
  right car c - 0.65 heading 0). Turned the other way, the leaf rests in the wall and slides ACROSS the doorway as a ped walks up,
  so the lift can never be entered. The on-screen lift probe (`jc3_probe.py lifts`) caught it: walk in through the landing door,
  press E as a real key into the game window (`C9Test/key.ps1 -Vk 69 -Scan 18`), click the floor row in ox_lib (`oxclick.sh`),
  check the arrival floor. Control: E pressed outside a cab must open no menu.
- **Lift landings:** size the landing in front of every lift door first (>= 1.5 m deep, door wide) and check it in a unit test. The
  holding cells' wall once stood 0.3 m off the secure lift door, and no geometry gate noticed.
- **Fly-through look-ahead:** a camera that looks 6 m ahead along its path tips down onto the end point as it arrives. jc3_fly.sh now
  extrapolates the look target along the last leg. A still scripted camera inside an MLO shows the outside world for about 5 s before
  the interior takes it: trim the head of the first segment (jc3_fly_area2.sh). End each segment clear of walls and furniture.

## jail-area-4 (Justice Center phase 3, Jail I, MLO jc_jail, 2026-10-29)

- **Mission Row's block wall, measured** (`v_20_policedlc_shell`, shader xj_v_breeze03): the texture tiles every **4.05 m** and its
  dark wainscot band (bottom ~31 % of the texture) sits at the floor: DX v = -0.2471 z + c, i.e. Blender v = 0.2471 (z - floor) + 0.032.
  Anchor each wall face's v to its own floor. A wall taller than ~4 m bands TWICE (the second band ~4 m up reads as a stripe): use
  his concrete (xj_v_conc_wall) for the 6 m sally port and the stair shafts, and split a two-tier cell block's linings per tier so each
  tier gets its own wainscot. Other MR scales: speckled floor 1.71 m per UV, ceiling tile 0.85 m, concrete ~3.3 m. Colour0 medians:
  walls (0, 0.60, 0), floors (0, 0.65, 0), ceilings (0, 0.68, 0). Measure with a 20-line parser over the shell's CodeWalker XML.
- **A window between two rooms of one MLO: each room draws only its own half of the frame.** The vision windows in the holding cells'
  wall had the whole steel frame in the cell room; from booking, the frame's faces in FRONT of the portal plane belong to the other
  room's drawable and are not this room's to draw - the portal-aware gap check reported 81 rays through the frame edges. Split frame
  boxes at the portal plane (booking half / cell half); the one glass pane can sit on the plane.
- **Interior ground check (drawn vs walked), rules that made it trustworthy:** cast from just under the room's ceiling (a ray started
  at floor + 2 m began UNDER a glass screen's collision top and under stair ramps: false mismatches); skip grid points inside a solid
  (wall boxes); a drawn top more than 2.2 m over the collision is a fitting you walk under; stairs may differ by one riser. Plant: a
  1 x 1 m patch of floor collision removed must be found.
- **Wall lights in a stairwell go over the landings (landing + 2.4 m), never over a flight:** a wall lamp at a fixed height over a
  descending flight was 1.8 m above its treads (found by the ground check as a drawn face 1.8-2.0 m over the ramp).
- **Sally port drive gate:** a pure plan test (door width / height, ceiling, the tail clear of the doorway so the roll-up closes,
  platform / ramp outside the car's swept footprint, proven on a planted 4.6 m truck) + a built-geometry test: each vehicle's swept
  AABB (+0.3 m each side, floor + 0.15 to roof + 0.2, street to its stop) against every built triangle - ours drawn + collision and the
  exterior's - with a separating-axis triangle / box test (a vertex-in-box test misses big wall triangles). Plant: a pillar in the bay.
- **A secure route across a public galleria:** any ground-level walled corridor between two buildings that sit either side of an
  L-shaped hall cuts the hall in two unless it hugs the hall's outer band. Antonio chose a tunnel (B1, 6 m under L1 = the same 30-riser
  stair as L1 -> L2, top 2 m under every slab / hull bottom). Before digging under a cleared lot, scan the game for collision VERTICES
  and entities inside the tunnel's world box (`tools/justice/p4/below_scan.ps1`), then prove it with rays on the rig.
- **A lift stop in another MLO: no MLO-to-MLO doorway.** The courts tower's secure lift (jc_courts) gets a B1 stop drawn by jc_jail at
  exactly the same cab position (cab, front wall, `v_ilev_finelevdoor01` at c + 0.65, heading 180, as tc_kit.lift_bank's left car);
  the lift script fades between identical cabs, so the hand-over between the two interiors is the fade.
- **Build into a staging folder and swap**: another agent's assemble copies our out/ at any time. Build to out_next, run every gate there,
  then mv. A hold flag must have CONTENT: the build's own "delete 0-byte files" sweep (the hook-junk rule) deleted an empty flag file and
  the swap went ahead.
- **Filming aid for fly-throughs through native doors:** add the doors to the client's DoorSystem under hashes of your own, open by
  ratio, hold open; remove them afterwards (`jj_doorctl.py open|close`) - never shipped, never a lock.
- **Prove the rig runs the newest build before any test (Antonio, 2026-10-29).** He saw no steel tables in game: the rig still ran an
  older jc_jail while the newest sat in work/jail/out (another agent owns assemble / deploy). `jj_deploy_check.py` hashes every
  jc_jail_* / jc_jail.* file in the LIVE resource's stream against the build's output (missing, stale, extra), proven on a planted stale
  file; then a 13:00 shot of a room the change shows in (the dayroom's tables). Run it at the start of every rig session; a mismatch
  means no test. Name filters matter: `jc_jail*` also matched phase 2's `jc_jail1` / `jc_jail2` shells.
- **Deploy check (Antonio 2026-10-29: the rig ran an old Jail I build):** after every deploy, each MLO's live stream files must
  hash-match its build outputs (`tools/justice/deploy_check.py <live dir> courts jail`, proven first on a planted one-byte change).
  It is fatal at the end of assemble's deploy. When one MLO's owner needs its newest build live while another MLO is mid-build, use a
  single-MLO redeploy into the last gated deploy (`tools/justice/deploy_mlo.sh jail`): swap only that MLO's files, re-merge the one
  `_manifest.ymf`, run its stream gate and the deploy check. Never assemble half-built outputs to get one MLO out.
- **Windows Python + bash paths:** pass `cygpath -w` paths to py -3. A `/c/...` path is read as `C:\c\...`, and a check that cannot
  find its files must fail, never pass.
- **A roll-up in an outer-wall opening as a plain map entity needs Rockstar's MAP DOOR flags (1572864)**, not the plain entity default
  (32) a generic ymap writer puts on everything: with 32 the jail's sally-port roll-up stood as a wall and three test cars stopped
  nose-on against it (the drive test's collision log + video). Tower City's parking roll-ups were written with 1572864 explicitly.
- **Driving a test vehicle on a server with a keys resource:** keyless cars won't start (c9_vehiclekeys holds the engine off): spawn it
  with the engine on, give the player the key on the server (`exports.c9_vehiclekeys:GiveKeysByPlate(src, plate, true)`), then drive
  with short `TaskVehicleTempAction` pulses (23 gas, 22 reverse, 1 brake) along a straight line. `TaskVehicleDriveToCoord` re-routes
  over the street's road nodes and left the bay; `SetControlNormal` did nothing in the harness thread.
- **Rig tests are run by main, not by agents (Antonio, 2026-10-29).** An agent hands over one unattended runner per area
  (`tools/justice/p4/jj_rig_tests.sh <test>`: deploy check first, each test ends with one `JJ_TEST <name> PASS|FAIL` line).

## tower-city-night-glow (Tower City, 2026-10-29)

The Justice Center's 23:00 glow (exterior-vertex-colours above) was in Tower City too, because both come from the same kit. At 23:00
the tower and mall walls were evenly lit pink. From 1 km the tower was a solid orange block over a dark city. Offline it was the
same: every non-emissive face of tc_tower_ext / tc_mall_ext / tc_garage_ext / tc_ug_ext was Colour0 255/255/255. Interiors were
0/124/0 (the workshop kit's `(0, .2, 0)` through `.color`), emissive faces too.

**Measure the neighbours, not a far model.** The downtown blocks round the site (dt1_05_build1_h, dt1_06_build1_1 / build2_1,
dt1_07_building2, dt1_09_building_01, dt1_10_build1: 134k vertices) give Colour0 by surface: up 174/7/0, wall 132/30/0,
down (soffits) 84/12/0. G stays under about 45 on walls. B is 0 on two thirds of them.

**The fix lives in the kit, not on top of it.** tc_kit.export_all now writes `VCOL_EXT` per face normal (up / wall / down) on every
exterior model. `init(vcol={room: 'glazed' | 'enclosed'})` writes `VCOL_INT` per room: glazed 153/107/255 floor, 115/115/255
wall, 102/115/255 ceiling; enclosed 0/158/0, 0/153/0, 0/163/0. Every room must be classed or init asserts. Emissive-shader faces
get 1.0. All of it is written with `color_srgb`. Builds that pass no `vcol` (Justice Center p3, which writes its own colours in a
`new_drawable` wrapper) keep their interiors as they were. JC p2 overwrites the exterior colours in its own POST_EXT pass.

**Gate on the built files:** `tools/towercity/vcol_check.py` turns the stream into CodeWalker XML (`ydr_xml_dir.ps1`; shader names
come back as joaat hashes: emissive.sps = hash_9D183303, emissivenight.sps = hash_557DB6E4). It fails on:
- any non-emissive vertex with G >= 250;
- an interior colour that is not a VCOL_INT class;
- an emissive vertex below 255.
It runs in build_east / build_west / build_l0 after ground_check, before deploy. It was proven three ways: on the old build
(fail: 4 exteriors + every room), on one planted 255 vertex in the new tc_tower_ext (fail: 1 vertex), and on the clean build
(pass, 786,831 vertices). A half rebuild (west only) fails it on the east lot's old files, as it should.

**The rebuild changes colours only:** 81 of 84 drawables have identical positions / normals / UVs / indices, and the other 3 have the same
vertices to 1 cm. Our ytyps and ymaps are byte-identical, so the archetype bounds are unchanged.

**Rig shots (C9Test):** `tc_glow_shots.sh <tag> <hour> [ext|far|int]` takes the 6 standard exterior views, 500 m / 1 km / 500 m north,
and the mall court / tower lobby / casino, with the clock held. `tc_glow_flyby.sh <out.mp4> [hour] [secs]` is an eased
(smoothstep) night orbit round both lots.
- **Fly-through paths are checked offline before anyone records them** (`tools/justice/p4/jj_flycheck.py`): sample the camera's own
  Catmull-Rom spline every 0.2 m and measure to every built triangle - >= 0.9 m from any face, 0.45 m only within 1.2 m of a doorway;
  no hold > 3 s. The first jail paths hugged block walls for 25 s and came within 2 cm of a counter. Keep the camera >= 1.5 m above
  stair treads (perpendicular distance on a 36 deg flight is only 0.8 x the vertical), add a waypoint at the top of each flight, and give
  doorway legs two aligned points either side (the spline overshoots into the jamb otherwise). Record exactly the path's time
  (sum of len / speed): a padded duration left a 25 s static ending.
- **Recordings stopped from Git bash must flush continuously:** ffmpeg cannot be told to quit (its stdin is not a console); a hard-killed
  x264 / matroska recording "ended prematurely" or wrote nothing. Use `-tune zerolatency -flush_packets 1 -movflags
  +frag_keyframe+empty_moov` with a keyframe a second, remux to a plain mp4 and check its duration with ffprobe (proven on a testsrc
  recording killed at 6 s: 6.0 s valid).
- **Walk probe time limits scale with the leg** (6 s + 1.5 x length / 1.1 m/s): a flat 20 s failed a 36 m tunnel leg the walker was still
  walking. Prove the walk check on a planted leg into a wall (it must not arrive).
- **Sit-sheet cameras are picked, not fixed:** "2 m in front of the sitter" put the camera inside a counter, and for a chair facing a
  wall outside the building. Try spots round the sitter and take the first that is in the seat's room, outside every fitting, >= 0.9 m
  from other sitters and with a line of sight over the fittings (a booth's chairs: from behind, through its glass).
- **Filming door opener: close in a trap** - a fly that failed before its close left the roll-up open in the next pair shots; the close
  drives every door shut, reads each ratio back and only then removes them; the pair shots run it first.
- **DoorSystemGetOpenRatio reports the system's target, not the leaf:** after a "close", 50 of 51 doors read 1.0. Check doors
  PHYSICALLY: the door object at its spot, heading within 3 deg and position within 0.15 m of its placement. Reset = drive shut (ratio 0,
  locked), take every door out of the door system (the map default applies), then the physical check.
- **A walk-check plant must be unreachable by ANY path:** a leg into the property room's wall "arrived" - its door was standing open (the
  filming door opener had failed to close). Plant a target inside the building's solid hull, and count "arrived" only with the root ~1 m
  over the target floor (never on another level).
- Lua sent to the rig is compiled offline first (`jj_luacheck.py`, lupa's Lua runtime, proven on a planted syntax error).
- Compiling is not enough: EXECUTE it offline (`tools/justice/p4/jj_luasim.py`). 2026-10-30 a drive self-test died on the rig in
  `ValueError: could not convert string to float: '%.2f'` - a Python string holding `"%%.2f"` was never %-formatted, so Lua got a literal
  `%%` and returned the template. A dry run with stubbed results could not see it. The fix: run every chunk in lupa against a small mock
  of the natives (vectors with arithmetic, a game timer that advances, entities that remember position AND heading - without heading the
  mock spawn "failed" and the buggy chunk was never reached, a false pass), drive the real probe functions with `lua` routed there, and
  flag any result that still holds `%d/%f/%s`. Plus a static AST check: `%%` in a string literal that is not the left side of a `%`.
  Both proven on plants, and the unfixed probe must FAIL the sim before the fix counts.
- Test cars on a server with a keys script that blocks auto-start (c9_vehiclekeys `disableAutoStart`): a raw `SetVehicleEngineOn`
  reads "running" but the script switches it off every frame while a player is in the driver's seat, so gas moves the car 0.14 m (rig
  2026-10-30). Start the engine through the script (`exports.c9_vehiclekeys:ToggleEngine()` after its `CanDrive` is true) and check
  the engine still runs 1.5 s later and fuel > 0 (ox_fuel state bag) before calling the drive a test. The offline sim mocks that guard,
  and the pre-fix probe fails there at 0.0 m, as on the rig. Also: the sim must keep ONE Lua state across a probe's chunks (globals and
  cars persist on the rig); a fresh state per chunk hid the car between chunks.
- Seating the test driver is a step with its own checks, not one warp: stand the ped out of any vehicle and not ragdolled first, wait
  until the new car is networked and owned (request control), then warp with retries (3 warps, then SetPedIntoVehicle) until
  GetPedInVehicleSeat(v,-1) is the player; on failure report the seat occupant, ped state, door lock (rig 2026-10-30: the warp into the
  plant car straight after the self-test did not take). The sim runs the plant in the same Lua state right after the self-test and
  mocks a car that takes a ped only 1.5 s after it is created; the single-warp probe fails there with the rig's message. Mock tables
  must be declared before the first mock function that uses them, or Lua reads a nil global (here: the stub function).
- One driving method for every drive probe (rig 2026-10-30): TaskVehicleTempAction gas (23) / reverse (22) / brake (1) in 300 ms
  slices re-issued back to back moved the car 27 m; the same actions in 200 ms slices left it standing (-0.01 m). The self-test, the
  plant and the drive now share one Lua helper (DRV in jj_probe.py: slice + heading hold on the line, speed capped with
  SetEntityMaxSpeed), so the self-test proves the exact method the test uses. The sim moves its car only on that method (a 200 ms slice
  is planted and must not move it); the pre-fix probe fails there with the rig's "never moved". Lua that is %-formatted twice must
  not hold a Lua % operator: use math.fmod.
- Read ox_fuel's state bag only after it has seen the driver (a server round trip): wait for Entity(v).state.fuel up to 3 s.
- Hinge side matters for walkways: a native door swings both ways, and the leaf a walker pushes open lies at 90 deg from its hinge on
  the walker's side. book_stair's hinge stood at the opening's end next to the stair, so the pushed-open leaf lay across the foot of flight 1
  and the next leg stalled (rig 2026-10-30, all doors shut; it passed earlier only because the door system held the doors open). Gate:
  tools/justice/p4/jj_swing.py - for each walk route, the doors it pushes open, the leaf on the side it went (less the 0.3 m tip),
  must clear every other leg by the walker's body; proven on the old hinge. Fix in the plan (hinge="near": hinge at the wall end,
  heading +180), never by opening doors for the walker.
- A map garage door (prop_hw1_03_gardoor_01 as a ymap door) opens by itself when the player is near. A door test must first force it
  SHUT through the door system (registered, ratio 0, locked) before reading "shut"; releasing it hands it back to the map default.
- Test-car speed: neither a SetEntityMaxSpeed cap (at 2.8 m/s a standing car never started) nor TaskVehicleTempAction gas / brake
  slices can hold a walking-pace speed - a 300 ms gas slice keeps pulling about one slice longer and a brake slice nearly stops the car
  (rig 2026-10-30: 2.5 wanted, 0.0-5.75 m/s seen). Use a per-frame governor: the target speed (tapering to the stop) ramped at
  +2 / -3 m/s2 and SET with SetVehicleForwardSpeed every frame (negative to reverse), engine on, heading hold every 250 ms, and stop
  pushing on a new impact (physics still resolves the hit). Brake slices only to park. The self-test proves the governor (2.5 held
  +-0.7 for 5 s). The sim is fitted to the rig's slice response (one-slice lag, gas 8, brake 9 m/s2) so the old slice loop fails there,
  and has the jail's west face as a wall so the plant's impact must register while the speed is being set.
- A freshly spawned test car can report a contact before it moves (rig 2026-10-30: contacts AT the spawn, horizontal normals); an
  impact counter that stops the drive on the first hit then stops it on frame one, and only the probe that ignores impacts (the
  self-test) ever moved. Contacts before the car has moved 0.5 m and within 1 s of a leg's start are spawn contacts: count them apart,
  log what the car touches (flag, normal, material, objects within 4.5 m). Spawn in open street, 2 m clear all round.
- A mock clock must tick per frame (Wait(0) = 16 ms), not per GetGameTimer call: a 50 ms tick per call made the mock time outrun a
  per-frame governor. With the frame clock the mock's ramp matched the rig's speeds slice for slice.
- Fly-throughs: never ease each leg - a smoothstep per waypoint leg stops the camera at every point (stop-start, static moments),
  and hold legs plus a recording margin leave long static ends (rig 2026-10-30 review). Build the track once (tools/justice/p4/
  jj_flypath.py): Catmull-Rom through the points, speed per POINT blended by cosine, ease only at the first / last 1.5 m, aim smoothed
  over 0.7 s, sampled every 0.4 s and played back with a Catmull-Rom in time; the clip = motion + 1 s. The check (jj_flycheck.py) reads
  the same frames: CLOSE (0.9 m, 0.45 at doors), HUG (rays both sides at camera and body height: nearer >= 1.2 m or centred in the
  middle 30 %), STATIC (< 0.25 m/s and < 5 deg/s for > 2 s); each proven on a plant. A rail under the camera narrows a stair: measure
  the space across at body height too, or the check pushes the camera into the mid wall.
- Never LOCK a door that is not physically shut: a locked door-system door freezes at its current angle, and ratio 0 cannot bring it
  home (rig 2026-10-30: 14 doors locked part-open at ~10 / 30 / 46 deg, every close and hold failed on the same 14). Unlock, ratio 0
  (forced), poll the leaves physically and drive again; nudge a leaf still open after 8 s (its heading set to the placement while
  unlocked); only when every leaf is shut LOCK (hold) or release (close), then read again. A released map door has no spring.
- Door work needs the doors streamed in: after a restart the player is far away and 0 of 51 objects are found. Stand the player in
  the building, put the focus on the doors' centre, poll until every object is found (20 s max), then clear the focus and put the
  player back. The sim mocks both (locked = frozen, objects only near the focus after 3 s); the old door control fails there exactly
  as on the rig. Mock locals must be declared before the functions that use them, or the catch-all stub answers (0 is truthy in Lua).
- Photos with a map garage door in view: release to the map default and it opens by itself near the player (the 23:00 pair shots
  showed the sally roll-up open). Hold every door LOCKED shut in the door system for the shots (jj_doorctl.py hold) and release in
  the step's exit trap.
- A door placed as a plain EXTERIOR map entity (ymap) in a building's opening renders black on its inside face at night: the MLO's
  lights do not reach an exterior entity and the night's natural ambient is ~0 (Jail I's sally roll-up at 23:00, 2026-10-30; its
  vertex colour was fine: Rockstar's prop has Colour0 136/133/129 on both faces). Put an opening's door in the MLO as an entity of the
  room it opens from (same model, coords, heading, door flags), so interior light reaches its inside face; check the inside at 23:00.
  CAUTION: a ROLL-UP moved into the MLO (flags 1572866) never opened for cars (jc-interiors, police garages: they were moved out to a
  map ymap for that). For a roll-up, first light its inner face from the interior (a light aimed at it, an emissive strip over the
  opening, a light-only portal attachment) and keep it a map entity; move it in only if that fails, then re-run the drive test in AND
  out through the door system before shipping.
- A FAIL line must carry the reason: the rig runner appends the newest log's traceback last line / `PROBE:` line when the detail is empty.
- **Count impacts, not contact, in a drive test:** HasEntityCollidedWithAnything is true every frame a car rolls on the floor (~2300 per
  run). Count a frame only when `GetCollisionNormalOfLastHitForEntity` is not the ground's (|n.z| < 0.6) and 0.6 s after the previous
  impact; prove it on an off-line drive into a wall. Read a garage door PHYSICALLY (object offset + pitch from its placement) while the
  car is near it: the sally-port roll-up (map door flags) opened for a car arriving from the street, then the cars reversing out stopped
  with their rears on its line - it had closed behind them.

## police-hq-area-3 (Justice Center phase 3, Police HQ + B1 garage in jc_courts, 2026-10-30)

- **The exterior colonnade follows the garage doors:** moving the garage doors moved the end of the east arcade (it stops at the door
  pier), so the lobby behind it suddenly did not front the whole glass run. A unit test now checks that the lobby region fronts
  every arcade glass segment (GAR_N to the link), proven on the old line.
- **One portal per glass run, not per door span:** portals cut around each door span left slits the gap check found. Put a single
  portal over the whole glass run, a little inside the glass (EG - 0.3).
- **A reveal belongs to the room it starts in:** put the portal at the plane where the next room starts (ramp foot at U_FOOT across
  the full lane), not at the middle of a reveal; a counter ledge that crosses a wall plane is split there and the lobby draws its half.
- **Cut a slab hole by bisecting on the hole lines, then delete the faces inside:** deleting faces whose centre is inside the hole
  left saw-tooth holes (ground check HOLE cells along the edge).
- **The street opening = the garage room:** a garage room wider than its door opening drew over the facade beside the door.
- **Garage bay lines as a decal shader**, not raised paint (paint coplanar with the slab flickers; raised paint was a trip edge).
- **Ramps:** build each ramp as a prism over the clear lane (inset 0.2 from the linings) so the ramp top is never coplanar with a
  lining foot; 4 m parabolic transitions at both ends, 1:7 between, checked by a unit test for the car's ground clearance.
- **Cross-drawable flicker check at 3 cm:** a driveway strip 3 cm over the slab still flickered at distance; its last 0.4 m eases to
  +3.8 cm and the cross check uses DZ 0.03 (proven on a planted strip).
- **One-way garage loop:** check the loop's lane paths never meet head-on in a plan test (IN lane, U-turn, return, OUT lane), and
  steer the drive probe by waypoints (SetEntityHeading capped per tick + SetVehicleForwardSpeed); count IMPACTS only (see the jail's
  note above), with an open-plaza and a planted-wall control.
- **Interview mirror:** Rockstar's `vw_vwint02_pent_mbt_mirror` (1.87 x 1.24, plane YZ) scaled to the window, as its own entity, with
  a mirror portal (flags 4) to limbo; the observation side is dark glass plus a room-to-room portal.
- **Gap rays explained:** `tools/justice/p3/tools_gap_why.py` names the first triangle (and its room) each leaking gap ray would hit,
  which turns a gap count into a fix list.
- **Anything that goes below the lot slab needs a hole in it - drawn AND collision** (jail secure stair, 6 m down): phase 1's slab at
  28.29 crossed the shaft as an invisible floor; the walker stood on it 2.5 risers down. An earlier "pass" of that leg was false: the
  arrival test had no z. Gate `jj_intrusion.py`: every other build's drawn + collision triangles against each room's clear volume (SAT),
  proven on a planted slab, run before every rig session. Hook: `jj_hooks.SLAB_HOLES` -> `p2_plan.SLAB_HOLES` -> `p1_slab.py`.
- **A garage door the server's lock system will run** (Antonio: "client add locks"): the game auto-opens a roll-up only for a car
  arriving from outside. The drive test opens it for the back-out leg through the door system (held open while the car is near, then
  released and removed), as a lock script would; the mlo-data marks the door `lock_config_required` with model hash and coords.
- **A slab hole's edge gets no skirt or apron:** the lot slab's collision apron (0.5 m out, 3 cm down) and the drawn skirt were
  extruded from EVERY boundary edge, so once holes were cut, the apron reached 0.5 m back into each hole. Jail I's stair still had
  51 collision triangles across it after the hole was cut. Extrude only the lot's outer edge (skip edges lying on a hole's lines).
  Found by jc-jail's `jj_intrusion.py` (every foreign triangle against every room's clear volume, proven on a plant), now a fatal gate
  in build_p1.sh. Hole numbers that belong to another agent's MLO are read lazily from its hooks file (jj_hooks -> jj_plan imports
  p2_plan: a module-level import is circular).
- **Never edit a shell script while it runs:** bash reads the file by offset as it goes; inserting lines into build_p1.sh mid-run
  gave "syntax error near unexpected token" at a line that was fine. Edit, then start a fresh run.
- **No sit tests for client builds (Antonio, 2026-10-30):** clients likely run no sit script. Seats are still built to sensible heights
  (chairs 0.45-0.50, benches / stools ~0.45, bunks 0.48), but there is no sit probe or sit sheet in the rig runs.
- **Drive tests with several cars in a row:** clear the spawn spot of vehicles (ClearAreaOfVehicles), require the car on the line and
  heading before it moves (abort "nothing was tested" otherwise), delete it for certain (mission entity + DeleteVehicle + check) - a
  leftover car from the previous run pushed the next one 8 m off the line and the third 100 m away. A garage door the client's lock
  system runs is opened through the door system for BOTH legs in the test: the game's own auto-open fired for the first car only.
- **Drive test pieces, each proven on its own first** (`drive_selftest`): the garage door read-back (shut ~0 / door-system open > 1 /
  shut ~0) with the door OBJECT looked up anew at every read and measured against its placement (a handle taken before the door was
  registered read 0 while a car drove under the open door); a car on a purged street moves >= 2 m on 2 s of gas; it is deleted for
  certain. Purge = every vehicle within 30 m, mission entities included (ClearAreaOfVehicles leaves those - a car left by an earlier
  run blocked two test cars at their spawn). A car that never moves is "nothing was tested", not a failed bay.
- **Rockstar's penthouse mirror is no single pane:** `vw_vwint02_pent_mbt_mirror` is TWO panels (y 0.30..0.94 and -0.94..-0.30, a 0.6 m
  gap) and its reflecting normal is **-x**. Scaled to a 5.6 m interview window it left a see-through strip, and turned with +x into
  the room it showed its back: from the interview room the window read as clear glass into the observation room. Read a vanilla
  model's vertex normals (vanilla_xml.ps1) before placing it. The interview mirrors are now our own 1 x 1 m `mirror_default` panel
  (Tower City's tc_prop_mirror recipe, facing -Y, heading 90 / 270, scaled to the span) with its own archetype in the MLO's ytyp; a unit
  test turns the panel normal by the heading and checks it faces the interview room (proven on the old heading).
- **A garage roll-up inside an MLO does not open for cars:** placed as an MLO entity (flags 1572866) the police roll-ups stayed shut
  and the drive test stopped on the IN door. Garage roll-ups are plain MAP door entities with flags 1572864 in their own ymap
  (`jc_courts_ext.ymap`; Tower City gar_meta, Jail I's sally port). Write that ymap's extents from the doors, not the writer's origin.
- **Check a drive control's lines offline first** (`tools/justice/p3/jc3_corridor.py`): the first "open plaza" line crossed a site
  planter (5 impacts) and the "planted wall" line ran into the open arcade (0 impacts, arrived) - an inverted control. The open line
  must list no near-vertical built face; the wall line must list the wall, and the wall run must NOT arrive.
- **Police roll-ups as map doors still stay shut for a car** (rig 2026-10-30, as Jail I's sally port): the buyer's door-lock system opens
  them. The garage drive (`tools/justice/p3/jc3_gdrive.py`) opens both through the door system (registered, open ratio 1, held), reads
  each door's opening from a fresh object read-back while the car is at it, then shuts and releases them; a self-test step proves the
  read-back (shut / open / shut) and that a keyed car moves. It drives with jc-jail's method (jj_probe DRV: TaskVehicleTempAction
  slices, speed cap, engine via c9_vehiclekeys ToggleEngine), the heading turned toward each waypoint 0.9 deg a frame for the turns.
  The buyer README lists both roll-ups (hash, coords, heading) under "Access / locks"; mlo-data carries them as street doors.
- **mlo-data written for area 1 went stale silently:** it listed every door of the MLO (68) as a galleria street door. Street doors are
  the doors on a portal to limbo; the rest go in `interior_doors`, each with its model hash.
- **Swept-path gate for garage drives** (`tools/justice/p3/jc3_drive_sweep.py`, fatal in build_p1.sh, proven on a planted column): the
  real footprint (width x length + 0.15 m) moved along the probe's OWN route every 0.25 m against every built face that is not a
  driving surface (drawn + collision, ours and phase 2's), the placed props' survey boxes and the bollards, with the floor taken WHERE
  THE OBSTACLE STANDS (a 6 m body spans 0.9 m of a 1:7 ramp; a ceiling plate spans rooms). It reproduced the rig's stop (the IN lane's
  line 0.8 m off the lining: the plan measured from the wall line, not the lining's face). Waypoint checks (a corridor along the
  centre line) missed it.
- **The route lives in the plan** (`jc3_pgarage.loop_route`): the plan drawing, the swept-path gate and the rig drive use one list.
  Lane lines are set off the LINING faces by the vehicle's swing on the turn (hypot(r + w/2, l/2) - r for a body turned about its
  centre, which is how the heading-hold probe turns it).
- **A 6.2 m van does not fit a garage loop that a car does:** with a 10 m deep turning pocket at the ramp feet, the IN turn and the
  U-turn into the OUT lane cannot both clear for policet, turned about its centre (rear in the walled lane) or about its rear axle
  (front corner into the lane divider, and into a 3.5 m aisle beside a fuel island). Size the van's U-turn pocket (~13 m) and its
  aisles before drawing a loop; gate the vehicles the client actually drives there.
- **Colonnade floor slabs over a basement:** phase 2's 0.5 m colonnade slab (28.3 .. 28.8) hung 8 cm under B1's ceiling (28.38),
  drawn and colliding. Phase 2 now cuts everything it builds against `p2_plan.below_mlo(k)` (B1 + walls up to its ceiling).
  (A first, wrong read blamed the colonnade floor height - PL.G is the colonnade FLOOR, 28.8; check what a z means before rebuilding.)
- **A ramp's collision is ONE welded surface, never per-slice boxes** (rig 2026-10-30: police3 climbing the OUT ramp counted impacts
  at exactly the 0.5 m slice boundaries; going down it rolled over them). Prisms with their own collision leave a vertical end face
  flush under every seam, and wheels climbing a slope catch its top edge. Draw the slices; build the collision as one open, up-facing
  strip with shared vertices. Gate: `tools/justice/p3/jc3_ramp_seams.py` reads the compiled bound (CodeWalker XML; GeometryBVH
  vertices are relative to GeometryCenter) and fails on any riser reaching the driving surface inside a lane (found 360 on the old
  build). A geometry sweep cannot find this, because nothing stands above the surface.
- **Size the garage for the vehicles that will use it, and say so:** Antonio 2026-10-30: B1 is for patrol cars; the transport van uses
  the sally port. The plan holds the design vehicle (`jc3_pgarage.VEHICLES`); lane lines = the lining face + the body's turn swing +
  0.3 m for the probe's chord steering (the van's larger swing had hidden that allowance); mlo-data `police_garage` and the buyer
  README state it.
- Side-by-side hand-back sheet: `tools/justice/p3/jc3_sheet.py` (Blender | 13:00 | 23:00 per view, labelled).

## police-hq-dressing (Justice Center area 3, 2026-10-31: Antonio "garage & headquarters look basic")
- **Dress from Rockstar's own station:** `survey/mlo_scan.tsv` lists every entity of Mission Row (`hei_heist_police_dlc`,
  `v_policehub`): folders, paper piles, mugs, lamps, keyboards, notice boards `v_20_notbrd*`, `v_20_lspd_sign`, `v_20_copfile*`,
  `v_20_evidence01`, `prop_game_clock_02`, printers, vending, water coolers, CCTV, extinguishers. The fire station gives the garage set.
  The dressing is plan data (`jc3_police_dress.py`, `jc3_pgarage_dress.py`): wall items placed by wall line + side + lining thickness,
  desks with seeded clutter so no two desks match.
- **Measure which side a wall model shows before hanging it:** Mission Row's notice boards face **+y** (their paper faces' normals),
  the whiteboard, pinboard, clock and LSPD sign face -y. Placed by the whiteboard's convention every notice board would have hung
  backwards (`facing` = summed up-facing area per side from the CodeWalker XML normals).
- **A dressing gate per prop** (`jc3_dress_check.py`, plants: a board 0.3 m off its wall, a prop in the wrong room, a board across a
  door): every prop inside its OWN room's zone (eleven lockers had stayed in the public lobby after the patrol room shrank - another
  room's entities only draw when that room is visible); wall items with a built face behind them (the stair's lining is 0.15, not 0.1;
  the lobby ceiling is CEIL - 0.2 in the tall hall, 2.6 m in the low hall); no wall item over a door opening.
- **Skirting boards in one pass over the built walls:** every vertical wall face meeting the floor gets a 10 cm board, cut against
  every wall box and every board already placed, none on faces under 0.45 m (jambs, split-lining ends). 2 cm proud: the sweep reads
  same-facing faces within 1.2 cm as fighting (12 mm boards and 6 mm hazard bands both failed). The ground check now treats a
  horizontal drawn face under 5 cm wide as trim, not ground (a sample landed on a board's top).
- **Previews with the props:** `vanilla_xml.ps1` now also reads fragments (`.yft` -> `<name>.yft.xml`: vending machines, monitors,
  TVs, water coolers, CCTV), the renderer takes either XML, and `tools/counter_kit/cw.ps1 tex` fetches the shared-txd textures into
  `survey/vanilla/_tex` (87 for this pass). Without the export the preview silently skipped every new prop.
- Check every new placement against the existing layout and the route's swing: the NE extinguisher sat in the corner turn's front
  swing (the drive sweep found it); a sofa, a flag and a copier stood in door swings (found while planning, from INTO).
- **Second dressing pass (Antonio: records, captain's office, B1 hall):** open shelving `v_corp_cabshelves01` in runs with 1 m+
  aisles instead of the dark `v_corp_offshelfdark` blocks; a commander's office = meeting table under a wall TV, sofa corner on a rug
  (`apa_mp_h_01_acc_rug`: a FLAT prop, excluded from the footprint gate), bookshelf with awards, framed pictures (measured: they face
  +y), gun rack, safe. Rockstar has NO wheel-stop and NO first-aid / eyewash prop: those are our own blocks / small cabinets with
  signs (kit geometry only where no prop exists); wheel stops 10 cm high stay under the drive sweep's 0.15 m body band.
- **One model, one kind:** making `prop_tyre_rack_01` a wall-hung model also turned the workshop's free-standing racks into wall items
  (the dressing gate found no wall behind them). A model is either hung or standing across the whole build.
- The drive sweep keeps paying off: every new hall item near a corner (a hose cabinet in the NW turn, the eyewash in the NE turn, an
  extinguisher earlier) was in the car's front swing; put wall items on the aisles' straights.
