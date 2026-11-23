$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if ($e.NameLower -notmatch '.ytyp$') { continue }
    try { $y = New-Object CodeWalker.GameFiles.YtypFile; $y.Load($e.File.ExtractFile($e), $e) } catch { continue }
    foreach ($a in $y.AllArchetypes) { if ($a.Name -like 'cs4_02_sy_wallc*') { "TXD $($e.Path) $($a.Name) txd=$([CodeWalker.GameFiles.JenkIndex]::GetString($a._BaseArchetypeDef.textureDictionary.Hash)) lod=$($a._BaseArchetypeDef.lodDist) bb=$($a._BaseArchetypeDef.bbMin) $($a._BaseArchetypeDef.bbMax)" } } } }
