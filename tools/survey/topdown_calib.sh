#!/bin/bash
# Top-down survey shot + its calibration: world points (z given) -> screen fractions while the shot camera is live.
# jc_calib.sh <png> cx cy camz fov z_ground ; prints "wx wy sx sy" lines. Ped restored + tc_release on exit.
cd /c/C9Test
POS=$(./t.sh cl 1 "local c=GetEntityCoords(PlayerPedId()) return string.format('%.2f,%.2f,%.2f,%.1f',c.x,c.y,c.z,GetEntityHeading(PlayerPedId()))" 10 | grep -o '"result":"[^"]*"' | cut -d'"' -f4)
[ -n "$POS" ] || { echo "NO CLIENT ANSWER"; exit 1; }
restore() { bash /c/C9Test/tc_release.sh; IFS=, read x y z h <<< "$POS"; ./t.sh cl 1 "local p=PlayerPedId() SetEntityCoords(p,$x+0.0,$y+0.0,$z+0.0) SetEntityHeading(p,$h+0.0) return 'back'" 10 | grep -o '"result":"[^"]*"'; }
trap restore EXIT
bash tcshot.sh "$1" $2 $3 $4 $2 $(py -3 -c "print($3+0.01)") $6 $5 14
./t.sh cl 1 "local o={} for dx=-150,150,50 do for dy=-150,150,50 do local ok,sx,sy=GetScreenCoordFromWorldCoord($2+dx+0.0,$3+dy+0.0,$6+0.0) if ok then o[#o+1]=string.format('%.1f %.1f %.5f %.5f',$2+dx,$3+dy,sx,sy) end end end local c=GetCamCoord(_G.__tccam) local r=GetCamRot(_G.__tccam,2) o[#o+1]=string.format('cam %.2f %.2f %.2f rot %.2f %.2f %.2f fov %.2f',c.x,c.y,c.z,r.x,r.y,r.z,GetCamFov(_G.__tccam)) return table.concat(o,';')" 10 | grep -o '"result":"[^"]*"' | cut -d'"' -f4 | tr ';' '\n' > "${1%.png}_calib.txt"
wc -l "${1%.png}_calib.txt"; tail -1 "${1%.png}_calib.txt"
