# Tower City survey (read-only): a catalogue of the game's furniture / clutter / cash props - every archetype whose name matches
# the furniture pattern, with its bounding box and owning ytyp. Writes prop_catalogue.json next to this script.
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$pat = 'sofa|couch|chair|stool|table|tbl|desk|bed|cash|money|wardrobe|shelf|shelve|bar_|stool|lamp|rug|plant|art_|safe|gold|bag|case|kitchen|counter|fridge|cabinet|cab_|tv|monitor|bath|sink|toilet|shower|mirror|dresser|bookcase|book|piano|dining|din_|lounge|coffee|stn_|yacht|off_|office|console|ottoman|bench|vase|sculpt|statue|paint|pict|frame|clock|phone|laptop|cup|mug|bottle|glass|tray|towel|pillow|cushion|fire|chand|light|cctv|server|rack|locker|crate|trolley|cart|bin|hamper|wine|champ|vodka|whisk|poster|ammo|gun|weapon|jewel|watch|diamond|brief|duffel|box'
$exclude = '^(vw_vwint|sf_int|ch_int|hei_|v_\d|int_|.*_lprox|.*_blocker|.*_tint|.*_shell|.*_edgeblend|.*_nontint|.*_window|.*_lod)'
$out = [ordered]@{}; $n = 0
foreach ($f in $rpf.AllRpfs) {
    if (-not $f.AllEntries) { continue }
    foreach ($e in $f.AllEntries) {
        if ($e.Name -notmatch '\.ytyp$') { continue }
        $yn = [IO.Path]::GetFileNameWithoutExtension($e.Name)
        if ($yn -notmatch '^(apa_|ex_|ch_|vw_|sf_|bkr_|imp_|hei_|xm_|ba_|v_|int_|prop|m23|tr_|sum_|h4_|xs_|ch1|arena)') { continue }
        try { $t = New-Object CodeWalker.GameFiles.YtypFile; $t.Load($e.File.ExtractFile($e), $e) } catch { continue }
        foreach ($a in @($t.AllArchetypes)) {
            if (-not $a) { continue }
            $nm = $a.Name.ToLower()
            if ($nm -notmatch $pat -or $nm -match $exclude -or $out.Contains($nm)) { continue }
            $d = $a._BaseArchetypeDef
            $out[$nm] = @([math]::Round($d.bbMin.X,2),[math]::Round($d.bbMin.Y,2),[math]::Round($d.bbMin.Z,2),[math]::Round($d.bbMax.X,2),[math]::Round($d.bbMax.Y,2),[math]::Round($d.bbMax.Z,2),$yn)
            $n++
        }
    }
}
$out | ConvertTo-Json -Depth 3 -Compress | Set-Content (Join-Path $PSScriptRoot 'prop_catalogue.json') -Encoding utf8
"catalogued $n archetypes"
