"""campath_cut.py <ffmpeg.exe> <raw.mkv> <out.mp4> : turns a campath.sh recording into the finished video. The raw take has a few
seconds of black before each shot (the next shot streaming in); every black stretch is cut down to a short dip (DIP s), the
start and end get a gentle fade, and the result is encoded 1080p H.264 for sharing (no audio)."""
import re, subprocess, sys

DIP, PAD = 0.45, 0.25
ff, raw, out = sys.argv[1:4]
probe = subprocess.run([ff, '-hide_banner', '-i', raw, '-vf', 'blackdetect=d=0.3:pix_th=0.05:pic_th=0.97', '-an', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
blacks = [(float(a), float(b)) for a, b in re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', probe)]
m =re.search(r'Duration: (\d+):(\d+):([\d.]+)', probe); dur = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
keep, t = [], 0.0
for a, b in blacks:                                     # keep the picture between black stretches, plus a short dip each side
    if a - t > 0.5: keep.append((max(0.0, t - (PAD if t else 0)), min(dur, a + DIP / 2)))
    t = b
if dur - t > 0.5: keep.append((max(0.0, t - PAD), dur))
assert keep, 'nothing but black in the recording'
parts = ''.join(f'[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS[v{i}];' for i, (a, b) in enumerate(keep))
total = sum(b - a for a, b in keep)
fc = parts + ''.join(f'[v{i}]' for i in range(len(keep))) + f'concat=n={len(keep)}:v=1:a=0,scale=1920:-2,fade=t=in:d=0.6,fade=t=out:st={total - 0.8:.2f}:d=0.8[o]'
subprocess.run([ff, '-hide_banner', '-loglevel', 'error', '-y', '-i', raw, '-filter_complex', fc, '-map', '[o]', '-r', '30',
                '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], check=True)
print('CAMPATH_CUT_PASS', out, f'{total:.1f} s from {len(keep)} pieces (raw {dur:.1f} s, {len(blacks)} black stretches)')
