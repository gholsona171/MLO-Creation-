#!/bin/bash
# Justice Center phase 3 (offline): tests -> Blender build -> metadata compile -> gates (each proven on a planted defect first) ->
# mlo-data -> plan drawing. Nothing here touches work/p2, the resource or the rig. Pass line BUILD_P3_PASS.
set -e -o pipefail; cd /c/Users/anton/Documents/Codex/JusticeCenter/work/p3; mkdir -p logs
B="/c/Users/anton/Documents/Codex/2026-10-10/our-goal-is-to-build-machine/outputs/MLO-Workshop/tools/blender-4.5.14-windows-x64/blender.exe"
py -3 -m pytest tests -q | tail -1
"$B" -b --python jc3_build.py > logs/jc3_build.log 2>&1; grep -o "JC3_BUILD_PASS.*" logs/jc3_build.log || { grep -A12 Traceback logs/jc3_build.log; exit 1; }
grep -q '"zfight": {}' logs/jc3_build.log || { echo 'SWEEP FAILED (out/zfight.json)'; exit 1; }
py -3 jc3_meta.py | grep JC3_META_PASS
for f in jc_courts_galleria.ydr jc_courts.ybn; do powershell -NoProfile -ExecutionPolicy Bypass -File tools/local_xml.ps1 -In "$(cygpath -w $PWD/out/$f)" -Out "$(cygpath -w $PWD/out/xml/$f.xml)" > /dev/null; done
py -3 -c "import xml.etree.ElementTree as E; r=E.parse('out/xml/jc_courts.ybn.xml').getroot(); ids=[int(i.find('RoomID').get('value')) for m in r.iter('Materials') for i in m]; assert ids and min(ids)>=1, ids; print('ROOM_IDS_OK', sorted(set(ids)))"
py -3 jc3_gap_check.py --plant 2>/dev/null | grep JC3_GAP_PLANT_FOUND
py -3 jc3_gap_check.py 2>/dev/null | grep JC3_GAP_PASS
py -3 jc3_footprint.py --plant | grep JC3_FOOTPRINT_PLANT_FOUND
py -3 jc3_footprint.py | grep JC3_FOOTPRINT_PASS
py -3 jc3_mlo_data.py
py -3 jc3_plandraw.py "C:/Users/anton/Documents/Codex/JusticeCenter/shots/p3_area1_plan.png"
echo BUILD_P3_PASS
