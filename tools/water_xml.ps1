# Tower City survey (read-only): every water*.xml in the game archives (the swim volumes: ocean, rivers, every pool) -> survey/water/
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$out = Join-Path $PSScriptRoot 'water'; New-Item -ItemType Directory -Force $out | Out-Null
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) {
    if ($e.Name -match '^water.*\.xml$') {
      $b = $e.File.ExtractFile($e); $n = ($e.Path -replace '[\\/:]', '_')
      [IO.File]::WriteAllBytes((Join-Path $out $n), $b); "$($e.Path) $($b.Length)" } } }
