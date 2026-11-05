# Merge: base = Malmqvist's lr_sc1_occl_00 (boxes + model 1 + model 7 cut); add KQ's cut = the model-7 triangles KQ removed from vanilla.
param([string]$Vanilla, [string]$Base, [string]$Other, [int]$Model, [string]$Out)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\tools\CodeWalker'
if (-not (Test-Path "$cw\CodeWalker.Core.dll")) { $cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
function L($p) { $y = New-Object CodeWalker.GameFiles.YmapFile; $y.Load([IO.File]::ReadAllBytes($p)); $y }
function K($m, $t) { $v = $m.Vertices; $ix = $m.Indices; $i = $t * 3
  ((@($ix[$i], $ix[$i+1], $ix[$i+2]) | % { $q = $v[$_]; '{0:F3},{1:F3},{2:F3}' -f $q.X, $q.Y, $q.Z }) | Sort-Object) -join ';' }
$yv = L $Vanilla; $yb = L $Base; $yo = L $Other
$mv = $yv.OccludeModels[$Model]; $mo = $yo.OccludeModels[$Model]; $mb = $yb.OccludeModels[$Model]
$okeys = @{}; for ($t = 0; $t -lt $mo.Indices.Length / 3; $t++) { $okeys[(K $mo $t)] = 1 }
$cut = @{}; for ($t = 0; $t -lt $mv.Indices.Length / 3; $t++) { $k = K $mv $t; if (-not $okeys.ContainsKey($k)) { $cut[$k] = 1 } }
"other author's cut in model ${Model}: $($cut.Count) triangles"
$n = 0
for ($t = $mb.Indices.Length / 3 - 1; $t -ge 0; $t--) { $k = K $mb $t
  if ($cut.ContainsKey($k)) { $tri = $mb.Triangles[$t]; if (-not $yb.RemoveOccludeModelTriangle($tri)) { throw "remove failed at $t" }; $n++; $mb = $yb.OccludeModels[$Model] } }
"removed $n from base model $Model -> $($mb.Indices.Length / 3) tris, $($mb.Vertices.Length) verts"
if ($n -ne $cut.Count) { throw "expected $($cut.Count) removals, did $n" }
$yb.Name = [IO.Path]::GetFileNameWithoutExtension($Out)   # Save() writes the CMapData / block name from this; empty otherwise
$bytes = $yb.Save(); [IO.File]::WriteAllBytes($Out, $bytes); "saved $Out $($bytes.Length) bytes"
