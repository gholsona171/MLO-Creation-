# Read-only on the game: extract every pedDecorationCollection overlay XML (*overlays.xml) and every shop_tattoo.meta from the
# GTA V install (best-ranked copy per name), plus named tattoo ytds.
#   powershell -File scan_overlays.ps1 -Out ..\ref\overlays [-Ytd mpbiker_overlays.ytd,...]
param([string]$Out, [string[]]$Ytd = @())
$ErrorActionPreference = 'Stop'
$gta = if ($env:GTA_DIR) { $env:GTA_DIR } else { 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V' }
$cw = if ($env:CODEWALKER) { $env:CODEWALKER } else { 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
function Rank($p) { $m = [regex]::Match($p, 'patchday(\d+)'); if ($m.Success) { return 100 + [int]$m.Groups[1].Value }; if ($p -match 'dlc_patch') { return 60 }; if ($p -match 'dlcpacks') { return 50 }; return 0 }
$want = @{}; foreach ($n in $Ytd) { foreach ($m in ($n -split ',')) { if ($m) { $want[$m.ToLower()] = $null } } }
$xml = @{}; $shops = New-Object System.Collections.ArrayList
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { $k = $e.Name.ToLower()
    if ($k.EndsWith('overlays.xml')) { if (-not $xml[$k] -or (Rank $xml[$k].Path) -le (Rank $e.Path)) { $xml[$k] = $e } }
    elseif ($k -eq 'shop_tattoo.meta') { [void]$shops.Add($e) }
    elseif ($want.ContainsKey($k)) { if (-not $want[$k] -or (Rank $want[$k].Path) -le (Rank $e.Path)) { $want[$k] = $e } } } }
New-Item -ItemType Directory -Force $Out | Out-Null
foreach ($k in $xml.Keys) { $e = $xml[$k]; [IO.File]::WriteAllBytes((Join-Path $Out $e.Name), $e.File.ExtractFile($e)); "xml $($e.Name) <- $($e.Path)" }
$i = 0; foreach ($e in $shops) { $i++; $n = ($e.Path -replace '[\\/:]', '_'); [IO.File]::WriteAllBytes((Join-Path $Out "shop_$n"), $e.File.ExtractFile($e)) }
"shop_tattoo.meta copies: $i"
foreach ($k in $want.Keys) { $e = $want[$k]; if (-not $e) { Write-Warning "not found: $k"; continue }
  $y = New-Object CodeWalker.GameFiles.YtdFile; $y.Load($e.File.ExtractFile($e), $e)
  $d = Join-Path $Out ([IO.Path]::GetFileNameWithoutExtension($e.Name)); New-Item -ItemType Directory -Force $d | Out-Null
  foreach ($t in $y.TextureDict.Textures.data_items) {
    [IO.File]::WriteAllBytes((Join-Path $d "$($t.Name).dds"), [CodeWalker.Utils.DDSIO]::GetDDSFile($t))
    "$($e.Name) $($t.Name) $($t.Width)x$($t.Height) $($t.Format) L$($t.Levels)" }
  "ytd $($e.Name) <- $($e.Path)" }
