#!/bin/bash
# lod_all.sh: the distance-model cut, end to end (wiped first): lod_list.py -> lod_extract.ps1 -> lod_cut.py on every extracted
# dictionary, 4 at a time. Output ../site/lodcut/*.ydd (only the dictionaries that changed).
cd "$(dirname "$0")"
B="/c/Users/anton/Documents/Codex/2026-10-10/our-goal-is-to-build-machine/outputs/MLO-Workshop/tools/blender-4.5.14-windows-x64/blender.exe"
rm -rf ../site/lodcut; mkdir -p ../site/lodcut
/c/Users/anton/AppData/Local/Programs/Python/Python313/python lod_list.py
powershell -NoProfile -ExecutionPolicy Bypass -File lod_extract.ps1 | cut -c1-200
ls ../vanilla/lod/*.ydd | xargs -n1 basename | sed 's/\.ydd$//' | xargs -P 4 -I{} sh -c "\"$B\" -b --python lod_cut.py -- {} 2>&1 | grep -E 'LOD_CUT_PASS|LOD_CUT_UNCHANGED|Traceback|Error:'"
