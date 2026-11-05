# export|import ymap/ybn <-> CodeWalker XML
param([string]$Mode, [string]$In, [string]$Out)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\tools\CodeWalker'
if (-not (Test-Path "$cw\CodeWalker.Core.dll")) { $cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
if ($Mode -eq 'export') {
  $bytes = [IO.File]::ReadAllBytes($In)
  if ($In -match '\.ymap$') { $y = New-Object CodeWalker.GameFiles.YmapFile } else { $y = New-Object CodeWalker.GameFiles.YbnFile }
  $y.Load($bytes); $fn = ''; $x = [CodeWalker.GameFiles.MetaXml]::GetXml($y, [ref]$fn); [IO.File]::WriteAllText($Out, $x); "exported $In -> $($x.Length) chars"
} else {
  $doc = New-Object System.Xml.XmlDocument; $doc.Load($In)
  if ($Out -match '\.ymap$') { $m = [CodeWalker.GameFiles.XmlMeta]::GetMeta($doc); $y = New-Object CodeWalker.GameFiles.YmapFile; $y.Load([CodeWalker.GameFiles.ResourceBuilder]::Build($m, 2)) ; $bytes = $y.Save() }
  else { $y = [CodeWalker.GameFiles.XmlYbn]::GetYbn($doc); $bytes = $y.Save() }
  [IO.File]::WriteAllBytes($Out, $bytes); "imported -> $($bytes.Length) bytes"
}
