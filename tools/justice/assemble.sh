#!/bin/bash
# Justice Center: rebuilds resource/justice_center from the work outputs only (never edited by hand), then (DEPLOY=1, the default) copies it
# to the C9Test rig. DEPLOY=0: the resource only, the rig is not touched. Phase 1 = the cleared Davis block (sc1_19).
set -e; DEPLOY=${DEPLOY:-1}; J="/c/Users/anton/Documents/Codex/JusticeCenter"; cd "$J"
R=resource/justice_center; rm -rf $R; mkdir -p $R/stream
cp work/maps/bin/* work/col/*.ybn work/slab/jc_lot.ydr work/slab/jc_lot_col.ybn work/slab/jc_empty.ydr work/lodcut/* work/occl/* work/lodlights/bin/* $R/stream/
cp work/scripts/area_clear.lua $R/
cat > $R/fxmanifest.lua <<'MAN'
fx_version 'cerulean'
game 'gta5'
author 'Justice Center MLO'
description 'Justice Center, phase 1: the Davis block (sc1_19 - the courts tower, library, Davis sheriff station, car park, plaza) cleared to one flat lot.'
this_is_a_map 'yes'
data_file 'DLC_ITYP_REQUEST' 'stream/jc_lot.ytyp'
client_script 'area_clear.lua'   -- the old block's traffic lanes, walkable ground, scenarios and car generators are off inside the lot
MAN
find $R -size 0 -type f -delete
echo "files: $(ls $R/stream | wc -l)  size: $(du -sh $R | cut -f1)"
if [ "$DEPLOY" = 0 ]; then echo "built (DEPLOY=0: the rig was not touched)"; exit 0; fi
D="/c/C9Test/live/resources/[localtest]/justice_center"; rm -rf "$D"; cp -r $R "$D"
grep -q "^ensure justice_center" /c/C9Test/live/server.local.cfg || printf 'ensure justice_center   # [local test] Justice Center (Documents\Codex\JusticeCenter), phase 1: the Davis block cleared\n' >> /c/C9Test/live/server.local.cfg
echo "deployed to $D (restart the rig with tc_restart.sh)"
