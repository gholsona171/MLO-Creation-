#!/bin/bash
# jj_rec.sh <out.mp4> <max seconds> <command...> : records client 1's game window (gameplay camera, what a player sees) with ffmpeg while
# the command runs (a probe walk / drive / lift ride) and stops when it ends. ffmpeg cannot be asked to quit cleanly from Git bash
# (stdin is not its console), so it writes a FRAGMENTED mp4 (every keyframe, once a second, closes a fragment): stopped at any moment the
# file is valid up to its last fragment. It is then remuxed to a plain mp4 (faststart) and checked with ffprobe: a recording that does not
# finalise (no duration, or under 2 s) fails HERE (2026-10-29: a killed matroska recording logged "File ended prematurely").
# zerolatency + flush_packets: nothing waits in the encoder / file buffers. Proven offline: a testsrc recording hard-killed at 6 s
# remuxed to a valid 6.0 s mp4 (without the flags the hard kill left an unreadable file).
# Exits with the command's status, or 3 when the recording itself failed.
OUT=$1; MAX=$2; shift 2
BIN=$(ls -d /c/Users/anton/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin | head -1); FF=$BIN/ffmpeg.exe; FPR=$BIN/ffprobe.exe
h=$(powershell -NoProfile -Command "(Get-Process FiveM_b3258_GTAProcess | ? MainWindowHandle -ne 0 | Select -First 1).MainWindowHandle.ToInt64()")
[ -n "$h" ] || { echo "REC_FAIL no game window"; exit 3; }
RAW="$OUT.frag.mp4"; rm -f "$RAW"
"$FF" -hide_banner -loglevel error -y -f gdigrab -framerate 25 -i hwnd=$h -t $MAX -vf "scale=1280:-2" -c:v libx264 -preset veryfast -tune zerolatency -crf 23 -g 25 -flush_packets 1 \
      -pix_fmt yuv420p -movflags +frag_keyframe+empty_moov+default_base_moof "$RAW" </dev/null &
FPID=$!; sleep 1
"$@"; RC=$?
sleep 2; kill $FPID 2>/dev/null; wait $FPID 2>/dev/null
"$FF" -hide_banner -loglevel error -y -i "$RAW" -c copy -movflags +faststart "$OUT" && rm -f "$RAW"
D=$("$FPR" -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null)
if [ -z "$D" ] || [ "$(py -3 -c "print(1 if float('${D:-0}') >= 2.0 else 0)")" != 1 ]; then echo "REC_FAIL $OUT (duration '$D')"; exit 3; fi
echo "REC_OK $OUT (${D%.*} s, command exit $RC)"; exit $RC
