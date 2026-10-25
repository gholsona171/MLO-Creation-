# archetype details (textureDictionary, flags, lodDist, physicsDictionary) for named archetypes
param([string]$Names)
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$want = @{}; foreach ($n in ($Names -split ',')) { $want[$n.Trim().ToLower()] = $true }
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if ($e.Name -notmatch '\.ytyp$') { continue }
    try { $t = New-Object CodeWalker.GameFiles.YtypFile; $t.Load($e.File.ExtractFile($e), $e) } catch { continue }
    foreach ($a in @($t.AllArchetypes)) { if (-not $a) { continue }; $n = $a.Name.ToLower(); if (-not $want[$n]) { continue }
      $d = $a._BaseArchetypeDef
      "$n`ttxd=$($a.TextureDict)`tflags=$($d.flags)`tlod=$($d.lodDist)`tphys=$($a.PhysicsDict)`tdd=$($a.DrawableDict)`tytyp=$($e.Name)"
      $want.Remove($n) } } }
