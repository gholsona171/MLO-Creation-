# Justice Center phase 3 (read-only): Rockstar drawables -> CodeWalker XML for previews and material reading, wherever they live:
# a .ydr of that name, or a drawable inside any .ydd (prop dictionaries: v_corp_bk_rope, prop_cctv_cam_06a ...). A .ydd hit writes
# just that drawable as <name>.ydr.xml (YdrXml of a YdrFile wrapping it). Textures: only the embedded ones are written (the rest
# live in txds: tools/counter_kit/cw.ps1 tex fetches them).
# Usage: powershell -File vanilla_xml.ps1 -Names a,b,c -Out <dir>
param([string]$Names, [string]$Out)
$ErrorActionPreference = 'Stop'
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
New-Item -ItemType Directory -Force $Out | Out-Null
$want = @{}; foreach ($n in ($Names -split ',')) { $k = $n.Trim().ToLower(); if ($k) { $want[[CodeWalker.GameFiles.JenkHash]::GenHash($k)] = $k } }
foreach ($pass in 'ydr', 'ydd') {
  foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries -or $want.Count -eq 0) { continue }
    foreach ($e in $f.AllEntries) {
      if ($want.Count -eq 0) { break }
      if ($pass -eq 'ydr' -and $e.Name -like '*.ydr') {
        $n = [IO.Path]::GetFileNameWithoutExtension($e.Name).ToLower(); $h = [CodeWalker.GameFiles.JenkHash]::GenHash($n)
        if (-not $want.ContainsKey($h)) { continue }
        $y = New-Object CodeWalker.GameFiles.YdrFile; $y.Load($e.File.ExtractFile($e), $e)
        [IO.File]::WriteAllText((Join-Path $Out "$n.ydr.xml"), [CodeWalker.GameFiles.YdrXml]::GetXml($y, (Join-Path $Out $n))); "found $n (ydr) $($e.Path)"; $want.Remove($h)
      } elseif ($pass -eq 'ydd' -and $e.Name -like '*.ydd') {
        try { $d = New-Object CodeWalker.GameFiles.YddFile; $d.Load($e.File.ExtractFile($e), $e) } catch { continue }
        if (-not $d.Dict) { continue }
        foreach ($kv in $d.Dict.GetEnumerator()) {
          $h = [uint32]$kv.Key; if (-not $want.ContainsKey($h)) { continue }
          $n = $want[$h]; $y = New-Object CodeWalker.GameFiles.YdrFile; $y.Drawable = $kv.Value; $y.Name = "$n.ydr"
          [IO.File]::WriteAllText((Join-Path $Out "$n.ydr.xml"), [CodeWalker.GameFiles.YdrXml]::GetXml($y, (Join-Path $Out $n))); "found $n (in $($e.Name))"; $want.Remove($h)
        } } } } }
if ($want.Count) { "not found: $($want.Values -join ', ')" }
'VANILLA_XML_DONE'
