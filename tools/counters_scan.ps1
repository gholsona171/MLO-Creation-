# every archetype that could be a counter: name pattern + counter-like bounds. TSV: name ytyp interior txd sx sy sz zmin phys flags lod
param([string]$Out = 'counters_scan.tsv')
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$pat = 'counter|ctr|cntr|desk|bar|till|checkout|reception|recep|island|kitchen|kit_|deli|display|disp|case|cab|worktop|prep|serv|cashier|register|pay|cafe|diner|dine|sushi|ramen|food|bakery|kiosk|stand|unit|bench|table|top|front|booth|ff_|bs_|cb_|bean|cof'
$seen = @{}; $rows = New-Object System.Collections.Generic.List[string]
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if ($e.Name -notmatch '\.ytyp$') { continue }
    try { $t = New-Object CodeWalker.GameFiles.YtypFile; $t.Load($e.File.ExtractFile($e), $e) } catch { continue }
    $int = if ($e.Path -match 'interiors') { 'int' } else { 'prop' }
    foreach ($a in @($t.AllArchetypes)) { if (-not $a) { continue }; $n = $a.Name.ToLower(); if ($seen[$n] -or $n -notmatch $pat) { continue }
      $d = $a._BaseArchetypeDef; $sx = $d.bbMax.X - $d.bbMin.X; $sy = $d.bbMax.Y - $d.bbMin.Y; $sz = $d.bbMax.Z - $d.bbMin.Z
      if ($sz -lt 0.75 -or $sz -gt 1.45 -or [math]::Max($sx,$sy) -lt 0.8 -or [math]::Max($sx,$sy) -gt 8 -or [math]::Min($sx,$sy) -lt 0.3) { continue }
      $seen[$n] = 1
      $rows.Add((('{0}|{1}|{2}|{3}|{4:N2}|{5:N2}|{6:N2}|{7:N2}|{8}|{9}|{10}') -f $n, [IO.Path]::GetFileNameWithoutExtension($e.Name), $int, $a.TextureDict, $sx, $sy, $sz, $d.bbMin.Z, $a.PhysicsDict, $d.flags, $d.lodDist)) } } }
$rows | Set-Content $Out -Encoding utf8
"$($rows.Count) rows"
