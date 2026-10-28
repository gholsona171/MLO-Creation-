#!/bin/bash
# Justice Center rig shots for before / after pair sheets: jc_pair.sh <outdir> [lod] [night]
# Cameras: plan/cameras.txt ("name x y z tx ty tz fov" per line; the survey's cameras + the far LOD views). For every camera:
#   <name>.png (13:00); with 'lod' also <name>_l08.png / <name>_l04.png under OverrideLodscaleThisFrame 0.08 / 0.04 (docs 02/07: the game
#   picks the LOD / SLOD1 / SLOD2 models close up - what a far player sees); with 'night' also <name>_n.png at 23:00 (LOD lights).
# The clock is held in a thread for the whole run; client 1's ped is saved first and put back; tc_release.sh always runs (trap).
cd /c/C9Test
OUT=$1; MODE="$2 $3"; mkdir -p "$OUT"
POS=$(./t.sh cl 1 "local c=GetEntityCoords(PlayerPedId()) return string.format('%.2f,%.2f,%.2f,%.1f',c.x,c.y,c.z,GetEntityHeading(PlayerPedId()))" 10 | grep -o '"result":"[^"]*"' | cut -d'"' -f4)
[ -n "$POS" ] || { echo "NO CLIENT ANSWER"; exit 1; }
echo "saved ped at $POS"
restore() { bash /c/C9Test/tc_release.sh; IFS=, read x y z h <<< "$POS"; ./t.sh cl 1 "local p=PlayerPedId() SetEntityCoords(p,$x+0.0,$y+0.0,$z+0.0) SetEntityHeading(p,$h+0.0) return 'back'" 10 | grep -o '"result":"[^"]*"'; }
trap restore EXIT
hold() { ./t.sh cl 1 "_G.__hh=$1 if not _G.__hold then _G.__hold=true CreateThread(function() while _G.__hold do NetworkOverrideClockTime(_G.__hh or 13,0,0) Wait(0) end end) end return 'hold'" 5 > /dev/null; }
lods() { ./t.sh cl 1 "_G.__lods=$1 if not _G.__lodt then _G.__lodt=true CreateThread(function() while _G.__lodt do if _G.__lods then OverrideLodscaleThisFrame(_G.__lods) end Wait(0) end end) end return 'lods'" 5 > /dev/null; }
first=1
while read n x y z tx ty tz fov; do [ -z "$n" ] || [ "${n:0:1}" = "#" ] && continue
  w=5; [ $first = 1 ] && w=14; first=0
  hold 13; lods nil; HOUR=13 bash tcshot.sh "$OUT/$n.png" $x $y $z $tx $ty $tz ${fov:-55} $w || echo "FAILED $n"
  if [[ "$MODE" == *lod* ]]; then for s in 0.08 0.04; do lods $s; HOUR=13 bash tcshot.sh "$OUT/${n}_l${s#0.}.png" $x $y $z $tx $ty $tz ${fov:-55} 5 || echo "FAILED ${n}_l$s"; done; lods nil; fi
  if [[ "$MODE" == *night* ]]; then hold 23; HOUR=23 bash tcshot.sh "$OUT/${n}_n.png" $x $y $z $tx $ty $tz ${fov:-55} 6 || echo "FAILED ${n}_n"; hold 13; fi
done < /c/Users/anton/Documents/Codex/JusticeCenter/plan/cameras.txt
ls "$OUT" | wc -l
