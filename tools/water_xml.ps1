# Extract every water map the game can load (read-only) and say which gta5 water.xml is the one in force.
#   powershell -File water_xml.ps1 [-Out <dir>]
# Scans the Steam install (common.rpf, update\update.rpf, update2.rpf, every dlc pack) AND FiveM's game-build overlay
# (%LOCALAPPDATA%\FiveM\FiveM.app\data\game-storage\update+update.rpf_<sha1>, update+update2.rpf_<sha1>): with
# sv_enforceGameBuild FiveM loads those instead of the Steam update*.rpf, so they are what the client really runs.
# The overlay files must be opened under their real name (update.rpf / update2.rpf): RPF7 NG decryption picks its key from the
# archive's file name + size, and the hashed name gives "Error in RPF7 file entry".
# Precedence: update2.rpf beats update.rpf beats common.rpf; the FiveM overlay beats the Steam update*.rpf.
# Findings (2026-11-05, b3258 + Steam Legacy): the only gta5 water.xml is common.rpf\data\levels\gta5\water.xml
# (504 water / 542 calming / 116 wave quads, md5 1a76f16b...); update.rpf only adds water_heistisland.xml (Cayo Perico),
# identical in the b3258 overlay and in Steam.
param([string]$Out = (Join-Path $PSScriptRoot 'water'))
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = @('C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\tools\CodeWalker',
        'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker') |
      Where-Object { Test-Path "$_\CodeWalker.Core.dll" } | Select-Object -First 1
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
New-Item -ItemType Directory -Force $Out | Out-Null
$found = New-Object System.Collections.ArrayList
function Take($rpfs, $tag) {
  foreach ($f in $rpfs) { if (-not $f.AllEntries) { continue }
    foreach ($e in $f.AllEntries) { if ($e.Name -notmatch '^water.*\.xml$') { continue }
      $b = $e.File.ExtractFile($e); $n = $tag + '__' + ($e.Path -replace '[^A-Za-z0-9._-]', '_')
      [IO.File]::WriteAllBytes((Join-Path $Out $n), $b)
      $md5 = -join ([Security.Cryptography.MD5]::Create().ComputeHash($b) | ForEach-Object { $_.ToString('x2') })
      [void]$found.Add([pscustomobject]@{ Source = $tag; Path = $e.Path; Bytes = $b.Length; Md5 = $md5; File = $n }) } } }
# 1. Steam install, every archive
$rm = New-Object CodeWalker.GameFiles.RpfManager
$rm.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) Write-Warning $s }, $false, $true)
Take $rm.AllRpfs 'steam'
# 2. FiveM game-build overlay
$gs = Join-Path $env:LOCALAPPDATA 'FiveM\FiveM.app\data\game-storage'
foreach ($p in @(Get-ChildItem $gs -Filter 'update+*.rpf_*' -ErrorAction SilentlyContinue)) {
  $leaf = $p.Name -replace '^update\+', '' -replace '_[0-9a-f]{40}$', ''
  $r = New-Object CodeWalker.GameFiles.RpfFile($p.FullName, $leaf); $r.Name = $leaf
  $r.ScanStructure([Action[string]]{ param($s) }, [Action[string]]{ param($s) Write-Warning $s })
  $all = New-Object System.Collections.ArrayList; $st = New-Object System.Collections.Stack; $st.Push($r)
  while ($st.Count) { $x = $st.Pop(); [void]$all.Add($x); foreach ($c in @($x.Children)) { if ($c) { $st.Push($c) } } }
  Take $all ('fivem_' + $leaf) }
$found | Format-Table Source, Path, Bytes, Md5 -AutoSize | Out-String -Width 220
$rank = { param($o) $s = 0; if ($o.Path -match 'update2\.rpf') { $s = 2 } elseif ($o.Path -match 'update\.rpf') { $s = 1 }; if ($o.Source -like 'fivem_*') { $s += 10 }; $s }
$main = $found | Where-Object { $_.Path -match 'levels\\gta5\\water\.xml$' } | Sort-Object { & $rank $_ } -Descending | Select-Object -First 1
"IN FORCE: $($main.Source) $($main.Path) -> $($main.File)"
