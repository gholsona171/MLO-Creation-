param([string]$In, [string]$Out)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\tools\CodeWalker'
if (-not (Test-Path "$cw\CodeWalker.Core.dll")) { $cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
$y = New-Object CodeWalker.GameFiles.YtypFile; $y.Load([IO.File]::ReadAllBytes($In))
$fn = ''; $x = [CodeWalker.GameFiles.MetaXml]::GetXml($y, [ref]$fn); [IO.File]::WriteAllText($Out, $x); "exported $In -> $($x.Length)"
