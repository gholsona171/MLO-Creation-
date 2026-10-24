"""Tower City swimmable pool: the game's own water map (survey/water/common.rpf_data_levels_gta5_water.xml: every ocean, river and
reservoir quad untouched) + the penthouse pool's swim cells -> src/water/tc_water.xml. tower_city's water.lua loads it with
LoadWaterFromPath (FiveM).

Rig findings (2026-10-22):
  * Water quads register only on the 2 m grid: a 2 x 2 m cell on even coordinates works; 1 m, 0.5 m and off-grid quads are ignored.
  * The pool is turned 69.5 deg with the tower, so it is filled with every 2 m cell whose four corners lie inside the raised pool
    deck (POOL +/- DECK_M in the lot frame); the deck stands 4 cm above the water line, so where a cell reaches past the pool edge
    it lies under stone, never on an open floor. DECK_M 1.8 -> ~97 % of the pool swims.
  * IsInvisible: our own water surface is drawn by the room (tower_crown.water_mat); HasLimitedDepth keeps the floors under the
    pool dry.
A collision surface with material WATER + MAP_RIVER (how Rockstar's house pools work) is seen by script probes but did not make
peds swim at this height/location - not used."""
import math, xml.etree.ElementTree as ET
from pathlib import Path
import tower_crown as C
T = Path(__file__).resolve().parents[1]
SRC = T / 'survey/water/common.rpf_data_levels_gta5_water.xml'; OUT = T / 'src/water/tc_water.xml'
OX, OY, HEAD = -78.897, -827.328, math.radians(69.5)
def W(u, v): return OX + u * math.cos(HEAD) - v * math.sin(HEAD), OY + u * math.sin(HEAD) + v * math.cos(HEAD)
def L(x, y):
    dx, dy = x - OX, y - OY; return dx * math.cos(HEAD) + dy * math.sin(HEAD), -dx * math.sin(HEAD) + dy * math.cos(HEAD)
def cells(region, step=2):
    """every step-m grid cell whose four corners lie inside region = (u0, u1, v0, v1) in the lot frame."""
    inside = lambda x, y: region[0] <= L(x, y)[0] <= region[1] and region[2] <= L(x, y)[1] <= region[3]
    P = [W(u, v) for u in region[:2] for v in region[2:]]; xs = [p[0] for p in P]; ys = [p[1] for p in P]
    out = []
    for gx in range(int(min(xs) // step) * step, int(max(xs) // step) * step + step, step):
        for gy in range(int(min(ys) // step) * step, int(max(ys) // step) * step + step, step):
            if all(inside(x, y) for x, y in ((gx, gy), (gx + step, gy), (gx, gy + step), (gx + step, gy + step))): out.append((gx, gx + step, gy, gy + step))
    return out
def main():
    tree = ET.parse(SRC); q = tree.getroot().find('WaterQuads'); n0 = len(q); z = C.WATER_Z
    cs = cells(C.DECK)
    for x0, x1, y0, y1 in cs:
        it = ET.SubElement(q, 'Item')
        for t, v in (('minX', x0), ('maxX', x1), ('minY', y0), ('maxY', y1), ('Type', 0), ('IsInvisible', 'true'), ('HasLimitedDepth', 'true'),
                     ('z', round(z, 3)), ('a1', 26), ('a2', 26), ('a3', 26), ('a4', 26), ('NoStencil', 'false')):
            ET.SubElement(it, t, value=str(v))
    OUT.parent.mkdir(parents=True, exist_ok=True); ET.indent(tree, space='  '); tree.write(OUT, encoding='UTF-8', xml_declaration=True)
    print('POOL_WATER', OUT.name, 'vanilla quads', n0, '+ pool cells', len(cs), 'z', round(z, 2))
if __name__ == '__main__': main()
