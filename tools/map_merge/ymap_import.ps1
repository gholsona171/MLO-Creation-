# CodeWalker XML -> ymap (RSC7) via XmlMeta, the same way CodeWalker's own XML import does; name comes from <name> in the XML
param([string]$In, [string]$Out)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\tools\CodeWalker'
if (-not (Test-Path "$cw\CodeWalker.Core.dll")) { $cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
$doc = New-Object System.Xml.XmlDocument; $doc.Load($In)
$bytes = [CodeWalker.GameFiles.XmlMeta]::GetData($doc, [CodeWalker.GameFiles.MetaFormat]::RSC, [IO.Path]::GetFileName($Out))
[IO.File]::WriteAllBytes($Out, $bytes); "imported -> $($bytes.Length) bytes"
