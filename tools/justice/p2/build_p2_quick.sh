#!/bin/bash
# Justice Center phase 2, quick rebuild while iterating (the full chain stays work/build_p1.sh, which must pass before anything is
# reported): p2_site -> p2_build -> gates -> p1_maps (the LOD hooks + site ymap) -> assemble (DEPLOY as given) -> ground check.
set -e -o pipefail; cd /c/Users/anton/Documents/Codex/JusticeCenter/work
B="/c/Users/anton/Documents/Codex/2026-10-10/our-goal-is-to-build-machine/outputs/MLO-Workshop/tools/blender-4.5.14-windows-x64/blender.exe"
py -3 p2/p2_site.py
"$B" -b --python p2/p2_build.py > logs/p2_build.log 2>&1; grep -o "P2_BUILD_PASS.\{0,300\}" logs/p2_build.log || { grep -A12 Traceback logs/p2_build.log; exit 1; }
[ "${LOD:-0}" = 1 ] && { "$B" -b --python p2/p2_lod.py > logs/p2_lod.log 2>&1; grep -o "P2_LOD_PASS.\{0,100\}" logs/p2_lod.log || { grep -A12 Traceback logs/p2_lod.log; exit 1; }; }
py -3 p2/p2_gates.py sweep cross --plant
py -3 p1_maps.py | tail -3
DEPLOY=0 bash assemble.sh
py -3 tools/ground_check.py --no-dump > logs/ground_check.log 2>&1 || { grep -A10 "MISMATCH\|NOCOL\|HOLE" logs/ground_check.log | head -40; echo 'GROUND CHECK FAILED'; exit 1; }
grep GROUND_CHECK_PASS logs/ground_check.log
[ "${DEPLOY:-0}" = 1 ] && bash assemble.sh
echo BUILD_P2_QUICK_PASS
