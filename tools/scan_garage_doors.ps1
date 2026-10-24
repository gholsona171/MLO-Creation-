# Tower City survey (read-only): every archetype with special attribute 5 (garage door: roll-up / tilt, the game drives it),
# its bounds, flags and ytyp. Output (tab separated) -> survey/doors_garage.json via py (see the tower parking, 2026-10-23).
# Run: powershell -File scan_garage_doors.ps1 > garage_doors.tsv
$ErrorActionPreference = 'Continue'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$seen = @{}
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if ($e.Name -notmatch '\.ytyp$') { continue }
    try { $y = New-Object CodeWalker.GameFiles.YtypFile; $y.Load($e.File.ExtractFile($e), $e) } catch { continue }
    foreach ($a in $y.AllArchetypes) { $d = $a._BaseArchetypeDef
      if ($d.specialAttribute -ne 5) { continue }
      $n = $a.Name; if ($seen[$n]) { continue }; $seen[$n] = 1
      $mn = $d.bbMin; $mx = $d.bbMax
      "{0}`t{1:N2}`t{2:N2}`t{3:N2}`t{4:N2}`t{5:N2}`t{6:N2}`t{7}`t{8}`t{9}" -f $n, $mn.X, $mn.Y, $mn.Z, $mx.X, $mx.Y, $mx.Z, $d.flags, $e.Name, $d.physicsDictionary } } }
