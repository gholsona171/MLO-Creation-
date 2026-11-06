param([string]$Out, [string[]]$Names = @('lr_sc1_occl_00.ymap','sc1_28_0.ybn','hi@sc1_28_0.ybn'))
$ErrorActionPreference = 'Stop'
$Names = @($Names | % { $_ -split ',' } | % { $_.Trim() } | ? { $_ })
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\tools\CodeWalker'
if (-not (Test-Path "$cw\CodeWalker.Core.dll")) { $cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if ($e.Name -notin $Names) { continue }
    $b = $e.File.ExtractFile($e)
    if ($e.Name -match '\.ybn$') { $y = New-Object CodeWalker.GameFiles.YbnFile; $y.Load($b, $e); $b = $y.Save() }
    elseif ($e.Name -match '\.ymap$') { $y = New-Object CodeWalker.GameFiles.YmapFile; $y.Load($b, $e); $b = $y.Save() }
    $tag = ($e.Path -replace '[\:]','_')
    $dir = Join-Path $Out $tag; New-Item -ItemType Directory -Force $dir | Out-Null
    [IO.File]::WriteAllBytes((Join-Path $dir $e.Name), $b); "$($e.Path) -> $tag $($b.Length) bytes"
  } }
