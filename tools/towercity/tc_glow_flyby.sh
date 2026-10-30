#!/bin/bash
# tc_glow_flyby.sh <out.mp4> [hour] [secs]: a smooth night orbit round Tower City (the mall + the tower) on client 1, eased in and out
# (smoothstep on the angle, height and look point), clock held at <hour> (default 23), recorded with ffmpeg gdigrab 30 fps.
# The orbit: centre between the two lots, 260 m out, 120 -> 70 m up, 210 degrees from the south-east round to the north-west.
cd /c/C9Test; trap 'bash /c/C9Test/tc_release.sh' EXIT
OUT=$1; H=${2:-23}; DUR=${3:-36}
./t.sh cl 1 "_G.__hh=$H if not _G.__hold then _G.__hold=true CreateThread(function() while _G.__hold do NetworkOverrideClockTime(_G.__hh,0,0) Wait(0) end end) end
local C=vector3(-5.0,-855.0,0.0) local R=260.0 local A0=math.rad(-60.0) local A1=math.rad(150.0) local Z0=120.0 local Z1=70.0
local function ease(t) return t*t*(3.0-2.0*t) end
local function pos(t) local e=ease(t) local a=A0+(A1-A0)*e return vector3(C.x+R*math.cos(a), C.y+R*math.sin(a), Z0+(Z1-Z0)*e) end
local function look(t) local e=ease(t) return vector3(C.x, C.y, 140.0-70.0*e) end
local p=PlayerPedId() SetEntityInvincible(p,true) SetEntityVisible(p,false) SetEntityCollision(p,false,false) FreezeEntityPosition(p,true)
if _G.__tccam then DestroyCam(_G.__tccam,false) end
local s=pos(0.0) local c=CreateCamWithParams('DEFAULT_SCRIPTED_CAMERA',s.x,s.y,s.z,0.0,0.0,0.0,50.0,false,0) SetCamActive(c,true) RenderScriptCams(true,false,0,true,true) _G.__tccam=c
local l=look(0.0) PointCamAtCoord(c,l.x,l.y,l.z) SetEntityCoords(p,s.x,s.y,s.z,false,false,false,false) SetFocusPosAndVel(s.x,s.y,s.z,0.0,0.0,0.0)
SetWeatherTypeNowPersist('EXTRASUNNY') DisplayRadar(false) DisplayHud(false)
_G.__tcfly=true
CreateThread(function() Wait(${PRE:-6}*1000) local t0=GetGameTimer() local T=($DUR-2)*1000.0
  while _G.__tcfly do local t=math.min(1.0,(GetGameTimer()-t0)/T) local q=pos(t) local lk=look(t)
    SetCamCoord(c,q.x,q.y,q.z) PointCamAtCoord(c,lk.x,lk.y,lk.z) SetEntityCoords(p,q.x,q.y,q.z,false,false,false,false) SetFocusPosAndVel(q.x,q.y,q.z,0.0,0.0,0.0)
    if t>=1.0 then break end Wait(0) end _G.__tcfly=false end)
return 'orbit'" 20 | grep -o '"result":"[^"]*"\|"err":"[^"]*"'
sleep ${PRE:-6}
FF=$(ls -d /c/Users/anton/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin | head -1)/ffmpeg.exe
h=$(powershell -NoProfile -Command "(Get-Process FiveM_b3258_GTAProcess | ? MainWindowHandle -ne 0 | Select -First 1).MainWindowHandle.ToInt64()")
"$FF" -hide_banner -loglevel error -y -f gdigrab -framerate 30 -i hwnd=$h -t $DUR -vf "scale=1280:-2" -c:v libx264 -preset veryfast -crf 21 -pix_fmt yuv420p "$OUT" </dev/null
./t.sh cl 1 "_G.__tcfly=false return 'stop'" 5 > /dev/null
[ -s "$OUT" ] && echo "$OUT ($DUR s)" || { echo "FLYBY FAILED: no video"; exit 1; }
