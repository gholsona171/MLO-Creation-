"""Jail I sit sheet (the visual half of the sit test: ON the seat, not in it - jc-interiors' jc3_sitshots pattern): clones of the player
take their seat's scenario at its sit point - every seat of every group (booking counter + officer station chairs, the waiting bench, a
holding cell bench, the dayroom tables, the officer desk, bunks of both tiers) - then a camera 2.2 m in front (0.8 m off-axis) of each
(room, scenario, facing) group. Then a contact sheet shots/p4_jail_sit_sheet.jpg. Run: py -3 jj_sitshots.py <out dir>"""
import json, math, sys, time, subprocess
from pathlib import Path
JL = Path(__file__).resolve().parent; sys.path[:0] = [str(JL), str(JL.parent)]
import jj_probe as P, jc_frame as F
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
S = P.L['seats']
def group(room, what): return [i for i, s in enumerate(S) if s[4] == room and s[6].startswith(what)]
import jj_fit as JF
FIT = P.L['fit_boxes']                                                     # [u0, u1, v0, v1, z0, z1] of every kit fitting
CANDS = [(2.0, 0.7), (2.0, -0.7), (1.4, 1.4), (1.4, -1.4), (0.6, 1.8), (0.6, -1.8), (-0.6, 1.8), (-0.6, -1.8), (1.2, 0.0),
         (-1.4, 0.7), (-1.4, -0.7), (-3.0, 0.8), (-3.0, -0.8)]          # last: from behind (a booth: through its glass)
def pick_camera(i):
    """a camera spot for seat i's photo (2026-10-29: fixed 'in front' put cameras inside counters and, for a chair facing a wall, outside
    the building): the first of CANDS (forward, lateral in the sitter's frame) that lies in the seat's room clear rect (0.25 m in), not in
    a fitting's footprint, not within 0.9 m of another sitter, with a line of sight to the sitter's chest over every fitting."""
    u, v, z, h, room, sc, what = S[i]; hr = math.radians(h); fu, fv = -math.sin(hr), math.cos(hr); ru, rv = fv, -fu
    rects = JF.clear(room); others = [(s_[0], s_[1]) for j, s_ in enumerate(S) if j != i and abs(s_[2] - z) < 1.0 and j in picks]
    for f, l in CANDS:
        cu, cv = u + fu * f + ru * l, v + fv * f + rv * l
        if not any(r[0] + 0.25 < cu < r[1] - 0.25 and r[2] + 0.25 < cv < r[3] - 0.25 for r in rects): continue
        if any(b[0] < cu < b[1] and b[2] < cv < b[3] and b[4] < z + 1.2 for b in FIT): continue
        if any(math.hypot(cu - a, cv - c) < 0.9 for a, c in others): continue
        blocked = False
        for k in range(1, 20):
            t = k / 20; pu, pv, pz = cu + (u - cu) * t, cv + (v - cv) * t, z + 0.75 + (0.15 - 0.75) * t
            if any(b[0] < pu < b[1] and b[2] < pv < b[3] and b[4] < pz < b[5] for b in FIT): blocked = True; break
        if not blocked: return cu, cv
    return None
picks = (group('book', 'booking counter') + group('book', 'officer station') + group('book', 'booking bench') + group('hold', 'holding cell 1')
         + group('hold', 'holding cell 2') + group('block', 'officer desk') + group('block', 'dayroom table')[:8]
         + group('block', 'cell W101') + group('block', 'cell W102') + group('block', 'cell E101') + group('block', 'cell W201') + group('block', 'cell E201'))
try:
    P.revive(); P.stand(-17.0, 9.0, P.J.G); time.sleep(2)
    P.lua('_G.__sitters=_G.__sitters or {} for _,c in ipairs(_G.__sitters) do DeleteEntity(c) end _G.__sitters={} return "clear"', 20)
    for b in range(0, len(picks), 8):
        code = 'local P0=PlayerPedId() '
        for i in picks[b:b + 8]:
            u, v, z, h, room, sc, what = S[i]; x, y = F.W(u, v)
            code += ('do local c=ClonePed(P0,false,false,true) SetEntityCoords(c,%.3f,%.3f,%.3f) TaskStartScenarioAtPosition(c,"%s",%.3f,%.3f,%.3f,%.1f,0,true,true) '
                     '_G.__sitters[#_G.__sitters+1]=c end ' % (x, y, z + 0.5, sc, x, y, z, (h + F.HDEG) % 360))
        P.lua(code + 'return "ok"', 30)
    r = P.lua('Wait(5000) local n=0 for _,c in ipairs(_G.__sitters) do if IsPedUsingAnyScenario(c) then n=n+1 end end return tostring(#_G.__sitters)..":"..tostring(n)', 30)
    print('SITTERS placed:using =', r, 'of', len(picks))
    cams, seen = [], set()
    for i in picks:
        u, v, z, h, room, sc, what = S[i]; k = (room, sc, h, what.split(' bunk')[0][:14])
        if k in seen: continue
        seen.add(k); cam = pick_camera(i)
        if cam is None: print('SIT_CAMERA_NONE', i, room, what); continue
        cu, cv = cam; x, y = F.W(cu, cv); tx, ty = F.W(u, v)
        cams.append([f'sit_{room}_{i}', x, y, z + 0.75, tx, ty, z + 0.15])
    for n, x, y, z, tx, ty, tz in cams:
        subprocess.run([P.GB, '-c', f'HOUR=13 bash /c/C9Test/tcshot.sh {OUT.as_posix()}/{n}.png {x:.2f} {y:.2f} {z:.2f} {tx:.2f} {ty:.2f} {tz:.2f} 55 4'], capture_output=True, timeout=120)
finally:
    P.lua('for _,c in ipairs(_G.__sitters or {}) do DeleteEntity(c) end _G.__sitters={} return "gone"', 20)
    subprocess.run([P.GB, '-c', 'bash /c/C9Test/tc_release.sh'], capture_output=True, timeout=60)
from PIL import Image, ImageDraw
shots = sorted(OUT.glob('sit_*.png')); W_, H_ = 480, 270; cols = 4; rows = (len(shots) + cols - 1) // cols
sheet = Image.new('RGB', (W_ * cols, H_ * rows), (20, 20, 20)); d = ImageDraw.Draw(sheet)
for k, p in enumerate(shots):
    im = Image.open(p).convert('RGB').resize((W_, H_)); sheet.paste(im, ((k % cols) * W_, (k // cols) * H_)); d.text(((k % cols) * W_ + 8, (k // cols) * H_ + 8), p.stem, fill=(255, 255, 0))
sheet.save(JL.parents[1] / 'shots/p4_jail_sit_sheet.jpg', quality=85)
print('SITSHOTS', len(shots), 'sheet shots/p4_jail_sit_sheet.jpg')
