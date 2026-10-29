# a BUILT (local) ydr / ybn -> CodeWalker XML, to check what the file really carries (vertex colours, room ids).
# Usage: powershell -File local_xml.ps1 -In <file.ydr|file.ybn> -Out <file.xml>
param([string]$In, [string]$Out)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
$b = [IO.File]::ReadAllBytes($In)
if ($In -like '*.ydr') { $y = New-Object CodeWalker.GameFiles.YdrFile; $y.Load($b); $x = [CodeWalker.GameFiles.YdrXml]::GetXml($y, [IO.Path]::GetDirectoryName($Out)) }
else { $y = New-Object CodeWalker.GameFiles.YbnFile; $y.Load($b); $x = [CodeWalker.GameFiles.YbnXml]::GetXml($y) }
[IO.File]::WriteAllText($Out, $x); "LOCAL_XML $Out $($x.Length)"
