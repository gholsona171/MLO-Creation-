# Tower City survey (read-only): which game ytyp holds each archetype (the MLO manifest's itypDepArray needs them), plus each
# archetype's bounding box (for placing the props). Writes arch_ytyp.json next to this script.
param([string[]]$Names)
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$want = @{}; foreach ($n in $Names) { $want[$n.ToLower()] = $true }
$jf = Join-Path $PSScriptRoot 'arch_ytyp.json'; $out = [ordered]@{}               # merged into what earlier runs found
if (Test-Path $jf) { (Get-Content $jf -Raw | ConvertFrom-Json).PSObject.Properties | ForEach-Object { $out[$_.Name] = $_.Value } }
foreach ($f in $rpf.AllRpfs) {
    if (-not $f.AllEntries) { continue }
    foreach ($e in $f.AllEntries) {
        if ($e.Name -notmatch '\.ytyp$') { continue }
        try { $t = New-Object CodeWalker.GameFiles.YtypFile; $t.Load($e.File.ExtractFile($e), $e) } catch { continue }
        foreach ($a in $t.AllArchetypes) {
            $n = $a.Name.ToLower()
            if ($want.ContainsKey($n) -and -not $out.Contains($n)) {   # (first copy found wins)
                $out[$n] = [ordered]@{ ytyp = [IO.Path]::GetFileNameWithoutExtension($e.Name); path = $e.Path; bbMin = "$($a._BaseArchetypeDef.bbMin)"; bbMax = "$($a._BaseArchetypeDef.bbMax)" }
            }
        }
    }
}
$out | ConvertTo-Json -Depth 4 | Set-Content $jf -Encoding utf8
"found $(@($Names | Where-Object { $out.Contains($_.ToLower()) }).Count) of $($Names.Count)"
foreach ($n in $Names) { if (-not $out.Contains($n.ToLower())) { "MISSING $n" } }
