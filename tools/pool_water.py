"""Tower City swimmable pool: the game's own water map (survey/water/common.rpf_data_levels_gta5_water.xml: every ocean, river and
reservoir quad untouched) + the penthouse pool's swim cells -> src/water/tc_water.xml. tower_city's water.lua loads it with
LoadWaterFromPath (FiveM).

Rig findings (2026-10-22):
  * Water quads register only on the 2 m grid: a 2 x 2 m cell on even coordinates works; 1 m, 0.5 m and off-grid quads are ignored.
  * The pool is turned 69.5 deg with the tower, so it is filled with every 2 m cell that lies wholly inside POOL +/- SWIM_M and
    inside the spa's floor. The water line is 25 cm below the floor (Antonio: the first, higher water let you swim where you
    shouldn't), so wherever a cell reaches past the pool edge it lies under the floor slab, never in the open.
  * Antonio (2026-10-22, review 2): the surface still read too high and rolled like the sea. The line is now 45 cm under the floor
    and a CalmingQuad (the game's own lake/reservoir mechanism) covers the pool so the water lies still.
  * The game draws the pool's water itself (IsInvisible false; Antonio: our extra drawn surface was a moving overlay, the game's
    water is right). HasLimitedDepth keeps the floors under the pool dry.
A collision surface with material WATER + MAP_RIVER (how Rockstar's house pools work) is seen by script probes but did not make
peds swim at this height/location - not used."""
import math, xml.etree.ElementTree as ET
from pathlib import Path
import tower_crown as C
T = Path(__file__).resolve().parents[1]
CALM = 0.0                                                     # calming-quad dampening over the pool (vanilla lakes use 0.05; 0 = flat)
SRC = T / 'survey/water/common.rpf_data_levels_gta5_water.xml'; OUT = T / 'src/water/tc_water.xml'
OX, OY, HEAD = -78.897, -827.328, math.radians(69.5)
def W(u, v): return OX + u * math.cos(HEAD) - v * math.sin(HEAD), OY + u * math.sin(HEAD) + v * math.cos(HEAD)
def L(x, y):
    dx, dy = x - OX, y - OY; return dx * math.cos(HEAD) + dy * math.sin(HEAD), -dx * math.sin(HEAD) + dy * math.cos(HEAD)
def cells(region, step=2, room='ph_spa'):
    """every step-m grid cell that lies wholly inside region = (u0, u1, v0, v1) in the lot frame AND inside the room's floor
    (C.rects: never in the outside corner notch). Nine sample points per cell (corners, edge mids, centre)."""
    rs = C.rects(room)
    def inside(x, y):
        u, v = L(x, y)
        return region[0] <= u <= region[1] and region[2] <= v <= region[3] and any(a <= u <= b and c <= v <= d for a, b, c, d in rs)
    P = [W(u, v) for u in region[:2] for v in region[2:]]; xs = [p[0] for p in P]; ys = [p[1] for p in P]
    out = []
    for gx in range(int(min(xs) // step) * step, int(max(xs) // step) * step + step, step):
        for gy in range(int(min(ys) // step) * step, int(max(ys) // step) * step + step, step):
            if all(inside(gx + i * step / 2, gy + j * step / 2) for i in range(3) for j in range(3)): out.append((gx, gx + step, gy, gy + step))
    return out
def main():
    tree = ET.parse(SRC); q = tree.getroot().find('WaterQuads'); n0 = len(q); z = C.WATER_Z
    cs = cells(C.SWIM)
    for x0, x1, y0, y1 in cs:
        it = ET.SubElement(q, 'Item')
        for t, v in (('minX', x0), ('maxX', x1), ('minY', y0), ('maxY', y1), ('Type', 0), ('IsInvisible', 'false'), ('HasLimitedDepth', 'true'),
                     ('z', round(z, 3)), ('a1', 26), ('a2', 26), ('a3', 26), ('a4', 26), ('NoStencil', 'false')):
            ET.SubElement(it, t, value=str(v))
    xs = [c[0] for c in cs] + [c[1] for c in cs]; ys = [c[2] for c in cs] + [c[3] for c in cs]
    cq = tree.getroot().find('CalmingQuads'); it = ET.SubElement(cq, 'Item')       # a calming quad over the pool: still indoor water
    for t, v in (('minX', min(xs)), ('maxX', max(xs)), ('minY', min(ys)), ('maxY', max(ys)), ('fDampening', CALM)): ET.SubElement(it, t, value=str(v))
    OUT.parent.mkdir(parents=True, exist_ok=True); ET.indent(tree, space='  '); tree.write(OUT, encoding='UTF-8', xml_declaration=True)
    print('POOL_WATER', OUT.name, 'vanilla quads', n0, '+ pool cells', len(cs), 'z', round(z, 2))
if __name__ == '__main__': main()
