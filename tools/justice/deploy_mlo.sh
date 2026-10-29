#!/bin/bash
# deploy_mlo.sh jail : redeploy ONE MLO's build into the last full (gated) deploy, without touching the others - for when that MLO's
# owner needs its newest build on the rig while the rest of the resource is mid-build. Its files are swapped in the live resource and in
# resource/ (kept equal), the one _manifest.ymf re-merged (work/tools/merge_manifest.py), its stream gate run, and the deploy check must
# show its live files hash-equal to its build (tools/deploy_check.py, proven on a plant first). Run under the rig lock; restart after.
set -e; M=$1; J="/c/Users/anton/Documents/Codex/JusticeCenter"; cd "$J"
[ "$M" = jail ] || { echo "only 'jail' is wired"; exit 1; }
[ -f work/jail/out/bin/jc_jail.ytyp ] && [ -f work/jail/out/interior.json ] || { echo 'jail: work/jail/out not built'; exit 1; }
LIVE="/c/C9Test/live/resources/[localtest]/justice_center"; R=resource/justice_center
for D in "$LIVE" "$R"; do
  rm -f "$D"/stream/jc_jail*.ydr "$D"/stream/jc_jail.ybn "$D"/stream/jc_jail.ytyp "$D"/stream/jc_jail_milo_.ymap "$D"/stream/jc_jail_ext.ymap
  cp work/jail/out/bin/jc_jail.ytyp work/jail/out/bin/jc_jail_milo_.ymap work/jail/out/bin/jc_jail_ext.ymap work/jail/out/jc_jail_*.ydr work/jail/out/jc_jail.ybn "$D"/stream/
  cp work/jail/out/mlo-data/jc_jail.json "$D"/mlo-data/
done
py -3 work/tools/merge_manifest.py work/out_manifest work/p3/out/interior.json work/jail/out/interior.json || { echo 'MANIFEST MERGE FAILED'; exit 1; }
cp work/out_manifest/bin/_manifest.ymf "$LIVE"/stream/; cp work/out_manifest/bin/_manifest.ymf "$R"/stream/
py -3 work/jail/jj_stream_check.py "$(cygpath -w "$LIVE/stream")" --plant && py -3 work/jail/jj_stream_check.py "$(cygpath -w "$LIVE/stream")" || { echo 'JAIL STREAM GATE FAILED'; exit 1; }
py -3 work/tools/deploy_check.py "$(cygpath -w "$LIVE")" jail --plant && py -3 work/tools/deploy_check.py "$(cygpath -w "$LIVE")" jail || { echo 'DEPLOY CHECK FAILED'; exit 1; }
echo "DEPLOY_MLO_DONE $M (restart the rig with tc_restart.sh)"
