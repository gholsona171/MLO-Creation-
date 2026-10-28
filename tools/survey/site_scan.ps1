# Justice Center survey (read-only): everything the game loads around the Davis City Hall lot, from the best-ranked copies.
# -> near_entities.tsv (every ymap entity within R of the centre, + archetype bounds), site_scan.txt (occluders, LOD lights,
#    distant lights, car generators, collision files by bounds, path nodes, scenario points inside the box).
param([double]$X = 330, [double]$Y = -1615, [double]$R = 170,
      [double]$BX0 = 270, [double]$BX1 = 400, [double]$BY0 = -1700, [double]$BY1 = -1530,
      [string]$Dir = 'C:\Users\anton\Documents\Codex\JusticeCenter\survey')
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
function Rank($p) { $m = [regex]::Match($p, 'patchday(\d+)'); if ($m.Success) { return 100 + [int]$m.Groups[1].Value }; if ($p -match 'dlc_patch') { return 60 }; if ($p -match 'dlcpacks') { return 50 }; return 0 }
function InBox($x, $y) { return ($x -ge $BX0 -and $x -le $BX1 -and $y -ge $BY0 -and $y -le $BY1) }
$best = @{}; $bb = @{}; $ybns = @{}; $ynds = @(); $ymts = @()
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if ($e -isnot [CodeWalker.GameFiles.RpfFileEntry]) { continue }
    $k = $e.Name.ToLower()
    if ($k.EndsWith('.ymap')) { if (-not $best.ContainsKey($k) -or (Rank $best[$k].Path) -le (Rank $e.Path)) { $best[$k] = $e } }
    elseif ($k.EndsWith('.ybn')) { if (-not $ybns.ContainsKey($k) -or (Rank $ybns[$k].Path) -le (Rank $e.Path)) { $ybns[$k] = $e } }
    elseif ($k.EndsWith('.ynd')) { $ynds += $e }
    elseif ($k.EndsWith('.ymt') -and $e.Path -match 'scenario') { $ymts += $e }
    elseif ($k.EndsWith('.ytyp')) {
      try { $t = New-Object CodeWalker.GameFiles.YtypFile; $t.Load($e.File.ExtractFile($e), $e) } catch { continue }
      foreach ($a in @($t.AllArchetypes)) { if ($a) { $bb[$a.Name.ToLower()] = @($a, $k) } } } } }
$log = New-Object System.Collections.Generic.List[string]
$rows = New-Object System.Collections.Generic.List[string]
$rows.Add("ymap`tarchetype`tytyp`tx`ty`tz`tqx`tqy`tqz`tqw`tlodLevel`tlodDist`tparentIndex`tparentYmap`tbbMinX`tbbMinY`tbbMinZ`tbbMaxX`tbbMaxY`tbbMaxZ`tymapPath")
foreach ($k in $best.Keys) { $e = $best[$k]
  try { $ym = New-Object CodeWalker.GameFiles.YmapFile; $ym.Load($e.File.ExtractFile($e), $e) } catch { continue }
  $cd = $ym.CMapData; $mn = $cd.entitiesExtentsMin; $mx = $cd.entitiesExtentsMax
  # occluders (live in ymaps with empty entity lists, test by their own boxes)
  if ($ym.BoxOccluders) { foreach ($o in $ym.BoxOccluders) { $b = $o._Box; $cx = $b.iCenterX / 4.0; $cy = $b.iCenterY / 4.0
      $hw = [math]::Max($b.iLength, $b.iWidth) / 8.0
      if ($cx + $hw -ge $BX0 -and $cx - $hw -le $BX1 -and $cy + $hw -ge $BY0 -and $cy - $hw -le $BY1) { $log.Add("BOXOCC`t$k`tc=($cx,$cy,$($b.iCenterZ/4.0)) L=$($b.iLength/4.0) W=$($b.iWidth/4.0) H=$($b.iHeight/4.0)`t$($e.Path)") } } }
  if ($ym.OccludeModels) { foreach ($o in $ym.OccludeModels) { $a = $o._OccludeModel.bmin; $b = $o._OccludeModel.bmax
      if ($b.X -ge $BX0 -and $a.X -le $BX1 -and $b.Y -ge $BY0 -and $a.Y -le $BY1) { $log.Add("OCCMODEL`t$k`t$a .. $b`t$($e.Path)") } } }
  if ($ym.CarGenerators) { foreach ($c in $ym.CarGenerators) { $p = $c._CCarGen.position; if (InBox $p.X $p.Y) { $log.Add("CARGEN`t$k`t$p model=$($c._CCarGen.carModel) flags=$($c._CCarGen.flags)") } } }
  if ($ym.LODLights -and $ym.LODLights.LodLights) { $n = 0; foreach ($l in $ym.LODLights.LodLights) { if ($l -and (InBox $l.Position.X $l.Position.Y)) { $n++ } }
      if ($n) { $log.Add("LODLIGHTS`t$k`t$n in box`t$($e.Path)") } }
  if ($ym.DistantLODLights -and $ym.DistantLODLights.positions) { $n = 0; foreach ($p in $ym.DistantLODLights.positions) { if (InBox $p.x $p.y) { $n++ } }
      if ($n) { $log.Add("DISTLIGHTS`t$k`t$n in box`t$($e.Path)") } }
  if ($mx.X -lt $X - $R -or $mn.X -gt $X + $R -or $mx.Y -lt $Y - $R -or $mn.Y -gt $Y + $R) { continue }
  if (-not $ym.AllEntities) { continue }
  foreach ($en in $ym.AllEntities) { $d = $en.CEntityDef; $p = $d.position
    if ([math]::Sqrt(($p.X - $X) * ($p.X - $X) + ($p.Y - $Y) * ($p.Y - $Y)) -gt $R) { continue }
    $n = "$($d.archetypeName)".ToLower(); $a = $bb[$n]; $q = $d.rotation
    if ($a) { $ad = $a[0]._BaseArchetypeDef; $bmin = $ad.bbMin; $bmax = $ad.bbMax; $ty = $a[1] } else { $bmin = $null; $bmax = $null; $ty = '?' }
    $rows.Add("$k`t$n`t$ty`t$($p.X)`t$($p.Y)`t$($p.Z)`t$($q.X)`t$($q.Y)`t$($q.Z)`t$($q.W)`t$($d.lodLevel)`t$($d.lodDist)`t$($d.parentIndex)`t$($cd.parent)`t$($bmin.X)`t$($bmin.Y)`t$($bmin.Z)`t$($bmax.X)`t$($bmax.Y)`t$($bmax.Z)`t$($e.Path)") } }
[IO.File]::WriteAllLines("$Dir\near_entities.tsv", $rows)
foreach ($k in $ybns.Keys) { $e = $ybns[$k]
  try { $yb = New-Object CodeWalker.GameFiles.YbnFile; $yb.Load($e.File.ExtractFile($e), $e) } catch { continue }
  $b = $yb.Bounds; if (-not $b) { continue }
  $a = $b.BoxMin; $c = $b.BoxMax
  if ($c.X -ge $BX0 -and $a.X -le $BX1 -and $c.Y -ge $BY0 -and $a.Y -le $BY1 -and [math]::Abs($a.X) -gt 1) { $log.Add("YBN`t$k`t$a .. $c`t$($e.Path)") } }
foreach ($e in $ynds) {
  try { $yn = New-Object CodeWalker.GameFiles.YndFile; $yn.Load($e.File.ExtractFile($e), $e) } catch { continue }
  if (-not $yn.Nodes) { continue }
  foreach ($nd in $yn.Nodes) { $p = $nd.Position; if (InBox $p.X $p.Y) { $log.Add("NODE`t$($e.Name)`t$([math]::Round($p.X,1)),$([math]::Round($p.Y,1)),$([math]::Round($p.Z,1))`tped=$($nd.IsPedNode) flags0=$($nd.Flags0.Value) flags1=$($nd.Flags1.Value) flags2=$($nd.Flags2.Value) flags3=$($nd.Flags3.Value) flags4=$($nd.Flags4.Value) links=$($nd.LinkCount) street=$($nd.StreetName)") } } }
foreach ($e in $ymts) {
  try { $yt = New-Object CodeWalker.GameFiles.YmtFile; $yt.Load($e.File.ExtractFile($e), $e) } catch { continue }
  $sr = $yt.ScenarioRegion; if (-not $sr -or -not $sr.Nodes) { continue }
  foreach ($sn in $sr.Nodes) { $p = $sn.Position; if (InBox $p.X $p.Y) { $t = ''; if ($sn.MyPoint) { $t = "type=$($sn.MyPoint.Type)" } elseif ($sn.ChainingNode) { $t = "chain=$($sn.ChainingNode.ScenarioType)" } elseif ($sn.EntityPoint) { $t = "entity=$($sn.EntityPoint.Type)" }
      $log.Add("SCEN`t$($e.Name)`t$([math]::Round($p.X,1)),$([math]::Round($p.Y,1)),$([math]::Round($p.Z,1))`t$t`t$($e.Path)") } } }
[IO.File]::WriteAllLines("$Dir\site_scan.txt", $log)
"entities $($rows.Count - 1)  log $($log.Count)"
