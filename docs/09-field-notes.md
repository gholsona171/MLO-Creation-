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
