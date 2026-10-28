# Tower City level 0: remove every vanilla occluder that reaches over the two lots, from EVERY occlusion ymap the game loads that
# touches them (2026-10-24 sweep, Antonio: things vanish behind invisible occluders of the removed buildings).
#  * occlude-model triangle: removed when it overlaps a lot - any corner, its centre, or any of 21 points spread over it lies in a
#    lot (a big triangle can cover a lot with all three corners outside); a model left with no triangles is removed.
#  * box occluder: removed when its footprint overlaps a lot - a 5 x 5 grid over it in WORLD space. FIXED 2026-10-28 (Justice Center):
#    CodeWalker's BBMin / BBMax are LOCAL to the box's Position and turned by its Orientation; read as world corners no box ever matched
#    (Tower City's working copy still has the old test: re-run its occluder step to see whether boxes over its lots were missed).
# Which ymaps: every *occl* ymap (best-ranked copy: patchday > dlc_patch > dlcpacks > base) whose occluders reach within 30 m of a
# lot. Writes the edited copies to -Out and prints one line per ymap; -Report lists every occluder near the lots without writing.
# Our own maps carry no occluders (checked 2026-10-24).
param([string]$Out = 'C:\Users\anton\Documents\Codex\TowerCity\resource\tower_city\stream', [switch]$Report)
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
function Rank($p) { $m = [regex]::Match($p, 'patchday(\d+)'); if ($m.Success) { return 100 + [int]$m.Groups[1].Value }; if ($p -match 'dlc_patch') { return 60 }; if ($p -match 'dlcpacks') { return 50 }; return 0 }
$polys = Get-Content 'C:\Users\anton\Documents\Codex\TowerCity\plan\lot_polys.json' -Raw | ConvertFrom-Json
$P = @($polys.east, $polys.west)
$ext = Get-Content 'C:\Users\anton\Documents\Codex\TowerCity\plan\ext_cuts.json' -Raw | ConvertFrom-Json   # + the exterior clean-up zones (ext_plan.py:
foreach ($q in @($ext.occl)) { $P += ,$q }                                                                    # the San Andreas branch, the PARKING block, the drives)
$X0 = 1e9; $X1 = -1e9; $Y0 = 1e9; $Y1 = -1e9
foreach ($poly in $P) { foreach ($q in $poly) { $X0 = [math]::Min($X0, $q[0]); $X1 = [math]::Max($X1, $q[0]); $Y0 = [math]::Min($Y0, $q[1]); $Y1 = [math]::Max($Y1, $q[1]) } }
function InLot([double]$x, [double]$y) { foreach ($poly in $P) { $c = $false; $n = $poly.Count
    for ($i = 0; $i -lt $n; $i++) { $a = $poly[$i]; $b = $poly[($i + 1) % $n]
      if ((($a[1] -gt $y) -ne ($b[1] -gt $y)) -and ($x -lt ($b[0] - $a[0]) * ($y - $a[1]) / ($b[1] - $a[1]) + $a[0])) { $c = -not $c } }
    if ($c) { return $true } }; return $false }
function TriHits($t) { $a = $t.Corner1; $b = $t.Corner2; $c = $t.Corner3
  for ($i = 0; $i -le 5; $i++) { for ($j = 0; $j -le 5 - $i; $j++) { $k = 5 - $i - $j
      $x = ($a.X * $i + $b.X * $j + $c.X * $k) / 5; $y = ($a.Y * $i + $b.Y * $j + $c.Y * $k) / 5
      if (InLot $x $y) { return $true } } }
  return (InLot (($a.X + $b.X + $c.X) / 3) (($a.Y + $b.Y + $c.Y) / 3)) }
function BoxHits($bx) { $mn = $bx.BBMin; $mx = $bx.BBMax; $o = $bx.Orientation; $c = $bx.Position   # BBMin / BBMax are LOCAL (about
  $a = 2 * [math]::Atan2($o.Z, $o.W); $ca = [math]::Cos($a); $sa = [math]::Sin($a)                   # Position), turned by Orientation about z
  for ($i = 0; $i -le 4; $i++) { for ($j = 0; $j -le 4; $j++) {
      $lx = $mn.X + ($mx.X - $mn.X) * $i / 4; $ly = $mn.Y + ($mx.Y - $mn.Y) * $j / 4
      if (InLot ($c.X + $lx * $ca - $ly * $sa) ($c.Y + $lx * $sa + $ly * $ca)) { return $true } } }
  return $false }
$best = @{}
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { $k = $e.Name.ToLower(); if (-not ($k.EndsWith('.ymap') -and $k.Contains('occl'))) { continue }
    if (-not $best.ContainsKey($k) -or (Rank $best[$k].Path) -le (Rank $e.Path)) { $best[$k] = $e } } }
foreach ($k in ($best.Keys | Sort-Object)) { $e = $best[$k]
  $y = New-Object CodeWalker.GameFiles.YmapFile; try { $y.Load($e.File.ExtractFile($e), $e) } catch { continue }
  $near = $false
  foreach ($m in @($y.OccludeModels)) { if ($m) { foreach ($t in @($m.Triangles)) { foreach ($q in @($t.Corner1, $t.Corner2, $t.Corner3)) { if ($q.X -gt $X0 - 30 -and $q.X -lt $X1 + 30 -and $q.Y -gt $Y0 - 30 -and $q.Y -lt $Y1 + 30) { $near = $true } } } } }
  foreach ($b in @($y.BoxOccluders)) { if ($b -and $b.Position.X -gt $X0 - 60 -and $b.Position.X -lt $X1 + 60 -and $b.Position.Y -gt $Y0 - 60 -and $b.Position.Y -lt $Y1 + 60) { $near = $true } }
  if (-not $near) { continue }
  $rt = 0; $rm = 0; $rb = 0; $kt = 0; $kb = 0
  foreach ($m in @($y.OccludeModels)) { if (-not $m) { continue }
    foreach ($t in @($m.Triangles)) { if (TriHits $t) { if (-not $Report) { [void]$y.RemoveOccludeModelTriangle($t) }; $rt++ } else { $kt++ } }
    if (-not $Report -and @($m.Triangles).Count -eq 0) { [void]$y.RemoveOccludeModel($m); $rm++ } }
  foreach ($b in @($y.BoxOccluders)) { if (-not $b) { continue }
    if (BoxHits $b) { if (-not $Report) { [void]$y.RemoveBoxOccluder($b) }; $rb++ } else { $kb++ } }
  if (-not $Report -and ($rt + $rb) -gt 0) { [IO.File]::WriteAllBytes((Join-Path $Out $k), $y.Save()) }
  "{0}: triangles removed {1} (kept {2}), empty models {3}, boxes removed {4} (kept {5})  (rank {6}){7}" -f $k, $rt, $kt, $rm, $rb, $kb, (Rank $e.Path), $(if (($rt + $rb) -eq 0) { '  - nothing over the lots, not shipped' } else { '' }) }
"L0_OCCL_DONE"
