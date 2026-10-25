#!/bin/bash
# ctr/aimplace.sh <x> <y> <z> <shot> : aims the gameplay camera at a world point (laser active), takes a shot, then presses Enter while still aiming
cd /c/C9Test
AIM="_G.__fp=${FP:-0} local tx,ty,tz=$1+0.0,$2+0.0,$3+0.0 local p=PlayerPedId() local function aim() if (_G.__fp or 0) > 0 then SetFollowPedCamViewMode(4) end local c=GetGameplayCamCoord() local dx,dy,dz=tx-c.x,ty-c.y,tz-c.z SetGameplayCamRelativeHeading(((math.deg(math.atan(-dx,dy))-GetEntityHeading(p)+540.0)%360.0)-180.0) SetGameplayCamRelativePitch(math.deg(math.atan(dz,math.sqrt(dx*dx+dy*dy))),1.0) end"
./t.sh cl 1 "$AIM local t=GetGameTimer()+${HOLD:-2200} while GetGameTimer()<t do aim() Wait(0) end _G.__aimhold=true CreateThread(function() while _G.__aimhold do aim() Wait(0) end end) return true" 15 >/dev/null
bash gshot.sh shots/ctr/$4.png >/dev/null
./t.sh cl 1 "for i = 1, 8 do SetControlNormal(0, 191, 1.0) SetControlNormal(2, 191, 1.0) Wait(0) end Wait(300) _G.__aimhold=false Wait(1500) return true" 15 >/dev/null
