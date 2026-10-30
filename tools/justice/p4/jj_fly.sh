#!/bin/bash
# jj_fly.sh <out.mp4> <pathfile> : a cinematic camera fly-through on client 1 (C9Test), recorded with ffmpeg (gdigrab, 25 fps).
# The camera track comes from jj_flypath.py (the same track jj_flycheck.py checks): a Catmull-Rom spline through the path file's points,
# speed blended smoothly between the points' speeds (never a stop), eased in / out only at the very start and end, the aim smoothed
# over time; sampled every 0.4 s in world coordinates and played back here with a Catmull-Rom in time. The clip = the motion + 1 s
# (rig 2026-10-30 review: per-leg easing made the camera stop at every waypoint, and holds + a 2 s margin left long static ends).
# Holds the clock (HOUR, default 13). Run tc_release.sh after (the caller's trap does).
[ -f "$2" ] || { echo "JJ_FLY_FAIL path file not found: $2"; exit 2; }
# both paths absolute (Windows form for the Windows python and ffmpeg) BEFORE the cd to the rig (2026-10-29: a relative path file was
# looked up in C:\C9Test, python failed, ffmpeg got an empty -t and no video was made)
JL=$(cd "$(dirname "$0")" && pwd)
PF=$(cygpath -w "$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"); OUT=$(cygpath -w "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")")
TRK=$(py -3 "$(cygpath -w "$JL/jj_flypath.py")" lua "$PF"); DUR=$(py -3 "$(cygpath -w "$JL/jj_flypath.py")" dur "$PF")
[ -n "$TRK" ] && [ -n "$DUR" ] || { echo "JJ_FLY_FAIL could not build the track from $PF"; exit 2; }
cd /c/C9Test
./t.sh cl 1 "$TRK
for i=1,#S do S[i]=vector3(S[i][1],S[i][2],S[i][3]) K[i]=vector3(K[i][1],K[i][2],K[i][3]) end
local function cr(p0,p1,p2,p3,t) local t2=t*t local t3=t2*t return (p1*2.0+(p2-p0)*t+(p0*2.0-p1*5.0+p2*4.0-p3)*t2+(p3-p0+(p1-p2)*3.0)*t3)*0.5 end
local function at(A,x) local n=#A local i=math.floor(x) local f=x-i i=i+1 return cr(A[math.max(1,i-1)],A[math.min(n,i)],A[math.min(n,i+1)],A[math.min(n,i+2)],f) end
local p=PlayerPedId() SetEntityInvincible(p,true) SetEntityVisible(p,false) SetEntityCollision(p,false,false) FreezeEntityPosition(p,true)
if _G.__tccam then DestroyCam(_G.__tccam,false) end
local c=CreateCamWithParams('DEFAULT_SCRIPTED_CAMERA',S[1].x,S[1].y,S[1].z,0.0,0.0,0.0,${FOV:-60}+0.0,false,0) SetCamActive(c,true) RenderScriptCams(true,false,0,true,true) _G.__tccam=c
_G.__hold=true CreateThread(function() while _G.__hold do NetworkOverrideClockTime(${HOUR:-13},0,0) Wait(0) end end)
SetWeatherTypeNowPersist('EXTRASUNNY') DisplayRadar(false) DisplayHud(false)
_G.__tcfly=true
CreateThread(function() Wait(${PRE:-4}*1000) local t0=GetGameTimer()
  while _G.__tcfly do local x=(GetGameTimer()-t0)/1000.0/DT if x>#S-1 then x=#S-1 end
    local pos=at(S,x) local look=at(K,x)
    SetCamCoord(c,pos.x,pos.y,pos.z) PointCamAtCoord(c,look.x,look.y,look.z) SetEntityCoords(p,pos.x,pos.y,pos.z-1.0,false,false,false,false) SetFocusPosAndVel(pos.x,pos.y,pos.z,0.0,0.0,0.0)
    if x>=#S-1 then break end Wait(0) end
  _G.__tcfly=false end)
SetEntityCoords(p,S[1].x,S[1].y,S[1].z-1.0,false,false,false,false) SetFocusPosAndVel(S[1].x,S[1].y,S[1].z,0.0,0.0,0.0) SetCamCoord(c,S[1].x,S[1].y,S[1].z) PointCamAtCoord(c,K[1].x,K[1].y,K[1].z)
return 'fly '..#S" 20 | grep -o '"result":"[^"]*"\|"err":"[^"]*"'
sleep ${PRE:-4}
FF=$(ls -d /c/Users/anton/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin | head -1)/ffmpeg.exe
h=$(powershell -NoProfile -Command "(Get-Process FiveM_b3258_GTAProcess | ? MainWindowHandle -ne 0 | Select -First 1).MainWindowHandle.ToInt64()")
"$FF" -hide_banner -loglevel error -y -f gdigrab -framerate 25 -i hwnd=$h -t $DUR -vf "scale=1280:-2" -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p "$OUT" </dev/null
D=$("$(dirname "$FF")/ffprobe.exe" -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null)
[ -n "$D" ] && [ "$(py -3 -c "print(1 if float('${D:-0}') >= $DUR - 3 else 0)")" = 1 ] && echo "JJ_FLY_OK $OUT (${D%.*} s of $DUR)" || echo "JJ_FLY_FAIL $OUT (duration '$D' of $DUR)"
./t.sh cl 1 "_G.__tcfly=false _G.__hold=false return 'stop'" 5 > /dev/null; bash tcshot_off.sh > /dev/null
