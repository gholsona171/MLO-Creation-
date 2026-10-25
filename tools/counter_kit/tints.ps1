# c9_dj counter kit: the tint (palette row) Rockstar gives each named archetype where it is placed (interior MLO entities and ymaps).
# A *_tnt shader takes its colour from a palette texture row chosen by the ENTITY's tint; a script-spawned copy gets row 0, so the
# build copies the row Rockstar uses into row 0 of our palette (counters_out.py). Prints: name <tab> tint values seen <tab> where.
#   powershell -File tints.ps1 -Names bkr_int_02_bar_wood,bkr_bar_bar01
param([string]$Names)
$ErrorActionPreference = 'Stop'
$gta = if ($env:GTA_DIR) { $env:GTA_DIR } else { 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V' }
$cw = if ($env:CODEWALKER) { $env:CODEWALKER } else { 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$want = @{}; foreach ($n in ($Names -split ',')) { $want[[CodeWalker.GameFiles.JenkHash]::GenHash($n.Trim().ToLower())] = $n.Trim() }
$seen = @{}
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) {
    if ($e.Name -notmatch '\.ytyp$') { continue }
    try { $t = New-Object CodeWalker.GameFiles.YtypFile; $t.Load($e.File.ExtractFile($e), $e) } catch { continue }
    foreach ($a in @($t.AllArchetypes)) {
      if (-not ($a -is [CodeWalker.GameFiles.MloArchetype])) { continue }
      foreach ($ent in @($a.entities)) {
        if (-not $ent) { continue }
        $h = [uint32]$ent._CEntityDef.archetypeName
        if ($want.ContainsKey($h)) { $k = $want[$h]; $seen["$k|$($ent._CEntityDef.tintValue)|$($e.Name)"] = 1 }
      }
    }
  }
}
$seen.Keys | Sort-Object
