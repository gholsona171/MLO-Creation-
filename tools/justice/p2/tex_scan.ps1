# tex_scan.ps1 (read-only on the game): every texture whose NAME matches -Rx, in every .ytd whose path matches -Path; lists
# name / size / ytd and (with -Out) saves a 128 px PNG of each (top mip). The survey of Rockstar's own stone / glass recipes (p2).
param([string]$Rx, [string]$Path = '_citye|_cityw', [string]$Out = '')
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll"); Add-Type -AssemblyName System.Drawing
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
if ($Out) { New-Item -ItemType Directory -Force $Out | Out-Null }
$seen = @{}
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) {
    if (-not $e.Name.EndsWith('.ytd') -or $e.Path -notmatch $Path) { continue }
    $y = New-Object CodeWalker.GameFiles.YtdFile
    try { $y.Load($e.File.ExtractFile($e), $e) } catch { continue }
    foreach ($t in $y.TextureDict.Textures.data_items) {
      if ($t.Name -notmatch $Rx) { continue }
      "$($t.Name)`t$($t.Width)x$($t.Height)`t$($e.Name)"
      $k = $t.Name.ToLower(); if (-not $Out -or $seen.ContainsKey($k) -or $t.Name -match '_n$|_s$|_spec|_nrm|_n\.') { continue }; $seen[$k] = 1
      try { $px = [CodeWalker.Utils.DDSIO]::GetPixels($t, 0) } catch { continue }
      $bmp = New-Object System.Drawing.Bitmap($t.Width, $t.Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
      $r = New-Object System.Drawing.Rectangle(0, 0, $t.Width, $t.Height)
      $d = $bmp.LockBits($r, [System.Drawing.Imaging.ImageLockMode]::WriteOnly, $bmp.PixelFormat)
      [Runtime.InteropServices.Marshal]::Copy($px, 0, $d.Scan0, $px.Length); $bmp.UnlockBits($d)
      $sm = New-Object System.Drawing.Bitmap($bmp, 128, 128); $sm.Save((Join-Path $Out "$($t.Name)__$($e.Name).png"), [System.Drawing.Imaging.ImageFormat]::Png); $sm.Dispose(); $bmp.Dispose()
    }
  }
}
