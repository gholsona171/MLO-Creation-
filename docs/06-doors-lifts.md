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
