param([string]$Root, [string]$Out)
$ErrorActionPreference = 'Continue'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\tools\CodeWalker'
if (-not (Test-Path "$cw\CodeWalker.Core.dll")) { $cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
$sb = New-Object Text.StringBuilder
Get-ChildItem -LiteralPath $Root -Recurse -Filter *.ymap | % {
  try { $y = New-Object CodeWalker.GameFiles.YmapFile; $y.Load([IO.File]::ReadAllBytes($_.FullName)); $d = $y._CMapData
    $n = 0; if ($y.AllEntities) { $n = $y.AllEntities.Length }
    [void]$sb.AppendLine(("{0}`t{1}`t{2}`t{3}`t{4}`t{5}`t{6}`t{7}`t{8}" -f $_.FullName, $d.entitiesExtentsMin.X, $d.entitiesExtentsMin.Y, $d.entitiesExtentsMin.Z, $d.entitiesExtentsMax.X, $d.entitiesExtentsMax.Y, $d.entitiesExtentsMax.Z, $n, $d.flags))
  } catch { [void]$sb.AppendLine("$($_.FullName)`tERR") } }
[IO.File]::WriteAllText($Out, $sb.ToString()); "done"
