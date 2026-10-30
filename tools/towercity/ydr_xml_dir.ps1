# every ydr in a folder -> CodeWalker XML (<name>.ydr.xml) in another, to read what the BUILT files carry (vcol_check.py).
# Usage: powershell -File ydr_xml_dir.ps1 -InDir <stream> -OutDir <dir> [-Pattern tc_*.ydr]
param([string]$InDir, [string]$OutDir, [string]$Pattern = 'tc_*.ydr')
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
$n = 0
foreach ($f in Get-ChildItem $InDir -Filter $Pattern) {
  $y = New-Object CodeWalker.GameFiles.YdrFile; $y.Load([IO.File]::ReadAllBytes($f.FullName))
  $sub = Join-Path $OutDir ($f.BaseName + '_tex'); 
  $x = [CodeWalker.GameFiles.YdrXml]::GetXml($y, $sub)
  [IO.File]::WriteAllText((Join-Path $OutDir ($f.BaseName + '.ydr.xml')), $x); $n++
}
"YDR2XML $n files"
