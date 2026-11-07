# CodeWalker export of built ydr / yft back to XML + textures (proves what the binaries hold; feeds render_props.py)
param([string]$In, [string]$Out)
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
New-Item -ItemType Directory -Force $Out | Out-Null
foreach ($f in Get-ChildItem $In -Include *.ydr, *.yft -Recurse) {
  $b = [IO.File]::ReadAllBytes($f.FullName); $n = $f.BaseName
  if ($f.Extension -eq '.ydr') { $y = New-Object CodeWalker.GameFiles.YdrFile; $y.Load($b); $x = [CodeWalker.GameFiles.YdrXml]::GetXml($y, (Join-Path $Out $n)) }
  else { $y = New-Object CodeWalker.GameFiles.YftFile; $y.Load($b); $x = [CodeWalker.GameFiles.YftXml]::GetXml($y, (Join-Path $Out $n)) }
  [IO.File]::WriteAllText((Join-Path $Out "$n$($f.Extension).xml"), $x); "exported $($f.Name)"
}
