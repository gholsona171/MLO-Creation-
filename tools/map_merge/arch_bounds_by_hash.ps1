# Bounds (bbMin/bbMax/bsRadius) of archetypes by hash (lines "hash_XXXXXXXX") from every ytyp in the game -> JSON (first copy wins, newest dlc_patch first)
param([string]$List, [string]$Out)
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\tools\CodeWalker'
if (-not (Test-Path "$cw\CodeWalker.Core.dll")) { $cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$want = @{}; foreach ($l in Get-Content $List) { $l = $l.Trim(); if ($l) { $want[[uint32]('0x' + $l.Substring(5))] = $l } }
$res = @{}
$rpfs = @($rpf.AllRpfs | Sort-Object { if ($_.Path -match 'dlc_patch') { 0 } elseif ($_.Path -match '^update') { 1 } else { 2 } })
foreach ($f in $rpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if ($e.Name -notmatch '\.ytyp$') { continue }
    try { $t = New-Object CodeWalker.GameFiles.YtypFile; $t.Load($e.File.ExtractFile($e), $e) } catch { continue }
    foreach ($a in $t.AllArchetypes) { $h = [uint32]$a._BaseArchetypeDef.name.Hash
      if ($want.ContainsKey($h) -and -not $res.ContainsKey($want[$h])) { $d = $a._BaseArchetypeDef
        $res[$want[$h]] = @{ name = $a.Name; ytyp = $e.Path; bbMin = @($d.bbMin.X, $d.bbMin.Y, $d.bbMin.Z); bbMax = @($d.bbMax.X, $d.bbMax.Y, $d.bbMax.Z); bsRadius = $d.bsRadius } } } } }
$res | ConvertTo-Json -Depth 4 | Set-Content $Out -Encoding utf8
"found $($res.Count) of $($want.Count)"; foreach ($k in $want.Values) { if (-not $res.ContainsKey($k)) { "MISSING $k" } }
