#!/bin/bash
# Justice Center phases 1 + 2: rebuilds EVERY output (the block clearing, then the new complex's shells + LOD chain) from source, runs the
# gates, then assembles (+ deploys, DEPLOY=1).
# No patchwork: every step wipes its own output folder and rebuilds it from the game's files and the rules in these scripts.
#   lot_outline.py -> plan/lot_poly.json   (Rockstar's back-of-sidewalk line round the block, from his road models)
#   p1_slab.py     -> work/slab            (the lot slab: his sidewalk im_sidewalk012; collision; jc_empty)
#   p1_maps.py     -> work/maps            (every ymap of the block + the road ymaps: removals, LOD pass, car gens; jc_lot ytyp / ymap)
#   p1_col.py      -> work/col             (the block's collision emptied, the street files' old-block collision cut by the lot)
#   p1_cut_lod.py  -> work/lodcut          (SLOD2 sc1_lod_19 + road SLOD2s, SLOD3, emissive SLODs cut by the lot; prop-combo LODs by the inner lot)
#   p1_occl.ps1    -> work/occl            (occluders over the lot)
#   p1_lodlights.py-> work/lodlights       (distant LOD lights inside the lot -> z -1000)
#   p1_area.py     -> work/scripts         (area_clear.lua: AI off inside the lot)
#   PHASE 2 (p2/):
#   p2_tex.ps1     -> p2/tex_rs          (Rockstar's textures for the p2 recipes, read from the game)
#   p2_site.py     -> plan/p2_site.json  (podium, steps, lawn + sloped walk, bollards, walls, Portal line, props)
#   p2_build.py    -> p2/out             (every HD shell + _emi models, jc_site, jc_core, jc_ext_col.ybn, the sweep)
#   p2_lod.py      -> p2/out_lod         (per-building LODs, jc_slod1, jc_emi_lod, jc_emi_slod, the SLOD2/3 massing + ground plates)
#   p1_maps.py hooks the complex into the block's LOD tree (p2/p2_maps.py); p1_cut_lod.py --add puts the massing into SLOD2 / SLOD3
#   gates: the LOD partial list covered; p2/p2_gates.py (sweep + cross: no visible coplanar overlap anywhere); tools/ground_check.py
#   --plant must PROVE itself, then tools/ground_check.py must PASS (drawn vs collision, the new site included)
set -e -o pipefail; cd /c/Users/anton/Documents/Codex/JusticeCenter/work
B="/c/Users/anton/Documents/Codex/2026-10-10/our-goal-is-to-build-machine/outputs/MLO-Workshop/tools/blender-4.5.14-windows-x64/blender.exe"
mkdir -p logs
py -3 lot_outline.py
powershell -NoProfile -ExecutionPolicy Bypass -File p2/p2_tex.ps1 | tee logs/p2_tex.log; ! grep -q MISSING logs/p2_tex.log || { echo 'P2_TEX: a recipe texture is missing'; exit 1; }
py -3 p2/p2_site.py
"$B" -b --python p2/p2_build.py > logs/p2_build.log 2>&1; grep -o "P2_BUILD_PASS.\{0,300\}" logs/p2_build.log || { grep -A12 Traceback logs/p2_build.log; exit 1; }
"$B" -b --python p2/p2_lod.py > logs/p2_lod.log 2>&1; grep -o "P2_LOD_PASS.\{0,400\}" logs/p2_lod.log || { grep -A12 Traceback logs/p2_lod.log; exit 1; }
py -3 p2/p2_gates.py sweep cross --plant || { echo 'P2 SWEEP / CROSS FAILED - nothing deployed'; exit 1; }
"$B" -b --python p1_slab.py > logs/p1_slab.log 2>&1; grep -o "P1_SLAB_PASS.\{0,80\}" logs/p1_slab.log || { grep -A12 Traceback logs/p1_slab.log; exit 1; }
py -3 p1_maps.py | tee logs/p1_maps.log
rm -rf col; : > logs/p1_col_all.log
for f in ../src/game/*.ybn; do n=$(basename $f .ybn)
  "$B" -b --python p1_col.py -- $n > logs/p1_col_one.log 2>&1
  grep -h -o "P1_COL_PASS.*" logs/p1_col_one.log >> logs/p1_col_all.log || { echo "P1_COL FAILED $n"; grep -A12 Traceback logs/p1_col_one.log; exit 1; }
done
echo "P1_COL $(grep -c P1_COL_PASS logs/p1_col_all.log) files"
rm -rf lodcut; : > logs/p1_cut_lod_all.log
for a in "sc1_lod_slod4_children.ydd --add=sc1_lod_19 sc1_lod_19 sc1_lod_04_rd sc1_lod_05_rd" "sc1_lod_slod4.ydr --add=sc1_lod_slod4" "sc1_lod_emi_a_slod3.ydr" "sc1_lod_emi_a_slod3_children.ydd sc1_lod_emissive" \
         "sc1_lod_19_children.ydd --inner sc1_props_combo0504_slod sc1_props_combo0505_slod sc1_props_combo0506_slod" \
         "sc1_props_combo0504_slod_children.ydd --inner sc1_props_combo0504_01_lod sc1_props_combo0504_06_lod" \
         "sc1_props_combo0506_slod_children.ydd --inner sc1_props_combo0506_02_lod"; do
  set -- $a; "$B" -b --python p1_cut_lod.py -- $a > logs/p1_cut_lod.log 2>&1
  grep -o "P1_LODCUT_PASS.*" logs/p1_cut_lod.log | tee -a logs/p1_cut_lod_all.log | cut -c1-200 || { echo "P1_CUT_LOD FAILED $1"; grep -A12 Traceback logs/p1_cut_lod.log; exit 1; }
done
py -3 - <<'PY'
import json, re
P = json.load(open('p1_lod_partial.json')); L = open('logs/p1_cut_lod_all.log').read()
def joaat(t):
    h = 0
    for ch in t.lower().encode():
        h = (h + ch) & 0xFFFFFFFF; h = (h + (h << 10)) & 0xFFFFFFFF; h ^= h >> 6
    h = (h + (h << 3)) & 0xFFFFFFFF; h ^= h >> 11; h = (h + (h << 15)) & 0xFFFFFFFF; return h
cut = {}
for m in re.finditer(r'P1_LODCUT_PASS \S+ \S+ (\{.*\})', L): cut.update(json.loads(m.group(1)))
miss = sorted({p['archetype'] for p in P if not isinstance(cut.get('hash_%08x' % joaat(p['archetype'])) or cut.get(p['archetype']), list)})
must = ['sc1_lod_19', 'sc1_lod_slod4', 'sc1_lod_emi_a_slod3', 'sc1_lod_emissive']
dead0 = [n for n in must if not (cut.get(n) or cut.get('hash_%08x' % joaat(n)) or [0])[0]]
print('LOD_PARTIAL', len(P), 'entities; uncut:', miss, '| block SLODs with nothing cut:', dead0)
raise SystemExit(1 if miss or dead0 else 0)
PY
powershell -NoProfile -ExecutionPolicy Bypass -File p1_occl.ps1 > logs/p1_occl.log; grep -q P1_OCCL_DONE logs/p1_occl.log && ! grep -q Exception logs/p1_occl.log || { cat logs/p1_occl.log; exit 1; }; grep -v "not shipped" logs/p1_occl.log
py -3 p1_lodlights.py | tee logs/p1_lodlights.log
py -3 p1_area.py
DEPLOY=0 bash assemble.sh
py -3 tools/ground_check.py --plant > logs/ground_check_plant.log 2>&1; grep "GROUND_CHECK_PLANT\|plant:" logs/ground_check_plant.log || { tail -20 logs/ground_check_plant.log; echo 'GROUND CHECK NOT PROVEN - nothing deployed'; exit 1; }
py -3 tools/ground_check.py --no-dump > logs/ground_check.log 2>&1 || { grep "GROUND_CHECK\|^    " logs/ground_check.log | head -40; echo 'GROUND CHECK FAILED: drawn ground and collision disagree (above) - nothing deployed'; exit 1; }
grep "GROUND_CHECK" logs/ground_check.log
if [ "${DEPLOY:-1}" != 0 ]; then bash assemble.sh; fi
echo BUILD_P1_PASS
