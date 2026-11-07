# Export every ymap/ytyp listed in a text file (one "path|tag" per line) to CodeWalker XML in $Out as <tag>__<name>.xml
param([string]$List, [string]$Out)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\tools\CodeWalker'
if (-not (Test-Path "$cw\CodeWalker.Core.dll")) { $cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
foreach ($ln in Get-Content $List) { if (-not $ln.Trim()) { continue }; $p, $tag = $ln -split '\|'
  $b = [IO.File]::ReadAllBytes($p)
  if ($p -match '\.ymap$') { $y = New-Object CodeWalker.GameFiles.YmapFile } elseif ($p -match '\.ytyp$') { $y = New-Object CodeWalker.GameFiles.YtypFile } else { continue }
  try { $y.Load($b); $fn = ''; $x = [CodeWalker.GameFiles.MetaXml]::GetXml($y, [ref]$fn)
    [IO.File]::WriteAllText((Join-Path $Out ("{0}__{1}.xml" -f $tag, [IO.Path]::GetFileName($p))), $x); "ok $tag $([IO.Path]::GetFileName($p))" } catch { "FAIL $p : $_" } }
