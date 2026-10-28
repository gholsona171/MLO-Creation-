# Justice Center survey (read-only): every game file of the sc1_19 block family (any rpf, any prefix) + every entity of the
# block's own ymaps (best-ranked copy: patchday > dlc_patch > dlcpacks > base). Writes block_files.tsv + block_entities.tsv.
param([string]$Rx = '^(hei_|apa_|bkr_|xm_|ch_|sf_|ma@|hi@)?sc1_19', [string]$Dir = 'C:\Users\anton\Documents\Codex\JusticeCenter\survey')
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
function Rank($p) { $m = [regex]::Match($p, 'patchday(\d+)'); if ($m.Success) { return 100 + [int]$m.Groups[1].Value }; if ($p -match 'dlc_patch') { return 60 }; if ($p -match 'dlcpacks') { return 50 }; return 0 }
$files = New-Object System.Collections.Generic.List[string]; $best = @{}
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if ($e -isnot [CodeWalker.GameFiles.RpfFileEntry]) { continue }
    if ($e.Name -notmatch $Rx) { continue }
    $files.Add("$($e.Name)`t$(Rank $e.Path)`t$($e.Path)")
    $k = $e.Name.ToLower()
    if ($k.EndsWith('.ymap')) { if (-not $best.ContainsKey($k) -or (Rank $best[$k].Path) -le (Rank $e.Path)) { $best[$k] = $e } } } }
[IO.File]::WriteAllLines("$Dir\block_files.tsv", $files)
$rows = New-Object System.Collections.Generic.List[string]
$rows.Add("ymap`tarchetype`tx`ty`tz`tqx`tqy`tqz`tqw`tlodLevel`tlodDist`tparentIndex`tflags`tmlo`tparentYmap`tymapFlags`tcontentFlags")
foreach ($k in $best.Keys) { $e = $best[$k]
  $ym = New-Object CodeWalker.GameFiles.YmapFile; $ym.Load($e.File.ExtractFile($e), $e)
  $cd = $ym.CMapData
  $extra = ''
  if ($ym.LODLights) { $extra += " lodlights=$($ym.LODLights.LodLights.Length)" }
  if ($ym.DistantLODLights) { $extra += " distlights=$($ym.DistantLODLights.positions.Length)" }
  if ($ym.BoxOccluders) { $extra += " boxocc=$($ym.BoxOccluders.Length)" }
  if ($ym.OccludeModels) { $extra += " occmodels=$($ym.OccludeModels.Length)" }
  if ($ym.CarGenerators) { $extra += " cargens=$($ym.CarGenerators.Length)" }
  if ($ym.GrassInstanceBatches) { $extra += " grass=$($ym.GrassInstanceBatches.Length)" }
  "YMAP $k parent=$($cd.parent) flags=$($cd.flags) content=$($cd.contentFlags) ext=$($cd.entitiesExtentsMin) .. $($cd.entitiesExtentsMax) streamExt=$($cd.streamingExtentsMin) .. $($cd.streamingExtentsMax)$extra  [$($e.Path)]"
  if (-not $ym.AllEntities) { continue }
  foreach ($en in $ym.AllEntities) { $d = $en.CEntityDef; $p = $d.position; $q = $d.rotation
    $rows.Add("$k`t$($d.archetypeName)`t$($p.X)`t$($p.Y)`t$($p.Z)`t$($q.X)`t$($q.Y)`t$($q.Z)`t$($q.W)`t$($d.lodLevel)`t$($d.lodDist)`t$($d.parentIndex)`t$($d.flags)`t$($en.IsMlo)`t$($cd.parent)`t$($cd.flags)`t$($cd.contentFlags)") } }
[IO.File]::WriteAllLines("$Dir\block_entities.tsv", $rows)
"files $($files.Count) ymaps $($best.Count) entities $($rows.Count - 1)"
