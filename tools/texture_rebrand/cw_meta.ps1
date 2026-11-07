# compile CodeWalker meta XML (ymap / ytyp) -> RSC, export it again and compare with the XML it came from (round-trip gate)
#   cw_meta.ps1 -Xml <dir of *.ymap.xml / *.ytyp.xml> -Out <dir>
param([string]$Xml, [string]$Out)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
New-Item -ItemType Directory -Force $Out | Out-Null
foreach ($f in Get-ChildItem $Xml -Filter *.xml) {
  $doc = New-Object System.Xml.XmlDocument; $doc.Load($f.FullName)
  $bytes = [CodeWalker.GameFiles.XmlMeta]::GetData($doc, [CodeWalker.GameFiles.MetaFormat]::RSC, $Xml)
  $name = $f.Name -replace '\.xml$', ''; $p = Join-Path $Out $name; [IO.File]::WriteAllBytes($p, $bytes)
  if ($name -like '*.ymap') { $y = New-Object CodeWalker.GameFiles.YmapFile } else { $y = New-Object CodeWalker.GameFiles.YtypFile }
  $y.Load($bytes); $fn = ''; $back = [CodeWalker.GameFiles.MetaXml]::GetXml($y, [ref]$fn)
  $same = ($back -replace '\r', '') -eq ((Get-Content $f.FullName -Raw) -replace '\r', '')
  "{0} {1} bytes, round-trip identical: {2}" -f $name, $bytes.Length, $same
  if (-not $same) { [IO.File]::WriteAllText("$p.back.xml", $back) }
}
