# Justice Center (read-only): name -> parent of every ymap whose name matches -Rx (best-ranked copy), for the LOD pass (every child ymap of
# a LOD ymap we edit must be read, or a LOD whose children live in an unread ymap would look childless).
param([string]$Rx = 'sc1_')
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
  foreach ($e in $f.AllEntries) { $k = $e.Name.ToLower(); if (-not $k.EndsWith('.ymap') -or $k -notmatch $Rx) { continue }
    if (-not $best.ContainsKey($k) -or (Rank $best[$k].Path) -le (Rank $e.Path)) { $best[$k] = $e } } }
foreach ($k in ($best.Keys | Sort-Object)) { $e = $best[$k]
  $y = New-Object CodeWalker.GameFiles.YmapFile; try { $y.Load($e.File.ExtractFile($e), $e) } catch { continue }
  "{0}`t{1}`t{2}" -f $k, $y.CMapData.parent, @($y.AllEntities).Count }
