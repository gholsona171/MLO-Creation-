# ents_at.ps1 (read-only): every map entity within -R m of (X, Y) (ymap entities, not interiors): archetype, position, lodDist,
# ymap - which Rockstar models make up a given spot (ground, glue, decal overlays...).
param([double]$X, [double]$Y, [double]$R = 40)
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$seen = @{}
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }; foreach ($e in $f.AllEntries) { if (-not $e.Name.EndsWith('.ymap')) { continue }
  try { $ym = New-Object CodeWalker.GameFiles.YmapFile; $ym.Load($e.File.ExtractFile($e), $e) } catch { continue }
  if (-not $ym.AllEntities) { continue }
  foreach ($en in $ym.AllEntities) { $p = $en.Position; if ([Math]::Abs($p.X - $X) -gt $R -or [Math]::Abs($p.Y - $Y) -gt $R) { continue }
    $n = $en._CEntityDef.archetypeName.ToString(); $k = "$n@$([int]$p.X),$([int]$p.Y)"; if ($seen[$k]) { continue }; $seen[$k] = 1
    "$n`t$([math]::Round($p.X,1)),$([math]::Round($p.Y,1)),$([math]::Round($p.Z,1))`tlod=$($en._CEntityDef.lodDist)`t$($e.Name)" } } }
