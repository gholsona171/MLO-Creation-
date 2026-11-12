#!/bin/bash
# photo_set.sh <outdir> [name-filter]: one 1920 px jpg per viewpoint of photo_views.py (client 1, scripted camera, 13:00, clear sky).
# Saves the ped position first and puts it back after (tc_release + restore), like JusticeCenter/work/jc_shots.sh.
M=/c/C9Test/rebuild/install/jc_live_merge; OUT=$1; F=${2:-.}; mkdir -p "$OUT/png"; cd /c/C9Test
FF=$(ls -d /c/Users/anton/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin | head -1)/ffmpeg.exe
POS=$(./t.sh cl 1 "local c=GetEntityCoords(PlayerPedId()) return string.format('%.2f,%.2f,%.2f,%.1f',c.x,c.y,c.z,GetEntityHeading(PlayerPedId()))" 10 | grep -o '"result":"[^"]*"' | cut -d'"' -f4)
[ -n "$POS" ] || { echo "NO CLIENT ANSWER"; exit 1; }
restore() { bash /c/C9Test/tc_release.sh >/dev/null 2>&1; IFS=, read x y z h <<< "$POS"; ./t.sh cl 1 "local p=PlayerPedId() SetEntityCoords(p,$x+0.0,$y+0.0,$z+0.0) SetEntityHeading(p,$h+0.0) return 'back'" 10 | grep -o '"result":"[^"]*"'; }
trap restore EXIT
py -3 $M/tools/photo_views.py | grep -E "$F" | while read n x y z tx ty tz fov; do
  HOUR=13 bash tcshot.sh "$OUT/png/$n.png" $x $y $z $tx $ty $tz $fov ${WAIT:-9} >/dev/null || echo "FAILED $n"
  # the photo itself: the harness's screenshot-basic grab (the game frame without the HUD / NUI), scaled to 1920 px wide
  S="/c/C9Test/live/resources/[localtest]/c9_testharness/shots/jcm_$n.jpg"; rm -f "$S"; ./t.sh shot 1 "jcm_$n" >/dev/null
  for i in $(seq 1 20); do [ -s "$S" ] && break; sleep 1; done
  "$FF" -hide_banner -loglevel error -y -i "C:${S#/c}" -vf scale=1920:-2 -q:v 2 "$OUT/$n.jpg" </dev/null && echo "$OUT/$n.jpg"
done
