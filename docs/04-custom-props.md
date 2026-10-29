# 04 · Custom props

When the game has no good version (a 181-inch TV, a urinal, a faucet), model one. Tools: `tools/custom_props/tc_props.py`
(Blender) and `tools/custom_props/props_meta.py` (patch, import, ytyp).

## Pipeline
1. **Model in Blender + Sollumz** (headless). Convention: front = -Y, back plane at y = 0 (sits flush on a wall), z = 0 at the base.
   Smooth, believable shapes: bmesh bevels for edges; **boolean modifiers** to carve (the urinal bowl = an ellipsoid subtracted from a
   rounded block; apply with `bpy.ops.object.modifier_apply` after making the object active).
2. **Materials** are Sollumz shader materials with embedded textures generated in numpy (brushed metal = streak noise, vents = slot
   rows, logos via PIL). Copy Rockstar's shader recipe first: export the closest vanilla prop (`ydr_xml.ps1 -Mode export`) and read
   its shader + parameters.
3. **Export as CW XML** (`target_formats={'CWXML'}`) when anything must be patched, then **import with CodeWalker**
   (`ydr_xml.ps1 -Mode import`).
4. **ytyp**: one plain archetype per model (embedded textures, lodDist ~150), compiled with TequiBuild; ship it with
   `data_file 'DLC_ITYP_REQUEST' 'stream/<name>.ytyp'`.
5. **Tell the survey** (`arch_ytyp.json`) which ytyp holds the model, so the MLO depends on it and the placement code knows its bounds.
6. Place it like any prop (any scale: MLO entities take `scaleXY` / `scaleZ`).

## Render targets (a TV screen scripts can draw on)
Rockstar's recipe (from `prop_tv_flat_01`): the screen shader (`normal_spec_emissive`) samples a texture named
`script_rt_<name>` that is in the drawable's texture dictionary with **Usage SCRIPT**, **UsageFlags X1024, UNK24**, uncompressed
**D3DFMT_A8R8G8B8**, **one mip**. Sollumz can't set usage, so patch the CW XML and write the DDS yourself (`props_meta.py`).
- Size must be a power of two (we use 1024 × 512 for 16:9); the texture size is the render resolution.
- UV orientation: in Blender, v = 1 at the TOP of the screen (we had it upside down first; test with a pattern that says LEFT/TOP).
- Script side: `RegisterNamedRendertarget('<name>')`, `LinkNamedRendertarget(model)`, `GetNamedRendertargetRenderId`, then
  `SetTextRenderId(id)` around draw calls. Linking is **per model**: every copy shows the same picture.
- MLO entities are not script objects: `GetClosestObjectOfType` does NOT find them. Ship their positions in the MLO data file and
  test distance to those.
- Add a glass layer 1 mm in front of the screen for reflections (Rockstar does).

## What we built
| Model | Notes |
|---|---|
| `tc_prop_tv` | 4.00 × 2.25 m screen (181 in) at scale 1; 10 mm piano-black bezel, brushed titanium edge band, graphite vented back, steel bracket, glass cover, standby LED, chin logo; 95 mm deep. Render target `tc_tvscreen`. Placed at 0.55–1.3 scale (99–235 in). |
| `tc_prop_urinal` | solid vitreous-china body, bowl carved by boolean, chrome flush valve + trap. |
| `tc_prop_faucet` | chrome gooseneck mixer for inset basins. |
| `tc_prop_mirror` | 1 × 1 m `mirror_default` panel; stretch with scaleXY / scaleZ; needs a mirror portal on its plane (doc 02). |

- **Building with Rockstar's own textures without embedding them**: import the vanilla model (Sollumz), reuse its materials on new
  geometry, export without embedding, and give the new archetype the vanilla archetype's `textureDictionary` (e.g. the junkyard
  walls' `cs4_02_airscrap_2`). Texture names come in lower case on import; GTA's lookup is case-insensitive.
- Match Rockstar's texel density: measure metres per UV from the vanilla faces (wow2easy_move/tools: the plaster was 3.5 m a repeat).
- Copy their vertex colour too: Rockstar's exterior walls carry Colour0 ~ (0.46, 0, 0.44); all-white makes a new piece glow next to them.
  G is the ARTIFICIAL ambient (night light): about 0.05 on his walls (sc1_19_courts 0.467 / 0.054 / 0.222, sheriff 0.581 / 0.132 / 0.368,
  hw1_26 0.484 / 0.015 / 0.485, read with `color_srgb`). Never 1.0 on an exterior or LOD: at 23:00 every wall glows (Justice Center, doc 13).
- v13_kit `new_drawable(name, ...)` treats an existing object called `name` as the root: never name the mesh part the same.
- Climb-proof walls: a ped climbs ~2.5 m from where it stands; an SUV roof adds ~1.9 m. 6 m of wall with collision to 6.6 m is out of
  reach from any car or SUV.

