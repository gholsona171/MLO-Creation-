# tex_slim.ps1 - texture budget for streamed files: .ytd AND textures embedded in .ydr / .ydd (CodeWalker.Core).
# Extended copy of C:\C9Test\rebuild\tools\ytd_shrink.ps1 (that tool is unchanged).
#   tex_slim.ps1 -Mode scan   -Dir <folder>                              lists every file over the rules, with its biggest textures
#   tex_slim.ps1 -Mode shrink -Dir <folder> [-Out <folder>] [-Backup <folder>]
#        writes the slimmed files to -Out (same relative paths); without -Out in place (originals copied to -Backup first if given;
#        a build step that rewrites its own fresh output needs no backup)
# Rules (ytd_shrink's, plus one lossless step): every texture capped at MaxDim; then, while the file's PHYSICAL size (RSC7
# graphics pages, measured on the saved file) is not under BudgetMiB (FiveM warns from 16 MiB, 16.0 included):
#   1. compress the largest uncompressed 32-bit texture (same resolution; -Compress BC3 = DXT5 as ytd_shrink, or BC7 where dark
#      greys must stay clean - BC3's 5:6:5 endpoints turn them into purple / green speckle)
#   2. lossless: the largest DXT5 whose alpha is 255 everywhere -> DXT1 (bit-exact, half the bytes)
#   3. halve the largest texture (never below MinDim on either side)
# Steps 1-2 lose no resolution and always run while over BudgetMiB. Step 3's target is BudgetMiB, except for a drawable that
# cannot get under BudgetMiB even with every texture at the floor (big 1024 x 256 sign strips cannot be halved): its target is
# FallbackMiB (FiveM's 48 MiB "Oversized" line), so textures are not cut for no gain. Such files are reported OVER.# How a texture shrinks: a 2048 texture with mips drops its top level (the author's own 1024 mip, no re-compression); a texture
# without mips is resized by Microsoft texconv (same format, full mip chain).
# Textures are changed IN PLACE on the loaded file (size, format, mips, data): name, usage, flags and every shader reference stay
# the same object, so an embedded texture never ends up written twice. The file is reloaded and checked before it is written:
# same texture count and names, each texture's new size / format / mips, and for drawables the CodeWalker XML of the whole file
# with the texture entries left out must be identical to the original's (geometry, shaders, lights, bounds untouched).
# Encrypted (FXAP / Cfx escrow) files are never touched; they are listed as SKIP.
param([string]$Mode, [string]$Dir, [string]$Out, [string]$Backup, [int]$MaxDim = 2048, [int]$MinDim = 512, [double]$BudgetMiB = 16,
      [double]$FallbackMiB = 48, [ValidateSet('BC3', 'BC7')][string]$Compress = 'BC3', [string[]]$Only)
$ErrorActionPreference = 'Stop'
$cw = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\outputs\MLO-Workshop\tools\CodeWalker'
[void][Reflection.Assembly]::LoadFrom("$cw\CodeWalker.Core.dll")
$texconv = 'C:\Users\anton\Documents\Codex\2026-10-10\our-goal-is-to-build-machine\work\texture-tools\texconv.exe'   # Microsoft DirectXTex
$work = Join-Path $env:TEMP "tex_slim_work_$PID"

# ---------- RSC7 header sizes (CodeWalker GetSizeFromFlags, as the stream audit) ----------
function Size-FromFlags([uint32]$f) {
  $s = ((($f -shr 27) -band 1) -shl 0) + ((($f -shr 26) -band 1) -shl 1) + ((($f -shr 25) -band 1) -shl 2) + ((($f -shr 24) -band 1) -shl 3) +
       ((($f -shr 17) -band 0x7F) -shl 4) + ((($f -shr 11) -band 0x3F) -shl 5) + ((($f -shr 7) -band 0xF) -shl 6) +
       ((($f -shr 5) -band 3) -shl 7) + ((($f -shr 4) -band 1) -shl 8)
  [double]0x200 * [Math]::Pow(2, ($f -band 0xF)) * $s
}
function Phys-MiB([byte[]]$b) { (Size-FromFlags ([BitConverter]::ToUInt32($b, 12))) / 1MB }
function Sys-MiB([byte[]]$b) { (Size-FromFlags ([BitConverter]::ToUInt32($b, 8))) / 1MB }

# ---------- files and their texture dictionaries ----------
function Load-File([string]$ext, [byte[]]$b) {
  switch ($ext) { '.ytd' { $f = New-Object CodeWalker.GameFiles.YtdFile } '.ydr' { $f = New-Object CodeWalker.GameFiles.YdrFile }
                  '.ydd' { $f = New-Object CodeWalker.GameFiles.YddFile } }
  $f.Load($b); $f
}
function Tex-Of($f) {
  $dicts = switch ($f.GetType().Name) {
    'YtdFile' { @($f.TextureDict) }
    'YdrFile' { @($f.Drawable.ShaderGroup.TextureDictionary) }
    'YddFile' { @($f.Drawables | % { $_.ShaderGroup.TextureDictionary }) } }
  @(foreach ($d in $dicts) { if ($d -and $d.Textures) { foreach ($t in @($d.Textures.data_items)) { if ($t) { $t } } } })
}
function Xml-Of($f, [string]$ext) {   # whole-file XML without the texture entries (the gate for drawables)
  $x = switch ($ext) { '.ydr' { [CodeWalker.GameFiles.YdrXml]::GetXml($f, '') } '.ydd' { [CodeWalker.GameFiles.YddXml]::GetXml($f, '') } }
  [regex]::Replace($x, '(?s)<TextureDictionary>.*?</TextureDictionary>', '<TextureDictionary/>')
}

# ---------- DDS ----------
function Dds-Info([byte[]]$d) {
  $h = [BitConverter]::ToInt32($d, 12); $w = [BitConverter]::ToInt32($d, 16); $mips = [Math]::Max(1, [BitConverter]::ToInt32($d, 28))
  $pfFlags = [BitConverter]::ToInt32($d, 80); $four = [Text.Encoding]::ASCII.GetString($d, 84, 4); $bits = [BitConverter]::ToInt32($d, 88)
  $off = 128; $block = 0; $bpp = 0
  if ($pfFlags -band 4) {
    switch ($four) {
      'DXT1' { $block = 8 } 'ATI1' { $block = 8 } 'BC4U' { $block = 8 }
      'DXT3' { $block = 16 } 'DXT5' { $block = 16 } 'ATI2' { $block = 16 } 'BC5U' { $block = 16 }
      'DX10' { $off = 148; $fmt = [BitConverter]::ToInt32($d, 128)
               $block = if ($fmt -in 70, 71, 72, 79, 80, 81) { 8 } elseif ($fmt -in 73..78 + 82..84 + 94..99) { 16 } else { 0 }
               if (-not $block) { $bpp = 4 } }
      default { throw "unknown DDS fourCC $four" }
    }
  } else { $bpp = [int]($bits / 8) }
  [pscustomobject]@{ W = $w; H = $h; Mips = $mips; Block = $block; Bpp = $bpp; Off = $off }
}
function Level-Size($i, [int]$w, [int]$h) {
  if ($i.Block) { [Math]::Max(1, [Math]::Ceiling($w / 4)) * [Math]::Max(1, [Math]::Ceiling($h / 4)) * $i.Block } else { $w * $h * $i.Bpp }
}
function Can-Halve([byte[]]$d) { $i = Dds-Info $d; [int]($i.W / 2) -ge $MinDim -and [int]($i.H / 2) -ge $MinDim }
function Dds-Halve([byte[]]$d) {
  $i = Dds-Info $d
  if ($i.Mips -le 1) { return ,(Dds-Resize $d $i) }
  $cut = Level-Size $i $i.W $i.H
  $o = New-Object byte[] ($d.Length - $cut)
  [Array]::Copy($d, 0, $o, 0, $i.Off)
  [Array]::Copy($d, $i.Off + $cut, $o, $i.Off, $d.Length - $i.Off - $cut)
  $nw = [Math]::Max(1, [int]($i.W / 2)); $nh = [Math]::Max(1, [int]($i.H / 2))
  [BitConverter]::GetBytes([int]$nh).CopyTo($o, 12); [BitConverter]::GetBytes([int]$nw).CopyTo($o, 16)
  $pitch = if ($i.Block) { Level-Size $i $nw $nh } else { $nw * $i.Bpp }
  [BitConverter]::GetBytes([int]$pitch).CopyTo($o, 20)
  [BitConverter]::GetBytes([int]($i.Mips - 1)).CopyTo($o, 28)
  ,$o
}
function Dds-Resize([byte[]]$d, $i) {
  $four = [Text.Encoding]::ASCII.GetString($d, 84, 4)
  $fmt = if (-not $i.Block) { 'B8G8R8A8_UNORM' } else { switch ($four) { 'DXT1' {'BC1_UNORM'} 'DXT3' {'BC2_UNORM'} 'DXT5' {'BC3_UNORM'}
         'ATI1' {'BC4_UNORM'} 'BC4U' {'BC4_UNORM'} 'ATI2' {'BC5_UNORM'} 'BC5U' {'BC5_UNORM'} 'DX10' {'BC7_UNORM'} default { throw "no resize format for $four" } } }
  ,(Run-Texconv $d ([Math]::Max(1, [int]($i.W / 2))) ([Math]::Max(1, [int]($i.H / 2))) $fmt)
}
function Dds-Compress([byte[]]$d) { $i = Dds-Info $d; $f = if ($Compress -eq 'BC7') { 'BC7_UNORM' } else { 'BC3_UNORM' }; ,(Run-Texconv $d $i.W $i.H $f) }
function Run-Texconv([byte[]]$d, [int]$w, [int]$h, [string]$fmt) {
  New-Item -ItemType Directory -Force "$work\out" | Out-Null
  $src = "$work\t.dds"; [IO.File]::WriteAllBytes($src, $d); Remove-Item "$work\out\t.dds" -ErrorAction SilentlyContinue
  $hdr = if ($fmt -like 'BC7*') { '-dx10' } else { '-dx9' }
  $log = & $texconv -nologo -y $hdr -w $w -h $h -m 0 -f $fmt -o "$work\out" $src 2>&1
  if (-not (Test-Path "$work\out\t.dds")) { throw "texconv failed: $log" }
  ,[IO.File]::ReadAllBytes("$work\out\t.dds")
}
function Data-Bytes([byte[]]$d) { $d.Length - (Dds-Info $d).Off }
# CodeWalker's DDSIO.GetDDSFile throws "Invalid slice pitch" on non-square textures whose mip chain runs to 1x1 (e.g. 1024x256 with
# 11 levels: Sollumz-built sign textures; also the Nov 5 PD pistol). Then the DDS is written here from the texture's own fields:
# the levels' expected sizes, the data padded (Sollumz stores w*h*4*4/3 bytes, a few bytes short of the tail mips).
function Get-Dds($t) {
  try { return ,[CodeWalker.Utils.DDSIO]::GetDDSFile($t) } catch { if ($_.Exception.Message -notmatch 'pitch') { throw } }
  $f = "$($t.Format)"; $block = 0; $bpp = 0; $four = $null; $dx10 = 0
  switch ($f) { 'D3DFMT_A8R8G8B8' { $bpp = 4 } 'D3DFMT_DXT1' { $block = 8; $four = 'DXT1' } 'D3DFMT_DXT3' { $block = 16; $four = 'DXT3' }
                'D3DFMT_DXT5' { $block = 16; $four = 'DXT5' } 'D3DFMT_ATI1' { $block = 8; $four = 'ATI1' } 'D3DFMT_ATI2' { $block = 16; $four = 'ATI2' }
                'D3DFMT_BC7' { $block = 16; $four = 'DX10'; $dx10 = 98 } default { throw "no DDS writer for $f" } }
  $w = [int]$t.Width; $h = [int]$t.Height; $n = [int]$t.Levels; $total = 0
  for ($l = 0; $l -lt $n; $l++) { $lw = [Math]::Max(1, $w -shr $l); $lh = [Math]::Max(1, $h -shr $l)
    $total += if ($block) { [Math]::Max(1, [Math]::Ceiling($lw / 4)) * [Math]::Max(1, [Math]::Ceiling($lh / 4)) * $block } else { $lw * $lh * $bpp } }
  $hl = if ($dx10) { 148 } else { 128 }; $o = New-Object byte[] ($hl + $total)
  $src = $t.Data.FullData; [Array]::Copy($src, 0, $o, $hl, [Math]::Min($src.Length, $total))
  $p = { param($v, $at) [BitConverter]::GetBytes([int]$v).CopyTo($o, $at) }
  [Text.Encoding]::ASCII.GetBytes('DDS ').CopyTo($o, 0); & $p 124 4
  & $p (0x1 -bor 0x2 -bor 0x4 -bor 0x1000 -bor 0x20000 -bor $(if ($block) { 0x80000 } else { 0x8 })) 8
  & $p $h 12; & $p $w 16
  & $p $(if ($block) { [Math]::Max(1, [Math]::Ceiling($w / 4)) * [Math]::Max(1, [Math]::Ceiling($h / 4)) * $block } else { $w * $bpp }) 20
  & $p $n 28; & $p 32 76
  if ($block) { & $p 4 80; [Text.Encoding]::ASCII.GetBytes($four).CopyTo($o, 84) }
  else { & $p 0x41 80; & $p 32 88; & $p 0x00ff0000 92; & $p 0x0000ff00 96; & $p 0x000000ff 100; [BitConverter]::GetBytes([int]0xff000000).CopyTo($o, 104) }
  & $p (0x1000 -bor 0x400000 -bor 0x8) 108
  if ($dx10) { & $p $dx10 128; & $p 3 132; & $p 0 136; & $p 1 140; & $p 0 144 }
  ,$o
}
# DXT5 whose alpha is 255 in every texel -> DXT1, bit-exact: a DXT5 colour block is a DXT1 4-colour block; where its endpoints are
# in 3-colour order (c0 <= c1) they are swapped and the indices remapped (XOR 1; all 0 when c0 == c1). Half the bytes, same pixels.
# Opacity is checked on every level of 4x4 and up; the 1-block tail mips (2x2, 1x1) are not checked: Sollumz stores a few bytes too
# few for them (w*h*4/3), so they read as zero blocks; they are transcoded as they are (seen only from very far).
Add-Type -TypeDefinition @'
public static class Dxt {
  public static byte[] Dxt5ToDxt1(byte[] d, int off, int check) {
    int n = (d.Length - off) / 16; if ((d.Length - off) % 16 != 0) return null;
    byte[] o = new byte[off + n * 8]; System.Array.Copy(d, 0, o, 0, off);
    int[] a = new int[8];
    for (int b = 0; b < n; b++) {
      int s = off + b * 16, t = off + b * 8;
      int a0 = d[s], a1 = d[s + 1];
      a[0] = a0; a[1] = a1;
      if (a0 > a1) { for (int k = 1; k < 7; k++) a[k + 1] = ((7 - k) * a0 + k * a1) / 7; }
      else { for (int k = 1; k < 5; k++) a[k + 1] = ((5 - k) * a0 + k * a1) / 5; a[6] = 0; a[7] = 255; }
      ulong bits = 0; for (int k = 0; k < 6; k++) bits |= (ulong)d[s + 2 + k] << (8 * k);
      if (b < check) for (int k = 0; k < 16; k++) if (a[(int)((bits >> (3 * k)) & 7)] != 255) return null;
      int c0 = d[s + 8] | (d[s + 9] << 8), c1 = d[s + 10] | (d[s + 11] << 8);
      uint idx = (uint)(d[s + 12] | (d[s + 13] << 8) | (d[s + 14] << 16) | (d[s + 15] << 24));
      if (c0 < c1) { int x = c0; c0 = c1; c1 = x; idx ^= 0x55555555u; }
      else if (c0 == c1) { idx = 0; }
      o[t] = (byte)c0; o[t + 1] = (byte)(c0 >> 8); o[t + 2] = (byte)c1; o[t + 3] = (byte)(c1 >> 8);
      o[t + 4] = (byte)idx; o[t + 5] = (byte)(idx >> 8); o[t + 6] = (byte)(idx >> 16); o[t + 7] = (byte)(idx >> 24);
    }
    return o;
  }
}
'@
function Dds-ToDxt1([byte[]]$d) {
  if ([Text.Encoding]::ASCII.GetString($d, 84, 4) -ne 'DXT5') { return $null }
  $i = Dds-Info $d; $need = 128; for ($l = 0; $l -lt $i.Mips; $l++) { $need += (Level-Size $i ([Math]::Max(1, $i.W -shr $l)) ([Math]::Max(1, $i.H -shr $l))) }
  if ($d.Length -lt $need) { $q = New-Object byte[] $need; [Array]::Copy($d, $q, $d.Length); $d = $q }   # Sollumz short tail: pad to whole blocks
  $chk = 0; for ($l = 0; $l -lt $i.Mips; $l++) { $lw = $i.W -shr $l; $lh = $i.H -shr $l; if ($lw -ge 4 -and $lh -ge 4) { $chk += ($lw / 4) * ($lh / 4) } }
  $o = [Dxt]::Dxt5ToDxt1($d, 128, [int]$chk); if (-not $o) { return $null }
  [Text.Encoding]::ASCII.GetBytes('DXT1').CopyTo($o, 84)
  $i = Dds-Info $d; [BitConverter]::GetBytes([int]([Math]::Max(1, [Math]::Ceiling($i.W / 4)) * [Math]::Max(1, [Math]::Ceiling($i.H / 4)) * 8)).CopyTo($o, 20)
  ,$o
}
function Fmt-Tex($i) { "{0}x{1}/{2}" -f $i.W, $i.H, $i.Mips }

$files = Get-ChildItem -LiteralPath $Dir -Recurse -File | ? { $_.Extension -in '.ytd', '.ydr', '.ydd' }
if ($Only) { $files = $files | ? { $Only -contains $_.Name } }
foreach ($fi in $files) { try {
  $rel = $fi.FullName.Substring($Dir.TrimEnd('\').Length).TrimStart('\'); $ext = $fi.Extension.ToLower()
  $bytes = [IO.File]::ReadAllBytes($fi.FullName)
  if ([Text.Encoding]::ASCII.GetString($bytes, 0, 4) -ne 'RSC7') { "SKIP (encrypted or not a resource) $rel"; continue }
  $phys0 = Phys-MiB $bytes; $sys0 = Sys-MiB $bytes
  try { $file = Load-File $ext $bytes } catch { "SKIP (cannot read) ${rel}: $($_.Exception.Message)"; continue }
  $tex = Tex-Of $file
  if ($tex.Count -eq 0) { continue }
  $dds = @(foreach ($t in $tex) { [pscustomobject]@{ T = $t; Bytes = (Get-Dds $t); Orig = $null; NoDxt1 = $false } })
  foreach ($e in $dds) { $e.Orig = $e.Bytes }
  $texMiB = ($dds | % { Data-Bytes $_.Bytes } | Measure -Sum).Sum / 1MB
  $geo = 0.0                                                      # vertex + index buffers: what textures cannot remove
  if ($ext -ne '.ytd') { $ds = if ($ext -eq '.ydd') { @($file.Drawables) } else { @($file.Drawable) }
    foreach ($d in $ds) { foreach ($m in @($d.AllModels)) { foreach ($g in @($m.Geometries)) { if ($g) {
      $geo += $g.VertexData.VertexBytes.Length + 2 * $g.IndexBuffer.Indices.Length } } } } ; $geo /= 1MB }
  $big = @($tex | ? { $_.Width -gt $MaxDim -or $_.Height -gt $MaxDim })
  if ($phys0 -lt $BudgetMiB -and $big.Count -eq 0) { continue }
  $ratio = $phys0 / ($geo + $texMiB)                              # page packing: physical pages per byte of data, measured
  # the least the textures can weigh: every one compressed (if uncompressed) and halved to the floor
  $floor = 0.0
  foreach ($e in $dds) { $i = Dds-Info $e.Bytes; $w = $i.W; $h = $i.H
    while (($w -gt $MaxDim -or $h -gt $MaxDim) -or ([int]($w / 2) -ge $MinDim -and [int]($h / 2) -ge $MinDim)) { $w = [int]($w / 2); $h = [int]($h / 2) }
    $bpp = if ($i.Block -eq 8) { 0.5 } else { 1 }
    $floor += $w * $h * $bpp * 4 / 3 }
  $floor /= 1MB
  if ($Mode -eq 'scan') {
    $top = ($tex | Sort-Object { $_.Width * $_.Height } -Descending | Select -First 3 | % { "$($_.Name) $($_.Width)x$($_.Height) $($_.Format)" }) -join '; '
    "{0,7:N1} phys MiB (textures {1:N1}, geometry {2:N1}, floor ~{3:N1})  {4}  [{5}]" -f $phys0, $texMiB, $geo, ($ratio * ($geo + $floor)), $rel, $top
    continue
  }
  $changed = @{}
  $xml0 = if ($ext -ne '.ytd') { Xml-Of (Load-File $ext $bytes) $ext } else { $null }
  function Data-Now { $geo + (($dds | % { Data-Bytes $_.Bytes } | Measure -Sum).Sum / 1MB) }
  function Apply-Save {   # writes every changed DDS into its own texture object, saves, returns the bytes
    foreach ($e in $changed.Values) { $n = [CodeWalker.Utils.DDSIO]::GetTexture($e.Bytes); $t = $e.T
      $t.Width = $n.Width; $t.Height = $n.Height; $t.Depth = $n.Depth; $t.Levels = $n.Levels; $t.Format = $n.Format; $t.Stride = $n.Stride; $t.Data = $n.Data }
    ,$file.Save() }
  foreach ($e in $dds) {
    while ($true) { $i = Dds-Info $e.Bytes; if ($i.W -le $MaxDim -and $i.H -le $MaxDim) { break }
                    $n = Dds-Halve $e.Bytes; if (-not $n) { break }; $e.Bytes = $n; $changed[$e.T.Name] = $e } }
  # 1) no resolution lost: compress the largest uncompressed texture, then lossless DXT5 -> DXT1, while over BudgetMiB
  while ($ratio * (Data-Now) -ge $BudgetMiB) {
    $e = $dds | ? { (Dds-Info $_.Bytes).Block -eq 0 } | Sort-Object { $_.Bytes.Length } -Descending | Select -First 1
    if ($e) { $e.Bytes = Dds-Compress $e.Bytes; $changed[$e.T.Name] = $e; continue }
    $e = $dds | ? { -not $_.NoDxt1 -and [Text.Encoding]::ASCII.GetString($_.Bytes, 84, 4) -eq 'DXT5' } | Sort-Object { $_.Bytes.Length } -Descending | Select -First 1
    if ($e) { $n = Dds-ToDxt1 $e.Bytes; if ($n) { $e.Bytes = $n; $changed[$e.T.Name] = $e } else { $e.NoDxt1 = $true }; continue }
    break
  }
  $new = if ($changed.Count) { Apply-Save } else { $bytes }; $phys = Phys-MiB $new; $ratio = $phys / (Data-Now)
  # 2) halving, measured: the target is BudgetMiB, or FallbackMiB for a drawable that cannot reach BudgetMiB even at the floor
  $budget = if ($ext -eq '.ytd' -or $ratio * ($geo + $floor) -lt $BudgetMiB) { $BudgetMiB } else { $FallbackMiB }
  while ($phys -ge $budget) {
    $e = $dds | Sort-Object { $_.Bytes.Length } -Descending | ? { Can-Halve $_.Bytes } | Select -First 1
    if (-not $e) { break }
    $e.Bytes = Dds-Halve $e.Bytes; $changed[$e.T.Name] = $e
    if ($ratio * (Data-Now) -lt $budget -or -not ($dds | ? { Can-Halve $_.Bytes })) { $new = Apply-Save; $phys = Phys-MiB $new; $ratio = $phys / (Data-Now) }
  }
  if ($changed.Count -eq 0) { "UNCHANGED (at size floor) {0:N1} MiB  {1}" -f $phys0, $rel; continue }
  $new = Apply-Save
  $log = @(foreach ($e in $changed.Values) { "{0} {1} {2} -> {3} {4}" -f $e.T.Name, (Fmt-Tex (Dds-Info $e.Orig)), ([Text.Encoding]::ASCII.GetString($e.Orig, 84, 4)), (Fmt-Tex (Dds-Info $e.Bytes)), $e.T.Format })
  # reload and check
  $chk = Load-File $ext $new; $ct = Tex-Of $chk
  if ($ct.Count -ne $tex.Count) { "FAILED check (texture count $($ct.Count)/$($tex.Count)) $rel"; continue }
  $bad = @(foreach ($e in $dds) { $i = Dds-Info $e.Bytes; $c = $ct | ? { $_.Name -eq $e.T.Name } | Select -First 1
           if (-not $c -or $c.Width -ne $i.W -or $c.Height -ne $i.H -or $c.Levels -ne $i.Mips) { $e.T.Name } })
  if ($bad.Count) { "FAILED check (mismatched: $($bad -join ',')) $rel"; continue }
  if ($xml0 -ne $null) { $xml1 = Xml-Of $chk $ext; if ($xml1 -ne $xml0) { "FAILED check (drawable XML changed outside textures) $rel"; continue } }
  $phys1 = Phys-MiB $new; $sys1 = Sys-MiB $new
  if ($Out) { $dest = Join-Path $Out $rel } else {
    $dest = $fi.FullName
    if ($Backup) { $bk = Join-Path $Backup $rel; New-Item -ItemType Directory -Force (Split-Path $bk) | Out-Null
                   if (-not (Test-Path -LiteralPath $bk)) { Copy-Item -LiteralPath $fi.FullName -Destination $bk } } }
  New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
  [IO.File]::WriteAllBytes($dest, $new)
  $flag = if ($phys1 -ge $BudgetMiB) { if ($budget -gt $BudgetMiB) { "  OVER $BudgetMiB (cannot reach it at the texture floor; geometry {0:N1} MiB)" -f $geo } else { "  OVER $BudgetMiB (at floor)" } } else { '' }
  "SLIM`t{0}`tphys {1:N2} -> {2:N2}`tsys {3:N2} -> {4:N2}`t{5} textures changed{6}" -f $rel, $phys0, $phys1, $sys0, $sys1, $changed.Count, $flag
  foreach ($l in $log) { "  tex`t$rel`t$l" }
} catch { "ERROR $($fi.FullName): $($_.Exception.Message)" } }
Remove-Item -Recurse -Force $work -ErrorAction SilentlyContinue
