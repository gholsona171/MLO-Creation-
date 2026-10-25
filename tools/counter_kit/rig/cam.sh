#!/bin/bash
# ctr/cam.sh <out.png> x y z tx ty tz [fov] : one scripted-camera frame of client 1 (the ped stays where it is), camera released after
cd /c/C9Test
./t.sh cl 1 "if _G.__tccam then DestroyCam(_G.__tccam,false) end
local c=CreateCamWithParams('DEFAULT_SCRIPTED_CAMERA',$2+0.0,$3+0.0,$4+0.0,0.0,0.0,0.0,${8:-55}+0.0,false,0) PointCamAtCoord(c,$5+0.0,$6+0.0,$7+0.0) SetCamActive(c,true) RenderScriptCams(true,false,0,true,true) _G.__tccam=c
SetFocusPosAndVel($5+0.0,$6+0.0,$7+0.0,0.0,0.0,0.0) DisplayRadar(false) DisplayHud(false) return 'cam'" 20 >/dev/null
sleep ${WAIT:-3}; bash gshot.sh "$1" >/dev/null && echo "$1"
[ -z "$KEEP" ] && bash tcshot_off.sh >/dev/null
