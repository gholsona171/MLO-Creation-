# Block Boyz site survey (read-only on the game): what site_scan.ps1 does not give.
#  nodes.tsv     every path node of the given ynd files, with its links (area/node), flags and street-name hash
#  scenarios.tsv scenario points in the box from the given region ymts, type names via the hashed known-name list
#  grass.tsv     grass / scrub instances in the box from the live (lr_ > hei_ > base) ymaps of the given families
param([double]$BX0 = 1000, [double]$BX1 = 1500, [double]$BY0 = 3400, [double]$BY1 = 3900,
      [string]$Ynd = 'nodes721.ynd,nodes722.ynd,nodes753.ynd,nodes754.ynd',
      [string]$Ymt = 'alamo_sea.ymt,marina_drive.ymt,sandy_shores.ymt,senora_hills.ymt,grande_senora_desert.ymt',
      [string]$Fam = '^(lr_|hei_)?(cs4_01|cs4_03|cs4_04|cs4_06|cs4_12|cs4_roads|cs4_roadsb|cs2_06b)(_|\.)',
      [string]$Dir = 'C:\Users\anton\Documents\Codex\blockboyz_truckclub\survey')
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
function Rank($p) { $m = [regex]::Match($p, 'patchday(\d+)'); if ($m.Success) { return 100 + [int]$m.Groups[1].Value }; if ($p -match 'dlc_patch') { return 60 }; if ($p -match 'dlcpacks') { return 50 }; return 0 }
function Var($n) { if ($n -match '^lr_') { 2 } elseif ($n -match '^hei_') { 1 } else { 0 } }
$ynds = @{}; foreach ($n in $Ynd.Split(',')) { $ynds[$n] = $null }
$ymts = @{}; foreach ($n in $Ymt.Split(',')) { $ymts[$n] = $null }
$maps = @{}
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if ($e -isnot [CodeWalker.GameFiles.RpfFileEntry]) { continue }; $k = $e.Name.ToLower()
    if ($ynds.ContainsKey($k)) { if (-not $ynds[$k] -or (Rank $ynds[$k].Path) -le (Rank $e.Path)) { $ynds[$k] = $e } }
    elseif ($ymts.ContainsKey($k)) { if (-not $ymts[$k] -or (Rank $ymts[$k].Path) -le (Rank $e.Path)) { $ymts[$k] = $e } }
    elseif ($k.EndsWith('.ymap') -and $k -match $Fam) { $base = $k -replace '^(lr_|hei_)', ''
      if (-not $maps.ContainsKey($base) -or (Var $maps[$base].Name) -lt (Var $k) -or ((Var $maps[$base].Name) -eq (Var $k) -and (Rank $maps[$base].Path) -le (Rank $e.Path))) { $maps[$base] = $e } } } }
# path nodes
$rows = New-Object System.Collections.Generic.List[string]; $rows.Add("ynd`tarea`tnode`tx`ty`tz`tped`tflags0`tflags1`tflags2`tflags3`tflags4`tstreet`tlinks")
foreach ($k in $ynds.Keys) { $e = $ynds[$k]; if (-not $e) { continue }
  $yn = New-Object CodeWalker.GameFiles.YndFile; $yn.Load($e.File.ExtractFile($e), $e)
  foreach ($nd in $yn.Nodes) { $p = $nd.Position; $ls = @()
    $L = $yn.NodeDictionary.Links; for ($i = 0; $i -lt $nd.LinkCount; $i++) { $r = $L[$nd.LinkID + $i]; $ls += "$($r.AreaID):$($r.NodeID)" }
    $rows.Add("$k`t$($nd.AreaID)`t$($nd.NodeID)`t$([math]::Round($p.X,2))`t$([math]::Round($p.Y,2))`t$([math]::Round($p.Z,2))`t$($nd.IsPedNode)`t$($nd.Flags0.Value)`t$($nd.Flags1.Value)`t$($nd.Flags2.Value)`t$($nd.Flags3.Value)`t$($nd.Flags4.Value)`t$($nd.StreetName.Hash)`t$($ls -join ' ')") } }
[IO.File]::WriteAllLines("$Dir\nodes.tsv", $rows); "nodes $($rows.Count - 1)"
# scenarios
$known = (Get-Content (Join-Path $PSScriptRoot 'scenario_names.txt')) -split '\s+' | Where-Object { $_ }
$hn = @{}; foreach ($n in $known) { $hn[[CodeWalker.GameFiles.JenkHash]::GenHash($n.ToLower())] = $n }
function Nm($yt, $id) { $tn = $yt.CScenarioPointRegion.LookUps.TypeNames; try { $h = [uint32]$tn[$id].Hash } catch { try { $h = [uint32]$tn[$id] } catch { return "id$id" } }; if ($hn.ContainsKey($h)) { return $hn[$h] }; return ('0x{0:X8}' -f $h) }
$rows = New-Object System.Collections.Generic.List[string]; $rows.Add("ymt`tx`ty`tz`tkind`ttype`tflags`ttime")
foreach ($k in $ymts.Keys) { $e = $ymts[$k]; if (-not $e) { continue }
  $yt = New-Object CodeWalker.GameFiles.YmtFile; $yt.Load($e.File.ExtractFile($e), $e); $sr = $yt.ScenarioRegion; if (-not $sr) { continue }
  foreach ($sn in $sr.Nodes) { $p = $sn.Position; if ($p.X -lt $BX0 -or $p.X -gt $BX1 -or $p.Y -lt $BY0 -or $p.Y -gt $BY1) { continue }
    $kd = ''; $t = ''; $fl = ''; $tm = ''
    if ($sn.MyPoint) { $kd = 'point'; $t = Nm $yt $sn.MyPoint.TypeId; $fl = "$($sn.MyPoint.Flags)"; $tm = "$($sn.MyPoint.TimeStart)-$($sn.MyPoint.TimeEnd)" }
    elseif ($sn.ChainingNode) { $kd = 'chain'; $t = "$($sn.ChainingNode.ScenarioType)" }
    elseif ($sn.EntityPoint) { $kd = 'entity'; $t = "$($sn.EntityPoint.Type)" }
    elseif ($sn.ClusterMyPoint) { $kd = 'cluster'; $t = "$($sn.ClusterMyPoint.Type)" }
    $rows.Add("$k`t$([math]::Round($p.X,2))`t$([math]::Round($p.Y,2))`t$([math]::Round($p.Z,2))`t$kd`t$t`t$fl`t$tm") } }
[IO.File]::WriteAllLines("$Dir\scenarios.tsv", $rows); "scenarios $($rows.Count - 1)"
# grass
$rows = New-Object System.Collections.Generic.List[string]; $rows.Add("ymap`tarchetype`tx`ty`tz")
$sum = New-Object System.Collections.Generic.List[string]
foreach ($k in $maps.Keys) { $e = $maps[$k]
  $ym = New-Object CodeWalker.GameFiles.YmapFile; $ym.Load($e.File.ExtractFile($e), $e)
  if (-not $ym.GrassInstanceBatches) { continue }
  foreach ($b in $ym.GrassInstanceBatches) { $mn = $b.AABBMin; $mx = $b.AABBMax; $n = 0
    if ($mx.X -lt $BX0 -or $mn.X -gt $BX1 -or $mx.Y -lt $BY0 -or $mn.Y -gt $BY1) { continue }
    $arch = "$($b.Batch.archetypeName)"
    foreach ($i in $b.Instances) { $q = $i.Position.u0, $i.Position.u1, $i.Position.u2
      $x = $mn.X + ($mx.X - $mn.X) * $q[0] / 65535.0; $y = $mn.Y + ($mx.Y - $mn.Y) * $q[1] / 65535.0; $z = $mn.Z + ($mx.Z - $mn.Z) * $q[2] / 65535.0
      if ($x -ge $BX0 -and $x -le $BX1 -and $y -ge $BY0 -and $y -le $BY1) { $rows.Add("$($e.Name)`t$arch`t$([math]::Round($x,2))`t$([math]::Round($y,2))`t$([math]::Round($z,2))"); $n++ } }
    $sum.Add("GRASS`t$($e.Name)`t$arch`t$n in box`t$mn .. $mx") } }
[IO.File]::WriteAllLines("$Dir\grass.tsv", $rows); $sum; "grass $($rows.Count - 1)"
"live ymaps used: $(($maps.Values | ForEach-Object { $_.Name }) -join ',')"
