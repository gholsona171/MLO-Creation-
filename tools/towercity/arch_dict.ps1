# Tower City survey (read-only): for named archetypes, the ytyp that defines them and their drawableDictionary / textureDictionary
# (LOD and SLOD models live in drawable dictionaries: the file to cut). Usage: -Names a,b,c
param([string[]]$Names)
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$want = @{}; foreach ($n in $Names) { foreach ($m in ($n -split ',')) { if ($m) { $want[$m.ToLower()] = 1 } } }
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if (-not $e.Name.ToLower().EndsWith('.ytyp')) { continue }
    try { $t = New-Object CodeWalker.GameFiles.YtypFile; $t.Load($e.File.ExtractFile($e), $e) } catch { continue }
    foreach ($a in @($t.AllArchetypes)) { if (-not $a) { continue }; $n = $a.Name.ToLower(); if (-not $want.ContainsKey($n)) { continue }
      $b = $a._BaseArchetypeDef
      "{0}`t{1}`tdd={2}`ttxd={3}`tasset={4}`tlod={5}" -f $n, $e.Path, $b.drawableDictionary, $b.textureDictionary, $b.assetName, $b.lodDist } } }
