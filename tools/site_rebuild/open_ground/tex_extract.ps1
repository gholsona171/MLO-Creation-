# tex_extract.ps1 (read-only on the game): Rockstar's textures by name, saved as .dds (their own compression, byte for byte) into
# ..\tex\vanilla (wiped first). Each name is looked up in the texture dictionaries of the country / shared texture packs
# (paths matching $Where); the largest copy wins. Writes ..\tex\vanilla\index.tsv (name, size, format, dictionary path).
# Usage: powershell -File tex_extract.ps1 -Names "a,b,c"
param([string]$Names, [string]$Where = '_hills\\country_0|gtxd|\\textures\\|cdimages')
$ErrorActionPreference = 'Stop'
$M = Split-Path $PSScriptRoot -Parent; $Out = Join-Path $M 'tex\vanilla'
if (Test-Path -LiteralPath $Out) { Remove-Item -LiteralPath $Out -Recurse -Force }; New-Item -ItemType Directory -Force $Out | Out-Null
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$want = @{}; foreach ($n in ($Names -split ',')) { if ($n.Trim()) { $want[$n.Trim().ToLower()] = $null } }
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if (-not $e.Name.ToLower().EndsWith('.ytd') -or $e.Path -notmatch $Where) { continue }
    try { $y = New-Object CodeWalker.GameFiles.YtdFile; $y.Load($e.File.ExtractFile($e), $e) } catch { continue }
    if (-not $y.TextureDict -or -not $y.TextureDict.Textures) { continue }
    foreach ($t in $y.TextureDict.Textures.data_items) { $k = $t.Name.ToLower()
      if ($want.ContainsKey($k) -and (-not $want[$k] -or $want[$k][0].Width -lt $t.Width)) { $want[$k] = @($t, $e.Path) } } } }
$rows = @()
foreach ($k in $want.Keys) { if (-not $want[$k]) { throw "texture $k not found" }
  $t = $want[$k][0]; [IO.File]::WriteAllBytes((Join-Path $Out "$k.dds"), [CodeWalker.Utils.DDSIO]::GetDDSFile($t))
  $rows += "$k`t$($t.Width)x$($t.Height)`t$($t.Format)`t$($want[$k][1])" }
[IO.File]::WriteAllLines((Join-Path $Out 'index.tsv'), [string[]]$rows)
"TEX_EXTRACT_PASS $($rows.Count) textures"; $rows
