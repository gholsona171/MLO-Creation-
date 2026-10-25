"""zip_package.py <resource parent dir> <out.zip>: zips tower_city + tower_city_life with FORWARD-slash paths (Compress-Archive writes
backslashes, which some Linux unzip tools - most FiveM hosts - mishandle). Edit the folder list for another MLO."""
import os, sys, zipfile
src, out = sys.argv[1], sys.argv[2]
tmp = out + '.new'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for top in ('tower_city', 'tower_city_life'):
        for root, dirs, files in os.walk(os.path.join(src, top)):
            dirs.sort()
            for f in sorted(files):
                p = os.path.join(root, f)
                z.write(p, os.path.relpath(p, src).replace(os.sep, '/'))
os.replace(tmp, out)
