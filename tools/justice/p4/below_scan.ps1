# Jail I tunnel (read-only on the game): what lies BELOW the plaza where the tunnel runs. Every collision file (game archives, newest copy,
# and the loose resources on the rig) whose bounds intersect the box, and every ymap entity / MLO instance whose position lies in it
# (XY box + z range). For each collision hit, the number of its triangles / primitives with a vertex inside the box.
# Usage: powershell -File below_scan.ps1 -X0 .. -X1 .. -Y0 .. -Y1 .. -Z0 .. -Z1 .. [-Loose C:\C9Test\live\resources]
param([double]$X0, [double]$X1, [double]$Y0, [double]$Y1, [double]$Z0, [double]$Z1, [string]$Loose = 'C:\C9Test\live\resources')
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
function Over($mn, $mx) { return ($mn.X -le $X1 -and $mx.X -ge $X0 -and $mn.Y -le $Y1 -and $mx.Y -ge $Y0 -and $mn.Z -le $Z1 -and $mx.Z -ge $Z0) }
function In($v) { return ($v.X -ge $X0 -and $v.X -le $X1 -and $v.Y -ge $Y0 -and $v.Y -le $Y1 -and $v.Z -ge $Z0 -and $v.Z -le $Z1) }
function Count($b) {
  $n = 0
  if ($b.Children -and $b.Children.data_items) { foreach ($c in $b.Children.data_items) { if ($c) { $n += Count $c } } }
  if ($b.Vertices) { $cen = $b.Center; foreach ($v in $b.Vertices) { $w = New-Object SharpDX.Vector3(($v.X + $cen.X), ($v.Y + $cen.Y), ($v.Z + $cen.Z)); if (In $w) { $n++ } } }
  return $n }
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { $k = $e.Name.ToLower()
    if ($k.EndsWith('.ybn')) {
      try { $y = New-Object CodeWalker.GameFiles.YbnFile; $y.Load($e.File.ExtractFile($e), $e) } catch { continue }
      if ($y.Bounds -and (Over $y.Bounds.BoxMin $y.Bounds.BoxMax)) { "YBN $($e.Path) verts_inside=$(Count $y.Bounds)  $($y.Bounds.BoxMin) .. $($y.Bounds.BoxMax)" } }
    elseif ($k.EndsWith('.ymap')) {
      try { $m = New-Object CodeWalker.GameFiles.YmapFile; $m.Load($e.File.ExtractFile($e), $e) } catch { continue }
      if (-not $m.AllEntities) { continue }
      foreach ($en in $m.AllEntities) { $p = $en.Position; if (In $p) { "ENT $($e.Path) $($en.Name) $p mlo=$([bool]$en.MloInstance)" } } } } }
foreach ($p in (Get-ChildItem -Recurse -Filter *.ybn $Loose)) {
  try { $y = New-Object CodeWalker.GameFiles.YbnFile; $y.Load([IO.File]::ReadAllBytes($p.FullName)) } catch { continue }
  if ($y.Bounds -and (Over $y.Bounds.BoxMin $y.Bounds.BoxMax)) { "LOOSE $($p.FullName) verts_inside=$(Count $y.Bounds)" } }
"BELOW_SCAN_DONE"
