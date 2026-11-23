# ybn_procs.ps1 (read-only): for the static collision files whose bounds contain (X, Y): every (material, procedural id,
# material colour index) combination used by their polygons, with counts - how Rockstar sets up a given kind of ground.
param([double]$X, [double]$Y)
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if ($e.Name -notmatch '\.ybn$' -or $e.Name -match '^(hi@|ma@)') { continue }
    try { $yb = New-Object CodeWalker.GameFiles.YbnFile; $yb.Load($e.File.ExtractFile($e), $e) } catch { continue }
    if (-not $yb.Bounds) { continue }; $mn = $yb.Bounds.BoxMin; $mx = $yb.Bounds.BoxMax
    if ($X -lt $mn.X -or $X -gt $mx.X -or $Y -lt $mn.Y -or $Y -gt $mx.Y) { continue }
    $xml = [CodeWalker.GameFiles.YbnXml]::GetXml($yb)
    $ms = [regex]::Matches($xml, '<Type value="(\d+)" />\s*<ProceduralID value="(\d+)" />\s*<RoomID value="\d+" />\s*<PedDensity value="\d+" />\s*<Flags>[^<]*</Flags>\s*<MaterialColourIndex value="(\d+)" />')
    $c = @{}; foreach ($m in $ms) { $k = "mat$($m.Groups[1].Value)/proc$($m.Groups[2].Value)/col$($m.Groups[3].Value)"; $c[$k] = 1 + [int]$c[$k] }
    $cols = ([regex]::Matches($xml, '<MaterialColours>([\s\S]*?)</MaterialColours>') | % { $_.Groups[1].Value.Trim() -replace '\s+', ' ' }) -join ' | '
    "$($e.Name): " + (($c.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 10 | % { "$($_.Key)" }) -join '  ') + "   COLOURS: " + $cols.Substring(0, [Math]::Min(300, $cols.Length))
  } }
