# Rocky Shop 8: Senora junkyard garage (FiveM map)

A copy of Rocky's Shop 8 garage, rebuilt as an MLO at the Senora junkyard (around `x 2356 y 3140`). The building, its own props, the pole sign, real game doors and the lot ground are included. The yard
under and around it is cleaned up so nothing of the old site pokes through: the old hangar and pit, the grass inside the
building, the roadside billboard and the night lights of the removed buildings.

| Folder | What it is | Needed? |
|---|---|---|
| `rocky_shop8_junkyard` | The map | **Yes** |

It doesn't need any other resource and doesn't use any scripts.

## 1. Install

1. **Check for conflicts first.** Run this from your server's `resources` folder (before or after installing):

       powershell -ExecutionPolicy Bypass -File .\rocky_shop8_junkyard\tools\check_conflicts.ps1

   It reads files only and changes nothing. It reports:
   - **SAME FILE**: another resource ships a Rockstar file this map also replaces. Only one copy loads, so you'd get holes,
     missing ground or the old junkyard buildings showing through. Remove that file from the other resource (or remove the
     other resource), or keep theirs and leave this map out.
   - **same area**: another resource replaces a different Rockstar file in the same block (`cs4_02` and its `hei_` / `lr_` /
     `hi@` versions). Usually fine, but check the junkyard in game.
   - **scripts that use the area**: a script refers to the old junkyard models here. Check what it does.

   It can't see another MLO placed at the same spot under different file names. Check around the Senora junkyard
   (x 2356 y 3140) by hand.
2. Copy `rocky_shop8_junkyard` into `resources` and add `ensure rocky_shop8_junkyard` to `server.cfg`.
3. **Restart the whole server.** A map's streamed files only load cleanly on a full restart, not on `restart <resource>`.

If you also run the original **Rocky Shop 8** (`wow2easy`) at its first location, both can run together: this copy uses its
own file names (`jy_...`).

## 2. What's inside
- **Doors**: real game doors (they swing, and door-lock scripts such as ox_doorlock can lock them by model and position). The
  east side has no door; it is a solid wall.
- **The lot**: a flat concrete slab that meets the surrounding ground with no step.
- **Rockstar files replaced:** the junkyard block `cs4_02` (map files, collision, ground, walls, grass), its occluder
  `cs4_occl_04`, nearby power wires, and the far-away night lights (`*distlodlights*`) of the removed buildings. Our own files
  all start with `jy_`.

## 3. Troubleshooting
| You see | Cause and fix |
|---|---|
| Old junkyard buildings showing through, holes, or floating grass | A file conflict: run `tools/check_conflicts.ps1` |
| Doors or props invisible | The map was started with `restart`, not a full server restart |
| Map looks broken after `restart rocky_shop8_junkyard` | Do a full server restart |
