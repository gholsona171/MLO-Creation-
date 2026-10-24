# Tower City: a game drawable <-> CodeWalker XML. -Mode export -Name <archetype> -Out <dir> (writes <dir>/<name>.ydr.xml + textures)
#                                                 -Mode import -In <xml> -Out <file.ydr>   (textures: the <name>/ folder beside the xml)
param([string]$Mode, [string]$Name, [string]$In, [string]$Out)
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
if ($Mode -eq 'export') {
    [CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
    $rpf = New-Object CodeWalker.GameFiles.RpfManager
    $rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
    $want = @{}; foreach ($n in ($Name -split ',')) { $want[$n.Trim().ToLower()] = $true }     # several names in one scan: -Name a,b,c
    New-Item -ItemType Directory -Force $Out | Out-Null
    foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
      foreach ($e in $f.AllEntries) { $n = [IO.Path]::GetFileNameWithoutExtension($e.Name).ToLower(); if (-not $e.Name.EndsWith('.ydr') -or -not $want[$n]) { continue }
        $bytes = $e.File.ExtractFile($e); $y = New-Object CodeWalker.GameFiles.YdrFile; $y.Load($bytes, $e)
        $x = [CodeWalker.GameFiles.YdrXml]::GetXml($y, (Join-Path $Out $n)); [IO.File]::WriteAllText((Join-Path $Out "$n.ydr.xml"), $x); "found $n $($bytes.Length) bytes"; $want.Remove($n) } }
    if ($want.Count) { "not found: $($want.Keys -join ', ')" }
} else {
    $doc = New-Object System.Xml.XmlDocument; $doc.Load($In)
    $tex = Join-Path ([IO.Path]::GetDirectoryName($In)) ([IO.Path]::GetFileName($In) -replace '\.ydr\.xml$', '')
    $y = [CodeWalker.GameFiles.XmlYdr]::GetYdr($doc, $tex); $bytes = $y.Save(); [IO.File]::WriteAllBytes($Out, $bytes); "imported -> $($bytes.Length) bytes"
}
