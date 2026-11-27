# vanilla_extract.ps1 (read-only on the game): everything the site steps read from Rockstar's files, newest copy of each name wins
# (patchday > dlc_patch > dlcpacks > base). Two passes (vanilla.sh runs both):
#   -Box "x0,x1,y0,y1"   into ..\vanilla (wiped first):
#     * every map file (.ymap, any prefix: base / hei_ / lr_ ...) whose entity or streaming extents reach the box, as CodeWalker XML
#       (<name>.ymap.xml): entity maps, LOD parents, grass, occluders. Interior (milo) maps and world-wide maps are skipped.
#     * every distant-LOD-light map with a light in the box (lodlights\<name>.ymap.xml)
#     * every static collision file (.ybn, any prefix incl. hi@ / ma@) whose bounds reach the box, as a full RSC7 file (for Sollumz)
#     index.tsv: kind, name, source path
#   -Ydr "a,b,..."       the named drawables as full RSC7 .ydr into ..\vanilla\models (wiped first); index_models.tsv
# Usage: powershell -File vanilla_extract.ps1 -Box "x0,x1,y0,y1"  |  -Ydr "a,b"
param([string]$Box = '', [string]$Ydr = '')
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
function Rank($p) { $m = [regex]::Match($p, 'patchday(\d+)'); if ($m.Success) { return 100 + [int]$m.Groups[1].Value }; if ($p -match 'dlc_patch') { return 60 }; if ($p -match 'dlcpacks') { return 50 }; return 0 }
$Van = Join-Path (Split-Path $PSScriptRoot -Parent) 'vanilla'
$maps = [bool]$Box
$Out = if ($maps) { $Van } else { Join-Path $Van 'models' }
if (Test-Path -LiteralPath $Out) { Remove-Item -LiteralPath $Out -Recurse -Force }
New-Item -ItemType Directory -Force $Out | Out-Null
if ($maps) { New-Item -ItemType Directory -Force (Join-Path $Out 'lodlights') | Out-Null
  $b = [double[]]($Box -split ','); $X0 = $b[0]; $X1 = $b[1]; $Y0 = $b[2]; $Y1 = $b[3] }
function Hit($mn, $mx) { return -not ($mx.X -lt $X0 -or $mn.X -gt $X1 -or $mx.Y -lt $Y0 -or $mn.Y -gt $Y1) }
$wantYdr = @{}; foreach ($n in ($Ydr -split ',')) { if ($n.Trim()) { $wantYdr[$n.Trim().ToLower() + '.ydr'] = $true } }
$best = @{}                                                         # name -> entry (newest copy)
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { $k = $e.Name.ToLower()
    if ($maps) { if (-not ($k.EndsWith('.ymap') -or $k.EndsWith('.ybn'))) { continue } }
    elseif (-not $wantYdr.ContainsKey($k)) { continue }
    if ($e.Path -match '\\interiors?\\|_milo_|\\int_') { continue }
    if (-not $best.ContainsKey($k) -or (Rank $best[$k].Path) -le (Rank $e.Path)) { $best[$k] = $e } } }
$rows = New-Object System.Collections.Generic.List[string]
foreach ($k in $best.Keys) { $e = $best[$k]
  try {
    if ($k.EndsWith('.ymap')) {
      $ym = New-Object CodeWalker.GameFiles.YmapFile; $ym.Load($e.File.ExtractFile($e), $e)
      if ($k -match 'lodlights') {
        $n = 0; if ($ym.DistantLODLights -and $ym.DistantLODLights.positions) { foreach ($p in $ym.DistantLODLights.positions) { if ($p.x -ge $X0 -and $p.x -le $X1 -and $p.y -ge $Y0 -and $p.y -le $Y1) { $n++ } } }
        if ($n -eq 0) { continue }
        $fn = ''; $x = [CodeWalker.GameFiles.MetaXml]::GetXml($ym, [ref]$fn); [IO.File]::WriteAllText((Join-Path $Out "lodlights\$($e.Name).xml"), $x)
        $rows.Add("lodlights`t$($e.Name)`t$($e.Path)`t$n"); continue }
      $d = $ym.CMapData
      if (-not ((Hit $d.entitiesExtentsMin $d.entitiesExtentsMax) -or (Hit $d.streamingExtentsMin $d.streamingExtentsMax))) { continue }
      if ($d.entitiesExtentsMax.X - $d.entitiesExtentsMin.X -gt 3000) { continue }            # world-wide maps (no block of ours)
      $fn = ''; $x = [CodeWalker.GameFiles.MetaXml]::GetXml($ym, [ref]$fn); [IO.File]::WriteAllText((Join-Path $Out "$($e.Name).xml"), $x)
      $rows.Add("ymap`t$($e.Name)`t$($e.Path)")
    } elseif ($k.EndsWith('.ybn')) {
      $yb = New-Object CodeWalker.GameFiles.YbnFile; $yb.Load($e.File.ExtractFile($e), $e)
      if (-not $yb.Bounds -or -not (Hit $yb.Bounds.BoxMin $yb.Bounds.BoxMax)) { continue }
      [IO.File]::WriteAllBytes((Join-Path $Out $e.Name), $yb.Save()); $rows.Add("ybn`t$($e.Name)`t$($e.Path)")
    } else {
      $y = New-Object CodeWalker.GameFiles.YdrFile; $y.Load($e.File.ExtractFile($e), $e)
      [IO.File]::WriteAllBytes((Join-Path $Out $e.Name), $y.Save()); $rows.Add("ydr`t$($e.Name)`t$($e.Path)")
    }
  } catch { $rows.Add("error`t$($e.Name)`t$($e.Path)`t$($_.Exception.Message)") } }
foreach ($k in $wantYdr.Keys) { if (-not $best.ContainsKey($k)) { $rows.Add("missing`t$k") } }
[IO.File]::WriteAllLines((Join-Path $Out $(if ($maps) { 'index.tsv' } else { 'index_models.tsv' })), $rows)
"VANILLA_EXTRACT ymap $(@($rows | ? { $_ -like 'ymap*' }).Count) ybn $(@($rows | ? { $_ -like 'ybn*' }).Count) ydr $(@($rows | ? { $_ -like 'ydr*' }).Count) lodlights $(@($rows | ? { $_ -like 'lodlights*' }).Count) errors $(@($rows | ? { $_ -like 'error*' -or $_ -like 'missing*' }).Count)"
