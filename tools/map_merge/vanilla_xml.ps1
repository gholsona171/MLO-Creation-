# Vanilla game files by exact archive path -> <Out>\<name> (ybn: RSC7 via Save; ymap: raw entry re-wrapped is not possible, so XML only) + <Out>\xml\<name>.xml
param([string]$Out, [string]$Paths)
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\tools\CodeWalker'
if (-not (Test-Path "$cw\CodeWalker.Core.dll")) { $cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
New-Item -ItemType Directory -Force "$Out\xml" | Out-Null
foreach ($p in ($Paths -split ';')) { $e = $rpf.GetEntry($p); if (-not $e) { Write-Warning "not found: $p"; continue }
  $b = $e.File.ExtractFile($e); $fn = ''
  if ($e.Name -match '\.ybn$') { $y = New-Object CodeWalker.GameFiles.YbnFile; $y.Load($b, $e); [IO.File]::WriteAllBytes("$Out\$($e.Name)", $y.Save()) }
  elseif ($e.Name -match '\.ymap$') { $y = New-Object CodeWalker.GameFiles.YmapFile; $y.Load($b, $e) }
  else { "$($e.Name): $($e.FileSize) bytes in archive, $($b.Length) bytes unpacked ($p)"; continue }
  $x = [CodeWalker.GameFiles.MetaXml]::GetXml($y, [ref]$fn); [IO.File]::WriteAllText("$Out\xml\$($e.Name).xml", $x); "$($e.Name): xml $($x.Length) chars ($p)"
  if ($e.Name -match '\.ymap$') { $doc = New-Object System.Xml.XmlDocument; $doc.LoadXml($x); [IO.File]::WriteAllBytes("$Out\$($e.Name)", [CodeWalker.GameFiles.XmlMeta]::GetData($doc, [CodeWalker.GameFiles.MetaFormat]::RSC, $e.Name)) }
}
