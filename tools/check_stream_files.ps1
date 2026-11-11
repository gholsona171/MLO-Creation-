<#
.SYNOPSIS
    Finds broken game files (models, textures, maps, collisions) anywhere in the server's resources folder.

.DESCRIPTION
    Every streamed GTA file (.ytd .ydr .yft .ydd .ybn .ymap .ytyp .ycd) is checked the way the game reads it:
      - RSC7 files: the header says how big the file is once unpacked; the packed data is unpacked in full and the
        size must match. A file cut short (a broken upload, a failed copy, a half-finished download) or with damaged
        data fails here. This is the kind of file that makes a player's game hang with
        "Ignoring Z_BUF_ERROR with avail_in == 0" flooding the client log.
      - RSC8 and FXAP files (encrypted, e.g. Cfx escrow): skipped, their data cannot be unpacked outside the game.
      - Anything else (empty files, text, a Git LFS pointer, an HTML error page saved as a .ytd) is reported.
    Nothing is changed. Results go to the screen and to a report file next to this script.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File tools\vps\check-stream-files.ps1
    powershell -ExecutionPolicy Bypass -File tools\vps\check-stream-files.ps1 -Path "C:\FXServer\server-data\resources\[stream]"
#>
param(
    [string]$Path = (Join-Path $PSScriptRoot '..\..\resources'),
    [string]$Report = (Join-Path $PSScriptRoot 'stream-check-report.txt')
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression

$exts = @('.ytd', '.ydr', '.yft', '.ydd', '.ybn', '.ymap', '.ytyp', '.ycd')

function Get-PageSize([uint32]$f) {
    $base = [uint64](0x200 -shl ($f -band 0xF))
    $counts = @(
        (($f -shr 4) -band 0x1), (($f -shr 5) -band 0x3), (($f -shr 7) -band 0xF), (($f -shr 11) -band 0x3F),
        (($f -shr 17) -band 0x7F), (($f -shr 24) -band 0x1), (($f -shr 25) -band 0x1), (($f -shr 26) -band 0x1),
        (($f -shr 27) -band 0x1)
    )
    [uint64]$total = 0
    for ($i = 0; $i -lt 9; $i++) { $total += [uint64]$counts[$i] * ($base * [uint64][math]::Pow(2, 8 - $i)) }
    return $total
}

function Test-StreamFile([string]$file) {
    $bytes = [System.IO.File]::ReadAllBytes($file)
    if ($bytes.Length -eq 0) { return 'EMPTY (0 bytes)' }
    if ($bytes.Length -lt 16) { return "TOO SMALL ($($bytes.Length) bytes)" }
    $magic = [System.Text.Encoding]::ASCII.GetString($bytes, 0, 4)
    if ($magic -eq 'RSC8' -or $magic -eq 'FXAP') { return $null }   # encrypted (RSC8, Cfx escrow FXAP): cannot be unpacked here
    if ($magic -ne 'RSC7') {
        $raw = [System.Text.Encoding]::ASCII.GetString($bytes, 0, [math]::Min(40, $bytes.Length))
        $head = $raw -replace '[^\x20-\x7e]', '.'
        if ($raw.StartsWith('<?xml') -or $raw.StartsWith('<CMap')) { return "NOTE: XML text version of the file ('$head')" }
        if ($raw -match '^[\x09\x0a\x0d\x20-\x7e]+$') { return "NOT A GAME FILE: text, e.g. a Git LFS pointer or a saved web page ('$head')" }
        return "NOTE: unusual header, not checked ('$head')"
    }
    $sys = [BitConverter]::ToUInt32($bytes, 8)
    $gfx = [BitConverter]::ToUInt32($bytes, 12)
    $want = (Get-PageSize $sys) + (Get-PageSize $gfx)
    $ms = [System.IO.MemoryStream]::new($bytes, 16, ($bytes.Length - 16))
    $ds = [System.IO.Compression.DeflateStream]::new($ms, [System.IO.Compression.CompressionMode]::Decompress)
    $buf = New-Object byte[] 1048576
    [uint64]$got = 0
    try {
        while (($n = $ds.Read($buf, 0, $buf.Length)) -gt 0) {
            $got += $n
            if ($got -gt $want) { break }
        }
    } catch {
        return "DAMAGED DATA (unpacking failed after $got of $want bytes: $($_.Exception.Message))"
    } finally { $ds.Dispose() }
    if ($got -ne $want) { return "CUT SHORT OR WRONG SIZE (unpacks to $got bytes, header says $want)" }
    return $null
}

$root = (Resolve-Path $Path).Path
Write-Host "Checking game files under $root ..."
$files = Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $exts -contains $_.Extension.ToLower() }
$bad = New-Object System.Collections.Generic.List[string]
$notes = New-Object System.Collections.Generic.List[string]
$i = 0
foreach ($f in $files) {
    $i++
    if ($i % 500 -eq 0) { Write-Host "  $i / $($files.Count)" }
    try { $why = Test-StreamFile $f.FullName } catch { $why = "COULD NOT READ ($($_.Exception.Message))" }
    if ($why) {
        $rel = $f.FullName.Substring($root.Length).TrimStart('\')
        $line = "$rel  ->  $why"
        if ($why.StartsWith('NOTE:')) { $notes.Add($line); continue }
        $bad.Add($line)
        Write-Host "  BROKEN  $line" -ForegroundColor Red
    }
}

$summary = "Checked $($files.Count) game files under $root on $(Get-Date -Format 'yyyy-MM-dd HH:mm'): $($bad.Count) broken, $($notes.Count) notes (not errors)."
Write-Host ''
if ($bad.Count -eq 0) { Write-Host $summary -ForegroundColor Green } else { Write-Host $summary -ForegroundColor Red }
@($summary, '', 'BROKEN (fix or remove these):') + $bad + @('', 'NOTES (left as they are, listed for reference):') + $notes |
    Set-Content -LiteralPath $Report -Encoding UTF8
Write-Host "Report: $Report"
if ($bad.Count -gt 0) { exit 1 }
