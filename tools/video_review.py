"""Video -> review contact sheets: one frame every N seconds, labelled with its time, tiled 2x2 (or 3x3) per sheet.
Usage: py -3 video_review.py walkthrough.mp4 out_dir [seconds=3] [grid=2]
Needs ffmpeg (WinGet Gyan.FFmpeg is found automatically) and Pillow."""
import glob, os, subprocess, sys
from PIL import Image, ImageDraw

def ffmpeg():
    hits = glob.glob(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg-*\bin\ffmpeg.exe'))
    return hits[0] if hits else 'ffmpeg'

def main(video, out, every=3.0, grid=2):
    os.makedirs(out, exist_ok=True); tag = os.path.splitext(os.path.basename(video))[0]
    for f in glob.glob(os.path.join(out, f'{tag}_f*.jpg')): os.remove(f)
    subprocess.run([ffmpeg(), '-hide_banner', '-loglevel', 'error', '-y', '-i', video, '-vf', f'fps=1/{every},scale=960:-2',
                    os.path.join(out, f'{tag}_f%03d.jpg')], check=True)
    frames = sorted(glob.glob(os.path.join(out, f'{tag}_f*.jpg'))); per = grid * grid; W, Hh = 1920 // grid * grid, 1080
    for s in range(0, len(frames), per):
        sheet = Image.new('RGB', (1920, 1080))
        for j, f in enumerate(frames[s:s + per]):
            im = Image.open(f).resize((1920 // grid, 1080 // grid)); d = ImageDraw.Draw(im); n = int(f[-7:-4])
            d.rectangle((0, 0, 170, 24), fill='black'); d.text((6, 6), f't={(n - 1) * every:.0f}s', fill='yellow')
            sheet.paste(im, ((j % grid) * (1920 // grid), (j // grid) * (1080 // grid)))
        sheet.save(os.path.join(out, f'{tag}_sheet{s // per:02d}.jpg'), quality=85)
    print(len(frames), 'frames ->', (len(frames) + per - 1) // per, 'sheets in', out)

if __name__ == '__main__':
    a = sys.argv; main(a[1], a[2], float(a[3]) if len(a) > 3 else 3.0, int(a[4]) if len(a) > 4 else 2)
