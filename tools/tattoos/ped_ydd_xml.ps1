# Read-only on the game: export freemode ped drawables (ydd) to CodeWalker XML, to read the mesh UV channels the tattoos use.
#   ped_ydd_xml.ps1 -Out <dir> -Names uppr_000_u,hand_000_r [-Ped mp_m_freemode_01]
param([string]$Out, [string]$Names, [string]$Ped = 'mp_m_freemode_01')
$ErrorActionPreference = 'Stop'
$gta = if ($env:GTA_DIR) { $env:GTA_DIR } else { 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V' }
$cw = if ($env:CODEWALKER) { $env:CODEWALKER } else { 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$want = @{}; foreach ($n in ($Names -split ',')) { $want[$n.Trim().ToLower()] = $true }
New-Item -ItemType Directory -Force $Out | Out-Null
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) {
    if (-not $e.Name.EndsWith('.ydd')) { continue }
    if ($e.Path -notmatch ([regex]::Escape("streamedpeds_mp.rpf\$Ped\"))) { continue }   # the base ped, not DLC variants
    $n = [IO.Path]::GetFileNameWithoutExtension($e.Name).ToLower(); if (-not $want[$n]) { continue }
    $y = New-Object CodeWalker.GameFiles.YddFile; $y.Load($e.File.ExtractFile($e), $e)
    $x = [CodeWalker.GameFiles.YddXml]::GetXml($y, (Join-Path $Out "${Ped}_$n"))
    [IO.File]::WriteAllText((Join-Path $Out "${Ped}_$n.ydd.xml"), $x); "found $n <- $($e.Path)"; $want.Remove($n) } }
if ($want.Count) { "not found: $($want.Keys -join ', ')" }
