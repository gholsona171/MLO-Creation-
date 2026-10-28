# Justice Center (read-only): every collision file (every copy, game archives + a folder of loose ybns) whose bounds contain a point.
param([double]$X, [double]$Y, [double]$Z, [string]$Loose = 'C:\C9Test\live\resources')
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
function Hit($b) { return ($b -and $b.BoxMin.X -le $X -and $b.BoxMax.X -ge $X -and $b.BoxMin.Y -le $Y -and $b.BoxMax.Y -ge $Y -and $b.BoxMin.Z -le $Z -and $b.BoxMax.Z -ge $Z) }
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if (-not $e.Name.ToLower().EndsWith('.ybn')) { continue }
    try { $y = New-Object CodeWalker.GameFiles.YbnFile; $y.Load($e.File.ExtractFile($e), $e) } catch { continue }
    if (Hit $y.Bounds) { "GAME $($e.Path)  $($y.Bounds.BoxMin) .. $($y.Bounds.BoxMax)" } } }
foreach ($p in (Get-ChildItem -Recurse -Filter *.ybn $Loose)) {
  try { $y = New-Object CodeWalker.GameFiles.YbnFile; $y.Load([IO.File]::ReadAllBytes($p.FullName)) } catch { continue }
  if (Hit $y.Bounds) { "LOOSE $($p.FullName)" } }
"YBN_AT_DONE"
