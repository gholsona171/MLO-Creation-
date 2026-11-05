param([string]$In, [string]$Out)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\tools\CodeWalker'
if (-not (Test-Path "$cw\CodeWalker.Core.dll")) { $cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
$y = New-Object CodeWalker.GameFiles.YmapFile; $y.Load([IO.File]::ReadAllBytes($In))
$sb = New-Object Text.StringBuilder
for ($i = 0; $i -lt $y.OccludeModels.Length; $i++) { $m = $y.OccludeModels[$i]
  $v = $m.Vertices; $ix = $m.Indices
  for ($t = 0; $t -lt $ix.Length; $t += 3) { $p = @($ix[$t], $ix[$t+1], $ix[$t+2]) | % { $q = $v[$_]; '{0:F3},{1:F3},{2:F3}' -f $q.X, $q.Y, $q.Z }
    [void]$sb.AppendLine("$i;$($p -join ';')") } }
[IO.File]::WriteAllText($Out, $sb.ToString()); "$In : $($y.OccludeModels.Length) models"
