# Tower City survey (read-only on the game): extract game files by FILE NAME (the copy the game loads: patchday > dlc_patch > dlcpacks
# > base, same rank as l0_occl.ps1). resources (ybn/ydr/ydd/ytd/yft) are re-saved as standalone RSC7 files (see extract_file.ps1).
# Usage: powershell -File survey/extract_by_name.ps1 -Out src/game -Names dt1_rd1_r1_12.ydr,hei_dt1_rd1_strm_1.ymap
param([string]$Out, [string[]]$Names)
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
function Rank($p) { $m = [regex]::Match($p, 'patchday(\d+)'); if ($m.Success) { return 100 + [int]$m.Groups[1].Value }; if ($p -match 'dlc_patch') { return 60 }; if ($p -match 'dlcpacks') { return 50 }; return 0 }
$want = @{}; foreach ($n in $Names) { foreach ($m in ($n -split ',')) { if ($m) { $want[$m.ToLower()] = $null } } }
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { $k = $e.Name.ToLower(); if (-not $want.ContainsKey($k)) { continue }
    if (-not $want[$k] -or (Rank $want[$k].Path) -le (Rank $e.Path)) { $want[$k] = $e } } }
New-Item -ItemType Directory -Force $Out | Out-Null
foreach ($k in $want.Keys) { $e = $want[$k]; if (-not $e) { Write-Warning "not found: $k"; continue }
  $b = $e.File.ExtractFile($e)
  $t = @{ '.ybn' = 'YbnFile'; '.ydr' = 'YdrFile'; '.ydd' = 'YddFile'; '.ytd' = 'YtdFile'; '.yft' = 'YftFile' }[[IO.Path]::GetExtension($e.Name).ToLower()]
  if ($t) { $y = New-Object "CodeWalker.GameFiles.$t"; $y.Load($b, $e); $b = $y.Save() }   # raw resource data -> a standalone RSC7 file
  [IO.File]::WriteAllBytes((Join-Path $Out $e.Name), $b); "$($e.Name) $($b.Length) bytes  <- $($e.Path)" }
