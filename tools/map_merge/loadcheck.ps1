param([string]$Ymap, [string]$Ybn)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\tools\CodeWalker'
if (-not (Test-Path "$cw\CodeWalker.Core.dll")) { $cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
$y = New-Object CodeWalker.GameFiles.YmapFile; $y.Load([IO.File]::ReadAllBytes($Ymap))
"ymap: name=$($y.Name) loaded=$($y.Loaded) boxes=$($y.BoxOccluders.Length) models=$($y.OccludeModels.Length) tris=" + (($y.OccludeModels | % { $_.Triangles.Length }) -join ',') + " hdr=$($y._CMapData.flags)/$($y._CMapData.contentFlags) ext=$($y._CMapData.streamingExtentsMin)..$($y._CMapData.streamingExtentsMax)"
$b = New-Object CodeWalker.GameFiles.YbnFile; $b.Load([IO.File]::ReadAllBytes($Ybn))
$r = $b.Bounds; "ybn: loaded=$($b.Loaded) root=$($r.GetType().Name) box=$($r.BoxMin)..$($r.BoxMax) children=$($r.Children.data_items.Length)"
$i = 0; foreach ($c in $r.Children.data_items) { $bv = $c.BVH
  "  child ${i}: $($c.GetType().Name) polys=$($c.Polygons.Length) verts=$($c.Vertices.Length) mats=$($c.Materials.Length) bvhNodes=$($bv.Nodes.data_items.Length) bvhTrees=$($bv.Trees.data_items.Length) box=$($c.BoxMin)..$($c.BoxMax)"; $i++ }
