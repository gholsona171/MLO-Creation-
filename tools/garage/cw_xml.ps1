# cw_xml.ps1 (read-only, hole_grid_offline.py): export every .ybn / .ydr given (paths) to CodeWalker XML in OutDir (read-only)
param([string]$OutDir, [string[]]$Files)
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
New-Item -ItemType Directory -Force $OutDir | Out-Null
foreach ($p in $Files) {
  $n = [IO.Path]::GetFileName($p)
  if ($p.EndsWith('.ybn')) { $y = New-Object CodeWalker.GameFiles.YbnFile; $y.Load([IO.File]::ReadAllBytes($p)); $fn=''; $x = [CodeWalker.GameFiles.MetaXml]::GetXml($y, [ref]$fn) }
  else { $y = New-Object CodeWalker.GameFiles.YdrFile; $y.Load([IO.File]::ReadAllBytes($p)); $x = [CodeWalker.GameFiles.YdrXml]::GetXml($y, $null) }
  [IO.File]::WriteAllText((Join-Path $OutDir "$n.xml"), $x); "ok $n $($x.Length)"
}
