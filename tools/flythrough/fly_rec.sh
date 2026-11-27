#!/bin/bash
# fly_rec.sh <out.mp4> <pathfile> : record a cinematic fly-through on the C9Test rig (generalised from justice/p4/jj_fly.sh, 2026-11-27).
# The track comes from fly_path.py (world coordinates; the same track `fly_path.py check` checks). Env:
#   CL     client (server id) to fly on (default 1)            HOUR  clock held every frame (default 13; 22 for night)
#   FOV    camera fov (default 60)                              PRE   seconds for the first spot to stream in before the ride (default 4)
#   DOORS  "model x y z [t];model x y z [t]" doors to swing/roll OPEN on camera t s into the ride (default 0; take t from
#          `fly_path.py times`). Filming aid only: our own door-system hashes, held shut until t, shut and removed after; never shipped.
# The server HUD (c9_hud) is hidden for the ride and shown again after; GTA's own HUD and radar too. Needs the player healed first
# (osp_ambulance blur / camera shake would be recorded): Block Boyz tools/bbheal.sh pattern.
[ -f "$2" ] || { echo "FLY_FAIL path file not found: $2"; exit 2; }
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${PY:-/c/Users/anton/AppData/Local/Programs/Python/Python313/python.exe}
PF=$(cygpath -w "$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"); OUT=$(cygpath -w "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")")
TRK=$("$PY" "$(cygpath -w "$HERE/fly_path.py")" lua "$PF"); DUR=$("$PY" "$(cygpath -w "$HERE/fly_path.py")" dur "$PF")
[ -n "$TRK" ] && [ -n "$DUR" ] || { echo "FLY_FAIL could not build the track from $PF"; exit 2; }
CL=${CL:-1}; DL=""
IFS=';' read -ra DA <<< "${DOORS:-}"; for d in "${DA[@]}"; do set -- $d; [ -n "$1" ] && DL="$DL{'$1',$2,$3,$4,${5:-0}},"; done
cd /c/C9Test
./t.sh cl $CL "$TRK
for i=1,#S do S[i]=vector3(S[i][1],S[i][2],S[i][3]) K[i]=vector3(K[i][1],K[i][2],K[i][3]) end
local function cr(p0,p1,p2,p3,t) local t2=t*t local t3=t2*t return (p1*2.0+(p2-p0)*t+(p0*2.0-p1*5.0+p2*4.0-p3)*t2+(p3-p0+(p1-p2)*3.0)*t3)*0.5 end
local function at(A,x) local n=#A local i=math.floor(x) local f=x-i i=i+1 return cr(A[math.max(1,i-1)],A[math.min(n,i)],A[math.min(n,i+1)],A[math.min(n,i+2)],f) end
local D={$DL} _G.__flydoors={}
for i,d in ipairs(D) do local h=GetHashKey('flyrec_door_'..i) AddDoorToSystem(h,GetHashKey(d[1]),d[2]+0.0,d[3]+0.0,d[4]+0.0,false,false,false) DoorSystemSetDoorState(h,1,false,true) DoorSystemSetOpenRatio(h,0.0,false,true) _G.__flydoors[#_G.__flydoors+1]={h,d[5]} end
local p=PlayerPedId() SetEntityInvincible(p,true) SetEntityVisible(p,false) SetEntityCollision(p,false,false) FreezeEntityPosition(p,true)
pcall(function() exports.c9_hud:SetVisible(false) end)
if _G.__tccam then DestroyCam(_G.__tccam,false) end
local c=CreateCamWithParams('DEFAULT_SCRIPTED_CAMERA',S[1].x,S[1].y,S[1].z,0.0,0.0,0.0,${FOV:-60}+0.0,false,0) SetCamActive(c,true) RenderScriptCams(true,false,0,true,true) _G.__tccam=c
_G.__hold=true CreateThread(function() while _G.__hold do NetworkOverrideClockTime(${HOUR:-13},0,0) SetWeatherTypeNowPersist('EXTRASUNNY') HideHudAndRadarThisFrame() Wait(0) end end)
DisplayRadar(false) DisplayHud(false)
_G.__tcfly=true
CreateThread(function() Wait(${PRE:-4}*1000) local t0=GetGameTimer() local opened={}
  while _G.__tcfly do local el=(GetGameTimer()-t0)/1000.0 local x=el/DT if x>#S-1 then x=#S-1 end
    for i,dh in ipairs(_G.__flydoors) do if not opened[i] and el>=dh[2] then opened[i]=true DoorSystemSetDoorState(dh[1],0,false,true) DoorSystemSetOpenRatio(dh[1],1.0,false,true) end end
    local pos=at(S,x) local look=at(K,x)
    SetCamCoord(c,pos.x,pos.y,pos.z) PointCamAtCoord(c,look.x,look.y,look.z) SetEntityCoords(p,pos.x,pos.y,pos.z-1.0,false,false,false,false) SetFocusPosAndVel(pos.x,pos.y,pos.z,0.0,0.0,0.0)
    if x>=#S-1 then break end Wait(0) end
  _G.__tcfly=false end)
SetEntityCoords(p,S[1].x,S[1].y,S[1].z-1.0,false,false,false,false) SetFocusPosAndVel(S[1].x,S[1].y,S[1].z,0.0,0.0,0.0) SetCamCoord(c,S[1].x,S[1].y,S[1].z) PointCamAtCoord(c,K[1].x,K[1].y,K[1].z)
return 'fly '..#S..' doors '..#D" 25 | grep -o '"result":"[^"]*"\|"err":"[^"]*"'
sleep ${PRE:-4}
FF=$(ls -d /c/Users/anton/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin | head -1)/ffmpeg.exe
h=$(powershell -NoProfile -Command "(Get-Process FiveM_b3258_GTAProcess | ? MainWindowHandle -ne 0 | Select -First 1).MainWindowHandle.ToInt64()")
"$FF" -hide_banner -loglevel error -y -f gdigrab -framerate 25 -i hwnd=$h -t $DUR -vf "scale=1920:-2" -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p "$OUT" </dev/null
D=$("$(dirname "$FF")/ffprobe.exe" -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null)
[ -n "$D" ] && [ "$("$PY" -c "print(1 if float('${D:-0}') >= $DUR - 3 else 0)")" = 1 ] && echo "FLY_OK $OUT (${D%.*} s of $DUR)" || echo "FLY_FAIL $OUT (duration '$D' of $DUR)"
# release: doors shut and handed back to the map, camera off, ped back, HUD back
./t.sh cl $CL "_G.__tcfly=false _G.__hold=false
for _,dh in ipairs(_G.__flydoors or {}) do DoorSystemSetDoorState(dh[1],1,false,true) DoorSystemSetOpenRatio(dh[1],0.0,false,true) end
CreateThread(function() Wait(6000) for _,dh in ipairs(_G.__flydoors or {}) do RemoveDoorFromSystem(dh[1]) end _G.__flydoors=nil end)
if _G.__tccam then RenderScriptCams(false,false,0,true,true) DestroyCam(_G.__tccam,false) _G.__tccam=nil end ClearFocus()
local p=PlayerPedId() SetEntityVisible(p,true) FreezeEntityPosition(p,false) SetEntityCollision(p,true,true) SetEntityInvincible(p,false)
pcall(function() exports.c9_hud:SetVisible(true) end) DisplayRadar(true) DisplayHud(true) return 'released'" 15 | grep -o '"result":"[^"]*"'
