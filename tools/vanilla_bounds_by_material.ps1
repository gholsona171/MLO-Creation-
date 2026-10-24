# Tower City survey (read-only): how Rockstar makes a house pool swimmable - every collision polygon / primitive with a WATER-family
# material in the Rockford Hills / Vinewood Hills area (Michael's house and its neighbours), with its file, type and height range.
# Exports the first such ybn to survey/water/ for a full read.
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$out = Join-Path $PSScriptRoot 'water'; $done = $false; $found = @{}
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if ($e.Name -notmatch '\.ybn$') { continue }
    try { $y = New-Object CodeWalker.GameFiles.YbnFile; $y.Load($e.File.ExtractFile($e), $e) } catch { continue }
    $b = $y.Bounds; if (-not $b) { continue }
    if ($b.BoxMax.X -lt -900 -or $b.BoxMin.X -gt -700 -or $b.BoxMax.Y -lt 100 -or $b.BoxMin.Y -gt 260) { continue }
    $stack = New-Object System.Collections.Stack; $stack.Push($b)
    while ($stack.Count) { $g = $stack.Pop()
      if ($g -is [CodeWalker.GameFiles.BoundComposite]) { foreach ($ch in @($g.Children.data_items)) { if ($ch) { $stack.Push($ch) } }; continue }
      if ($g -is [CodeWalker.GameFiles.BoundGeometry] -and $g.Polygons) {
        foreach ($p in $g.Polygons) { $m = $g.GetMaterial($p.Index); $t = [int]$m.Type.Index; $n = if ($t -eq 125) { 'WATER' } else { "m$t" }
          if ($n -match 'WATER') { $k = "$($e.Path) | $n | $($p.GetType().Name)"; $found[$k] = 1 + [int]$found[$k]
            if (-not $done) { $fn = ''; $x = [CodeWalker.GameFiles.MetaXml]::GetXml($y, [ref]$fn); [IO.File]::WriteAllText((Join-Path $out ($e.Name + '.xml')), $x); $done = $true; "exported $($e.Name)" } } } }
      elseif ($g -isnot [CodeWalker.GameFiles.BoundComposite]) {
        $t = [int]$g.MaterialIndex; $n = if ($t -eq 125) { 'WATER' } else { "m$t" }
        if ($n -match 'WATER') { $k = "$($e.Path) | $n | $($g.GetType().Name) z $([math]::Round($g.BoxMin.Z,2))..$([math]::Round($g.BoxMax.Z,2))"; $found[$k] = 1 + [int]$found[$k] } } } } }
$found.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Value)x $($_.Name)" }
