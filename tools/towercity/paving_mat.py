"""Tower City: the exterior paving material (run inside Blender): mid grey 1 m concrete flags (0.47: the 0.60 first try read white in the sun) with dark joints, each flag a hair
lighter / darker - the read of Rockstar's downtown sidewalk around the lots. Used by the level-0 lot slab (l0_slab.py) and the
exterior clean-up's paving (ext_build.py), so every piece of our ground outside the buildings is one surface.
The texture spans 4 m (the kits' 0.25 UV scale): 4 x 4 flags."""
import numpy as np
def make(M, name='TC paving', stem='tc_paving'):
    d, n, r = M.maps('brushed_concrete')
    g = d[:, :, :3].mean(axis=2, keepdims=True); d[:, :, :3] = 0.47 + (g - g.mean()) * 0.5
    h, w = d.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]
    J = max(2, h // 220)
    joint = ((yy * 4) % h < J) | ((xx * 4) % w < J)
    rs = np.random.default_rng(7).uniform(-0.035, 0.035, (4, 4))
    d[:, :, :3] += rs[(yy * 4) // h, (xx * 4) // w][:, :, None]
    d[joint, :3] *= 0.55; n[joint, 2] *= 0.85; d[:, :, 3] = 1.0
    return M.material(name, stem, np.clip(d, 0, 1), n, M.spec_from(r, .02, .08), .8, .06, 20)
