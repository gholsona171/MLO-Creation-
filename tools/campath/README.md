# campath: cinematic camera fly-throughs

Antonio (2026-11-24): "smooth movements and transitions, very cinematic, not robotic and stiff; move room to room; none of the
points inside walls". Replaces `cine.sh`, which ran a uniform Catmull-Rom per shot. That moved faster where points were far apart,
and its per-shot smoothstep stopped the camera dead at every shot's end.

| Step | Tool | What it does |
|---|---|---|
| 1 | your route script | writes `route.json`: shots of keys `{p, speed, look?, fov?}`, `hour`, `fov`, `shake`, `clearance` |
| 2 | your solids script | writes `solids.json`: boxes for walls, glass, slabs, furniture, poles, from the build's own plans |
| 3 | `campath.py route.json outdir --solids solids.json` | compiles the track and checks every 5 cm against the solids (`CAMPATH_PASS` / `CAMPATH_FAIL` with the shot, time, point and box) |
| 4 | `campath_plot.py track solids out.png [x0 y0 x1 y1]` | top-down drawing for review; `ZBAND=z0,z1` draws one storey |
| 5 | `CL=<id> OPENS=model:swing:90:9 campath.sh track.json probe` | flies it in game at 2x, sweeping every frame with shape tests; prints every crossing or near-miss (`CAMPATH_PROBE_CLEAN`) |
| 6 | `CL=<id> OPENS=... campath.sh track.json run out.mp4` | records it; `campath_cut.py` trims the black between shots to a short dip and encodes 1080p |

What makes it read as cinematic, not robotic:
- **Centripetal Catmull-Rom, re-timed by arc length.** The speed is the one you set, whatever the spacing of the keys, and
  tight corners don't loop or overshoot.
- **Speed blends key to key** (cosine) under an acceleration limit (0.55 m/s²). A shot starts already moving and never stops; a
  dip to black joins shots.
- **The aim glides.** Each key either looks along the path or at a point. Consecutive look points slide into each other while
  the camera moves, which gives parallax. Yaw and pitch are then Gaussian-smoothed over 0.55 s, so turns ease in and out.
- **A light hand-held shake** (`HAND_SHAKE` 0.12). Streaming focus is pushed half a second ahead, the invisible ped rides with
  the camera so MLO rooms render, and doors you list open on camera (the leaf swings or slides, eased over 1.4 s, by hand: the door system can't move a door a door-lock script already owns). Unlocked sliding gates open by themselves for the ped riding with the camera.
- On Cleveland: the player turns off the weather sync and `dd_hud` for the run and turns them back on after.

Pacing that worked (Graveyard yard, golden hour 17:30): aerial 9-12 m/s, ground approach 4-8 m/s, through gates 3 m/s, interiors
1.0-1.4 m/s, stairs 1.0 m/s. Near power lines, stay under 6 m over the ground or far above (lines hang at ~9-10 m).
Worked example: graveyard_towyard `tools/fly_route.py` + `tools/cam_solids.py`.
