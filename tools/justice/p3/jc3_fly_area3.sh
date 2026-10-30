#!/bin/bash
# jc3_fly_area3.sh <out dir> : the area 3 fly-through - the police lobby from the front doors to the counter, the public hall, the L2 open
# office, the B1 garage loop (down the IN ramp, round the deck past the workshop, up the OUT ramp); each segment via jc3_fly.sh (eased
# look-ahead), the first segment's 6.5 s camera hand-over and every segment's 1.5 s settle trimmed, joined, 960 px crf 28. Pass line FLY_DONE.
set -u; O=$1; mkdir -p "$O"; P=/c/Users/anton/Documents/Codex/JusticeCenter/work/p3
FF=$(ls -d /c/Users/anton/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin | head -1)/ffmpeg.exe
trap 'bash /c/C9Test/tc_release.sh >/dev/null' EXIT
PRE=8 bash $P/jc3_fly.sh "$O/s1_lobby.mp4" 1.6 "40.5 -24.5 30.6" "36.5 -24.0 30.4" "34.2 -21.5 30.3" "36.0 -14.0 30.5" "28.0 -10.5 30.4" "19.5 -9.5 30.4"
PRE=4 bash $P/jc3_fly.sh "$O/s2_office.mp4" 1.4 "12.0 -26.0 33.7" "12.2 -38.0 33.7" "19.5 -43.5 33.6"
PRE=4 bash $P/jc3_fly.sh "$O/s3_garage.mp4" 2.5 "44.2 -54.5 29.9" "38.0 -54.5 29.4" "30.0 -54.5 28.3" "21.5 -54.5 27.1" "15.0 -51.5 27.1" "13.0 -40.0 27.1" "14.0 -13.5 27.1" "30.0 -11.0 27.1" "41.0 -16.0 27.1" "41.0 -37.0 27.1" "24.0 -38.0 27.1" "17.0 -44.0 27.1" "22.0 -49.6 27.1" "40.0 -49.6 29.2" "44.2 -49.6 29.9"
for f in "$O"/s?_*.mp4; do
  case "$f" in *_t.mp4) continue;; esac
  hd=2.0; [[ "$f" == *s1_* ]] && hd=6.5
  d=$("$FF" -i "$(cygpath -m "$f")" 2>&1 | grep -o "Duration: [0-9:.]*" | cut -d' ' -f2); t=$(py -3 -c "h,m,s='$d'.split(':');print(int(h)*3600+int(m)*60+float(s)-$hd-1.5)")
  "$FF" -hide_banner -loglevel error -y -ss $hd -i "$(cygpath -m "$f")" -t $t -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p "$(cygpath -m "${f%.mp4}_t.mp4")" </dev/null
done
for f in "$O"/s?_*_t.mp4; do echo "file '$(cygpath -m "$f")'"; done > "$O/list.txt"
"$FF" -hide_banner -loglevel error -y -f concat -safe 0 -i "$(cygpath -m "$O/list.txt")" -vf "scale=960:-2" -c:v libx264 -preset veryfast -crf 28 -pix_fmt yuv420p "$(cygpath -m "$O/area3_flythrough.mp4")" </dev/null
[ -s "$O/area3_flythrough.mp4" ] && echo FLY_DONE "$O/area3_flythrough.mp4" || echo FLY_FAIL
