"""Rockstar's own textures for our materials: the DDS files tex_extract.ps1 pulls from the game into ../tex/vanilla. Picked by
looking at the game, not by name (survey: shots ref_*).
  ROOF   sc1_rsn_ns_ground_0010 (+ _n): the flat roof of the Chumash modern house (ch1_10_house102), smooth grey concrete.
  LAWN   ch1_10_ih_manicuredgrass01 (+ n): that house's own kept lawn.
  LOT    brand-new blacktop (Nov 23, the client: "blacktop ... no impurities or imperfections, looks like it was just built, no
         oil"): Rockstar's freshly laid road tarmac cs_rsl_ps_newtarmac_001 (Route 68 and the desert highways) as the base, with
         soft broad patches of two other fresh blacktops (the tuner car meet's tun_tarmac, the airport's dark car-park tarmac) so
         a 1.2 ha lot does not read as one tiled texture. Same 4-layer terrain shader as Rockstar's lots, no parallax relief.
  PAINT  crisp fresh parking paint: Rockstar's downtown car-park markings atlas (im_carparkmarkings01), white and yellow
         versions with one layout (line strip, arrows, the wheelchair symbol), alpha-masked decals.
         (Tried and dropped: Harmony's worn used-car-lot recipe with cracks / oil / sand decals and Sandy Shores' worn paint -
         the client wants it new; before that one flat blacktop with drawn-on cracks, the freeway tarmac's lane stripes.)
house.py and pave.py read ROOF / LAWN as float RGBA arrays (load); the lot textures are copied byte for byte (their own
compression) into jy_pave.ytd under our names (pave.py). The game's files are never changed.
Run: python vanilla_tex.py   prints the tex_extract.ps1 -Names list (build.sh uses it)."""
from pathlib import Path
D = Path(__file__).resolve().parents[1] / 'tex' / 'vanilla'
HOUSE102 = 'ch1_10_house102+hidr.ytd'
LOT_LAYERS = [  # (diffuse, normal) for layers 0..3, each name@dictionary (survey/freshscan.tsv); height maps are flat (pave.py)
    ('cs_rsl_ps_newtarmac_001@ch1+hi.ytd', 'dc_parking_tarmac_01_n@ch3struct01+hi.ytd'),                         # base
    ('tun_tarmac@tr_int2_tuner_car_meet_txd.ytd', 'tun_tarmac_n@tr_int2_tuner_car_meet_txd.ytd'),                # soft patches
    ('ap1_dc_parking_tarmac_01_dark@ap1_01_b_sidebit1spl2+hidr.ytd', 'dc_parking_tarmac_01_n@ch3struct01+hi.ytd'),  # soft patches
    ('cs_rsl_ps_newtarmac_001@ch1+hi.ytd', 'tun_tarmac_n@tr_int2_tuner_car_meet_txd.ytd')]                       # (unused corner)
PAINT = {'white': 'im_carparkmarkings01_a_bigim_carparkmarkings01_a_big@dt1_09_carpark_ov4+hidr.ytd',
         'yellow': 'im_carparkmarkings01_bigim_carparkmarkings01_a@sc1_06_carpark+hidr.ytd'}
PAINT_UV = {'line': (852 / 1024, 954 / 1024),                                   # u range of the line strip; it runs the whole v
            'arrow': (52 / 1024, 215 / 1024, 1 - 532 / 1024, 1 - 1011 / 1024),  # u0, u1, v at the tail, v at the tip (points -v)
            'sign': (24 / 1024, 1 - 475 / 1024, 439 / 1024, 1 - 16 / 1024)}     # wheelchair: u0, v0, u1, v1 (upright = +v)
NAMES = [f'sc1_rsn_ns_ground_0010@{HOUSE102}', f'sc1_rsn_ns_ground_0010_n@{HOUSE102}',
         f'ch1_10_ih_manicuredgrass01@{HOUSE102}', f'ch1_10_ih_manicuredgrass01n@{HOUSE102}'] + \
        [s for layer in LOT_LAYERS for s in layer] + list(PAINT.values())


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
