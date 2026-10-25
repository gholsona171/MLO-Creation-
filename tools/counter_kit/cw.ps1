# c9_dj prop build on Windows: CodeWalker.Core (the same library cwbuild wraps) for the counter kit (prop/build/counters.py).
#   cw.ps1 ydr  <in.ydr.xml> <out.ydr>                 (textures: none embedded; the archetype's ytd has them)
#   cw.ps1 ytyp <in.ytyp.xml> <out.ytyp>
#   cw.ps1 ytd  <folder of .dds> <out.ytd>             (every .dds in the folder, named after its file)
#   cw.ps1 tex  <names,comma,separated> <out folder> [preferred txd,...]   (finds each texture in the game: preferred txds first,
#        then every ytd and every drawable's embedded dictionary; writes <name>.dds; prints MISSING for any not found)
# Paths: $env:GTA_DIR (default Steam) and $env:CODEWALKER (default the MLO Workshop copy).
param([string]$Mode, [string]$A, [string]$B, [string]$C)
$ErrorActionPreference = 'Stop'
$gta = if ($env:GTA_DIR) { $env:GTA_DIR } else { 'C:\Program Files (x86)\Steam\steamapps\common\Grand Theft Auto V' }
$cw = if ($env:CODEWALKER) { $env:CODEWALKER } else { 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker' }
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")

function Load-Xml($p) { $d = New-Object System.Xml.XmlDocument; $d.Load($p); $d }

switch ($Mode) {
  'ydr' {
    $y = [CodeWalker.GameFiles.XmlYdr]::GetYdr((Load-Xml $A), [IO.Path]::GetDirectoryName((Resolve-Path $A)))
    $bytes = $y.Save(); [IO.File]::WriteAllBytes($B, $bytes)
    $chk = New-Object CodeWalker.GameFiles.YdrFile; $chk.Load($bytes)
    "$B $($bytes.Length) bytes, bound: $([bool]$chk.Drawable.Bound)"
  }
  'ytyp' {
    $bytes = [CodeWalker.GameFiles.XmlMeta]::GetData((Load-Xml $A), [CodeWalker.GameFiles.MetaFormat]::RSC, [IO.Path]::GetDirectoryName((Resolve-Path $A)))
    [IO.File]::WriteAllBytes($B, $bytes); "$B $($bytes.Length) bytes"
  }
  'ytd' {
    $list = New-Object 'System.Collections.Generic.List[CodeWalker.GameFiles.Texture]'
    foreach ($f in (Get-ChildItem $A -Filter *.dds | Sort-Object Name)) {
      $t = [CodeWalker.Utils.DDSIO]::GetTexture([IO.File]::ReadAllBytes($f.FullName))
      $n = [IO.Path]::GetFileNameWithoutExtension($f.Name)
      $t.Name = $n; $t.NameHash = [CodeWalker.GameFiles.JenkHash]::GenHash($n.ToLower())
      $list.Add($t)
    }
    $td = New-Object CodeWalker.GameFiles.TextureDictionary; $td.BuildFromTextureList($list)
    $y = New-Object CodeWalker.GameFiles.YtdFile; $y.TextureDict = $td
    $bytes = $y.Save(); [IO.File]::WriteAllBytes($B, $bytes); "$B $($bytes.Length) bytes, $($list.Count) textures"
  }
  'tex' {
    [CodeWalker.GameFiles.GTA5Keys]::LoadFromPath($gta, $false, $null)
    $rpf = New-Object CodeWalker.GameFiles.RpfManager
    $rpf.Init($gta, $false, [Action[string]]{ param($s) }, [Action[string]]{ param($s) }, $false, $true)
    New-Item -ItemType Directory -Force $B | Out-Null
    $want = @{}; foreach ($n in ($A -split ',')) { if ($n.Trim()) { $want[$n.Trim().ToLower()] = $true } }
    $pref = @{}; if ($C) { foreach ($n in ($C -split ',')) { $pref[$n.Trim().ToLower()] = $true } }
    function Take($dict, $where) {
      if (-not $dict -or -not $dict.Textures -or -not $dict.Textures.data_items) { return }
      foreach ($t in $dict.Textures.data_items) {
        $n = "$($t.Name)".ToLower()
        if ($want.ContainsKey($n)) {
          [IO.File]::WriteAllBytes((Join-Path $B "$n.dds"), [CodeWalker.Utils.DDSIO]::GetDDSFile($t))
          "found $n in $where ($($t.Width)x$($t.Height) $($t.Format))"; $want.Remove($n)
        }
      }
    }
    foreach ($pass in 1, 2, 3) {
      foreach ($f in $rpf.AllRpfs) { if (-not $f.AllEntries) { continue }
        foreach ($e in $f.AllEntries) {
          if ($want.Count -eq 0) { break }
          $nm = [IO.Path]::GetFileNameWithoutExtension($e.Name).ToLower()
          try {
            if ($e.Name -like '*.ytd' -and (($pass -eq 1 -and $pref[$nm]) -or $pass -eq 2)) {
              $y = New-Object CodeWalker.GameFiles.YtdFile; $y.Load($e.File.ExtractFile($e), $e); Take $y.TextureDict $e.Path
            } elseif ($pass -eq 3 -and $e.Name -like '*.ydr') {
              $y = New-Object CodeWalker.GameFiles.YdrFile; $y.Load($e.File.ExtractFile($e), $e)
              if ($y.Drawable -and $y.Drawable.ShaderGroup) { Take $y.Drawable.ShaderGroup.TextureDictionary $e.Path }
            }
          } catch { }
        }
      }
    }
    foreach ($n in $want.Keys) { "MISSING $n" }
  }
  default { 'usage: cw.ps1 ydr|ytyp|ytd|tex ...'; exit 2 }
}
