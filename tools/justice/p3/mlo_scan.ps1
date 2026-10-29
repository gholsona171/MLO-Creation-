# Justice Center phase 3 survey (read-only): every MLO archetype (interior) in the game whose name, or any of whose entity
# archetypes, matches a regex: rooms, portals count, and entity archetype counts. Also every plain archetype matching the regex.
param([string]$Rx = 'police|sheriff|_ph_|cell|jail|prison|court|judge|jury|mugshot|lspd|cop|gavel|metaldet|xray|security', [string]$Out = 'mlo_scan.tsv')
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$sw = New-Object System.IO.StreamWriter($Out, $false)
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) {
    if ($e.Name -notmatch '\.ytyp$') { continue }
    try { $t = New-Object CodeWalker.GameFiles.YtypFile; $t.Load($e.File.ExtractFile($e), $e) } catch { continue }
    foreach ($a in @($t.AllArchetypes)) { if (-not $a) { continue }
      if ($a -is [CodeWalker.GameFiles.MloArchetype]) {
        $names = @{}
        foreach ($en in @($a.entities)) { if ($en) { $n = $en._Data.archetypeName.ToString(); $names[$n] = 1 + [int]$names[$n] } }
        $hit = ($a.Name -match $Rx) -or (@($names.Keys | Where-Object { $_ -match $Rx }).Count -gt 0)
        if ($hit) {
          $rooms = (@($a.rooms) | ForEach-Object { $_.RoomName }) -join ','
          $sw.WriteLine("MLO`t$($a.Name)`t$($e.Path)`trooms=$rooms`tportals=$(@($a.portals).Count)`tents=$(@($a.entities).Count)")
          foreach ($k in $names.Keys) { $sw.WriteLine("ENT`t$($a.Name)`t$k`t$($names[$k])") } }
      } elseif ($a.Name -match $Rx) {
        $d = $a._BaseArchetypeDef
        $sw.WriteLine("ARCH`t$($a.Name)`t$($e.Name)`t$($d.bbMin.X),$($d.bbMin.Y),$($d.bbMin.Z)`t$($d.bbMax.X),$($d.bbMax.Y),$($d.bbMax.Z)`ttxd=$($a.TextureDict)`tflags=$($d.flags)`tattr=$($d.specialAttribute)")
      } } } }
$sw.Close(); "MLO_SCAN_DONE"
