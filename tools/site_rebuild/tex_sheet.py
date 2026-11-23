"""(read-only) A contact sheet of every .dds in a folder: each texture scaled to CELL px with its name under it.
Run: blender -b --python tex_sheet.py -- <dds dir> <out.png>"""
import bpy, sys, numpy as np
from pathlib import Path
a = sys.argv[sys.argv.index('--') + 1:]; D = Path(a[0]); OUT = a[1]; CELL = 256; COLS = 5
fs = sorted(D.glob('*.dds')); rows = (len(fs) + COLS - 1) // COLS
sheet = np.ones((rows * CELL, COLS * CELL, 4), np.float32)
for k, f in enumerate(fs):
    im = bpy.data.images.load(str(f)); im.scale(CELL, CELL)
    px = np.array(im.pixels[:], np.float32).reshape(CELL, CELL, 4); px[..., 3] = 1
    r, c = rows - 1 - k // COLS, k % COLS; sheet[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL] = px
    print('SHEET', k, f.stem, flush=True)
out = bpy.data.images.new('sheet', COLS * CELL, rows * CELL); out.pixels = sheet.ravel(); out.filepath_raw = OUT; out.file_format = 'PNG'; out.save()
