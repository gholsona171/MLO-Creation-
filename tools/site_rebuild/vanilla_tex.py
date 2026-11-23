"""Rockstar's own textures for our materials: the DDS files tex_extract.ps1 pulls from the game into ../tex/vanilla, read back
(in Blender) as float RGBA arrays in the layout proc_tex.py returns, so house.py and pave.py take them where they took procedural ones.
Picked by looking at the game, not by name (survey: shots ref_*):
  ROOF     sc1_rsn_ns_ground_0010 (+ _n): the flat roof of the Chumash modern house (ch1_10_house102, -3011 750), the same
           style as Graveyard's house - smooth grey concrete with hairline cracks. (The gravel ballast roofs read as noise up close.)
  LAWN     ch1_10_ih_manicuredgrass01 (+ n): that house's own kept lawn
  ASPHALT  ap1_dc_parking_tarmac_01_dark (+ dc_parking_tarmac_01_n): the airport car parks' dark blacktop - even fine
           aggregate, the tone of Route 68 beside the yard. (Tried: dc_parking_tarmac_01 read pale with a 3 m blotch grid from
           the air; cs_rsn_sl_freewaytarmac_001_drk carries lane wheel-stripes that corrugate a lot.)
The textures are re-saved under our own names in our own dictionaries; the game's files are never changed.
Run: python vanilla_tex.py   prints the tex_extract.ps1 -Names list (build.sh uses it)."""
from pathlib import Path
D = Path(__file__).resolve().parents[1] / 'tex' / 'vanilla'
NAMES = ['sc1_rsn_ns_ground_0010@ch1_10_house102+hidr.ytd', 'sc1_rsn_ns_ground_0010_n@ch1_10_house102+hidr.ytd',
         'ch1_10_ih_manicuredgrass01@ch1_10_house102+hidr.ytd', 'ch1_10_ih_manicuredgrass01n@ch1_10_house102+hidr.ytd',
         'ap1_dc_parking_tarmac_01_dark', 'dc_parking_tarmac_01_n']


def load(name, data=False):
    import bpy, numpy as np
    f = D / f'{name}.dds'
    assert f.exists(), f'{f} missing: run tex_extract.ps1 -Names "{",".join(NAMES)}"'
    im = bpy.data.images.load(str(f))
    if data: im.colorspace_settings.name = 'Non-Color'
    w, h = im.size; px = np.array(im.pixels[:], np.float32).reshape(h, w, 4); px[..., 3] = 1.0
    bpy.data.images.remove(im); return px


def normal(name):
    """a normal map with its blue channel rebuilt from red / green (two-channel BC5 maps carry none)."""
    import numpy as np
    n = load(name, True); x, y = n[..., 0] * 2 - 1, n[..., 1] * 2 - 1
    n[..., 2] = np.sqrt(np.clip(1 - x * x - y * y, 0, 1)) * .5 + .5; return n


def _rough(d, v):
    import numpy as np
    r = np.ones_like(d); r[..., :3] = v; return r


def roof():
    d = load('sc1_rsn_ns_ground_0010'); return d, normal('sc1_rsn_ns_ground_0010_n'), _rough(d, .85)


def lawn():
    d = load('ch1_10_ih_manicuredgrass01'); return d, normal('ch1_10_ih_manicuredgrass01n'), _rough(d, .95)


def asphalt():
    d = load('ap1_dc_parking_tarmac_01_dark'); return d, normal('dc_parking_tarmac_01_n'), _rough(d, .9)


if __name__ == '__main__': print(','.join(NAMES))
