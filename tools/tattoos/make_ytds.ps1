# One texture dictionary per DDS: <dds dir>\<name>.dds -> <out>\<name>.ytd holding one texture <name> (a tattoo's txdHash = txtHash).
# Each ytd is loaded back and checked.   make_ytds.ps1 -Dds <dir> -Out <stream dir>
param([string]$Dds, [string]$Out)
$ErrorActionPreference = 'Stop'
$cw = if ($env:CODEWALKER) { $env:CODEWALKER } else { 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
New-Item -ItemType Directory -Force $Out | Out-Null
foreach ($f in Get-ChildItem -LiteralPath $Dds -Filter *.dds) {
  $name = $f.BaseName.ToLower()
  $t = [CodeWalker.Utils.DDSIO]::GetTexture([IO.File]::ReadAllBytes($f.FullName))
  $t.Name = $name; $t.NameHash = [CodeWalker.GameFiles.JenkHash]::GenHash($name)
  $list = New-Object 'System.Collections.Generic.List[CodeWalker.GameFiles.Texture]'; $list.Add($t)
  $td = New-Object CodeWalker.GameFiles.TextureDictionary; $td.BuildFromTextureList($list)
  $y = New-Object CodeWalker.GameFiles.YtdFile; $y.TextureDict = $td
  $bytes = $y.Save(); $p = Join-Path $Out "$name.ytd"; [IO.File]::WriteAllBytes($p, $bytes)
  $c = New-Object CodeWalker.GameFiles.YtdFile; $c.Load($bytes)
  $k = $c.TextureDict.Textures.data_items[0]
  if ($k.Name -ne $name -or $k.Width -ne $t.Width -or $k.Levels -ne $t.Levels) { throw "reload mismatch $name" }
  "$name.ytd $($bytes.Length) bytes: $($k.Name) $($k.Width)x$($k.Height) $($k.Format) L$($k.Levels)"
}
