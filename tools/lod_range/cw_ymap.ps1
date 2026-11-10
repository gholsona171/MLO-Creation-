# ymap <-> CodeWalker XML with a round-trip gate (MLO-Creation tools/texture_rebrand/cw_meta.ps1 logic)
#   cw_ymap.ps1 export <in.ymap> <out.xml>
#   cw_ymap.ps1 build  <in.xml> <out.ymap>   compiles, re-exports, and fails unless the re-export equals the XML
param([string]$Mode, [string]$In, [string]$Out)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
function Export-Xml([byte[]]$b) { $y = New-Object CodeWalker.GameFiles.YmapFile; $y.Load($b); $fn = ''; [CodeWalker.GameFiles.MetaXml]::GetXml($y, [ref]$fn) }
if ($Mode -eq 'export') {
  [IO.File]::WriteAllText($Out, (Export-Xml ([IO.File]::ReadAllBytes($In)))); "exported $In"
} elseif ($Mode -eq 'build') {
  $src = [IO.File]::ReadAllText($In)
  $doc = New-Object System.Xml.XmlDocument; $doc.LoadXml($src)
  $bytes = [CodeWalker.GameFiles.XmlMeta]::GetData($doc, [CodeWalker.GameFiles.MetaFormat]::RSC, (Split-Path $In))
  $back = Export-Xml $bytes
  if (($back -replace '\r', '') -ne ($src -replace '\r', '')) { [IO.File]::WriteAllText("$Out.back.xml", $back); throw "ROUND-TRIP MISMATCH $In (see $Out.back.xml)" }
  [IO.File]::WriteAllBytes($Out, $bytes); "built $Out ($($bytes.Length) bytes), round-trip identical"
} else { throw 'mode: export | build' }
