# grass_at.ps1 (read-only): the grass-instance batches (ymap GrassInstanceList) within -R m of (X, Y): ymap, archetype, instance
# count, batch box, lod distances, scale range, a sample of the per-blade colours. How Rockstar grows grass on a given ground.
param([double]$X, [double]$Y, [double]$R = 60)
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if ($e.Name -notmatch '\.ymap$' -or $e.Name -notmatch 'grass|_strm_|long') { } 
    if (-not $e.Name.EndsWith('.ymap')) { continue }
    try { $ym = New-Object CodeWalker.GameFiles.YmapFile; $ym.Load($e.File.ExtractFile($e), $e); $script:ny++ } catch { $script:nerr++; if ($script:nerr -lt 3) { "ERR $($e.Name) $_" }; continue }
    if (-not $ym.GrassInstanceBatches) { continue }; $script:ng++
    foreach ($b in $ym.GrassInstanceBatches) { $mn = $b.AABBMin; $mx = $b.AABBMax
      if ($X -lt $mn.X - $R -or $X -gt $mx.X + $R -or $Y -lt $mn.Y - $R -or $Y -gt $mx.Y + $R) { continue }
      $bt = $b.Batch; $ins = $b.Instances
      $cols = @($ins | Select-Object -First 4 | % { "$($_.Color[0]),$($_.Color[1]),$($_.Color[2])" }) -join ' '
      $sc = @($ins | % { $_.Scale }); $smin = ($sc | Measure-Object -Minimum -Maximum)
      "$($e.Name)`t$($bt.archetypeName)`tn=$($ins.Length)`tbox=($([int]$mn.X),$([int]$mn.Y),$([int]$mn.Z))-($([int]$mx.X),$([int]$mx.Y),$([int]$mx.Z))`tlod=$($bt.lodDist) fade=$($bt.LodFadeStartDist)/$($bt.LodInstFadeRange) orient=$($bt.OrientToTerrain) scale=$($bt.ScaleRange.X),$($bt.ScaleRange.Y),$($bt.ScaleRange.Z) iscale=$($smin.Minimum)-$($smin.Maximum)`tcol=$cols`tao=$(@($ins|select -First 3|%{$_.Ao}) -join ',')"
    } } }
"SCAN ymaps=$script:ny errors=$script:nerr withgrass=$script:ng"
