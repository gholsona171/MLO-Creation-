"""zip_package.py <resource parent dir> <out.zip>: zips the given resource folders (default tower_city + tower_city_life) with FORWARD-slash paths (Compress-Archive writes
backslashes, which some Linux unzip tools - most FiveM hosts - mishandle). Usage: py -3 zip_package.py <parent dir> <out.zip> [folder ...]"""
import os, sys, zipfile
src, out = sys.argv[1], sys.argv[2]
folders = sys.argv[3:] or ['tower_city', 'tower_city_life']   # the resource folders to pack (under src)
tmp = out + '.new'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for top in folders:
        for root, dirs, files in os.walk(os.path.join(src, top)):
            dirs.sort()
            for f in sorted(files):
                p = os.path.join(root, f)
                z.write(p, os.path.relpath(p, src).replace(os.sep, '/'))
os.replace(tmp, out)
