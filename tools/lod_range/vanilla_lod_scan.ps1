# vanilla_lod_scan.ps1 > out.tsv : every entity with lodDist >= 2500 in the game's LOD / SLOD ymaps and Cayo Perico (h4_) ymaps
# (ymap path, entity, lodDist, childLodDist, lod level, x,y, children). Used to pick a realistic far range for a distant model.
# Results 2026-11-10: Cayo terrain SLOD2 2500 / SLOD3 5000 / SLOD4 10000, Cayo prop SLOD3 4000 / SLOD4 8000, prologue distant LODs 4000,
# city SLOD3 / emissive SLOD2 8000-15000 (all tiny low-poly models).
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if ($e.Name -notmatch '\.ymap$') { continue }
    if ($e.Name -notmatch '^(h4_|.*lod|.*slod)') { continue }
    try { $y = New-Object CodeWalker.GameFiles.YmapFile; $y.Load($e.File.ExtractFile($e), $e) } catch { continue }
    foreach ($ent in @($y.AllEntities)) { if (-not $ent) { continue }; $d = $ent._CEntityDef
      if ($d.lodDist -ge 2500) { "{0}`t{1}`t{2}`t{3}`t{4}`t{5:N0},{6:N0}`t{7}" -f $e.Path, $ent.Name, $d.lodDist, $d.childLodDist, $d.lodLevel, $d.position.X, $d.position.Y, $d.numChildren } } } }
