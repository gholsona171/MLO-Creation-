# Justice Center (read-only on the game): every distant-LOD-light ymap (distlodlights_*, every DLC prefix, best-ranked copy of each name)
# with lights inside the lot outline (plan/lot_poly.json) -> XML in -Out (src/lodlights) + one count line per file.
# The near-view twins (lodlights_*) read their positions from these by index, so these are the files to edit (Tower City l0_lodlights).
param([string]$Out = 'C:\Users\anton\Documents\Codex\JusticeCenter\src\lodlights')
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
function Rank($p) { $m = [regex]::Match($p, 'patchday(\d+)'); if ($m.Success) { return 100 + [int]$m.Groups[1].Value }; if ($p -match 'dlc_patch') { return 60 }; if ($p -match 'dlcpacks') { return 50 }; return 0 }
$P = (Get-Content 'C:\Users\anton\Documents\Codex\JusticeCenter\plan\lot_poly.json' -Raw | ConvertFrom-Json).world
$X0 = ($P | ForEach-Object { $_[0] } | Measure-Object -Minimum).Minimum; $X1 = ($P | ForEach-Object { $_[0] } | Measure-Object -Maximum).Maximum
$Y0 = ($P | ForEach-Object { $_[1] } | Measure-Object -Minimum).Minimum; $Y1 = ($P | ForEach-Object { $_[1] } | Measure-Object -Maximum).Maximum
function InLot([double]$x, [double]$y) { if ($x -lt $X0 -or $x -gt $X1 -or $y -lt $Y0 -or $y -gt $Y1) { return $false }; $c = $false; $n = $P.Count
  for ($i = 0; $i -lt $n; $i++) { $a = $P[$i]; $b = $P[($i + 1) % $n]
    if ((($a[1] -gt $y) -ne ($b[1] -gt $y)) -and ($x -lt ($b[0] - $a[0]) * ($y - $a[1]) / ($b[1] - $a[1]) + $a[0])) { $c = -not $c } }; return $c }
$best = @{}
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { $k = $e.Name.ToLower(); if (-not ($k.EndsWith('.ymap') -and $k.Contains('distlodlights'))) { continue }
    if (-not $best.ContainsKey($k) -or (Rank $best[$k].Path) -le (Rank $e.Path)) { $best[$k] = $e } } }
New-Item -ItemType Directory -Force $Out | Out-Null
foreach ($k in ($best.Keys | Sort-Object)) { $e = $best[$k]
  $y = New-Object CodeWalker.GameFiles.YmapFile; try { $y.Load($e.File.ExtractFile($e), $e) } catch { continue }
  if (-not $y.DistantLODLights -or -not $y.DistantLODLights.positions) { continue }
  $n = 0; foreach ($q in $y.DistantLODLights.positions) { if (InLot $q.x $q.y) { $n++ } }   # (not $p: PowerShell names ignore case, $p is the polygon $P)
  if ($n -eq 0) { continue }
  $fn = ''; [IO.File]::WriteAllText((Join-Path $Out ($k + '.xml')), [CodeWalker.GameFiles.MetaXml]::GetXml($y, [ref]$fn))
  "{0}`t{1}`tof {2}`t{3}" -f $k, $n, @($y.DistantLODLights.positions).Count, $e.Path }
"LODLIGHTS_FIND_DONE"
