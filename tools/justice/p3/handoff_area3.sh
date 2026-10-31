#!/bin/bash
# handoff_area3.sh [step ...] : the Police HQ + B1 garage rig tests, for main to run (Antonio 2026-10-29: agents do not touch the rig).
# Run AFTER the deploy (work/assemble.sh, its deploy check passing) and tc_restart.sh. Each step prints one line "STEP <name> PASS|FAIL ..."
# and leaves its evidence under shots/p3_area3_rig/ (json results, videos, shots). With no arguments every step runs in this order:
#   selftest gdrive_selftest (each roll-up's read-back reads shut / open / shut through the door system; a keyed car moves >= 2 m)
#   control  gdrive_control (the drive method proven: the open IN lane arrives with 0 impacts, a planted run into stone does not arrive)
#   models   every room drawable registered (planted unstreamed name reads false)
#   rooms    every room's key in game (plaza control = no interior)
#   doors    every door both ways (police + area 2; the garage roll-ups are the drive test)
#   lifts    both banks on screen, the secure bank incl. jc-jail's B1 stop
#   walks    the police routes: galleria link -> hall -> lobby, staff corridor -> stair, B1 garage -> stair
#   drive    police car, recorded: both roll-ups opened by the door system (as the buyer's lock system will), in through the IN door,
#            down, the loop, a bay, out by the OUT ramp; 0 impacts, each door read open at the car, shut + released after
#   shots    13:00 + 23:00 of every area 3 view (lobby, counter, office, interview mirror, observation glass, garage, workshop, ramp, doors)
#   fly      the fly-through (jc3_fly_area3.sh)
# Every step releases the camera at the end (tc_release.sh); nothing here restarts the server.
J=/c/Users/anton/Documents/Codex/JusticeCenter; P=$J/work/p3; O=$J/shots/p3_area3_rig; mkdir -p "$O"; cd "$P"
STEPS="${*:-selftest control models rooms doors lifts walks drive shots fly}"   # patrol cars only: the van uses Jail I's sally port (Antonio 2026-10-30)   # no sit tests: client builds (Antonio 2026-10-30)
probe() {   # probe <name> <jc3_probe function...>: the probe's own PASS / FAIL line is the verdict; its json is kept
  local n=$1; shift; py -3 jc3_probe.py "$@" > "$O/$n.log" 2>&1
  for f in "$@"; do cp out/probe_$f.json "$O/" 2>/dev/null; done
  if grep -q "_FAIL" "$O/$n.log" || ! grep -q "_PASS" "$O/$n.log"; then echo "STEP $n FAIL (see $O/$n.log)"; else echo "STEP $n PASS"; fi
}
for s in $STEPS; do case $s in
  selftest) probe selftest gdrive_selftest ;;
  control) probe control gdrive_control ;;
  models)  probe models models ;;
  rooms)   probe rooms rooms ;;
  doors)   probe doors doors2 ;;
  lifts)   probe lifts lifts ;;
  walks)   probe walks walk3 ;;
  drive)   RECDIR=jc_p3 bash /c/C9Test/rec.sh start area3_drive_car > /dev/null; probe drive gdrive; RECDIR=jc_p3 bash /c/C9Test/rec.sh stop > /dev/null 2>&1
           cp /c/C9Test/videos/jc_p3/area3_drive_car.mp4 "$O/" 2>/dev/null ;;
  shots)   rm -f "$O/shots"/*.png; (cd $J/work && CAMS=$P/cams_area3.txt bash jc_pair.sh "$O/shots" night > "$O/shots.log" 2>&1)
           n=$(ls "$O/shots"/*.png 2>/dev/null | wc -l); want=$(( $(grep -c . $P/cams_area3.txt) * 2 )); [ "$n" -ge "$want" ] && echo "STEP shots PASS ($n of $want images: $O/shots - mirror: p3_a3_interview, glass: p3_a3_observe)" || echo "STEP shots FAIL ($n of $want images)" ;;
  fly)     bash $P/jc3_fly_area3.sh "$O/video" > "$O/fly.log" 2>&1; grep -q FLY_DONE "$O/fly.log" && echo "STEP fly PASS $O/video/area3_flythrough.mp4" || echo "STEP fly FAIL" ;;
  *) echo "STEP $s FAIL (unknown step)" ;;
esac; bash /c/C9Test/tc_release.sh > /dev/null 2>&1; done
