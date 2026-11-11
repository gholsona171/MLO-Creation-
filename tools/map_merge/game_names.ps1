# game_names.ps1 -Out <names.txt>: every file name (no extension, lower case) in every GTA V RPF, one per line (about 245k).
# Pair with hash_names.py to resolve hash_XXXXXXXX archetype / txd / ymap names that the prop catalogue does not know (vegetation,
# rubbish, road props): py -3 -I hash_names.py names.txt 98B1C712 ... -> "98B1C712 prop_bush_med_03" (2026-11-11, anarchy trap house).
param([string]$Out)
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$h = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }; foreach ($e in $f.AllEntries) { [void]$h.Add([IO.Path]::GetFileNameWithoutExtension($e.NameLower)) } }
[IO.File]::WriteAllLines($Out, [string[]]@($h))
"names $($h.Count)"
