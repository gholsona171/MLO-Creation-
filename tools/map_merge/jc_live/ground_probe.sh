#!/bin/bash
# ground_probe.sh: drops client 1's ped (visible, collision on) 3 m above each road point of the merged spots, waits, and reads where
# it stands: final z, GetGroundZFor_3dCoord, IsPedFalling / in-air. A hole or missing road shows as a ped far below the ground z or
# still falling. Restores the ped afterwards. Output: one line per point, then GROUND_PASS / GROUND_FAIL.
cd /c/C9Test
POS=$(./t.sh cl 1 "local c=GetEntityCoords(PlayerPedId()) return string.format('%.2f,%.2f,%.2f',c.x,c.y,c.z)" 10 | grep -o '"result":"[^"]*"' | cut -d'"' -f4)
restore() { bash /c/C9Test/tc_release.sh >/dev/null 2>&1; IFS=, read x y z <<< "$POS"; ./t.sh cl 1 "SetEntityCoords(PlayerPedId(),$x+0.0,$y+0.0,$z+0.0) return 'back'" 10 >/dev/null; }
trap restore EXIT
bash /c/C9Test/tc_release.sh >/dev/null 2>&1
FAIL=0
while read n x y; do
  r=$(./t.sh cl 1 "local p=PlayerPedId() SetEntityVisible(p,true) FreezeEntityPosition(p,false) SetEntityCollision(p,true,true) SetEntityInvincible(p,true)
local x,y=$x+0.0,$y+0.0 RequestCollisionAtCoord(x,y,30.0) SetFocusPosAndVel(x,y,30.0,0,0,0)
local ok,gz=false,0.0 for i=1,60 do ok,gz=GetGroundZFor_3dCoord(x,y,150.0,false) if ok then break end Wait(100) end
SetEntityCoords(p,x,y,gz+3.0,false,false,false,false) Wait(4000)
local c=GetEntityCoords(p) ClearFocus()
return string.format('ground %.2f ped %.2f diff %.2f falling %s air %s', gz, c.z, c.z-gz, tostring(IsPedFalling(p)), tostring(IsEntityInAir(p)))" 25 | grep -o '"result":"[^"]*"' | cut -d'"' -f4)
  echo "$n ($x, $y): $r"
  d=$(echo "$r" | sed -n 's/.*diff \(-\?[0-9.]*\).*/\1/p'); f=$(echo "$r" | grep -c "falling true")
  awk -v d="$d" 'BEGIN{exit !(d=="" || d<0.5 || d>1.6)}' && FAIL=1; [ "$f" = 1 ] && FAIL=1
done <<'PTS'
jc_davis_ave_sw 280.0 -1690.0
jc_davis_ave_nw 300.0 -1575.0
jc_innocence_e 410.0 -1640.0
jc_south_corner 330.0 -1715.0
jc_plaza 369.8 -1590.3
bennys_front -205.0 -1305.0
bennys_road -230.0 -1290.0
strawberry_wash 20.0 -1400.0
strawberry_road 35.0 -1440.0
davis_wash 172.0 -1720.0
davis_road 140.0 -1745.0
grove_st 95.0 -1915.0
grove_compound -60.0 -1850.0
hood_street 340.0 -2050.0
hood_east 420.0 -2050.0
medical_center_front 344.0 -1440.0
medical_center_road 300.0 -1410.0
PTS
[ $FAIL = 0 ] && echo GROUND_PASS || echo GROUND_FAIL
