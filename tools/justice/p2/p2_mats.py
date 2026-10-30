"""Justice Center phase 2 materials (run inside Blender, after tc_kit.init): Rockstar's own recipes, copied (playbook doc 09
"copy Rockstar's materials"), registered in tc_kit.MAT by key. Textures are his, taken from the game by p2_tex.ps1 (work/p2/tex_rs)
and embedded (one drawable mixes sources from several of his dictionaries, so no single txd would bind them all):
  granite  normal.sps        ko_gv_wall (hw1_26+hi) + ko_gv_wall02_n; bumpiness 1, spec .4, falloff 100, fresnel .95 - his recipe on
                             hw1_26_build01 (ko_gv_wall03): warm sand / salmon stone panels, the real Spanish pink granite's read
  roof     normal_spec.sps   im_roof04_big + im_roof4_n + im_roof04 (the old courts tower's roof recipe)
  cream    default.sps       mc_wall_0001 (the old block's panel wall: Jail II's plain cream panels)
  brick    normal.sps        sc1_19_rsd_jp_brick_0001 + _n (the old plaza's red brick)
  kerb     normal.sps        im_kerbs03 + _n (granite kerbs, step nosings, the lawn edge)
  grass    default.sps       im_grass10deepb (the old block's lawn layer)
  glass_*  glass_env.sps, ALPHA bucket: Rockstar's exterior dark glass (dt1_06_build1_1, glass()); bronze / atrium = his texture scaled
  metal    normal_spec.sps   dark steel, spec .8 / falloff 40 / fresnel .9 (ba_trad_rails, doc 09): mullions, louvres, the Portal
  back     the dark backing panel behind shell glass; win_emis / soffit_emis: emissivenight.sps (lit only at night)
  sidewalk Rockstar's im_sidewalk012 (work/sidewalk_mat.py: his material, txd sc1_rd_road; the podium's paving = the slab's)
UV scale per material (metres per UV, his median): uv_scale() - applied in the build's exterior pass."""
import bpy, numpy as np, sys
from pathlib import Path
import tc_kit as TK
P2 = Path(__file__).resolve().parent; TEX = P2 / 'tex_rs'
# Rockstar's vertex colour 0 on an exterior (R natural ambient, G ARTIFICIAL ambient, B ...): the mean of the building we replace,
# sc1_19_courts.ydr (measured 2026-10-28; sheriff 0.58 / 0.13 / 0.37, hw1_26_build01 0.48 / 0.02 / 0.49). tc_kit writes 1.0 everywhere,
# and G = 1 lights every wall at night as if lit from inside (Antonio's 23:00 shots) - our exteriors and LODs carry his values;
# only the night-light (_emi) models keep 1.0.
EXT_VCOL = (0.467, 0.054, 0.222, 1.0)
M_PER_UV = {'granite': 4.05, 'roof': 5.0, 'cream': 6.0, 'brick': 1.5, 'kerb': 2.15, 'grass': 3.0, 'conc': 4.0, 'back': 4.0, 'metal': 2.0}
def _img(name, noncolor):
    p = TEX / (name + '.dds'); assert p.exists(), f'{p} missing: run p2_tex.ps1'
    im = bpy.data.images.load(str(p), check_existing=True); im.colorspace_settings.name = 'Non-Color' if noncolor else 'sRGB'
    if not im.packed_file: im.pack()
    return im
def rs(key, shader, samplers, params):
    """one of his recipes: shader file, {sampler: his texture name}, {parameter: value}."""
    m = TK.create_shader(shader); m.name = 'JC ' + key
    for s, tname in samplers.items():
        nd = m.node_tree.nodes.get(s); assert nd is not None, (key, s)
        nd.image = _img(tname, s != 'DiffuseSampler'); nd.texture_properties.embedded = True
    for s in ('BumpSampler', 'SpecSampler'):                    # a sampler the recipe leaves out: flat (as TK.tex_mat)
        nd = m.node_tree.nodes.get(s)
        if nd is not None and s not in samplers:
            nn = np.ones((8, 8, 4), np.float32); nn[:, :, :2] = .5 if s == 'BumpSampler' else .3
            nd.image = TK.dds(f'jc_{s.lower()}_{key}', nn, TK.OUT / 'tex', True); nd.texture_properties.embedded = True
    for p, v in params.items():
        q = m.node_tree.nodes.get(p)
        if q is not None: (q.set_vec3 if isinstance(v, tuple) else q.set_float)(v)
    TK.MAT[key] = m; return m
def glass(key, rgb_mult=(1.0, 1.0, 1.0), alpha_mult=1.0):
    """Rockstar's exterior dark glass, copied (dt1_06_build1_1, the downtown building: glass_env.sps, ALPHA bucket, his
    im_glass_01im_glass_01_a (RGB ~29, alpha ~0.6) + mc_window_0005_n + im_glass_01_s, bumpiness .5, spec 1, falloff 430, fresnel
    .97). glass_env has no environment sampler: it reflects the game's own reflection probe, which goes dark at night. (Our old
    glass_normal_spec_reflect carried a fixed light-grey environment texture, so every pane read light grey at 23:00 - Antonio.)
    A variant (bronze, the atrium's see-through glass) is HIS texture with its RGB / alpha scaled, embedded under its own name."""
    m = TK.create_shader('glass_env.sps'); m.name = 'JC ' + key
    im = _img('im_glass_01im_glass_01_a', False)
    if rgb_mult != (1.0, 1.0, 1.0) or alpha_mult != 1.0:
        w, h = im.size; px = np.array(im.pixels[:], np.float32).reshape(h, w, 4)
        px[:, :, :3] = np.clip(px[:, :, :3] * np.array(rgb_mult, np.float32), 0, 1); px[:, :, 3] = np.clip(px[:, :, 3] * alpha_mult, 0, 1)
        im = TK.dds('jc_glass_' + key, px, TK.OUT / 'tex', False, 'BC3_UNORM')
    for s_, img in (('DiffuseSampler', im), ('BumpSampler', _img('mc_window_0005_n', True)), ('SpecSampler', _img('im_glass_01_s', True))):
        nd = m.node_tree.nodes.get(s_); assert nd is not None, (key, s_); nd.image = img; nd.texture_properties.embedded = True
    for p, v in (('bumpiness', 0.5), ('specularIntensityMult', 1.0), ('specularFalloffMult', 430.0), ('specularFresnel', 0.97)):
        q = m.node_tree.nodes.get(p)
        if q is not None: q.set_float(v)
    TK.MAT[key] = m; return m
def flat(key, rgb, spec=.1, grain=.04, shader=None, params=None):
    k = 64; px = np.ones((k, k, 4), np.float32); px[:, :, :3] = np.clip(np.array(rgb)[None, None, :] * (1 + grain * TK.rng.normal(0, 1, (k, k, 1))), 0, 1)
    m = TK.tex_mat('JC ' + key, px, spec=spec, shader=shader)
    for p, v in (params or {}).items():
        q = m.node_tree.nodes.get(p)
        if q is not None: q.set_float(v)
    TK.MAT[key] = m; return m
def lit_window_px():
    """a lit office bay at night: warm ceiling light falling off downwards, blinds / mullion shadows (day: a dark interior)."""
    h, w = 64, 128; y = np.linspace(1, 0, h)[:, None]; x = np.linspace(0, 1, w)[None, :]
    lum = 0.55 + 0.45 * y ** 1.5
    lum = lum * (1 - 0.35 * ((np.floor(x * 6) % 2) * (np.abs(((x * 6) % 1) - .5) > .46)))
    px = np.ones((h, w, 4), np.float32); px[:, :, 0] = lum * 1.0; px[:, :, 1] = lum * .82; px[:, :, 2] = lum * .58
    px[:, :, :3] *= DAY                                       # by day a dim interior behind the dark glass; the night multiplier lights it
    return px
DAY = 0.16                                                    # (rig 2026-10-28: a full-bright lit-window texture read as beige panels at noon)
def build():
    rs('granite', 'normal.sps', {'DiffuseSampler': 'ko_gv_wall', 'BumpSampler': 'ko_gv_wall02_n'}, {'bumpiness': 1.0, 'specularIntensityMult': 0.4, 'specularFalloffMult': 100.0, 'specularFresnel': 0.95})
    rs('roof', 'normal_spec.sps', {'DiffuseSampler': 'im_roof04_big', 'BumpSampler': 'im_roof4_n', 'SpecSampler': 'im_roof04'}, {'bumpiness': 1.0, 'specularIntensityMult': 0.3, 'specularFalloffMult': 40.0})
    rs('cream', 'default.sps', {'DiffuseSampler': 'mc_wall_0001'}, {})
    rs('brick', 'normal.sps', {'DiffuseSampler': 'sc1_19_rsd_jp_brick_0001', 'BumpSampler': 'sc1_19_rsd_jp_brick_0001_n'}, {'bumpiness': 1.0, 'specularIntensityMult': 0.2, 'specularFalloffMult': 30.0})
    rs('kerb', 'normal.sps', {'DiffuseSampler': 'im_kerbs03', 'BumpSampler': 'im_kerbs03_n'}, {'bumpiness': 1.0, 'specularIntensityMult': 0.25, 'specularFalloffMult': 40.0})
    rs('grass', 'default.sps', {'DiffuseSampler': 'im_grass10deepb'}, {})
    glass('glass_dark')                                             # the shell / office glass: his dark glass as it is
    glass('glass_bronze', (1.45, 1.05, 0.62))                       # bronze-tinted base glass (police HQ, Jail I: Wikipedia): his, warmed
    glass('glass_atrium', (2.2, 2.4, 2.5), 0.45)                    # the galleria's curtain wall + roof: the one see-through glass
    flat('metal', (.045, .045, .05), .8, .02, 'normal_spec.sps', {'specularFalloffMult': 40.0, 'specularFresnel': 0.9})
    flat('back', (.030, .030, .034), .05, .03)                     # backing panel / window box: a dark, unlit interior
    flat('conc', (.42, .41, .39), .08, .06)                        # vehicle bay walls
    m = TK.tex_mat('JC win_emis', lit_window_px(), True, 3.0 / DAY, .1, 'emissivenight.sps'); TK.MAT['win_emis'] = m
    px = np.ones((16, 16, 4), np.float32); px[:, :, :3] = np.array((1.0, .9, .72)) * DAY
    m = TK.tex_mat('JC soffit_emis', px, True, 4.0 / DAY, .1, 'emissivenight.sps'); TK.MAT['soffit_emis'] = m
    px = np.ones((16, 16, 4), np.float32); px[:, :, :3] = (1.0, .05, .03)
    m = TK.tex_mat('JC aviation', px, True, 6.0, .1, 'emissive.sps'); TK.MAT['aviation'] = m
    sys.path.insert(0, str(P2.parent)); import sidewalk_mat as SW
    TK.MAT['sidewalk'] = SW.load()[SW.LOT_MAT['lot']]
    return SW
