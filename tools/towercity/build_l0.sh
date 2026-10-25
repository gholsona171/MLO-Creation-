#!/bin/bash
# Rebuilds every LEVEL-0 output from source (the vanilla removal + the exterior clean-up), then assembles + deploys (DEPLOY=0: build
# the resource only, the rig is not touched; ASSEMBLE=0: level 0 only, no assemble - e.g. while another build owns work/l1 / l2). Never runs l1/l2/l3 builds: their outputs (work/l1, l2, east, l3, west, res, gar, site)
# are reused as they are.
#   ext_plan.py  -> plan/ext_cuts.json + plan/ext_build.json (the exterior rules: San Andreas branch, PARKING block, drives, pillar)
#   l0_cut.py    -> work/cut (every vanilla drawable cut by the lot / footprint outlines + the exterior rules), one model per process
#   l0_cut_lod.py-> work/lodcut (district LODs + the prop-combo SLOD1 / LOD models the lots cut through: l0_maps.py's partial list)
#   l0_col.py    -> work/col (every vanilla collision file), one file per process
#   lot_ground.py + l0_slab.py -> work/slab (the lot slab: dense edge on the ground outside, draped inside, paving)
#   ext_build.py + ext_meta.py -> work/extfix (our paving over the old drives / the PARKING block's footprint / the branch pit, props)
#   checks: tools/slab_edge_check.py (slab edge vs the ground outside it), the LOD partial list covered, cross_check.py
set -e; cd /c/Users/anton/Documents/Codex/TowerCity/work
B="/c/Users/anton/Documents/Codex/2026-10-10/our-goal-is-to-build-machine/outputs/MLO-Workshop/tools/blender-4.5.14-windows-x64/blender.exe"
mkdir -p logs
py -3 ext_plan.py
CUT="dt1_11_decal_01 dt1_11_dt1_details dt1_11_dt1_details2 dt1_11_dt1_details3 dt1_11_dt1_details4 dt1_11_dt1_details_b dt1_11_dt1_details_c
 dt1_11_dt1_plaza dt1_11_dt1_plaza_gr dt1_11_fount_decal dt1_11_fount_decalx dt1_11_fur00 dt1_11_fur00x dt1_11_fur00y dt1_11_fur01 dt1_11_fur02
 dt1_11_fur03 dt1_11_fur07 dt1_11_glue dt1_11_glue_b dt1_11_glue_c dt1_11_glue_d dt1_11_glue_e dt1_11_hedge dt1_11_hedge_d dt1_11_hedge_d2
 dt1_11_hedge_d2_a dt1_11_hedge_d2_b dt1_11_hedge_d3 dt1_11_hedge_d3_b dt1_11_hedge_d4 dt1_11_hedge_d4_b dt1_11_hedge_d_1 dt1_11_hedge_d_2
 dt1_12_ground1 dt1_rd1_r1_ovly_24 hei_dt1_11_dt1_plaza hei_dt1_11_dt1_plaza_gr hei_dt1_11_glue_e
 dt1_rd1_r1_08 dt1_rd1_r1_10 dt1_rd1_r1_ovly_15 dt1_rd1_r1_14 dt1_rd1_r1_ovly_00 dt1_rd1_fwy05
 dt1_rd1_fwy02 dt1_rd1_r2_fwy_ovly_02 dt1_rd1_r1_12 dt1_rd1_r1_ovly_23
 dt1_rd1_r1_19 dt1_rd1_r6_28 dt1_rd1_r1_13 dt1_rd1_r1_ovly_27 dt1_rd1_r1_09 dt1_rd1_r1_ovly_20 dt1_rd1_r1_27 dt1_rd1_fur6
 dt1_10_build1 dt1_10_build1_rail2"   # (last line: street models reaching into the lots, tools/ground_check.py)
py -3 -c "import json; p='l0_cut_result.json'; r=json.load(open(p)); r['cut']={}; json.dump(r, open(p, 'w'), indent=1)"   # rebuilt below
: > logs/l0_cut_all.log
for n in $CUT; do
  "$B" -b --python l0_cut.py -- $n > logs/l0_cut_one.log 2>&1
  grep -h -o "L0_CUT_EXT.*\|L0_CUT_PASS.*" logs/l0_cut_one.log >> logs/l0_cut_all.log || { echo "L0_CUT FAILED $n"; grep -A12 Traceback logs/l0_cut_one.log; exit 1; }
done
py -3 -c "
import json; p='l0_cut_result.json'; r=json.load(open(p)); gone=[k for k, v in r['cut'].items() if v[1] == 0]
for k in gone: r['cut'].pop(k)                    # nothing left: its entities are swapped to tc_empty (l0_maps.py), the model is not shipped
json.dump(r, open(p, 'w'), indent=1); print('L0_CUT', len(r['cut']), 'models shipped,', len(gone), 'fully removed')"
py -3 l0_maps.py | tee logs/l0_maps.log                                       # (the partial LOD list for the LOD cut below)
: > logs/l0_cut_lod_ext.log
for a in "dt1_lod_slod3_children.ydd" "dt1_lod_slod3.ydr" "dt1_lod_5_20_emissive_proxy_children.ydd" "dt1_lod_5_20_emissive_proxy.ydr" \
         "dt1_lod_6_20_emissive_proxy_children.ydd" "dt1_lod_6_20_emissive_proxy.ydr" "dt1_lod_6_21_emissive_proxy_children.ydd" "dt1_lod_6_21_emissive_proxy.ydr" \
         "dt1_lod_03_04_05_11_children.ydd dt1_props_combo0107_slod dt1_props_combo0108_slod dt1_props_combo0109_slod" \
         "dt1_lod_12_13_22_23_children.ydd dt1_props_combo0407_slod dt1_props_combo0412_slod" \
         "dt1_props_combo0407_slod_children.ydd dt1_props_combo0407_21_lod" \
         "dt1_rd1_r1f_slod1_children.ydd hash_d50b466a" "dt1_lod_rd_children.ydd dt1_rd1_r1f_slod1"          "dt1_10_slod_children.ydd hash_1977f283" "dt1_lod_01_02_09_10_children.ydd hash_0c19b59c"; do   # (last two: the footbridge's LOD + SLOD)   # (last two: the moved pillar's LOD + SLOD1)
  set -- $a; "$B" -b --python l0_cut_lod.py -- $a > logs/l0_cut_lod.log 2>&1
  grep -o "L0_LODCUT_PASS.*" logs/l0_cut_lod.log | cut -c1-160 || { echo "L0_CUT_LOD FAILED $1"; grep -A12 Traceback logs/l0_cut_lod.log; exit 1; }
  grep -o "L0_LODCUT_EXT.*" logs/l0_cut_lod.log >> logs/l0_cut_lod_ext.log
done
py -3 -c "
import json, re; L = open('logs/l0_cut_lod_ext.log').read(); bad = []
for f, want in (('dt1_rd1_r1f_slod1_children.ydd', 24), ('dt1_lod_rd_children.ydd', 12)):   # the pillar's faces in its LOD / SLOD1
    m = re.search(re.escape(f) + r' (\{.*\})', L); n = sum(v.get('P driveway pillar (LOD)', 0) for v in json.loads(m.group(1)).values()) if m else 0
    print('LOD_MOVE', f, n, 'faces moved'); bad += [f] if n != want else []
for f in ('dt1_10_slod_children.ydd', 'dt1_lod_01_02_09_10_children.ydd'):                # the footbridge's faces cut from its LOD / SLOD
    m = re.search(re.escape(f) + r' (\{.*\})', L); n = sum(v.get('F footbridge (LOD + SLOD)', 0) for v in json.loads(m.group(1)).values()) if m else 0
    print('LOD_CUT', f, n, 'footbridge faces cut'); bad += [f] if n == 0 else []
raise SystemExit(1 if bad else 0)" || { echo 'LOD MOVE FAILED: the moved pillar is not moved in its LOD / SLOD1 - nothing deployed'; exit 1; }
py -3 -c "
import json; P=json.load(open('l0_lod_partial.json'))
cov={'dt1_props_combo0107_slod','dt1_props_combo0108_slod','dt1_props_combo0109_slod','dt1_props_combo0407_slod','dt1_props_combo0412_slod','dt1_props_combo0407_21_lod'}
miss=sorted({p['archetype'] for p in P} - cov)
print('LOD_PARTIAL', len(P), 'entities, uncut:', miss); raise SystemExit(1 if miss else 0)" || { echo 'A LOD model the lots cut through is not cut (add it to the LOD cut list above)'; exit 1; }
: > logs/l0_col_all.log
for f in ../src/game/*.ybn; do n=$(basename $f .ybn)
  "$B" -b --python l0_col.py -- $n > logs/l0_col_one.log 2>&1
  grep -h -o "L0_COL_EXT.*\|L0_COL_PASS.*" logs/l0_col_one.log >> logs/l0_col_all.log || { echo "L0_COL FAILED $n"; grep -A12 Traceback logs/l0_col_one.log; exit 1; }
done
grep -h "L0_COL_EXT" logs/l0_col_all.log | grep -v "{}" || true
py -3 lot_ground.py
"$B" -b --python l0_slab.py > logs/l0_slab.log 2>&1; grep -c "L0_SLAB_PASS" logs/l0_slab.log > /dev/null || { grep -A12 Traceback logs/l0_slab.log; exit 1; }
"$B" -b --python ext_build.py > logs/ext_build.log 2>&1; grep -o "EXT_BUILD_PASS.*" logs/ext_build.log || { grep -A12 Traceback logs/ext_build.log; exit 1; }
grep -q 'ZFIGHT {}' logs/ext_build.log || { grep ZFIGHT logs/ext_build.log; echo 'EXT SWEEP FAILED: coplanar faces in the exterior paving - nothing deployed'; exit 1; }
py -3 ext_meta.py | grep "compile failures: \[\]" || { echo 'EXT_META FAILED'; exit 1; }
py -3 tools/slab_edge_check.py || { echo 'SLAB EDGE FAILED: the lot slab stands off the ground outside it (above) - nothing deployed'; exit 1; }
py -3 cross_check.py || { echo 'CROSS FAILED: two drawables share a visible surface (above) - nothing deployed'; exit 1; }
if [ "${ASSEMBLE:-1}" = 0 ]; then echo 'BUILD_L0_PASS (ASSEMBLE=0: level 0 built, nothing assembled or deployed)'; exit 0; fi
DEPLOY=0 bash assemble.sh                                                        # the resource first, nothing on the rig yet
py -3 tools/ground_check.py > logs/ground_check.log 2>&1 || { grep "GROUND_CHECK\|^    " logs/ground_check.log | head -40; echo 'GROUND CHECK FAILED: drawn ground and collision disagree (above) - nothing deployed'; exit 1; }
grep "GROUND_CHECK_PASS\|allowed" logs/ground_check.log
if [ "${DEPLOY:-1}" != 0 ]; then bash assemble.sh; fi
echo BUILD_L0_PASS
