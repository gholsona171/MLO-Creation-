#!/bin/bash
# Justice Center survey shots on the C9Test rig: jc_shots.sh <outdir> "name x y z tx ty tz fov" ...
# Saves client 1's ped position first and puts it back afterwards; tc_release.sh always runs (trap), so Antonio gets the client back.
cd /c/C9Test
OUT=$1; shift; mkdir -p "$OUT"
POS=$(./t.sh cl 1 "local c=GetEntityCoords(PlayerPedId()) return string.format('%.2f,%.2f,%.2f,%.1f',c.x,c.y,c.z,GetEntityHeading(PlayerPedId()))" 10 | grep -o '"result":"[^"]*"' | cut -d'"' -f4)
[ -n "$POS" ] || { echo "NO CLIENT ANSWER"; exit 1; }
echo "saved ped at $POS"
restore() { bash /c/C9Test/tc_release.sh; IFS=, read x y z h <<< "$POS"; ./t.sh cl 1 "local p=PlayerPedId() SetEntityCoords(p,$x+0.0,$y+0.0,$z+0.0) SetEntityHeading(p,$h+0.0) return 'back'" 10 | grep -o '"result":"[^"]*"'; }
trap restore EXIT
first=1
for v in "$@"; do read n x y z tx ty tz fov <<< "$v"
  w=4; [ $first = 1 ] && w=12; first=0
  HOUR=${HOUR:-13} bash tcshot.sh "$OUT/$n.png" $x $y $z $tx $ty $tz ${fov:-55} $w || echo "FAILED $n"
done
