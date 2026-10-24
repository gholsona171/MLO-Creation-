# Tower City survey (read-only): export a game MLO (its whole source ytyp + its placement ymap) to XML, plus a summary JSON:
# rooms, portals, entities, entity sets, and the ytyp that defines every entity archetype (the replica's deps).
# Usage: powershell -File survey/export_mlo.ps1 -Names sf_dlc_office_sec,vw_dlc_casino_apart   -> survey/replica/<mlo>.*
param([string[]]$Names)
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
function AN($en) { $d = $en._Data; if (-not $d) { $d = $en._CEntityDef }; return $d.archetypeName.ToString() }   # MCEntityDef (ytyp) / YmapEntityDef
$out = Join-Path $PSScriptRoot 'replica'; New-Item -ItemType Directory -Force $out | Out-Null
$want = @{}; foreach ($n in ($Names -split ",")) { if ($n.Trim()) { $want[$n.Trim().ToLower()] = $true } }
$archTyp = @{}                                   # archetype name -> ytyp name (last one wins: dlc patches override base)
$mlos = @{}                                      # mlo name -> @{ arch; ytypEntry; ytypFile }
$ymaps = @{}                                     # mlo name -> ymap entry
foreach ($f in $rpf.AllRpfs) {
    if (-not $f.AllEntries) { continue }
    foreach ($e in $f.AllEntries) {
        if ($e.Name -match '\.ytyp$') {
            try { $t = New-Object CodeWalker.GameFiles.YtypFile; $t.Load($e.File.ExtractFile($e), $e) } catch { continue }
            $tn = [IO.Path]::GetFileNameWithoutExtension($e.Name)
            foreach ($a in $t.AllArchetypes) {
                $an = $a.Name.ToLower(); $archTyp[$an] = $tn
                if ($want[$an] -and ($a -is [CodeWalker.GameFiles.MloArchetype])) { $mlos[$an] = @{ arch = $a; entry = $e; file = $t } }
            }
        }
        elseif ($e.Name -match '\.ymap$') {
            if ($e.Name -notmatch 'milo|penthouse|placement|sf_') { continue }
            try { $y = New-Object CodeWalker.GameFiles.YmapFile; $y.Load($e.File.ExtractFile($e), $e) } catch { continue }
            foreach ($m in @($y.AllEntities | Where-Object { $_.IsMlo })) {
                $n = $m._CEntityDef.archetypeName.ToString().ToLower(); if ($want[$n]) { $ymaps[$n] = @{ entry = $e; file = $y } }
            }
        }
    }
}
foreach ($n in $want.Keys) {
    if (-not $mlos[$n]) { Write-Warning "MLO $n not found"; continue }
    $m = $mlos[$n]; $a = $m.arch
    $fn = ''; $x = [CodeWalker.GameFiles.MetaXml]::GetXml($m.file, [ref]$fn); Set-Content (Join-Path $out "$n.ytyp.xml") $x -Encoding utf8
    if ($ymaps[$n]) { $fn = ''; $x = [CodeWalker.GameFiles.MetaXml]::GetXml($ymaps[$n].file, [ref]$fn); Set-Content (Join-Path $out "$n.milo.ymap.xml") $x -Encoding utf8 }
    $deps = @{}; $missing = @()
    $allEnts = @($a.entities)
    foreach ($s in @($a.entitySets | Where-Object { $_ })) { $allEnts += @($s.Entities) }
    foreach ($en in $allEnts) { $m2 = (AN $en).ToLower(); if ($archTyp[$m2]) { $deps[$archTyp[$m2]] = $true } else { $missing += $m2 } }
    $sets = @($a.entitySets | Where-Object { $_ } | ForEach-Object {
        [ordered]@{ name = "$($_._Data.name)"; entities = @($_.Entities).Count; models = @(@($_.Entities) | Select-Object -First 5 | ForEach-Object { (AN $_) }) } })
    $sum = [ordered]@{ name = $n; ytyp_path = $m.entry.Path; ytyp_name = [IO.Path]::GetFileNameWithoutExtension($m.entry.Name)
        ymap_path = $(if ($ymaps[$n]) { $ymaps[$n].entry.Path } else { $null })
        rooms = @($a.rooms | ForEach-Object { $_.RoomName }); portals = @($a.portals).Count; entities = @($a.entities).Count
        entity_sets = $sets; deps = @($deps.Keys | Sort-Object); unresolved = @($missing | Sort-Object -Unique)
        archetype_ytyp = @{} }
    foreach ($en in $allEnts) { $m2 = (AN $en).ToLower(); if ($archTyp[$m2]) { $sum.archetype_ytyp[$m2] = $archTyp[$m2] } }
    $sum | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $out "$n.json") -Encoding utf8
    '{0,-28} rooms {1,2} portals {2,3} entities {3,4} sets {4,2} deps {5,2} unresolved {6}' -f $n, $sum.rooms.Count, $sum.portals, $sum.entities, $sets.Count, $sum.deps.Count, $sum.unresolved.Count
    foreach ($s in $sets) { '    set {0,-36} {1,4} ents  e.g. {2}' -f $s.name, $s.entities, ($s.models -join ', ') }
}
