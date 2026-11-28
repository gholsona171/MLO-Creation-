# game_files.ps1 (dot-source it: . (Join-Path $PSScriptRoot 'game_files.ps1')): Rockstar's files AS THE SERVER'S GAME BUILD HAS
# THEM, for every step that reads the game (vanilla_extract, lod_extract, grass_cut, site_occl, tex_extract).
# The Steam install is newer than the build the server enforces (site.json game_build, 3258): its update.rpf / update2.rpf and its
# newest DLC packs (mp2024_02, mp2025_01/02 ...) carry 2025 copies of the Vinewood Bowl's maps (dlc_patch\mpapartment drops the hill
# ch2_04_land06 for Rockstar's mansions), and a copy of ours built from those removed the hill's HD model on b3258, so its LOD stuck
# up close. So:
#   * the Steam install's own update.rpf / update2.rpf are left out; the build's pair is read instead from site.json
#     game_build_update_dir (hard links to FiveM's stored copies, named update.rpf / update2.rpf: NG decryption keys on the name);
#   * a DLC pack (any ...\dlcpacks\<pack>\...) is read only when the build mounts it: the build's own update.rpf
#     common\data\dlclist.xml, both forms ("dlcpacks:/mpheist/", "platform:/dlcPacks/mpBeach/"; b3258: 89 packs, up to mp2024_01 /
#     patch2024_01). The client's log is no substitute: it names only packs with a content.xml (it missed mpbeach, mpheist ...).
# Defines: $gta, $cw (CodeWalker loaded, keys loaded), $GameRpfs (every archive of the build, nested ones too: each has .AllEntries
# and .Path), and Rank($path) (patchday > dlc_patch > dlcpacks > base: the newest copy of a name within the build wins).
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$site = Get-Content (Join-Path (Split-Path $PSScriptRoot -Parent) 'site.json') -Raw | ConvertFrom-Json
if (-not $site.game_build -or -not $site.game_build_update_dir) { throw 'site.json: game_build and game_build_update_dir are needed (see game_build_note)' }
function Rank($p) { $m = [regex]::Match($p, 'patchday(\d+)'); if ($m.Success) { return 100 + [int]$m.Groups[1].Value }; if ($p -match 'dlc_patch') { return 60 }; if ($p -match 'dlcpacks') { return 50 }; return 0 }
function Add-RpfTree($f) { $GameRpfs.Add($f); if ($f.Children) { foreach ($c in $f.Children) { Add-RpfTree $c } } }
function Find-Entry($f, $name) { foreach ($e in $f.AllEntries) { if ($e.Path -like "*\$name") { return $e } }; if ($f.Children) { foreach ($c in $f.Children) { $r = Find-Entry $c $name; if ($r) { return $r } } }; return $null }
$buildRpfs = @()
foreach ($n in 'update.rpf', 'update2.rpf') {
  $path = Join-Path $site.game_build_update_dir $n
  if (-not (Test-Path -LiteralPath $path)) { throw "the build's $n is missing: $path (site.json game_build_update_dir)" }
  $u = New-Object CodeWalker.GameFiles.RpfFile($path, "update\$n")
  $u.ScanStructure([Action[string]]{ param($s) }, [Action[string]]{ param($s) })
  if ($u.LastError) { throw "the build's $n did not open: $($u.LastError.Message)" }
  $buildRpfs += , $u }
$dl = Find-Entry $buildRpfs[0] 'common\data\dlclist.xml'
if (-not $dl) { throw "the build's update.rpf has no common\data\dlclist.xml" }
$buildDlcs = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($m in [regex]::Matches([Text.Encoding]::UTF8.GetString($dl.File.ExtractFile($dl)), '(?i)dlcpacks:?[\\/]+([^\\/<]+)')) { [void]$buildDlcs.Add($m.Groups[1].Value.ToLower()) }
$GameRpfs = New-Object System.Collections.Generic.List[object]
$rpfm = New-Object CodeWalker.GameFiles.RpfManager
$rpfm.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$skipped = @{}
foreach ($f in $rpfm.AllRpfs) {
  $p = $f.Path.ToLower()
  if ($p -match '^update\\update2?\.rpf') { continue }                                     # the Steam install's own (newer) update
  $m = [regex]::Match($p, '\\dlcpacks\\([^\\]+)\\')
  if ($m.Success -and -not $buildDlcs.Contains($m.Groups[1].Value)) { $skipped[$m.Groups[1].Value] = $true; continue }   # a pack the build does not mount
  $GameRpfs.Add($f) }
foreach ($u in $buildRpfs) { Add-RpfTree $u }
[Console]::Error.WriteLine("GAME_FILES build $($site.game_build): $($buildDlcs.Count) packs in its dlclist, $($GameRpfs.Count) archives; packs left out: $(($skipped.Keys | Sort-Object) -join ' ')")
