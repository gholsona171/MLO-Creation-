# 01 · Pipeline

## The chain
1. **Model in Blender 4.5 + Sollumz, headless** (`blender.exe -b --python <build>.py`). Geometry is authored in a local lot
   frame (u, v, z) and placed in the world with one origin + heading. Tower City: tower lot origin (-78.897, -827.328), heading 69.5°.
2. **Export with Sollumz** (`bpy.ops.sollumz.export_assets(target_formats={'NATIVE'})` for game files, `{'CWXML'}` when the XML must be
   patched first, e.g. a render-target texture).
3. **Write the metadata in Python** (ytyp, ymap, _manifest.ymf as XML) and **compile with TequiBuild** (`TequiBuild.exe compile in.xml out`).
4. **Gates before deploy** — the build stops on any of them:
   - *sweep*: leftover / z-fighting / flickering geometry, clashes between two surfaces closer than ~2 cm.
   - *cross check*: two drawables sharing a visible surface.
   - *route check*: ambient-life walk routes hitting geometry.
   - unit tests on the pure-Python layout tables (rooms, partitions, doorways, overlaps).
5. **Assemble** the resource from build outputs only (never edit the resource by hand), copy to the rig, restart.

## Hard-won rules
- A build log's "completed" from the launching shell is NOT the build finishing. Watch for the pass line (e.g. `L3_BUILD_PASS`) and the
  gate lines; grep broadly (`Traceback|FAILED|EXIT`).
- The gate exists for a reason: a sweep failure means nothing was deployed. Fix the source, rebuild. Never deploy around it.
- Rebuild from source; never patch a deployed file (see Working agreements: no patchwork).
- Keep a backup of shared survey files before a script rewrites them (`arch_ytyp.json.bak_*`).
- Long jobs (builds ~15 min, mall ~40 min) run in the background; keep working on independent things meanwhile.
- A deploy into a running server can crash the test client. Restart the rig after every deploy (`tc_restart.sh`).

## The test rig (C:\C9Test)
- `t.sh cl 1 "<lua>" <timeout>` runs Lua in client 1 and returns the result. The fastest way to probe anything in game.
- `tc_restart.sh` closes the client, restarts the server, starts a fresh client. Never `restart`/`stop` the map resource with a
  client inside it (the client crashes).
- `tcshot.sh out.png x y z tx ty tz fov wait` / `tc_tviews.sh <tag> "name u v z tu tv tz" ...` take screenshots from a scripted
  camera (lot frame for tc_tviews). Always `tcshot_off.sh` afterwards: the shot camera stays on otherwise.
- `tc_fly.sh out.mp4 speed "u v z" ...` records a fly-through (ffmpeg gdigrab, 20 fps).
- Two clients on one PC: `sv_lan 1` + `-cl2 +connect`.
- Stopping a background job in the app can leave its child process running: check `Get-CimInstance Win32_Process` for leftovers
  before recording, or the old job will hijack the camera.

## Shipping to a buyer (2026-10-24)
- Ship a README in the resource: install order, full server restart, every config switch with its default, access lists with full identifier examples (`license:` / `discord:` / `fivem:`), the TV render target (model, target name, texture, the DUI pattern, `LocalPlayer.state.tcTvBusy`, one target per model = every copy shows the same picture), the water-map rule and the list of Rockstar files replaced. Example: `tools/towercity/buyer_README_example.md`.
- Ship the conflict check inside the resource (`tools/check_conflicts.ps1`), generated from the build's own vanilla-named stream files (`tools/towercity/conflict_list.py` + `check_conflicts.ps1.in`), so it never goes stale. It skips our own folders, so it works after install too. Prove it on a planted conflict before shipping.
- Ship safe defaults: optional moving parts off (escalators), every access check off (all floors open), and let the server owner turn them on.
