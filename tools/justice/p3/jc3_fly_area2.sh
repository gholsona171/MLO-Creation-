#!/bin/bash
# jc3_fly_area2.sh <out dir> : the area 2 fly-through - five eased segments (the camera never passes a closed door; cuts between rooms):
# the tower lobby, the L3 public corridor, courtroom 3A (in by the east aisle, over the bar, up to the bench, the jury box), the holding
# corridor, courtroom 5B (a slow sweep). Each segment via jc3_fly.sh, joined with ffmpeg, scaled to 960 px (crf 28). tc_release.sh at the end.
set -u; O=$1; mkdir -p "$O"; P=/c/Users/anton/Documents/Codex/JusticeCenter/work/p3
FF=$(ls -d /c/Users/anton/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin | head -1)/ffmpeg.exe
trap 'bash /c/C9Test/tc_release.sh >/dev/null' EXIT
PRE=8 bash $P/jc3_fly.sh "$O/s1_lobby.mp4" 1.8 "46.0 19.6 30.9" "32.0 19.8 30.7" "19.0 22.5 30.7" "17.2 38.0 31.0" "19.5 49.5 31.4" "26.0 48.5 31.4"
PRE=4 bash $P/jc3_fly.sh "$O/s2_corridor.mp4" 1.6 "15.2 19.4 37.8" "27.0 19.4 37.7" "40.0 19.6 37.8"
PRE=4 bash $P/jc3_fly.sh "$O/s3_courtroomA.mp4" 1.0 "29.9 23.4 38.1" "29.9 28.9 38.0" "26.6 29.5 37.9" "25.65 31.5 38.0" "25.65 36.4 38.4"
PRE=4 bash $P/jc3_fly.sh "$O/s4_holding.mp4" 1.2 "33.1 25.9 37.7" "31.95 27.6 37.7" "31.95 35.6 37.7"
PRE=4 LOOK="25.3,40.0,44.6" bash $P/jc3_fly.sh "$O/s5_courtroomB.mp4" 0.8 "30.5 23.4 47.2" "21.2 23.4 47.2"
for f in "$O"/s?_*.mp4; do                                               # trim each segment: 2 s camera hand-over, 1.5 s settle at the end
  hd=2.0; [[ "$f" == *s1_lobby* ]] && hd=6.5                                 # the first segment: ~5 s before the interior takes the still camera
  d=$("$FF" -i "$(cygpath -m "$f")" 2>&1 | grep -o "Duration: [0-9:.]*" | cut -d' ' -f2); t=$(py -3 -c "h,m,s='$d'.split(':');print(int(h)*3600+int(m)*60+float(s)-$hd-1.5)")
  "$FF" -hide_banner -loglevel error -y -ss $hd -i "$(cygpath -m "$f")" -t $t -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p "$(cygpath -m "${f%.mp4}_t.mp4")" </dev/null
done
for f in "$O"/s?_*_t.mp4; do echo "file '$(cygpath -m "$f")'"; done > "$O/list.txt"      # ffmpeg is a Windows program: Windows paths
"$FF" -hide_banner -loglevel error -y -f concat -safe 0 -i "$(cygpath -m "$O/list.txt")" -vf "scale=960:-2" -c:v libx264 -preset veryfast -crf 28 -pix_fmt yuv420p "$(cygpath -m "$O/area2_flythrough.mp4")" </dev/null
ls -la "$O/area2_flythrough.mp4"
