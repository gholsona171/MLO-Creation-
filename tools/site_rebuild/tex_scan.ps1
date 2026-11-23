# tex_scan.ps1 (read-only on the game): every texture in the map's texture dictionaries (levels\gta5 ytds, plus the map ydr/ydd
# embedded ones are skipped) whose name matches -Pattern, with its size and dictionary -> ..\survey\<-Name>.tsv (default tex_scan: tex_extract.ps1 reads that one)
param([string]$Pattern = 'grass|lawn|turf|roof|gravel|felt|tarmac|asphalt', [string]$Name = 'tex_scan')
$gta = 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
[CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
$rpf = New-Object CodeWalker.GameFiles.RpfManager
$rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
$out = New-Object System.Collections.Generic.List[string]; $n = 0
foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
  foreach ($e in $f.AllEntries) { if (-not $e.Name.ToLower().EndsWith('.ytd') -or $e.Path -notmatch 'levels\\gta5') { continue }
    try { $y = New-Object CodeWalker.GameFiles.YtdFile; $y.Load($e.File.ExtractFile($e), $e); $n++ } catch { continue }
    foreach ($t in $y.TextureDict.Textures.data_items) { if ($t.Name -match $Pattern) { $out.Add("$($t.Name)`t$($t.Width)x$($t.Height)`t$($t.Format)`t$($e.Name)`t$($e.Path)") } } } }
[IO.File]::WriteAllLines((Join-Path (Split-Path $PSScriptRoot -Parent) "survey\$Name.tsv"), [string[]]$out)
"TEX_SCAN $n dictionaries, $($out.Count) matches"
