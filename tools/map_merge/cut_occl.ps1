# Remove listed box occluders and occlude-model triangles from a ymap (spec JSON: {boxes:[[cx,cy,cz,cos,L,W,H,sin],...], tris:[[[x,y,z]x3],...]})
param([string]$In, [string]$Spec, [string]$Out)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\tools\CodeWalker'
if (-not (Test-Path "$cw\CodeWalker.Core.dll")) { $cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
$sp = Get-Content -Raw $Spec | ConvertFrom-Json
$y = New-Object CodeWalker.GameFiles.YmapFile; $y.Load([IO.File]::ReadAllBytes($In))
$nb = 0
foreach ($b in @($sp.boxes)) { $hit = @($y.BoxOccluders) | ? { $o = $_._Box; $o.iCenterX -eq $b[0] -and $o.iCenterY -eq $b[1] -and $o.iCenterZ -eq $b[2] -and $o.iLength -eq $b[4] -and $o.iWidth -eq $b[5] -and $o.iHeight -eq $b[6] -and ($null -eq $b[3] -or ([math]::Abs($o.iCosZ - $b[3]) -le 2 -and [math]::Abs($o.iSinZ - $b[7]) -le 2)) }
  if ($hit) { [void]$y.RemoveBoxOccluder($hit[0]); $nb++ } }
$want = @{}; foreach ($t in @($sp.tris)) { $k = (@($t | % { '{0:F3},{1:F3},{2:F3}' -f $_[0], $_[1], $_[2] }) | Sort-Object) -join ';'; $want[$k] = 1 }
$nt = 0
for ($mi = $y.OccludeModels.Length - 1; $mi -ge 0; $mi--) { $m = $y.OccludeModels[$mi]; $v = $m.Vertices; $ix = $m.Indices
  for ($t = $ix.Length / 3 - 1; $t -ge 0; $t--) { $i = $t * 3
    $k = (@($ix[$i], $ix[$i+1], $ix[$i+2]) | % { $q = $v[$_]; '{0:F3},{1:F3},{2:F3}' -f $q.X, $q.Y, $q.Z } | Sort-Object) -join ';'
    if ($want.ContainsKey($k)) { if (-not $y.RemoveOccludeModelTriangle($y.OccludeModels[$mi].Triangles[$t])) { throw "remove failed" }; $nt++ } } }
$y.Name = [IO.Path]::GetFileNameWithoutExtension($Out)
$bytes = $y.Save(); [IO.File]::WriteAllBytes($Out, $bytes)
"removed boxes $nb of $(@($sp.boxes).Count), triangles $nt of $($want.Count); now boxes $($y.BoxOccluders.Length), models $($y.OccludeModels.Length)"
