# Tower City survey (read-only on the game): extract game files by exact archive path to a folder.
# Usage: powershell -File survey/extract_file.ps1 -Out src/game -Paths "update\update.rpf\...\dt1_11.rpf\hei_dt1_11_carpark.ybn"
param([string]$Out, [string[]]$Paths)
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
New-Item -ItemType Directory -Force $Out | Out-Null
foreach ($p in $Paths) {
  $e = $rpf.GetEntry($p); if (-not $e) { Write-Warning "not found: $p"; continue }
  $b = $e.File.ExtractFile($e)
  if ($e.Name -match '\.ybn$') { $y = New-Object CodeWalker.GameFiles.YbnFile; $y.Load($b, $e); $b = $y.Save() }   # raw resource data -> a standalone RSC7 file
  [IO.File]::WriteAllBytes((Join-Path $Out $e.Name), $b); "$($e.Name) $($b.Length) bytes"
}
