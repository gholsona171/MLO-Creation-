# Tower City: ybn <-> CodeWalker XML. -Export <in.ybn> <out.xml> | -Import <in.xml> <out.ybn> (RSC7, as the game wants it)
param([string]$Mode, [string]$In, [string]$Out)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\tools\CodeWalker'
if (-not (Test-Path "$cw\CodeWalker.Core.dll")) { $cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
if ($Mode -eq 'export') {
    $y = New-Object CodeWalker.GameFiles.YbnFile; $y.Load([IO.File]::ReadAllBytes($In))
    $fn = ''; $x = [CodeWalker.GameFiles.MetaXml]::GetXml($y, [ref]$fn); [IO.File]::WriteAllText($Out, $x); "exported $($x.Length) chars"
} else {
    $doc = New-Object System.Xml.XmlDocument; $doc.Load($In)
    $y = [CodeWalker.GameFiles.XmlYbn]::GetYbn($doc); $bytes = $y.Save(); [IO.File]::WriteAllBytes($Out, $bytes); "imported -> $($bytes.Length) bytes"
}
