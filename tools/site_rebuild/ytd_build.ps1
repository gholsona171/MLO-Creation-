# ytd_build.ps1 -Dds <folder of .dds> -Out <file.ytd>: one texture dictionary holding every DDS in the folder, each texture named
# after its file (the names the drawables reference with embedded = off). Loaded back and checked.
# pave.py's textures -> ..\site\pave\jy_pave.ytd (every paving tile's textureDictionary).
param([string]$Dds, [string]$Out)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
$list = New-Object 'System.Collections.Generic.List[CodeWalker.GameFiles.Texture]'
foreach ($f in Get-ChildItem -LiteralPath $Dds -Filter *.dds | Sort-Object Name) {
  $name = $f.BaseName.ToLower(); $t = [CodeWalker.Utils.DDSIO]::GetTexture([IO.File]::ReadAllBytes($f.FullName))
  $t.Name = $name; $t.NameHash = [CodeWalker.GameFiles.JenkHash]::GenHash($name); $list.Add($t) }
if ($list.Count -eq 0) { throw "no .dds in $Dds" }
$td = New-Object CodeWalker.GameFiles.TextureDictionary; $td.BuildFromTextureList($list)
$y = New-Object CodeWalker.GameFiles.YtdFile; $y.TextureDict = $td
$bytes = $y.Save(); [IO.File]::WriteAllBytes($Out, $bytes)
$c = New-Object CodeWalker.GameFiles.YtdFile; $c.Load($bytes)
$names = @($c.TextureDict.Textures.data_items | % { "$($_.Name) $($_.Width)x$($_.Height) $($_.Format)" })
if ($names.Count -ne $list.Count) { throw "reload: $($names.Count) of $($list.Count) textures" }
"YTD_BUILD_PASS $Out $($bytes.Length) bytes: $($names -join '; ')"
