# N-way occluder merge: base author's ymap + every other author's change vs vanilla (box removed / added, occlude-model triangles removed, model deleted).
# Boxes compare with +-2 on iCosZ/iSinZ (CodeWalker re-derives them on save). Models are matched by bmin/bmax, not index. Stops on anything else.
param([string]$Vanilla, [string]$Base, [string]$Others, [string]$Out)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\tools\CodeWalker'
if (-not (Test-Path "$cw\CodeWalker.Core.dll")) { $cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
function L($p) { $y = New-Object CodeWalker.GameFiles.YmapFile; $y.Load([IO.File]::ReadAllBytes($p)); $y }
function BK($b) { $o = $b._Box; "$($o.iCenterX),$($o.iCenterY),$($o.iCenterZ),$($o.iLength),$($o.iWidth),$($o.iHeight)" }
function BEq($a, $b) { (BK $a) -eq (BK $b) -and [math]::Abs($a._Box.iCosZ - $b._Box.iCosZ) -le 2 -and [math]::Abs($a._Box.iSinZ - $b._Box.iSinZ) -le 2 }
function MK($m) { $o = $m._OccludeModel; "$($o.bmin)|$($o.bmax)" }
function TK($m, $t) { $v = $m.Vertices; $ix = $m.Indices; $i = $t * 3
  ((@($ix[$i], $ix[$i+1], $ix[$i+2]) | % { $q = $v[$_]; '{0:F3},{1:F3},{2:F3}' -f $q.X, $q.Y, $q.Z }) | Sort-Object) -join ';' }
function Tris($m) { $h = @{}; for ($t = 0; $t -lt $m.Indices.Length / 3; $t++) { $h[(TK $m $t)] = 1 }; $h }
$yv = L $Vanilla; $yb = L $Base
foreach ($op in ($Others -split ';')) { $yo = L $op; $tag = Split-Path (Split-Path $op) -Leaf; "--- $tag"
  foreach ($vb in @($yv.BoxOccluders)) { if (-not (@($yo.BoxOccluders) | ? { BEq $vb $_ })) {
      $hit = @($yb.BoxOccluders) | ? { BEq $vb $_ }
      if ($hit) { [void]$yb.RemoveBoxOccluder($hit[0]); "  box removed: $(BK $vb)" } else { "  box already gone in base: $(BK $vb)" } } }
  foreach ($ob in @($yo.BoxOccluders)) { if (-not (@($yv.BoxOccluders) | ? { BEq $ob $_ })) {
      if (@($yb.BoxOccluders) | ? { BEq $ob $_ }) { "  box already in base: $(BK $ob)" } else {
        $nb = New-Object CodeWalker.GameFiles.YmapBoxOccluder($yb, $ob._Box); $yb.AddBoxOccluder($nb); "  box added: $(BK $ob)" } } }
  foreach ($vm in @($yv.OccludeModels)) { $k = MK $vm
    $om = @($yo.OccludeModels) | ? { (MK $_) -eq $k }; $bm = @($yb.OccludeModels) | ? { (MK $_) -eq $k }
    if (-not $om) { if ($bm) { [void]$yb.RemoveOccludeModel($bm[0]); "  model deleted: $k" } else { "  model already deleted in base: $k" }; continue }
    $vt = Tris $vm; $ot = Tris $om[0]
    foreach ($x in $ot.Keys) { if (-not $vt.ContainsKey($x)) { throw "STOP: $tag ADDED a triangle to model $k - not handled" } }
    $cut = @($vt.Keys | ? { -not $ot.ContainsKey($_) }); if (-not $cut) { continue }
    if (-not $bm) { "  model $k already deleted in base (covers $($cut.Count) cut triangles)"; continue }
    $m = $bm[0]; $n = 0
    for ($t = $m.Indices.Length / 3 - 1; $t -ge 0; $t--) { if ($cut -contains (TK $m $t)) { if (-not $yb.RemoveOccludeModelTriangle($m.Triangles[$t])) { throw "remove failed" }; $n++ } }
    $miss = $cut.Count - $n; "  model ${k}: removed $n of $($cut.Count) cut triangles" + $(if ($miss) { " ($miss already gone in base)" } else { '' }) } }
$yb.Name = [IO.Path]::GetFileNameWithoutExtension($Out)
$bytes = $yb.Save(); [IO.File]::WriteAllBytes($Out, $bytes); "saved $Out $($bytes.Length) bytes, boxes $($yb.BoxOccluders.Length), models $($yb.OccludeModels.Length)"
