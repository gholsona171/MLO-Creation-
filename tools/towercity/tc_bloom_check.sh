#!/bin/bash
# tc_bloom_check.sh <tag>: night-bloom check (main, 2026-10-25) with the GAMEPLAY camera (scripted cams skip room timecycles):
# court, a storefront, the Grill (2 views), station platform, promenade/concourse at 23:00 and 13:00 -> shots/towercity/<tag>/
# Always gives client 1 back (tc_release.sh).
cd /c/C9Test; trap 'bash /c/C9Test/tc_release.sh >/dev/null' EXIT
T=${1:-bloom}; D=shots/towercity/$T; mkdir -p $D
# name x y z heading relheading pitch   (mall lot frame converted to world for the first ones; the Grill in world, from main)
read -r -d '' SPOTS <<EOF
court $(py -3 -c "import math;h=math.radians(69.5);O=(71.0,-884.0);u,v=30,0;print('%.2f %.2f'%(O[0]+u*math.cos(h)-v*math.sin(h),O[1]+u*math.sin(h)+v*math.cos(h)))") 30.6 339.5 0 5
shops $(py -3 -c "import math;h=math.radians(69.5);O=(71.0,-884.0);u,v=-28,-3;print('%.2f %.2f'%(O[0]+u*math.cos(h)-v*math.sin(h),O[1]+u*math.sin(h)+v*math.cos(h)))") 30.9 159.5 0 0
grill1 41.0 -907.5 29.2 20 0 -20
grill2 41.0 -907.5 29.2 20 150 -25
platform $(py -3 -c "import math;h=math.radians(69.5);O=(71.0,-884.0);u,v=5,24;print('%.2f %.2f'%(O[0]+u*math.cos(h)-v*math.sin(h),O[1]+u*math.sin(h)+v*math.cos(h)))") 20.7 120 0 -5
concourse $(py -3 -c "import math;h=math.radians(69.5);O=(71.0,-884.0);u,v=5,39;print('%.2f %.2f'%(O[0]+u*math.cos(h)-v*math.sin(h),O[1]+u*math.sin(h)+v*math.cos(h)))") 24.4 140 0 -5
EOF
for HR in 23 13; do
  ./t.sh cl 1 "_G.__holdh=$HR if not _G.__hold then _G.__hold=true CreateThread(function() while _G.__hold do NetworkOverrideClockTime(_G.__holdh or 13,0,0) Wait(0) end end) end return 'hold'" 5 >/dev/null
  while read -r n x y z h rh pt; do
    [ -z "$n" ] && continue
    ./t.sh cl 1 "local p=PlayerPedId() RenderScriptCams(false,false,0,true,true) FreezeEntityPosition(p,false) SetEntityVisible(p,true) SetEntityCollision(p,true,true)
SetEntityCoords(p,$x+0.0,$y+0.0,$z+0.0,false,false,false,false) SetEntityHeading(p,$h+0.0) SetFollowPedCamViewMode(2) Wait(500)
SetGameplayCamRelativeHeading($rh+0.0) SetGameplayCamRelativePitch($pt+0.0,1.0) DisplayRadar(false) DisplayHud(false) return 'ok'" 10 >/dev/null
    sleep 5; ./t.sh cl 1 "SetGameplayCamRelativeHeading($rh+0.0) SetGameplayCamRelativePitch($pt+0.0,1.0) return 1" 5 >/dev/null; sleep 1
    bash gshot.sh $D/${n}_${HR}.png >/dev/null && echo $D/${n}_${HR}.png
  done <<< "$SPOTS"
done
