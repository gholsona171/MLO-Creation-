#!/bin/bash
# jj_rec.sh <out.mp4> <max seconds> <command...> : records client 1's game window (gameplay camera, what a player sees) with ffmpeg while
# the command runs (a probe walk / drive / lift ride), stops when the command ends. Used for the walk, drive and lift clips.
OUT=$1; MAX=$2; shift 2
FF=$(ls -d /c/Users/anton/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin | head -1)/ffmpeg.exe
h=$(powershell -NoProfile -Command "(Get-Process FiveM_b3258_GTAProcess | ? MainWindowHandle -ne 0 | Select -First 1).MainWindowHandle.ToInt64()")
[ -n "$h" ] || { echo "REC: no game window"; exit 1; }
"$FF" -hide_banner -loglevel error -y -f gdigrab -framerate 25 -i hwnd=$h -t $MAX -vf "scale=1280:-2" -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p -f matroska "$OUT.mkv" </dev/null &
FP=$!; sleep 1
"$@"; RC=$?
sleep 1; kill $FP 2>/dev/null; wait $FP 2>/dev/null
"$FF" -hide_banner -loglevel error -y -i "$OUT.mkv" -c copy "$OUT" && rm -f "$OUT.mkv"      # a killed recording: matroska stays readable, remux to mp4
echo "REC $OUT (command exit $RC)"; exit $RC
