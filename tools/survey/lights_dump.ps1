# Justice Center survey (read-only): every distant LOD light position in a box from the distlodlights ymaps (all prefixes) -> lights_box.tsv
param([double]$BX0 = 200, [double]$BX1 = 450, [double]$BY0 = -1760, [double]$BY1 = -1500, [string]$Dir = 'C:\Users\anton\Documents\Codex\JusticeCenter\survey')
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$rows = New-Object System.Collections.Generic.List[string]; $rows.Add("ymap`tindex`tx`ty`tz`tpath")
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if ($e.Name -notmatch 'distlodlights_.*\.ymap$') { continue }
    try { $ym = New-Object CodeWalker.GameFiles.YmapFile; $ym.Load($e.File.ExtractFile($e), $e) } catch { continue }
    if (-not $ym.DistantLODLights -or -not $ym.DistantLODLights.positions) { continue }
    $i = 0; foreach ($p in $ym.DistantLODLights.positions) { if ($p.x -ge $BX0 -and $p.x -le $BX1 -and $p.y -ge $BY0 -and $p.y -le $BY1) { $rows.Add("$($e.Name)`t$i`t$($p.x)`t$($p.y)`t$($p.z)`t$($e.Path)") }; $i++ } } }
[IO.File]::WriteAllLines("$Dir\lights_box.tsv", $rows); "rows $($rows.Count - 1)"
