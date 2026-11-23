"""Rockstar's own textures for our materials: the DDS files tex_extract.ps1 pulls from the game into ../tex/vanilla. Picked by
looking at the game, not by name (survey: shots ref_*).
  ROOF   sc1_rsn_ns_ground_0010 (+ _n): the flat roof of the Chumash modern house (ch1_10_house102), smooth grey concrete.
  LAWN   ch1_10_ih_manicuredgrass01 (+ n): that house's own kept lawn.
  LOT    the Harmony used-car lot (cs6_03_usedlotmc, ~1208 2719), the most real-looking paved lot near the yard. Rockstar
         paints it with terrain_cb_w_4lyr_pxm_spm, four layers blended by vertex colour 2 (+ parallax height maps), and dresses it
         with decals faded by vertex alpha (cs6_03_usedlotmc_d001). LOT_LAYERS / LOT_DECALS are those exact textures.
         (Tried and dropped: one flat blacktop texture + procedural cracks - dc_parking_tarmac_01 read pale with a 3 m blotch
         grid, the freeway tarmac carries lane wheel-stripes, the dark car-park blacktop read fake: "doesn't look realistic".)
house.py and pave.py read ROOF / LAWN as float RGBA arrays (load); the lot textures are copied byte for byte (their own
compression) into jy_pave.ytd under our names (pave.py). The game's files are never changed.
Run: python vanilla_tex.py   prints the tex_extract.ps1 -Names list (build.sh uses it)."""
from pathlib import Path
D = Path(__file__).resolve().parents[1] / 'tex' / 'vanilla'
HOUSE102 = 'ch1_10_house102+hidr.ytd'
LOT_LAYERS = [  # (diffuse, normal, height) for layers 0..3, each name@dictionary (survey/lotscan.tsv)
    ('im_concrete09a@cs6_03_extra+hi.ytd', 'im_concrete09_n@desertsaltonoutskirts+hi.ytd', 'nxg_delete_h@cshillssoutheast.ytd'),
    ('im_concrete11a@cs6_03_extra+hi.ytd', 'im_concrete11_n@desertsaltonoutskirts.ytd', 'nxg_im_concrete11_h@desertsaltonoutskirts.ytd'),
    ('cs_rsn_sl_road_0007@desertsaltonsouth+hi.ytd', 'cs_rsn_sl_road_0007_n@ch1.ytd', 'nxg_cs_rsn_sl_road_0007_h@hw1_06_g.ytd'),
    ('cs_rsn_sl_desgravelstonesdirt_01@ch3landmidwest+hi.ytd', 'cs_rsn_sl_desgravelstonesdirt_01_n@ch3landmidwest+hi.ytd',
     'nxg_cs_rsn_sl_desgravelstonesdirt_01_h@cshillssoutheast.ytd')]
LOT_DECALS = {
    'busted': ('et_tarmacbusted02@id221ground+hi.ytd', 'et_tarmacbusted02_n@po1_05_ground03+hidr.ytd'),   # broken, patched tarmac
    'drift': ('cs_rsl_aa_dirttrack5@cs2roads+hi.ytd', 'cs_rsl_aa_dirttrack5_n@cs2roads+hi.ytd'),          # sand washed onto the lot
    'splats': ('dc_parking_splats_01dc_parking_splats_01_a@des_aptblock_root002+hidr.ytd',),               # oil splats atlas (alpha)
    'stain': ('im_ground_overlay0006im_ground_overlay0006_a@dt1_21_bld_d+hi.ytd',)}                        # brown ground stain (alpha)
NAMES = [f'sc1_rsn_ns_ground_0010@{HOUSE102}', f'sc1_rsn_ns_ground_0010_n@{HOUSE102}',
         f'ch1_10_ih_manicuredgrass01@{HOUSE102}', f'ch1_10_ih_manicuredgrass01n@{HOUSE102}'] + \
        [s for layer in LOT_LAYERS for s in layer] + [s for v in LOT_DECALS.values() for s in v]


def path(spec):
    """the extracted DDS of a name@dictionary spec."""
    f = D / f"{spec.split('@')[0]}.dds"
    assert f.exists(), f'{f} missing: run tex_extract.ps1 -Names "$(python vanilla_tex.py)"'
    return f


def load(name, data=False):
    import bpy, numpy as np
    im = bpy.data.images.load(str(path(name)))
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


if __name__ == '__main__': print(','.join(NAMES))
