# CodeWalker import of our props: <name>.ydr.xml / <name>.yft.xml (textures in the <name>\ folder beside the xml) -> binaries,
# then load each result back and print what it holds (embedded textures, geometry count, cloth).
#   cw_import.ps1 -Xml <xml dir> -Out <stream dir>
param([string]$Xml, [string]$Out)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
New-Item -ItemType Directory -Force $Out | Out-Null
foreach ($f in Get-ChildItem $Xml -Filter *.xml) {
  $doc = New-Object System.Xml.XmlDocument; $doc.Load($f.FullName)
  $name = $f.Name -replace '\.(ydr|yft)\.xml$', ''
  $tex = Join-Path $Xml $name
  if ($f.Name -like '*.ydr.xml') {
    $bytes = ([CodeWalker.GameFiles.XmlYdr]::GetYdr($doc, $tex)).Save(); $p = Join-Path $Out "$name.ydr"; [IO.File]::WriteAllBytes($p, $bytes)
    $c = New-Object CodeWalker.GameFiles.YdrFile; $c.Load($bytes); $d = $c.Drawable
  } else {
    $bytes = ([CodeWalker.GameFiles.XmlYft]::GetYft($doc, $tex)).Save(); $p = Join-Path $Out "$name.yft"; [IO.File]::WriteAllBytes($p, $bytes)
    $c = New-Object CodeWalker.GameFiles.YftFile; $c.Load($bytes); $d = $c.Fragment.Drawable
  }
  $tx = @($d.ShaderGroup.TextureDictionary.Textures.data_items | % { "$($_.Name) $($_.Width)x$($_.Height) $($_.Format) L$($_.Levels)" }) -join '; '
  $geo = ($d.DrawableModels.High | % { $_.Geometries.Count } | Measure-Object -Sum).Sum
  $cloth = if ($c -is [CodeWalker.GameFiles.YftFile]) { " cloth=$([bool]$c.Fragment.Cloths)" } else { '' }
  "{0} {1} bytes, geometries {2}, textures [{3}]{4}" -f (Split-Path $p -Leaf), $bytes.Length, $geo, $tx, $cloth
}
