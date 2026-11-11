#!/bin/bash
# rain_measure.sh <tag> "name x y z heading pitch" ...   (C9Test rig, local test only)
# For each spot: teleport the rig player there, point the camera (heading, pitch), read interior / rain level, count rain streaks
# with rainmeter.ps1 (5 frame pairs, median) and save a game-window shot as $RAIN_OUT/<tag>_<name>.png.
# Set the weather first (THUNDER, 21:00) through the server's weather script; PID = the player's server id (default 1).
# Calibration (Tower City court, 2026-11-10): rain falling in view 11-13k, the same spot with SetRainLevel(0) ~600.
# Moving peds and rain seen THROUGH a window also count: look at the shot before calling a high number a leak.
# Anything thin that moves counts too: trees swaying in the storm's wind (after a rig restart the court read 15k with
# SetRainLevel(0)). Always take a rain-off baseline at the same spot first; if it is high, judge by cropped shots instead
# (looking up at the roof against the dark sky shows every streak). The player is hidden while it measures.
OUT="${RAIN_OUT:-$(pwd)/rain_shots}"; mkdir -p "$OUT"
RM="$(cygpath -w "$(cd "$(dirname "$0")" && pwd)/rainmeter.ps1")"; tag=$1; shift; cd /c/C9Test
for s in "$@"; do set -- $s
 r=$(./t.sh cl ${PID:-1} "local p=PlayerPedId() SetEntityHealth(p,200) SetEntityVisible(p,false,false) SetEntityCoords(p,$2+0.0,$3+0.0,$4+0.0) SetEntityHeading(p,$5+0.0) Wait(2500) SetGameplayCamRelativeHeading(0.0) SetGameplayCamRelativePitch($6+0.0,1.0) Wait(3500) local c=GetEntityCoords(p) return string.format('int=%d rain=%.2f z=%.1f',GetInteriorFromEntity(p),GetRainLevel(),c.z)" 25 | grep -o '"result":"[^"]*"')
 m=$(powershell -NoProfile -ExecutionPolicy Bypass -File "$RM" -Pairs 5)
 powershell -NoProfile -ExecutionPolicy Bypass -File winshot.ps1 -Proc FiveM_b3258_GTAProcess -Out "$(cygpath -w "$OUT")\\${tag}_$1.png" > /dev/null
 echo "$tag $1 $r $m"
done
