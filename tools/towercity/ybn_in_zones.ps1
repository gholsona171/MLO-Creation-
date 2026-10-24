# Tower City (read-only): every downtown collision file (newest copy) with triangles inside the exterior clean-up zones
# (plan/ext_cuts.json 'occl' polygons = the cut zones A / B, + the moved pillar's circle): the files l0_col.py must process.
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
function Rank($p) { $m = [regex]::Match($p, 'patchday(\d+)'); if ($m.Success) { return 100 + [int]$m.Groups[1].Value }; if ($p -match 'dlc_patch') { return 60 }; if ($p -match 'dlcpacks') { return 50 }; return 0 }
$R = Get-Content 'C:\Users\anton\Documents\Codex\TowerCity\plan\ext_cuts.json' -Raw | ConvertFrom-Json
$Z = @($R.occl); $mv = $R.move[0]
function Inside($poly, [double]$x, [double]$y) { $c = $false; $n = $poly.Count
  for ($i = 0; $i -lt $n; $i++) { $a = $poly[$i]; $b = $poly[($i + 1) % $n]
    if ((($a[1] -gt $y) -ne ($b[1] -gt $y)) -and ($x -lt ($b[0] - $a[0]) * ($y - $a[1]) / ($b[1] - $a[1]) + $a[0])) { $c = -not $c } }; return $c }
$best = @{}
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { $k = $e.Name.ToLower(); if (-not $k.EndsWith('.ybn') -or $e.Path -notmatch 'downtown_01') { continue }
    if (-not $best.ContainsKey($k) -or (Rank $best[$k].Path) -le (Rank $e.Path)) { $best[$k] = $e } } }
foreach ($k in ($best.Keys | Sort-Object)) { $e = $best[$k]
  try { $y = New-Object CodeWalker.GameFiles.YbnFile; $y.Load($e.File.ExtractFile($e), $e) } catch { continue }
  $b = $y.Bounds; if (-not $b) { continue }
  if ($b.BoxMax.X -lt -60 -or $b.BoxMin.X -gt 40 -or $b.BoxMax.Y -lt -890 -or $b.BoxMin.Y -gt -760) { continue }
  $hit = 0
  $stack = New-Object System.Collections.Stack; $stack.Push($b)
  while ($stack.Count) { $g = $stack.Pop()
    if ($g -is [CodeWalker.GameFiles.BoundComposite]) { foreach ($ch in @($g.Children.data_items)) { if ($ch) { $stack.Push($ch) } }; continue }
    if ($g -isnot [CodeWalker.GameFiles.BoundGeometry] -or -not $g.Polygons) { continue }
    $c = $g.CenterGeom; $v = $g.Vertices
    foreach ($p in $g.Polygons) {
      if ($p -is [CodeWalker.GameFiles.BoundPolygonTriangle]) { $q = $v[$p.vertIndex1] } elseif ($p -is [CodeWalker.GameFiles.BoundPolygonBox]) { $q = $v[$p.boxIndex1] } else { continue }
      $x = $q.X + $c.X; $yy = $q.Y + $c.Y
      $in = $false; foreach ($z in $Z) { if (Inside $z $x $yy) { $in = $true; break } }
      if (-not $in -and [math]::Sqrt(($x - $mv.centre[0]) * ($x - $mv.centre[0]) + ($yy - $mv.centre[1]) * ($yy - $mv.centre[1])) -lt 2.0) { $in = $true }
      if ($in) { $hit++ } } }
  if ($hit -gt 0) { "{0}`t{1}`t{2}" -f $k, $hit, $e.Path } }
"YBN_IN_ZONES_DONE"
