# Tower City survey (read-only): find the collision file (ybn) behind an MLO's hashed physicsDictionary and extract it to
# survey/replica/<mlo>.ybn, so our replica can ship its collision under our own name (with our landing's collision merged in).
# Usage: powershell -File survey/export_mlo_ybn.ps1 -Pairs "vw_dlc_casino_apart=202CE536,sf_dlc_office_sec=F4449841"
param([string]$Pairs)
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$out = Join-Path $PSScriptRoot 'replica'
$want = @{}; foreach ($p in ($Pairs -split ',')) { $kv = $p.Trim() -split '='; if ($kv.Count -eq 2) { $want[[uint32]('0x' + $kv[1])] = $kv[0] } }
$found = @{}
foreach ($f in $rpf.AllRpfs) {
    if (-not $f.AllEntries) { continue }
    foreach ($e in $f.AllEntries) {
        if ($e.Name -notmatch '\.ybn$') { continue }
        $h = [CodeWalker.GameFiles.JenkHash]::GenHash([IO.Path]::GetFileNameWithoutExtension($e.Name).ToLower())
        if ($want[$h]) { $found[$h] = $e; "$($want[$h]) <- $($e.Path)  ($($e.Name))" }
    }
}
foreach ($h in $want.Keys) {
    if (-not $found[$h]) { Write-Warning ("no ybn hashes to {0:X8} ({1})" -f $h, $want[$h]); continue }
    $e = $found[$h]; $bytes = $e.File.ExtractFile($e)
    [IO.File]::WriteAllBytes((Join-Path $out ($want[$h] + '.ybn')), $bytes)
    $y = New-Object CodeWalker.GameFiles.YbnFile; $y.Load($bytes, $e)
    $fn = ''; $x = [CodeWalker.GameFiles.MetaXml]::GetXml($y, [ref]$fn)
    "{0}: {1} bytes, xml {2} chars, name {3}" -f $want[$h], $bytes.Length, $x.Length, $e.Name
}
