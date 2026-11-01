# 06 · Doors and lifts

- **Room doors are native game doors**, not scripts: real door props as MLO entities with Rockstar's door entity flags
  (1572866, as on `v_ilev_roc_door2`), Dynamic + door physics in the archetype; sliding doors use attribute 8. Players push them open.
  Lock systems (ox_doorlock etc.) must still work on them. Don't script room doors — a door thread that "manages" them locked every
  door in the penthouse once.
- Door data per model: leaf width, pivot height above the floor (many pivot mid-height), which way the leaf runs (+x or -x).
- **Lift doors** (`v_ilev_garageliftdoor`, `v_ilev_finelevdoor01`) are scripted with DoorSystem:
  - sliding doors take an open ratio only in **state 4**; state 0 ignores the ratio;
  - each panel of a pair needs its own sign (for `v_ilev_garageliftdoor`: -1 on both) or both slide to the middle;
  - invisible walls in a vanilla collision file can block a lift doorway: cut them with blocker boxes in our own collision.
- A lift stop = a cab you can stand in behind the doors, a landing in front, an indicator sign, and the panel; `lifts.lua` fades the
  player between stops at the same cab position on every floor.

- Lift doorways need a visible sill: the room floor under the front wall's door hole gets culled as buried, so a 30 cm strip shows
  the void (looked like a gap). Add a steel sill box in each opening, flush with the cab floor plate. Keep the per-door floor indicator
  centred above its door and the bank sign clear above it (they were jammed together).

- Solid (non-glass) single doors in the vanilla set are all 1.30 m leaves (`ex_p_mp_door_office_door01`, `ex_p_mp_door_apart_*`,
  origin 1.15 m up, leaf along -x). The `sf_prop_sf_door_office_l/r` 1.0 m leaves are glass. Plan corridors for a 1.30 m door plus
  5 cm jambs: the doorway test fails if a wall box touches the clear zone.
- Restrooms get solid doors (Antonio): never glass.

- **Door types are the archetype's special attribute** (Sollumz `SpecialAttribute`): 5 garage door (roll-up / tilt, the game drives
  it), 7 normal door, 8 sliding door, 9 barrier arm, 10 vertical sliding. Rockstar's door archetypes carry flags 604110848; map door
  entities flags 1572864 (as `prop_fnclink_06gate3`). A custom model with those values behaves as a real door (wow2easy's roll-ups).
- **Vanilla garage doors** (special attribute 5): `survey/scan_garage_doors.ps1` lists all 49 with bounds (Tower City
  `survey/doors_garage.json`). Base-game, pivot centred: `prop_hw1_03_gardoor_01` 6.22 x 4.37 m (Tower City parking),
  `prop_ss1_mpint_garage` 8.74 x 3.97, `prop_bh1_09_mp_gar` 8.02 x 3.54, `prop_com_gar_door_01` 4.0 x 4.0. A pivot at mid-height:
  seat it at floor + half its height. Placed as a plain map entity (flags 1572864) in the wall opening, opening = door top + 10 cm,
  the portal stays on the room side.
- **Sliding gates need a parking run**: as long as the leaf, straight in line with the opening, clear on the side it slides to. Where
  that doesn't exist (three gates in a 22 m diagonal, a corner one end, a building the other) use roller doors (attribute 5) with a
  header over the opening: the wall stays continuous at full height. Rockstar's tall sliding gates for reference: `prop_sc1_06_gate_l/r`
  6.8 x 4.3 m, `prop_gar_door_05_l/r` 6.2 x 4.0 m, `xm3_prop_xm3_gate_01a` 6.3 x 3.1 m.


- **Shell-only units (buyer brings the lock system):** every door is a plain native door entity (flags 1572866), with no lock
  config, no DoorSystem registration and no door script. Only the lift doors stay scripted by `lifts.lua` (that is the lift, not a
  lock). Ship the door list (model, world position, heading) in the MLO data file so the buyer can paste it into his lock config.
- A new lift stop on an existing bank means a new cab panel on EVERY stop of that bank (the panel is baked into the sign
  texture). Keep the bank's floor list in one constant (Tower City: `tower_plan.PANEL`) that every floor module imports, and
  rebuild all of them.

## Ground under a door's swing (wow2easy junkyard, round 7, 2026-10-23)
- Rocky's shop doors sit on the floor with 1-4 mm to spare. New ground laid in their swing 1 cm OVER the floor (an asphalt lot
  run up to the threshold) jammed the north porch door: the player pushed at it for 16 s. Before, there was no ground there, so
  it swung free - fixing a fall-through created the jam.
- Lay outside ground a hair UNDER the floor across every door's whole swing (the junkyard lot: `lot_plan.SILL`, 1 cm under the
  floor inside the slab and its 2 m band). A 1 cm step down out of a door trips nothing.
- Check every door, not just the reported one: `wow2easy_move/tools/door_swing_check.py` samples the half disc each leaf sweeps
  (both ways) against the built collision (every flat face, either way up - door physics is not a ray) and prints the clearance.
  Run it on the jammed build first: it flagged all 6 outside door leaves at -6 to -9 mm.

## Door openings and frames: fit the opening to the leaf (Justice Center, 2026-11-01)
Antonio: "the cutouts are too big, gaps all over the doors". Our openings were the leaf + 5 cm a side + 10 cm over the head; every door
showed a slit of light round it.

**How Rockstar does it** (measured in Mission Row: `v_policehub` entities against `v_20_policedlc_shell`, every
`v_ilev_ph_gendoor00x`): the shell's jamb faces sit exactly on the hinge and latch edges of the leaf's bounding box, the head face on
its top, the floor under its bottom - 0 mm (+-2 mm). The pivot sits on the hinge edge at mid-height (z +-1.15 for a 2.30 m leaf), so
the leaf stands on the floor. No clearance is modelled: the leaf mesh itself is a hair inside its bbox.

**The tool:** `tools/doors/door_fit.py`
- `fit_single(lo, hi, a0, z)` / `fit_pair(...)`: the exact opening from the archetype's bbox (`leaf_bbox(arch, model)` reads
  `arch_ytyp.json`), the hinge position (the end of the opening the pivot sits on) and the pivot height. Cut the wall hole with this
  opening and place the door entity on `hinge` / `zc`.
- `fillers(opening, la0, la1, z_top)`: when the hole is not yours to cut (another phase's curtain-wall bay or facade frame), the frame
  pieces that close it down to the leaves (jambs and a transom in the glass plane).
- `casing(op, face, side)`: a 7 cm casing round the opening on a wall face, 5.5 cm proud (clear of skirting / wainscot bands at
  2 - 4.8 cm and signs at 5 cm). Lay trim bands after the casings so they stop at them.
- `check(tris, doors, arch, tol=0.005)`: the gate. Per leaf: rays through the wall 2 / 5 / 10 / 20 / 40 mm outside each side and the
  head (a ray that meets nothing is a slit, unless it runs inside a perpendicular wall: odd face count above the point); the gap each
  side measured along the wall 12 mm either side of the leaf's mid plane (two rooms' linings meet on it). The other leaves of the list
  are solid (a pair's meeting edge). Pick nearby triangles by bounding box, not centroid: a long wall face's centre lies metres away
  (that bug alone made two good doors fail).
- `py -3 door_fit.py` proves the gate on a planted 5 cm opening (DOOR_FIT_PROVEN). In a build, run it with `shrink={door: 0.05}` on
  one real door as the plant (Justice Center: `work/p3/jc3_door_gate.py`, 94 doors, worst gap 0.2 mm, 0 slit rays).
- Doors in mesh / cage walls: a 6 cm steel frame on the fitted opening (the jambs are the frame), no casing.
- **Clearance, not just fit (rig 2026-11-01: three doors fitted to 0 mm the walker still could not get through):**
  `clearance(dr, arch, boxes, floor_z, depth, max_angle)` checks the walking lane through the middle of each leaf (0.7 m wide, both
  sides) and the leaf's swing both ways against props' AABBs and built solids. Depth = the probe's walk distance - 0.3 (a ped arrives
  0.6 m short of its target and is 0.3 m wide: obstacles inside 1.2 m stop it); swing to 70 deg (the leaf then leaves 0.85 m clear).
  Sample every 5 cm across and along: a 10 cm screen post and a 6 cm-thick one both slipped between 0.35 / 0.1 m samples. The three
  causes found: a training table 0.9 m beyond a door, a desk pod 1.15 m beyond one, and a glass screen line that ran into the middle
  of a door pair (one leaf on the public side of the screening line - a design fault the fit could never show).
- The slit test's "inside a perpendicular wall" check: faces within 0.3 m both ways along the door's wall. Counting faces above the point
  (parity) broke on single-sided surfaces (roofs, decals) and hid every slit.
