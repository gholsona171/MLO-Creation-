# Tower City survey (read-only on the game): every collision file (newest copy) whose bounds reach the lots' area (both lots + 25 m),
# re-saved standalone into -Out (default src/ground_ref) - the walked ground the resource does NOT ship, for work/tools/ground_check.py.
param([string]$Out = 'C:\Users\anton\Documents\Codex\TowerCity\src\ground_ref', [double]$X0 = -205, [double]$X1 = 200, [double]$Y0 = -1010, [double]$Y1 = -700)
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
function Rank($p) { $m = [regex]::Match($p, 'patchday(\d+)'); if ($m.Success) { return 100 + [int]$m.Groups[1].Value }; if ($p -match 'dlc_patch') { return 60 }; if ($p -match 'dlcpacks') { return 50 }; return 0 }
$best = @{}
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { $k = $e.Name.ToLower(); if (-not $k.EndsWith('.ybn') -or $e.Path -notmatch '_citye') { continue }
    if (-not $best.ContainsKey($k) -or (Rank $best[$k].Path) -le (Rank $e.Path)) { $best[$k] = $e } } }
New-Item -ItemType Directory -Force $Out | Out-Null; $n = 0
foreach ($k in ($best.Keys | Sort-Object)) { $e = $best[$k]
  try { $y = New-Object CodeWalker.GameFiles.YbnFile; $y.Load($e.File.ExtractFile($e), $e) } catch { continue }
  $b = $y.Bounds; if (-not $b) { continue }
  if ($b.BoxMax.X -lt $X0 -or $b.BoxMin.X -gt $X1 -or $b.BoxMax.Y -lt $Y0 -or $b.BoxMin.Y -gt $Y1) { continue }
  if ($b.BoxMax.Z -lt 15 -or $b.BoxMin.Z -gt 60) { continue }
  [IO.File]::WriteAllBytes((Join-Path $Out $k), $y.Save()); $n++; "$k <- $($e.Path)" }
"YBN_NEAR_LOTS $n"
