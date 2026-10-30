#!/bin/bash
# Justice Center: rebuilds resource/justice_center from the work outputs only (never edited by hand), then (DEPLOY=1, the default) copies it
# to the C9Test rig. DEPLOY=0: the resource only, the rig is not touched. Phase 1 = the cleared Davis block (sc1_19).
set -e; DEPLOY=${DEPLOY:-1}; J="/c/Users/anton/Documents/Codex/JusticeCenter"; cd "$J"
R=resource/justice_center; rm -rf $R; mkdir -p $R/stream
cp work/maps/bin/* work/col/*.ybn work/slab/jc_lot.ydr work/slab/jc_lot_col.ybn work/slab/jc_empty.ydr work/lodcut/* work/occl/* work/lodlights/bin/* $R/stream/
cp work/p2/out/*.ydr work/p2/out/jc_ext_col.ybn work/p2/out_lod/*.ydr $R/stream/            # phase 2: the complex's shells + LOD chain
cp work/scripts/area_clear.lua $R/
# phase 3: the interiors (MLO jc_courts: every room's drawable) - built by work/p3/build_p3.sh; the stream gate must prove itself, then pass
cp work/p3/out/bin/jc_courts.ytyp work/p3/out/bin/jc_courts_milo_.ymap work/p3/out/jc_courts_*.ydr work/p3/out/jc_courts.ybn $R/stream/
# area 4: Jail I (MLO jc_jail), built by jc-jail in work/jail (numbers: work/jail/jj_hooks.ASSEMBLE). Only when its build is there; its
# own stream gate must prove itself, then pass (the folder is wiped while build_jail.sh runs: a partial one fails the gate)
JAIL=0; INTS="work/p3/out/interior.json"
if [ -f work/jail/out/bin/jc_jail.ytyp ] && [ -f work/jail/out/interior.json ]; then
  cp work/jail/out/bin/jc_jail.ytyp work/jail/out/bin/jc_jail_milo_.ymap work/jail/out/bin/jc_jail_ext.ymap work/jail/out/jc_jail_*.ydr work/jail/out/jc_jail.ybn $R/stream/
  py -3 work/jail/jj_stream_check.py $R/stream --plant || { echo 'JAIL STREAM GATE NOT PROVEN - nothing deployed'; exit 1; }
  py -3 work/jail/jj_stream_check.py $R/stream || { echo 'JAIL STREAM GATE FAILED - nothing deployed'; exit 1; }
  JAIL=1; INTS="$INTS work/jail/out/interior.json"
else echo 'jail: work/jail/out not built - Jail I not in this resource'; fi
# the resource's one _manifest.ymf: every interior's INTERIOR_DATA entry
py -3 work/tools/merge_manifest.py work/out_manifest $INTS || { echo 'MANIFEST MERGE FAILED - nothing deployed'; exit 1; }
cp work/out_manifest/bin/_manifest.ymf $R/stream/
py -3 work/p3/jc3_stream_check.py $R/stream --plant || { echo 'STREAM GATE NOT PROVEN - nothing deployed'; exit 1; }
py -3 work/p3/jc3_stream_check.py $R/stream || { echo 'STREAM GATE FAILED - nothing deployed'; exit 1; }
mkdir -p $R/mlo-data; cp work/p3/out/mlo-data/*.json $R/mlo-data/
[ $JAIL = 1 ] && cp work/jail/out/mlo-data/jc_jail.json $R/mlo-data/
cp work/p3/scripts/lifts.lua work/p3/out/lifts.json $R/                                  # the courts tower's elevators (ox_lib menu)
cat > $R/fxmanifest.lua <<'MAN'
fx_version 'cerulean'
game 'gta5'
author 'Justice Center MLO'
description 'Justice Center (Davis block sc1_19): phase 1 the block cleared, phase 2 the exterior shells of the courts tower, atrium, police HQ, Jail I, Jail II, skybridges, plaza, lawn and the LOD chain; phase 3 the interiors (the atrium galleria: entrance and security checkpoint).'
this_is_a_map 'yes'
data_file 'DLC_ITYP_REQUEST' 'stream/jc_lot.ytyp'
data_file 'DLC_ITYP_REQUEST' 'stream/jc_ext.ytyp'
data_file 'DLC_ITYP_REQUEST' 'stream/jc_courts.ytyp'
files { 'mlo-data/*.json', 'lifts.json' }
shared_script '@ox_lib/init.lua'
client_script 'lifts.lua'       -- the courts tower's elevators: fade between the same cab on two floors
dependency 'ox_lib'
client_script 'area_clear.lua'   -- the old block's traffic lanes, walkable ground, scenarios and car generators are off inside the lot
MAN
[ $JAIL = 1 ] && printf "data_file 'DLC_ITYP_REQUEST' 'stream/jc_jail.ytyp'
" >> $R/fxmanifest.lua
find $R -size 0 -type f -delete
echo "files: $(ls $R/stream | wc -l)  size: $(du -sh $R | cut -f1)"
if [ "$DEPLOY" = 0 ]; then echo "built (DEPLOY=0: the rig was not touched)"; exit 0; fi
D="/c/C9Test/live/resources/[localtest]/justice_center"; rm -rf "$D"; cp -r $R "$D"
MLOS="courts"; [ $JAIL = 1 ] && MLOS="courts jail"                        # every MLO's live stream files hash-equal to its build (proven on a plant)
py -3 work/tools/deploy_check.py "$(cygpath -w "$D")" $MLOS --plant || { echo 'DEPLOY CHECK NOT PROVEN'; exit 1; }
py -3 work/tools/deploy_check.py "$(cygpath -w "$D")" $MLOS || { echo 'DEPLOY CHECK FAILED: the live resource is not the build'; exit 1; }
grep -q "^ensure justice_center" /c/C9Test/live/server.local.cfg || printf 'ensure justice_center   # [local test] Justice Center (Documents\Codex\JusticeCenter), phase 1: the Davis block cleared\n' >> /c/C9Test/live/server.local.cfg
echo "deployed to $D (restart the rig with tc_restart.sh)"
