#!/bin/bash
# Justice Center area 4 (Jail I, MLO jc_jail), offline: tests -> sweep plant -> Blender build -> metadata compile -> gates (each proven on a
# planted defect first) -> mlo-data -> plan drawings. Builds into out_next and swaps it in as out only when everything passed (jc-interiors'
# assemble copies from out at any time: it never sees a half-built folder). Touches only work/jail and shots/p4_jail*.
# Pass line BUILD_JAIL_PASS. Any gate failing stops the script (gate || exit: a gate inside a && chain under set -e does not stop it).
set -e -o pipefail; cd /c/Users/anton/Documents/Codex/JusticeCenter/work/jail; mkdir -p logs
B="/c/Users/anton/Documents/Codex/2026-10-10/our-goal-is-to-build-machine/outputs/MLO-Workshop/tools/blender-4.5.14-windows-x64/blender.exe"
export JJ_OUT=out_next; O=out_next
py -3 -m pytest tests -q | tail -1
JJ_PLANT=sweep "$B" -b --python jj_build.py > logs/jj_build_plant.log 2>&1 || true
grep -q 'ZFIGHT {"jc_jail_book"' logs/jj_build_plant.log || { echo 'SWEEP NOT PROVEN (the planted coplanar box was not found)'; exit 1; }; echo JJ_SWEEP_PLANT_FOUND; rm -rf out_plant
"$B" -b --python jj_build.py > logs/jj_build.log 2>&1; grep -o "JJ_BUILD_PASS.*" logs/jj_build.log || { grep -A12 Traceback logs/jj_build.log; exit 1; }
grep -q '"zfight": {}' logs/jj_build.log || { echo "SWEEP FAILED ($O/zfight.json)"; exit 1; }; echo JJ_SWEEP_PASS
py -3 jj_meta.py | grep JJ_META_PASS
mkdir -p $O/xml; powershell -NoProfile -ExecutionPolicy Bypass -File tools/local_xml.ps1 -In "$(cygpath -w $PWD/$O/jc_jail.ybn)" -Out "$(cygpath -w $PWD/$O/xml/jc_jail.ybn.xml)" > /dev/null
for g in roomids ground drive; do
  py -3 jj_gates.py $g --plant | tail -1 | grep PLANT_FOUND || { echo "$g GATE NOT PROVEN"; exit 1; }
  py -3 jj_gates.py $g | tail -1 | grep PASS || { py -3 jj_gates.py $g | tail -20; echo "$g GATE FAILED"; exit 1; }
done
py -3 jj_gap_check.py --plant 2>/dev/null | grep JJ_GAP_PLANT_FOUND || { echo 'GAP CHECK NOT PROVEN'; exit 1; }
py -3 jj_gap_check.py 2>/dev/null | tail -22 | grep -A21 JJ_GAP || true; py -3 -c "import json,sys; s=json.load(open('$O/gap_check.json'))['summary']; sys.exit(1 if s['gaps'] else 0)" || { echo 'GAP CHECK FAILED'; exit 1; }
py -3 jj_footprint.py --plant | grep JJ_FOOTPRINT_PLANT_FOUND || { echo 'FOOTPRINT NOT PROVEN'; exit 1; }
py -3 jj_footprint.py | tail -12 | grep -B11 JJ_FOOTPRINT_PASS || { py -3 jj_footprint.py | tail -20; echo 'FOOTPRINT FAILED'; exit 1; }
[ -f out/probe_sit.json ] && cp out/probe_*.json $O/ 2>/dev/null || true          # rig results carry over (mlo-data marks tested seats)
py -3 jj_mlo_data.py; py -3 jj_cams.py > /dev/null
py -3 jj_plandraw.py ../../shots/p4_jail_plan_L1.png ../../shots/p4_jail_plan_L2.png ../../shots/p4_jail_plan_L3.png ../../shots/p4_jail_plan_B1.png ../../shots/p4_jail_section.png
find . -size 0 -type f -delete
if [ -s HOLD_OUT ]; then echo "SWAP HELD (HOLD_OUT: jc-interiors is reading out/) - the new build waits in $O; run: bash swap_out.sh"; else rm -rf out_prev; [ -d out ] && mv out out_prev; mv $O out; echo "SWAPPED $O -> out"; fi
echo BUILD_JAIL_PASS
