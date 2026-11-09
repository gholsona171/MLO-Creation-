# Import every <name>.ymap.xml in -In to <name>.ymap in -Out with CodeWalker XmlMeta (ymap_import.ps1 method), then load-check name/parent
param([string]$In, [string]$Out)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\tools\CodeWalker'
if (-not (Test-Path "$cw\CodeWalker.Core.dll")) { $cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
New-Item -ItemType Directory -Force $Out | Out-Null
foreach ($f in Get-ChildItem $In -Filter '*.ymap.xml') { $name = $f.Name -replace '\.xml$',''
  $doc = New-Object System.Xml.XmlDocument; $doc.Load($f.FullName)
  $bytes = [CodeWalker.GameFiles.XmlMeta]::GetData($doc, [CodeWalker.GameFiles.MetaFormat]::RSC, $name)
  [IO.File]::WriteAllBytes((Join-Path $Out $name), $bytes)
  $y = New-Object CodeWalker.GameFiles.YmapFile; $y.Load($bytes)
  $n = $y._CMapData.name; $p = $y._CMapData.parent
  "$name bytes=$($bytes.Length) loaded=$($y.Loaded) name=$n parent=$p entities=$($y.AllEntities.Length) boxes=$($y.BoxOccluders.Length) models=$($y.OccludeModels.Length) lodlights=$(if ($y.LODLights) { $y.LODLights.LodLights.Length } else { 0 }) dist=$(if ($y.DistantLODLights) { $y.DistantLODLights.positions.Length } else { 0 }) cargens=$($y.CarGenerators.Length)" }
