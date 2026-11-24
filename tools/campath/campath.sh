#!/bin/bash
# campath.sh <track.json> <run|probe> [out.mp4] : plays a campath.py track on the C9Test rig client CL (env, required).
#   probe : flies it at PROBE_SPEED (default 2x) with no fades, sweeping every frame with shape tests; prints every place the
#           camera crossed or came within 0.3 m of collision (CAMPATH_PROBE_CLEAN when none)
#   run   : records the FiveM window (gdigrab, 30 fps, full window) while the track plays, then campath_cut.py trims the black
#           between shots to a short dip and writes out.mp4
# env: CL (client server id), OPENS (doors to open on camera, comma list of model:swing|slide:amount:near, e.g.
#      jy_house_frontdoor:swing:90:9 = swing 90 deg as the camera comes within 9 m), WEATHER. Take the rig lock first.
set -e; HERE=$(cd "$(dirname "$0")" && pwd); T=/c/C9Test/t.sh
TRACK=$1; MODE=${2:-probe}; OUT=$3; : "${CL:?set CL to the client id (t.sh players)}"
PY=/c/Users/anton/AppData/Local/Programs/Python/Python313/python
# 1. the track as Lua, sent in <20 kB chunks (the harness takes the code on a command line)
CH=$(mktemp -d); $PY - "$TRACK" "$CH" <<'EOF'
import json, sys
D = json.load(open(sys.argv[1])); f = lambda a: '{' + ','.join(repr(x) for x in a) + '}'
shots = ','.join('{hour=%r,dt=%r,dur=%r,name=%r,x=%s,y=%s,z=%s,pitch=%s,yaw=%s,fov=%s}' % (s['hour'], s['dt'], s['dur'], s['name'],
         f(s['x']), f(s['y']), f(s['z']), f(s['pitch']), f(s['yaw']), f(s['fov'])) for s in D['shots'])
src = '{shake=%r,shots={%s}}' % (D.get('shake', 0.12), shots); n = 18000
for i in range(0, len(src), n): open(f'{sys.argv[2]}/c{i // n:04d}', 'w').write(src[i:i + n])
EOF
bash $T cl $CL "_G.__cpbuf='' return 'ok'" 5 >/dev/null
for c in "$CH"/c*; do r=$(bash $T cl $CL "_G.__cpbuf=_G.__cpbuf..[==[$(cat "$c")]==] return #_G.__cpbuf" 5 | grep -o '"result":[0-9]*'); done
echo "track sent ($r chars)"; rm -rf "$CH"
DL=$(echo "${OPENS:-}" | $PY -c "import sys; print(','.join('{model=%r,kind=%r,amount=%s,near=%s}' % tuple(d.split(':')) for d in sys.stdin.read().strip().split(',') if d))")
bash $T cl $CL "_G.__cp=load('return '.._G.__cpbuf)() _G.__cpbuf=nil _G.__cpopt={probe=$([ "$MODE" = probe ] && echo true || echo false),probe_speed=${PROBE_SPEED:-2.0},opens={$DL},weather='${WEATHER:-EXTRASUNNY}'} return #_G.__cp.shots" 10 | grep -o '"result":[^,}]*'
FF=$(ls -d /c/Users/anton/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin | head -1)/ffmpeg.exe
if [ "$MODE" = run ]; then
  RAW="${OUT%.mp4}.raw.mkv"
  h=$(powershell -NoProfile -Command "(Get-Process FiveM_b3258_GTAProcess | ? MainWindowHandle -ne 0 | Select -First 1).MainWindowHandle.ToInt64()" | tr -d '\r')
  "$FF" -hide_banner -loglevel error -y -f gdigrab -framerate 30 -i hwnd=$h -c:v libx264 -preset veryfast -crf 16 -pix_fmt yuv420p -f matroska "$RAW" </dev/null >/dev/null 2>&1 &
  FPID=$!; sleep 1
fi
bash $T cl $CL "$(cat "$HERE/player.lua")" 10 | grep -o '"result":"[^"]*"\|"err[^}]*'
until bash $T cl $CL "return _G.__cprun" 5 | grep -q '"result":"done"'; do sleep 3; done
if [ "$MODE" = run ]; then
  sleep 1; powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='ffmpeg.exe'\" | ? { \$_.CommandLine -like '*$(basename "$RAW")*' } | % { Stop-Process -Id \$_.ProcessId -Force }"
  sleep 2; $PY "$HERE/campath_cut.py" "$FF" "$RAW" "$OUT"
else
  bash $T cl $CL "local o={} for _,h in ipairs(_G.__cphits or {}) do o[#o+1]=('shot %d t=%.1f %s at %.2f %.2f %.2f model %d'):format(h.shot,h.t,h.kind,h.x,h.y,h.z,h.model) end return #o==0 and 'CAMPATH_PROBE_CLEAN' or table.concat(o,' | ')" 10 | grep -o '"result":"[^"]*"' | tr '|' '\n'
fi
