# assemble a chain of modules by their joints (same maths as c9_dj shared/barsnap.lua) and render it (textured, offline):
#   py -3 assemble_preview.py <set> out.png el,s200,oc,s100,er ["eyex,eyey,eyez,atx,aty,atz" ...]
# (each module after the first mates its first joint onto the previous module's last free joint)
import sys, math, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import counters as C, counters_sets as S, rsxview, rsx, numpy as np
def mat(x, y, w):
    M = np.eye(4); M[:3, :3] = rsx.rot_z(w); M[:3, 3] = (x, y, 0); return M
def world(px, py, w, j):
    c, s = math.cos(math.radians(w)), math.sin(math.radians(w))
    return px + j[0]*c - j[1]*s, py + j[0]*s + j[1]*c, (w + j[2]) % 360
def mate(gj, k):
    w = (k[2] + 180 - gj[2]) % 360
    c, s = math.cos(math.radians(w)), math.sin(math.radians(w))
    return k[0] - (gj[0]*c - gj[1]*s), k[1] - (gj[0]*s + gj[1]*c), w
def chain(mods, names):
    placed = []; free = None
    for i, n in enumerate(names):
        v = mods[n]
        if i == 0:
            x, y, w = 0.0, 0.0, 0.0
        else:
            gj = v['joints'][0]
            x, y, w = mate(gj, free)
        placed.append((v['model'], mat(x, y, w)))
        outs = [world(x, y, w, j) for j in v['joints'][(0 if i == 0 else 1):]]
        free = outs[-1] if outs else None
    return placed
if __name__ == '__main__':
    key, out = sys.argv[1], sys.argv[2]
    names = sys.argv[3].split(',')
    mods = C.build_set(key, S.SETS[key])
    pl = chain(mods, names)
    P = np.vstack([ (m.bounds()[0], m.bounds()[1]) for m, M in pl]); 
    allp = np.vstack([(np.vstack([g.pos for g in m.geos]) @ M[:3,:3].T + M[:3,3]) for m, M in pl])
    c = (allp.min(0) + allp.max(0)) / 2; r = np.linalg.norm(allp.max(0) - allp.min(0))
    views = [(c[0]-0.6*r, c[1]-0.9*r, 0.8*r), (c[0]+0.7*r, c[1]+0.8*r, 0.9*r), (c[0]-0.1*r, c[1]-0.15*r, 1.6*r)]
    cells = [('%s %s view %d' % (key, ','.join(names), i), rsxview.render(pl, C.RSX + '/tex', size=(900, 600), eye=e, at=c)) for i, e in enumerate(views)]
    extra = sys.argv[4:] 
    for e in extra:
        ex, ey, ez, ax, ay, az = map(float, e.split(','))
        cells.append(('close %s' % e, rsxview.render(pl, C.RSX + '/tex', size=(900, 600), eye=(ex, ey, ez), at=(ax, ay, az), fov=30)))
    rsxview.sheet(cells, 2, out, cell=(900, 600))
