"""Justice Center phase 2: reference photo | our render side-by-sides (the main proof of the look, playbook doc 09 reference rule).
Pairs: survey/ref/<photo> with shots/p2_ref/<camera>.png (plan/cameras_p2.txt, taken by work/jc_pair.sh with CAMS=...). Each pair is
scaled to one height, labelled, and stacked into one sheet; a missing render FAILS (no silent gaps).
Run: py -3 ref_sheet.py <render dir> <out.jpg>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
J = Path(r'C:\Users\anton\Documents\Codex\JusticeCenter')
PAIRS = [('jc_complex_2024.jpg', 'ref_complex_2024', 'Ontario St / St Clair: police HQ, Courts Tower, Portal  ->  Innocence Blvd / Roy Lowenstein'),
         ('jc_jail1_tower_jail2.jpg', 'ref_jail1_tower_jail2', 'Jail I (louvres), the tower, Jail II (cream)  ->  from Macdonald St'),
         ('jc_lemay_a.jpg', 'ref_lemay_a', 'Jail I corner, colonnade, ribbon glass, louvre bands  ->  Macdonald / Davis'),
         ('jc_lemay_c.jpg', 'ref_lemay_c', 'steps under the colonnade, the lawn  ->  Jail I west colonnade'),
         ('jc_courts_tower_skyline.jpg', 'ref_courts_skyline', 'the tower: fins, dark window bands, mast'),
         ('jc_police_hq_sign.jpg', 'ref_police_sign', 'the plaza wall with the bronze letters')]
def main(rd, out):
    rd = Path(rd); rows = []; H = 520
    for photo, cam, label in PAIRS:
        r = rd / (cam + '.png')
        if not r.exists(): raise SystemExit(f'REF_SHEET: render missing {r}')
        a = Image.open(J / 'survey/ref' / photo).convert('RGB'); b = Image.open(r).convert('RGB')
        a = a.resize((int(a.width * H / a.height), H)); b = b.resize((int(b.width * H / b.height), H))
        row = Image.new('RGB', (a.width + b.width + 30, H + 34), 'white'); row.paste(a, (0, 34)); row.paste(b, (a.width + 30, 34))
        d = ImageDraw.Draw(row); d.text((6, 8), 'REAL  ' + photo, fill='black'); d.text((a.width + 36, 8), 'OURS  ' + cam + '   ' + label, fill='black')
        rows.append(row)
    W_ = max(r.width for r in rows); S = Image.new('RGB', (W_, sum(r.height + 10 for r in rows)), 'white'); y = 0
    for r in rows: S.paste(r, (0, y)); y += r.height + 10
    S.save(out, quality=88); print('REF_SHEET', out, len(rows), 'pairs')
if __name__ == '__main__': main(sys.argv[1], sys.argv[2])
