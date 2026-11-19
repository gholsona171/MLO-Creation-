# List every ymap's entity extents and every MLO (interior) placement in it, for location-conflict checks between map packs.
# Usage: powershell -File mlo_scan.ps1 -Root <folder> -Out <tsv>
# Lines: Y <ymap path> minX minY minZ maxX maxY maxZ entityCount
#        M <ymap path> <archetype name or hash> x y z
param([string]$Root, [string]$Out)
$ErrorActionPreference = 'Continue'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\tools\CodeWalker'
if (-not (Test-Path "$cw\CodeWalker.Core.dll")) { $cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
$sb = New-Object Text.StringBuilder
Get-ChildItem -LiteralPath $Root -Recurse -Filter *.ymap | % {
  $p = $_.FullName
  try { $y = New-Object CodeWalker.GameFiles.YmapFile; $y.Load([IO.File]::ReadAllBytes($p)); $d = $y._CMapData
    $n = 0; if ($y.AllEntities) { $n = $y.AllEntities.Length }
    [void]$sb.AppendLine(("Y`t{0}`t{1}`t{2}`t{3}`t{4}`t{5}`t{6}`t{7}" -f $p, $d.entitiesExtentsMin.X, $d.entitiesExtentsMin.Y, $d.entitiesExtentsMin.Z, $d.entitiesExtentsMax.X, $d.entitiesExtentsMax.Y, $d.entitiesExtentsMax.Z, $n))
    if ($y.MloEntities) { foreach ($e in $y.MloEntities) { $c = $e._CEntityDef
      [void]$sb.AppendLine(("M`t{0}`t{1}`t{2}`t{3}`t{4}" -f $p, $c.archetypeName.ToString(), $c.position.X, $c.position.Y, $c.position.Z)) } }
  } catch { [void]$sb.AppendLine("E`t$p`t$($_.Exception.Message)") } }
[IO.File]::WriteAllText($Out, $sb.ToString()); "done $Out"
