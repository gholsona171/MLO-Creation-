# Justice Center (read-only): every ymap entity (best-ranked copy of each ymap NAME) within R of the block centre whose archetype
# bounds can reach the box, with archetype bounds + ytyp + drawableDictionary -> -Out tsv. Wider than the survey's near_entities.tsv
# (R 170 by entity origin missed the Davis Ave / Macdonald St corner's road model).
param([double]$X = 324, [double]$Y = -1618, [double]$R = 400, [string]$Out = 'C:\Users\anton\Documents\Codex\JusticeCenter\plan\near_entities_wide.tsv')
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
function Rank($p) { $m = [regex]::Match($p, 'patchday(\d+)'); if ($m.Success) { return 100 + [int]$m.Groups[1].Value }; if ($p -match 'dlc_patch') { return 60 }; if ($p -match 'dlcpacks') { return 50 }; return 0 }
$best = @{}; $bb = @{}
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if ($e -isnot [CodeWalker.GameFiles.RpfFileEntry]) { continue }
    $k = $e.Name.ToLower()
    if ($k.EndsWith('.ymap')) { if (-not $best.ContainsKey($k) -or (Rank $best[$k].Path) -le (Rank $e.Path)) { $best[$k] = $e } }
    elseif ($k.EndsWith('.ytyp')) {
      try { $t = New-Object CodeWalker.GameFiles.YtypFile; $t.Load($e.File.ExtractFile($e), $e) } catch { continue }
      foreach ($a in @($t.AllArchetypes)) { if ($a) { $bb[$a.Name.ToLower()] = @($a, $k); $bb[('hash_{0:x8}' -f [uint32]$a._BaseArchetypeDef.name.Hash)] = @($a, $k) } } } } }
$rows = New-Object System.Collections.Generic.List[string]
$rows.Add("ymap`tarchetype`tytyp`tx`ty`tz`tqx`tqy`tqz`tqw`tlodLevel`tlodDist`tparentIndex`tparentYmap`tbbMinX`tbbMinY`tbbMinZ`tbbMaxX`tbbMaxY`tbbMaxZ`tdd`tymapPath")
foreach ($k in $best.Keys) { $e = $best[$k]
  try { $ym = New-Object CodeWalker.GameFiles.YmapFile; $ym.Load($e.File.ExtractFile($e), $e) } catch { continue }
  $cd = $ym.CMapData; $mn = $cd.entitiesExtentsMin; $mx = $cd.entitiesExtentsMax
  if ($mx.X -lt $X - $R -or $mn.X -gt $X + $R -or $mx.Y -lt $Y - $R -or $mn.Y -gt $Y + $R) { continue }
  if (-not $ym.AllEntities) { continue }
  foreach ($en in $ym.AllEntities) { $d = $en.CEntityDef; $p = $d.position
    $n = "$($d.archetypeName)".ToLower(); $a = $bb[$n]
    if ($a) { $ad = $a[0]._BaseArchetypeDef; $bmin = $ad.bbMin; $bmax = $ad.bbMax; $ty = $a[1]; $dd = "$($ad.drawableDictionary)" } else { $bmin = $null; $bmax = $null; $ty = '?'; $dd = '' }
    $rad = 0; if ($a) { $rad = [math]::Sqrt(($bmax.X - $bmin.X) * ($bmax.X - $bmin.X) + ($bmax.Y - $bmin.Y) * ($bmax.Y - $bmin.Y)) / 2 + [math]::Max([math]::Abs($bmax.X + $bmin.X), [math]::Abs($bmax.Y + $bmin.Y)) / 2 }
    if ([math]::Sqrt(($p.X - $X) * ($p.X - $X) + ($p.Y - $Y) * ($p.Y - $Y)) - $rad -gt 125) { continue }
    $q = $d.rotation
    $rows.Add("$k`t$n`t$ty`t$($p.X)`t$($p.Y)`t$($p.Z)`t$($q.X)`t$($q.Y)`t$($q.Z)`t$($q.W)`t$($d.lodLevel)`t$($d.lodDist)`t$($d.parentIndex)`t$($cd.parent)`t$($bmin.X)`t$($bmin.Y)`t$($bmin.Z)`t$($bmax.X)`t$($bmax.Y)`t$($bmax.Z)`t$dd`t$($e.Path)") } }
[IO.File]::WriteAllLines($Out, $rows); "NEAR_ENTS $($rows.Count - 1)"
