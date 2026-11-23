# lod_extract.ps1 (read-only on the game): the drawable dictionaries (.ydd) that hold the distance models listed in
# ..\site\lod_targets.tsv (lod_list.py), as full RSC7 files (for Sollumz) into ..\vanilla\lod\ - newest copy wins.
# The area's LODs are not single .ydr files: each lives in a dictionary (cs4_02_props_p126_slod_children.ydd ...) named by its
# archetype's drawableDictionary in the area's ytyps (country_04_metadata_*.ytyp). Archetypes the ymaps only name by hash (hash_d9b390e6) are matched by hash.
# ..\vanilla\lod\targets.tsv: target <TAB> dictionary <TAB> drawable hash (hex), for lod_cut.py.
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
function Rank($p) { $m = [regex]::Match($p, 'patchday(\d+)'); if ($m.Success) { return 100 + [int]$m.Groups[1].Value }; if ($p -match 'dlc_patch') { return 60 }; if ($p -match 'dlcpacks') { return 50 }; return 0 }
$root = Split-Path $PSScriptRoot -Parent; $out = Join-Path $root 'vanilla\lod'
if (Test-Path $out) { Remove-Item -Recurse -Force $out }; New-Item -ItemType Directory $out | Out-Null
$want = @{}                                                         # archetype hash -> target name as listed
foreach ($l in Get-Content (Join-Path $root 'site\lod_targets.tsv')) { $a = ($l -split "`t")[0]
  if ($a -match '^hash_([0-9a-f]{8})$') { $h = [Convert]::ToUInt32($matches[1], 16) } else { $h = [CodeWalker.GameFiles.JenkHash]::GenHash($a.ToLower()) }
  $want[[uint32]$h] = $a }
# 1 the area's ytyps: archetype -> drawable dictionary
$dict = @{}                                                         # archetype hash -> dictionary hash
$ytyps = @{}
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { $n = $e.Name.ToLower(); if ($n.EndsWith('.ytyp') -and $e.Path -like '*\country_04\*' -and (-not $ytyps.ContainsKey($n) -or (Rank $ytyps[$n].Path) -le (Rank $e.Path))) { $ytyps[$n] = $e } } }
foreach ($e in $ytyps.Values) { $y = New-Object CodeWalker.GameFiles.YtypFile; $y.Load($e.File.ExtractFile($e), $e)
  foreach ($a in $y.AllArchetypes) { $h = [uint32]$a._BaseArchetypeDef.name.Hash; if ($want.ContainsKey($h)) { $dict[$h] = [uint32]$a._BaseArchetypeDef.drawableDictionary.Hash } } }
# 2 the dictionaries
$need = @{}; foreach ($d in $dict.Values) { if ($d -ne 0) { $need[[uint32]$d] = $true } }
$best = @{}
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if (-not $e.Name.ToLower().EndsWith('.ydd')) { continue }; $h = [uint32]$e.ShortNameHash; if (-not $need.ContainsKey($h)) { continue }
    if (-not $best.ContainsKey($h) -or (Rank $best[$h].Path) -le (Rank $e.Path)) { $best[$h] = $e } } }
foreach ($h in $best.Keys) { $e = $best[$h]; $y = New-Object CodeWalker.GameFiles.YddFile; $y.Load($e.File.ExtractFile($e), $e)
  [IO.File]::WriteAllBytes((Join-Path $out $e.Name.ToLower()), $y.Save()) }
$rows = @(); $miss = @()
foreach ($h in $want.Keys) {
  if (-not $dict.ContainsKey($h) -or $dict[$h] -eq 0) { $miss += "$($want[$h]) (no dictionary)"; continue }
  if (-not $best.ContainsKey($dict[$h])) { $miss += "$($want[$h]) (dictionary not found)"; continue }
  $rows += "$($want[$h])`t$($best[$dict[$h]].Name.ToLower() -replace '\.ydd$','')`t$('{0:x8}' -f $h)" }
[IO.File]::WriteAllLines((Join-Path $out 'targets.tsv'), [string[]]$rows)
"LOD_EXTRACT $($rows.Count) of $($want.Count) targets in $($best.Count) dictionaries; not found: $($miss -join ', ')"
