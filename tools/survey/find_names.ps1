# Justice Center survey (read-only): archetype names matching a regex across every ytyp, with ytyp + bounds.
param([string]$Rx = 'hall|court|civic|monument')
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) {
    if ($e.Name -match '\.(ydr|ydd|ybn|ymap)$' -and $e.Name -match $Rx) { "FILE`t$($e.Path)" }
    if ($e.Name -notmatch '\.ytyp$') { continue }
    try { $t = New-Object CodeWalker.GameFiles.YtypFile; $t.Load($e.File.ExtractFile($e), $e) } catch { continue }
    foreach ($a in @($t.AllArchetypes)) { if ($a -and $a.Name -match $Rx) { "ARCH`t$($a.Name)`t$($e.Name)`t$($a._BaseArchetypeDef.bbMin)`t$($a._BaseArchetypeDef.bbMax)" } } } }
