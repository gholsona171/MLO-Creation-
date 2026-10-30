#!/bin/bash
# jj_rig_tests.sh <test> : the Jail I rig tests, one per call, unattended; every test ends with ONE line  JJ_TEST <name> PASS|FAIL ...
# Run by main (Antonio 2026-10-29: agents do not test on the rig), under the rig lock, after jc-interiors' deploy:
#   deploy   the live resource holds exactly this build (hash check, proven on a planted stale file first)        - run FIRST, always
#   rooms    rooms + models probes (control: the street is no interior; a planted unstreamed model name reads false)
#   doors    every door (50) walked through both ways
#   sit      all 91 seats (scenario at the sit point) + the sit sheet (clones seated, photos -> shots/p4_jail_sit_sheet.jpg)
#   walks    the intake walk + up to the cell block and the tier, recorded -> shots/p4_jail_video/p4_jail_walks.mp4
#   drive    drive_plant (a car 4.5 m off the line must hit the wall) then police, police3, policet in and out, recorded
#   lift     the secure lift B1 -> L3 -> B1 on screen ([E] + the ox_lib menu); needs the B1 stop in lifts.json
#   route    the prisoner's whole way sally port -> ... -> tunnel -> lift -> L3 -> defendant door, recorded
#   fly      both fly-throughs (doors opened for filming, closed after) -> shots/p4_jail_video/p4_jail_fly_*.mp4
#   pairs    13:00 / 23:00 shots of every view + the pair sheet shots/p4_jail_pairs.jpg
set -o pipefail; JL=/c/Users/anton/Documents/Codex/JusticeCenter/work/jail; S=/c/Users/anton/Documents/Codex/JusticeCenter/shots; cd $JL
V=$S/p4_jail_video; mkdir -p $V
res() { echo "JJ_TEST $1 $2 $3"; [ "$2" = PASS ]; }
trap 'bash /c/C9Test/tc_release.sh > /dev/null 2>&1' EXIT
case "$1" in
deploy)  py -3 jj_deploy_check.py --plant | grep -q JJ_DEPLOY_PLANT_FOUND || { res deploy FAIL "the check did not find its planted stale file"; exit 1; }
         out=$(py -3 jj_deploy_check.py); echo "$out" | tail -15
         echo "$out" | grep -q JJ_DEPLOY_PASS && res deploy PASS "$(echo "$out" | tail -1)" || res deploy FAIL "live files differ from work/jail/out: do not test, redeploy" ;;
rooms)   py -3 jj_probe.py rooms models > logs/rig_rooms.log 2>&1; grep -o "PROBE_[A-Z_]*" logs/rig_rooms.log
         grep -q PROBE_ROOMS_PASS logs/rig_rooms.log && grep -q PROBE_MODELS_PASS logs/rig_rooms.log && res rooms PASS "10 rooms + models" || res rooms FAIL "see work/jail/logs/rig_rooms.log, out/probe_rooms.json, out/probe_models.json" ;;
doors)   py -3 jj_probe.py doors > logs/rig_doors.log 2>&1
         grep -q PROBE_DOORS_PASS logs/rig_doors.log && res doors PASS "50/50 both ways" || res doors FAIL "see out/probe_doors.json (a / b = the two directions)" ;;
sit)     py -3 jj_probe.py sit > logs/rig_sit.log 2>&1; P=$?
         py -3 jj_sitshots.py $S/p4_jail_sit > logs/rig_sitshots.log 2>&1; grep "SITTERS\|SITSHOTS" logs/rig_sitshots.log
         py -3 jj_mlo_data.py > /dev/null                                      # marks the passed seats tested in mlo-data
         n=$(py -3 -c "import json; r=json.load(open('out/probe_sit.json'))['seats']; print(sum(x['ok'] for x in r), 'of', len(r))")
         [ $P = 0 ] && grep -q SITSHOTS logs/rig_sitshots.log && res sit PASS "$n seats; sheet shots/p4_jail_sit_sheet.jpg" || res sit FAIL "$n seats pass; see out/probe_sit.json" ;;
walks)   bash jj_rec.sh $V/p4_jail_walks.mp4 1200 py -3 jj_probe.py walk > logs/rig_walks.log 2>&1
         grep -q PROBE_WALK_PASS logs/rig_walks.log && res walks PASS "video $V/p4_jail_walks.mp4" || res walks FAIL "see out/probe_walk.json" ;;
drive)   py -3 jj_probe.py drive_plant > logs/rig_drive_plant.log 2>&1
         grep -q PROBE_DRIVE_PLANT_PASS logs/rig_drive_plant.log || { res drive FAIL "the planted off-line drive did not collide: the check is not proven"; exit 1; }
         bash jj_rec.sh $V/p4_jail_drive_test.mp4 900 py -3 jj_probe.py drive > logs/rig_drive.log 2>&1
         grep -q PROBE_DRIVE_PASS logs/rig_drive.log && res drive PASS "3 vehicles in and out, 0 collisions; video $V/p4_jail_drive_test.mp4" || res drive FAIL "see out/probe_drive.json (collisions / stop_nose_u)" ;;
lift)    bash jj_rec.sh $V/p4_jail_lift_b1.mp4 300 py -3 jj_probe.py lift_b1 > logs/rig_lift.log 2>&1
         grep -q PROBE_LIFT_B1_PASS logs/rig_lift.log && res lift PASS "B1 -> L3 -> B1" || res lift FAIL "see out/probe_lift_b1.json / logs/rig_lift.log" ;;
route)   bash jj_rec.sh $V/p4_jail_prisoner_route.mp4 1500 py -3 jj_probe.py route > logs/rig_route.log 2>&1
         grep -q PROBE_ROUTE_PASS logs/rig_route.log && res route PASS "video $V/p4_jail_prisoner_route.mp4" || res route FAIL "see out/probe_route.json" ;;
fly)     py -3 jj_doorctl.py open || { res fly FAIL "doors could not be opened"; exit 1; }
         HOUR=13 bash jj_fly.sh $V/p4_jail_fly_intake.mp4 fly_route.txt; HOUR=13 bash jj_fly.sh $V/p4_jail_fly_cellblock.mp4 fly_block.txt
         py -3 jj_doorctl.py close
         ok=1; for f in $V/p4_jail_fly_intake.mp4 $V/p4_jail_fly_cellblock.mp4; do [ -s "$f" ] && [ $(stat -c %s "$f") -gt 1000000 ] || ok=0; done
         [ $ok = 1 ] && res fly PASS "videos in $V (review the frames: py -3 MLO-Creation/tools/video_review.py)" || res fly FAIL "a fly video is missing or empty" ;;
pairs)   CAMS=$JL/out/cams_jail.txt bash ../jc_pair.sh $S/p4_jail_game night > logs/rig_pairs.log 2>&1
         py -3 jj_pairs.py $S/p4_jail_game $S/p4_jail_pairs.jpg > logs/rig_pairsheet.log 2>&1
         grep -q PAIRS logs/rig_pairsheet.log && res pairs PASS "$(cat logs/rig_pairsheet.log)" || res pairs FAIL "a shot is missing: see logs/rig_pairs.log" ;;
*) echo "usage: jj_rig_tests.sh deploy|rooms|doors|sit|walks|drive|lift|route|fly|pairs"; exit 2 ;;
esac
