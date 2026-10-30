#!/bin/bash
# jj_fly.sh <out.mp4> <pathfile> : a cinematic camera fly-through on client 1 (C9Test), recorded with ffmpeg (gdigrab, 25 fps).
# The path file has one waypoint per line, lot frame:  "u v z  speed  [look_u look_v look_z]"  - speed (m/s) of the leg that ENDS at
# this point; a look target (optional) fixes the camera's aim for that leg, else it looks 5 m ahead along the curve.
# The camera rides a Catmull-Rom spline through the points (no corners), each leg eased in and out (smoothstep), and the aim is
# blended between legs (playbook: smooth and cinematic, slow at doors, sweeping turns). Justice Center lot: OX 335.87 OY -1640.11, 50 deg.
# Holds the clock (HOUR, default 13). Run tc_release.sh after (the caller's trap does).
[ -f "$2" ] || { echo "JJ_FLY_FAIL path file not found: $2"; exit 2; }
# both paths absolute (Windows form for the Windows python and ffmpeg) BEFORE the cd to the rig (2026-10-29: a relative path file was
# looked up in C:\C9Test, python failed, ffmpeg got an empty -t and no video was made)
PF=$(cygpath -w "$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"); OUT=$(cygpath -w "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")")
cd /c/C9Test
PTS=$(py -3 - "$PF" <<'PY'
import sys
rows = [l.split() for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
out = []
for r in rows:
    u, v, z, sp = map(float, r[:4]); lk = r[4:7]
    out.append('{%s,%s,%s,%s%s}' % (u, v, z, sp, (',' + ','.join(lk)) if lk else ''))
print(','.join(out))
PY
)
DUR=$(py -3 - "$PF" <<'PY'
import sys, math
rows = [list(map(float, l.split()[:4])) for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
t = sum(max(0.4, math.dist(a[:3], b[:3]) / b[3]) for a, b in zip(rows, rows[1:]))   # the Lua gives each leg exactly len / speed (min 0.4 s): no idle tail (2026-10-29: x1.18 + 6 s left a 25 s static end)
print(int(t + 2))                                                                   # recording starts with the motion (both wait PRE): +2 s margin
PY
)
[ -n "$PTS" ] && [ -n "$DUR" ] || { echo "JJ_FLY_FAIL could not read the path file $PF"; exit 2; }
./t.sh cl 1 "local O=vector2(${OX:-335.87},${OY:--1640.11}) local H=math.rad(${HDEG:-50.0})
local function W(u,v,z) return vector3(O.x+u*math.cos(H)-v*math.sin(H), O.y+u*math.sin(H)+v*math.cos(H), z) end
local raw={$PTS} local P={} local SP={} local LK={}
for i,q in ipairs(raw) do P[i]=W(q[1],q[2],q[3]) SP[i]=q[4] if q[5] then LK[i]=W(q[5],q[6],q[7]) end end
local function cr(p0,p1,p2,p3,t) local t2=t*t local t3=t2*t return (p1*2.0+(p2-p0)*t+(p0*2.0-p1*5.0+p2*4.0-p3)*t2+(p3-p0+(p1-p2)*3.0)*t3)*0.5 end
local function pt(i,t) local n=#P return cr(P[math.max(1,i-1)],P[i],P[math.min(n,i+1)],P[math.min(n,i+2)],t) end
local p=PlayerPedId() SetEntityInvincible(p,true) SetEntityVisible(p,false) SetEntityCollision(p,false,false) FreezeEntityPosition(p,true)
if _G.__tccam then DestroyCam(_G.__tccam,false) end
local c=CreateCamWithParams('DEFAULT_SCRIPTED_CAMERA',P[1].x,P[1].y,P[1].z,0.0,0.0,0.0,${FOV:-60}+0.0,false,0) SetCamActive(c,true) RenderScriptCams(true,false,0,true,true) _G.__tccam=c
_G.__hold=true CreateThread(function() while _G.__hold do NetworkOverrideClockTime(${HOUR:-13},0,0) Wait(0) end end)
SetWeatherTypeNowPersist('EXTRASUNNY') DisplayRadar(false) DisplayHud(false)
_G.__tcfly=true
CreateThread(function() Wait(${PRE:-4}*1000) local lastLook=nil
  for i=1,#P-1 do
    local len=#(P[i+1]-P[i]) local dur=math.max(0.4,len/SP[i+1])*1000.0 local t0=GetGameTimer()
    while _G.__tcfly do local e=(GetGameTimer()-t0)/dur if e>1.0 then break end
      local s=e*e*(3.0-2.0*e) local pos=pt(i,s)
      local look=LK[i+1] or pt(i,math.min(1.0,s+0.25)) if not LK[i+1] and s>0.75 and i<#P-1 then look=pt(i+1,(s-0.75)) end
      if (look-pos).x==0 and (look-pos).y==0 then look=pos+(P[i+1]-P[i]) end
      if lastLook then look=lastLook+(look-lastLook)*0.12 end lastLook=look
      SetCamCoord(c,pos.x,pos.y,pos.z) PointCamAtCoord(c,look.x,look.y,look.z) SetEntityCoords(p,pos.x,pos.y,pos.z-1.0,false,false,false,false) SetFocusPosAndVel(pos.x,pos.y,pos.z,0.0,0.0,0.0) Wait(0) end
  end _G.__tcfly=false end)
SetEntityCoords(p,P[1].x,P[1].y,P[1].z-1.0,false,false,false,false) SetFocusPosAndVel(P[1].x,P[1].y,P[1].z,0.0,0.0,0.0) PointCamAtCoord(c,P[2].x,P[2].y,P[2].z)
return 'fly '..#P" 20 | grep -o '"result":"[^"]*"\|"err":"[^"]*"'
sleep ${PRE:-4}
FF=$(ls -d /c/Users/anton/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin | head -1)/ffmpeg.exe
h=$(powershell -NoProfile -Command "(Get-Process FiveM_b3258_GTAProcess | ? MainWindowHandle -ne 0 | Select -First 1).MainWindowHandle.ToInt64()")
"$FF" -hide_banner -loglevel error -y -f gdigrab -framerate 25 -i hwnd=$h -t $DUR -vf "scale=1280:-2" -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p "$OUT" </dev/null
D=$("$(dirname "$FF")/ffprobe.exe" -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null)
[ -n "$D" ] && [ "$(py -3 -c "print(1 if float('${D:-0}') >= $DUR - 3 else 0)")" = 1 ] && echo "JJ_FLY_OK $OUT (${D%.*} s of $DUR)" || echo "JJ_FLY_FAIL $OUT (duration '$D' of $DUR)"
./t.sh cl 1 "_G.__tcfly=false _G.__hold=false return 'stop'" 5 > /dev/null; bash tcshot_off.sh > /dev/null
