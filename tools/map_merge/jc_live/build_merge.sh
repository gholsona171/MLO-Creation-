#!/bin/sh
# JC live merge (2026-11-12): every sc1 file justice_center shares with another pack, rebuilt from the game's newest vanilla file plus each
# author's own edit (vs the file that author started from). Run from jc_live_merge/. XML out in merged_xml/, logs in logs/.
set -u
T="py -3 -I tools/occl_variant_merge.py"; X=xml; O=merged_xml; mkdir -p $O logs; F=0
v() { echo "$X/vanilla__$1.ymap.xml"; }
# occl_00: JC + hood + Grove union (kq/gcom/Grimzy/hood lr_ cuts, already one file) + 17mov
for n in sc1_occl_00 hei_sc1_occl_00; do
  $T --target $(v $n) --out $O/$n.ymap.xml --author jc $X/src_jc__$n.ymap.xml $(v $n) --author hood $X/src_hood__$n.ymap.xml $(v $n) \
     --author grove_union $X/src_grove_union__lr_sc1_occl_00.ymap.xml $(v lr_sc1_occl_00) --author 17mov $X/src_17mov__lr_sc1_occl_00.ymap.xml $(v lr_sc1_occl_00) \
     > logs/occl_$n.txt || { echo FAIL $n; F=1; }; done
# occl_01: JC + hood (lr_: the hood's first cut vs vanilla and its round-2 cut vs the file it was cut from; sc1_/hei_: the hood's own cut files)
$T --target $(v lr_sc1_occl_01) --out $O/lr_sc1_occl_01.ymap.xml --author jc $X/src_jc__lr_sc1_occl_01.ymap.xml $(v lr_sc1_occl_01) \
   --author hood_v1 $X/src_hood_lr01_v1__lr_sc1_occl_01.ymap.xml $(v lr_sc1_occl_01) \
   --author hood_r2 $X/src_hood_lr01_r2__lr_sc1_occl_01.ymap.xml $X/src_hood_lr01_r2base__lr_sc1_occl_01.ymap.xml > logs/occl_lr_sc1_occl_01.txt || { echo FAIL lr01; F=1; }
for n in sc1_occl_01 hei_sc1_occl_01; do
  $T --target $(v $n) --out $O/$n.ymap.xml --author jc $X/src_jc__$n.ymap.xml $(v $n) --author hood $X/src_hood__$n.ymap.xml $(v $n) > logs/occl_$n.txt || { echo FAIL $n; F=1; }; done
# occl_03: JC + 17mov + amb-hospital (amb's edit from its lr_ file; its hei_ file is a renamed lr_ copy)
for n in lr_sc1_occl_03 hei_sc1_occl_03 sc1_occl_03; do
  $T --target $(v $n) --out $O/$n.ymap.xml --author jc $X/src_jc__$n.ymap.xml $(v $n) --author 17mov $X/src_17mov__lr_sc1_occl_03.ymap.xml $(v lr_sc1_occl_03) \
     --author amb_hospital $X/src_amb_hospital__lr_sc1_occl_03.ymap.xml $(v lr_sc1_occl_03) > logs/occl_$n.txt || { echo FAIL $n; F=1; }; done
# entity ymaps (entities by guid, car generators by position)
M="py -3 -I tools/merge_ymap_vanilla.py"
$M $(v lr_sc1_rd) $O/lr_sc1_rd.ymap.xml $X/src_17mov__lr_sc1_rd.ymap.xml $X/src_grimzy__lr_sc1_rd.ymap.xml $X/src_jc__lr_sc1_rd.ymap.xml > logs/ents_lr_sc1_rd.txt || { echo FAIL rd; F=1; }
$M $(v lr_sc1_rd_long_0) $O/lr_sc1_rd_long_0.ymap.xml $X/src_bennys__lr_sc1_rd_long_0.ymap.xml $X/src_jc__lr_sc1_rd_long_0.ymap.xml > logs/ents_lr_sc1_rd_long_0.txt || { echo FAIL long0; F=1; }
$M $(v lr_sc1_rd_long_1) $O/lr_sc1_rd_long_1.ymap.xml $X/src_17mov__lr_sc1_rd_long_1.ymap.xml $X/src_gcom__lr_sc1_rd_long_1.ymap.xml $X/src_jc__lr_sc1_rd_long_1.ymap.xml > logs/ents_lr_sc1_rd_long_1.txt || { echo FAIL long1; F=1; }
$M $(v lr_sc1_rd_strm_3) $O/lr_sc1_rd_strm_3.ymap.xml $X/src_17mov__lr_sc1_rd_strm_3.ymap.xml $X/src_jc__lr_sc1_rd_strm_3.ymap.xml > logs/ents_lr_sc1_rd_strm_3.txt || { echo FAIL strm3; F=1; }
[ $F = 0 ] && echo BUILD_OK || echo BUILD_FAILED
