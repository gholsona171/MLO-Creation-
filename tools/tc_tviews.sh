#!/bin/bash
# tc_tviews.sh <tag> "<name> u v z tu tv tz" ... : tower-lot viewpoints with a LIVE ped (unfrozen, so its room updates) ->
# shots/towercity/<tag>_<name>.png   (OX=71.0 OY=-884.0 for the mall lot)
D=/c/C9Test/shots/towercity; mkdir -p $D; cd /c/C9Test; TAG=$1; shift
for spec in "$@"; do
  set -- $spec; n=$1; shift
  ./t.sh cl 1 "local O=vector2(${OX:--78.897},${OY:--827.328}) local H=math.rad(69.5)
local function W(u,v) return O.x+u*math.cos(H)-v*math.sin(H), O.y+u*math.sin(H)+v*math.cos(H) end
local x,y=W($1+0.0,$2+0.0) local tx,ty=W($4+0.0,$5+0.0) local p=PlayerPedId()
SetEntityInvincible(p,true) FreezeEntityPosition(p,false) SetEntityVisible(p,false) SetEntityCollision(p,true,true) SetEntityCoords(p,x,y,$3-1.0,false,false,false,false)
if _G.__tccam then DestroyCam(_G.__tccam,false) end
local c=CreateCamWithParams('DEFAULT_SCRIPTED_CAMERA',x,y,$3+0.0,0.0,0.0,0.0,62.0,false,0) PointCamAtCoord(c,tx,ty,$6+0.0) SetCamActive(c,true) RenderScriptCams(true,false,0,true,true) _G.__tccam=c
NetworkOverrideClockTime(${HOUR:-13},0,0) DisplayRadar(false) DisplayHud(false) return 'cam'" 20 >/dev/null
  sleep ${WAIT:-7}; bash gshot.sh $D/${TAG}_$n.png >/dev/null && echo $D/${TAG}_$n.png
done
bash tcshot_off.sh >/dev/null
