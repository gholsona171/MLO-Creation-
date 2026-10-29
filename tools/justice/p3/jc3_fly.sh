#!/bin/bash
# jc3_fly.sh <out.mp4> <speed m/s> "<u> <v> <z>" ... : a camera fly-through on client 1 along lot-frame waypoints (Justice Center lot:
# OX 335.87 OY -1640.11 heading 50 - copy of C9Test/tc_fly.sh with the heading as HDEG), recorded with ffmpeg (20 fps). Run tc_release.sh after.
cd /c/C9Test; OUT=$1; SPEED=$2; shift 2
LEN=$(py -3 -c "
import math,sys; p=[tuple(map(float,s.split())) for s in sys.argv[1:]]; print(sum(math.dist(p[i],p[i+1]) for i in range(len(p)-1)))" "$@")
PTS=""; for spec in "$@"; do set -- $spec; PTS="$PTS{$1,$2,$3},"; done                  # (set -- clobbers "$@": the length is taken first)
DUR=$(py -3 -c "print(int($LEN/$SPEED)+2)")
./t.sh cl 1 "local O=vector2(${OX:-335.87},${OY:--1640.11}) local H=math.rad(${HDEG:-50.0})
local function W(u,v,z) return vector3(O.x+u*math.cos(H)-v*math.sin(H), O.y+u*math.sin(H)+v*math.cos(H), z) end
local raw={$PTS} local P={} for i,q in ipairs(raw) do P[i]=W(q[1],q[2],q[3]) end
local LOOK=nil if '${LOOK:-}' ~= '' then local l={${LOOK:-0,0,0}} LOOK=W(l[1],l[2],l[3]) end   -- LOOK="u,v,z": a fixed look-at instead of 6 m ahead
local p=PlayerPedId() SetEntityInvincible(p,true) SetEntityVisible(p,false) SetEntityCollision(p,false,false) FreezeEntityPosition(p,true)
if _G.__tccam then DestroyCam(_G.__tccam,false) end
local c=CreateCamWithParams('DEFAULT_SCRIPTED_CAMERA',P[1].x,P[1].y,P[1].z,0.0,0.0,0.0,62.0,false,0) SetCamActive(c,true) RenderScriptCams(true,false,0,true,true) _G.__tccam=c
NetworkOverrideClockTime(${HOUR:-13},0,0) SetWeatherTypeNowPersist('EXTRASUNNY') DisplayRadar(false) DisplayHud(false)
local function at(d) local i=1 while i<#P-1 and #(P[i+1]-P[i])<d do d=d-#(P[i+1]-P[i]) i=i+1 end local seg=#(P[i+1]-P[i]) local t=d/seg if i<#P-1 then t=math.min(1.0,t) end return P[i]+(P[i+1]-P[i])*t end   -- past the end: carries on along the last leg (the look-ahead never collapses onto the end point)
_G.__tcfly=true
CreateThread(function() Wait(${PRE:-0}*1000) local d=0.0 local total=0 for i=1,#P-1 do total=total+#(P[i+1]-P[i]) end local last=GetGameTimer()
  while _G.__tcfly and d<total do local now=GetGameTimer() d=d+$SPEED*(now-last)/1000.0 last=now
    local pos=at(d) local look=LOOK or at(d+6.0) SetCamCoord(c,pos.x,pos.y,pos.z) PointCamAtCoord(c,look.x,look.y,LOOK and look.z or look.z-0.3)
    SetEntityCoords(p,pos.x,pos.y,pos.z-1.0,false,false,false,false) SetFocusPosAndVel(pos.x,pos.y,pos.z,0.0,0.0,0.0) Wait(0) end
  _G.__tcfly=false end)
SetEntityCoords(p,P[1].x,P[1].y,P[1].z-1.0,false,false,false,false) SetFocusPosAndVel(P[1].x,P[1].y,P[1].z,0.0,0.0,0.0)
local l0=LOOK or P[2] PointCamAtCoord(c,l0.x,l0.y,LOOK and l0.z or l0.z-0.3)
return 'fly '..#P" 20 | grep -o '"result":"[^"]*"\|"err":"[^"]*"'
sleep ${PRE:-1}                                                                          # PRE: seconds for the rooms to stream in before the ride (the thread waits too)
FF=$(ls -d /c/Users/anton/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin | head -1)/ffmpeg.exe
h=$(powershell -NoProfile -Command "(Get-Process FiveM_b3258_GTAProcess | ? MainWindowHandle -ne 0 | Select -First 1).MainWindowHandle.ToInt64()")
"$FF" -hide_banner -loglevel error -y -f gdigrab -framerate 20 -i hwnd=$h -t $DUR -vf "scale=1280:-2" -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p "$OUT" </dev/null
echo "$OUT ($DUR s, ${LEN%.*} m)"
./t.sh cl 1 "_G.__tcfly=false return 'stop'" 5 > /dev/null; bash tcshot_off.sh > /dev/null
