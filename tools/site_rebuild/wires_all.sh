#!/bin/bash
# wires_all.sh: every vanilla wire model over the site through wires.py (positions: site_scan.ps1, ../site/wide_scan.tsv). Wiped first.
cd "$(dirname "$0")"
B="/c/Users/anton/Documents/Codex/2026-10-10/our-goal-is-to-build-machine/outputs/MLO-Workshop/tools/blender-4.5.14-windows-x64/blender.exe"
rm -rf ../site/wires; mkdir -p ../site/wires
for n in cs5_rd_props_cs5_wire_115 cs5_rd_props_cs5_wire_117 cs5_rd_props_cs5_wire_119 cs5_rd_props_cs5_wire_217 cs5_rd_props_cs5_wire_elec_119 cs5_rd_props_wire_919; do
  read x y z < <(awk -F'\t' -v n="$n" '$2 == n {print $3, $4, $5; exit}' ../site/wide_scan.tsv)
  "$B" -b --python wires.py -- "$n" "$x" "$y" "$z" 2>&1 | grep -E "WIRES_PASS|WIRES_UNCHANGED|WIRES_SPANS|Traceback|Error" | cut -c1-400
done
